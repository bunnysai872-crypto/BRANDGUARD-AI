"""
Tests for the Visual Brand Compliance Checker feature.

Covers:
- Valid image upload and analysis (mocked Gemini)
- Invalid file types and oversized files
- Unauthenticated requests
- Unauthorized roles and cross-brand access
- Gemini API failures and malformed responses
- Missing / insufficient brand guidelines
- Fabricated guideline ID sanitization
"""

import io
import json
import struct
import zlib
from unittest.mock import MagicMock, patch


# ─── Helpers ──────────────────────────────────────────────────────────────────

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
    payload = {"name": name, **kwargs}
    res = client.post(
        "/api/brands",
        data=json.dumps(payload),
        content_type="application/json",
        headers=headers,
    )
    assert res.status_code == 201, f"Create brand failed: {res.get_json()}"
    return res.get_json()["brand"]["id"]


def _add_member(client, headers, brand_id, user_id):
    client.post(
        f"/api/brands/{brand_id}/members",
        data=json.dumps({"user_id": user_id}),
        content_type="application/json",
        headers=headers,
    )


def _create_guideline(client, headers, brand_id, category="Visual Identity", title="Logo Rule",
                      rule_content="Logo must appear in the top-left corner with clear space."):
    res = client.post(
        f"/api/brands/{brand_id}/guidelines",
        data=json.dumps({
            "category": category,
            "title": title,
            "rule_content": rule_content,
            "severity": "High",
        }),
        content_type="application/json",
        headers=headers,
    )
    assert res.status_code == 201, f"Create guideline failed: {res.get_json()}"
    return res.get_json()["guideline"]["id"]


def _make_minimal_png(width=4, height=4):
    """
    Return raw bytes of a tiny valid PNG image (4×4 white pixels).
    Avoids any filesystem access.
    """
    def _chunk(name: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", crc)

    png_signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    ihdr = _chunk(b"IHDR", ihdr_data)

    # Raw image data: scanlines (filter byte 0 + RGB pixels)
    raw_rows = b""
    for _ in range(height):
        raw_rows += b"\x00" + b"\xff\xff\xff" * width  # white pixels
    compressed = zlib.compress(raw_rows)
    idat = _chunk(b"IDAT", compressed)
    iend = _chunk(b"IEND", b"")

    return png_signature + ihdr + idat + iend


def _png_file(filename="test_poster.png"):
    return (io.BytesIO(_make_minimal_png()), filename, "image/png")


def _mock_gemini_success(guideline_id=None):
    """Return a mock Gemini client that returns a valid visual compliance JSON response."""
    mock_output = {
        "summary": "The uploaded image shows minor layout concerns. Logo placement and brand colors were not fully verifiable.",
        "review_status": "Action Required",
        "compliance_score": 72,
        "findings": [
            {
                "category": "Layout & Spacing",
                "severity": "Medium",
                "visual_element": "Large block of text near the bottom with insufficient white space",
                "referenced_guideline_id": guideline_id,
                "guideline_rule": "Maintain adequate white space around text elements." if guideline_id else None,
                "explanation": "The text area appears crowded and lacks breathing room, reducing readability.",
                "suggested_correction": "Increase padding around the text block to at least 20px on all sides.",
                "human_verification_required": False,
            },
            {
                "category": "Logo Usage",
                "severity": "Unable to Verify",
                "visual_element": "Logo in top-left corner",
                "referenced_guideline_id": None,
                "guideline_rule": None,
                "explanation": "Cannot verify Pantone-specific brand color of the logo without specification sheet.",
                "suggested_correction": "Confirm logo color matches Pantone 354 C per brand guide.",
                "human_verification_required": True,
            },
        ],
    }
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_output)
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


# ─── Test cases ───────────────────────────────────────────────────────────────

class TestVisualComplianceUnauthenticated:
    """All endpoints should reject unauthenticated requests."""

    def test_analyze_unauthenticated(self, client):
        data = {"image": _png_file(), "brand_id": "1"}
        res = client.post("/api/visual-compliance/analyze", data=data)
        assert res.status_code == 401

    def test_history_unauthenticated(self, client):
        res = client.get("/api/visual-compliance/brands/1/history")
        assert res.status_code == 401

    def test_get_analysis_unauthenticated(self, client):
        res = client.get("/api/visual-compliance/1")
        assert res.status_code == 401



