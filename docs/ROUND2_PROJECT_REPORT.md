# BrandGuard AI — Round 2 Project Report
### Inkloom AI Hackathon · The Build Phase

**Project:** CloudNova BrandGuard AI — Intelligent Brand Governance & Content Compliance Platform  
**Round:** 2 (The Build)  
**Deadline:** 2026-10-25 10:00 AM IST  
**Team:** Solo submission  
**Report Date:** 2026-10-24  

---

## 1. Problem Statement

Modern enterprise marketing teams, creative agencies, and freelance copywriters produce thousands of promotional assets every month. The widespread adoption of generative AI tools has accelerated content velocity, while simultaneously increasing the risk of:

1. **Unsubstantiated & Prohibited Claims** — Unauthorized uptime guarantees ("100% downtime-proof"), impossible pricing claims ("zero cost forever"), and unverified performance statistics create significant legal liability under FTC, ASA, and SEC advertising standards.
2. **Off-Brand Voice & Hallucinated Facts** — Large language models frequently hallucinate organizational statistics, cite outdated product capabilities, or adopt informal tones that dilute hard-earned brand equity.
3. **Fragmented, Manual Review Cycles** — Brand governance leads spend hundreds of hours manually copy-editing drafts distributed across spreadsheets, email chains, and messaging platforms — without versioning snapshots, structured rule citations, or audit history.

**The Business Need:** Organizations urgently need an automated, evidence-linked compliance verification platform that integrates into creator workflows, evaluates copy against active brand rulebooks, and enforces human-in-the-loop managerial sign-offs before publication.

---

## 2. Target Users

| Role | Description | Primary Pain Point |
|:---|:---|:---|
| **Brand Manager (admin)** | Senior marketeer or legal/brand lead responsible for defining and enforcing brand governance rules | Spending hours manually reviewing copy for regulatory compliance and brand consistency |
| **Content Creator (creator)** | Copywriter, growth marketer, or agency freelancer producing promotional material | Uncertainty about which claims are approved; slow, opaque feedback cycles from reviewers |

---

## 3. Proposed Solution

**BrandGuard AI** is a multi-tenant brand governance platform with three core pillars:

1. **Centralized Brand Rulebooks** — Brand Managers define organizational guidelines across 10 categories (Tone, Terminology, Messaging, Approved Facts, Restricted Claims, Prohibited Claims, Mandatory Disclaimer, Visual Identity, Accessibility, Other), with severity levels (Critical / High / Medium / Low), approved wording, and prohibited wording.
2. **Evidence-Grounded AI Auditing** — Content Creators submit promotional drafts for analysis by Google Gemini 2.5 Flash. The model evaluates copy strictly against the brand's active guidelines, returning structured JSON findings with: quoted problematic text, violated guideline reference (with DB ID validation), severity level, detailed explanation, suggested compliant rewrite, confidence level, and human-verification flags.
3. **Human-in-the-Loop Governance** — No content can be published without formal Brand Manager sign-off. High/critical violations require explicit creator acknowledgement before submission and manager acknowledgement before approval. Every review action is permanently recorded in `ReviewDecision` with reviewer identity, timestamp, and revision number.

---

## 4. Architecture

### Backend
- **Framework:** Python 3.12 + Flask 3.0 Application Factory pattern
- **Database ORM:** Flask-SQLAlchemy 3.1 with declarative relational models
- **Database:** SQLite (local development), PostgreSQL (production via `DATABASE_URL`)
- **Authentication:** Flask-JWT-Extended 4.6 — stateless HMAC-SHA256 JWT tokens, 7-day expiry, role claims embedded in token payload
- **AI Integration:** Official `google-genai` Python SDK (≥1.0.0), model `gemini-2.5-flash`, JSON output mode (`response_mime_type="application/json"`), temperature 0.1 for deterministic output
- **Production WSGI:** Gunicorn 21.2 with multi-worker configuration

### Frontend
- **Framework:** React 18 Single Page Application built with Vite 5
- **Styling:** Tailwind CSS with a curated deep forest green palette
- **Routing:** React Router DOM 6 with role-based `ProtectedRoute` wrappers
- **HTTP Client:** Axios with automatic JWT Bearer header injection and 401 auto-logout

### Database Schema (10 tables)
```
users                  — id, username, email, password_hash, role, full_name
brands                 — id, name, description, tone_style, approved_terminology,
                         approved_facts, restricted_words, prohibited_claims
brand_memberships      — id, brand_id, user_id, role
brand_guidelines       — id, brand_id, category, title, rule_content,
                         approved_wording, prohibited_wording, severity, is_active
content_submissions    — id, creator_id, brand_id, title, content_text, status,
                         published_at, published_by_id
content_revisions      — id, submission_id, revision_number, title, content_text,
                         reason, created_by_id
compliance_analyses    — id, submission_id, revision_number, model_identifier,
                         summary, review_status, issues_count,
                         critical/high/medium/low_severity_count, is_outdated
compliance_findings    — id, analysis_id, category, severity, problematic_text,
                         explanation, guideline_id, suggested_correction,
                         confidence_level, human_verification_required
review_decisions       — id, submission_id, reviewer_id, decision, review_comments,
                         revision_number, analysis_id
```

