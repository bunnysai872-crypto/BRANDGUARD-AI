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

def test_approval_submission_validation_rules(client):
    manager_headers, manager_id = get_auth_headers(
        client, "mgr_p4_1", "m_p4_1@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "crt_p4_1", "c_p4_1@brand.com", "Password123!", "creator"
    )

    # 1. Create brand and assign creator
    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "CloudNova",
        "tone_style": "Professional",
        "approved_facts": "CloudNova serves 50,000 enterprise customers.",
        "restricted_words": "Zero downtime guaranteed"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    # 2. Create submission without running AI analysis
    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "CloudNova Enterprise Ad",
        "content_text": "Join CloudNova enterprise cloud infrastructure today."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # 3. Creator tries to submit unanalyzed draft for approval -> 400 rejected
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)
    assert res.status_code == 400
    assert "must have a successful AI compliance analysis" in res.get_json()["error"]

    # 4. Run AI analysis with mock clean response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "summary": "Copy is fully compliant with brand guidelines.",
        "review_status": "Compliant",
        "findings": []
    })
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        res = client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)
        assert res.status_code == 201

    # 5. Creator edits content -> Revision #2 created (analysis becomes outdated)
    client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "CloudNova Enterprise Ad (Edited)",
        "content_text": "Join CloudNova enterprise cloud infrastructure today with zero downtime guaranteed.",
        "reason": "Updated wording"
    }), content_type="application/json")

    # 6. Outdated AI analysis blocks approval submission -> 400 rejected
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)
    assert res.status_code == 400
    assert "AI compliance report is outdated" in res.get_json()["error"]

    # 7. Re-analyze Revision #2 with high severity violation
    mock_response.text = json.dumps({
        "summary": "High severity restricted claim detected.",
        "review_status": "Violations Detected",
        "findings": [
            {
                "category": "Restricted Claims",
                "severity": "High",
                "problematic_text": "zero downtime guaranteed",
                "explanation": "Guarantees zero downtime which breaches brand policy.",
                "referenced_guideline_id": None,
                "suggested_correction": "industry-leading 99.99% uptime SLA",
                "human_verification_required": True
            }
        ]
    })
    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)

    # 8. Submit without acknowledgement when high severity warning exists -> 422 Requires acknowledgement
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers, data=json.dumps({
        "acknowledgement": False
    }), content_type="application/json")
    assert res.status_code == 422
    assert res.get_json()["requires_acknowledgement"] is True

    # 9. Submit WITH acknowledgement -> 200 Success, status is "Pending Manager Approval"
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers, data=json.dumps({
        "acknowledgement": True
    }), content_type="application/json")
    assert res.status_code == 200
    assert res.get_json()["submission"]["status"] == "Pending Manager Approval"

    # 10. Duplicate submission is rejected -> 400
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)
    assert res.status_code == 400
    assert "already pending manager approval" in res.get_json()["error"]

    # 11. Creator cannot edit while pending approval -> 400
    res = client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "Unauthorized Mid-Review Edit"
    }), content_type="application/json")
    assert res.status_code == 400
    assert "cannot be edited while manager approval is pending" in res.get_json()["error"]

def test_manager_queue_and_review_workflow(client):
    manager_headers, manager_id = get_auth_headers(
        client, "mgr_p4_2", "m_p4_2@brand.com", "Password123!", "admin"
    )
    other_manager_headers, other_mgr_id = get_auth_headers(
        client, "mgr_p4_unauthorized", "m_p4_unauth@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "crt_p4_2", "c_p4_2@brand.com", "Password123!", "creator"
    )

    # Manager creates brand and assigns creator
    b_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "Apex Security",
        "tone_style": "Rigorous"
    }), content_type="application/json")
    brand_id = b_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    # Create submission
    s_res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "Apex Zero-Trust Launch",
        "content_text": "Deploy Apex Zero-Trust architecture across distributed workloads."
    }), content_type="application/json")
    sub_id = s_res.get_json()["submission"]["id"]

    # Run AI compliance
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "summary": "Compliant technical overview.",
        "review_status": "Compliant",
        "findings": []
    })
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)

    # Submit for approval
    client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)

    # 1. Manager views review queue -> sees 1 pending submission
    q_res = client.get("/api/submissions/queue", headers=manager_headers)
    assert q_res.status_code == 200
    queue = q_res.get_json()["queue"]
    assert len(queue) >= 1
    target_item = [item for item in queue if item["id"] == sub_id][0]
    assert target_item["status"] == "Pending Manager Approval"
    assert target_item["brand_name"] == "Apex Security"

    # 2. Manager requests changes
    rev_res = client.post(f"/api/submissions/{sub_id}/review", headers=manager_headers, data=json.dumps({
        "decision": "Changes Requested",
        "comments": "Please add explicit mention of Kubernetes support in paragraph 1."
    }), content_type="application/json")
    assert rev_res.status_code == 200
    assert rev_res.get_json()["submission"]["status"] == "Changes Requested"
    assert rev_res.get_json()["decision"]["decision"] == "Changes Requested"
    assert rev_res.get_json()["decision"]["review_comments"] == "Please add explicit mention of Kubernetes support in paragraph 1."

    # 3. Creator can now edit content because changes were requested -> revision count increments, status resets to Draft
    edit_res = client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "Apex Zero-Trust Launch (v2)",
        "content_text": "Deploy Apex Zero-Trust architecture across distributed Kubernetes workloads.",
        "reason": "Added Kubernetes support mention per manager review"
    }), content_type="application/json")
    assert edit_res.status_code == 200
    assert edit_res.get_json()["submission"]["status"] == "Draft"
    assert edit_res.get_json()["submission"]["revision_count"] == 2

    # 4. Re-analyze Revision #2
    with patch("app.services.compliance_service.ComplianceService._get_gemini_client", return_value=(mock_client, None)):
        client.post(f"/api/submissions/{sub_id}/analyze", headers=creator_headers)

    # 5. Creator re-submits for approval
    res = client.post(f"/api/submissions/{sub_id}/submit-approval", headers=creator_headers)
    assert res.status_code == 200
    assert res.get_json()["submission"]["status"] == "Pending Manager Approval"

    # 6. Manager approves content
    app_res = client.post(f"/api/submissions/{sub_id}/review", headers=manager_headers, data=json.dumps({
        "decision": "Approved",
        "comments": "Excellent revision. Meets all compliance standards. Approved for publication."
    }), content_type="application/json")
    assert app_res.status_code == 200
    assert app_res.get_json()["submission"]["status"] == "Approved"

    # 7. Check decision history contains both decisions in chronological order
    dec_res = client.get(f"/api/submissions/{sub_id}/decisions", headers=creator_headers)
    assert dec_res.status_code == 200
    decisions = dec_res.get_json()["decisions"]
    assert len(decisions) == 2
    assert decisions[0]["decision"] == "Approved"
    assert decisions[1]["decision"] == "Changes Requested"

    # 8. Approved content is locked from editing
    lock_res = client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "Attempt to tamper with approved copy"
    }), content_type="application/json")
    assert lock_res.status_code == 400
    assert "Approved content is locked and cannot be edited" in lock_res.get_json()["error"]
