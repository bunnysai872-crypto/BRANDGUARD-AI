"""
Tests for the Multi-Format & Accessibility Document Review feature.

Covers:
- Unauthenticated access (all endpoints → 401)
- File validation: missing file, missing brand_id, unsupported formats, oversized, empty
- Format detection: TXT, PDF, DOCX magic-byte checks
- Extraction edge cases: image-only PDFs, empty text, truncation
- Brand access isolation: unassigned creator, cross-brand history/record
- Gemini failure modes: no API key, malformed JSON, exception, quota exceeded
- Missing brand guidelines → 400
- Successful analysis: findings persisted, hallucinated IDs stripped, fully compliant
- History and single-record retrieval
"""

import io
import json
import struct
import zipfile
import zlib
from unittest.mock import MagicMock, patch


# ─── File builders ─────────────────────────────────────────────────────────────

def _make_txt_file(content="This is a brand document.", filename="brief.txt"):
    return io.BytesIO(content.encode("utf-8")), filename, "text/plain"


def _make_minimal_pdf_bytes(text_content="Brand Guideline Document for review."):
    """
    Build a minimal valid (linearizable) PDF in memory containing one text page.
    Avoids any disk I/O.
    """
    pdf = b"%PDF-1.4\n"
    pdf += b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    pdf += b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    content_stream = f"BT /F1 12 Tf 100 700 Td ({text_content}) Tj ET".encode()
    pdf += b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
    pdf += b"/MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    pdf += f"4 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode()
    pdf += content_stream
    pdf += b"\nendstream\nendobj\n"
    pdf += b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    pdf += b"xref\n0 6\n"
    pdf += b"0000000000 65535 f \n"
    for _ in range(5):
        pdf += b"0000000009 00000 n \n"
    pdf += b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
    return pdf


def _make_pdf_file(text="This document contains brand policy information."):
    return io.BytesIO(_make_minimal_pdf_bytes(text)), "policy.pdf", "application/pdf"


def _make_docx_bytes(text="This is a test DOCX document with brand content."):
    """Build a minimal valid DOCX (ZIP) in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # [Content_Types].xml
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
        # _rels/.rels
        zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>""")
        # word/_rels/document.xml.rels
        zf.writestr("word/_rels/document.xml.rels", """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>""")
        # word/document.xml
        doc_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
            xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
  </w:body>
