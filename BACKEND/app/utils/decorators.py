from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

def role_required(*allowed_roles):
    """Decorator to require one of the specified roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            
            if user_role not in allowed_roles:
                return jsonify({
                    "error": "Forbidden",
                    "message": f"Access denied. Requires one of roles: {', '.join(allowed_roles)}. Your role is '{user_role}'."
                }), 403
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required():
    """Require admin / brand manager role."""
    return role_required("admin")

def creator_required():
    """Require creator role."""
    return role_required("creator")
