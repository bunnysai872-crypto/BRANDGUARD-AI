from app.models import (
    db,
    ContentSubmission,
    ReviewDecision,
    ComplianceAnalysis,
    Brand,
    BrandMembership,
    User
)
from app.services.brand_service import BrandService

class ReviewService:
    @staticmethod
    def submit_for_approval(submission_id, user_id, role, acknowledgement=False):
        submission = db.session.get(ContentSubmission, submission_id)
        if not submission:
            return None, "Submission not found.", 404

        # 1. Enforce creator ownership
        if role == "creator" and submission.creator_id != user_id:
            return None, "You can only submit your own content for approval.", 403

        # 2. Check if already pending, approved, or published
        if submission.status == "Pending Manager Approval":
            return None, "This submission is already pending manager approval.", 400
        if submission.status == "Approved":
            return None, "This submission has already been approved.", 400
        if submission.status == "Published":
            return None, "This submission has already been published.", 400

        from app.models import ContentRevision
        current_rev = ContentRevision.query.filter_by(submission_id=submission.id).count() or 1

        # 3. Retrieve latest analysis
        latest_analysis = (
            ComplianceAnalysis.query
            .filter_by(submission_id=submission.id)
            .order_by(ComplianceAnalysis.id.desc())
            .first()
        )

        if not latest_analysis:
            return None, (
                "Content must have a successful AI compliance analysis before submitting for manager approval. "
                "Please run an AI Compliance Check first."
            ), 400

        # Check if analysis is outdated
        is_stale = (current_rev > latest_analysis.revision_number) or latest_analysis.is_outdated
        if is_stale:
            return None, (
                "The current AI compliance report is outdated because content was revised. "
                "Please rerun the AI compliance check on the latest content before submitting for approval."
            ), 400

        # 4. Check for high/critical-severity issues or human verification warnings
        high_issues = [f for f in latest_analysis.findings if f.severity in ["Critical", "High"]]
        human_warnings = [f for f in latest_analysis.findings if f.human_verification_required]

        if (high_issues or human_warnings) and not acknowledgement:
            return {
                "requires_acknowledgement": True,
                "high_issues_count": len(high_issues),
                "human_warnings_count": len(human_warnings),
                "message": (
                    "Content contains high-severity compliance issues or claims requiring human verification. "
                    "Explicit creator acknowledgement is required to submit for manager review."
                )
            }, "Acknowledgement required for high-risk flags.", 422

        # 5. Transition status to Pending Manager Approval
        submission.status = "Pending Manager Approval"
        db.session.commit()

        return submission.to_dict(include_revisions=True, include_decisions=True), None, 200

    @staticmethod
    def get_manager_queue(user_id, role, brand_id=None, status=None):
        if role != "admin":
            return None, "Only Brand Managers can view the approval queue.", 403

        # Get accessible brands
        accessible_brands = BrandService.get_accessible_brands(user_id, role)
        accessible_brand_ids = [b["id"] for b in accessible_brands]

        if not accessible_brand_ids:
            return [], None, 200

        query = ContentSubmission.query.filter(ContentSubmission.brand_id.in_(accessible_brand_ids))

        if brand_id:
            query = query.filter_by(brand_id=int(brand_id))

        if status and status != "All":
            query = query.filter_by(status=status)
        elif not status:
            # Default to showing pending approvals first
            query = query.filter(ContentSubmission.status == "Pending Manager Approval")

        submissions = query.order_by(ContentSubmission.updated_at.desc()).all()

        queue = []
        for s in submissions:
            data = s.to_dict(include_revisions=False, include_decisions=True)
            # Attach latest analysis summary if present
            latest_analysis = (
                ComplianceAnalysis.query
                .filter_by(submission_id=s.id)
                .order_by(ComplianceAnalysis.created_at.desc())
                .first()
            )
            if latest_analysis:
                data["latest_analysis"] = {
                    "id": latest_analysis.id,
                    "review_status": latest_analysis.review_status,
                    "summary": latest_analysis.summary,
                    "issues_count": latest_analysis.issues_count,
                    "high_severity_count": latest_analysis.high_severity_count,
                    "medium_severity_count": latest_analysis.medium_severity_count,
                    "low_severity_count": latest_analysis.low_severity_count,
                    "is_outdated": latest_analysis.is_outdated or (len(s.revisions) > latest_analysis.revision_number)
                }
            queue.append(data)

        return queue, None, 200

    @staticmethod
    def review_submission(submission_id, reviewer_id, role, decision, comments, acknowledgement=False):
        if role != "admin":
            return None, "Only Brand Managers can make review decisions.", 403

        submission = db.session.get(ContentSubmission, submission_id)
        if not submission:
            return None, "Submission not found.", 404

        # Enforce brand access
        if not BrandService.user_has_brand_access(submission.brand_id, reviewer_id, role):
            return None, "You do not have management permissions for this brand.", 403

        if submission.status != "Pending Manager Approval":
            return None, f"Submission is not pending manager approval (current status: '{submission.status}').", 400

        if decision not in ["Approved", "Changes Requested"]:
            return None, "Invalid decision. Must be 'Approved' or 'Changes Requested'.", 400

        clean_comments = (comments or "").strip()
        if not clean_comments or len(clean_comments) < 3:
            return None, "Review comments are required (minimum 3 characters).", 400

        from app.models import ContentRevision
        current_rev = ContentRevision.query.filter_by(submission_id=submission.id).count() or 1

        # Retrieve latest analysis
        latest_analysis = (
            ComplianceAnalysis.query
            .filter_by(submission_id=submission.id)
            .order_by(ComplianceAnalysis.created_at.desc())
            .first()
        )

        # Check if analysis matches exact current revision
        if latest_analysis:
            if current_rev > latest_analysis.revision_number or latest_analysis.is_outdated:
                return None, "Cannot review: content was modified after the latest AI analysis.", 400

        # If approving content with high/critical severity or human verification issues, require manager acknowledgement
        if decision == "Approved" and latest_analysis:
            crit_count = getattr(latest_analysis, 'critical_severity_count', 0)
            has_high = (crit_count > 0) or (latest_analysis.high_severity_count > 0)
            has_human = any(f.human_verification_required for f in latest_analysis.findings)
            if (has_high or has_human) and not acknowledgement:
                return {
                    "requires_acknowledgement": True,
                    "high_issues_count": crit_count + latest_analysis.high_severity_count,
                    "has_unverified_claims": has_human,
                    "message": "Approving content with high-severity issues or unverified claims requires explicit manager acknowledgement."
                }, "Manager acknowledgement required to approve content with compliance warnings.", 422

        # Create immutable ReviewDecision
        review_decision = ReviewDecision(
            submission_id=submission.id,
            reviewer_id=reviewer_id,
            decision=decision,
            review_comments=clean_comments,
            revision_number=current_rev,
            analysis_id=latest_analysis.id if latest_analysis else None
        )
        db.session.add(review_decision)

        # Update submission status
        submission.status = decision
        db.session.commit()

        return {
            "decision": review_decision.to_dict(),
            "submission": submission.to_dict(include_revisions=True, include_decisions=True)
        }, None, 200

    @staticmethod
    def get_decision_history(submission_id, user_id, role):
        submission = db.session.get(ContentSubmission, submission_id)
        if not submission:
            return None, "Submission not found.", 404

        # Access check
        if role == "creator" and submission.creator_id != user_id:
            return None, "Access denied.", 403
        elif role == "admin" and not BrandService.user_has_brand_access(submission.brand_id, user_id, role):
            return None, "Access denied.", 403

        decisions = (
            ReviewDecision.query
            .filter_by(submission_id=submission_id)
            .order_by(ReviewDecision.id.desc())
            .all()
        )
        return [d.to_dict() for d in decisions], None, 200
