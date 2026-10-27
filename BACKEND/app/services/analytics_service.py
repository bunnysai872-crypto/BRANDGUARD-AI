"""
Extended AnalyticsService — Governance Intelligence Dashboard
=============================================================
Augments the existing get_governance_analytics() by adding:
- Visual compliance review metrics (VisualComplianceAnalysis)
- Document review metrics (DocumentReview)
- Combined cross-review-type finding aggregations (no double-counting)
- Turnaround metrics (submission → approval timestamps)
- Actionable insights from historical patterns (evidence-backed only)
- Date-range filter applied to all review types

All data is aggregated from real DB records. No invented statistics.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from app.models import (
    db,
    ContentSubmission,
    ContentRevision,
    ReviewDecision,
    ComplianceAnalysis,
    ComplianceFinding,
    Brand,
    BrandGuideline,
    VisualComplianceAnalysis,
    VisualComplianceFinding,
    DocumentReview,
    DocumentReviewFinding,
)
from app.services.brand_service import BrandService


class AnalyticsService:

    # ─── Original method (preserved exactly) ─────────────────────────────────
    @staticmethod
    def get_governance_analytics(user_id, role, brand_id=None, days=None):
        # 1. Resolve accessible brands
        accessible_brands = BrandService.get_accessible_brands(user_id, role)
        accessible_brand_ids = [b["id"] for b in accessible_brands]

        if not accessible_brand_ids:
            return {
                "metrics": {
                    "total_submissions": 0,
                    "drafts_count": 0,
                    "pending_review_count": 0,
                    "changes_requested_count": 0,
                    "approved_count": 0,
                    "published_count": 0,
                    "avg_revisions_per_submission": 0.0,
                    "total_brands": 0,
                    "total_guidelines": 0,
                    "active_guidelines": 0,
                    "total_findings": 0
                },
                "category_distribution": [],
                "common_issues": [],
                "severity_distribution": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
                "review_outcomes": [],
                "timeline_trends": [],
                "brands": [],
                "governance_note": "No accessible brands or records found for the current user session."
            }, None, 200

        # Scope brand IDs
        target_brand_ids = accessible_brand_ids
        if brand_id:
            try:
                b_id = int(brand_id)
                if b_id in accessible_brand_ids:
                    target_brand_ids = [b_id]
                else:
                    return None, "Access denied to the specified brand analytics.", 403
            except (ValueError, TypeError):
                return None, "Invalid brand ID parameter.", 400

        # Base submissions query
        subs_query = ContentSubmission.query.filter(ContentSubmission.brand_id.in_(target_brand_ids))
        if role == "creator":
            subs_query = subs_query.filter_by(creator_id=user_id)

        # Date range filter
        cutoff = None
        if days:
            try:
                days_int = int(days)
                if days_int <= 0:
                    return None, "days parameter must be a positive integer.", 400
                cutoff = datetime.now(timezone.utc) - timedelta(days=days_int)
                subs_query = subs_query.filter(ContentSubmission.created_at >= cutoff)
            except (ValueError, TypeError):
                return None, "Invalid days parameter. Must be a positive integer.", 400

        submissions = subs_query.all()
        submission_ids = [s.id for s in submissions]
        total_subs = len(submissions)

        # Status counts
        status_counts = {
            "Draft": 0,
            "Ready for AI Review": 0,
            "AI Reviewed": 0,
            "Changes Requested": 0,
            "Pending Manager Approval": 0,
            "Approved": 0,
            "Published": 0
        }
        for s in submissions:
            if s.status in status_counts:
                status_counts[s.status] += 1
            else:
                status_counts[s.status] = 1

        # Revisions count
        total_revisions = 0
        if submission_ids:
            total_revisions = ContentRevision.query.filter(
                ContentRevision.submission_id.in_(submission_ids)
            ).count()
        avg_revisions = round(total_revisions / total_subs, 2) if total_subs > 0 else 0.0

        # Brand guidelines counts
        guidelines_query = BrandGuideline.query.filter(BrandGuideline.brand_id.in_(target_brand_ids))
        total_guidelines = guidelines_query.count()
        active_guidelines = guidelines_query.filter_by(is_active=True).count()

        # Findings from text submission compliance
        category_distribution = []
        common_issues = []
        severity_dist = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        total_findings = 0

        if submission_ids:
            analysis_ids = [
                a.id for a in ComplianceAnalysis.query.filter(
                    ComplianceAnalysis.submission_id.in_(submission_ids)
                ).all()
            ]

            if analysis_ids:
                cat_results = (
                    db.session.query(
                        ComplianceFinding.category,
                        func.count(ComplianceFinding.id).label("count")
                    )
                    .filter(ComplianceFinding.analysis_id.in_(analysis_ids))
                    .group_by(ComplianceFinding.category)
                    .order_by(func.count(ComplianceFinding.id).desc())
                    .all()
                )
                category_distribution = [{"category": r[0], "count": r[1]} for r in cat_results]

                sev_results = (
                    db.session.query(
                        ComplianceFinding.severity,
                        func.count(ComplianceFinding.id).label("count")
                    )
                    .filter(ComplianceFinding.analysis_id.in_(analysis_ids))
                    .group_by(ComplianceFinding.severity)
                    .all()
                )
                for s_row in sev_results:
                    sev_name = s_row[0].capitalize() if s_row[0] else "Medium"
                    if sev_name in severity_dist:
                        severity_dist[sev_name] = s_row[1]
                    else:
                        severity_dist[sev_name] = s_row[1]
                total_findings = sum(severity_dist.values())

                issue_results = (
                    db.session.query(
                        ComplianceFinding.category,
                        ComplianceFinding.problematic_text,
                        ComplianceFinding.severity,
                        func.count(ComplianceFinding.id).label("freq")
                    )
                    .filter(ComplianceFinding.analysis_id.in_(analysis_ids))
                    .group_by(
                        ComplianceFinding.problematic_text,
                        ComplianceFinding.category,
                        ComplianceFinding.severity
                    )
                    .order_by(func.count(ComplianceFinding.id).desc())
                    .limit(8)
                    .all()
                )
                common_issues = [
                    {
                        "category": r[0],
                        "problematic_text": r[1][:60] + "..." if len(r[1]) > 60 else r[1],
                        "severity": r[2],
                        "frequency": r[3]
                    }
                    for r in issue_results
                ]

        # Review Decision outcomes
        review_outcomes = []
        if submission_ids:
            dec_results = (
                db.session.query(
                    ReviewDecision.decision,
                    func.count(ReviewDecision.id).label("count")
                )
                .filter(ReviewDecision.submission_id.in_(submission_ids))
                .group_by(ReviewDecision.decision)
                .all()
            )
            review_outcomes = [{"decision": d[0], "count": d[1]} for d in dec_results]

        # Timeline trends
        timeline_trends = []
        if submissions:
            date_map = {}
            for s in sorted(submissions, key=lambda x: x.created_at or datetime.now(timezone.utc)):
                dt_str = s.created_at.strftime("%Y-%m-%d") if s.created_at else "Unknown"
                if dt_str not in date_map:
                    date_map[dt_str] = {"date": dt_str, "submissions": 0, "approved": 0, "published": 0}
                date_map[dt_str]["submissions"] += 1
                if s.status == "Approved":
                    date_map[dt_str]["approved"] += 1
                elif s.status == "Published":
                    date_map[dt_str]["published"] += 1
            timeline_trends = list(date_map.values())[-10:]

        # Accessible brand list for filter UI
        brand_list = [{"id": b["id"], "name": b["name"]} for b in accessible_brands]

        return {
            "metrics": {
                "total_submissions": total_subs,
                "drafts_count": status_counts.get("Draft", 0),
                "ready_ai_count": status_counts.get("Ready for AI Review", 0),
                "ai_reviewed_count": status_counts.get("AI Reviewed", 0),
                "pending_review_count": status_counts.get("Pending Manager Approval", 0),
                "changes_requested_count": status_counts.get("Changes Requested", 0),
                "approved_count": status_counts.get("Approved", 0),
                "published_count": status_counts.get("Published", 0),
                "avg_revisions_per_submission": avg_revisions,
                "total_brands": len(target_brand_ids),
                "total_guidelines": total_guidelines,
                "active_guidelines": active_guidelines,
                "total_findings": total_findings
            },
            "category_distribution": category_distribution,
            "common_issues": common_issues,
            "severity_distribution": severity_dist,
            "review_outcomes": review_outcomes,
            "timeline_trends": timeline_trends,
            "brands": brand_list,
            "governance_note": (
                "Historical compliance analytics are computed directly from active application database records. "
                "Compliance trends and revision frequencies reflect internal governance checkpoints, "
                "and historical trends do not necessarily prove causation."
            )
        }, None, 200

    # ─── New method: extended governance intelligence ─────────────────────────
    @staticmethod
    def get_intelligence_dashboard(user_id, role, brand_id=None, days=None):
        """
        Extended governance intelligence dashboard combining:
        - Text submission compliance (ComplianceAnalysis / ComplianceFinding)
        - Visual compliance (VisualComplianceAnalysis / VisualComplianceFinding)
        - Document review (DocumentReview / DocumentReviewFinding)

        No double-counting: each review type is aggregated separately, then
        combined into unified totals.

        Returns (data_dict, error_str, http_status_code).
        """
        # ── Validate params first (before any DB lookups) ──────────────────────
        cutoff = None
        if days is not None and days != "":
            try:
                days_int = int(days)
                if days_int <= 0:
                    return None, "days parameter must be a positive integer.", 400
                cutoff = datetime.now(timezone.utc) - timedelta(days=days_int)
            except (ValueError, TypeError):
                return None, "Invalid days parameter. Must be a positive integer.", 400

        # ── Brand scoping ──────────────────────────────────────────────────────
        accessible_brands = BrandService.get_accessible_brands(user_id, role)
        accessible_brand_ids = [b["id"] for b in accessible_brands]

        if not accessible_brand_ids:
            if brand_id:
                try:
                    int(brand_id)
                except (ValueError, TypeError):
                    return None, "Invalid brand_id parameter.", 400
                return None, "Access denied to the specified brand analytics.", 403
            return _empty_intelligence_response(accessible_brands, brand_id, days), None, 200

        target_brand_ids = accessible_brand_ids
        if brand_id:
            try:
                b_id = int(brand_id)
                if b_id not in accessible_brand_ids:
                    return None, "Access denied to the specified brand analytics.", 403
                target_brand_ids = [b_id]
            except (ValueError, TypeError):
                return None, "Invalid brand_id parameter.", 400

        # ── Date cutoff (already computed above) ───────────────────────────────

        # ── Text submission compliance ─────────────────────────────────────────
        subs_q = ContentSubmission.query.filter(
            ContentSubmission.brand_id.in_(target_brand_ids)
        )
        if role == "creator":
            subs_q = subs_q.filter_by(creator_id=user_id)
        if cutoff:
            subs_q = subs_q.filter(ContentSubmission.created_at >= cutoff)
        submissions = subs_q.all()
        submission_ids = [s.id for s in submissions]

        status_counts = {}
        for s in submissions:
            status_counts[s.status] = status_counts.get(s.status, 0) + 1

        total_revisions = 0
        if submission_ids:
            total_revisions = ContentRevision.query.filter(
                ContentRevision.submission_id.in_(submission_ids)
            ).count()
        avg_revisions = round(total_revisions / len(submissions), 2) if len(submissions) > 0 else 0.0

        # Text compliance findings
        text_finding_sevs = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Unable to Verify": 0}
        text_cat_dist = {}
        text_common_issues = []
        text_analysis_count = 0

        if submission_ids:
            analysis_ids = [
                a.id for a in ComplianceAnalysis.query.filter(
                    ComplianceAnalysis.submission_id.in_(submission_ids)
                ).all()
            ]
            text_analysis_count = len(analysis_ids)

            if analysis_ids:
                for row in (
                    db.session.query(
                        ComplianceFinding.severity,
                        func.count(ComplianceFinding.id)
                    )
                    .filter(ComplianceFinding.analysis_id.in_(analysis_ids))
                    .group_by(ComplianceFinding.severity)
                    .all()
                ):
                    sev = (row[0] or "Medium").strip()
                    if sev in text_finding_sevs:
                        text_finding_sevs[sev] += row[1]
                    else:
                        text_finding_sevs[sev] = row[1]

                for row in (
                    db.session.query(
                        ComplianceFinding.category,
                        func.count(ComplianceFinding.id)
                    )
                    .filter(ComplianceFinding.analysis_id.in_(analysis_ids))
                    .group_by(ComplianceFinding.category)
                    .all()
                ):
                    text_cat_dist[row[0] or "Other"] = text_cat_dist.get(row[0] or "Other", 0) + row[1]

                for row in (
                    db.session.query(
                        ComplianceFinding.category,
                        ComplianceFinding.problematic_text,
                        ComplianceFinding.severity,
                        func.count(ComplianceFinding.id).label("freq")
                    )
                    .filter(ComplianceFinding.analysis_id.in_(analysis_ids))
                    .group_by(
                        ComplianceFinding.problematic_text,
                        ComplianceFinding.category,
                        ComplianceFinding.severity
                    )
                    .order_by(func.count(ComplianceFinding.id).desc())
                    .limit(10)
                    .all()
                ):
                    text_common_issues.append({
                        "source": "Text Compliance",
                        "category": row[0] or "Other",
                        "text": row[1][:80] + "..." if len(row[1]) > 80 else row[1],
                        "severity": row[2] or "Medium",
                        "frequency": row[3],
                    })

        # Manager review decisions
        decision_counts = {}
        if submission_ids:
            for row in (
                db.session.query(ReviewDecision.decision, func.count(ReviewDecision.id))
                .filter(ReviewDecision.submission_id.in_(submission_ids))
                .group_by(ReviewDecision.decision)
                .all()
            ):
                decision_counts[row[0]] = row[1]

        # Turnaround: days from submission created_at to first approval decision
        turnaround_days = []
        if submission_ids:
            decisions = ReviewDecision.query.filter(
                ReviewDecision.submission_id.in_(submission_ids),
                ReviewDecision.decision.in_(["Approved", "Rejected"])
            ).all()
            sub_created = {s.id: s.created_at for s in submissions}
            for d in decisions:
                created = sub_created.get(d.submission_id)
                if created and d.created_at:
                    created_utc = created.replace(tzinfo=timezone.utc) if created.tzinfo is None else created
                    decided_utc = d.created_at.replace(tzinfo=timezone.utc) if d.created_at.tzinfo is None else d.created_at
                    delta = (decided_utc - created_utc).total_seconds() / 86400
                    if 0 <= delta <= 365:
                        turnaround_days.append(delta)
        avg_turnaround = round(sum(turnaround_days) / len(turnaround_days), 1) if turnaround_days else None

        # ── Visual compliance reviews ──────────────────────────────────────────
        vis_q = VisualComplianceAnalysis.query.filter(
            VisualComplianceAnalysis.brand_id.in_(target_brand_ids)
        )
        if cutoff:
            vis_q = vis_q.filter(VisualComplianceAnalysis.created_at >= cutoff)
        visual_analyses = vis_q.all()
        visual_ids = [v.id for v in visual_analyses]

        vis_status_counts = {"Compliant": 0, "Action Required": 0, "Violations Detected": 0}
        vis_finding_sevs = {"High": 0, "Medium": 0, "Low": 0, "Unable to Verify": 0}
        vis_cat_dist = {}
        avg_vis_score = None
        vis_common_issues = []

        for va in visual_analyses:
            s = va.review_status or "Action Required"
            vis_status_counts[s] = vis_status_counts.get(s, 0) + 1

        if visual_ids:
            for row in (
                db.session.query(
                    VisualComplianceFinding.severity,
                    func.count(VisualComplianceFinding.id)
                )
                .filter(VisualComplianceFinding.analysis_id.in_(visual_ids))
                .group_by(VisualComplianceFinding.severity)
                .all()
            ):
                sev = (row[0] or "Medium").strip()
                vis_finding_sevs[sev] = vis_finding_sevs.get(sev, 0) + row[1]

            for row in (
                db.session.query(
                    VisualComplianceFinding.category,
                    func.count(VisualComplianceFinding.id)
                )
                .filter(VisualComplianceFinding.analysis_id.in_(visual_ids))
                .group_by(VisualComplianceFinding.category)
                .all()
            ):
                vis_cat_dist[row[0] or "Other"] = vis_cat_dist.get(row[0] or "Other", 0) + row[1]

            for row in (
                db.session.query(
                    VisualComplianceFinding.category,
                    VisualComplianceFinding.visual_element,
                    VisualComplianceFinding.severity,
                    func.count(VisualComplianceFinding.id).label("freq")
                )
                .filter(VisualComplianceFinding.analysis_id.in_(visual_ids))
                .group_by(
                    VisualComplianceFinding.visual_element,
                    VisualComplianceFinding.category,
                    VisualComplianceFinding.severity
                )
                .order_by(func.count(VisualComplianceFinding.id).desc())
                .limit(5)
                .all()
            ):
                vis_common_issues.append({
                    "source": "Visual Compliance",
                    "category": row[0] or "Other",
                    "text": row[1][:80] + "..." if len(row[1]) > 80 else row[1],
                    "severity": row[2] or "Medium",
                    "frequency": row[3],
                })

            scored = [v.compliance_score for v in visual_analyses if v.compliance_score is not None]
            avg_vis_score = round(sum(scored) / len(scored)) if scored else None

        # ── Document reviews ───────────────────────────────────────────────────
        doc_q = DocumentReview.query.filter(
            DocumentReview.brand_id.in_(target_brand_ids)
        )
        if cutoff:
            doc_q = doc_q.filter(DocumentReview.created_at >= cutoff)
        doc_reviews = doc_q.all()
        doc_ids = [d.id for d in doc_reviews]

        doc_status_counts = {"Compliant": 0, "Action Required": 0, "Violations Detected": 0}
        doc_finding_sevs = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Unable to Verify": 0}
        doc_cat_dist = {}
        doc_a11y_count = 0
        doc_brand_count = 0
        doc_fmt_dist = {}
        doc_common_issues = []

        for dr in doc_reviews:
            s = dr.review_status or "Action Required"
            doc_status_counts[s] = doc_status_counts.get(s, 0) + 1
            fmt = dr.detected_format or "unknown"
            doc_fmt_dist[fmt] = doc_fmt_dist.get(fmt, 0) + 1

        if doc_ids:
            for row in (
                db.session.query(
                    DocumentReviewFinding.severity,
                    func.count(DocumentReviewFinding.id)
                )
                .filter(DocumentReviewFinding.review_id.in_(doc_ids))
                .group_by(DocumentReviewFinding.severity)
                .all()
            ):
                sev = (row[0] or "Medium").strip()
                doc_finding_sevs[sev] = doc_finding_sevs.get(sev, 0) + row[1]

            for row in (
                db.session.query(
                    DocumentReviewFinding.review_type,
                    func.count(DocumentReviewFinding.id)
                )
                .filter(DocumentReviewFinding.review_id.in_(doc_ids))
                .group_by(DocumentReviewFinding.review_type)
                .all()
            ):
                if row[0] == "Accessibility":
                    doc_a11y_count += row[1]
                else:
                    doc_brand_count += row[1]

            for row in (
                db.session.query(
                    DocumentReviewFinding.category,
                    func.count(DocumentReviewFinding.id)
                )
                .filter(DocumentReviewFinding.review_id.in_(doc_ids))
                .group_by(DocumentReviewFinding.category)
                .all()
            ):
                doc_cat_dist[row[0] or "Other"] = doc_cat_dist.get(row[0] or "Other", 0) + row[1]

            for row in (
                db.session.query(
                    DocumentReviewFinding.category,
                    DocumentReviewFinding.problematic_text,
                    DocumentReviewFinding.severity,
                    func.count(DocumentReviewFinding.id).label("freq")
                )
                .filter(DocumentReviewFinding.review_id.in_(doc_ids))
                .group_by(
                    DocumentReviewFinding.problematic_text,
                    DocumentReviewFinding.category,
                    DocumentReviewFinding.severity
                )
                .order_by(func.count(DocumentReviewFinding.id).desc())
                .limit(5)
                .all()
            ):
                doc_common_issues.append({
                    "source": "Document Review",
                    "category": row[0] or "Other",
                    "text": row[1][:80] + "..." if len(row[1]) > 80 else row[1],
                    "severity": row[2] or "Medium",
                    "frequency": row[3],
                })

        # ── Combined unified totals (no double-counting) ───────────────────────
        combined_sevs = {
            "Critical": (
                text_finding_sevs.get("Critical", 0) +
                doc_finding_sevs.get("Critical", 0)
            ),
            "High": (
                text_finding_sevs.get("High", 0) +
                vis_finding_sevs.get("High", 0) +
                doc_finding_sevs.get("High", 0)
            ),
            "Medium": (
                text_finding_sevs.get("Medium", 0) +
                vis_finding_sevs.get("Medium", 0) +
                doc_finding_sevs.get("Medium", 0)
            ),
            "Low": (
                text_finding_sevs.get("Low", 0) +
                vis_finding_sevs.get("Low", 0) +
                doc_finding_sevs.get("Low", 0)
            ),
            "Unable to Verify": (
                text_finding_sevs.get("Unable to Verify", 0) +
                vis_finding_sevs.get("Unable to Verify", 0) +
                doc_finding_sevs.get("Unable to Verify", 0)
            ),
        }
        total_all_findings = sum(combined_sevs.values())

        # ── Actionable insights (evidence-backed only) ─────────────────────────
        insights = _build_insights(
            submissions=submissions,
            submission_ids=submission_ids,
            decision_counts=decision_counts,
            avg_turnaround=avg_turnaround,
            total_revisions=total_revisions,
            text_cat_dist=text_cat_dist,
            vis_cat_dist=vis_cat_dist,
            doc_cat_dist=doc_cat_dist,
            doc_a11y_count=doc_a11y_count,
            doc_brand_count=doc_brand_count,
            vis_analyses=visual_analyses,
            combined_sevs=combined_sevs,
        )

        # ── Timeline trends (all review types combined) ────────────────────────
        timeline_trends = _build_timeline(submissions, visual_analyses, doc_reviews)

        # ── Guideline health ───────────────────────────────────────────────────
        guidelines_q = BrandGuideline.query.filter(BrandGuideline.brand_id.in_(target_brand_ids))
        total_guidelines = guidelines_q.count()
        active_guidelines = guidelines_q.filter_by(is_active=True).count()

        return {
            # Per-review-type counts
            "review_counts": {
                "text_compliance_analyses": text_analysis_count,
                "visual_compliance_analyses": len(visual_analyses),
                "document_reviews": len(doc_reviews),
                "total_reviews": text_analysis_count + len(visual_analyses) + len(doc_reviews),
            },
            # Submission metrics
            "submission_metrics": {
                "total": len(submissions),
                "draft": status_counts.get("Draft", 0),
                "pending_approval": status_counts.get("Pending Manager Approval", 0),
                "changes_requested": status_counts.get("Changes Requested", 0),
                "approved": status_counts.get("Approved", 0),
                "published": status_counts.get("Published", 0),
                "avg_revisions": avg_revisions,
                "avg_turnaround_days": avg_turnaround,
            },
            # Visual compliance metrics
            "visual_metrics": {
                "total": len(visual_analyses),
                "compliant": vis_status_counts.get("Compliant", 0),
                "action_required": vis_status_counts.get("Action Required", 0),
                "violations": vis_status_counts.get("Violations Detected", 0),
                "avg_compliance_score": avg_vis_score,
                "finding_severity": vis_finding_sevs,
                "category_distribution": [
                    {"category": k, "count": v}
                    for k, v in sorted(vis_cat_dist.items(), key=lambda x: -x[1])
                ],
            },
            # Document review metrics
            "document_metrics": {
                "total": len(doc_reviews),
                "compliant": doc_status_counts.get("Compliant", 0),
                "action_required": doc_status_counts.get("Action Required", 0),
                "violations": doc_status_counts.get("Violations Detected", 0),
                "accessibility_findings": doc_a11y_count,
                "brand_compliance_findings": doc_brand_count,
                "format_distribution": [
                    {"format": k, "count": v}
                    for k, v in sorted(doc_fmt_dist.items(), key=lambda x: -x[1])
                ],
                "finding_severity": doc_finding_sevs,
                "category_distribution": [
                    {"category": k, "count": v}
                    for k, v in sorted(doc_cat_dist.items(), key=lambda x: -x[1])
                ],
            },
            # Combined unified severities (no double-counting)
            "combined_severity": combined_sevs,
            "total_findings": total_all_findings,
            # Common recurring issues across all sources
            "recurring_issues": sorted(
                text_common_issues + vis_common_issues + doc_common_issues,
                key=lambda x: -x["frequency"]
            )[:12],
            # Actionable insights
            "insights": insights,
            # Timeline
            "timeline_trends": timeline_trends,
            # Manager decisions
            "decision_distribution": [
                {"decision": k, "count": v}
                for k, v in sorted(decision_counts.items(), key=lambda x: -x[1])
            ],
            # Guideline health
            "guideline_health": {
                "total": total_guidelines,
                "active": active_guidelines,
                "inactive": total_guidelines - active_guidelines,
            },
            # Filter metadata
            "brands": [{"id": b["id"], "name": b["name"]} for b in accessible_brands],
            "applied_filters": {
                "brand_id": str(brand_id) if brand_id is not None else None,
                "days": str(days) if days is not None else None,
            },
            "methodology_note": (
                "All metrics are aggregated directly from live database records. "
                "Text compliance, visual compliance, and document review findings are "
                "counted separately to avoid double-counting. "
                "Insights are generated from observed patterns only — no invented statistics. "
                "Turnaround metrics require both a submission timestamp and a manager decision timestamp."
            ),
        }, None, 200

    # ─── New: Creator Insights ─────────────────────────────────────────────────
    @staticmethod
    def get_creator_insights(user_id, role, brand_id=None, days=None):
        """
        Per-creator compliance breakdown (admin/manager only).

        Returns:
          - List of creators with brand access, each containing:
            - total submissions (scoped to brand + date filter)
            - approved / published / changes_requested counts
            - total text compliance findings (from ComplianceFinding)
            - avg findings per submission that was analysed
            - most frequent violation category
            - whether data is sufficient for pattern detection (≥ 5 submissions)
          - Applied filters echoed back
          - brands list for UI filter

        Access: Admin only — never exposes private user data beyond
        aggregated, role-scoped counts.
        """
        if role != "admin":
            return None, "Creator insights are available to Brand Managers only.", 403

        # ── Validate params ────────────────────────────────────────────────────
        cutoff = None
        if days is not None and days != "":
            try:
                days_int = int(days)
                if days_int <= 0:
                    return None, "days parameter must be a positive integer.", 400
                cutoff = datetime.now(timezone.utc) - timedelta(days=days_int)
            except (ValueError, TypeError):
                return None, "Invalid days parameter. Must be a positive integer.", 400

        # Validate brand_id format early (before any DB lookup)
        if brand_id:
            try:
                int(brand_id)
            except (ValueError, TypeError):
                return None, "Invalid brand_id parameter.", 400

        # ── Brand scoping ──────────────────────────────────────────────────────
        accessible_brands = BrandService.get_accessible_brands(user_id, role)
        accessible_brand_ids = [b["id"] for b in accessible_brands]

        if not accessible_brand_ids:
            return {
                "creator_insights": [],
                "brands": [],
                "applied_filters": {
                    "brand_id": str(brand_id) if brand_id is not None else None,
                    "days": str(days) if days is not None else None,
                },
                "methodology_note": "No accessible brands found for this session.",
            }, None, 200

        target_brand_ids = accessible_brand_ids
        if brand_id:
            b_id = int(brand_id)  # already validated above
            if b_id not in accessible_brand_ids:
                return None, "Access denied to the specified brand analytics.", 403
            target_brand_ids = [b_id]

        # ── Fetch all submissions in scope ─────────────────────────────────────
        subs_q = ContentSubmission.query.filter(
            ContentSubmission.brand_id.in_(target_brand_ids)
        )
        if cutoff:
            subs_q = subs_q.filter(ContentSubmission.created_at >= cutoff)
        all_submissions = subs_q.all()

        if not all_submissions:
            return {
                "creator_insights": [],
                "brands": [{
                    "id": b["id"], "name": b["name"]
                } for b in accessible_brands],
                "applied_filters": {
                    "brand_id": str(brand_id) if brand_id is not None else None,
                    "days": str(days) if days is not None else None,
                },
                "methodology_note": (
                    "No submissions found in the selected period and brand scope. "
                    "Creator insights require at least one submission."
                ),
            }, None, 200

        # ── Group submissions by creator ───────────────────────────────────────
        from collections import defaultdict
        creator_subs = defaultdict(list)
        for s in all_submissions:
            creator_subs[s.creator_id].append(s)

        # Pre-fetch all analysis IDs for submissions in scope
        all_sub_ids = [s.id for s in all_submissions]
        analyses = ComplianceAnalysis.query.filter(
            ComplianceAnalysis.submission_id.in_(all_sub_ids)
        ).all()
        analysis_by_sub = defaultdict(list)
        for a in analyses:
            analysis_by_sub[a.submission_id].append(a)

        # Pre-fetch finding categories for all analyses in scope
        all_analysis_ids = [a.id for a in analyses]
        finding_cats = {}  # analysis_id → [category, ...]
        if all_analysis_ids:
            for row in (
                db.session.query(
                    ComplianceFinding.analysis_id,
                    ComplianceFinding.category,
                    func.count(ComplianceFinding.id)
                )
                .filter(ComplianceFinding.analysis_id.in_(all_analysis_ids))
                .group_by(ComplianceFinding.analysis_id, ComplianceFinding.category)
                .all()
            ):
                if row[0] not in finding_cats:
                    finding_cats[row[0]] = {}
                finding_cats[row[0]][row[1]] = row[2]

        # Fetch usernames for creators
        creator_ids = list(creator_subs.keys())
        from app.models.user import User
        users = {u.id: u for u in User.query.filter(User.id.in_(creator_ids)).all()}

        # ── Per-creator aggregation ────────────────────────────────────────────
        creator_results = []
        for creator_id, subs in creator_subs.items():
            user = users.get(creator_id)
            total = len(subs)
            approved = sum(1 for s in subs if s.status in ("Approved", "Published"))
            published = sum(1 for s in subs if s.status == "Published")
            changes_req = sum(1 for s in subs if s.status == "Changes Requested")
            pending = sum(1 for s in subs if s.status == "Pending Manager Approval")

            # Text compliance findings for this creator's submissions
            creator_analyses = []
            for s in subs:
                creator_analyses.extend(analysis_by_sub[s.id])
            total_findings = 0
            cat_totals = defaultdict(int)
            for a in creator_analyses:
                for cat, cnt in finding_cats.get(a.id, {}).items():
                    total_findings += cnt
                    cat_totals[cat] += cnt

            analysed = len(creator_analyses)
            avg_findings = round(total_findings / analysed, 1) if analysed > 0 else None
            top_category = max(cat_totals, key=cat_totals.get) if cat_totals else None

            # Compliance rate: submissions approved or published out of total decided
            total_decided = approved + changes_req
            compliance_rate = round((approved / total_decided) * 100) if total_decided > 0 else None

            sufficient_data = total >= 5

            creator_results.append({
                "creator_id": creator_id,
                "creator_name": (user.full_name or user.username) if user else f"User#{creator_id}",
                "creator_username": user.username if user else None,
                "total_submissions": total,
                "approved_or_published": approved,
                "published": published,
                "changes_requested": changes_req,
                "pending_approval": pending,
                "compliance_rate": compliance_rate,
                "total_text_findings": total_findings,
                "avg_findings_per_analysis": avg_findings,
                "top_violation_category": top_category,
                "sufficient_data": sufficient_data,
                "data_note": (
                    None if sufficient_data
                    else f"Only {total} submission(s) — patterns require ≥ 5 for reliability."
                ),
            })

        # Sort by most submissions (descending) so busiest creators appear first
        creator_results.sort(key=lambda x: -x["total_submissions"])

        return {
            "creator_insights": creator_results,
            "total_creators": len(creator_results),
            "brands": [{"id": b["id"], "name": b["name"]} for b in accessible_brands],
            "applied_filters": {
                "brand_id": str(brand_id) if brand_id is not None else None,
                "days": str(days) if days is not None else None,
            },
            "methodology_note": (
                "Creator compliance scores are derived from manager approval outcomes recorded in the database. "
                "They reflect AI analysis results, which may be imperfect. "
                "Treat as guidance for training prioritisation, not performance evaluation. "
                "Patterns require ≥ 5 submissions per creator for statistical reliability."
            ),
        }, None, 200

    # ─── New: Guideline Effectiveness ─────────────────────────────────────────
    @staticmethod
    def get_guideline_effectiveness(user_id, role, brand_id=None, days=None):
        """
        Per-guideline effectiveness signals from real ComplianceFinding data.

        For each active brand guideline in scope, returns:
          - How many distinct analyses referenced it (via ComplianceFinding.guideline_id)
          - Total finding count citing it
          - Violation rate = findings / total_analyses_in_scope
          - Signal classification: 'High-Impact', 'Active', 'Low-Signal', or 'No-Signal'
          - Severity of the guideline itself

        Access: Admin only.
        """
        if role != "admin":
            return None, "Guideline effectiveness is available to Brand Managers only.", 403

        # ── Validate params ────────────────────────────────────────────────────
        cutoff = None
        if days is not None and days != "":
            try:
                days_int = int(days)
                if days_int <= 0:
                    return None, "days parameter must be a positive integer.", 400
                cutoff = datetime.now(timezone.utc) - timedelta(days=days_int)
            except (ValueError, TypeError):
                return None, "Invalid days parameter. Must be a positive integer.", 400

        # Validate brand_id format early (before any DB lookup)
        if brand_id:
            try:
                int(brand_id)
            except (ValueError, TypeError):
                return None, "Invalid brand_id parameter.", 400

        # ── Brand scoping ──────────────────────────────────────────────────────
        accessible_brands = BrandService.get_accessible_brands(user_id, role)
        accessible_brand_ids = [b["id"] for b in accessible_brands]

        if not accessible_brand_ids:
            return {
                "guidelines": [],
                "summary": {"total": 0, "high_impact": 0, "low_signal": 0, "no_signal": 0, "active": 0},
                "total_analyses_in_scope": 0,
                "brands": [],
                "applied_filters": {
                    "brand_id": str(brand_id) if brand_id is not None else None,
                    "days": str(days) if days is not None else None,
                },
                "methodology_note": "No accessible brands found for this session.",
            }, None, 200

        target_brand_ids = accessible_brand_ids
        if brand_id:
            b_id = int(brand_id)  # already validated above
            if b_id not in accessible_brand_ids:
                return None, "Access denied to the specified brand analytics.", 403
            target_brand_ids = [b_id]

        # ── Count total analyses in scope (for violation-rate denominator) ─────
        subs_q = ContentSubmission.query.filter(
            ContentSubmission.brand_id.in_(target_brand_ids)
        )
        if cutoff:
            subs_q = subs_q.filter(ContentSubmission.created_at >= cutoff)
        submission_ids = [s.id for s in subs_q.all()]

        total_analyses = 0
        analysis_ids = []
        if submission_ids:
            analyses = ComplianceAnalysis.query.filter(
                ComplianceAnalysis.submission_id.in_(submission_ids)
            ).all()
            total_analyses = len(analyses)
            analysis_ids = [a.id for a in analyses]

        # ── Fetch all active guidelines in scope ───────────────────────────────
        guidelines = BrandGuideline.query.filter(
            BrandGuideline.brand_id.in_(target_brand_ids),
            BrandGuideline.is_active == True,
        ).order_by(BrandGuideline.brand_id, BrandGuideline.category).all()

        if not guidelines:
            return {
                "guidelines": [],
                "summary": {"total": 0, "high_impact": 0, "low_signal": 0, "no_signal": 0},
                "brands": [{"id": b["id"], "name": b["name"]} for b in accessible_brands],
                "applied_filters": {
                    "brand_id": str(brand_id) if brand_id is not None else None,
                    "days": str(days) if days is not None else None,
                },
                "methodology_note": "No active guidelines found in the selected scope.",
            }, None, 200

        guideline_ids = [g.id for g in guidelines]

        # ── Count findings per guideline ───────────────────────────────────────
        finding_counts = {}       # guideline_id → total findings
        analysis_counts = {}      # guideline_id → distinct analyses referencing it
        if analysis_ids:
            for row in (
                db.session.query(
                    ComplianceFinding.guideline_id,
                    func.count(ComplianceFinding.id).label("finding_cnt"),
                    func.count(func.distinct(ComplianceFinding.analysis_id)).label("analysis_cnt")
                )
                .filter(
                    ComplianceFinding.guideline_id.in_(guideline_ids),
                    ComplianceFinding.analysis_id.in_(analysis_ids)
                )
                .group_by(ComplianceFinding.guideline_id)
                .all()
            ):
                finding_counts[row[0]] = row[1]
                analysis_counts[row[0]] = row[2]

        # ── Compute per-guideline signals ──────────────────────────────────────
        result_guidelines = []
        summary = {"total": 0, "high_impact": 0, "low_signal": 0, "no_signal": 0, "active": 0}

        for g in guidelines:
            fc = finding_counts.get(g.id, 0)
            ac = analysis_counts.get(g.id, 0)
            violation_rate = round((ac / total_analyses) * 100) if total_analyses > 0 else None

            # Signal classification
            if fc == 0:
                signal = "No-Signal"
                summary["no_signal"] += 1
            elif total_analyses > 0 and ac / total_analyses >= 0.5:
                signal = "High-Impact"
                summary["high_impact"] += 1
            elif fc <= 1 and total_analyses >= 5:
                signal = "Low-Signal"
                summary["low_signal"] += 1
            else:
                signal = "Active"
                summary["active"] += 1

            summary["total"] += 1
            result_guidelines.append({
                "guideline_id": g.id,
                "brand_id": g.brand_id,
                "title": g.title,
                "category": g.category,
                "severity": g.severity,
                "rule_content": g.rule_content[:120] + "…" if len(g.rule_content) > 120 else g.rule_content,
                "total_findings": fc,
                "analyses_referencing": ac,
                "violation_rate_pct": violation_rate,
                "signal": signal,
            })

        # Sort: High-Impact first, then Active, then Low-Signal, then No-Signal
        signal_order = {"High-Impact": 0, "Active": 1, "Low-Signal": 2, "No-Signal": 3}
        result_guidelines.sort(key=lambda x: (signal_order.get(x["signal"], 9), -x["total_findings"]))

        return {
            "guidelines": result_guidelines,
            "summary": summary,
            "total_analyses_in_scope": total_analyses,
            "brands": [{"id": b["id"], "name": b["name"]} for b in accessible_brands],
            "applied_filters": {
                "brand_id": str(brand_id) if brand_id is not None else None,
                "days": str(days) if days is not None else None,
            },
            "methodology_note": (
                "Violation rate = % of text compliance analyses in scope that produced a finding citing that guideline. "
                "A 'No-Signal' guideline may be too vague, not relevant to recent campaigns, or genuinely well-followed. "
                "A 'High-Impact' guideline (cited in ≥50% of analyses) warrants review for clarity and specificity. "
                "Only active guidelines and text compliance findings are counted here."
            ),
        }, None, 200


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _empty_intelligence_response(accessible_brands, brand_id=None, days=None):
    return {
        "review_counts": {
            "text_compliance_analyses": 0,
            "visual_compliance_analyses": 0,
            "document_reviews": 0,
            "total_reviews": 0,
        },
        "submission_metrics": {
            "total": 0, "draft": 0, "pending_approval": 0,
            "changes_requested": 0, "approved": 0, "published": 0,
            "avg_revisions": 0.0, "avg_turnaround_days": None,
        },
        "visual_metrics": {
            "total": 0, "compliant": 0, "action_required": 0, "violations": 0,
            "avg_compliance_score": None,
            "finding_severity": {"High": 0, "Medium": 0, "Low": 0, "Unable to Verify": 0},
            "category_distribution": [],
        },
        "document_metrics": {
            "total": 0, "compliant": 0, "action_required": 0, "violations": 0,
            "accessibility_findings": 0, "brand_compliance_findings": 0,
            "format_distribution": [], "finding_severity": {}, "category_distribution": [],
        },
        "combined_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Unable to Verify": 0},
        "total_findings": 0,
        "recurring_issues": [],
        "insights": [],
        "timeline_trends": [],
        "decision_distribution": [],
        "guideline_health": {"total": 0, "active": 0, "inactive": 0},
        "brands": [{"id": b["id"], "name": b["name"]} for b in accessible_brands],
        "applied_filters": {
            "brand_id": str(brand_id) if brand_id is not None else None,
            "days": str(days) if days is not None else None,
        },
        "methodology_note": "No accessible brands or data found for the current session.",
    }


def _build_insights(
    submissions, submission_ids, decision_counts,
    avg_turnaround, total_revisions,
    text_cat_dist, vis_cat_dist, doc_cat_dist, doc_a11y_count, doc_brand_count,
    vis_analyses, combined_sevs,
):
    """
    Build actionable insights strictly from observed data patterns.
    Each insight includes evidence counts so the frontend can show backing data.
    Never fabricates statistics.
    """
    insights = []
    total_subs = len(submissions)

    # 1. High revision rate
    if total_subs >= 3 and total_revisions > 0:
        avg_rev = total_revisions / total_subs
        if avg_rev >= 2.0:
            insights.append({
                "type": "warning",
                "title": "High Revision Rate Detected",
                "description": (
                    f"Submissions are averaging {avg_rev:.1f} revisions each across {total_subs} "
                    f"recorded submissions. This suggests recurring compliance issues are being "
                    f"caught late in the workflow."
                ),
                "recommendation": "Provide creators with guideline summaries before drafting to reduce revision cycles.",
                "evidence": f"{total_revisions} revisions across {total_subs} submissions",
                "metric": round(avg_rev, 1),
                "metric_label": "avg revisions/submission",
            })

    # 2. Most violated text compliance category
    if text_cat_dist:
        top_cat, top_count = max(text_cat_dist.items(), key=lambda x: x[1])
        total_text = sum(text_cat_dist.values())
        if total_text >= 3:
            pct = round((top_count / total_text) * 100)
            insights.append({
                "type": "info",
                "title": f"Recurring Brand Compliance Issue: {top_cat}",
                "description": (
                    f"'{top_cat}' violations represent {pct}% of all text compliance findings "
                    f"({top_count} of {total_text} total findings)."
                ),
                "recommendation": f"Schedule a team review of the '{top_cat}' brand guideline rules to reduce recurring violations.",
                "evidence": f"{top_count} '{top_cat}' findings from text compliance analyses",
                "metric": top_count,
                "metric_label": "findings in top category",
            })

    # 3. High rejection rate
    rejected = decision_counts.get("Rejected", 0) + decision_counts.get("Changes Requested", 0)
    approved = decision_counts.get("Approved", 0)
    total_decided = rejected + approved
    if total_decided >= 3 and rejected > 0:
        rejection_pct = round((rejected / total_decided) * 100)
        if rejection_pct >= 40:
            insights.append({
                "type": "warning",
                "title": "Elevated Rejection / Change Rate",
                "description": (
                    f"{rejection_pct}% of reviewed submissions required changes or were rejected "
                    f"({rejected} of {total_decided} manager decisions)."
                ),
                "recommendation": "Consider adding a mandatory AI pre-check step before submissions enter the manager queue.",
                "evidence": f"{rejected} rejections/change requests, {approved} approvals",
                "metric": rejection_pct,
                "metric_label": "% requiring changes",
            })

    # 4. Slow turnaround
    if avg_turnaround is not None and avg_turnaround >= 3:
        insights.append({
            "type": "info",
            "title": "Manager Review Turnaround is Slow",
            "description": (
                f"Average time from submission to manager decision is {avg_turnaround} days. "
                f"Long review cycles can delay publishing timelines."
            ),
            "recommendation": "Set SLA targets for manager reviews and send automated reminders for items pending > 2 days.",
            "evidence": f"{avg_turnaround} day average turnaround from submission to decision",
            "metric": avg_turnaround,
            "metric_label": "avg days to decision",
        })

    # 5. Visual compliance score warning
    if vis_analyses:
        scored = [v.compliance_score for v in vis_analyses if v.compliance_score is not None]
        if scored:
            avg_score = round(sum(scored) / len(scored))
            if avg_score < 70:
                insights.append({
                    "type": "warning",
                    "title": "Low Average Visual Compliance Score",
                    "description": (
                        f"Across {len(scored)} scored image analyses, the average visual compliance "
                        f"score is {avg_score}/100. This indicates frequent visual guideline deviations."
                    ),
                    "recommendation": "Distribute visual brand guidelines (logo, colour palette, typography) to design teams.",
                    "evidence": f"{len(scored)} visual analyses scored, avg {avg_score}/100",
                    "metric": avg_score,
                    "metric_label": "avg visual compliance score",
                })

    # 6. Top visual compliance category
    if vis_cat_dist:
        top_vis_cat, top_vis_count = max(vis_cat_dist.items(), key=lambda x: x[1])
        total_vis = sum(vis_cat_dist.values())
        if total_vis >= 3:
            insights.append({
                "type": "info",
                "title": f"Most Frequent Visual Finding: {top_vis_cat}",
                "description": (
                    f"'{top_vis_cat}' is the most commonly flagged visual compliance area "
                    f"({top_vis_count} of {total_vis} visual findings)."
                ),
                "recommendation": f"Add specific '{top_vis_cat}' rules to your brand guidelines with visual examples.",
                "evidence": f"{top_vis_count} '{top_vis_cat}' findings in visual analyses",
                "metric": top_vis_count,
                "metric_label": "visual findings in top category",
            })

    # 7. Accessibility issues in documents
    total_doc = doc_a11y_count + doc_brand_count
    if total_doc >= 3 and doc_a11y_count > 0:
        a11y_pct = round((doc_a11y_count / total_doc) * 100)
        insights.append({
            "type": "info",
            "title": "Document Accessibility Issues Detected",
            "description": (
                f"{a11y_pct}% of document review findings relate to accessibility issues "
                f"({doc_a11y_count} of {total_doc} findings). These are often fixable with "
                f"plain-language and structural improvements."
            ),
            "recommendation": "Adopt a plain-language writing guide and ensure headings are structured consistently in brand documents.",
            "evidence": f"{doc_a11y_count} accessibility findings from document reviews",
            "metric": doc_a11y_count,
            "metric_label": "accessibility findings in documents",
        })

    # 8. High-severity concentration
    critical_high = combined_sevs.get("Critical", 0) + combined_sevs.get("High", 0)
    total_combined = sum(combined_sevs.values())
    if total_combined >= 5 and critical_high > 0:
        ch_pct = round((critical_high / total_combined) * 100)
        if ch_pct >= 30:
            insights.append({
                "type": "critical",
                "title": "High Concentration of Critical/High Severity Findings",
                "description": (
                    f"{ch_pct}% of all findings across all review types are Critical or High severity "
                    f"({critical_high} of {total_combined} total). These require immediate action."
                ),
                "recommendation": "Prioritize resolving Critical and High severity findings before new content is submitted for approval.",
                "evidence": f"{critical_high} Critical/High findings of {total_combined} total across all review types",
                "metric": ch_pct,
                "metric_label": "% Critical/High severity",
            })

    return insights


def _build_timeline(submissions, visual_analyses, doc_reviews):
    """Build a unified per-day activity timeline across all review types."""
    date_map = {}

    for s in submissions:
        if s.created_at:
            dt = s.created_at.strftime("%Y-%m-%d")
            if dt not in date_map:
                date_map[dt] = {"date": dt, "text_submissions": 0, "visual_reviews": 0, "doc_reviews": 0, "total": 0}
            date_map[dt]["text_submissions"] += 1
            date_map[dt]["total"] += 1

    for va in visual_analyses:
        if va.created_at:
            dt = va.created_at.strftime("%Y-%m-%d")
            if dt not in date_map:
                date_map[dt] = {"date": dt, "text_submissions": 0, "visual_reviews": 0, "doc_reviews": 0, "total": 0}
            date_map[dt]["visual_reviews"] += 1
            date_map[dt]["total"] += 1

    for dr in doc_reviews:
        if dr.created_at:
            dt = dr.created_at.strftime("%Y-%m-%d")
            if dt not in date_map:
                date_map[dt] = {"date": dt, "text_submissions": 0, "visual_reviews": 0, "doc_reviews": 0, "total": 0}
            date_map[dt]["doc_reviews"] += 1
            date_map[dt]["total"] += 1

    return sorted(date_map.values(), key=lambda x: x["date"])[-14:]
