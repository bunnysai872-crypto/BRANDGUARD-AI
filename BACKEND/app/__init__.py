import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import config_by_name
from app.models import db

jwt = JWTManager()
cors = CORS()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Setup safe logging
    log_level = logging.INFO if config_name == "production" else logging.DEBUG
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Parse CORS origins
    cors_origins_env = app.config.get("CORS_ORIGINS", "*")
    if cors_origins_env == "*":
        allowed_origins = "*"
    else:
        allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    # JWT Error Handlers
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({
            "success": False,
            "error": "Missing or invalid authorization token."
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return jsonify({
            "success": False,
            "error": "Invalid token. Please log in again."
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "success": False,
            "error": "Token has expired. Please log in again."
        }), 401

    # Generic Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404

    @app.errorhandler(500)
    def handle_server_error(e):
        app.logger.error(f"Internal server error: {e}")
        return jsonify({"success": False, "error": "Internal server error."}), 500

    # Register Blueprints
    from app.routes import auth_bp, health_bp, brands_bp, guidelines_bp, submissions_bp, analytics_bp, visual_compliance_bp, document_review_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(brands_bp)
    app.register_blueprint(guidelines_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(visual_compliance_bp)
    app.register_blueprint(document_review_bp)

    # Safe table creation & non-destructive migration for SQLite / DB
    with app.app_context():
        db.create_all()
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)

            if "brand_guidelines" in inspector.get_table_names():
                bg_cols = {c["name"] for c in inspector.get_columns("brand_guidelines")}
                if "approved_wording" not in bg_cols:
                    db.session.execute(text("ALTER TABLE brand_guidelines ADD COLUMN approved_wording TEXT"))
                if "prohibited_wording" not in bg_cols:
                    db.session.execute(text("ALTER TABLE brand_guidelines ADD COLUMN prohibited_wording TEXT"))
                if "severity" not in bg_cols:
                    db.session.execute(text("ALTER TABLE brand_guidelines ADD COLUMN severity VARCHAR(20) DEFAULT 'Medium'"))
                if "is_active" not in bg_cols:
                    db.session.execute(text("ALTER TABLE brand_guidelines ADD COLUMN is_active BOOLEAN DEFAULT 1"))

            if "content_submissions" in inspector.get_table_names():
                cs_cols = {c["name"] for c in inspector.get_columns("content_submissions")}
                if "published_at" not in cs_cols:
                    db.session.execute(text("ALTER TABLE content_submissions ADD COLUMN published_at DATETIME"))
                if "published_by_id" not in cs_cols:
                    db.session.execute(text("ALTER TABLE content_submissions ADD COLUMN published_by_id INTEGER"))

            if "compliance_findings" in inspector.get_table_names():
                cf_cols = {c["name"] for c in inspector.get_columns("compliance_findings")}
                if "confidence_level" not in cf_cols:
                    db.session.execute(text("ALTER TABLE compliance_findings ADD COLUMN confidence_level VARCHAR(20) DEFAULT 'High'"))

            if "compliance_analyses" in inspector.get_table_names():
                ca_cols = {c["name"] for c in inspector.get_columns("compliance_analyses")}
                if "critical_severity_count" not in ca_cols:
                    db.session.execute(text("ALTER TABLE compliance_analyses ADD COLUMN critical_severity_count INTEGER DEFAULT 0"))

            if "visual_compliance_analyses" in inspector.get_table_names():
                vca_cols = {c["name"] for c in inspector.get_columns("visual_compliance_analyses")}
                if "compliance_score" not in vca_cols:
                    db.session.execute(text("ALTER TABLE visual_compliance_analyses ADD COLUMN compliance_score INTEGER"))
                if "unable_to_verify_count" not in vca_cols:
                    db.session.execute(text("ALTER TABLE visual_compliance_analyses ADD COLUMN unable_to_verify_count INTEGER DEFAULT 0"))
                if "has_limitations" not in vca_cols:
                    db.session.execute(text("ALTER TABLE visual_compliance_analyses ADD COLUMN has_limitations BOOLEAN DEFAULT 0"))

            db.session.commit()
        except Exception as e:
            app.logger.warning(f"Schema migration check notice: {e}")
            db.session.rollback()

    return app
