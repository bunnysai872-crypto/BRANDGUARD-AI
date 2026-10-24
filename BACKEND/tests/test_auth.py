import json

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "BrandGuard AI" in data["service"]

def test_user_registration_success(client):
    payload = {
        "username": "creator_sarah",
        "email": "sarah@company.com",
        "password": "Password123!",
        "role": "creator",
        "full_name": "Sarah Creator"
    }
    response = client.post(
        "/api/auth/register",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["user"]["username"] == "creator_sarah"
    assert data["user"]["role"] == "creator"
    assert "token" in data
    assert "password_hash" not in data["user"]

def test_duplicate_registration_fails(client):
    payload = {
        "username": "creator_sarah",
        "email": "sarah@company.com",
        "password": "Password123!",
        "role": "creator"
    }
    client.post("/api/auth/register", data=json.dumps(payload), content_type="application/json")
    
    # Repeat registration
    response = client.post("/api/auth/register", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 409
    data = response.get_json()
    assert data["success"] is False
    assert "already taken" in data["error"] or "already registered" in data["error"]

def test_registration_validation_rules(client):
    # Short password
    res = client.post("/api/auth/register", data=json.dumps({
        "username": "valid_user",
        "email": "valid@email.com",
        "password": "123",
        "role": "creator"
    }), content_type="application/json")
    assert res.status_code == 400

    # Invalid role
    res = client.post("/api/auth/register", data=json.dumps({
        "username": "valid_user2",
        "email": "valid2@email.com",
        "password": "Password123",
        "role": "superman"
    }), content_type="application/json")
    assert res.status_code == 400

def test_login_flow(client):
    # Register user
    client.post("/api/auth/register", data=json.dumps({
        "username": "manager_alex",
        "email": "alex@company.com",
        "password": "ManagerPass123",
        "role": "admin"
    }), content_type="application/json")

    # Login with email
    res1 = client.post("/api/auth/login", data=json.dumps({
        "identifier": "alex@company.com",
        "password": "ManagerPass123"
    }), content_type="application/json")
    assert res1.status_code == 200
    assert res1.get_json()["user"]["role"] == "admin"
    assert "token" in res1.get_json()

    # Login with username
    res2 = client.post("/api/auth/login", data=json.dumps({
        "identifier": "manager_alex",
        "password": "ManagerPass123"
    }), content_type="application/json")
    assert res2.status_code == 200

    # Login with bad password
    res3 = client.post("/api/auth/login", data=json.dumps({
        "identifier": "manager_alex",
        "password": "WrongPassword"
    }), content_type="application/json")
    assert res3.status_code == 401

def test_protected_routes_and_role_permissions(client):
    # Register Creator
    res_c = client.post("/api/auth/register", data=json.dumps({
        "username": "creator_user",
        "email": "creator@company.com",
        "password": "SecretPassword123",
        "role": "creator"
    }), content_type="application/json")
    creator_token = res_c.get_json()["token"]

    # Register Admin
    res_a = client.post("/api/auth/register", data=json.dumps({
        "username": "admin_user",
        "email": "admin@company.com",
        "password": "AdminPassword123",
        "role": "admin"
    }), content_type="application/json")
    admin_token = res_a.get_json()["token"]

    # Test /api/auth/me without token -> 401
    res = client.get("/api/auth/me")
    assert res.status_code == 401

    # Test /api/auth/me with creator token -> 200
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {creator_token}"})
    assert res.status_code == 200
    assert res.get_json()["user"]["username"] == "creator_user"

    # Test Admin-only endpoint with Creator token -> 403 Forbidden
    res = client.get("/api/auth/admin-only", headers={"Authorization": f"Bearer {creator_token}"})
    assert res.status_code == 403

    # Test Admin-only endpoint with Admin token -> 200 Success
    res = client.get("/api/auth/admin-only", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.get_json()["role"] == "admin"


# ---------------------------------------------------------------------------
# Demo Login endpoint tests
# ---------------------------------------------------------------------------

def test_demo_login_admin(client):
    """POST /api/auth/demo-login with role=admin returns 200 + admin JWT."""
    res = client.post(
        "/api/auth/demo-login",
        data=json.dumps({"role": "admin"}),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "manager@brandguard.ai"
    assert "token" in data
    assert "password" not in data  # password never leaks


def test_demo_login_creator(client):
    """POST /api/auth/demo-login with role=creator returns 200 + creator JWT."""
    res = client.post(
        "/api/auth/demo-login",
        data=json.dumps({"role": "creator"}),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["role"] == "creator"
    assert data["user"]["email"] == "creator@brandguard.ai"
    assert "token" in data


def test_demo_login_invalid_role(client):
    """POST /api/auth/demo-login with unknown role returns 400."""
    res = client.post(
        "/api/auth/demo-login",
        data=json.dumps({"role": "superadmin"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "Invalid demo role" in data["error"]


def test_demo_login_missing_role(client):
    """POST /api/auth/demo-login without role returns 400."""
    res = client.post(
        "/api/auth/demo-login",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False


def test_demo_login_idempotent(client):
    """Calling demo-login twice for admin must return the same user ID (no duplicates)."""
    res1 = client.post(
        "/api/auth/demo-login",
        data=json.dumps({"role": "admin"}),
        content_type="application/json",
    )
    res2 = client.post(
        "/api/auth/demo-login",
        data=json.dumps({"role": "admin"}),
        content_type="application/json",
    )
    assert res1.status_code == 200
    assert res2.status_code == 200
    # Same user – same ID – no duplicate created
    assert res1.get_json()["user"]["id"] == res2.get_json()["user"]["id"]
