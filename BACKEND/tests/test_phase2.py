import json

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

def test_brand_management_workflow(client):
    manager_headers, manager_id = get_auth_headers(
        client, "manager_tim", "tim@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "creator_dan", "dan@brand.com", "Password123!", "creator"
    )

    # 1. Creator attempts to create brand -> 403 Forbidden
    res = client.post("/api/brands", headers=creator_headers, data=json.dumps({
        "name": "Acme Corp"
    }), content_type="application/json")
    assert res.status_code == 403

    # 2. Manager creates brand -> 201 Success
    res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "Acme Corp",
        "description": "Global innovative technology solutions",
        "tone_style": "Authoritative, forward-looking, yet approachable",
        "approved_terminology": "CloudFlow, NextGen AI, Enterprise Suite",
        "restricted_words": "Cheap, Guaranteed, Flawless",
        "approved_facts": "Founded in 2020. 99.99% uptime guarantee across all regions.",
        "prohibited_claims": "Never state our system is completely immune to cyberattacks."
    }), content_type="application/json")
    assert res.status_code == 201
    brand_data = res.get_json()["brand"]
    brand_id = brand_data["id"]
    assert brand_data["name"] == "Acme Corp"
    assert brand_data["tone_style"] == "Authoritative, forward-looking, yet approachable"

    # 3. Manager lists brands -> 200 (sees Acme Corp)
    res = client.get("/api/brands", headers=manager_headers)
    assert res.status_code == 200
    assert len(res.get_json()["brands"]) == 1

    # 4. Creator lists brands before assignment -> 200 (sees 0 brands)
    res = client.get("/api/brands", headers=creator_headers)
    assert res.status_code == 200
    assert len(res.get_json()["brands"]) == 0

    # 5. Creator tries to access Acme Corp directly before assignment -> 403 Forbidden
    res = client.get(f"/api/brands/{brand_id}", headers=creator_headers)
    assert res.status_code == 403

    # 6. Manager assigns creator to brand -> 201 Success
    res = client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id,
        "role": "contributor"
    }), content_type="application/json")
    assert res.status_code == 201

    # 7. Creator now lists accessible brands -> 200 (sees Acme Corp!)
    res = client.get("/api/brands", headers=creator_headers)
    assert res.status_code == 200
    assert len(res.get_json()["brands"]) == 1
    assert res.get_json()["brands"][0]["id"] == brand_id

    # 8. Manager updates brand profile -> 200
    res = client.put(f"/api/brands/{brand_id}", headers=manager_headers, data=json.dumps({
        "description": "Updated global tech description"
    }), content_type="application/json")
    assert res.status_code == 200
    assert res.get_json()["brand"]["description"] == "Updated global tech description"

def test_guideline_crud_and_creator_read_only(client):
    manager_headers, manager_id = get_auth_headers(
        client, "manager_emma", "emma@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "creator_leo", "leo@brand.com", "Password123!", "creator"
    )

    # Manager creates brand and assigns creator
    brand_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "Nova Health"
    }), content_type="application/json")
    brand_id = brand_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    # 1. Creator attempts to create guideline -> 403
    res = client.post(f"/api/brands/{brand_id}/guidelines", headers=creator_headers, data=json.dumps({
        "category": "Tone",
        "title": "Use Empathetic Language",
        "rule_content": "Always speak with empathy and medical accuracy."
    }), content_type="application/json")
    assert res.status_code == 403

    # 2. Manager creates guideline with invalid category -> 400
    res = client.post(f"/api/brands/{brand_id}/guidelines", headers=manager_headers, data=json.dumps({
        "category": "InvalidCategory",
        "title": "Bad Rule",
        "rule_content": "Some text"
    }), content_type="application/json")
    assert res.status_code == 400

    # 3. Manager creates multiple guidelines across categories -> 201
    g1_res = client.post(f"/api/brands/{brand_id}/guidelines", headers=manager_headers, data=json.dumps({
        "category": "Tone",
        "title": "Empathetic and Scientific Tone",
        "rule_content": "Every customer-facing communication must convey empathy backed by peer-reviewed evidence.",
        "reference_evidence": "Brand Voice Handbook 2026, Section 2.1"
    }), content_type="application/json")
    assert g1_res.status_code == 201
    g1_id = g1_res.get_json()["guideline"]["id"]

    g2_res = client.post(f"/api/brands/{brand_id}/guidelines", headers=manager_headers, data=json.dumps({
        "category": "Restricted Claims",
        "title": "No Cure Claims",
        "rule_content": "Never claim our dietary supplement cures or prevents chronic illnesses.",
        "reference_evidence": "FDA Compliance Guidelines Part 101"
    }), content_type="application/json")
    assert g2_res.status_code == 201
    g2_id = g2_res.get_json()["guideline"]["id"]

    # 4. Creator reads guidelines for assigned brand -> 200
    res = client.get(f"/api/brands/{brand_id}/guidelines", headers=creator_headers)
    assert res.status_code == 200
    guidelines = res.get_json()["guidelines"]
    assert len(guidelines) == 2

    # 5. Filter by category
    res = client.get(f"/api/brands/{brand_id}/guidelines?category=Tone", headers=creator_headers)
    assert res.status_code == 200
    assert len(res.get_json()["guidelines"]) == 1
    assert res.get_json()["guidelines"][0]["title"] == "Empathetic and Scientific Tone"

    # 6. Manager updates guideline
    res = client.put(f"/api/guidelines/{g1_id}", headers=manager_headers, data=json.dumps({
        "title": "Updated Tone Guideline"
    }), content_type="application/json")
    assert res.status_code == 200
    assert res.get_json()["guideline"]["title"] == "Updated Tone Guideline"

    # 7. Creator tries to delete guideline -> 403
    res = client.delete(f"/api/guidelines/{g2_id}", headers=creator_headers)
    assert res.status_code == 403

    # 8. Manager deletes guideline -> 200
    res = client.delete(f"/api/guidelines/{g2_id}", headers=manager_headers)
    assert res.status_code == 200

