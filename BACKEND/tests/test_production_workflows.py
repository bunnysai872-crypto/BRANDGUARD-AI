import json
import pytest
from unittest.mock import patch, MagicMock
from app.models import db, User, Brand, BrandGuideline, ContentSubmission, ContentRevision, ReviewDecision

def get_auth_headers(client, username, email, password, role="creator"):
    res = client.post("/api/auth/register", data=json.dumps({
        "username": username,
        "email": email,
        "password": password,
        "full_name": f"Test {username}",
        "role": role
    }), content_type="application/json")
    assert res.status_code == 201
    data = res.get_json()
    token = data.get("token")
    user_id = data.get("user", {}).get("id")
    return {"Authorization": f"Bearer {token}"}, user_id

def test_production_health_check_safety(client):
    """Verify health check endpoint returns 200, checks DB, and never exposes credentials."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["service"] == "BrandGuard AI Backend"
    assert "version" in data
    # Ensure sensitive credentials are NOT exposed
    assert "GEMINI_API_KEY" not in str(data)
    assert "SECRET_KEY" not in str(data)
    assert "password" not in str(data).lower()

def test_role_authorization_and_cross_user_isolation(client):
    """Verify creators cannot review their own submissions, and cannot access other creators' submissions."""
    manager_headers, manager_id = get_auth_headers(
        client, "prod_mgr_1", "prod_mgr_1@brand.com", "Password123!", "admin"
    )
    creator1_headers, creator1_id = get_auth_headers(
        client, "prod_crt_1", "prod_crt_1@brand.com", "Password123!", "creator"
    )
    creator2_headers, creator2_id = get_auth_headers(
        client, "prod_crt_2", "prod_crt_2@brand.com", "Password123!", "creator"
    )

    # 1. Manager creates Brand and assigns Creator 1
    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "ApexSecurity",
        "tone_style": "Authoritative",
        "restricted_words": "Hack-proof, 100% impenetrable"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator1_id
    }), content_type="application/json")

    # 2. Creator 1 creates a draft
    s_res = client.post("/api/submissions", headers=creator1_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "Apex Security Launch Campaign",
        "content_text": "ApexSecurity provides next-gen cybersecurity software for modern enterprises."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # 3. Creator 2 attempts to read Creator 1's draft -> 403 Forbidden
    res = client.get(f"/api/submissions/{sub_id}", headers=creator2_headers)
    assert res.status_code == 403

    # 4. Creator 2 attempts to edit Creator 1's draft -> 403 Forbidden
    res = client.put(f"/api/submissions/{sub_id}", headers=creator2_headers, data=json.dumps({
        "title": "Hijacked Title",
        "content_text": "Unauthorized modification"
    }), content_type="application/json")
    assert res.status_code == 403

    # 5. Creator 1 attempts to review/approve their own submission -> 403 Forbidden
    res = client.post(f"/api/submissions/{sub_id}/review", headers=creator1_headers, data=json.dumps({
        "decision": "Approved",
        "review_comments": "Self-approving my own copy"
    }), content_type="application/json")
    assert res.status_code == 403
    assert "Only Brand Managers can" in res.get_json()["error"]

    # 6. Manager attempts to review draft before creator submitted for approval -> 400 Bad Request
    res = client.post(f"/api/submissions/{sub_id}/review", headers=manager_headers, data=json.dumps({
        "decision": "Approved",
        "review_comments": "Trying to approve unsubmitted draft"
    }), content_type="application/json")
    assert res.status_code == 400
    assert "not pending manager approval" in res.get_json()["error"]

def test_complete_end_to_end_governance_lifecycle(client):
    """
    Test complete lifecycle:
    Draft -> AI Review (violations) -> Rejected approval attempt -> Acknowledged submission
    -> Manager Requests Changes -> Creator revises (Rev 2, auto-reset to Draft)
    -> AI Re-review (clean) -> Submit Approval -> Manager Approves -> Edit locked -> Audit trail
    """
    manager_headers, manager_id = get_auth_headers(
        client, "e2e_mgr", "e2e_mgr@corp.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "e2e_crt", "e2e_crt@corp.com", "Password123!", "creator"
    )

    # 1. Manager creates Brand and Guideline
    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "NovaPay",
        "tone_style": "Professional, Trustworthy",
        "restricted_words": "Zero transaction fees forever"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    # 2. Creator creates initial submission with restricted claim
    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "NovaPay Launch Promo",
        "content_text": "Experience NovaPay payments with zero transaction fees forever guaranteed."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # 3. AI analysis flags High severity violation
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "summary": "Restricted fee claim detected.",
        "review_status": "Violations Detected",
        "findings": [{
            "category": "Restricted Claims",
            "severity": "High",
            "problematic_text": "zero transaction fees forever guaranteed",
            "explanation": "Guarantees of zero fees forever violate regulatory transparency policies.",
            "suggested_correction": "Experience NovaPay with industry-leading low transaction fees.",
            "human_verification_required": False
        }]
    })
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)
        assert res.status_code == 201

    # 4. Creator attempts approval submission without acknowledgement -> 422
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers, data=json.dumps({
        "acknowledgement": False
    }), content_type="application/json")
    assert res.status_code == 422
    assert res.get_json()["requires_acknowledgement"] is True

    # 5. Creator acknowledges warning and submits -> Status: Pending Manager Approval
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers, data=json.dumps({
        "acknowledgement": True
    }), content_type="application/json")
    assert res.status_code == 200
    assert res.get_json()["submission"]["status"] == "Pending Manager Approval"

    # 6. Content editing is locked while pending
    res = client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "NovaPay Promo (Edit Attempt)",
        "content_text": "Attempting edit during review"
    }), content_type="application/json")
    assert res.status_code == 400
    assert "approval is pending" in res.get_json()["error"]

    # 7. Manager reviews and Requests Changes
    res = client.post(f"/api/submissions/{sub_id}/review", headers=manager_headers, data=json.dumps({
        "decision": "Changes Requested",
        "review_comments": "Please remove 'zero transaction fees forever' as it violates marketing compliance."
    }), content_type="application/json")
    assert res.status_code == 200
    assert res.get_json()["submission"]["status"] == "Changes Requested"

    # 8. Creator revises copy -> Revision #2 created, auto-reset to Draft
    res = client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "NovaPay Launch Promo (Revised)",
        "content_text": "Experience NovaPay payments with competitive, transparent transaction rates.",
        "reason": "Removed absolute zero fee guarantee"
    }), content_type="application/json")
    assert res.status_code == 200
    sub_data = res.get_json()["submission"]
    assert sub_data["status"] == "Draft"
    assert sub_data["revision_count"] == 2

    # 9. Prior AI report is outdated -> cannot submit without re-audit
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)
    assert res.status_code == 400
    assert "report is outdated" in res.get_json()["error"]

    # 10. Re-audit Revision #2 -> AI returns Compliant
    mock_clean_response = MagicMock()
    mock_clean_response.text = json.dumps({
        "summary": "Revised copy is fully compliant with brand guidelines.",
        "review_status": "Compliant",
        "findings": []
    })
    mock_client.models.generate_content.return_value = mock_clean_response

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)
        assert res.status_code == 201
        assert res.get_json()["analysis"]["review_status"] == "Compliant"

    # 11. Creator submits clean draft for approval
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)
    assert res.status_code == 200
    assert res.get_json()["submission"]["status"] == "Pending Manager Approval"

    # 12. Manager Approves content
    res = client.post(f"/api/submissions/{sub_id}/review", headers=manager_headers, data=json.dumps({
        "decision": "Approved",
        "review_comments": "Excellent revision. Copy is compliant, accurate, and approved for release."
    }), content_type="application/json")
    assert res.status_code == 200
    assert res.get_json()["submission"]["status"] == "Approved"

    # 13. Approved content is permanently locked
    res = client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "Sneak Modification",
        "content_text": "Sneaking text into approved copy"
    }), content_type="application/json")
    assert res.status_code == 400
    assert "Approved content is locked" in res.get_json()["error"]

    # 14. Verify immutable decision history contains both review events
    res = client.get(f"/api/submissions/{sub_id}/decisions", headers=creator_headers)
    assert res.status_code == 200
    decisions = res.get_json()["decisions"]
    assert len(decisions) == 2
    assert decisions[0]["decision"] == "Approved"
    assert decisions[1]["decision"] == "Changes Requested"