### Frontend Application Routes
```
/login                          Public login page (one-click demo buttons)
/register                       Self-registration
/creator-dashboard              Creator home: metrics, recent submissions
/creator/submissions            My Submissions list
/creator/submissions/new        New submission editor
/submissions/:id                Submission detail: AI findings, revisions, decisions
/manager-dashboard              Manager home: pending count, brand overview
/manager/brands                 Brand profile management
/manager/guidelines             Brand guideline CRUD with severity, active toggle
/manager/approvals              Manager approval queue
/published-content              In-app published content archive
/analytics                      Governance analytics dashboard
```

---

## 5. Technologies

| Layer | Component | Version / Specification |
|:---|:---|:---|
| Frontend | React SPA | React 18, Vite 5.4, Tailwind CSS, React Router 6, Axios, Lucide React |
| Backend | REST API | Python 3.12, Flask 3.0, Application Factory, Blueprint modules |
| WSGI | Production Server | Gunicorn 21.2 |
| Database | ORM + Storage | Flask-SQLAlchemy 3.1, SQLite (dev), PostgreSQL (prod) |
| Authentication | JWT | Flask-JWT-Extended 4.6, HMAC-SHA256, Werkzeug PBKDF2 password hashing |
| AI Integration | GenAI SDK | google-genai ≥1.0.0, Gemini 2.5 Flash, JSON output mode |
| PDF Extraction | Text parsing | pypdf ≥4.0.0 |
| Testing | Test runner | pytest 9.1 with in-memory SQLite test fixtures |

---

## 6. Completed Features

### Phase 1 — Authentication & RBAC
- Flask Application Factory with modular Blueprint architecture
- PBKDF2/SHA-256 password hashing via Werkzeug
- Stateless JWT with role claims (`admin`, `creator`) embedded in token payload
- Role-based `ProtectedRoute` wrappers in React
- Idempotent `/api/auth/demo-login` endpoint for one-click evaluator access

### Phase 2 — Brand Governance & Content Management
- Brand profile CRUD with tone, approved facts, prohibited claims, and restricted words
- Brand membership assignment with cross-brand data isolation enforced at service layer
- 10-category brand guideline taxonomy with severity levels, approved/prohibited wording, active/inactive toggling, and file-based text extraction
- Content submission creation with immutable `ContentRevision` snapshots on every edit

### Phase 3 — Gemini AI Compliance Engine
- Structured system prompt grounded in brand's active guidelines, approved facts, and restricted words
- JSON output mode with `temperature=0.1` for deterministic, parseable responses
- Validated findings: severity (Critical/High/Medium/Low), violated guideline ID (DB-validated to prevent hallucination), suggested correction, confidence level, human-verification flag
- Stale report detection: `is_outdated` flag set when content is edited post-analysis
- Error handling for missing API key, invalid key, rate limits, quota exhaustion, and malformed JSON

### Phase 4 — Manager Review Workflow
- Creator submission gate: AI analysis required before escalation; stale reports blocked
- High/critical-severity acknowledgement modal: creator must explicitly confirm before escalating
- Manager approval queue with brand/status filters and live pending counters
- Manager review: `Approved` or `Changes Requested` with mandatory comments (min 3 chars)
- Manager acknowledgement required for approving content with high/critical findings
- Status lifecycle: Draft → AI Reviewed → Pending Manager Approval → Approved/Changes Requested
- Immutable `ReviewDecision` log with reviewer identity, timestamp, revision number

### Phase 5 — Publishing & Analytics
- Publish endpoint: Brand Manager only, Approved submissions only; sets `published_at` and `published_by_id`; permanently locked post-publication
- Published Content archive UI showing all published submissions with metadata
- Governance Analytics dashboard: submission counts by status, revision frequency, finding category distribution, severity distribution, common issues, review outcomes, timeline trends — all computed from live database records

---

## 7. Test Evidence

**Test command run (2026-10-24):**
```bash
cd BACKEND && venv\Scripts\python.exe -m pytest tests/ -v
```

**Result: 39 passed, 0 failed, 0 errors in 21.72s**

