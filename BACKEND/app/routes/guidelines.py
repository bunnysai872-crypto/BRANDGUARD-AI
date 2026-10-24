from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.guideline_service import GuidelineService
from app.services.brand_service import BrandService
from app.models.guideline import GUIDELINE_CATEGORIES, GUIDELINE_SEVERITIES
from app.utils.decorators import admin_required

guidelines_bp = Blueprint("guidelines", __name__, url_prefix="/api/guidelines")

@guidelines_bp.route("/categories", methods=["GET"])
def get_categories():
    return jsonify({
        "success": True,
        "categories": GUIDELINE_CATEGORIES,
        "severities": GUIDELINE_SEVERITIES
    }), 200

@guidelines_bp.route("/extract-text", methods=["POST"])
@admin_required()
def extract_text_from_document():
    """Extract text securely from an uploaded .txt or .pdf guideline document."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part in request. Please upload a file."}), 400

    file = request.files["file"]
    result, error, status_code = GuidelineService.extract_text_from_file(file)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({
        "success": True,
        "message": f"Successfully extracted text from '{result['filename']}'.",
        "extracted_text": result.get("extracted_text", ""),
        "filename": result.get("filename", ""),
        "length": result.get("length", 0),
        "data": result
    }), status_code

@guidelines_bp.route("/<int:guideline_id>", methods=["GET"])
@jwt_required()
def get_guideline(guideline_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    guideline = GuidelineService.get_guideline_by_id(guideline_id)
    if not guideline:
        return jsonify({"success": False, "error": "Guideline not found."}), 404

    if not BrandService.user_has_brand_access(guideline.brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied to this brand's guideline."}), 403

    return jsonify({"success": True, "guideline": guideline.to_dict()}), 200

@guidelines_bp.route("/<int:guideline_id>", methods=["PUT"])
@admin_required()
def update_guideline(guideline_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    guideline_obj = GuidelineService.get_guideline_by_id(guideline_id)
    if not guideline_obj:
        return jsonify({"success": False, "error": "Guideline not found."}), 404

    if not BrandService.user_has_brand_access(guideline_obj.brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied. You do not have management permissions for this brand."}), 403

    data = request.get_json() or {}
    guideline, error, status_code = GuidelineService.update_guideline(guideline_id, data)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "guideline": guideline}), status_code

@guidelines_bp.route("/<int:guideline_id>/toggle-active", methods=["POST"])
@admin_required()
def toggle_guideline_active(guideline_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    guideline_obj = GuidelineService.get_guideline_by_id(guideline_id)
    if not guideline_obj:
        return jsonify({"success": False, "error": "Guideline not found."}), 404

    if not BrandService.user_has_brand_access(guideline_obj.brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied."}), 403

    new_active = not guideline_obj.is_active
    guideline, error, status_code = GuidelineService.update_guideline(guideline_id, {"is_active": new_active})
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({
        "success": True,
        "message": f"Guideline marked as {'Active' if new_active else 'Inactive'}.",
        "guideline": guideline
    }), status_code

@guidelines_bp.route("/<int:guideline_id>", methods=["DELETE"])
@admin_required()
def delete_guideline(guideline_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    guideline_obj = GuidelineService.get_guideline_by_id(guideline_id)
    if not guideline_obj:
        return jsonify({"success": False, "error": "Guideline not found."}), 404

    if not BrandService.user_has_brand_access(guideline_obj.brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied. You do not have management permissions for this brand."}), 403

    success, error, status_code = GuidelineService.delete_guideline(guideline_id)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "message": "Guideline deleted successfully."}), 200
