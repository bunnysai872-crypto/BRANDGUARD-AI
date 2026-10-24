from datetime import datetime, timezone
from app.models import db

GUIDELINE_CATEGORIES = [
    "Tone",
    "Terminology",
    "Messaging",
    "Approved Facts",
    "Prohibited Claims",
    "Restricted Claims",
    "Mandatory Disclaimer",
    "Visual Identity",
    "Accessibility",
    "Other"
]

GUIDELINE_SEVERITIES = ["Low", "Medium", "High", "Critical"]

class BrandGuideline(db.Model):
    __tablename__ = "brand_guidelines"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    rule_content = db.Column(db.Text, nullable=False)
    approved_wording = db.Column(db.Text, nullable=True)
    prohibited_wording = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), default="Medium", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    reference_evidence = db.Column(db.Text, nullable=True) # Optional evidence or verified source
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "category": self.category,
            "title": self.title,
            "rule_content": self.rule_content,
            "approved_wording": self.approved_wording or "",
            "prohibited_wording": self.prohibited_wording or "",
            "severity": self.severity or "Medium",
            "is_active": self.is_active if self.is_active is not None else True,
            "reference_evidence": self.reference_evidence or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<BrandGuideline id={self.id} brand_id={self.brand_id} category='{self.category}' title='{self.title}'>"
