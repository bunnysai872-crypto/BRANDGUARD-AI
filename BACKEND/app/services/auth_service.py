import re
from flask_jwt_extended import create_access_token
from app.models import db, User

EMAIL_REGEX = r"^[^@]+@[^@]+\.[^@]+$"

class AuthService:
    @staticmethod
    def validate_registration_input(username, email, password, role):
        if not username or len(username.strip()) < 3:
            return "Username must be at least 3 characters long."
        if not re.match(r"^[a-zA-Z0-9_-]+$", username.strip()):
            return "Username may only contain letters, numbers, hyphens, and underscores."
        if not email or not re.match(EMAIL_REGEX, email.strip()):
            return "A valid email address is required."
        if not password or len(password) < 6:
            return "Password must be at least 6 characters long."
        if role not in ["admin", "creator"]:
            return "Role must be either 'admin' or 'creator'."
        return None

    @staticmethod
    def register_user(username, email, password, role="creator", full_name=None):
        error = AuthService.validate_registration_input(username, email, password, role)
        if error:
            return None, error, 400

        clean_username = username.strip()
        clean_email = email.strip().lower()

        # Check existing username
        if User.query.filter_by(username=clean_username).first():
            return None, f"Username '{clean_username}' is already taken.", 409

        # Check existing email
        if User.query.filter_by(email=clean_email).first():
            return None, f"Email '{clean_email}' is already registered.", 409

        # Create new user
        user = User(
            username=clean_username,
            email=clean_email,
            role=role,
            full_name=full_name.strip() if full_name else clean_username
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Generate JWT token
        additional_claims = {
            "role": user.role,
            "username": user.username,
            "email": user.email
        }
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        return {
            "user": user.to_dict(),
            "token": access_token
        }, None, 201

    @staticmethod
    def authenticate_user(identifier, password):
        if not identifier or not password:
            return None, "Identifier (username/email) and password are required.", 400

        clean_id = identifier.strip()
        # Find by email or username
        user = User.query.filter(
            (User.email == clean_id.lower()) | (User.username == clean_id)
        ).first()

        if not user or not user.check_password(password):
            return None, "Invalid email/username or password.", 401

        additional_claims = {
            "role": user.role,
            "username": user.username,
            "email": user.email
        }
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        return {
            "user": user.to_dict(),
            "token": access_token
        }, None, 200

    @staticmethod
    def get_user_by_id(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None
