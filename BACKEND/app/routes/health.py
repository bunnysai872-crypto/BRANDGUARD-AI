import os
from flask import Blueprint, jsonify
from datetime import datetime, timezone
from sqlalchemy import text
from app.models import db

health_bp = Blueprint("health", __name__, url_prefix="/api")

@health_bp.route("/health", methods=["GET"])
def health_check():
    db_status = "connected"
    http_code = 200

    try:
        # Check database connectivity
        db.session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: database unreachable"
        http_code = 503

    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))

    return jsonify({
        "status": "healthy" if http_code == 200 else "degraded",
        "service": "BrandGuard AI Backend",
        "version": "1.0.0",
        "environment": os.getenv("FLASK_ENV", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "ai_engine": {
            "provider": "Google Gemini",
            "configured": gemini_configured,
            "model": os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        }
    }), http_code
