import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.document_review_service import DocumentReviewService

logger = logging.getLogger(__name__)

document_review_bp = Blueprint(
    "document_review",
    __name__,
    url_prefix="/api/document-review",
)


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/document-review/analyze
# Upload a TXT / PDF / DOCX document and run combined brand + accessibility review.
# ──────────────────────────────────────────────────────────────────────────────
@document_review_bp.route("/analyze", methods=["POST"])
@jwt_required()
def analyze_document():
    """
    Accepts multipart/form-data with:
      - document : the file (TXT, PDF, or DOCX; ≤ 20 MB)
      - brand_id : integer brand ID whose guidelines to check against
    """
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    # ── Validate brand_id ─────────────────────────────────────────────────────
    brand_id_raw = request.form.get("brand_id")
    if not brand_id_raw:
        return jsonify({"success": False, "error": "brand_id is required."}), 400
    try:
        brand_id = int(brand_id_raw)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "brand_id must be a valid integer."}), 400

    # ── Validate and extract file ─────────────────────────────────────────────
    uploaded_file = request.files.get("document")
    raw_bytes, detected_format, original_filename, extracted_text, file_err = (
        DocumentReviewService.validate_and_extract(uploaded_file)
    )
    if file_err:
        return jsonify({"success": False, "error": file_err}), 422

    file_size = len(raw_bytes)

    # ── Delegate to service ───────────────────────────────────────────────────
    review, error, status_code = DocumentReviewService.analyze_document(
        brand_id=brand_id,
        user_id=user_id,
        role=role,
        raw_bytes=raw_bytes,
        detected_format=detected_format,
        original_filename=original_filename,
        extracted_text=extracted_text,
        file_size=file_size,
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "review": review}), status_code


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/document-review/brands/<brand_id>/history
# ──────────────────────────────────────────────────────────────────────────────
@document_review_bp.route("/brands/<int:brand_id>/history", methods=["GET"])
@jwt_required()
def get_brand_history(brand_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    limit_raw = request.args.get("limit", "20")
    try:
        limit = max(1, min(int(limit_raw), 100))
    except (ValueError, TypeError):
        limit = 20

    history, error, status_code = DocumentReviewService.get_brand_history(
        brand_id=brand_id,
        user_id=user_id,
        role=role,
        limit=limit,
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "history": history, "total": len(history)}), 200


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/document-review/<review_id>
# ──────────────────────────────────────────────────────────────────────────────
@document_review_bp.route("/<int:review_id>", methods=["GET"])
@jwt_required()
def get_review(review_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    review, error, status_code = DocumentReviewService.get_review_by_id(
        review_id=review_id,
        user_id=user_id,
        role=role,
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "review": review}), 200
