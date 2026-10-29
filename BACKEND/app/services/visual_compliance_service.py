import os
import io
import re
import json
import logging
from datetime import datetime, timezone
from flask import current_app
from app.models import (
    db,
    Brand,
    BrandGuideline,
    BrandMembership,
    VisualComplianceAnalysis,
    VisualComplianceFinding,
)

logger = logging.getLogger(__name__)


def _detect_image_type(data: bytes):
    """
    Detect image type from magic bytes without using the deprecated `imghdr` module.
    Returns 'png', 'jpeg', or None.
    """
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    if data[:3] == b'\xff\xd8\xff':
        return 'jpeg'
    return None

# Configurable limits
MAX_IMAGE_BYTES = int(os.getenv("MAX_VISUAL_IMAGE_BYTES", 10 * 1024 * 1024))  # 10 MB default
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg"}
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
# Gemini-supported MIME types for inline image data
GEMINI_IMAGE_MIME_MAP = {
    "image/png": "image/png",
    "image/jpeg": "image/jpeg",
}

# Visual categories used in findings
VISUAL_CATEGORIES = [
    "Logo Usage",
    "Brand Colors",
    "Typography",
    "Layout & Spacing",
    "Contrast & Readability",
    "Visual Hierarchy",
    "Other Visual Guideline",
]

VALID_SEVERITIES = {"High", "Medium", "Low", "Unable to Verify"}
VALID_REVIEW_STATUSES = {"Compliant", "Action Required", "Violations Detected"}


