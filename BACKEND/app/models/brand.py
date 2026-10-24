from datetime import datetime, timezone
from app.models import db

class Brand(db.Model):
    __tablename__ = "brands"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    tone_style = db.Column(db.String(255), nullable=True)
    approved_terminology = db.Column(db.Text, nullable=True)
    restricted_words = db.Column(db.Text, nullable=True)
    approved_facts = db.Column(db.Text, nullable=True)
    prohibited_claims = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by_id], backref="created_brands")
    guidelines = db.relationship("BrandGuideline", backref="brand", cascade="all, delete-orphan", lazy="dynamic")
    memberships = db.relationship("BrandMembership", backref="brand", cascade="all, delete-orphan", lazy="dynamic")
    submissions = db.relationship("ContentSubmission", backref="brand", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self, include_counts=True):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "tone_style": self.tone_style or "",
            "approved_terminology": self.approved_terminology or "",
            "restricted_words": self.restricted_words or "",
            "approved_facts": self.approved_facts or "",
            "prohibited_claims": self.prohibited_claims or "",
            "created_by_id": self.created_by_id,
            "created_by": self.creator.username if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_counts:
            data["guidelines_count"] = self.guidelines.count()
            data["members_count"] = self.memberships.count()
            data["submissions_count"] = self.submissions.count()
        return data

    def __repr__(self):
        return f"<Brand id={self.id} name='{self.name}'>"


class BrandMembership(db.Model):
    __tablename__ = "brand_memberships"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(50), default="contributor", nullable=False) # 'manager', 'contributor'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint("brand_id", "user_id", name="unique_brand_user_membership"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "user_email": self.user.email if self.user else None,
            "user_full_name": self.user.full_name if self.user else None,
            "user_role": self.user.role if self.user else None,
            "membership_role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
