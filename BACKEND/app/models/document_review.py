"""
DocumentReview model — stores multi-format document accessibility & compliance analysis results.
Findings are stored in a separate DocumentReviewFinding table that mirrors ComplianceFinding
structure so frontend components can reuse the same rendering patterns.
"""
from datetime import datetime, timezone
from app.models import db


class DocumentReview(db.Model):
    __tablename__ = "document_reviews"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(
        db.Integer,
        db.ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Document metadata (display only — never used for serving)
    original_filename = db.Column(db.String(255), nullable=False)
    detected_format = db.Column(db.String(20), nullable=False)   # 'txt' | 'pdf' | 'docx'
    file_size_bytes = db.Column(db.Integer, nullable=True)
    extracted_char_count = db.Column(db.Integer, default=0, nullable=False)

    # AI analysis metadata
    model_identifier = db.Column(db.String(100), default="gemini-2.5-flash", nullable=False)

    # Results
    summary = db.Column(db.Text, nullable=False)
    review_status = db.Column(db.String(50), default="Action Required", nullable=False)
    # 'Compliant' | 'Action Required' | 'Violations Detected'

    # Severity counts (brand compliance + accessibility combined)
    issues_count = db.Column(db.Integer, default=0, nullable=False)
    critical_severity_count = db.Column(db.Integer, default=0, nullable=False)
    high_severity_count = db.Column(db.Integer, default=0, nullable=False)
    medium_severity_count = db.Column(db.Integer, default=0, nullable=False)
    low_severity_count = db.Column(db.Integer, default=0, nullable=False)
    unable_to_verify_count = db.Column(db.Integer, default=0, nullable=False)
    has_limitations = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    findings = db.relationship(
        "DocumentReviewFinding",
        backref="review",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="DocumentReviewFinding.severity.desc()",
    )
    brand = db.relationship("Brand", foreign_keys=[brand_id])
    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self, include_findings=True):
        data = {
            "id": self.id,
            "brand_id": self.brand_id,
            "brand_name": self.brand.name if self.brand else None,
            "user_id": self.user_id,
            "reviewed_by": self.user.username if self.user else None,
            "original_filename": self.original_filename,
            "detected_format": self.detected_format,
            "file_size_bytes": self.file_size_bytes,
            "extracted_char_count": self.extracted_char_count,
            "model_identifier": self.model_identifier,
            "summary": self.summary,
            "review_status": self.review_status,
            "issues_count": self.issues_count,
            "critical_severity_count": self.critical_severity_count,
            "high_severity_count": self.high_severity_count,
            "medium_severity_count": self.medium_severity_count,
            "low_severity_count": self.low_severity_count,
            "unable_to_verify_count": self.unable_to_verify_count,
            "has_limitations": self.has_limitations,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_findings:
            data["findings"] = [f.to_dict() for f in self.findings]
        return data

    def __repr__(self):
        return (
            f"<DocumentReview id={self.id} brand_id={self.brand_id} "
            f"fmt='{self.detected_format}' status='{self.review_status}'>"
        )


class DocumentReviewFinding(db.Model):
    """Individual finding from a document review (brand compliance OR accessibility)."""
    __tablename__ = "document_review_findings"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(
        db.Integer,
        db.ForeignKey("document_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Review type: 'Brand Compliance' or 'Accessibility'
    review_type = db.Column(db.String(30), nullable=False, default="Brand Compliance")
    # Category within the type (Tone, Terminology, Readability, Structure, etc.)
    category = db.Column(db.String(80), nullable=False)
    # 'Critical' | 'High' | 'Medium' | 'Low' | 'Unable to Verify'
    severity = db.Column(db.String(30), nullable=False)
    # The problematic excerpt or description of the element
    problematic_text = db.Column(db.Text, nullable=False)
    # Guideline reference (nullable — accessibility issues may not map to a brand rule)
    guideline_id = db.Column(
        db.Integer,
        db.ForeignKey("brand_guidelines.id", ondelete="SET NULL"),
        nullable=True,
    )
    guideline_rule = db.Column(db.Text, nullable=True)
    explanation = db.Column(db.Text, nullable=False)
    suggested_correction = db.Column(db.Text, nullable=True)
    confidence_level = db.Column(db.String(20), default="High", nullable=False)
    human_verification_required = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    guideline = db.relationship("BrandGuideline", foreign_keys=[guideline_id])

    def to_dict(self):
        return {
            "id": self.id,
            "review_id": self.review_id,
            "review_type": self.review_type,
            "category": self.category,
            "severity": self.severity,
            "problematic_text": self.problematic_text,
            "guideline_id": self.guideline_id,
            "guideline_title": self.guideline.title if self.guideline else None,
            "guideline_category": self.guideline.category if self.guideline else None,
            "guideline_rule": self.guideline_rule or "",
            "explanation": self.explanation,
            "suggested_correction": self.suggested_correction or "",
            "confidence_level": self.confidence_level,
            "human_verification_required": self.human_verification_required,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return (
            f"<DocumentReviewFinding id={self.id} review_id={self.review_id} "
            f"severity='{self.severity}' category='{self.category}'>"
        )