class TestVisualComplianceMultipartBoundaryRegression:
    """
    Regression tests for the production bug where the frontend sent
    'Content-Type: multipart/form-data' WITHOUT the boundary parameter,
    causing Flask/Werkzeug to fail to parse form fields.  When form fields
    are unparseable, Flask-JWT-Extended cannot find the JWT (it only looks
    in headers, not the body — but Werkzeug still fails to parse the whole
    request), and returns 401, triggering the auto-logout redirect to /login.

    Root cause: VisualComplianceChecker.jsx passed
        headers: { 'Content-Type': 'multipart/form-data' }
    to api.post(), which stripped the auto-generated boundary from the header.

    Fix: remove the explicit Content-Type override so Axios sets the full
        'multipart/form-data; boundary=...' header automatically.
    """

    def _setup(self, client):
        mgr_h, mgr_id = _register(client, "vc_mgr_reg", "vc_mgr_reg@b.com", "Pwd123!", "admin")
        brand_id = _create_brand(client, mgr_h, "RegressionBrand",
                                 tone_style="Professional")
        _create_guideline(client, mgr_h, brand_id)
        return mgr_h, brand_id

    def test_authenticated_multipart_with_correct_boundary_succeeds(self, client):
        """
        Core regression: an authenticated multipart POST where the test client
        automatically sets Content-Type including the boundary must NOT return 401.
        This mirrors Axios sending FormData without a manual Content-Type override.
        """
        mgr_h, brand_id = self._setup(client)

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(), None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=mgr_h,
                content_type="multipart/form-data",
            )

        assert res.status_code != 401, (
            "Got 401 on an authenticated multipart request — this is the login-redirect bug. "
            "The Authorization header or form body parsing is broken."
        )
        assert res.status_code == 201
        assert res.get_json()["success"] is True

    def test_multipart_request_missing_jwt_returns_401_for_correct_reason(self, client):
        """
        A multipart request with NO Authorization header must return 401
        for the correct reason (missing JWT), not because of a body parse failure.
        """
        mgr_h, brand_id = self._setup(client)

        res = client.post(
            "/api/visual-compliance/analyze",
            data={"image": _png_file(), "brand_id": str(brand_id)},
            # Deliberately omit Authorization header
            content_type="multipart/form-data",
        )
        assert res.status_code == 401
        body = res.get_json()
        assert body is not None
        error_text = body.get("error", "").lower()
        # Must be a JWT error message, not a body-parse error
        assert "token" in error_text or "authorization" in error_text

    def test_multipart_with_empty_form_returns_4xx_not_401(self, client):
        """
        A POST with an authenticated header but no form fields must return
        400 (brand_id missing) or 422 (image missing), never 401.
        A 401 here would mean form-parse failure is wrongly treated as auth failure.
        """
        mgr_h, brand_id = self._setup(client)

        res = client.post(
            "/api/visual-compliance/analyze",
            data={},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code in (400, 422), (
            f"Expected 400/422 for empty form, got {res.status_code}. "
            "A 401 here means JWT is incorrectly invalidated by a body-parse failure."
        )


class TestVisualComplianceBrandIdValidation:
    """
    Regression tests verifying proper validation of brand_id in multipart requests:
    - Missing brand_id returns 400 with 'brand_id is required.'
    - Empty brand_id returns 400 with 'brand_id is required.'
    - Non-integer brand_id (e.g. brand name string) returns 400 with 'brand_id must be a valid integer.'
    - Valid selected brand_id (as string or int) succeeds with 201.
    - Valid selected brand_id passed via values/query param also succeeds with 201.
    """

    def _setup(self, client):
        mgr_h, mgr_id = _register(client, "vc_mgr_bid", "vc_mgr_bid@b.com", "Pwd123!", "admin")
        brand_id = _create_brand(client, mgr_h, "BrandIdTestBrand", tone_style="Professional")
        _create_guideline(client, mgr_h, brand_id)
        return mgr_h, brand_id

    def test_missing_brand_id_returns_400(self, client):
        mgr_h, brand_id = self._setup(client)
        res = client.post(
            "/api/visual-compliance/analyze",
            data={"image": _png_file()},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code == 400
        body = res.get_json()
        assert body["success"] is False
        assert body["error"] == "brand_id is required."

    def test_empty_brand_id_returns_400(self, client):
        mgr_h, brand_id = self._setup(client)
        res = client.post(
            "/api/visual-compliance/analyze",
            data={"image": _png_file(), "brand_id": ""},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code == 400
        body = res.get_json()
        assert body["success"] is False
        assert body["error"] == "brand_id is required."

    def test_non_integer_brand_name_as_brand_id_returns_400(self, client):
        mgr_h, brand_id = self._setup(client)
        res = client.post(
            "/api/visual-compliance/analyze",
            data={"image": _png_file(), "brand_id": "CloudNova"},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code == 400
        body = res.get_json()
        assert body["success"] is False
        assert body["error"] == "brand_id must be a valid integer."

    def test_valid_selected_brand_id_string_succeeds(self, client):
        mgr_h, brand_id = self._setup(client)
        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(), None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=mgr_h,
                content_type="multipart/form-data",
            )
        assert res.status_code == 201
        body = res.get_json()
        assert body["success"] is True
        assert body["analysis"]["brand_id"] == brand_id

    def test_valid_selected_brand_id_int_succeeds(self, client):
        mgr_h, brand_id = self._setup(client)
        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(), None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": brand_id},
                headers=mgr_h,
                content_type="multipart/form-data",
            )
        assert res.status_code == 201
        body = res.get_json()
        assert body["success"] is True
        assert body["analysis"]["brand_id"] == brand_id

    def test_valid_brand_id_in_query_params_with_multipart_image_succeeds(self, client):
        mgr_h, brand_id = self._setup(client)
        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(), None),
        ):
            res = client.post(
                f"/api/visual-compliance/analyze?brand_id={brand_id}",
                data={"image": _png_file()},
                headers=mgr_h,
                content_type="multipart/form-data",
            )
        assert res.status_code == 201
        body = res.get_json()
        assert body["success"] is True
        assert body["analysis"]["brand_id"] == brand_id


