from datetime import datetime, timezone
from app.models import db


class VisualComplianceAnalysis(db.Model):
    """
    Stores an AI-driven visual compliance analysis for an uploaded marketing image.
    This is independent of text-based ContentSubmission and operates at the brand level.
    """
    __tablename__ = "visual_compliance_analyses"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(
        db.Integer,
        db.ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # User who requested the analysis
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    # Original filename for display purposes (never used for serving or storage pathing)
    original_filename = db.Column(db.String(255), nullable=False)
    # MIME type as detected on the backend
    mime_type = db.Column(db.String(100), nullable=False)
    # File size in bytes
    file_size_bytes = db.Column(db.Integer, nullable=True)
    # Which Gemini model was used
    model_identifier = db.Column(db.String(100), default="gemini-2.5-flash", nullable=False)
    # Overall summary from AI
    summary = db.Column(db.Text, nullable=False)
    # 'Compliant' | 'Action Required' | 'Violations Detected'
    review_status = db.Column(db.String(50), default="Violations Detected", nullable=False)
    # Aggregate score 0-100 (None if not calculable)
    compliance_score = db.Column(db.Integer, nullable=True)
    # Severity counts
    issues_count = db.Column(db.Integer, default=0, nullable=False)
    high_severity_count = db.Column(db.Integer, default=0, nullable=False)
    medium_severity_count = db.Column(db.Integer, default=0, nullable=False)
    low_severity_count = db.Column(db.Integer, default=0, nullable=False)
    # Number of guidelines that had insufficient visual evidence to verify
    unable_to_verify_count = db.Column(db.Integer, default=0, nullable=False)
    # Whether any limitations were reported
    has_limitations = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    findings = db.relationship(
        "VisualComplianceFinding",
        backref="analysis",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="VisualComplianceFinding.severity.desc()"
    )
    brand = db.relationship("Brand", foreign_keys=[brand_id])
    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self, include_findings=True):
        data = {
            "id": self.id,
            "brand_id": self.brand_id,
            "brand_name": self.brand.name if self.brand else None,
            "user_id": self.user_id,
            "analyzed_by": self.user.username if self.user else None,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "file_size_bytes": self.file_size_bytes,
            "model_identifier": self.model_identifier,
            "summary": self.summary,
            "review_status": self.review_status,
            "compliance_score": self.compliance_score,
            "issues_count": self.issues_count,
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
            f"<VisualComplianceAnalysis id={self.id} brand_id={self.brand_id} "
            f"status='{self.review_status}'>"
        )


class VisualComplianceFinding(db.Model):
    """Individual finding from a visual compliance analysis."""
    __tablename__ = "visual_compliance_findings"

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(
        db.Integer,
        db.ForeignKey("visual_compliance_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Visual category: Logo, Color, Typography, Layout, Contrast, Other
    category = db.Column(db.String(80), nullable=False)
    # 'High' | 'Medium' | 'Low' | 'Unable to Verify'
    severity = db.Column(db.String(30), nullable=False)
    # What the AI detected in the image (visual description)
    visual_element = db.Column(db.Text, nullable=False)
    # Guideline that was violated or relevant (nullable: not all findings reference a specific rule)
    guideline_id = db.Column(
        db.Integer,
        db.ForeignKey("brand_guidelines.id", ondelete="SET NULL"),
        nullable=True
    )
    # The specific rule / context from the guideline
    guideline_rule = db.Column(db.Text, nullable=True)
    # Explanation of the finding
    explanation = db.Column(db.Text, nullable=False)
    # Practical correction suggestion
    suggested_correction = db.Column(db.Text, nullable=True)
    # Whether human verification is needed
    human_verification_required = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    guideline = db.relationship("BrandGuideline", foreign_keys=[guideline_id])

    def to_dict(self):
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "category": self.category,
            "severity": self.severity,
            "visual_element": self.visual_element,
            "guideline_id": self.guideline_id,
            "guideline_title": self.guideline.title if self.guideline else None,
            "guideline_category": self.guideline.category if self.guideline else None,
            "guideline_rule": self.guideline_rule or "",
            "explanation": self.explanation,
            "suggested_correction": self.suggested_correction or "",
            "human_verification_required": self.human_verification_required,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return (
            f"<VisualComplianceFinding id={self.id} analysis_id={self.analysis_id} "
            f"severity='{self.severity}' category='{self.category}'>"
        )
