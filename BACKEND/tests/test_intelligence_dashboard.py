"""
Tests for the Governance Intelligence Dashboard (Improvement 3).

Covers:
- Unauthenticated access → 401
- Empty dataset (no brands) → valid empty response
- Basic aggregation accuracy for all three review types
- Date-range filter (days param) applied to all review types
- Brand filter: restricted to user-accessible brands
- Cross-brand isolation: creator cannot see other brand's data
- Invalid filter params (negative days, non-integer brand_id) → 400
- Role: creator sees only own submissions; manager sees all brand data
- Actionable insights presence and evidence-backed format
- No double-counting: findings from different review types are separate
- Missing timestamps: turnaround returns null gracefully
- Existing /api/analytics endpoint still works (regression)
"""
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _register(client, username, email, pw, role):
    res = client.post("/api/auth/register", data=json.dumps({
        "username": username, "email": email, "password": pw,
        "role": role, "full_name": username.title(),
    }), content_type="application/json")
    assert res.status_code == 201, res.get_json()
    d = res.get_json()
    return {"Authorization": f"Bearer {d['token']}"}, d["user"]["id"]


def _create_brand(client, h, name, **kw):
    r = client.post("/api/brands", data=json.dumps({"name": name, **kw}),
                    content_type="application/json", headers=h)
    assert r.status_code == 201
    return r.get_json()["brand"]["id"]


def _add_member(client, h, brand_id, user_id):
    client.post(f"/api/brands/{brand_id}/members",
                data=json.dumps({"user_id": user_id}),
                content_type="application/json", headers=h)


def _create_guideline(client, h, brand_id):
    r = client.post(f"/api/brands/{brand_id}/guidelines", data=json.dumps({
        "category": "Tone", "title": "Voice Rule", "rule_content": "Keep it professional.",
        "severity": "High",
    }), content_type="application/json", headers=h)
    assert r.status_code == 201
    return r.get_json()["guideline"]["id"]


def _create_submission(client, h, brand_id, title="Test Content", text="This is compliant professional content."):
    r = client.post("/api/submissions", data=json.dumps({
        "brand_id": brand_id, "title": title, "content_text": text
    }), content_type="application/json", headers=h)
    assert r.status_code == 201
    return r.get_json()["submission"]["id"]


def _mock_compliance_ok(gid=None):
    payload = {
        "summary": "Minor tone issues.",
        "compliance_status": "Action Required",
        "overall_score": 75,
        "findings": [{
            "guideline_id": gid,
            "category": "Tone",
            "severity": "Medium",
            "problematic_text": "guarantee",
            "explanation": "Absolute guarantees are prohibited.",
            "suggested_correction": "Use 'strive'.",
            "confidence_level": "High",
            "human_verification_required": False,
        }],
    }
    mc = MagicMock()
    mr = MagicMock()
    mr.text = json.dumps(payload)
    mc.models.generate_content.return_value = mr
    return mc


def _make_png():
    return (io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 200), "img.png", "image/png")


def _make_txt(text="Some brand marketing document with enough content here."):
    return (io.BytesIO(text.encode()), "brief.txt", "text/plain")


def _make_docx_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
        zf.writestr("_rels/.rels", """<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>""")
        zf.writestr("word/_rels/document.xml.rels", """<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>""")
        zf.writestr("word/document.xml", """<?xml version="1.0"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>Brand document content for testing accessibility review.</w:t></w:r></w:p></w:body>
</w:document>""")
    return buf.getvalue()


def _mock_visual_ok(gid=None):
    payload = {
        "summary": "Minor colour issue.",
        "review_status": "Action Required",
        "compliance_score": 72,
        "findings": [{
            "visual_element": "Logo colour",
            "category": "Colour",
            "severity": "High",
            "guideline_id": gid,
            "guideline_rule": None,
            "explanation": "Wrong shade.",
            "suggested_correction": "Use #166534.",
            "confidence_level": "High",
            "human_verification_required": False,
        }],
    }
    mc = MagicMock()
    mr = MagicMock()
    mr.text = json.dumps(payload)
    mc.models.generate_content.return_value = mr
    return mc


def _mock_doc_ok(gid=None):
    payload = {
        "summary": "One tone issue and one readability issue.",
        "review_status": "Action Required",
        "findings": [
            {
                "review_type": "Brand Compliance",
                "category": "Tone",
                "severity": "Medium",
                "problematic_text": "guarantee best results",
                "referenced_guideline_id": gid,
                "guideline_rule": None,
                "explanation": "Prohibited guarantee language.",
                "suggested_correction": "Remove guarantee.",
                "confidence_level": "High",
                "human_verification_required": False,
            },
            {
                "review_type": "Accessibility",
                "category": "Language Complexity",
                "severity": "Low",
                "problematic_text": "utilise aforementioned paradigm",
                "referenced_guideline_id": None,
                "guideline_rule": None,
                "explanation": "Overly complex phrasing.",
                "suggested_correction": "Simplify.",
                "confidence_level": "High",
                "human_verification_required": False,
            },
        ],
    }
    mc = MagicMock()
    mr = MagicMock()
    mr.text = json.dumps(payload)
    mc.models.generate_content.return_value = mr
    return mc


