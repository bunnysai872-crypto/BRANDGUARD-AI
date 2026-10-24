import io
import json
from unittest.mock import MagicMock, patch
from app.models import db, ContentSubmission, ContentRevision, ReviewDecision, Brand, BrandGuideline, User

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

def test_guideline_crud_and_new_fields(client):
    """Test 1: Creating, reading, updating, and toggling guidelines with severity and approved/prohibited wording."""
    mgr_headers, mgr_id = get_auth_headers(client, "g_mgr", "g_mgr@test.com", "Password123!", "admin")

    # Create Brand
    b_res = client.post("/api/brands", headers=mgr_headers, data=json.dumps({
        "name": "Nova Health",
        "tone_style": "Scientific, Empathetic"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    # 1. Create guideline with full fields
    g_res = client.post(f"/api/brands/{brand_id}/guidelines", headers=mgr_headers, data=json.dumps({
        "category": "Approved Facts",
        "title": "Clinical Trial Metric",
        "rule_content": "Always cite the 99.4% efficacy from phase 3 clinical study.",
        "approved_wording": "99.4% verified patient satisfaction in double-blind trials.",
        "prohibited_wording": "100% cure guarantee",
        "severity": "Critical",
        "reference_evidence": "Clinical Trial Registry #CTR-8812",
        "is_active": True
    }), content_type="application/json")
    assert g_res.status_code == 201
    g_data = g_res.get_json()["guideline"]
    guideline_id = g_data["id"]
    assert g_data["severity"] == "Critical"
    assert g_data["approved_wording"] == "99.4% verified patient satisfaction in double-blind trials."
    assert g_data["prohibited_wording"] == "100% cure guarantee"
    assert g_data["is_active"] is True

    # 2. Toggle active status
    t_res = client.post(f"/api/guidelines/{guideline_id}/toggle-active", headers=mgr_headers)
    assert t_res.status_code == 200
    assert t_res.get_json()["guideline"]["is_active"] is False

    # Toggle back to active
    t_res2 = client.post(f"/api/guidelines/{guideline_id}/toggle-active", headers=mgr_headers)
    assert t_res2.status_code == 200
    assert t_res2.get_json()["guideline"]["is_active"] is True

    # 3. Fetch guidelines filtered by category
    f_res = client.get(f"/api/brands/{brand_id}/guidelines?category=Approved Facts", headers=mgr_headers)
    assert f_res.status_code == 200
    assert len(f_res.get_json()["guidelines"]) == 1

def test_cross_brand_guideline_isolation(client):
    """Test 2: Prevent users from accessing another brand's guidelines."""
    mgr_a_headers, _ = get_auth_headers(client, "mgr_a", "mgr_a@test.com", "Password123!", "admin")
    crt_b_headers, crt_b_id = get_auth_headers(client, "crt_b", "crt_b@test.com", "Password123!", "creator")

    # Manager A creates Brand A
    b_res = client.post("/api/brands", headers=mgr_a_headers, data=json.dumps({
        "name": "Confidential Brand A"
    }), content_type="application/json")
    brand_a_id = b_res.get_json()["brand"]["id"]

    # Manager A adds a guideline to Brand A
    g_res = client.post(f"/api/brands/{brand_a_id}/guidelines", headers=mgr_a_headers, data=json.dumps({
        "category": "Restricted Claims",
        "title": "Secret Formula",
        "rule_content": "Never reveal secret compound X"
    }), content_type="application/json")
    g_id = g_res.get_json()["guideline"]["id"]

    # Creator B (not a member of Brand A) attempts to read Brand A's guidelines
    read_res = client.get(f"/api/brands/{brand_a_id}/guidelines", headers=crt_b_headers)
    assert read_res.status_code == 403

    # Creator B attempts to read guideline by ID directly
    single_res = client.get(f"/api/guidelines/{g_id}", headers=crt_b_headers)
    assert single_res.status_code == 403

def test_document_text_extraction(client):
    """Test 14: Secure document upload validation for .txt and .pdf text extraction."""
    mgr_headers, _ = get_auth_headers(client, "doc_mgr", "doc_mgr@test.com", "Password123!", "admin")

    # 1. Valid TXT upload
    txt_content = b"Brand Rule: Always use lowercase for product handles @cloudnova."
    data = {
        'file': (io.BytesIO(txt_content), 'guidelines.txt')
    }
    res = client.post("/api/guidelines/extract-text", headers=mgr_headers, data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    assert "Always use lowercase for product handles" in res.get_json()["extracted_text"]

    # 2. Unsupported extension (e.g. .exe or .py)
    bad_data = {
        'file': (io.BytesIO(b"malicious script"), 'hack.exe')
    }
    bad_res = client.post("/api/guidelines/extract-text", headers=mgr_headers, data=bad_data, content_type='multipart/form-data')
    assert bad_res.status_code == 400
    assert "Unsupported file format" in bad_res.get_json()["error"]

def test_ai_review_grounded_in_brand_guidelines(client):
    """Test 3 & 5: AI review using active brand guidelines, returning confidence level & structured findings."""
    mgr_headers, mgr_id = get_auth_headers(client, "ai_mgr", "ai_mgr@test.com", "Password123!", "admin")
    crt_headers, crt_id = get_auth_headers(client, "ai_crt", "ai_crt@test.com", "Password123!", "creator")

    # Create Brand & assign Creator
    b_res = client.post("/api/brands", headers=mgr_headers, data=json.dumps({
        "name": "CloudNova FinTech",
        "tone_style": "Conservative, Compliant"
    }), content_type="application/json")
    b_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{b_id}/members", headers=mgr_headers, data=json.dumps({
        "user_id": crt_id,
        "role": "contributor"
    }), content_type="application/json")

    # Add active guideline
    g_res = client.post(f"/api/brands/{b_id}/guidelines", headers=mgr_headers, data=json.dumps({
        "category": "Prohibited Claims",
        "title": "No Guaranteed Investment Returns",
        "rule_content": "Never claim 100% risk-free returns or guaranteed yields.",
        "prohibited_wording": "risk-free, guaranteed returns",
        "severity": "Critical",
        "is_active": True
    }), content_type="application/json")
    g_id = g_res.get_json()["guideline"]["id"]

    # Creator creates submission with violation
    s_res = client.post("/api/submissions", headers=crt_headers, data=json.dumps({
        "brand_id": b_id,
        "title": "Crypto Fund Pitch",
        "content_text": "Invest in CloudNova Vault for 100% risk-free guaranteed returns!"
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # Mock Gemini response with confidence level and critical severity
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "summary": "Violations detected against FinTech brand rules.",
        "review_status": "Violations Detected",
        "findings": [
            {
                "category": "Prohibited Claims",
                "severity": "Critical",
                "problematic_text": "100% risk-free guaranteed returns",
                "explanation": "Violates explicit prohibition against guaranteed return promises.",
                "referenced_guideline_id": g_id,
                "guideline_title": "No Guaranteed Investment Returns",
                "suggested_correction": "competitive market-rate yields subject to market volatility",
                "confidence_level": "High",
                "human_verification_required": True
            }
        ]
    })
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        analyze_res = client.post(f"/api/submissions/{sub_id}/analyze", headers=crt_headers)
        assert analyze_res.status_code == 201
        analysis = analyze_res.get_json()["analysis"]
        assert analysis["review_status"] == "Violations Detected"
        assert analysis["critical_severity_count"] == 1
        finding = analysis["findings"][0]
        assert finding["confidence_level"] == "High"
        assert finding["severity"] == "Critical"
        assert finding["guideline_title"] == "No Guaranteed Investment Returns"

def test_missing_or_insufficient_guidelines(client):
    """Test 4: Correct handling when brand has zero active guidelines."""
    mgr_headers, mgr_id = get_auth_headers(client, "empty_mgr", "empty_mgr@test.com", "Password123!", "admin")
    crt_headers, crt_id = get_auth_headers(client, "empty_crt", "empty_crt@test.com", "Password123!", "creator")

    # 1. Brand with completely empty rules returns 400 with explanation
    b_res = client.post("/api/brands", headers=mgr_headers, data=json.dumps({
        "name": "Barebones Brand"
    }), content_type="application/json")
    b_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{b_id}/members", headers=mgr_headers, data=json.dumps({
        "user_id": crt_id
    }), content_type="application/json")

    s_res = client.post("/api/submissions", headers=crt_headers, data=json.dumps({
        "brand_id": b_id,
        "title": "Generic Promo",
        "content_text": "Check out our services today."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    res_empty = client.post(f"/api/submissions/{sub_id}/analyze", headers=crt_headers)
    assert res_empty.status_code == 400
    assert "has no registered guidelines" in res_empty.get_json()["error"]

    # 2. Brand with baseline tone style but zero specific guidelines evaluates with limited disclosure
    client.put(f"/api/brands/{b_id}", headers=mgr_headers, data=json.dumps({
        "name": "Barebones Brand",
        "tone_style": "Simple and straightforward"
    }), content_type="application/json")

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "summary": "Review performed with limited available guidelines.",
        "review_status": "Compliant",
        "findings": []
    })
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        res_limited = client.post(f"/api/submissions/{sub_id}/analyze", headers=crt_headers)
        assert res_limited.status_code == 201
        call_args = mock_client.models.generate_content.call_args[1]
        assert "zero registered guideline rules" in call_args["contents"]

def test_ai_failure_and_malformed_response_handling(client):
    """Test 6: Graceful error response when Gemini raises exception or returns malformed JSON."""
    mgr_headers, mgr_id = get_auth_headers(client, "fail_mgr", "fail_mgr@test.com", "Password123!", "admin")
    crt_headers, crt_id = get_auth_headers(client, "fail_crt", "fail_crt@test.com", "Password123!", "creator")

    b_res = client.post("/api/brands", headers=mgr_headers, data=json.dumps({
        "name": "Resilient Brand",
        "tone_style": "Professional"
    }), content_type="application/json")
    b_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{b_id}/members", headers=mgr_headers, data=json.dumps({"user_id": crt_id}), content_type="application/json")
    s_res = client.post("/api/submissions", headers=crt_headers, data=json.dumps({
        "brand_id": b_id,
        "title": "Promo Copy",
        "content_text": "Sample promotional text."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # 1. API exception -> 502
    mock_err_client = MagicMock()
    mock_err_client.models.generate_content.side_effect = Exception("Gemini API connection timeout")
    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_err_client, None)):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=crt_headers)
        assert res.status_code == 502
        assert "Gemini API request failed" in res.get_json()["error"]

    # 2. Malformed non-JSON output -> 502
    mock_bad = MagicMock()
    bad_resp = MagicMock()
    bad_resp.text = "This is not valid JSON from the LLM"
    mock_bad.models.generate_content.return_value = bad_resp

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_bad, None)):
        res2 = client.post(f"/api/submissions/{sub_id}/analyze", headers=crt_headers)
        assert res2.status_code == 502
        assert "Failed to parse" in res2.get_json()["error"]

