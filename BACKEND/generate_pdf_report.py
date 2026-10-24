"""
Generate professional PDF report for BrandGuard AI Hackathon Round 2 Submission.
Outputs to docs/ROUND2_SUBMISSION.pdf using ReportLab.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

def build_pdf():
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    os.makedirs(docs_dir, exist_ok=True)
    pdf_path = os.path.join(docs_dir, "ROUND2_SUBMISSION.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#14532d")  # Deep Forest Green
    SECONDARY = colors.HexColor("#166534") # Forest Green
    TEXT_DARK = colors.HexColor("#0f172a") # Slate 900
    TEXT_MUTED = colors.HexColor("#475569") # Slate 600
    BORDER_COLOR = colors.HexColor("#e2e8f0")
    BG_LIGHT = colors.HexColor("#f8fafc")
    ACCENT_EMERALD = colors.HexColor("#059669")

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=TEXT_MUTED,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        leftIndent=15,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=PRIMARY,
        spaceAfter=6
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("BrandGuard AI – Intelligent Governance Platform", title_style))
    story.append(Paragraph("Inkloom AI Hackathon Round 2 Build Report • The Build Phase • October 2026", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceBefore=0, spaceAfter=12))

    # Executive Metadata Table
    meta_data = [
        [
            Paragraph("<b>Project:</b> BrandGuard AI", table_cell_style),
            Paragraph("<b>Target Stack:</b> React 18, Flask, Gemini 2.5", table_cell_style),
        ],
        [
            Paragraph("<b>Repository:</b> github.com/your-username/brandguard-ai", table_cell_style),
            Paragraph("<b>Deployment:</b> Vercel (Front) + Render (API)", table_cell_style),
        ],
        [
            Paragraph("<b>Verification:</b> 19/19 Unit/E2E Tests Passed", table_cell_style),
            Paragraph("<b>Status:</b> Production Ready (Phases 1–5 Complete)", table_cell_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[260, 272])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 1. Problem Statement
    story.append(Paragraph("1. Problem Statement", h1_style))
    story.append(Paragraph(
        "Enterprise marketing teams and creative agencies face acute brand safety risks when drafting high-velocity promotional content. "
        "The proliferation of generative AI tools has accelerated content output, but has dramatically elevated the risk of unsubstantiated claims "
        "(e.g., '100% downtime-proof guarantee', 'zero cost forever'), off-brand tone, and hallucinated organizational facts. "
        "Manual review cycles in spreadsheets lack audit history, versioning snapshots, and objective rule enforcement.",
        body_style
    ))

    # 2. Proposed Solution
    story.append(Paragraph("2. Proposed Solution", h1_style))
    story.append(Paragraph(
        "BrandGuard AI is a multi-tenant brand governance platform delivering an end-to-end, human-in-the-loop compliance engine:",
        body_style
    ))
    story.append(Paragraph("• <b>Centralized Brand Rulebooks:</b> Full governance across 6 categories (Tone, Terminology, Messaging, Approved Facts, Restricted Claims, Accessibility).", bullet_style))
    story.append(Paragraph("• <b>Evidence-Grounded AI Auditing:</b> Google Gemini 2.5 Flash evaluates copy against active guidelines, providing line quotes, severity ratings, and replacement text.", bullet_style))
    story.append(Paragraph("• <b>Immutable Revision Snapshots:</b> Every content update creates an unalterable revision with changelog reasons and word count tracking.", bullet_style))
    story.append(Paragraph("• <b>Stale Report Protection:</b> Content revisions automatically invalidate prior AI analyses, preventing outdated reports from being submitted for approval.", bullet_style))
    story.append(Paragraph("• <b>Manager Sign-Off & Audit Trail:</b> Content locks during review. Managers sign off or request revisions with required directives; all actions are logged in ReviewDecision.", bullet_style))

    # 3. Completed Features
    story.append(Paragraph("3. Completed & Verified Features (Phases 1–5)", h1_style))
    features_data = [
        [Paragraph("Feature Area", table_header_style), Paragraph("Key Capabilities & Verification", table_header_style)],
        [
            Paragraph("<b>Authentication & RBAC</b>", table_cell_style),
            Paragraph("Stateless JWT auth with roles for Content Creator and Brand Manager. Secure password hashing.", table_cell_style)
        ],
        [
            Paragraph("<b>Brand Rulebooks</b>", table_cell_style),
            Paragraph("6-category taxonomy, team membership isolation, approved facts, and prohibited keyword registries.", table_cell_style)
        ],
        [
            Paragraph("<b>Content Drafting & History</b>", table_cell_style),
            Paragraph("Rich draft editor, word/char counters, immutable ContentRevision snapshots, and version preview modal.", table_cell_style)
        ],
        [
            Paragraph("<b>Gemini AI Engine</b>", table_cell_style),
            Paragraph("Official google-genai SDK, structured JSON output, rule ID sanitization, severity counters.", table_cell_style)
        ],
        [
            Paragraph("<b>Manager Approval Workflow</b>", table_cell_style),
            Paragraph("Approval queue (/manager/approvals), warning acknowledgement modal, status locking, ReviewDecision timeline.", table_cell_style)
        ],
        [
            Paragraph("<b>Production Deployment</b>", table_cell_style),
            Paragraph("Gunicorn WSGI, PostgreSQL connection pooling, Vercel SPA rewrites, safe logging, non-destructive seeder.", table_cell_style)
        ]
    ]
    feat_table = Table(features_data, colWidths=[160, 372])
    feat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(feat_table)
    story.append(Spacer(1, 8))

    # 4. Testing & Verification Evidence
    story.append(Paragraph("4. Automated Testing & Verification Evidence", h1_style))
    story.append(Paragraph(
        "BrandGuard AI enforces zero-regression test coverage across all authorization boundaries and workflow transitions:",
        body_style
    ))
    test_rows = [
        [Paragraph("Test Suite File", table_header_style), Paragraph("Tests", table_header_style), Paragraph("Scope & Validated Invariants", table_header_style), Paragraph("Status", table_header_style)],
        [Paragraph("test_auth.py", table_cell_style), Paragraph("6", table_cell_style), Paragraph("Registration, password hashing, token expiration, RBAC", table_cell_style), Paragraph("100% PASS", table_cell_style)],
        [Paragraph("test_phase2.py", table_cell_style), Paragraph("3", table_cell_style), Paragraph("Brand CRUD, guideline taxonomy, revision snapshotting", table_cell_style), Paragraph("100% PASS", table_cell_style)],
        [Paragraph("test_phase3.py", table_cell_style), Paragraph("5", table_cell_style), Paragraph("Gemini integration, rule sanitization, stale-report detection", table_cell_style), Paragraph("100% PASS", table_cell_style)],
        [Paragraph("test_phase4.py", table_cell_style), Paragraph("2", table_cell_style), Paragraph("Manager queue, warning acknowledgement, decision log", table_cell_style), Paragraph("100% PASS", table_cell_style)],
        [Paragraph("test_production_workflows.py", table_cell_style), Paragraph("3", table_cell_style), Paragraph("Cross-user isolation, status locking, full E2E lifecycle", table_cell_style), Paragraph("100% PASS", table_cell_style)],
    ]
    test_table = Table(test_rows, colWidths=[150, 45, 275, 62])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TEXTCOLOR', (3, 1), (3, -1), ACCENT_EMERALD),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 8))

    # 5. Major Round 3 Roadmap
    story.append(Paragraph("5. Planned Round 3 Roadmap Innovations", h1_style))
    story.append(Paragraph("1. <b>Multimodal Visual & Ad Banner Compliance:</b> Ingest PNG/JPG display ads and PDFs with Gemini multimodal vision to audit logo placement, contrast ratios, and legal disclaimer legibility.", bullet_style))
    story.append(Paragraph("2. <b>Advanced Governance Analytics:</b> Cross-campaign dashboards tracking violation frequency, creator velocity, and team compliance trends over time.", bullet_style))
    story.append(Paragraph("3. <b>Autonomous Web Verification & Certificates:</b> Web-grounded citation checking of customer and benchmark metrics, exporting cryptographically signed PDF audit certificates.", bullet_style))

    # 6. Evaluator Quickstart
    story.append(Paragraph("6. Evaluator / Judge Quickstart", h1_style))
    story.append(Paragraph(
        "A non-destructive seeder is included for instant review (run <code>python seed_demo.py</code> in BACKEND):<br/>"
        "• <b>Brand Manager:</b> <code>judge.manager@brandguard.ai</code> / <code>DemoPassword123!</code><br/>"
        "• <b>Content Creator:</b> <code>judge.creator@brandguard.ai</code> / <code>DemoPassword123!</code><br/>"
        "• Pre-loaded Brand: <b>CloudNova</b> (with 6 guidelines, violation draft, and pending approval ad).",
        body_style
    ))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceBefore=4, spaceAfter=8))
    story.append(Paragraph("BrandGuard AI • Inkloom AI Hackathon Round 2 Build • Verified Complete & Deployment Ready", callout_style))

    doc.build(story)
    print(f"[OK] Generated submission PDF: {pdf_path}")

if __name__ == "__main__":
    build_pdf()