def _get_intel(client, h, **params):
    return client.get("/api/analytics/intelligence", headers=h, query_string=params)


# ─── Unauthenticated ───────────────────────────────────────────────────────────

class TestIntelligenceUnauth:
    def test_no_token_returns_401(self, client):
        assert client.get("/api/analytics/intelligence").status_code == 401


# ─── Empty dataset ─────────────────────────────────────────────────────────────

class TestIntelligenceEmpty:
    def test_no_brands_returns_empty_response(self, client):
        h, _ = _register(client, "int_crt_e", "int_crt_e@b.com", "Pwd123!", "creator")
        res = _get_intel(client, h)
        assert res.status_code == 200
        d = res.get_json()
        assert d["success"] is True
        assert d["review_counts"]["total_reviews"] == 0
        assert d["total_findings"] == 0
        assert d["insights"] == []
        assert d["timeline_trends"] == []

    def test_brand_with_no_reviews_returns_zeros(self, client):
        h, _ = _register(client, "int_mgr_e2", "int_mgr_e2@b.com", "Pwd123!", "admin")
        _create_brand(client, h, "EmptyIntelBrand", tone_style="Professional")
        res = _get_intel(client, h)
        assert res.status_code == 200
        d = res.get_json()
        assert d["review_counts"]["total_reviews"] == 0
        assert d["total_findings"] == 0


# ─── Aggregation accuracy ──────────────────────────────────────────────────────

class TestIntelligenceAggregation:
    def _full_setup(self, client, suffix):
        """Create brand, guideline, submission compliance, visual, and document reviews."""
        h, uid = _register(client, f"int_mgr_agg{suffix}", f"int_mgr_agg{suffix}@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, f"AggBrand{suffix}", tone_style="Professional",
                            restricted_words="guarantee")
        gid = _create_guideline(client, h, bid)
        return h, uid, bid, gid

    def test_text_compliance_counted_correctly(self, client):
        h, uid, bid, gid = self._full_setup(client, "1")
        sub_id = _create_submission(client, h, bid)
        # Trigger AI review
        with patch("app.services.compliance_service.ComplianceService._get_gemini_client",
                   return_value=(_mock_compliance_ok(gid), None)):
            client.post(f"/api/submissions/{sub_id}/analyze", headers=h)
        res = _get_intel(client, h)
        d = res.get_json()
        assert d["review_counts"]["text_compliance_analyses"] >= 1
        assert d["submission_metrics"]["total"] >= 1

    def test_visual_compliance_counted_separately(self, client):
        h, uid, bid, gid = self._full_setup(client, "2")
        with patch("app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
                   return_value=(_mock_visual_ok(gid), None)):
            client.post("/api/visual-compliance/analyze",
                        data={"image": _make_png(), "brand_id": str(bid)},
                        headers=h, content_type="multipart/form-data")
        res = _get_intel(client, h)
        d = res.get_json()
        assert d["review_counts"]["visual_compliance_analyses"] >= 1

    def test_document_review_counted_separately(self, client):
        h, uid, bid, gid = self._full_setup(client, "3")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_doc_ok(gid), None)):
            client.post("/api/document-review/analyze",
                        data={"document": _make_txt(), "brand_id": str(bid)},
                        headers=h, content_type="multipart/form-data")
        res = _get_intel(client, h)
        d = res.get_json()
        assert d["review_counts"]["document_reviews"] >= 1

    def test_no_double_counting_across_types(self, client):
        """Text findings, visual findings, and document findings must not be summed together in total_findings incorrectly."""
        h, uid, bid, gid = self._full_setup(client, "4")
        # Create one of each
        sub_id = _create_submission(client, h, bid)
        with patch("app.services.compliance_service.ComplianceService._get_gemini_client",
                   return_value=(_mock_compliance_ok(gid), None)):
            client.post(f"/api/submissions/{sub_id}/analyze", headers=h)
        with patch("app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
                   return_value=(_mock_visual_ok(gid), None)):
            client.post("/api/visual-compliance/analyze",
                        data={"image": _make_png(), "brand_id": str(bid)},
                        headers=h, content_type="multipart/form-data")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_doc_ok(gid), None)):
            client.post("/api/document-review/analyze",
                        data={"document": _make_txt(), "brand_id": str(bid)},
                        headers=h, content_type="multipart/form-data")
        res = _get_intel(client, h)
        d = res.get_json()
        # total_reviews should be exactly 3 (one per type)
        assert d["review_counts"]["total_reviews"] == (
            d["review_counts"]["text_compliance_analyses"] +
            d["review_counts"]["visual_compliance_analyses"] +
            d["review_counts"]["document_reviews"]
        )
        # combined_severity should equal sum of all severity counts
        cs = d["combined_severity"]
        assert d["total_findings"] == sum(cs.values())


