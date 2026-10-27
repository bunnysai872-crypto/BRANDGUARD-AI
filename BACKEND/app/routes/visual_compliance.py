import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.visual_compliance_service import VisualComplianceService

logger = logging.getLogger(__name__)

visual_compliance_bp = Blueprint(
    "visual_compliance",
    __name__,
    url_prefix="/api/visual-compliance"
)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/visual-compliance/analyze
# Upload an image and run AI visual compliance analysis against brand guidelines.
# ─────────────────────────────────────────────────────────────────────────────
@visual_compliance_bp.route("/analyze", methods=["POST"])
@jwt_required()
def analyze_image():
    """
    Accepts a multipart/form-data request with:
      - image   : the marketing image file (PNG / JPG / JPEG, ≤ 10 MB)
      - brand_id: integer ID of the brand whose guidelines to check against

    Returns a structured visual compliance analysis with findings.
    """
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    # ── 1. Validate brand_id ─────────────────────────────────────────────────
    brand_id_raw = request.form.get("brand_id")
    if not brand_id_raw:
        return jsonify({"success": False, "error": "brand_id is required."}), 400
    try:
        brand_id = int(brand_id_raw)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "brand_id must be a valid integer."}), 400

    # ── 2. Validate uploaded file ─────────────────────────────────────────────
    uploaded_file = request.files.get("image")
    image_bytes, mime_type, original_filename, file_err = (
        VisualComplianceService.validate_image_upload(uploaded_file)
    )
    if file_err:
        return jsonify({"success": False, "error": file_err}), 422

    file_size = len(image_bytes)

    # ── 3. Delegate to service ────────────────────────────────────────────────
    analysis, error, status_code = VisualComplianceService.analyze_image(
        brand_id=brand_id,
        user_id=user_id,
        role=role,
        image_bytes=image_bytes,
        mime_type=mime_type,
        original_filename=original_filename,
        file_size=file_size,
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "analysis": analysis}), status_code


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/visual-compliance/brands/<brand_id>/history
# Retrieve the visual compliance analysis history for a brand.
# ─────────────────────────────────────────────────────────────────────────────
@visual_compliance_bp.route("/brands/<int:brand_id>/history", methods=["GET"])
@jwt_required()
def get_brand_history(brand_id):
    """
    Returns a paginated list of past visual compliance analyses for the specified brand.
    Query param:
      - limit (int, default 20, max 100)
    """
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    limit_raw = request.args.get("limit", "20")
    try:
        limit = max(1, min(int(limit_raw), 100))
    except (ValueError, TypeError):
        limit = 20

    history, error, status_code = VisualComplianceService.get_brand_history(
        brand_id=brand_id,
        user_id=user_id,
        role=role,
        limit=limit,
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "history": history, "total": len(history)}), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/visual-compliance/<analysis_id>
# Retrieve a single visual compliance analysis with all findings.
# ─────────────────────────────────────────────────────────────────────────────
@visual_compliance_bp.route("/<int:analysis_id>", methods=["GET"])
@jwt_required()
def get_analysis(analysis_id):
    """
    Returns a single visual compliance analysis record (with findings).
    Enforces brand-level data isolation — users cannot view another brand's results.
    """
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    analysis, error, status_code = VisualComplianceService.get_analysis_by_id(
        analysis_id=analysis_id,
        user_id=user_id,
        role=role,
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "analysis": analysis}), 200
