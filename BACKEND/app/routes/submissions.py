from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.submission_service import SubmissionService
from app.services.brand_service import BrandService

submissions_bp = Blueprint("submissions", __name__, url_prefix="/api/submissions")

@submissions_bp.route("", methods=["POST"])
@jwt_required()
def create_submission():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")
    data = request.get_json() or {}

    brand_id = data.get("brand_id")
    if not brand_id:
        return jsonify({"success": False, "error": "Brand ID is required."}), 400

    # Ensure user has access to submit for this brand
    if not BrandService.user_has_brand_access(int(brand_id), user_id, role):
        return jsonify({"success": False, "error": "You do not have permission to submit content for this brand."}), 403

    submission, error, status_code = SubmissionService.create_submission(user_id, data)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "submission": submission}), status_code

@submissions_bp.route("", methods=["GET"])
@jwt_required()
def list_submissions():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    brand_id = request.args.get("brand_id")
    status = request.args.get("status")

    submissions, error, status_code = SubmissionService.get_accessible_submissions(
        user_id=user_id,
        role=role,
        brand_id=brand_id,
        status=status
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "submissions": submissions}), 200

@submissions_bp.route("/<int:submission_id>", methods=["GET"])
@jwt_required()
def get_submission(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    submission = SubmissionService.get_submission_by_id(submission_id)
    if not submission:
        return jsonify({"success": False, "error": "Submission not found."}), 404

    # Authorization check
    if role == "creator" and submission.creator_id != user_id:
        return jsonify({"success": False, "error": "Access denied."}), 403
    elif role == "admin" and not BrandService.user_has_brand_access(submission.brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied to this brand."}), 403

    return jsonify({"success": True, "submission": submission.to_dict(include_revisions=True, include_decisions=True)}), 200

@submissions_bp.route("/<int:submission_id>", methods=["PUT"])
@jwt_required()
def update_submission(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")
    data = request.get_json() or {}

    submission, error, status_code = SubmissionService.update_submission(
        submission_id=submission_id,
        user_id=user_id,
        role=role,
        data=data
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "submission": submission}), status_code

@submissions_bp.route("/<int:submission_id>/revisions", methods=["GET"])
@jwt_required()
def get_revisions(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    submission = SubmissionService.get_submission_by_id(submission_id)
    if not submission:
        return jsonify({"success": False, "error": "Submission not found."}), 404

    if role == "creator" and submission.creator_id != user_id:
        return jsonify({"success": False, "error": "Access denied."}), 403

    revisions, error, status_code = SubmissionService.get_submission_revisions(submission_id)
    return jsonify({"success": True, "revisions": revisions}), 200

# Compliance Analysis Endpoints (Phase 3)
@submissions_bp.route("/<int:submission_id>/analyze", methods=["POST"])
@jwt_required()
def analyze_submission(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    submission = SubmissionService.get_submission_by_id(submission_id)
    if not submission:
        return jsonify({"success": False, "error": "Submission not found."}), 404

    # Enforce access: creator can analyze own submission; admin can analyze brand submission
    if role == "creator" and submission.creator_id != user_id:
        return jsonify({"success": False, "error": "Access denied."}), 403
    elif role == "admin" and not BrandService.user_has_brand_access(submission.brand_id, user_id, role):
        return jsonify({"success": False, "error": "Access denied to this brand."}), 403

    from app.services.compliance_service import ComplianceService
    analysis, error, status_code = ComplianceService.analyze_submission(submission_id, user_id, role)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "analysis": analysis}), status_code

@submissions_bp.route("/<int:submission_id>/analysis", methods=["GET"])
@jwt_required()
def get_submission_analysis(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    submission = SubmissionService.get_submission_by_id(submission_id)
    if not submission:
        return jsonify({"success": False, "error": "Submission not found."}), 404

    if role == "creator" and submission.creator_id != user_id:
        return jsonify({"success": False, "error": "Access denied."}), 403

    from app.services.compliance_service import ComplianceService
    analysis, error, status_code = ComplianceService.get_latest_analysis(submission_id)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "analysis": analysis}), status_code

@submissions_bp.route("/<int:submission_id>/analysis/history", methods=["GET"])
@jwt_required()
def get_analysis_history(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    submission = SubmissionService.get_submission_by_id(submission_id)
    if not submission:
        return jsonify({"success": False, "error": "Submission not found."}), 404

    if role == "creator" and submission.creator_id != user_id:
        return jsonify({"success": False, "error": "Access denied."}), 403

    from app.services.compliance_service import ComplianceService
    history, error, status_code = ComplianceService.get_analysis_history(submission_id)
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "history": history}), status_code

# Phase 4 Manager Review & Approval Workflow Endpoints

@submissions_bp.route("/queue", methods=["GET"])
@jwt_required()
def get_manager_approval_queue():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    brand_id = request.args.get("brand_id")
    status = request.args.get("status")

    from app.services.review_service import ReviewService
    queue, error, status_code = ReviewService.get_manager_queue(
        user_id=user_id,
        role=role,
        brand_id=brand_id,
        status=status
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "queue": queue}), status_code

@submissions_bp.route("/<int:submission_id>/submit-approval", methods=["POST"])
@jwt_required()
def submit_for_approval(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")
    data = request.get_json(silent=True) or {}
    acknowledgement = bool(data.get("acknowledgement", False))

    from app.services.review_service import ReviewService
    result, error, status_code = ReviewService.submit_for_approval(
        submission_id=submission_id,
        user_id=user_id,
        role=role,
        acknowledgement=acknowledgement
    )
    if error:
        res_payload = {"success": False, "error": error}
        if isinstance(result, dict) and result.get("requires_acknowledgement"):
            res_payload.update(result)
        return jsonify(res_payload), status_code

    return jsonify({"success": True, "submission": result}), status_code

@submissions_bp.route("/<int:submission_id>/review", methods=["POST"])
@jwt_required()
def review_submission(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")
    data = request.get_json(silent=True) or {}

    decision = data.get("decision")
    comments = data.get("comments") or data.get("review_comments")
    acknowledgement = bool(data.get("acknowledgement", False))

    from app.services.review_service import ReviewService
    result, error, status_code = ReviewService.review_submission(
        submission_id=submission_id,
        reviewer_id=user_id,
        role=role,
        decision=decision,
        comments=comments,
        acknowledgement=acknowledgement
    )
    if error:
        res_payload = {"success": False, "error": error}
        if isinstance(result, dict) and result.get("requires_acknowledgement"):
            res_payload.update(result)
        return jsonify(res_payload), status_code

    return jsonify({
        "success": True,
        "message": f"Submission decision '{decision}' recorded successfully.",
        "decision": result["decision"],
        "submission": result["submission"]
    }), status_code

@submissions_bp.route("/<int:submission_id>/decisions", methods=["GET"])
@jwt_required()
def get_submission_decisions(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    from app.services.review_service import ReviewService
    decisions, error, status_code = ReviewService.get_decision_history(
        submission_id=submission_id,
        user_id=user_id,
        role=role
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({"success": True, "decisions": decisions}), status_code

@submissions_bp.route("/<int:submission_id>/publish", methods=["POST"])
@jwt_required()
def publish_submission(submission_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role", "creator")

    submission, error, status_code = SubmissionService.publish_submission(
        submission_id=submission_id,
        user_id=user_id,
        role=role
    )
    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({
        "success": True,
        "message": "Submission published successfully.",
        "submission": submission
    }), status_code

