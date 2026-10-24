import json
from unittest.mock import MagicMock, patch

def get_auth_headers(client, username, email, password, role):
    res = client.post("/api/auth/register", data=json.dumps({
        "username": username,
        "email": email,
        "password": password,
        "role": role,
        "full_name": f"{username.title()}"
    }), content_type="application/json")
    assert res.status_code == 201
    token = res.get_json()["token"]
    user_id = res.get_json()["user"]["id"]
    return {"Authorization": f"Bearer {token}"}, user_id

def test_missing_gemini_api_key(client):
    manager_headers, manager_id = get_auth_headers(
        client, "mgr_phase3_1", "m1@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "crt_phase3_1", "c1@brand.com", "Password123!", "creator"
    )

    # Create brand & assign creator
    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "CloudSecure AI",
        "restricted_words": "100% immune, Guaranteed"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    # Create submission
    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "CloudSecure Launch Copy",
        "content_text": "We guarantee 100% immune cloud infrastructure."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # When API key is empty
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)
        assert res.status_code == 503
        data = res.get_json()
        assert "Gemini API key is not configured" in data["error"]

def test_successful_compliance_analysis_with_mocked_gemini(client):
    manager_headers, manager_id = get_auth_headers(
        client, "mgr_phase3_2", "m2@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "crt_phase3_2", "c2@brand.com", "Password123!", "creator"
    )

    # 1. Create brand
    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "Acme Cloud",
        "tone_style": "Confident, authoritative, and fact-based",
        "approved_facts": "Our service provides encrypted cloud storage across US regions.",
        "restricted_words": "Never guarantee 100% security, flawless, miracle"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    # 2. Create actual stored guidelines
    g1_res = client.post(f"/api/brands/{brand_id}/guidelines", headers=manager_headers, data=json.dumps({
        "category": "Restricted Claims",
        "title": "No 100% Security Guarantees",
        "rule_content": "Never guarantee 100% security or complete immunity from cyberattacks.",
        "reference_evidence": "Cybersecurity Marketing Disclosure Standard 2026"
    }), content_type="application/json")
    g1_id = g1_res.get_json()["guideline"]["id"]

    # 3. Create content submission containing non-compliant claims
    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "Acme Cloud Security Announcement",
        "content_text": "Acme Cloud guarantees 100% security and completely eliminates every cyberattack."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # 4. Mock Gemini API response
    mock_ai_output = {
        "summary": "High risk detected. The copy makes absolute security promises and guarantees complete immunity from attacks.",
        "review_status": "Violations Detected",
        "findings": [
            {
                "category": "Restricted Claims",
                "severity": "High",
                "problematic_text": "guarantees 100% security",
                "explanation": "Directly breaches stored guideline prohibiting absolute security guarantees.",
                "referenced_guideline_id": g1_id,
                "suggested_correction": "provides enterprise-grade encrypted cloud storage with industry-standard safeguards",
                "human_verification_required": False
            },
            {
                "category": "Unsupported Claims",
                "severity": "High",
                "problematic_text": "completely eliminates every cyberattack",
                "explanation": "Unsubstantiated absolute claim that lacks technical verification and violates risk mitigation policy.",
                "referenced_guideline_id": None,
                "suggested_correction": "actively mitigates modern attack vectors through multi-layered defense",
                "human_verification_required": True
            }
        ]
    }

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_ai_output)
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)
        assert res.status_code == 201
        data = res.get_json()
        assert data["success"] is True
        analysis = data["analysis"]
        assert analysis["issues_count"] == 2
        assert analysis["high_severity_count"] == 2
        assert analysis["review_status"] == "Violations Detected"
        assert len(analysis["findings"]) == 2

        # Check guideline reference preservation
        finding_with_ref = [f for f in analysis["findings"] if f["guideline_id"] == g1_id][0]
        assert finding_with_ref["guideline_title"] == "No 100% Security Guarantees"

        # Check human verification requirement flag
        finding_with_human = [f for f in analysis["findings"] if f["human_verification_required"] is True][0]
        assert "eliminates every cyberattack" in finding_with_human["problematic_text"]

    # 5. Check submission status was updated to "AI Reviewed"
    sub_check = client.get(f"/api/submissions/{sub_id}", headers=creator_headers)
    assert sub_check.get_json()["submission"]["status"] == "AI Reviewed"

    # 6. Test GET /api/submissions/<id>/analysis
    get_res = client.get(f"/api/submissions/{sub_id}/analysis", headers=creator_headers)
    assert get_res.status_code == 200
    assert get_res.get_json()["analysis"]["issues_count"] == 2
    assert get_res.get_json()["analysis"]["is_outdated"] is False

