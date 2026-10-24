from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from app.models.user import User
from app.models.brand import Brand, BrandMembership
from app.models.guideline import BrandGuideline, GUIDELINE_CATEGORIES, GUIDELINE_SEVERITIES
from app.models.submission import ContentSubmission, ContentRevision, SUBMISSION_STATUSES
from app.models.compliance import ComplianceAnalysis, ComplianceFinding
from app.models.decision import ReviewDecision, DECISION_CHOICES

__all__ = [
    "db",
    "User",
    "Brand",
    "BrandMembership",
    "BrandGuideline",
    "GUIDELINE_CATEGORIES",
    "GUIDELINE_SEVERITIES",
    "ContentSubmission",
    "ContentRevision",
    "SUBMISSION_STATUSES",
    "ComplianceAnalysis",
    "ComplianceFinding",
    "ReviewDecision",
    "DECISION_CHOICES"
]