def test_revision_history_persistence(client):
    """Test 8: Editing content persists previous revisions without overwriting history."""
    mgr_headers, _ = get_auth_headers(client, "rev_mgr", "rev_mgr@test.com", "Password123!", "admin")
    crt_headers, crt_id = get_auth_headers(client, "rev_crt", "rev_crt@test.com", "Password123!", "creator")

    b_res = client.post("/api/brands", headers=mgr_headers, data=json.dumps({"name": "Revision Brand"}), content_type="application/json")
    b_id = b_res.get_json()["brand"]["id"]
    client.post(f"/api/brands/{b_id}/members", headers=mgr_headers, data=json.dumps({"user_id": crt_id}), content_type="application/json")

    s_res = client.post("/api/submissions", headers=crt_headers, data=json.dumps({
        "brand_id": b_id,
        "title": "Version 1",
        "content_text": "Initial copy text."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # Edit 1
    client.put(f"/api/submissions/{sub_id}", headers=crt_headers, data=json.dumps({
        "title": "Version 2",
        "content_text": "Updated second revision copy.",
        "revision_reason": "Tone improvement"
    }), content_type="application/json")

    # Fetch revisions
    details = client.get(f"/api/submissions/{sub_id}", headers=crt_headers).get_json()["submission"]
    assert len(details["revisions"]) >= 2
    assert details["content_text"] == "Updated second revision copy."
    rev_texts = [r["content_text"] for r in details["revisions"]]
    assert "Initial copy text." in rev_texts
    assert "Updated second revision copy." in rev_texts

def test_governance_analytics_calculated_from_db(client):
    """Test 9: Analytics endpoint computes real metrics from database records."""
    mgr_headers, _ = get_auth_headers(client, "stat_mgr", "stat_mgr@test.com", "Password123!", "admin")

    # Ensure manager has an accessible brand so metrics calculate from active records
    b_res = client.post("/api/brands", headers=mgr_headers, data=json.dumps({
        "name": "Metrics Unique Analytics Brand",
        "tone_style": "Data-driven"
    }), content_type="application/json")
    assert b_res.status_code in [201, 409]

    # Call analytics endpoint
    res = client.get("/api/analytics", headers=mgr_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    metrics = data["metrics"]
    assert "total_submissions" in metrics
    assert "approved_count" in metrics
    assert "published_count" in metrics
    assert "avg_revisions_per_submission" in metrics
    assert "severity_distribution" in data
    assert "Critical" in data["severity_distribution"]
    assert "governance_note" in data
    assert "do not necessarily prove causation" in data["governance_note"]

def test_publish_workflow_security_and_edit_locking(client):
    """Test 7, 10, 11, 12, 13: Publishing requires approval, locks editing, prevents duplicate publishing, enforces manager-only."""
    mgr_headers, mgr_id = get_auth_headers(client, "gate_mgr", "gate_mgr@test.com", "Password123!", "admin")
    crt_headers, crt_id = get_auth_headers(client, "gate_crt", "gate_crt@test.com", "Password123!", "creator")

    b_res = client.post("/api/brands", headers=mgr_headers, data=json.dumps({
        "name": "Gated Unique Brand",
        "tone_style": "Security-first, transparent"
    }), content_type="application/json")
    b_id = b_res.get_json()["brand"]["id"]
    client.post(f"/api/brands/{b_id}/members", headers=mgr_headers, data=json.dumps({"user_id": crt_id}), content_type="application/json")

    s_res = client.post("/api/submissions", headers=crt_headers, data=json.dumps({
        "brand_id": b_id,
        "title": "Gated Content",
        "content_text": "High security content ready for publication pipeline."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # 1. Creator attempts to publish own draft -> 403 Forbidden
    crt_pub = client.post(f"/api/submissions/{sub_id}/publish", headers=crt_headers)
    assert crt_pub.status_code == 403

    # 2. Manager attempts to publish while status is 'Draft' -> 400 Bad Request
    mgr_early_pub = client.post(f"/api/submissions/{sub_id}/publish", headers=mgr_headers)
    assert mgr_early_pub.status_code == 400
    assert "Only 'Approved'" in mgr_early_pub.get_json()["error"]

    # 3. Simulate compliant review & manager approval
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({"summary": "Approved", "review_status": "Compliant", "findings": []})
    mock_client.models.generate_content.return_value = mock_resp

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        a_res = client.post(f"/api/submissions/{sub_id}/analyze", headers=crt_headers)
        assert a_res.status_code == 201

    client.post(f"/api/submissions/{sub_id}/submit-approval", headers=crt_headers)
    appr_res = client.post(f"/api/submissions/{sub_id}/review", headers=mgr_headers, data=json.dumps({
        "decision": "Approved",
        "review_comments": "Looks great, fully compliant with brand guidelines."
    }), content_type="application/json")
    assert appr_res.status_code == 200

    # 4. Successful publish by manager
    pub_res = client.post(f"/api/submissions/{sub_id}/publish", headers=mgr_headers)
    assert pub_res.status_code == 200
    sub_data = pub_res.get_json()["submission"]
    assert sub_data["status"] == "Published"
    assert sub_data["published_at"] is not None
    assert sub_data["published_by_id"] == mgr_id

    # 5. Duplicate publishing prevention -> 400 Bad Request
    dup_pub = client.post(f"/api/submissions/{sub_id}/publish", headers=mgr_headers)
    assert dup_pub.status_code == 400
    assert "already been published" in dup_pub.get_json()["error"]

    # 6. Published content edit locking -> 400 Bad Request
    edit_locked = client.put(f"/api/submissions/{sub_id}", headers=crt_headers, data=json.dumps({
        "title": "Hacked edit",
        "content_text": "Trying to modify locked published copy"
    }), content_type="application/json")
    assert edit_locked.status_code == 400
    assert "locked" in edit_locked.get_json()["error"]