def test_fabricated_guideline_id_sanitization(client):
    manager_headers, manager_id = get_auth_headers(
        client, "mgr_phase3_3", "m3@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "crt_phase3_3", "c3@brand.com", "Password123!", "creator"
    )

    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "HealthCorp",
        "approved_facts": "Organic ingredients only."
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "Supplement Ad",
        "content_text": "Cures all joint pain instantly."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # AI returns a hallucinated/fabricated guideline ID (e.g. 99999) that does NOT exist
    mock_ai_output = {
        "summary": "Medical cure claim detected.",
        "review_status": "Violations Detected",
        "findings": [
            {
                "category": "Unsupported Claims",
                "severity": "High",
                "problematic_text": "Cures all joint pain instantly",
                "explanation": "Unsupported health claim.",
                "referenced_guideline_id": 99999, # Hallucinated ID
                "suggested_correction": "Helps support healthy joint mobility",
                "human_verification_required": True
            }
        ]
    }

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_ai_output)
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)
        assert res.status_code == 201
        analysis = res.get_json()["analysis"]
        # The hallucinated ID 99999 must have been stripped to None
        assert analysis["findings"][0]["guideline_id"] is None

def test_stale_report_detection_after_content_revision(client):
    manager_headers, manager_id = get_auth_headers(
        client, "mgr_phase3_4", "m4@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "crt_phase3_4", "c4@brand.com", "Password123!", "creator"
    )

    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "PaySwift",
        "restricted_words": "Zero fees forever"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "PaySwift Launch",
        "content_text": "Zero fees forever on international transfers."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # 1. Run analysis on Revision #1
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "summary": "Restricted claim detected.",
        "review_status": "Violations Detected",
        "findings": [
            {
                "category": "Restricted Claims",
                "severity": "High",
                "problematic_text": "Zero fees forever",
                "explanation": "Violates fee policy.",
                "referenced_guideline_id": None,
                "suggested_correction": "Low transparent fees",
                "human_verification_required": False
            }
        ]
    })
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)
        assert res.status_code == 201

    # Check report is NOT outdated
    res = client.get(f"/api/submissions/{sub_id}/analysis", headers=creator_headers)
    assert res.get_json()["analysis"]["is_outdated"] is False

    # 2. Creator edits content -> Revision #2 created
    client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "PaySwift Launch (Revised)",
        "content_text": "Competitive exchange rates on international transfers.",
        "reason": "Removed zero fee claim",
        "status": "Ready for AI Review"
    }), content_type="application/json")

    # 3. Check report is now marked as OUTDATED / STALE
    res = client.get(f"/api/submissions/{sub_id}/analysis", headers=creator_headers)
    assert res.status_code == 200
    assert res.get_json()["analysis"]["is_outdated"] is True
    assert res.get_json()["analysis"]["revision_number"] == 1
    assert res.get_json()["analysis"]["current_submission_revision"] == 2

def test_malformed_ai_response_handling(client):
    manager_headers, manager_id = get_auth_headers(
        client, "mgr_phase3_5", "m5@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "crt_phase3_5", "c5@brand.com", "Password123!", "creator"
    )

    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "RoboTech",
        "tone_style": "Scientific"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "RoboTech Ad",
        "content_text": "RoboTech makes life easier."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # Mock response returns unparseable non-JSON string
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Error: I am unable to analyze this text."
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)
        assert res.status_code == 502
        assert "Failed to parse AI output as JSON" in res.get_json()["error"]
