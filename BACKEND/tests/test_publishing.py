import json
from unittest.mock import MagicMock, patch
from app.models import db, ContentSubmission, ContentRevision, ReviewDecision, Brand

def get_auth_headers(client, username, email, password, role="creator"):
    res = client.post("/api/auth/register", data=json.dumps({
        "username": username,
        "email": email,
        "password": password,
        "full_name": f"Test {username.title()}",
        "role": role
    }), content_type="application/json")
    assert res.status_code == 201
    data = res.get_json()
    token = data.get("token")
    user_id = data.get("user", {}).get("id")
    return {"Authorization": f"Bearer {token}"}, user_id

def setup_approved_submission(client):
    """Helper to create brand, assign creator, run AI audit, and have manager approve content."""
    manager_headers, manager_id = get_auth_headers(
        client, "pub_mgr", "pub_mgr@test.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "pub_crt", "pub_crt@test.com", "Password123!", "creator"
    )

    # 1. Manager creates Brand
    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "CloudNova Gov",
        "tone_style": "Professional, Reliable",
        "approved_facts": "CloudNova holds SOC2 Type II compliance.",
        "restricted_words": "Cheap, Unlimited free tier"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    # 2. Assign creator to brand
    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id,
        "role": "contributor"
    }), content_type="application/json")

    # 3. Creator creates submission
    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "CloudNova Enterprise Solutions",
        "content_text": "CloudNova holds SOC2 Type II compliance for enterprise workloads."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # 4. Mock AI Analysis (Compliant)
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "summary": "Copy is fully compliant with brand guidelines.",
        "review_status": "Compliant",
        "findings": []
    })
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)
        assert res.status_code == 201

    # 5. Creator submits for approval
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)
    assert res.status_code == 200
    assert res.get_json()["submission"]["status"] == "Pending Manager Approval"

    # 6. Manager approves content
    res = client.post(f"/api/submissions/{sub_id}/review", headers=manager_headers, data=json.dumps({
        "decision": "Approved",
        "review_comments": "Approved for official publishing."
    }), content_type="application/json")
    assert res.status_code == 200
    assert res.get_json()["submission"]["status"] == "Approved"

    return manager_headers, creator_headers, sub_id, brand_id


def test_successful_publishing_by_authorized_manager(client):
    """Test authorized Brand Manager can successfully publish an Approved submission."""
    manager_headers, creator_headers, sub_id, brand_id = setup_approved_submission(client)

    # Manager publishes the approved submission
    res = client.post(f"/api/submissions/{sub_id}/publish", headers=manager_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "published successfully" in data["message"].lower()
    assert data["submission"]["status"] == "Published"
    assert data["submission"]["id"] == sub_id

    # Verify persistent state in database
    get_res = client.get(f"/api/submissions/{sub_id}", headers=manager_headers)
    assert get_res.status_code == 200
    assert get_res.get_json()["submission"]["status"] == "Published"


def test_creator_cannot_publish_directly(client):
    """Test that a creator attempting to publish gets 403 Forbidden."""
    manager_headers, creator_headers, sub_id, brand_id = setup_approved_submission(client)

    # Creator tries to publish
    res = client.post(f"/api/submissions/{sub_id}/publish", headers=creator_headers)
    assert res.status_code == 403
    data = res.get_json()
    assert data["success"] is False
    assert "Only Brand Managers can publish" in data["error"]

    # Submission status must remain Approved
    get_res = client.get(f"/api/submissions/{sub_id}", headers=creator_headers)
    assert get_res.get_json()["submission"]["status"] == "Approved"


def test_publishing_without_approval_rejected(client):
    """Test that publishing attempts on Draft, AI Reviewed, Pending Approval, or Changes Requested are rejected."""
    manager_headers, manager_id = get_auth_headers(
        client, "unapp_mgr", "unapp_mgr@test.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "unapp_crt", "unapp_crt@test.com", "Password123!", "creator"
    )

    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "NovaSecure Brand"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    # 1. Draft submission -> cannot publish
    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "Draft Post",
        "content_text": "Draft promotional content"
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    res = client.post(f"/api/submissions/{sub_id}/publish", headers=manager_headers)
    assert res.status_code == 400
    assert "Only 'Approved' submissions can be published" in res.get_json()["error"]

    # 2. AI Reviewed -> cannot publish
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "summary": "AI audit done.",
        "review_status": "Compliant",
        "findings": []
    })
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)

    res = client.post(f"/api/submissions/{sub_id}/publish", headers=manager_headers)
    assert res.status_code == 400
    assert "Only 'Approved' submissions can be published" in res.get_json()["error"]

    # 3. Pending Manager Approval -> cannot publish
    client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)
    res = client.post(f"/api/submissions/{sub_id}/publish", headers=manager_headers)
    assert res.status_code == 400
    assert "Only 'Approved' submissions can be published" in res.get_json()["error"]

    # 4. Changes Requested -> cannot publish
    client.post(f"/api/submissions/{sub_id}/review", headers=manager_headers, data=json.dumps({
        "decision": "Changes Requested",
        "review_comments": "Please update copy before signoff."
    }), content_type="application/json")

    res = client.post(f"/api/submissions/{sub_id}/publish", headers=manager_headers)
    assert res.status_code == 400
    assert "Only 'Approved' submissions can be published" in res.get_json()["error"]


