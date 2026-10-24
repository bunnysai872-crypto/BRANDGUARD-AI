from datetime import datetime, timezone
from app.models import db

class ComplianceAnalysis(db.Model):
    __tablename__ = "compliance_analyses"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey("content_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    revision_number = db.Column(db.Integer, nullable=False)
    model_identifier = db.Column(db.String(100), default="gemini-2.5-flash", nullable=False)
    summary = db.Column(db.Text, nullable=False)
    review_status = db.Column(db.String(50), default="Violations Detected", nullable=False)
    # 'Compliant', 'Action Required', 'Violations Detected'
    issues_count = db.Column(db.Integer, default=0, nullable=False)
    critical_severity_count = db.Column(db.Integer, default=0, nullable=False)
    high_severity_count = db.Column(db.Integer, default=0, nullable=False)
    medium_severity_count = db.Column(db.Integer, default=0, nullable=False)
    low_severity_count = db.Column(db.Integer, default=0, nullable=False)
    is_outdated = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    findings = db.relationship(
        "ComplianceFinding",
        backref="analysis",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="ComplianceFinding.severity.desc()"
    )

    def to_dict(self, include_findings=True):
        data = {
            "id": self.id,
            "submission_id": self.submission_id,
            "revision_number": self.revision_number,
            "model_identifier": self.model_identifier,
            "summary": self.summary,
            "review_status": self.review_status,
            "issues_count": self.issues_count,
            "critical_severity_count": self.critical_severity_count,
            "high_severity_count": self.high_severity_count,
            "medium_severity_count": self.medium_severity_count,
            "low_severity_count": self.low_severity_count,
            "is_outdated": self.is_outdated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_findings:
            data["findings"] = [f.to_dict() for f in self.findings]
        return data

    def __repr__(self):
        return f"<ComplianceAnalysis id={self.id} sub_id={self.submission_id} rev={self.revision_number} status='{self.review_status}'>"


class ComplianceFinding(db.Model):
    __tablename__ = "compliance_findings"

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(
        db.Integer,
        db.ForeignKey("compliance_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    category = db.Column(db.String(50), nullable=False)
    # 'Tone', 'Terminology', 'Messaging', 'Unsupported Claims', 'Contradictions with Approved Facts', 'Accessibility & Clarity'
    severity = db.Column(db.String(20), nullable=False) # 'Low', 'Medium', 'High'
    problematic_text = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    guideline_id = db.Column(
        db.Integer,
        db.ForeignKey("brand_guidelines.id", ondelete="SET NULL"),
        nullable=True
    )
    suggested_correction = db.Column(db.Text, nullable=True)
    confidence_level = db.Column(db.String(20), default="High", nullable=False) # 'High', 'Medium', 'Low'
    human_verification_required = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    guideline = db.relationship("BrandGuideline", foreign_keys=[guideline_id])

    def to_dict(self):
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "category": self.category,
            "severity": self.severity,
            "problematic_text": self.problematic_text,
            "explanation": self.explanation,
            "guideline_id": self.guideline_id,
            "guideline_title": self.guideline.title if self.guideline else None,
            "guideline_category": self.guideline.category if self.guideline else None,
            "guideline_reference": self.guideline.reference_evidence if self.guideline else None,
            "suggested_correction": self.suggested_correction or "",
            "confidence_level": self.confidence_level or "High",
            "human_verification_required": self.human_verification_required,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ComplianceFinding id={self.id} analysis_id={self.analysis_id} severity='{self.severity}'>"
