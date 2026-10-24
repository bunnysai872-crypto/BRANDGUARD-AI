from datetime import datetime, timezone
from app.models import db

SUBMISSION_STATUSES = [
    "Draft",
    "Ready for AI Review",
    "AI Reviewed",
    "Changes Requested",
    "Pending Manager Approval",
    "Approved",
    "Published"
]

class ContentSubmission(db.Model):
    __tablename__ = "content_submissions"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content_text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Draft", nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    published_at = db.Column(db.DateTime, nullable=True)
    published_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Relationships
    creator = db.relationship("User", foreign_keys=[creator_id], backref="submissions")
    publisher = db.relationship("User", foreign_keys=[published_by_id])
    revisions = db.relationship(
        "ContentRevision",
        backref="submission",
        cascade="all, delete-orphan",
        order_by="ContentRevision.revision_number.desc()"
    )
    analyses = db.relationship(
        "ComplianceAnalysis",
        backref="submission",
        cascade="all, delete-orphan",
        order_by="ComplianceAnalysis.created_at.desc()"
    )
    decisions = db.relationship(
        "ReviewDecision",
        backref="submission",
        cascade="all, delete-orphan",
        order_by="ReviewDecision.created_at.desc()"
    )

    def to_dict(self, include_revisions=False, include_decisions=False):
        data = {
            "id": self.id,
            "creator_id": self.creator_id,
            "creator_name": self.creator.full_name or self.creator.username if self.creator else None,
            "brand_id": self.brand_id,
            "brand_name": self.brand.name if self.brand else None,
            "title": self.title,
            "content_text": self.content_text,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "published_by_id": self.published_by_id,
            "published_by": self.publisher.full_name or self.publisher.username if self.publisher else None,
            "revision_count": len(self.revisions),
            "decision_count": len(self.decisions),
        }
        if include_revisions:
            data["revisions"] = [rev.to_dict() for rev in self.revisions]
        if include_decisions:
            data["decisions"] = [d.to_dict() for d in self.decisions]
        return data

    def __repr__(self):
        return f"<ContentSubmission id={self.id} title='{self.title}' status='{self.status}'>"


class ContentRevision(db.Model):
    __tablename__ = "content_revisions"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey("content_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    revision_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_text = db.Column(db.Text, nullable=False)
    reason = db.Column(db.String(255), nullable=True) # e.g., 'Initial draft', 'Addressed terminology flag'
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    editor = db.relationship("User", foreign_keys=[created_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "revision_number": self.revision_number,
            "title": self.title,
            "content_text": self.content_text,
            "reason": self.reason or "",
            "created_by_id": self.created_by_id,
            "created_by": self.editor.full_name or self.editor.username if self.editor else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ContentRevision id={self.id} sub_id={self.submission_id} rev={self.revision_number}>"
