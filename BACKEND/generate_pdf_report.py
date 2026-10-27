"""
Generate professional PDF report for BrandGuard AI Hackathon Round 2 Submission.
Outputs to docs/ROUND2_SUBMISSION.pdf using ReportLab.

Usage:  python generate_pdf_report.py
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

# ── Real deployed URLs ────────────────────────────────────────────────────────
GITHUB_URL   = "https://github.com/bunnysai872-crypto/BRANDGUARD-AI"
FRONTEND_URL = "https://brandguard-ai-tau.vercel.app/login"
BACKEND_URL  = "https://brandguard-ai-fdfl.onrender.com"
HEALTH_URL   = "https://brandguard-ai-fdfl.onrender.com/api/health"
# ─────────────────────────────────────────────────────────────────────────────


def build_pdf():
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    os.makedirs(docs_dir, exist_ok=True)
    pdf_path = os.path.join(docs_dir, "ROUND2_SUBMISSION.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=42,
        rightMargin=42,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()

    # ── Colour palette ────────────────────────────────────────────────────────
    PRIMARY        = colors.HexColor("#14532d")
    SECONDARY      = colors.HexColor("#166534")
    TEXT_DARK      = colors.HexColor("#0f172a")
    TEXT_MUTED     = colors.HexColor("#475569")
    BORDER_COLOR   = colors.HexColor("#e2e8f0")
    BG_LIGHT       = colors.HexColor("#f8fafc")
    ACCENT_EMERALD = colors.HexColor("#059669")
    ACCENT_BLUE    = colors.HexColor("#1d4ed8")

    # ── Typography ────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "DocTitle", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=22, leading=27,
        textColor=PRIMARY, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle", parent=styles["Normal"],
        fontName="Helvetica", fontSize=11, leading=15,
        textColor=TEXT_MUTED, spaceAfter=14,
    )
    h1_style = ParagraphStyle(
        "H1", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=13, leading=17,
        textColor=PRIMARY, spaceBefore=14, spaceAfter=5,
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=10.5, leading=14,
        textColor=SECONDARY, spaceBefore=7, spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9.5, leading=13.5,
        textColor=TEXT_DARK, spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, leading=13,
        textColor=TEXT_DARK, leftIndent=14, spaceAfter=3,
    )
    link_style = ParagraphStyle(
        "Link", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, leading=13,
        textColor=ACCENT_BLUE, spaceAfter=3,
    )
    callout_style = ParagraphStyle(
        "Callout", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=9, leading=13,
        textColor=PRIMARY, spaceAfter=6,
    )
    tbl_hdr = ParagraphStyle(
        "TblHdr", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=9, leading=11,
        textColor=colors.white,
    )
    tbl_cell = ParagraphStyle(
        "TblCell", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8.5, leading=11.5,
        textColor=TEXT_DARK,
    )
    tbl_cell_link = ParagraphStyle(
        "TblCellLink", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8.5, leading=11.5,
        textColor=ACCENT_BLUE,
    )

    story = []

    # ── Cover / Header ────────────────────────────────────────────────────────
    story.append(Paragraph("BrandGuard AI – Intelligent Brand Governance Platform", title_style))
    story.append(Paragraph(
        "Inkloom AI Hackathon · Round 2 (The Build) · October 2026",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceBefore=0, spaceAfter=10))

    # ── Project metadata card ─────────────────────────────────────────────────
    meta = [
        [
            Paragraph("<b>Project:</b> CloudNova BrandGuard AI", tbl_cell),
            Paragraph("<b>Stack:</b> React 18 · Flask 3 · Gemini 2.5 Flash", tbl_cell),
        ],
        [
            Paragraph(f"<b>GitHub:</b> {GITHUB_URL}", tbl_cell_link),
            Paragraph(f"<b>Live Demo:</b> {FRONTEND_URL}", tbl_cell_link),
        ],
        [
            Paragraph(f"<b>Backend API:</b> {BACKEND_URL}", tbl_cell_link),
            Paragraph(f"<b>Health Check:</b> {HEALTH_URL}", tbl_cell_link),
        ],
        [
            Paragraph("<b>Tests:</b> 39 / 39 Passed · pytest 9.1", tbl_cell),
            Paragraph("<b>Build:</b> Vite 5 · 0 errors · 0 warnings", tbl_cell),
        ],
    ]
    meta_tbl = Table(meta, colWidths=[258, 272])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BG_LIGHT),
        ("BOX",          (0, 0), (-1, -1), 1,   BORDER_COLOR),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 10))

    # ── 1. Problem Statement ──────────────────────────────────────────────────
    story.append(Paragraph("1. Problem Statement", h1_style))
    story.append(Paragraph(
        "Enterprise marketing teams and creative agencies face acute brand safety risks when generating "
        "high-velocity promotional content. The proliferation of generative AI tools has accelerated output "
        "tenfold but dramatically elevated the risk of unsubstantiated claims "
        "(<i>'100% downtime-proof'</i>, <i>'zero cost forever'</i>), off-brand tone deviations, "
        "and hallucinated organizational facts. Manual review cycles in spreadsheets lack audit history, "
        "versioning snapshots, and objective rule enforcement, exposing organizations to FTC, ASA, "
        "and SEC advertising violations.",
        body_style,
    ))

    # ── 2. Solution ───────────────────────────────────────────────────────────
    story.append(Paragraph("2. Proposed Solution", h1_style))
    story.append(Paragraph(
        "BrandGuard AI is a multi-tenant brand governance platform delivering an end-to-end "
        "human-in-the-loop compliance workflow:", body_style,
    ))
    bullets = [
        "<b>Centralized Brand Rulebooks:</b> Full governance across 10 categories — Tone, Terminology, "
        "Messaging, Approved Facts, Restricted Claims, Prohibited Claims, Mandatory Disclaimer, "
        "Visual Identity, Accessibility, Other.",
        "<b>Evidence-Grounded AI Auditing:</b> Google Gemini 2.5 Flash evaluates copy strictly against "
        "active guidelines, returning structured JSON findings with severity (Critical/High/Medium/Low), "
        "guideline citations (DB-validated to prevent hallucination), suggested rewrite, and confidence level.",
        "<b>Immutable Revision Snapshots:</b> Every content edit creates an unalterable ContentRevision "
        "record. Stale reports are automatically flagged (is_outdated=True), blocking approval.",
        "<b>Manager Sign-Off &amp; Immutable Audit Trail:</b> Content is locked during review. "
        "Managers approve or request changes with mandatory comments; all decisions are permanently "
        "logged in ReviewDecision with reviewer identity and timestamp.",
        "<b>In-App Publishing:</b> Brand Managers publish Approved content; published_at and "
        "published_by_id are persisted. Published submissions are permanently locked.",
    ]
    for b in bullets:
        story.append(Paragraph(f"• {b}", bullet_style))

    # ── 3. Completed Features ─────────────────────────────────────────────────
    story.append(Paragraph("3. Completed & Verified Features", h1_style))
    feat_rows = [
        [Paragraph("Phase", tbl_hdr), Paragraph("Feature Area", tbl_hdr), Paragraph("Key Capabilities", tbl_hdr)],
        [
            Paragraph("1", tbl_cell),
            Paragraph("<b>Auth &amp; RBAC</b>", tbl_cell),
            Paragraph("Flask-JWT-Extended · PBKDF2 hashing · admin/creator roles · ProtectedRoute SPA guards · idempotent demo-login endpoint", tbl_cell),
        ],
        [
            Paragraph("2", tbl_cell),
            Paragraph("<b>Brand Governance</b>", tbl_cell),
            Paragraph("Brand profiles · 10-category guideline taxonomy · severity levels · team membership · cross-brand data isolation · file text extraction (pypdf)", tbl_cell),
        ],
        [
            Paragraph("3", tbl_cell),
            Paragraph("<b>Gemini AI Engine</b>", tbl_cell),
            Paragraph("google-genai SDK · gemini-2.5-flash · JSON output mode · guideline ID validation · stale report detection · malformed response handling", tbl_cell),
        ],
        [
            Paragraph("4", tbl_cell),
            Paragraph("<b>Manager Workflow</b>", tbl_cell),
            Paragraph("Approval queue · high-severity acknowledgement modal · Approved/Changes Requested decisions · ReviewDecision audit timeline · status locking", tbl_cell),
        ],
        [
            Paragraph("5", tbl_cell),
            Paragraph("<b>Publishing &amp; Analytics</b>", tbl_cell),
            Paragraph("POST /publish endpoint · Published archive UI · governance analytics (severity dist., category dist., common issues, timeline trends) · Vercel proxy fix", tbl_cell),
        ],
    ]
    feat_tbl = Table(feat_rows, colWidths=[28, 105, 397])
    feat_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), PRIMARY),
        ("BOX",          (0, 0), (-1, -1), 1, BORDER_COLOR),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(feat_tbl)
    story.append(Spacer(1, 8))

    # ── 4. Technology Stack ───────────────────────────────────────────────────
    story.append(Paragraph("4. Technology Stack", h1_style))
    tech_rows = [
        [Paragraph("Layer", tbl_hdr), Paragraph("Technology", tbl_hdr), Paragraph("Purpose", tbl_hdr)],
        [Paragraph("Frontend", tbl_cell), Paragraph("React 18 + Vite 5", tbl_cell), Paragraph("SPA, HMR, role-based ProtectedRoute, Tailwind CSS", tbl_cell)],
        [Paragraph("Backend", tbl_cell), Paragraph("Python 3.12 + Flask 3.0", tbl_cell), Paragraph("Application Factory, modular blueprints, RESTful API", tbl_cell)],
        [Paragraph("Database", tbl_cell), Paragraph("SQLAlchemy 3.1 / PostgreSQL", tbl_cell), Paragraph("10-table relational schema; SQLite for local dev", tbl_cell)],
        [Paragraph("Auth", tbl_cell), Paragraph("Flask-JWT-Extended 4.6", tbl_cell), Paragraph("Stateless JWT, HMAC-SHA256, 7-day TTL, role claims", tbl_cell)],
        [Paragraph("AI Engine", tbl_cell), Paragraph("google-genai / Gemini 2.5 Flash", tbl_cell), Paragraph("JSON output mode, temp=0.1, structured findings", tbl_cell)],
        [Paragraph("WSGI", tbl_cell), Paragraph("Gunicorn 21.2", tbl_cell), Paragraph("Multi-worker production server (Render)", tbl_cell)],
        [Paragraph("Hosting", tbl_cell), Paragraph("Vercel + Render", tbl_cell), Paragraph("Vercel (SPA + API proxy) · Render (Flask + PostgreSQL)", tbl_cell)],
        [Paragraph("Testing", tbl_cell), Paragraph("pytest 9.1", tbl_cell), Paragraph("39 integration tests, in-memory SQLite fixtures", tbl_cell)],
    ]
    tech_tbl = Table(tech_rows, colWidths=[80, 145, 305])
    tech_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), SECONDARY),
        ("BOX",          (0, 0), (-1, -1), 1, BORDER_COLOR),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ("TOPPADDING",   (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3.5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tech_tbl)
    story.append(Spacer(1, 8))

    # ── 5. Test Evidence ──────────────────────────────────────────────────────
    story.append(Paragraph("5. Automated Test Coverage — 39 / 39 Passed", h1_style))
    story.append(Paragraph(
        "All tests run with <i>pytest 9.1</i> against an in-memory SQLite database (no live API calls "
        "for AI tests — Gemini is mocked). Zero failures on 2026-10-24.", body_style,
    ))
    test_rows = [
        [Paragraph("Test File", tbl_hdr), Paragraph("Tests", tbl_hdr), Paragraph("Scope", tbl_hdr), Paragraph("Result", tbl_hdr)],
        [Paragraph("test_auth.py", tbl_cell), Paragraph("11", tbl_cell), Paragraph("Registration · login · JWT · RBAC · demo-login idempotency", tbl_cell), Paragraph("✓ PASS", tbl_cell)],
        [Paragraph("test_hackathon_upgrades.py", tbl_cell), Paragraph("9", tbl_cell), Paragraph("Guideline fields · cross-brand isolation · PDF extraction · analytics · publish security", tbl_cell), Paragraph("✓ PASS", tbl_cell)],
        [Paragraph("test_phase2.py", tbl_cell), Paragraph("3", tbl_cell), Paragraph("Brand management · guideline CRUD · revision history", tbl_cell), Paragraph("✓ PASS", tbl_cell)],
        [Paragraph("test_phase3.py", tbl_cell), Paragraph("5", tbl_cell), Paragraph("Gemini API key missing · mocked analysis · ID sanitization · stale detection · malformed JSON", tbl_cell), Paragraph("✓ PASS", tbl_cell)],
        [Paragraph("test_phase4.py", tbl_cell), Paragraph("2", tbl_cell), Paragraph("Approval validation · manager review lifecycle", tbl_cell), Paragraph("✓ PASS", tbl_cell)],
        [Paragraph("test_production_workflows.py", tbl_cell), Paragraph("3", tbl_cell), Paragraph("Health check safety · cross-user isolation · full E2E lifecycle", tbl_cell), Paragraph("✓ PASS", tbl_cell)],
        [Paragraph("test_publishing.py", tbl_cell), Paragraph("6", tbl_cell), Paragraph("Manager-only publish · creator blocked · non-Approved blocked · cross-brand isolation · edit lock", tbl_cell), Paragraph("✓ PASS", tbl_cell)],
    ]
    test_tbl = Table(test_rows, colWidths=[148, 38, 290, 54])
    test_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), SECONDARY),
        ("BOX",          (0, 0), (-1, -1), 1, BORDER_COLOR),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TEXTCOLOR",    (3, 1), (3, -1), ACCENT_EMERALD),
        ("FONTNAME",     (3, 1), (3, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(test_tbl)
    story.append(Spacer(1, 8))

    # ── 6. Round 1 → Round 2 Progress ────────────────────────────────────────
    story.append(Paragraph("6. Progress from Round 1 to Round 2", h1_style))
    progress = [
        "<b>Complete Database Schema:</b> 10-table relational SQLAlchemy schema with cascading deletes, indexed FK, and non-destructive auto-migration.",
        "<b>Gemini AI Integration:</b> google-genai SDK, gemini-2.5-flash, JSON output mode (temp=0.1), structured findings with guideline ID validation.",
        "<b>Immutable Revision History:</b> Every content edit snapshots an unalterable ContentRevision; stale-report detection blocks outdated approvals.",
        "<b>Publishing Workflow:</b> POST /api/submissions/:id/publish — Brand Manager only, Approved status only; permanent edit lock post-publish.",
        "<b>Governance Analytics:</b> Real-time DB-computed dashboard (status counts, severity dist., common issues, timeline trends).",
        "<b>39 Automated Tests:</b> Full pytest coverage across auth, AI compliance, manager workflow, publishing, and cross-user isolation.",
        "<b>Live Deployment:</b> Vercel frontend + Render backend with PostgreSQL; 405 POST bug fixed via API proxy rewrite in vercel.json.",
    ]
    for p in progress:
        story.append(Paragraph(f"• {p}", bullet_style))

    # ── 7. Round 3 Roadmap ────────────────────────────────────────────────────
    story.append(Paragraph("7. Planned Round 3 Improvements", h1_style))
    r3 = [
        "<b>Visual Brand Compliance Engine:</b> Multimodal Gemini analysis of image creatives (PNG/JPG banners, PDF collateral) — logo variant detection, color palette validation, disclaimer legibility. Findings stored separately from text findings.",
        "<b>Multi-Format &amp; Accessibility Review:</b> HTML email, social post, and document format analysis; reading level estimation; alt-text presence checks; platform character-limit validation.",
        "<b>Brand Governance Intelligence:</b> Per-creator compliance scoring, recurring violation detection, guideline effectiveness signals — all computed from existing DB records, no new schema required.",
    ]
    for item in r3:
        story.append(Paragraph(f"• {item}", bullet_style))

    # ── 8. Known Limitations ──────────────────────────────────────────────────
    story.append(Paragraph("8. Known Limitations", h1_style))
    limits = [
        "<b>In-App Publishing Only:</b> 'Publish' records status in the database; no external CMS, social media, or ad network integration.",
        "<b>Text Content Only:</b> AI compliance analysis is text-only; images, video, and audio are not analyzed.",
        "<b>Scanned PDF / OCR:</b> pypdf extracts embedded text only; scanned image-based PDFs return empty or incomplete extraction.",
        "<b>Demo Login Security:</b> /api/auth/demo-login auto-creates accounts for evaluator convenience; not production-grade.",
        "<b>Render Cold Start:</b> Render free tier may take 30–60 seconds to respond after inactivity.",
    ]
    for lim in limits:
        story.append(Paragraph(f"• {lim}", bullet_style))

    # ── 9. Judge Quickstart ───────────────────────────────────────────────────
    story.append(Paragraph("9. Judge / Evaluator Quickstart", h1_style))
    story.append(Paragraph(
        f"<b>Live Demo:</b> Open <a href='{FRONTEND_URL}' color='#1d4ed8'>{FRONTEND_URL}</a><br/>"
        "Click <b>'Content Creator'</b> or <b>'Brand Manager'</b> in the One-Click Login panel "
        "(auto-creates demo accounts, no manual seeding required).<br/><br/>"
        "<b>Demo Credentials (auto-created on first use):</b><br/>"
        "• Brand Manager: <i>manager@brandguard.ai</i> / <i>Password123!</i><br/>"
        "• Content Creator: <i>creator@brandguard.ai</i> / <i>Password123!</i><br/><br/>"
        "<b>Or seed realistic data</b> (run <i>python seed_demo.py</i> in BACKEND):<br/>"
        "• judge.manager@brandguard.ai / DemoPassword123!<br/>"
        "• judge.creator@brandguard.ai / DemoPassword123!",
        body_style,
    ))

    # ── 10. AI Assistance Disclosure ──────────────────────────────────────────
    story.append(Paragraph("10. Third-Party & AI Assistance Disclosure", h1_style))
    story.append(Paragraph(
        "<b>AI SDK:</b> Official google-genai Python SDK (Apache 2.0). No API keys are committed to the repository.<br/>"
        "<b>Core Libraries:</b> Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, Werkzeug, python-dotenv, "
        "psycopg2-binary, psycopg[binary], pypdf, Gunicorn, React 18, Vite 5, Tailwind CSS, Lucide React, Axios, ReportLab.<br/>"
        "<b>AI Coding Assistance:</b> Google Antigravity IDE (Gemini 2.5) was used as an agentic pair-programmer "
        "for architecture, code generation, test writing, and documentation. All code validated against automated "
        "pytest suites and production build tools.",
        body_style,
    ))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph(
        "BrandGuard AI · Inkloom AI Hackathon Round 2 · 39/39 Tests Passing · Deployed on Vercel + Render",
        callout_style,
    ))

    doc.build(story)
    print(f"[OK] PDF generated: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    build_pdf()
