# BrandGuard AI – Inkloom AI Hackathon Round 2 Build Report

**Project Title**: BrandGuard AI – Intelligent Brand Governance & Content Compliance Platform  
**Competition**: Inkloom AI Hackathon Round 2 (The Build)  
**Submission Deadline**: October 25, 2026 – 10:00 AM IST  
**Repository**: [https://github.com/bunnysai872-crypto/BRANDGUARD-AI](https://github.com/bunnysai872-crypto/BRANDGUARD-AI)  
**Live Demo**: [https://brandguard-ai-tau.vercel.app/login](https://brandguard-ai-tau.vercel.app/login)  
**Backend API & Health**: [https://brandguard-ai-fdfl.onrender.com/api/health](https://brandguard-ai-fdfl.onrender.com/api/health)  

---

## 1. Problem Statement

Modern enterprise marketing teams, creative agencies, and growth copywriters produce thousands of promotional assets across multiple digital channels each month. With the widespread adoption of generative AI tools, the velocity of content generation has increased tenfold, introducing critical business risks:

1. **Unsubstantiated & Prohibited Claims**: Unvetted claims regarding uptime, security guarantees, performance metrics, and pricing (e.g., *"100% downtime-proof"*, *"zero transaction fees forever"*) create significant legal exposure, customer churn, and regulatory scrutiny (FTC, ASA, SEC guidelines).
2. **Off-Brand Voice & Hallucinated Facts**: Generative models frequently hallucinate organizational statistics, cite outdated product capabilities, or adopt informal, off-brand tones that dilute brand equity.
3. **Fragmented, Manual Review Cycles**: Brand Governance Leads spend hundreds of hours manually copy-editing drafts in spreadsheets and messaging channels. Existing workflows lack versioning snapshots, audit history, and structured rule citations.

Organizations urgently require an **automated, evidence-linked compliance verification platform** that integrates into creator workflows, checks text against active brand rulebooks, and enforces human-in-the-loop managerial sign-offs.

---

## 2. Proposed Solution

**BrandGuard AI** is an intelligent, multi-tenant brand governance platform that combines **centralized organization rulebooks**, **Google Gemini AI automated compliance analysis**, and an **immutable decision governance workflow**:

- **Centralized Brand Rulebooks**: Brand Managers define and curate organizational brand guidelines across 6 distinct categories (Tone, Terminology, Messaging, Approved Facts, Restricted Claims, Accessibility).
- **Evidence-Grounded AI Auditing**: Copywriters evaluate drafts using Google Gemini (via the official `google-genai` Python SDK). Gemini evaluates copy strictly against active brand guidelines, highlighting violating excerpts, citing the exact breached guideline, and providing actionable rewrite suggestions.
- **Revision Snapshotting & Stale Report Invalidation**: Every draft update creates an immutable revision record in `ContentRevision`. Any copy modification automatically flags existing AI reports as outdated (`is_outdated = True`), preventing outdated audits from being used for approval.
- **Human-in-the-Loop Governance & Audit Trail**: Content cannot be published without formal managerial sign-off. High-severity violations require explicit exception acknowledgements, and all review actions are permanently logged in `ReviewDecision`.

---

## 3. Completed Features (Phases 1–5 Built & Verified)

### Phase 1 — Authentication, RBAC & Core Application Architecture
- **Flask Application Factory**: Modular blueprint architecture (`auth`, `health`, `brands`, `guidelines`, `submissions`).
- **Stateless JWT Authentication**: Secure password hashing with PBKDF2/SHA-256 and 7-day JWT expiration tokens.
- **Role-Based Access Control (RBAC)**: Distinct permissions for `admin` (Brand Manager) and `creator` (Content Creator).
- **Modern React + Vite Frontend**: Responsive layout built with Tailwind CSS using a curated deep forest green palette (`#14532d` / `#166534`), accessible typography, and Lucide React icons.

### Phase 2 — Brand Guidelines Management & Content Persistence
- **Brand Profiles**: Managers create and configure organizational brand entities with industry, website, tone overview, and prohibited keywords.
- **Team Membership Assignment**: Managers assign creators to specific brand teams; cross-brand data isolation is strictly enforced.
- **6-Category Rulebook Taxonomy**: Full CRUD for guidelines across *Tone*, *Terminology*, *Messaging*, *Approved Facts*, *Restricted Claims*, and *Accessibility*.
- **Content Drafting & Revision History**: Creators draft copy with live word/char counters. Every edit snapshots an immutable record into `ContentRevision` with timestamp and changelog reason.

### Phase 3 — Gemini AI Compliance Checking Engine
- **Official Google GenAI SDK Integration**: Utilizes `google-genai` with model `gemini-2.5-flash`, JSON output mode (`response_mime_type="application/json"`), and temperature 0.1 for deterministic structured output.
- **Structured Schema & Evidence Linking**: Returns JSON findings including flagged excerpt, severity (*Critical*, *High*, *Medium*, *Low*), violated guideline ID (DB-validated), explanation, confidence level, human-verification flag, and suggested replacement copy.
- **Hallucinated Guideline Sanitization**: Validates all AI-returned rule IDs against the brand's database IDs, sanitizing fabricated citations.
- **Stale Report Invalidation**: Detects when copy has been revised after an audit and blocks submission until re-analysis.

### Phase 4 — Manager Review Queue & Decision Governance
- **Creator Approval Submission**: Escalates compliant copy to manager queue with mandatory High-Severity Warning Acknowledgement modal.
- **Manager Approval Queue**: Dedicated `/manager/approvals` queue for Brand Managers with search, brand filtering, status filtering, and live counters.
- **Decision Controls**: Managers review copy side-by-side with AI findings to **Approve Content** or **Request Changes** with mandatory review directives.
- **Status Locking**: `Pending Manager Approval` and `Approved` submissions are permanently locked against unauthorized modifications.
- **Auto-Reset Workflow**: Revising a `Changes Requested` submission auto-resets status to `Draft` and marks reports outdated for re-audit.
- **Immutable Decision History**: Full chronological timeline of review decisions logged in `ReviewDecision`.

### Phase 5 — Publishing, Analytics & Production Readiness
- **In-App Publishing Workflow**: Brand Managers publish `Approved` content via `POST /api/submissions/:id/publish`; sets `published_at`, `published_by_id`; permanently locks the submission against further edits.
- **Governance Analytics Dashboard**: Real-time DB-computed metrics: submission counts by status, severity distribution, violation category distribution, common flagged phrases, reviewer outcome ratios, and submission timeline trends.
- **PostgreSQL Connection Pooling**: Configured SQLAlchemy with auto-reconnection and connection recycling for hosted PostgreSQL.
- **Production Security**: Strict CORS headers, environment secret validation, safe logging, hardened health check (`/api/health`).
- **Gunicorn WSGI**: Production-grade WSGI with multi-worker configuration.
- **Vercel API Proxy**: `vercel.json` configured with `/api/:path*` → Render proxy rewrite before the SPA catch-all, eliminating 405 errors on POST requests.
- **Idempotent Demo Login**: `/api/auth/demo-login` endpoint auto-creates demo accounts and issues JWT — one-click evaluator access without manual seeding.
- **Automated Seeding**: `seed_demo.py` creates the CloudNova brand, 6 guidelines, and pre-loaded submissions.

---

## 4. Technologies & Implementation Details

| Layer | Component | Implementation Specification |
| :--- | :--- | :--- |
| **Frontend** | Single Page Application | React 18, Vite 5, Tailwind CSS, Lucide React, Axios |
| **Frontend Routing** | Client-side Router | React Router DOM 6 with role-based `ProtectedRoute` wrappers |
| **Backend** | REST API Server | Python 3.12, Flask 3.0 Application Factory |
| **WSGI Server** | Production Web Server | Gunicorn 21.2 (multi-worker, multi-thread) |
| **Database ORM** | Object-Relational Mapper | Flask-SQLAlchemy 3.1, declarative relational schemas |
| **Databases** | Relational Storage | SQLite (Local Dev) / PostgreSQL (Production – Render) |
| **Authentication** | Token-based Auth | Flask-JWT-Extended 4.6 (HMAC-SHA256, 7-day TTL) |
| **AI Integration** | GenAI Python SDK | `google-genai>=1.0.0`, Gemini 2.5 Flash, JSON output mode |
| **PDF Parsing** | Text Extraction | `pypdf>=4.0.0` (embedded-text PDFs; not OCR-capable) |
| **Testing** | Automated Test Runner | Pytest 9.1 with in-memory SQLite fixtures |

---

## 5. Architecture & Workflow Diagram

```text
[ Content Creator ]                              [ Google Gemini 2.5 Flash ]
       │                                                      ▲
       │ 1. Draft Promotional Copy                            │
       ▼                                                      │
[ ContentSubmission ] ───► Creates Revision #1 Snapshot       │
       │                                                      │
       │ 2. Request AI Compliance Check                       │
       └──────────────────────────────────────────────────────┘
       │    (Evaluates copy against active brand guidelines)
       ▼
[ ComplianceAnalysis ] ──► Stores Structured Findings, Severity & Corrections
       │
       │ 3. Submit for Manager Approval (Warning modal if High severity)
       ▼
[ Status: Pending Manager Approval ] (Content editing locked)
       │
       │ 4. Visible in Manager Queue (/manager/approvals)
       ▼
[ Brand Manager ]
       │
       ├────────────────────────────────────────┬───────────────────────────────────────┐
       ▼                                        ▼                                       ▼
 [ Action: Approve Content ]       [ Action: Request Changes ]            [ ReviewDecision Log ]
       │                                        │                                       ▲
       ▼                                        ▼                                       │
 [ Status: Approved ]            [ Status: Changes Requested ]                          │
 (Permanently locked)            (Creator revises copy; creates                         │
                                  Revision #2, auto-resets to Draft,                     │
                                  prior analysis marked outdated) ──────────────────────┘
```

---

## 6. Key Changes & Evolution from Round 1

In Round 1, BrandGuard AI was conceived as a conceptual architecture with preliminary design tokens. In Round 2 (The Build), the platform was implemented into an enterprise-grade full-stack system:

1. **Complete Database-Backed Persistence**: Replaced conceptual mockups with a relational SQLAlchemy schema (10 tables) supporting Users, Brands, Brand Memberships, Guidelines, Submissions, Revision Snapshots, Compliance Analyses, Findings, and Review Decisions.
2. **Official Google GenAI SDK Migration**: Integrated the modern `google-genai` SDK using `gemini-2.5-flash` with JSON output mode, severity counters, confidence levels, and citation sanitization.
3. **Immutable Revision History**: Built a changelog snapshot engine where every edit creates an unalterable revision with reason, word count, and timestamp.
4. **Stale-Report Protection System**: Implemented automated detection that prevents approving or escalating submissions whose content changed after the latest AI analysis.
5. **Bidirectional Review Lifecycle**: Built the Manager Approval Queue, Exception Acknowledgement modals, and immutable decision history timeline.
6. **Publishing Workflow**: Implemented `POST /api/submissions/:id/publish`; only Brand Managers can publish Approved content; `published_at` and `published_by_id` are persisted.
7. **Governance Analytics**: Real-time DB-computed analytics dashboard (submission metrics, severity distribution, common issues, timeline trends).
8. **Production Deployment**: Deployed frontend to Vercel (https://brandguard-ai-tau.vercel.app) and backend to Render (https://brandguard-ai-fdfl.onrender.com). Fixed 405 errors via Vercel API proxy rewrite.

---

## 7. Real Testing & Verification Evidence

All 39 automated integration and unit tests pass:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.9, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Documents\BRAND GUARD\BACKEND
collected 39 items

tests/test_auth.py (11 tests)                    PASSED  [ 28%]
tests/test_hackathon_upgrades.py (9 tests)        PASSED  [ 51%]
tests/test_phase2.py (3 tests)                    PASSED  [ 58%]
tests/test_phase3.py (5 tests)                    PASSED  [ 71%]
tests/test_phase4.py (2 tests)                    PASSED  [ 76%]
tests/test_production_workflows.py (3 tests)      PASSED  [ 84%]
tests/test_publishing.py (6 tests)                PASSED [ 100%]

============================= 39 passed in 21.72s =============================
```

Frontend production build (`npm run build`) succeeds cleanly with zero errors:
```text
vite v5.4.21 building for production...
1642 modules transformed.
dist/assets/index-*.css   35.59 kB | gzip: 6.46 kB
dist/assets/index-*.js   411.99 kB | gzip: 106.81 kB
built in 5.94s — 0 errors, 0 warnings
```

---

## 8. Major Round 3 Improvements Roadmap

Building upon Round 2, the following three major enterprise capabilities are scheduled for Round 3:

### 1. Multimodal Visual, Banner & Document Compliance Checking
- Ingest image creatives (PNG, JPG, SVG banners) and PDF marketing collaterals using Gemini multimodal visual understanding.
- Validate logo placement, brand color contrast ratios (WCAG compliance), font family adherence, and mandatory legal disclaimer visibility on digital display ads.

### 2. Advanced Governance Analytics & Brand Health Trends
- Cross-brand compliance dashboards showing violation frequency by category over time.
- Creator velocity metrics, identifying common training gaps (e.g., frequent restricted claims or terminology confusion).
- Exportable CSV/Excel governance summaries for Chief Marketing Officers (CMOs) and legal teams.

### 3. Automated External Evidence Verification & Signed Audit Reports
- Autonomous web-grounded verification of customer numbers, industry ranking claims, and benchmark citations against external trusted sources.
- One-click generation of cryptographically signed, downloadable PDF Compliance Certificates for publication sign-off.

---

## 9. Deployment URLs

| Service | Environment | URL |
| :--- | :--- | :--- |
| **Frontend Application** | Production (Vercel) | https://brandguard-ai-tau.vercel.app |
| **Login Page** | Production | https://brandguard-ai-tau.vercel.app/login |
| **Backend REST API** | Production (Render) | https://brandguard-ai-fdfl.onrender.com |
| **API Health Check** | Production | https://brandguard-ai-fdfl.onrender.com/api/health |
| **Local Development** | Localhost | Frontend: `http://localhost:5173` · Backend: `http://localhost:5000` |

---

## 10. Source Code & Repository Structure

- **Repository**: https://github.com/bunnysai872-crypto/BRANDGUARD-AI
- **Structure**:
  - `BACKEND/`: Flask application, models, routes, services, pytest test suites, `seed_demo.py`, `generate_pdf_report.py`.
  - `FRONTEND/`: React 18, Vite, Tailwind CSS, components, pages, context, `vercel.json` (with API proxy).
  - `docs/`: `ROUND2_SUBMISSION.md`, `ROUND2_SUBMISSION.pdf`, `ROUND2_PROJECT_REPORT.md`, `ROUND2_DEMO_GUIDE.md`, `ROUND2_TEST_REPORT.md`, `ROUND3_ROADMAP.md`, `DEPLOYMENT_GUIDE.md`.

---

## 11. Third-Party Dependencies & AI Assistance Disclosure

- **AI SDK**: Official `google-genai` Python SDK (Apache 2.0 License). No API keys committed to repository.
- **Core Libraries**: Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, Werkzeug, python-dotenv, psycopg2-binary, psycopg[binary], pypdf, Gunicorn, React, Vite, Tailwind CSS, Lucide React, Axios, ReportLab.
- **AI Coding Assistance**: Google Antigravity IDE (Gemini 2.5) was utilized as an agentic pair-programmer for architectural design, code refactoring, automated test generation, and documentation drafting. All code was audited and validated against automated pytest suites and production build tools.
