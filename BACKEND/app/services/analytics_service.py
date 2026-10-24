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
    BrandGuideline
)
from app.services.brand_service import BrandService

class AnalyticsService:
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
        if days:
            try:
                days_int = int(days)
                cutoff = datetime.now(timezone.utc) - timedelta(days=days_int)
                subs_query = subs_query.filter(ContentSubmission.created_at >= cutoff)
            except (ValueError, TypeError):
                pass

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
            total_revisions = ContentRevision.query.filter(ContentRevision.submission_id.in_(submission_ids)).count()
        avg_revisions = round(total_revisions / total_subs, 2) if total_subs > 0 else 0.0

        # Brand guidelines counts
        guidelines_query = BrandGuideline.query.filter(BrandGuideline.brand_id.in_(target_brand_ids))
        total_guidelines = guidelines_query.count()
        active_guidelines = guidelines_query.filter_by(is_active=True).count()

        # Findings queries
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
                # Category distribution
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

                # Severity distribution
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

                # Common issues (problematic phrases flagged)
                issue_results = (
                    db.session.query(
                        ComplianceFinding.category,
                        ComplianceFinding.problematic_text,
                        ComplianceFinding.severity,
                        func.count(ComplianceFinding.id).label("freq")
                    )
                    .filter(ComplianceFinding.analysis_id.in_(analysis_ids))
                    .group_by(ComplianceFinding.problematic_text, ComplianceFinding.category, ComplianceFinding.severity)
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

        # Recent timeline trends (past 7 distinct submission activity dates)
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
            "governance_note": (
                "Historical compliance analytics are computed directly from active application database records. "
                "Compliance trends and revision frequencies reflect internal governance checkpoints, and historical trends do not necessarily prove causation."
            )
        }, None, 200
