from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.analytics_service import AnalyticsService

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

@analytics_bp.route("", methods=["GET"])
@jwt_required()
def get_analytics():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    brand_id = request.args.get("brand_id")
    days = request.args.get("days")

    analytics_data, error, status_code = AnalyticsService.get_governance_analytics(
        user_id=user_id,
        role=role,
        brand_id=brand_id,
        days=days
    )

    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({
        "success": True,
        **analytics_data,
        "analytics": analytics_data
    }), 200
