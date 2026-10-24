import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from app.services.auth_service import AuthService
from app.utils.decorators import admin_required, creator_required, role_required
from app.models import db, User

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# ---------------------------------------------------------------------------
# Demo accounts configuration (credentials only – no secrets)
# ---------------------------------------------------------------------------
_DEMO_ACCOUNTS = {
    "admin": {
        "username": "brand_manager",
        "email": "manager@brandguard.ai",
        "password": "Password123!",
        "role": "admin",
        "full_name": "Alex Brand Manager",
    },
    "creator": {
        "username": "content_creator",
        "email": "creator@brandguard.ai",
        "password": "Password123!",
        "role": "creator",
        "full_name": "Sarah Content Creator",
    },
}

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "creator")
    full_name = data.get("full_name")

    result, error, status_code = AuthService.register_user(
        username=username,
        email=email,
        password=password,
        role=role,
        full_name=full_name
    )

    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({
        "success": True,
        "message": "User registered successfully.",
        "user": result["user"],
        "token": result["token"]
    }), status_code

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = data.get("identifier") or data.get("email") or data.get("username")
    password = data.get("password")

    result, error, status_code = AuthService.authenticate_user(
        identifier=identifier,
        password=password
    )

    if error:
        return jsonify({"success": False, "error": error}), status_code

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": result["user"],
        "token": result["token"]
    }), status_code

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    return jsonify({
        "success": True,
        "user": user.to_dict()
    }), 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    # Stateless JWT - client drops the token, but endpoint confirms successful logout
    return jsonify({
        "success": True,
        "message": "Successfully logged out."
    }), 200

@auth_bp.route("/admin-only", methods=["GET"])
@admin_required()
def admin_only_test():
    claims = get_jwt()
    return jsonify({
        "success": True,
        "message": "Welcome, Brand Manager / Admin!",
        "role": claims.get("role")
    }), 200

@auth_bp.route("/creator-only", methods=["GET"])
@creator_required()
def creator_only_test():
    claims = get_jwt()
    return jsonify({
        "success": True,
        "message": "Welcome, Content Creator!",
        "role": claims.get("role")
    }), 200


@auth_bp.route("/demo-login", methods=["POST"])
def demo_login():
    """
    Idempotent one-click demo login for hackathon evaluators.
    Accepts { "role": "admin" | "creator" }.
    Creates the demo account if it does not yet exist, then authenticates
    and returns a signed JWT — identical shape to /login.
    Never exposes passwords; credentials are server-side constants.
    """
    data = request.get_json() or {}
    role = (data.get("role") or "").strip().lower()

    if role not in _DEMO_ACCOUNTS:
        return jsonify({
            "success": False,
            "error": "Invalid demo role. Must be 'admin' or 'creator'."
        }), 400

    creds = _DEMO_ACCOUNTS[role]

    try:
        # 1. Try to find the demo user by email
        user = User.query.filter_by(email=creds["email"]).first()

        if not user:
            # 2. Auto-create if not found
            user = User(
                username=creds["username"],
                email=creds["email"],
                role=creds["role"],
                full_name=creds["full_name"],
            )
            user.set_password(creds["password"])
            db.session.add(user)
            db.session.commit()
            logger.info("Demo account auto-created: %s (%s)", creds["email"], creds["role"])
        else:
            # 3. Ensure role is correct in case DB was modified
            if user.role != creds["role"]:
                user.role = creds["role"]
                db.session.commit()

        # 4. Issue JWT
        additional_claims = {
            "role": user.role,
            "username": user.username,
            "email": user.email,
        }
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims,
        )

        logger.info("Demo login issued for %s (id=%s)", user.email, user.id)
        return jsonify({
            "success": True,
            "message": f"Demo {role} login successful.",
            "user": user.to_dict(),
            "token": access_token,
        }), 200

    except Exception:
        logger.exception("Unexpected error in /demo-login for role=%s", role)
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Demo login failed due to a server error. Please try again."
        }), 500