class VisualComplianceService:
    # ─────────────────────────────────────────────────────────────────────────
    # File validation (pure Python, no temp files stored on disk)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def validate_image_upload(file_storage):
        """
        Validate a Werkzeug FileStorage object for type, extension, and size.

        Returns (image_bytes: bytes, mime_type: str, original_filename: str, error: str|None)
        """
        if file_storage is None or file_storage.filename == "":
            return None, None, None, "No image file was provided."

        original_filename = file_storage.filename or "upload"

        # Extension check (case-insensitive)
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            return (
                None, None, original_filename,
                f"Unsupported file extension '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            )

        # Read the file into memory (avoids storing on disk)
        image_bytes = file_storage.read()
        if not image_bytes:
            return None, None, original_filename, "Uploaded file is empty."

        # Size check
        if len(image_bytes) > MAX_IMAGE_BYTES:
            max_mb = MAX_IMAGE_BYTES / (1024 * 1024)
            return (
                None, None, original_filename,
                f"Image exceeds the maximum allowed size of {max_mb:.0f} MB."
            )

        # Magic-byte MIME detection (do NOT trust the Content-Type header alone)
        detected_type = _detect_image_type(image_bytes)
        mime_map = {'png': 'image/png', 'jpeg': 'image/jpeg'}
        if detected_type not in mime_map:
            return (
                None, None, original_filename,
                "File content does not match a supported image type (PNG or JPEG). "
                "Please ensure you are uploading a real image file."
            )
        mime_type = mime_map[detected_type]

        # Cross-check extension vs. detected type to catch mismatches
        if ext in ("jpg", "jpeg") and detected_type != "jpeg":
            return (
                None, None, original_filename,
                f"File extension '.{ext}' does not match the detected content type '{mime_type}'."
            )
        if ext == "png" and detected_type != "png":
            return (
                None, None, original_filename,
                f"File extension '.{ext}' does not match the detected content type '{mime_type}'."
            )

        return image_bytes, mime_type, original_filename, None

    # ─────────────────────────────────────────────────────────────────────────
    # Gemini client (reuses existing pattern from compliance_service.py)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_gemini_client():
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key is None:
            try:
                api_key = current_app.config.get("GEMINI_API_KEY")
            except Exception:
                pass

        if not api_key or api_key.strip() in ["", "your-gemini-api-key-here"]:
            return None, (
                "Gemini API key is not configured. "
                "Please configure a valid GEMINI_API_KEY in BACKEND/.env to enable AI visual compliance checking."
            )

        try:
            from google import genai
            client = genai.Client(api_key=api_key.strip())
            return client, None
        except Exception as e:
            return None, f"Failed to initialize Google Gen AI SDK: {str(e)}"

    # ─────────────────────────────────────────────────────────────────────────
    # Prompt construction
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_visual_prompt(brand, guidelines):
        """
        Build the multimodal analysis prompt combining brand guidelines and the image.
        The image bytes are passed separately as a Part – this function only builds text.
        """
        # Serialize relevant visual guidelines only (or all if no visual ones exist)
        visual_categories = {"Visual Identity", "Accessibility", "Other", "Tone"}
        visual_guidelines = [g for g in guidelines if g.category in visual_categories]
        all_guidelines = visual_guidelines if visual_guidelines else guidelines

        guidelines_list = []
        for g in all_guidelines:
            guidelines_list.append({
                "id": g.id,
                "category": g.category,
                "title": g.title,
                "rule": g.rule_content,
                "approved_wording": getattr(g, "approved_wording", "") or "Not specified",
                "prohibited_wording": getattr(g, "prohibited_wording", "") or "Not specified",
                "severity": getattr(g, "severity", "Medium") or "Medium",
                "evidence_reference": g.reference_evidence or "Not specified",
            })

        guideline_note = ""
        if not guidelines_list:
            guideline_note = (
                "NOTE: This brand has no specific registered guidelines. "
                "Audit is limited to the brand profile fields below and general visual best practices."
            )

        prompt = f"""You are BrandGuard AI Visual Inspector — an authoritative AI system that audits marketing images and posters for visual brand compliance.

SECURITY & INTEGRITY SAFEGUARDS:
1. Analyze ONLY the image provided. Do NOT fabricate or invent violations that are not visually detectable.
2. SOURCE-BASED GROUNDING: Base all findings on the brand guidelines provided below. Do NOT invent rules.
3. If a guideline cannot be verified from the image (e.g. specific Pantone codes, proprietary font names), set severity to "Unable to Verify" and explain why.
4. Referenced guideline IDs must be taken exactly from the list below. Do NOT invent guideline IDs.
5. Provide a defensible compliance_score between 0 (fully non-compliant) and 100 (fully compliant) based on findings. Only include the score if you have enough visual evidence to support it; otherwise omit it (set to null).

=== BRAND GOVERNANCE PROFILE ===
Brand Name: {brand.name}
Brand Description: {brand.description or 'None provided'}
Approved Communication Tone & Style: {brand.tone_style or 'None specified'}
Approved Terminology: {brand.approved_terminology or 'None specified'}
Restricted / Prohibited Words: {brand.restricted_words or 'None specified'}
Approved Facts: {brand.approved_facts or 'None specified'}
Prohibited Claims: {brand.prohibited_claims or 'None specified'}

=== ACTIVE BRAND GUIDELINE RULES ({len(all_guidelines)} rules for visual audit) ===
{guideline_note}
{json.dumps(guidelines_list, indent=2)}

=== VISUAL AUDIT SCOPE ===
For each visually detectable element, evaluate the provided image for:
1. Logo Usage: Presence, placement, proportions, distortion, unauthorized modification, clear-space violations.
2. Brand Colors: Consistency with any stated color palette; obvious clashes with expected brand palette.
3. Typography: Font style consistency, readability, hierarchy (if typography guidelines exist).
4. Layout & Spacing: Visual hierarchy, crowding, alignment, white-space usage.
5. Contrast & Readability: Text legibility, contrast ratios, accessibility concerns.
6. Other Visual Guidelines: Any other brand rule that is visually checkable from the image.

=== SEVERITY LEVELS ===
- High: Clear, visually confirmed violation of a named brand rule with high confidence.
- Medium: Possible violation or noticeable deviation that needs review.
- Low: Minor stylistic or layout concern.
- Unable to Verify: The rule exists but cannot be confirmed or denied from the image alone.

=== OUTPUT FORMAT ===
Return ONLY valid JSON matching this exact schema. Do NOT include markdown fences.
{{
  "summary": "2-3 sentence executive summary of the visual compliance posture, citing checked elements and any limitations.",
  "review_status": "Compliant" | "Action Required" | "Violations Detected",
  "compliance_score": <integer 0-100 or null>,
  "findings": [
    {{
      "category": "Logo Usage" | "Brand Colors" | "Typography" | "Layout & Spacing" | "Contrast & Readability" | "Visual Hierarchy" | "Other Visual Guideline",
      "severity": "High" | "Medium" | "Low" | "Unable to Verify",
      "visual_element": "Description of the specific visual element or area of the image where the issue was detected",
      "referenced_guideline_id": <int_id_from_list_above_or_null>,
      "guideline_rule": "The specific rule text from the guideline (or null)",
      "explanation": "Objective explanation of why this is a finding",
      "suggested_correction": "Concrete, actionable correction suggestion",
      "human_verification_required": true | false
    }}
  ]
}}
"""
        return prompt

    # ─────────────────────────────────────────────────────────────────────────
    # AI response validation
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_and_validate_response(raw_text, valid_guideline_ids, guidelines=None):
        """
        Parse the Gemini response and validate all fields strictly.
        Returns (validated_dict, error_str).
        """
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return None, f"Failed to parse AI output as JSON: {str(e)}"

        if not isinstance(data, dict):
            return None, "Malformed AI response: root must be a JSON object."

        summary = data.get("summary")
        if not summary or not isinstance(summary, str):
            summary = "Visual brand compliance analysis completed based on registered brand guidelines."

        review_status = data.get("review_status", "Action Required")
        if review_status not in VALID_REVIEW_STATUSES:
            review_status = "Action Required"

        # Compliance score: only accept integers in [0, 100]
        raw_score = data.get("compliance_score")
        compliance_score = None
        if raw_score is not None:
            try:
                score_int = int(raw_score)
                if 0 <= score_int <= 100:
                    compliance_score = score_int
            except (ValueError, TypeError):
                compliance_score = None

        raw_findings = data.get("findings", [])
        if not isinstance(raw_findings, list):
            raw_findings = []

        validated_findings = []
        high_count = med_count = low_count = unable_count = 0

        for f in raw_findings:
            if not isinstance(f, dict):
                continue

            visual_element = str(f.get("visual_element") or "").strip()
            explanation = str(f.get("explanation") or "").strip()
            if not visual_element or not explanation:
                continue  # Skip malformed entries

            category = str(f.get("category") or "Other Visual Guideline").strip()
            if category not in VISUAL_CATEGORIES:
                category = "Other Visual Guideline"

            raw_sev = str(f.get("severity") or "Medium").strip()
            # Capitalise first letter of each word for "Unable to Verify"
            if raw_sev.lower() in ("unable to verify", "unableto verify", "unable_to_verify"):
                raw_sev = "Unable to Verify"
            elif raw_sev.capitalize() not in VALID_SEVERITIES:
                raw_sev = "Medium"
            else:
                raw_sev = raw_sev.capitalize()

            if raw_sev == "High":
                high_count += 1
            elif raw_sev == "Medium":
                med_count += 1
            elif raw_sev == "Low":
                low_count += 1
            elif raw_sev == "Unable to Verify":
                unable_count += 1

            # Validate guideline reference
            ref_id = f.get("referenced_guideline_id") or f.get("guideline_id")
            if ref_id is not None:
                try:
                    ref_id = int(ref_id)
                    if ref_id not in valid_guideline_ids:
                        ref_id = None  # Strip hallucinated IDs
                except (ValueError, TypeError):
                    ref_id = None
            elif guidelines and f.get("guideline_title"):
                target = str(f["guideline_title"]).strip().lower()
                for g in guidelines:
                    if g.title and g.title.strip().lower() == target:
                        ref_id = g.id
                        break

            guideline_rule = str(f.get("guideline_rule") or "").strip() or None
            suggested_correction = str(f.get("suggested_correction") or "").strip()
            human_verify = bool(f.get("human_verification_required", False))

            validated_findings.append({
                "category": category,
                "severity": raw_sev,
                "visual_element": visual_element,
                "guideline_id": ref_id,
                "guideline_rule": guideline_rule,
                "explanation": explanation,
                "suggested_correction": suggested_correction,
                "human_verification_required": human_verify,
            })

        # Recompute review_status based on validated findings
        real_violations = high_count + med_count + low_count
        if real_violations == 0 and unable_count == 0:
            review_status = "Compliant"
        elif high_count > 0:
            review_status = "Violations Detected"
        elif med_count > 0 or low_count > 0:
            review_status = "Action Required"
        # If only unable_to_verify, keep as Action Required
        elif unable_count > 0 and review_status == "Compliant":
            review_status = "Action Required"

        return {
            "summary": summary,
            "review_status": review_status,
            "compliance_score": compliance_score,
            "issues_count": real_violations,
            "high_severity_count": high_count,
            "medium_severity_count": med_count,
            "low_severity_count": low_count,
            "unable_to_verify_count": unable_count,
            "has_limitations": unable_count > 0,
            "findings": validated_findings,
        }, None

    # ─────────────────────────────────────────────────────────────────────────
    # Main analysis entry point
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def analyze_image(cls, brand_id, user_id, role, image_bytes, mime_type, original_filename, file_size):
        """
        Perform AI visual compliance analysis for a brand image.
        Returns (analysis_dict, error_str, http_status_code).
        """
        # 1. Verify brand exists
        brand = db.session.get(Brand, brand_id)
        if not brand:
            return None, "Brand not found.", 404

        # 2. Enforce brand-level access isolation
        from app.services.brand_service import BrandService
        if not BrandService.user_has_brand_access(brand_id, user_id, role):
            return None, "You do not have permission to run compliance checks for this brand.", 403

        # 3. Fetch active guidelines for this brand
        guidelines = BrandGuideline.query.filter_by(brand_id=brand_id, is_active=True).all()
        valid_guideline_ids = {g.id for g in guidelines}

        # 4. Check if there are any brand rules at all
        has_rules = bool(
            guidelines
            or brand.tone_style
            or brand.approved_terminology
            or brand.restricted_words
            or brand.approved_facts
            or brand.prohibited_claims
        )
        if not has_rules:
            return None, (
                f"A meaningful visual compliance check cannot be completed because brand '{brand.name}' "
                "has no registered guidelines, tone, facts, or restricted terms. "
                "Please ask a Brand Manager to configure guidelines first."
            ), 400

        # 5. Get Gemini client
        client, err = cls._get_gemini_client()
        if err:
            return None, err, 503

        # 6. Build prompt
        prompt_text = cls._build_visual_prompt(brand, guidelines)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        gemini_mime = GEMINI_IMAGE_MIME_MAP.get(mime_type, "image/jpeg")

        # 7. Call Gemini with multimodal input (text + inline image)
        try:
            from google.genai import types

            image_part = types.Part.from_bytes(data=image_bytes, mime_type=gemini_mime)
            text_part = types.Part.from_text(text=prompt_text)

            response = client.models.generate_content(
                model=model_name,
                contents=[types.Content(parts=[text_part, image_part], role="user")],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            raw_text = response.text
        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "invalid api key" in err_msg.lower():
                return None, "Gemini API key is invalid. Please verify your GEMINI_API_KEY.", 503
            elif "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                return None, "Gemini API rate limit or quota exceeded. Please try again shortly.", 429
            elif "timeout" in err_msg.lower():
                return None, "Gemini API request timed out. Please try again.", 504
            logger.error("Gemini visual compliance API error: %s", err_msg)
            return None, f"Gemini API request failed: {err_msg}", 502

        # 8. Parse and validate the AI response
        validated_data, parse_err = cls._parse_and_validate_response(
            raw_text, valid_guideline_ids, guidelines=guidelines
        )
        if parse_err:
            return None, parse_err, 502

        # 9. Persist analysis record
        analysis = VisualComplianceAnalysis(
            brand_id=brand_id,
            user_id=user_id,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size_bytes=file_size,
            model_identifier=model_name,
            summary=validated_data["summary"],
            review_status=validated_data["review_status"],
            compliance_score=validated_data["compliance_score"],
            issues_count=validated_data["issues_count"],
            high_severity_count=validated_data["high_severity_count"],
            medium_severity_count=validated_data["medium_severity_count"],
            low_severity_count=validated_data["low_severity_count"],
            unable_to_verify_count=validated_data["unable_to_verify_count"],
            has_limitations=validated_data["has_limitations"],
        )
        db.session.add(analysis)
        db.session.flush()  # Get analysis.id before adding findings

        # 10. Persist findings
        for f_data in validated_data["findings"]:
            finding = VisualComplianceFinding(
                analysis_id=analysis.id,
                category=f_data["category"],
                severity=f_data["severity"],
                visual_element=f_data["visual_element"],
                guideline_id=f_data["guideline_id"],
                guideline_rule=f_data["guideline_rule"],
                explanation=f_data["explanation"],
                suggested_correction=f_data["suggested_correction"],
                human_verification_required=f_data["human_verification_required"],
            )
            db.session.add(finding)

        db.session.commit()

        return analysis.to_dict(include_findings=True), None, 201

    # ─────────────────────────────────────────────────────────────────────────
    # History retrieval
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_brand_history(cls, brand_id, user_id, role, limit=20):
        """
        Return visual compliance analysis history for a brand.
        Enforces brand-level data isolation.
        """
        from app.services.brand_service import BrandService
        if not BrandService.user_has_brand_access(brand_id, user_id, role):
            return None, "Access denied to this brand's visual compliance history.", 403

        brand = db.session.get(Brand, brand_id)
        if not brand:
            return None, "Brand not found.", 404

        analyses = (
            VisualComplianceAnalysis.query
            .filter_by(brand_id=brand_id)
            .order_by(VisualComplianceAnalysis.created_at.desc())
            .limit(max(1, min(int(limit), 100)))
            .all()
        )
        return [a.to_dict(include_findings=False) for a in analyses], None, 200

    @classmethod
    def get_analysis_by_id(cls, analysis_id, user_id, role):
        """
        Retrieve a single visual analysis by ID, enforcing brand access.
        """
        analysis = db.session.get(VisualComplianceAnalysis, analysis_id)
        if not analysis:
            return None, "Visual compliance analysis not found.", 404

        from app.services.brand_service import BrandService
        if not BrandService.user_has_brand_access(analysis.brand_id, user_id, role):
            return None, "Access denied to this visual compliance analysis.", 403

        return analysis.to_dict(include_findings=True), None, 200