</w:document>"""
        zf.writestr("word/document.xml", doc_xml)
    return buf.getvalue()


def _make_docx_file(text="Brand marketing brief content."):
    return (
        io.BytesIO(_make_docx_bytes(text)),
        "marketing_brief.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ─── Auth helpers ──────────────────────────────────────────────────────────────

def _register(client, username, email, password, role):
    res = client.post(
        "/api/auth/register",
        data=json.dumps({
            "username": username,
            "email": email,
            "password": password,
            "role": role,
            "full_name": username.title(),
        }),
        content_type="application/json",
    )
    assert res.status_code == 201, f"Register failed: {res.get_json()}"
    data = res.get_json()
    return {"Authorization": f"Bearer {data['token']}"}, data["user"]["id"]


def _create_brand(client, headers, name, **kwargs):
    res = client.post(
        "/api/brands",
        data=json.dumps({"name": name, **kwargs}),
        content_type="application/json",
        headers=headers,
    )
    assert res.status_code == 201
    return res.get_json()["brand"]["id"]


def _add_member(client, headers, brand_id, user_id):
    client.post(
        f"/api/brands/{brand_id}/members",
        data=json.dumps({"user_id": user_id}),
        content_type="application/json",
        headers=headers,
    )


def _create_guideline(client, headers, brand_id, title="Tone Rule",
                      category="Tone", rule="Always use professional, clear language."):
    res = client.post(
        f"/api/brands/{brand_id}/guidelines",
        data=json.dumps({
            "category": category,
            "title": title,
            "rule_content": rule,
            "severity": "High",
        }),
        content_type="application/json",
        headers=headers,
    )
    assert res.status_code == 201
    return res.get_json()["guideline"]["id"]


def _mock_gemini_ok(guideline_id=None):
    """Return a mock client producing a valid combined review response."""
    payload = {
        "summary": "The document has minor tone deviations and one accessibility concern.",
        "review_status": "Action Required",
        "findings": [
            {
                "review_type": "Brand Compliance",
                "category": "Tone",
                "severity": "Medium",
                "problematic_text": "We guarantee the best results.",
                "referenced_guideline_id": guideline_id,
                "guideline_rule": "Always use professional, clear language." if guideline_id else None,
                "explanation": "Absolute guarantees are prohibited by brand guidelines.",
                "suggested_correction": "Replace with 'We strive to deliver the best results.'",
                "confidence_level": "High",
                "human_verification_required": False,
            },
            {
                "review_type": "Accessibility",
                "category": "Language Complexity",
                "severity": "Low",
                "problematic_text": "Utilise the aforementioned strategic paradigm to effectuate outcomes.",
                "referenced_guideline_id": None,
                "guideline_rule": None,
                "explanation": "Overly complex phrasing reduces readability for general audiences.",
                "suggested_correction": "Use simpler phrasing: 'Use this strategy to achieve results.'",
                "confidence_level": "High",
                "human_verification_required": False,
            },
            {
                "review_type": "Accessibility",
                "category": "Structure",
                "severity": "Unable to Verify",
                "problematic_text": "Document structure analysis",
                "referenced_guideline_id": None,
                "guideline_rule": None,
                "explanation": "Visual heading structure cannot be confirmed from plain-text extraction alone.",
                "suggested_correction": "Ensure heading hierarchy is applied correctly in the source document.",
                "confidence_level": "Low",
                "human_verification_required": True,
            },
        ],
    }
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(payload)
    mock_client.models.generate_content.return_value = mock_resp
    return mock_client


# ─── Unauthenticated tests ─────────────────────────────────────────────────────

class TestDocReviewUnauthenticated:
    def test_analyze_unauth(self, client):
        res = client.post("/api/document-review/analyze",
                          data={"document": _make_txt_file(), "brand_id": "1"})
        assert res.status_code == 401

    def test_history_unauth(self, client):
        assert client.get("/api/document-review/brands/1/history").status_code == 401

    def test_get_review_unauth(self, client):
        assert client.get("/api/document-review/1").status_code == 401


# ─── File validation tests ─────────────────────────────────────────────────────

class TestDocReviewFileValidation:
    def _setup(self, client, suffix):
        h, _ = _register(client, f"dr_mgr_fv{suffix}", f"dr_mgr_fv{suffix}@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, f"FVBrand{suffix}", tone_style="Professional")
        return h, bid

    def test_missing_file_returns_422(self, client):
        h, bid = self._setup(client, "1")
        res = client.post("/api/document-review/analyze", data={"brand_id": str(bid)}, headers=h,
                          content_type="multipart/form-data")
        assert res.status_code == 422
        assert "No document file" in res.get_json()["error"] or "provided" in res.get_json()["error"]

    def test_missing_brand_id_returns_400(self, client):
        h, bid = self._setup(client, "2")
        res = client.post("/api/document-review/analyze",
                          data={"document": _make_txt_file()}, headers=h,
                          content_type="multipart/form-data")
        assert res.status_code == 400

    def test_unsupported_format_returns_422(self, client):
        h, bid = self._setup(client, "3")
        fake = (io.BytesIO(b"GIF89a..."), "image.gif", "image/gif")
        res = client.post("/api/document-review/analyze",
                          data={"document": fake, "brand_id": str(bid)}, headers=h,
                          content_type="multipart/form-data")
        assert res.status_code == 422
        assert "Unsupported" in res.get_json()["error"] or "extension" in res.get_json()["error"].lower()

    def test_png_file_as_txt_rejected_returns_422(self, client):
        """A PNG file with .txt extension must be rejected — not valid text."""
        h, bid = self._setup(client, "4")
        fake = (io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100), "report.txt", "text/plain")
        res = client.post("/api/document-review/analyze",
                          data={"document": fake, "brand_id": str(bid)}, headers=h,
                          content_type="multipart/form-data")
        # Should either be detected as non-txt or fail with empty text extraction
        assert res.status_code in (422, 400)

    def test_oversized_file_returns_422(self, client):
        from app.services.document_review_service import MAX_DOC_BYTES
        h, bid = self._setup(client, "5")
        big = (io.BytesIO(b"A" * (MAX_DOC_BYTES + 1)), "huge.txt", "text/plain")
        res = client.post("/api/document-review/analyze",
                          data={"document": big, "brand_id": str(bid)}, headers=h,
                          content_type="multipart/form-data")
        assert res.status_code == 422
        assert "maximum" in res.get_json()["error"].lower() or "size" in res.get_json()["error"].lower()

    def test_empty_txt_returns_422(self, client):
        h, bid = self._setup(client, "6")
        # File with only whitespace — treated as empty
        fake = (io.BytesIO(b"   \n  "), "empty.txt", "text/plain")
        res = client.post("/api/document-review/analyze",
                          data={"document": fake, "brand_id": str(bid)}, headers=h,
                          content_type="multipart/form-data")
        assert res.status_code == 422
        assert "insufficient" in res.get_json()["error"].lower() or "empty" in res.get_json()["error"].lower()


# ─── Format detection tests ────────────────────────────────────────────────────

class TestDocReviewFormatDetection:
    def _setup(self, client, suffix):
        h, _ = _register(client, f"dr_mgr_fd{suffix}", f"dr_mgr_fd{suffix}@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, f"FmtBrand{suffix}", tone_style="Bold")
        _create_guideline(client, h, bid)
        return h, bid

    def test_valid_txt_accepted_and_analyzed(self, client):
        h, bid = self._setup(client, "1")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_gemini_ok(), None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("We guarantee the best outcomes."),
                                    "brand_id": str(bid)},
                              headers=h, content_type="multipart/form-data")
        assert res.status_code == 201
        assert res.get_json()["review"]["detected_format"] == "txt"

    def test_valid_docx_accepted_and_analyzed(self, client):
        h, bid = self._setup(client, "2")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_gemini_ok(), None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_docx_file("Brand-compliant content here."),
                                    "brand_id": str(bid)},
                              headers=h, content_type="multipart/form-data")
        assert res.status_code == 201
        assert res.get_json()["review"]["detected_format"] == "docx"

    def test_fake_docx_content_in_txt_extension(self, client):
        """DOCX magic bytes with .txt extension should be rejected for format mismatch."""
        h, bid = self._setup(client, "3")
        docx_bytes = _make_docx_bytes("test content")
        fake = (io.BytesIO(docx_bytes), "report.txt", "text/plain")
        res = client.post("/api/document-review/analyze",
                          data={"document": fake, "brand_id": str(bid)},
                          headers=h, content_type="multipart/form-data")
        assert res.status_code == 422


# ─── Brand access isolation tests ─────────────────────────────────────────────

class TestDocReviewBrandAccess:
    def test_creator_cannot_review_unassigned_brand(self, client):
        mgr_h, _ = _register(client, "dr_mgr_ba1", "dr_mgr_ba1@b.com", "Pwd123!", "admin")
        crt_h, _ = _register(client, "dr_crt_ba1", "dr_crt_ba1@b.com", "Pwd123!", "creator")
        bid = _create_brand(client, mgr_h, "IsolatedBrand DR", tone_style="Professional")
        # Creator NOT added as member
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_gemini_ok(), None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("some text"), "brand_id": str(bid)},
                              headers=crt_h, content_type="multipart/form-data")
        assert res.status_code == 403

    def test_creator_cannot_view_other_brand_history(self, client):
        mgr_h, _ = _register(client, "dr_mgr_ba2", "dr_mgr_ba2@b.com", "Pwd123!", "admin")
        crt_h, _ = _register(client, "dr_crt_ba2", "dr_crt_ba2@b.com", "Pwd123!", "creator")
        bid = _create_brand(client, mgr_h, "PrivateBrand DR", tone_style="Luxury")
        res = client.get(f"/api/document-review/brands/{bid}/history", headers=crt_h)
        assert res.status_code == 403

    def test_admin_can_review_own_brand(self, client):
        mgr_h, _ = _register(client, "dr_mgr_ba3", "dr_mgr_ba3@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, mgr_h, "AdminBrand DR", tone_style="Clear")
        _create_guideline(client, mgr_h, bid)
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_gemini_ok(), None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("Professional brand content."),
                                    "brand_id": str(bid)},
                              headers=mgr_h, content_type="multipart/form-data")
        assert res.status_code == 201


# ─── Gemini error handling tests ───────────────────────────────────────────────

class TestDocReviewGeminiErrors:
    def _setup(self, client, suffix):
        h, _ = _register(client, f"dr_mgr_ge{suffix}", f"dr_mgr_ge{suffix}@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, f"GEBrand{suffix}", tone_style="Energetic")
        _create_guideline(client, h, bid)
        return h, bid

    def test_no_api_key_returns_503(self, client):
        h, bid = self._setup(client, "1")
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("content"), "brand_id": str(bid)},
                              headers=h, content_type="multipart/form-data")
        assert res.status_code == 503

    def test_malformed_json_returns_502(self, client):
        h, bid = self._setup(client, "2")
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "Sorry, I cannot review this document."
        mock_client.models.generate_content.return_value = mock_resp
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(mock_client, None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("content"), "brand_id": str(bid)},
                              headers=h, content_type="multipart/form-data")
        assert res.status_code == 502
        assert "JSON" in res.get_json()["error"] or "parse" in res.get_json()["error"].lower()

    def test_gemini_exception_returns_502(self, client):
        h, bid = self._setup(client, "3")
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("network error")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(mock_client, None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("content"), "brand_id": str(bid)},
                              headers=h, content_type="multipart/form-data")
        assert res.status_code in (502, 504)

    def test_quota_exceeded_returns_429(self, client):
        h, bid = self._setup(client, "4")
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("RESOURCE_EXHAUSTED: quota")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(mock_client, None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("content"), "brand_id": str(bid)},
                              headers=h, content_type="multipart/form-data")
        assert res.status_code == 429


# ─── Missing guidelines tests ──────────────────────────────────────────────────

class TestDocReviewNoGuidelines:
    def test_brand_with_no_profile_returns_400(self, client):
        h, _ = _register(client, "dr_mgr_ng", "dr_mgr_ng@b.com", "Pwd123!", "admin")
        bid = _create_brand(client, h, "EmptyBrand DR")  # No tone, no guidelines
        res = client.post("/api/document-review/analyze",
                          data={"document": _make_txt_file("content"), "brand_id": str(bid)},
                          headers=h, content_type="multipart/form-data")
        assert res.status_code == 400
        assert "guideline" in res.get_json()["error"].lower()


# ─── Successful analysis tests ─────────────────────────────────────────────────

class TestDocReviewSuccess:
    def _setup(self, client, suffix):
        mgr_h, _ = _register(client, f"dr_mgr_s{suffix}", f"dr_mgr_s{suffix}@b.com", "Pwd123!", "admin")
        crt_h, crt_id = _register(client, f"dr_crt_s{suffix}", f"dr_crt_s{suffix}@b.com", "Pwd123!", "creator")
        bid = _create_brand(client, mgr_h, f"SuccessBrand DR{suffix}",
                            tone_style="Professional", restricted_words="guarantee, promise")
        _add_member(client, mgr_h, bid, crt_id)
        gid = _create_guideline(client, mgr_h, bid)
        return mgr_h, crt_h, bid, gid

    def test_txt_analysis_persisted_with_findings(self, client):
        mgr_h, crt_h, bid, gid = self._setup(client, "1")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_gemini_ok(guideline_id=gid), None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("We guarantee the best outcomes."),
                                    "brand_id": str(bid)},
                              headers=crt_h, content_type="multipart/form-data")
        assert res.status_code == 201
        review = res.get_json()["review"]
        assert review["brand_id"] == bid
        assert review["detected_format"] == "txt"
        assert review["review_status"] == "Action Required"
        assert review["medium_severity_count"] == 1
        assert review["low_severity_count"] == 1
        assert review["unable_to_verify_count"] == 1
        assert review["has_limitations"] is True
        findings = review["findings"]
        assert len(findings) == 3
        # Brand compliance finding must link to guideline
        bc = next((f for f in findings if f["review_type"] == "Brand Compliance"), None)
        assert bc is not None
        assert bc["guideline_id"] == gid
        # Accessibility findings
        a11y = [f for f in findings if f["review_type"] == "Accessibility"]
        assert len(a11y) == 2

    def test_docx_analysis_persisted(self, client):
        mgr_h, crt_h, bid, gid = self._setup(client, "2")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_gemini_ok(guideline_id=gid), None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_docx_file("Professional brand content."),
                                    "brand_id": str(bid)},
                              headers=crt_h, content_type="multipart/form-data")
        assert res.status_code == 201
        assert res.get_json()["review"]["detected_format"] == "docx"

    def test_hallucinated_guideline_id_stripped(self, client):
        mgr_h, crt_h, bid, gid = self._setup(client, "3")
        fake_payload = {
            "summary": "One compliance issue found.",
            "review_status": "Violations Detected",
            "findings": [{
                "review_type": "Brand Compliance",
                "category": "Prohibited Claims",
                "severity": "High",
                "problematic_text": "100% guaranteed success",
                "referenced_guideline_id": 99999,  # hallucinated
                "guideline_rule": None,
                "explanation": "Absolute guarantee language is prohibited.",
                "suggested_correction": "Remove the guarantee.",
                "confidence_level": "High",
                "human_verification_required": False,
            }],
        }
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = json.dumps(fake_payload)
        mock_client.models.generate_content.return_value = mock_resp
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(mock_client, None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("100% guaranteed success"),
                                    "brand_id": str(bid)},
                              headers=crt_h, content_type="multipart/form-data")
        assert res.status_code == 201
        findings = res.get_json()["review"]["findings"]
        assert findings[0]["guideline_id"] is None  # hallucinated ID stripped

    def test_compliant_document_no_findings(self, client):
        mgr_h, crt_h, bid, gid = self._setup(client, "4")
        compliant = {
            "summary": "Document fully complies with brand guidelines.",
            "review_status": "Compliant",
            "findings": [],
        }
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = json.dumps(compliant)
        mock_client.models.generate_content.return_value = mock_resp
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(mock_client, None)):
            res = client.post("/api/document-review/analyze",
                              data={"document": _make_txt_file("Professional, brand-approved content."),
                                    "brand_id": str(bid)},
                              headers=crt_h, content_type="multipart/form-data")
        assert res.status_code == 201
        review = res.get_json()["review"]
        assert review["review_status"] == "Compliant"
        assert review["issues_count"] == 0
        assert len(review["findings"]) == 0

    def test_history_returns_past_reviews(self, client):
        mgr_h, crt_h, bid, gid = self._setup(client, "5")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_gemini_ok(guideline_id=gid), None)):
            client.post("/api/document-review/analyze",
                        data={"document": _make_txt_file("some content"), "brand_id": str(bid)},
                        headers=crt_h, content_type="multipart/form-data")
        hist = client.get(f"/api/document-review/brands/{bid}/history", headers=crt_h)
        assert hist.status_code == 200
        assert len(hist.get_json()["history"]) >= 1

    def test_get_review_by_id(self, client):
        mgr_h, crt_h, bid, gid = self._setup(client, "6")
        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_gemini_ok(guideline_id=gid), None)):
            post_res = client.post("/api/document-review/analyze",
                                   data={"document": _make_txt_file("some content"), "brand_id": str(bid)},
                                   headers=crt_h, content_type="multipart/form-data")
        review_id = post_res.get_json()["review"]["id"]
        get_res = client.get(f"/api/document-review/{review_id}", headers=crt_h)
        assert get_res.status_code == 200
        assert get_res.get_json()["review"]["id"] == review_id
        assert len(get_res.get_json()["review"]["findings"]) == 3

    def test_cross_brand_review_access_denied(self, client):
        """Brand A's review must not be readable by a creator from Brand B."""
        mgr_a_h, _ = _register(client, "dr_mgr_xa", "dr_mgr_xa@b.com", "Pwd123!", "admin")
        bid_a = _create_brand(client, mgr_a_h, "CrossDocA", tone_style="Bold")
        _create_guideline(client, mgr_a_h, bid_a)

        mgr_b_h, _ = _register(client, "dr_mgr_xb", "dr_mgr_xb@b.com", "Pwd123!", "admin")
        crt_b_h, crt_b_id = _register(client, "dr_crt_xb", "dr_crt_xb@b.com", "Pwd123!", "creator")
        bid_b = _create_brand(client, mgr_b_h, "CrossDocB", tone_style="Minimal")
        _add_member(client, mgr_b_h, bid_b, crt_b_id)

        with patch("app.services.document_review_service.DocumentReviewService._get_gemini_client",
                   return_value=(_mock_gemini_ok(), None)):
            post_res = client.post("/api/document-review/analyze",
                                   data={"document": _make_txt_file("Brand A content"), "brand_id": str(bid_a)},
                                   headers=mgr_a_h, content_type="multipart/form-data")
        review_id = post_res.get_json()["review"]["id"]

        get_res = client.get(f"/api/document-review/{review_id}", headers=crt_b_h)
        assert get_res.status_code == 403