def test_publishing_already_published_submission_rejected(client):
    """Test that publishing an already Published submission returns 400."""
    manager_headers, creator_headers, sub_id, brand_id = setup_approved_submission(client)

    # First publish succeeds
    res = client.post(f"/api/submissions/{sub_id}/publish", headers=manager_headers)
    assert res.status_code == 200

    # Second publish fails with clear message
    res2 = client.post(f"/api/submissions/{sub_id}/publish", headers=manager_headers)
    assert res2.status_code == 400
    data = res2.get_json()
    assert data["success"] is False
    assert "already been published" in data["error"].lower()


def test_cross_brand_and_isolation_publishing_rules(client):
    """Test access isolation: unassigned creator from another brand cannot access or publish submission."""
    manager_headers, creator1_headers, sub_id, brand_id = setup_approved_submission(client)

    # Creator 2 belongs to another brand (or no brand)
    creator2_headers, creator2_id = get_auth_headers(
        client, "other_crt", "other_crt@test.com", "Password123!", "creator"
    )

    # Creator 2 cannot read Brand 1's submission
    res = client.get(f"/api/submissions/{sub_id}", headers=creator2_headers)
    assert res.status_code == 403
    assert "Access denied" in res.get_json()["error"]

    # Creator 2 cannot publish Brand 1's submission
    res = client.post(f"/api/submissions/{sub_id}/publish", headers=creator2_headers)
    assert res.status_code == 403
    assert "Only Brand Managers can publish" in res.get_json()["error"]


def test_published_content_permanently_locked_against_edits(client):
    """Test that published content cannot be modified, resubmitted, or review-altered."""
    manager_headers, creator_headers, sub_id, brand_id = setup_approved_submission(client)

    # Publish
    res = client.post(f"/api/submissions/{sub_id}/publish", headers=manager_headers)
    assert res.status_code == 200

    # Creator tries to edit published content -> 400 Locked
    res = client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "Tampered Title",
        "content_text": "Trying to edit published text"
    }), content_type="application/json")
    assert res.status_code == 400
    assert "Published content is locked and cannot be edited" in res.get_json()["error"]

    # Creator tries to submit published content for approval -> 400
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)
    assert res.status_code == 400
    assert "already been published" in res.get_json()["error"]

    # Manager tries to review published content -> 400
    res = client.post(f"/api/submissions/{sub_id}/review", headers=manager_headers, data=json.dumps({
        "decision": "Approved",
        "review_comments": "Attempting re-review"
    }), content_type="application/json")
    assert res.status_code == 400
    assert "not pending manager approval" in res.get_json()["error"]
