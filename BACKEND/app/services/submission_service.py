from app.models import db, ContentSubmission, ContentRevision, SUBMISSION_STATUSES, Brand
from app.services.brand_service import BrandService

class SubmissionService:
    @staticmethod
    def create_submission(creator_id, data):
        brand_id = data.get("brand_id")
        if not brand_id:
            return None, "Brand ID is required.", 400

        # Verify brand access
        brand = db.session.get(Brand, brand_id)
        if not brand:
            return None, "Selected brand does not exist.", 404

        title = (data.get("title") or "").strip()
        if not title:
            return None, "Submission title is required.", 400

        content_text = (data.get("content_text") or "").strip()
        if not content_text:
            return None, "Submission content text cannot be empty.", 400

        status = data.get("status", "Draft")
        # Ensure creator cannot manually forge AI Reviewed, Approved, or Published
        if status in ["AI Reviewed", "Approved", "Published"]:
            status = "Draft"
        elif status not in SUBMISSION_STATUSES:
            status = "Draft"

        submission = ContentSubmission(
            creator_id=creator_id,
            brand_id=brand_id,
            title=title,
            content_text=content_text,
            status=status
        )
        db.session.add(submission)
        db.session.flush()

        # Create initial revision #1
        initial_revision = ContentRevision(
            submission_id=submission.id,
            revision_number=1,
            title=title,
            content_text=content_text,
            reason=(data.get("reason") or "Initial draft").strip(),
            created_by_id=creator_id
        )
        db.session.add(initial_revision)
        db.session.commit()

        return submission.to_dict(include_revisions=True), None, 201

    @staticmethod
    def get_accessible_submissions(user_id, role, brand_id=None, status=None):
        query = ContentSubmission.query

        if role == "creator":
            query = query.filter_by(creator_id=user_id)
        elif role == "admin":
            # Brand managers see submissions across brands
            pass

        if brand_id:
            query = query.filter_by(brand_id=int(brand_id))

        if status:
            query = query.filter_by(status=status)

        submissions = query.order_by(ContentSubmission.updated_at.desc()).all()
        return [s.to_dict(include_revisions=False) for s in submissions], None, 200

    @staticmethod
    def get_submission_by_id(submission_id):
        return db.session.get(ContentSubmission, submission_id)

    @staticmethod
    def update_submission(submission_id, user_id, role, data):
        submission = db.session.get(ContentSubmission, submission_id)
        if not submission:
            return None, "Submission not found.", 404

        # Enforce authorization: creators can only edit their own submissions
        if role == "creator" and submission.creator_id != user_id:
            return None, "You do not have permission to modify this submission.", 403

        # Prevent editing while approval is pending or approved
        if submission.status == "Pending Manager Approval":
            return None, "Content cannot be edited while manager approval is pending.", 400

        if submission.status == "Approved":
            return None, "Approved content is locked and cannot be edited.", 400

        if submission.status == "Published":
            return None, "Published content is locked and cannot be edited.", 400

        new_title = (data.get("title") or submission.title).strip()
        new_content = (data.get("content_text") or submission.content_text).strip()
        new_status = data.get("status", submission.status)

        if not new_title:
            return None, "Title cannot be empty.", 400
        if not new_content:
            return None, "Content text cannot be empty.", 400

        # Creator status restrictions: creators cannot manually set restricted statuses
        if role == "creator" and "status" in data:
            requested_status = data.get("status")
            if requested_status in ["AI Reviewed", "Approved", "Pending Manager Approval", "Published"]:
                return None, f"Creators cannot manually set status to '{requested_status}'.", 403

        # Check if content or title changed -> snapshot new revision
        content_changed = (new_content != submission.content_text) or (new_title != submission.title)

        # If copy changed on an AI Reviewed or Changes Requested submission, auto-reset to Draft
        if content_changed and submission.status in ["AI Reviewed", "Changes Requested"]:
            new_status = "Draft"

        submission.title = new_title
        submission.content_text = new_content
        submission.status = new_status

        if content_changed:
            # Mark previous analyses as outdated
            for past_analysis in submission.analyses:
                past_analysis.is_outdated = True

            next_rev_num = ContentRevision.query.filter_by(submission_id=submission.id).count() + 1
            reason = (data.get("reason") or f"Revision {next_rev_num} update").strip()
            revision = ContentRevision(
                submission_id=submission.id,
                revision_number=next_rev_num,
                title=new_title,
                content_text=new_content,
                reason=reason,
                created_by_id=user_id
            )
            db.session.add(revision)

        db.session.commit()
        return submission.to_dict(include_revisions=True), None, 200

    @staticmethod
    def get_submission_revisions(submission_id):
        submission = db.session.get(ContentSubmission, submission_id)
        if not submission:
            return None, "Submission not found.", 404
        return [r.to_dict() for r in submission.revisions], None, 200

    @staticmethod
    def publish_submission(submission_id, user_id, role):
        submission = db.session.get(ContentSubmission, submission_id)
        if not submission:
            return None, "Submission not found.", 404

        # Enforce Brand Manager role
        if role != "admin":
            return None, "Only Brand Managers can publish content.", 403

        # Enforce brand management permissions
        if not BrandService.user_has_brand_access(submission.brand_id, user_id, role):
            return None, "You do not have management permissions for this brand.", 403

        # Reject already published submissions
        if submission.status == "Published":
            return None, "This submission has already been published.", 400

        # Reject any status other than Approved
        if submission.status != "Approved":
            return None, f"Cannot publish submission with status '{submission.status}'. Only 'Approved' submissions can be published.", 400

        # Transition status to Published
        from datetime import datetime, timezone
        submission.status = "Published"
        submission.published_at = datetime.now(timezone.utc)
        submission.published_by_id = user_id
        db.session.commit()

        return submission.to_dict(include_revisions=True, include_decisions=True), None, 200