def test_content_submission_and_revision_history(client):
    manager_headers, manager_id = get_auth_headers(
        client, "manager_rachel", "rachel@brand.com", "Password123!", "admin"
    )
    creator_headers, creator_id = get_auth_headers(
        client, "creator_sam", "sam@brand.com", "Password123!", "creator"
    )
    unauthorized_creator_headers, _ = get_auth_headers(
        client, "creator_stranger", "stranger@brand.com", "Password123!", "creator"
    )

    # Manager creates brand & assigns creator_sam
    brand_res = client.post("/api/brands", headers=manager_headers, data=json.dumps({
        "name": "FinTech Prime"
    }), content_type="application/json")
    brand_id = brand_res.get_json()["brand"]["id"]

    client.post(f"/api/brands/{brand_id}/members", headers=manager_headers, data=json.dumps({
        "user_id": creator_id
    }), content_type="application/json")

    # 1. Unauthorized creator cannot submit for FinTech Prime -> 403
    res = client.post("/api/submissions", headers=unauthorized_creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "Unauthorized Campaign",
        "content_text": "This should be rejected."
    }), content_type="application/json")
    assert res.status_code == 403

    # 2. Creator creates draft -> 201
    res = client.post("/api/submissions", headers=creator_headers, data=json.dumps({
        "brand_id": brand_id,
        "title": "Q4 High-Yield Savings Launch",
        "content_text": "Earn guaranteed 12% returns with zero risk on our revolutionary savings account.",
        "status": "Draft",
        "reason": "Initial copy draft"
    }), content_type="application/json")
    assert res.status_code == 201
    sub_data = res.get_json()["submission"]
    sub_id = sub_data["id"]
    assert sub_data["status"] == "Draft"
    assert len(sub_data["revisions"]) == 1
    assert sub_data["revisions"][0]["revision_number"] == 1

    # 3. Creator tries to mark as "AI Reviewed" or "Approved" manually -> 403
    res = client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "status": "Approved"
    }), content_type="application/json")
    assert res.status_code == 403

    # 4. Creator updates draft content -> Revision #2 automatically created
    res = client.put(f"/api/submissions/{sub_id}", headers=creator_headers, data=json.dumps({
        "title": "Q4 High-Yield Savings Launch (Revised)",
        "content_text": "Grow your savings with up to 5.2% APY through FDIC-insured partner banks.",
        "status": "Ready for AI Review",
        "reason": "Removed exaggerated claims and added APY details"
    }), content_type="application/json")
    assert res.status_code == 200
    updated_sub = res.get_json()["submission"]
    assert updated_sub["status"] == "Ready for AI Review"
    assert len(updated_sub["revisions"]) == 2
    assert updated_sub["revisions"][0]["revision_number"] == 2
    assert updated_sub["revisions"][0]["reason"] == "Removed exaggerated claims and added APY details"

    # 5. Fetch revision history endpoint
    res = client.get(f"/api/submissions/{sub_id}/revisions", headers=creator_headers)
    assert res.status_code == 200
    revisions = res.get_json()["revisions"]
    assert len(revisions) == 2
    assert revisions[0]["revision_number"] == 2
    assert revisions[1]["revision_number"] == 1