| Test File | Tests | Scope |
|:---|:---|:---|
| `test_auth.py` | 11 | Registration, login, JWT, role protection, demo-login idempotency |
| `test_hackathon_upgrades.py` | 9 | Guideline new fields, cross-brand isolation, PDF text extraction, AI grounding, analytics, publish security |
| `test_phase2.py` | 3 | Brand management, guideline CRUD, revision history |
| `test_phase3.py` | 5 | Missing API key, mocked Gemini analysis, hallucinated ID sanitization, stale detection, malformed JSON |
| `test_phase4.py` | 2 | Approval validation rules, manager review lifecycle |
| `test_production_workflows.py` | 3 | Health check safety, cross-user isolation, end-to-end governance lifecycle |
| `test_publishing.py` | 6 | Manager-only publishing, creator blocked, non-Approved blocked, double-publish blocked, cross-brand isolation, edit lock |

**Frontend production build (2026-10-24):**
```
vite v5.4.21 — 1642 modules transformed — built in 5.94s — 0 errors, 0 warnings
```

---

## 8. Changes from Round 1

> Note: The Round 1 submission in this repository (`docs/ROUND2_SUBMISSION.md` Section 6) describes the conceptual architecture planned in Round 1. The following summarizes what was actually built in Round 2 vs. what was proposed.

| Area | Round 1 (Proposed) | Round 2 (Implemented) |
|:---|:---|:---|
| **Database** | Conceptual schema described | Full relational schema: 10 tables, cascading deletes, indexed foreign keys |
| **AI Integration** | Gemini API integration planned | `google-genai` SDK integrated with JSON output mode, structured prompting, severity scoring, guideline ID validation, stale detection |
| **Revision History** | Mentioned | Fully implemented: every edit snapshots an immutable `ContentRevision` with reason, word count reference, and timestamp |
| **Stale Report System** | Not in Round 1 plan | Implemented: `is_outdated` flag, blocking approval of stale reports |
| **Governance Workflow** | Manager approval described | Full lifecycle: Draft→AI Reviewed→Pending→Approved/Changes Requested→Published with acknowledgement gates |
| **Publishing** | Not in Round 1 plan | Implemented: `POST /api/submissions/:id/publish`, `published_at`, `published_by_id`, in-app archive |
| **Analytics** | Not in Round 1 plan | Implemented: real-time DB-computed metrics, category/severity distributions, common issues, timeline trends |
| **Guideline Severity** | Not in Round 1 plan | Implemented: Critical/High/Medium/Low severity per guideline, counts per analysis |
| **Demo Login** | Not in Round 1 plan | Implemented: idempotent `/api/auth/demo-login` endpoint |
| **Test Coverage** | Not in Round 1 plan | 39 automated integration tests across 7 test files |

---

## 9. Limitations

| Limitation | Description |
|:---|:---|
| **In-App Publishing Only** | "Publish" marks content as Published within the platform. No external social media, CMS, or ad network integration. |
| **Text Content Only** | AI analysis is text-only. Images, PDFs with embedded images, audio, video, and rich HTML are not analyzed by the AI. |
| **Scanned PDF / OCR** | `pypdf` extracts embedded text only. Scanned PDFs (image-based pages) return empty or incomplete text. |
| **Demo Login** | `/api/auth/demo-login` creates demo accounts automatically for evaluator convenience. Not production-grade; should be restricted or removed before real deployment. |
| **Gemini Rate Limits** | Free-tier Gemini API may throttle under heavy concurrent use. Backend returns a descriptive 429 response. |
| **Single-Instance AI** | Each compliance check is a synchronous Gemini API call. No queuing or background processing for high-volume scenarios. |
| **No Email Notifications** | Status changes do not trigger email or webhook notifications; creators must poll the UI. |

---

## 10. Future Scope (Round 3)

See `docs/ROUND3_ROADMAP.md` for three detailed improvement proposals:

1. **Visual Brand Compliance Engine** — multimodal image analysis of creative assets against logo, color, and typography rules
2. **Multi-Format & Accessibility Review** — HTML email, social post, and document format analysis; WCAG accessibility evaluation
3. **Brand Governance Intelligence** — recurring violation detection, creator pattern analysis, guideline quality feedback

---

## 11. Third-Party Dependencies & AI Assistance Disclosure

**AI SDK:** Official `google-genai` Python SDK (Apache 2.0 License). The Gemini API key must be provided by the operator. No keys are committed to the repository.

**Core Libraries:** Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, Werkzeug, python-dotenv, gunicorn, psycopg2-binary, pypdf, google-genai, React, Vite, Tailwind CSS, React Router DOM, Axios, Lucide React, pytest.

**AI Coding Assistance:** Google Antigravity IDE (Gemini 2.5) was used as an agentic pair programmer for architectural design, code generation, automated test writing, and documentation drafting. All generated code was reviewed and validated against automated pytest suites, production build tools, and manual functional testing.

**No secrets, API keys, passwords, or user data are included in this report or the repository.**