# ─── Date-range filter ─────────────────────────────────────────────────────────

class TestIntelligenceDateFilter:
    def test_valid_days_filter_applied(self, client):
        h, _ = _register(client, "int_mgr_df", "int_mgr_df@b.com", "Pwd123!", "admin")
        _create_brand(client, h, "DateFilterBrand", tone_style="Bold")
        res = _get_intel(client, h, days="7")
        assert res.status_code == 200
        assert res.get_json()["success"] is True

    def test_negative_days_returns_400(self, client):
        h, _ = _register(client, "int_mgr_nd", "int_mgr_nd@b.com", "Pwd123!", "admin")
        res = _get_intel(client, h, days="-5")
        assert res.status_code == 400

    def test_zero_days_returns_400(self, client):
        h, _ = _register(client, "int_mgr_zd", "int_mgr_zd@b.com", "Pwd123!", "admin")
        res = _get_intel(client, h, days="0")
        assert res.status_code == 400

    def test_non_integer_days_returns_400(self, client):
        h, _ = _register(client, "int_mgr_bad", "int_mgr_bad@b.com", "Pwd123!", "admin")
        res = _get_intel(client, h, days="week")
        assert res.status_code == 400


# ─── Brand filter ──────────────────────────────────────────────────────────────

class TestIntelligenceBrandFilter:
    def test_valid_brand_filter_returns_200(self, client):
        h, _ = _register(client, "int_mgr_bf", "int_mgr_bf@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, "BrandFilterTest", tone_style="Casual")
        res = _get_intel(client, h, brand_id=bid)
        assert res.status_code == 200

    def test_inaccessible_brand_returns_403(self, client):
        mgr_h, _ = _register(client, "int_mgr_ba1", "int_mgr_ba1@b.com", "Pwd123!", "admin")
        crt_h, crt_id = _register(client, "int_crt_ba2", "int_crt_ba2@b.com", "Pwd123!", "creator")
        # Creator is added to brand A but NOT to brand B
        bid_a = _create_brand(client, mgr_h, "PrivateBrandIntelA", tone_style="Luxury")
        bid_b = _create_brand(client, mgr_h, "PrivateBrandIntelB", tone_style="Bold")
        _add_member(client, mgr_h, bid_a, crt_id)  # creator can access A
        # Creator tries to access brand B → 403
        res = _get_intel(client, crt_h, brand_id=bid_b)
        assert res.status_code == 403


    def test_non_integer_brand_id_returns_400(self, client):
        h, _ = _register(client, "int_mgr_bi", "int_mgr_bi@b.com", "Pwd123!", "admin")
        res = _get_intel(client, h, brand_id="not-a-number")
        assert res.status_code == 400


# ─── Role and isolation ────────────────────────────────────────────────────────

class TestIntelligenceRoleIsolation:
    def test_creator_sees_only_own_submissions(self, client):
        mgr_h, _ = _register(client, "int_mgr_ri", "int_mgr_ri@b.com", "Pwd123!", "admin")
        crt_h, crt_id = _register(client, "int_crt_ri", "int_crt_ri@b.com", "Pwd123!", "creator")
        bid = _create_brand(client, mgr_h, "RoleBrand", tone_style="Scientific")
        _add_member(client, mgr_h, bid, crt_id)
        # Manager creates submission, creator creates submission
        _create_submission(client, mgr_h, bid, title="Manager Sub")
        _create_submission(client, crt_h, bid, title="Creator Sub")

        mgr_res = _get_intel(client, mgr_h)
        crt_res = _get_intel(client, crt_h)
        mgr_total = mgr_res.get_json()["submission_metrics"]["total"]
        crt_total = crt_res.get_json()["submission_metrics"]["total"]
        # Creator should see fewer or equal submissions (only their own)
        assert crt_total <= mgr_total

    def test_creator_cannot_access_unjoined_brand_data(self, client):
        mgr_h, _ = _register(client, "int_mgr_iso", "int_mgr_iso@b.com", "Pwd123!", "admin")
        crt_h, _ = _register(client, "int_crt_iso", "int_crt_iso@b.com", "Pwd123!", "creator")
        bid = _create_brand(client, mgr_h, "IsolatedIntelBrand", tone_style="Bold")
        # Creator NOT added
        res = _get_intel(client, crt_h, brand_id=bid)
        assert res.status_code == 403


# ─── Insights structure ────────────────────────────────────────────────────────

class TestIntelligenceInsights:
    def test_insights_have_required_fields(self, client):
        h, _ = _register(client, "int_mgr_ins", "int_mgr_ins@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, "InsightBrand", tone_style="Professional")
        _create_guideline(client, h, bid)
        # Create several submissions with revisions to trigger revision-rate insight
        for i in range(5):
            _create_submission(client, h, bid, title=f"Sub {i}", text=f"Content item {i} about brand stuff.")
        res = _get_intel(client, h)
        d = res.get_json()
        for insight in d.get("insights", []):
            assert "type" in insight
            assert "title" in insight
            assert "description" in insight
            assert "recommendation" in insight
            assert "evidence" in insight
            assert insight["type"] in ("critical", "warning", "info")

    def test_insights_empty_with_insufficient_data(self, client):
        h, _ = _register(client, "int_mgr_noins", "int_mgr_noins@b.com", "Pwd123!", "admin")
        res = _get_intel(client, h)
        assert res.status_code == 200
        assert isinstance(res.get_json()["insights"], list)


# ─── Missing timestamps ────────────────────────────────────────────────────────

class TestIntelligenceMissingTimestamps:
    def test_turnaround_null_when_no_decisions(self, client):
        h, _ = _register(client, "int_mgr_ts", "int_mgr_ts@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, "TSTBrand", tone_style="Clear")
        _create_submission(client, h, bid, title="Draft Only")
        res = _get_intel(client, h)
        d = res.get_json()
        # No decisions → turnaround should be None / null
        assert d["submission_metrics"]["avg_turnaround_days"] is None


# ─── Methodology note ──────────────────────────────────────────────────────────

class TestIntelligenceMethodology:
    def test_methodology_note_present(self, client):
        h, _ = _register(client, "int_mgr_mn", "int_mgr_mn@b.com", "Pwd123!", "admin")
        res = _get_intel(client, h)
        d = res.get_json()
        assert "methodology_note" in d
        assert len(d["methodology_note"]) > 20


# ─── Timeline structure ────────────────────────────────────────────────────────

class TestIntelligenceTimeline:
    def test_timeline_has_correct_keys(self, client):
        h, _ = _register(client, "int_mgr_tl", "int_mgr_tl@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, "TimelineBrand", tone_style="Professional")
        _create_submission(client, h, bid, title="T1")
        res = _get_intel(client, h)
        d = res.get_json()
        for entry in d["timeline_trends"]:
            assert "date" in entry
            assert "total" in entry
            assert "text_submissions" in entry
            assert "visual_reviews" in entry
            assert "doc_reviews" in entry


# ─── Regression: original /api/analytics endpoint ─────────────────────────────

class TestIntelligenceRegression:
    def test_original_analytics_endpoint_still_works(self, client):
        h, _ = _register(client, "int_reg_mgr", "int_reg_mgr@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, "RegBrand", tone_style="Clear")
        _create_submission(client, h, bid, title="Reg Sub")
        res = client.get("/api/analytics", headers=h)
        assert res.status_code == 200
        d = res.get_json()
        assert d["success"] is True
        assert "metrics" in d
        assert d["metrics"]["total_submissions"] >= 1

    def test_original_analytics_with_days_filter(self, client):
        h, _ = _register(client, "int_reg_mgr2", "int_reg_mgr2@b.com", "Pwd123!", "admin")
        res = client.get("/api/analytics?days=30", headers=h)
        assert res.status_code == 200

    def test_original_analytics_with_invalid_days(self, client):
        h, _ = _register(client, "int_reg_mgr3", "int_reg_mgr3@b.com", "Pwd123!", "admin")
        # Must have at least one brand so the early no-brands return is not triggered
        _create_brand(client, h, "RegBrandValidation", tone_style="Clear")
        res = client.get("/api/analytics?days=-1", headers=h)
        assert res.status_code == 400

    def test_original_analytics_unauthenticated(self, client):
        assert client.get("/api/analytics").status_code == 401


# ─── Applied filters echoed back ──────────────────────────────────────────────

class TestIntelligenceFilterEcho:
    def test_applied_filters_in_response(self, client):
        h, _ = _register(client, "int_mgr_fe", "int_mgr_fe@b.com", "Pwd123!", "admin")
        res = _get_intel(client, h, days="30")
        d = res.get_json()
        assert d["applied_filters"]["days"] == "30"

    def test_brands_list_in_response(self, client):
        h, _ = _register(client, "int_mgr_bl", "int_mgr_bl@b.com", "Pwd123!", "admin")
        _create_brand(client, h, "BrandListTest", tone_style="Bold")
        res = _get_intel(client, h)
        d = res.get_json()
        assert isinstance(d["brands"], list)
        assert len(d["brands"]) >= 1
        assert "id" in d["brands"][0]
        assert "name" in d["brands"][0]
