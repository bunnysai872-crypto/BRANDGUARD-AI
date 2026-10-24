import io
import re
from werkzeug.utils import secure_filename
from app.models import db, BrandGuideline, GUIDELINE_CATEGORIES, GUIDELINE_SEVERITIES, Brand

class GuidelineService:
    @staticmethod
    def create_guideline(brand_id, data):
        brand = db.session.get(Brand, brand_id)
        if not brand:
            return None, "Brand not found.", 404

        category = (data.get("category") or "").strip()
        if category not in GUIDELINE_CATEGORIES:
            return None, f"Invalid category. Must be one of: {', '.join(GUIDELINE_CATEGORIES)}", 400

        title = (data.get("title") or "").strip()
        if not title:
            return None, "Guideline title is required.", 400

        rule_content = (data.get("rule_content") or data.get("description") or "").strip()
        if not rule_content:
            return None, "Guideline description / rule content is required.", 400

        severity = (data.get("severity") or "Medium").strip()
        if severity not in GUIDELINE_SEVERITIES:
            severity = "Medium"

        is_active = data.get("is_active", True)
        if isinstance(is_active, str):
            is_active = is_active.lower() not in ["false", "0", "inactive"]

        guideline = BrandGuideline(
            brand_id=brand_id,
            category=category,
            title=title,
            rule_content=rule_content,
            approved_wording=(data.get("approved_wording") or "").strip(),
            prohibited_wording=(data.get("prohibited_wording") or "").strip(),
            severity=severity,
            is_active=bool(is_active),
            reference_evidence=(data.get("reference_evidence") or "").strip()
        )
        db.session.add(guideline)
        db.session.commit()

        return guideline.to_dict(), None, 201

    @staticmethod
    def get_guidelines_for_brand(brand_id, category=None, active_only=False):
        brand = db.session.get(Brand, brand_id)
        if not brand:
            return None, "Brand not found.", 404

        query = BrandGuideline.query.filter_by(brand_id=brand_id)
        if category and category != "All":
            query = query.filter_by(category=category)
        if active_only:
            query = query.filter_by(is_active=True)

        guidelines = query.order_by(BrandGuideline.category.asc(), BrandGuideline.created_at.desc()).all()
        return [g.to_dict() for g in guidelines], None, 200

    @staticmethod
    def get_guideline_by_id(guideline_id):
        return db.session.get(BrandGuideline, guideline_id)

    @staticmethod
    def update_guideline(guideline_id, data):
        guideline = db.session.get(BrandGuideline, guideline_id)
        if not guideline:
            return None, "Guideline not found.", 404

        if "category" in data:
            category = (data.get("category") or "").strip()
            if category not in GUIDELINE_CATEGORIES:
                return None, f"Invalid category. Must be one of: {', '.join(GUIDELINE_CATEGORIES)}", 400
            guideline.category = category

        if "title" in data:
            title = (data.get("title") or "").strip()
            if not title:
                return None, "Title cannot be empty.", 400
            guideline.title = title

        if "rule_content" in data or "description" in data:
            rule_content = (data.get("rule_content") or data.get("description") or "").strip()
            if not rule_content:
                return None, "Rule content cannot be empty.", 400
            guideline.rule_content = rule_content

        if "approved_wording" in data:
            guideline.approved_wording = (data.get("approved_wording") or "").strip()

        if "prohibited_wording" in data:
            guideline.prohibited_wording = (data.get("prohibited_wording") or "").strip()

        if "severity" in data:
            sev = (data.get("severity") or "Medium").strip()
            if sev in GUIDELINE_SEVERITIES:
                guideline.severity = sev

        if "is_active" in data:
            val = data.get("is_active")
            if isinstance(val, str):
                guideline.is_active = val.lower() not in ["false", "0", "inactive"]
            else:
                guideline.is_active = bool(val)

        if "reference_evidence" in data:
            guideline.reference_evidence = (data.get("reference_evidence") or "").strip()

        db.session.commit()
        return guideline.to_dict(), None, 200

    @staticmethod
    def delete_guideline(guideline_id):
        guideline = db.session.get(BrandGuideline, guideline_id)
        if not guideline:
            return False, "Guideline not found.", 404

        db.session.delete(guideline)
        db.session.commit()
        return True, None, 200

    @staticmethod
    def extract_text_from_file(file_storage, max_size_bytes=5 * 1024 * 1024):
        """
        Safely extract text from uploaded TXT or text-based PDF file.
        Enforces filename sanitization, size limits, and safe character decoding.
        """
        if not file_storage or not file_storage.filename:
            return None, "No file provided or filename is empty.", 400

        filename = secure_filename(file_storage.filename)
        lower_name = filename.lower()
        if not (lower_name.endswith(".txt") or lower_name.endswith(".pdf") or lower_name.endswith(".md")):
            return None, "Unsupported file format. Please upload a .txt or .pdf file.", 400

        # Read into memory safely
        file_bytes = file_storage.read()
        if len(file_bytes) == 0:
            return None, "The uploaded file is empty.", 400
        if len(file_bytes) > max_size_bytes:
            return None, f"File exceeds maximum allowed size of {max_size_bytes // (1024 * 1024)}MB.", 400

        extracted_text = ""
        if lower_name.endswith(".txt") or lower_name.endswith(".md"):
            try:
                extracted_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    extracted_text = file_bytes.decode("latin-1")
                except Exception as e:
                    return None, f"Failed to decode text file: {str(e)}", 400
        elif lower_name.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(file_bytes))
                if len(reader.pages) == 0:
                    return None, "PDF file contains no pages.", 400
                pages_text = []
                for i, page in enumerate(reader.pages):
                    page_t = page.extract_text() or ""
                    if page_t.strip():
                        pages_text.append(page_t)
                extracted_text = "\n\n".join(pages_text)
                if not extracted_text.strip():
                    return None, "Could not extract readable text from PDF. Scanned or image-only PDFs are not supported.", 400
            except Exception as e:
                return None, f"Failed to extract text from PDF: {str(e)}", 400

        # Sanitize extracted text: remove null bytes and excessive whitespace
        cleaned_text = extracted_text.replace("\x00", "").strip()
        cleaned_text = re.sub(r"\r\n|\r", "\n", cleaned_text)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        # Enforce maximum character length (50k chars)
        if len(cleaned_text) > 50000:
            cleaned_text = cleaned_text[:50000]

        word_count = len(cleaned_text.split())
        return {
            "filename": filename,
            "text": cleaned_text,
            "extracted_text": cleaned_text,
            "word_count": word_count,
            "characters_count": len(cleaned_text),
            "length": len(cleaned_text)
        }, None, 200
