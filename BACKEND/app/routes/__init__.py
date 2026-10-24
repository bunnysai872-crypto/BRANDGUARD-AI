from app.routes.auth import auth_bp
from app.routes.health import health_bp
from app.routes.brands import brands_bp
from app.routes.guidelines import guidelines_bp
from app.routes.submissions import submissions_bp
from app.routes.analytics import analytics_bp

__all__ = [
    "auth_bp",
    "health_bp",
    "brands_bp",
    "guidelines_bp",
    "submissions_bp",
    "analytics_bp"
]
