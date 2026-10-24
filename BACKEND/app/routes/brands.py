from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.brand_service import BrandService
from app.services.guideline_service import GuidelineService
from app.utils.decorators import admin_required

brands_bp = Blueprint("brands", __name__, url_prefix="/api/brands")

@brands_bp.route("", methods=["POST"])
@admin_required()
def create_brand():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    brand, error, status_code = BrandService.create_brand(user_id, data)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "brand": brand}), status_code

@brands_bp.route("/creators-list", methods=["GET"])
@admin_required()
def get_assignable_creators():
    creators = BrandService.list_assignable_creators()
    return jsonify({"success": True, "creators": creators}), 200

@brands_bp.route("", methods=["GET"])
@jwt_required()
def list_brands():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    brands = BrandService.get_accessible_brands(user_id, role)
    return jsonify({"success": True, "brands": brands}), 200

@brands_bp.route("/<int:brand_id>", methods=["GET"])
@jwt_required()
def get_brand(brand_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    if not BrandService.user_has_brand_access(brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied to this brand."}), 403

    brand = BrandService.get_brand_by_id(brand_id)
    if not brand:
        return jsonify({"success": False, "error": "Brand not found."}), 404

    return jsonify({"success": True, "brand": brand.to_dict()}), 200

@brands_bp.route("/<int:brand_id>", methods=["PUT"])
@admin_required()
def update_brand(brand_id):
    data = request.get_json() or {}
    brand, error, status_code = BrandService.update_brand(brand_id, data)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "brand": brand}), status_code

@brands_bp.route("/<int:brand_id>/members", methods=["GET"])
@jwt_required()
def get_brand_members(brand_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    if not BrandService.user_has_brand_access(brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied."}), 403

    members = BrandService.get_members(brand_id)
    return jsonify({"success": True, "members": members}), 200

@brands_bp.route("/<int:brand_id>/members", methods=["POST"])
@admin_required()
def add_brand_member(brand_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")
    role = data.get("role", "contributor")

    if not user_id:
        return jsonify({"success": False, "error": "User ID is required."}), 400

    member, error, status_code = BrandService.add_member(brand_id, int(user_id), role)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "member": member}), status_code

@brands_bp.route("/<int:brand_id>/members/<int:member_user_id>", methods=["DELETE"])
@admin_required()
def remove_brand_member(brand_id, member_user_id):
    success, error, status_code = BrandService.remove_member(brand_id, member_user_id)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "message": "Member removed from brand."}), 200

# Guidelines sub-routes
@brands_bp.route("/<int:brand_id>/guidelines", methods=["POST"])
@admin_required()
def create_guideline(brand_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    if not BrandService.user_has_brand_access(brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied to this brand."}), 403

    data = request.get_json() or {}
    guideline, error, status_code = GuidelineService.create_guideline(brand_id, data)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "guideline": guideline}), status_code

@brands_bp.route("/<int:brand_id>/guidelines", methods=["GET"])
@jwt_required()
def get_guidelines_for_brand(brand_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    if not BrandService.user_has_brand_access(brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied to this brand's guidelines."}), 403

    category = request.args.get("category")
    guidelines, error, status_code = GuidelineService.get_guidelines_for_brand(brand_id, category)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "guidelines": guidelines}), 200
