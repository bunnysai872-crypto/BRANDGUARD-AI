# BrandGuard AI — Round 3 Submission
### CodeAxis Hackathon · CloudNova Track · 2026-10-27

---

## Project Overview

**BrandGuard AI** is an enterprise brand governance platform that helps marketing teams ensure every piece of content — text, images, and documents — complies with brand guidelines before publication.

Built on Flask (backend), React + Vite (frontend), Gemini 2.5 Flash AI, and SQLite (dev) / PostgreSQL (production).

---

## Round 3 Improvements

### 1. Visual Brand Compliance Engine
**Problem:** Text compliance passes while images violate brand identity. Manual visual review is slow and inconsistent.

**Solution:** `POST /api/visual-compliance/analyze` accepts PNG/JPG/WEBP images and runs Gemini 2.5 Flash multimodal analysis grounded in each brand's Visual Identity guidelines. Returns categorized findings (Logo, Color, Typography, Layout, Contrast) with severity ratings and correction suggestions.

**Verification:** 16 automated backend tests; frontend file drop zone with score ring display.

---

### 2. Multi-Format & Accessibility Review
**Problem:** Promotional content arrives as PDFs, DOCX briefs, and structured text documents. Pasting into a plain text box loses structural context and accessibility signals.

**Solution:** `POST /api/document-review/analyze` auto-detects TXT/PDF/DOCX formats, extracts text via pypdf/python-docx, and runs a combined brand compliance + accessibility analysis pass. Findings are separately tagged as `Brand Compliance` or `Accessibility`.

**Verification:** 34 automated backend tests; frontend format-specific guidance and dual finding tabs.

---

### 3. Brand Governance Intelligence Dashboard
**Problem:** Submissions are evaluated in isolation. Managers have no visibility into recurring violations, which creators need training, or which guidelines are generating the most flags.

**Solution:** Three coordinated endpoints + a 4-tab React dashboard:

| Endpoint | What It Computes |
|:---|:---|
| `GET /api/analytics/intelligence` | Unified governance overview across all review types |
| `GET /api/analytics/creator-insights` | Per-creator submission counts, approval rates, top violation categories |
| `GET /api/analytics/guideline-effectiveness` | Per-guideline finding counts, violation rates, signal classification |

**Dashboard Tabs:**
- **Overview** — review-type health cards, combined severity bars, timeline, recurring issues
- **Insights** — evidence-backed actionable recommendations, no fabricated statistics
- **Creator Breakdown** (admin) — ranked creator table with compliance rate, findings, and data-reliability warnings
- **Guideline Health** (admin) — guideline effectiveness table with High-Impact / Active / Low-Signal / No-Signal badges

**Verification:** 27 (base) + 38 (new) = 65 backend tests for the intelligence dashboard endpoints.

---

## Test Results

| Metric | Value |
|:---|:---|
| Total backend tests | **154** |
| Passed | **154** |
| Failed | **0** |
| Frontend build | **✅ 0 errors, 0 warnings** |
| Regressions | **0** |

---

## Key Technical Decisions

**1. No double-counting across review types**
Text compliance, visual compliance, and document review each have their own DB tables and are aggregated independently before combining into unified totals. This is enforced in the service layer and verified in tests.

**2. Early validation before any DB lookup**
Filter parameters (`days`, `brand_id`) are validated for format and range before any database query. Invalid strings return 400 immediately; access-denied brand IDs return 403 after access check.

**3. `sufficient_data` flag on creator insights**
Creator patterns are flagged as unreliable below 5 submissions. Every creator row includes `data_note` when insufficient data is present, preventing managers from drawing false conclusions.

**4. `methodology_note` in every response**
Every analytics API response includes a human-readable explanation of how the data was computed and what its limitations are. This is surfaced in the UI on every tab.

**5. Signal classification transparency**
Guideline signals have documented thresholds: High-Impact = cited in ≥50% of analyses, No-Signal = zero findings. The methodology note explains all four signal states including the honest interpretation of No-Signal (may be vague, not relevant, or genuinely well-followed).

---

## What BrandGuard AI Does NOT Claim

- No automated external fact verification against live websites
- No cryptographically signed audit certificates
- No direct integrations with design tools (Canva, Adobe, Figma)
- Creator compliance scores are advisory guidance, not performance evaluations
- Guideline signals require multiple submissions to be statistically meaningful

---

## File Structure

```
BRAND GUARD/
├── BACKEND/
│   ├── app/
│   │   ├── models/
│   │   │   ├── visual_compliance.py
│   │   │   └── document_review.py
│   │   ├── routes/
│   │   │   ├── analytics.py            ← 4 analytics endpoints
│   │   │   ├── visual_compliance.py
│   │   │   └── document_review.py
│   │   └── services/
│   │       ├── analytics_service.py    ← intelligence + creator + guideline methods
│   │       ├── visual_compliance_service.py
│   │       └── document_review_service.py
│   └── tests/
│       ├── test_intelligence_dashboard.py  (27 tests)
│       ├── test_governance_intelligence.py (38 tests, Round 3 new)
│       ├── test_visual_compliance.py       (16 tests)
│       └── test_document_review.py         (34 tests)
├── FRONTEND/
│   └── src/pages/
│       ├── IntelligenceDashboard.jsx   ← 4-tab dashboard
│       ├── VisualCompliancePage.jsx
│       └── DocumentReviewPage.jsx
└── docs/
    ├── ROUND3_PROJECT_REPORT.md
    ├── ROUND3_TEST_REPORT.md
    └── ROUND3_SUBMISSION.md           ← this file
```