class TestVisualComplianceFileValidation:
    """File type, extension, and size validation tests."""

    def _setup(self, client):
        mgr_h, mgr_id = _register(client, "vc_mgr_fv", "vc_mgr_fv@b.com", "Pwd123!", "admin")
        brand_id = _create_brand(client, mgr_h, "ValidateBrand FV",
                                 tone_style="Professional")
        return mgr_h, brand_id

    def test_missing_image_returns_422(self, client):
        mgr_h, brand_id = self._setup(client)
        res = client.post(
            "/api/visual-compliance/analyze",
            data={"brand_id": str(brand_id)},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code == 422
        assert "No image file" in res.get_json()["error"] or "provided" in res.get_json()["error"]

    def test_missing_brand_id_returns_400(self, client):
        mgr_h, brand_id = self._setup(client)
        res = client.post(
            "/api/visual-compliance/analyze",
            data={"image": _png_file()},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code == 400
        assert "brand_id" in res.get_json()["error"]

    def test_unsupported_file_type_gif_returns_422(self, client):
        mgr_h, brand_id = self._setup(client)
        fake_gif = (io.BytesIO(b"GIF89aXXXXXXX"), "animation.gif", "image/gif")
        res = client.post(
            "/api/visual-compliance/analyze",
            data={"image": fake_gif, "brand_id": str(brand_id)},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code == 422
        assert "gif" in res.get_json()["error"].lower() or "extension" in res.get_json()["error"].lower()

    def test_unsupported_file_type_pdf_returns_422(self, client):
        mgr_h, brand_id = self._setup(client)
        fake_pdf = (io.BytesIO(b"%PDF-1.4 fake content"), "report.pdf", "application/pdf")
        res = client.post(
            "/api/visual-compliance/analyze",
            data={"image": fake_pdf, "brand_id": str(brand_id)},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code == 422

    def test_oversized_file_returns_422(self, client):
        from app.services.visual_compliance_service import MAX_IMAGE_BYTES
        mgr_h, brand_id = self._setup(client)
        oversized = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * (MAX_IMAGE_BYTES + 1))  # fake JPEG header
        oversized_file = (oversized, "big_poster.jpg", "image/jpeg")
        res = client.post(
            "/api/visual-compliance/analyze",
            data={"image": oversized_file, "brand_id": str(brand_id)},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code == 422
        assert "maximum" in res.get_json()["error"].lower() or "size" in res.get_json()["error"].lower()

    def test_png_extension_with_jpeg_content_returns_422(self, client):
        """Extension must match actual file content."""
        mgr_h, brand_id = self._setup(client)
        # Real PNG bytes but claiming .jpg extension
        png_bytes = _make_minimal_png()
        mismatched = (io.BytesIO(png_bytes), "poster.jpg", "image/jpeg")
        res = client.post(
            "/api/visual-compliance/analyze",
            data={"image": mismatched, "brand_id": str(brand_id)},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert res.status_code == 422
        assert "match" in res.get_json()["error"].lower() or "content type" in res.get_json()["error"].lower()


class TestVisualComplianceBrandAccess:
    """Cross-brand access isolation and role permission tests."""

    def test_creator_cannot_analyze_unassigned_brand(self, client):
        mgr_h, mgr_id = _register(client, "vc_mgr_acc1", "vc_mgr_acc1@b.com", "Pwd123!", "admin")
        creator_h, creator_id = _register(client, "vc_crt_acc1", "vc_crt_acc1@b.com", "Pwd123!", "creator")

        brand_id = _create_brand(client, mgr_h, "IsolatedBrand ACC",
                                 tone_style="Professional")
        # Creator is NOT added as member

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(), None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=creator_h,
                content_type="multipart/form-data",
            )
        assert res.status_code == 403
        assert "permission" in res.get_json()["error"].lower() or "access" in res.get_json()["error"].lower()

    def test_creator_cannot_view_other_brand_history(self, client):
        mgr_h, mgr_id = _register(client, "vc_mgr_acc2", "vc_mgr_acc2@b.com", "Pwd123!", "admin")
        creator_h, creator_id = _register(client, "vc_crt_acc2", "vc_crt_acc2@b.com", "Pwd123!", "creator")

        brand_id = _create_brand(client, mgr_h, "PrivateBrand ACC2",
                                 tone_style="Luxury")
        # Creator not a member
        res = client.get(
            f"/api/visual-compliance/brands/{brand_id}/history",
            headers=creator_h,
        )
        assert res.status_code == 403

    def test_admin_can_analyze_any_brand(self, client):
        mgr_h, mgr_id = _register(client, "vc_mgr_adm", "vc_mgr_adm@b.com", "Pwd123!", "admin")
        brand_id = _create_brand(client, mgr_h, "AdminTestBrand",
                                 tone_style="Bold")
        _create_guideline(client, mgr_h, brand_id)

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(), None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=mgr_h,
                content_type="multipart/form-data",
            )
        assert res.status_code == 201
        assert res.get_json()["success"] is True


class TestVisualComplianceGeminiErrors:
    """Gemini API error handling tests."""

    def _setup_brand(self, client, suffix):
        mgr_h, mgr_id = _register(client, f"vc_mgr_err{suffix}", f"vc_mgr_err{suffix}@b.com", "Pwd123!", "admin")
        brand_id = _create_brand(client, mgr_h, f"GeminiErrBrand{suffix}",
                                 tone_style="Energetic")
        _create_guideline(client, mgr_h, brand_id)
        return mgr_h, brand_id

    def test_missing_api_key_returns_503(self, client):
        mgr_h, brand_id = self._setup_brand(client, "1")
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=mgr_h,
                content_type="multipart/form-data",
            )
        assert res.status_code == 503
        assert "GEMINI_API_KEY" in res.get_json()["error"] or "configured" in res.get_json()["error"].lower()

    def test_malformed_json_response_returns_502(self, client):
        mgr_h, brand_id = self._setup_brand(client, "2")
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "I cannot process this image."
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(mock_client, None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=mgr_h,
                content_type="multipart/form-data",
            )
        assert res.status_code == 502
        assert "Failed to parse AI output as JSON" in res.get_json()["error"]

    def test_gemini_api_exception_returns_502(self, client):
        mgr_h, brand_id = self._setup_brand(client, "3")

        def raise_error(*args, **kwargs):
            raise Exception("Connection timeout")

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = raise_error

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(mock_client, None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=mgr_h,
                content_type="multipart/form-data",
            )
        assert res.status_code in (502, 504)

    def test_quota_exceeded_returns_429(self, client):
        mgr_h, brand_id = self._setup_brand(client, "4")

        def raise_quota(*args, **kwargs):
            raise Exception("RESOURCE_EXHAUSTED: quota exceeded")

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = raise_quota

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(mock_client, None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=mgr_h,
                content_type="multipart/form-data",
            )
        assert res.status_code == 429


class TestVisualComplianceMissingGuidelines:
    """Test behaviour when a brand has no guidelines."""

    def test_no_guidelines_no_profile_returns_400(self, client):
        mgr_h, mgr_id = _register(client, "vc_mgr_ng", "vc_mgr_ng@b.com", "Pwd123!", "admin")
        # Brand with completely empty profile
        res = client.post(
            "/api/brands",
            data=json.dumps({"name": "EmptyBrand NG"}),
            content_type="application/json",
            headers=mgr_h,
        )
        brand_id = res.get_json()["brand"]["id"]

        result = client.post(
            "/api/visual-compliance/analyze",
            data={"image": _png_file(), "brand_id": str(brand_id)},
            headers=mgr_h,
            content_type="multipart/form-data",
        )
        assert result.status_code == 400
        assert "guideline" in result.get_json()["error"].lower() or "guidelines" in result.get_json()["error"].lower()


class TestVisualComplianceSuccessfulAnalysis:
    """End-to-end mocked success path tests."""

    def _setup(self, client, suffix):
        mgr_h, mgr_id = _register(client, f"vc_mgr_s{suffix}", f"vc_mgr_s{suffix}@b.com", "Pwd123!", "admin")
        creator_h, creator_id = _register(client, f"vc_crt_s{suffix}", f"vc_crt_s{suffix}@b.com", "Pwd123!", "creator")
        brand_id = _create_brand(client, mgr_h, f"SuccessBrand{suffix}",
                                 tone_style="Professional", restricted_words="unprofessional, sloppy")
        _add_member(client, mgr_h, brand_id, creator_id)
        g_id = _create_guideline(client, mgr_h, brand_id,
                                 category="Visual Identity",
                                 title="Logo Clear Space",
                                 rule_content="Logo must have 20px clear space on all sides.")
        return mgr_h, creator_h, brand_id, g_id

    def test_successful_analysis_persisted(self, client):
        mgr_h, creator_h, brand_id, g_id = self._setup(client, "1")

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(guideline_id=g_id), None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=creator_h,
                content_type="multipart/form-data",
            )

        assert res.status_code == 201
        data = res.get_json()
        assert data["success"] is True
        analysis = data["analysis"]
        assert analysis["brand_id"] == brand_id
        assert analysis["review_status"] == "Action Required"
        assert analysis["compliance_score"] == 72
        assert analysis["medium_severity_count"] == 1
        assert analysis["unable_to_verify_count"] == 1
        assert analysis["has_limitations"] is True
        assert len(analysis["findings"]) == 2

        # The guideline ID should be preserved for the layout finding
        layout_finding = next(
            (f for f in analysis["findings"] if f["category"] == "Layout & Spacing"), None
        )
        assert layout_finding is not None
        assert layout_finding["guideline_id"] == g_id
        assert layout_finding["severity"] == "Medium"

        # Unable-to-verify finding
        utv_finding = next(
            (f for f in analysis["findings"] if f["severity"] == "Unable to Verify"), None
        )
        assert utv_finding is not None
        assert utv_finding["human_verification_required"] is True

    def test_fabricated_guideline_id_stripped(self, client):
        mgr_h, creator_h, brand_id, g_id = self._setup(client, "2")

        # AI invents a non-existent guideline ID
        fake_output = {
            "summary": "Logo placement issue.",
            "review_status": "Violations Detected",
            "compliance_score": 45,
            "findings": [
                {
                    "category": "Logo Usage",
                    "severity": "High",
                    "visual_element": "Logo appears distorted in the header",
                    "referenced_guideline_id": 99999,  # Hallucinated
                    "guideline_rule": None,
                    "explanation": "Logo is stretched horizontally beyond acceptable ratio.",
                    "suggested_correction": "Use original logo file without scaling distortion.",
                    "human_verification_required": False,
                }
            ],
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(fake_output)
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(mock_client, None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=creator_h,
                content_type="multipart/form-data",
            )

        assert res.status_code == 201
        findings = res.get_json()["analysis"]["findings"]
        assert len(findings) == 1
        # Hallucinated ID must be stripped to None
        assert findings[0]["guideline_id"] is None

    def test_compliant_image_returns_correct_status(self, client):
        mgr_h, creator_h, brand_id, g_id = self._setup(client, "3")

        compliant_output = {
            "summary": "Image fully complies with all checked brand guidelines.",
            "review_status": "Compliant",
            "compliance_score": 100,
            "findings": [],
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(compliant_output)
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(mock_client, None),
        ):
            res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=creator_h,
                content_type="multipart/form-data",
            )

        assert res.status_code == 201
        analysis = res.get_json()["analysis"]
        assert analysis["review_status"] == "Compliant"
        assert analysis["compliance_score"] == 100
        assert analysis["issues_count"] == 0
        assert len(analysis["findings"]) == 0

    def test_history_endpoint_returns_past_analyses(self, client):
        mgr_h, creator_h, brand_id, g_id = self._setup(client, "4")

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(guideline_id=g_id), None),
        ):
            client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=creator_h,
                content_type="multipart/form-data",
            )

        history_res = client.get(
            f"/api/visual-compliance/brands/{brand_id}/history",
            headers=creator_h,
        )
        assert history_res.status_code == 200
        history = history_res.get_json()["history"]
        assert len(history) >= 1
        assert history[0]["brand_id"] == brand_id
        assert history[0]["original_filename"] == "test_poster.png"

    def test_get_analysis_by_id(self, client):
        mgr_h, creator_h, brand_id, g_id = self._setup(client, "5")

        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(guideline_id=g_id), None),
        ):
            post_res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_id)},
                headers=creator_h,
                content_type="multipart/form-data",
            )

        analysis_id = post_res.get_json()["analysis"]["id"]
        get_res = client.get(
            f"/api/visual-compliance/{analysis_id}",
            headers=creator_h,
        )
        assert get_res.status_code == 200
        assert get_res.get_json()["analysis"]["id"] == analysis_id
        assert len(get_res.get_json()["analysis"]["findings"]) == 2

    def test_cross_brand_analysis_access_denied(self, client):
        """User from Brand A must not be able to read Brand B's analysis."""
        # Brand A
        mgr_a_h, _ = _register(client, "vc_mgr_xa", "vc_mgr_xa@b.com", "Pwd123!", "admin")
        brand_a_id = _create_brand(client, mgr_a_h, "CrossBrandA",
                                   tone_style="Bold")
        _create_guideline(client, mgr_a_h, brand_a_id)

        # Brand B
        mgr_b_h, _ = _register(client, "vc_mgr_xb", "vc_mgr_xb@b.com", "Pwd123!", "admin")
        creator_b_h, creator_b_id = _register(client, "vc_crt_xb", "vc_crt_xb@b.com", "Pwd123!", "creator")
        brand_b_id = _create_brand(client, mgr_b_h, "CrossBrandB",
                                   tone_style="Minimal")
        _add_member(client, mgr_b_h, brand_b_id, creator_b_id)
        _create_guideline(client, mgr_b_h, brand_b_id)

        # Create analysis on Brand A
        with patch(
            "app.services.visual_compliance_service.VisualComplianceService._get_gemini_client",
            return_value=(_mock_gemini_success(), None),
        ):
            post_res = client.post(
                "/api/visual-compliance/analyze",
                data={"image": _png_file(), "brand_id": str(brand_a_id)},
                headers=mgr_a_h,
                content_type="multipart/form-data",
            )
        analysis_id = post_res.get_json()["analysis"]["id"]

        # Creator from Brand B must NOT see Brand A's analysis
        get_res = client.get(
            f"/api/visual-compliance/{analysis_id}",
            headers=creator_b_h,
        )
        assert get_res.status_code == 403
