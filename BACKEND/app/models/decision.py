from datetime import datetime, timezone
from app.models import db

DECISION_CHOICES = ["Approved", "Changes Requested"]

class ReviewDecision(db.Model):
    __tablename__ = "review_decisions"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey("content_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reviewer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    decision = db.Column(db.String(50), nullable=False)  # 'Approved' or 'Changes Requested'
    review_comments = db.Column(db.Text, nullable=False)
    revision_number = db.Column(db.Integer, nullable=False)
    analysis_id = db.Column(
        db.Integer,
        db.ForeignKey("compliance_analyses.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reviewer = db.relationship("User", foreign_keys=[reviewer_id])
    analysis = db.relationship("ComplianceAnalysis", foreign_keys=[analysis_id])

    def to_dict(self):
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "reviewer_id": self.reviewer_id,
            "reviewer_name": self.reviewer.full_name or self.reviewer.username if self.reviewer else None,
            "decision": self.decision,
            "review_comments": self.review_comments,
            "revision_number": self.revision_number,
            "analysis_id": self.analysis_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ReviewDecision id={self.id} sub_id={self.submission_id} decision='{self.decision}' rev={self.revision_number}>"
