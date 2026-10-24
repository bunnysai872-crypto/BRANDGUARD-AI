# CloudNova BrandGuard AI
### Intelligent Brand Governance & Content Compliance Platform

> **Inkloom AI Hackathon — Round 2 (The Build)**  
> Full-stack AI-powered platform combining centralized brand rulebooks, Google Gemini compliance analysis, and a human-in-the-loop manager approval workflow.

---

## Problem Statement

Modern enterprise marketing teams produce hundreds of promotional assets per month. Generative AI tools accelerate content velocity but introduce critical risks:

1. **Unsubstantiated & Prohibited Claims** — Unauthorized uptime guarantees, pricing promises, and regulatory violations create legal liability.
2. **Off-Brand Voice & Hallucinated Facts** — LLMs hallucinate statistics, cite outdated metrics, and adopt informal tones that dilute brand equity.
3. **Fragmented Manual Reviews** — Brand managers copy-edit in spreadsheets and chat threads with no audit trail or revision snapshots.

BrandGuard AI solves this by combining **centralized organization rulebooks**, **Google Gemini AI compliance analysis**, and an **immutable human-in-the-loop governance workflow**.

---

## Technology Stack

| Layer | Technology | Notes |
|:---|:---|:---|
| Frontend | React 18 + Vite 5 | SPA with role-based protected routes |
| Styling | Tailwind CSS | Deep forest green palette (#14532d / #166534) |
| Routing | React Router DOM 6 | `/creator/*`, `/manager/*`, `/submissions/:id` |
| Icons | Lucide React | Severity badges, status indicators |
| Backend | Python 3.12 + Flask 3.0 | Application factory, modular blueprints |
| ORM | Flask-SQLAlchemy 3.1 | Declarative models with cascading |
| Database | SQLite (dev) / PostgreSQL (prod) | Zero-config local development |
| Auth | Flask-JWT-Extended 4.6 | Stateless JWT, 7-day expiry, role claims |
| CORS | Flask-CORS 4.0 | Environment-configurable allowed origins |
| AI Engine | google-genai >= 1.0.0 | Gemini 2.5 Flash, JSON output mode |
| WSGI | Gunicorn 21.2 | Production multi-worker server |
| PDF Parsing | pypdf >= 4.0.0 | Text extraction from uploaded PDFs |
| Testing | pytest 9.1 | In-memory SQLite fixtures, 39 tests |

---

## Architecture

```
[ Content Creator ]          [ Brand Manager ]
        |                           |
        v                           v
+-----------------------------------------------+
|          React 18 SPA (Vite, Tailwind)         |
|  /creator-dashboard   /manager-dashboard        |
|  /creator/submissions  /manager/approvals       |
|  /submissions/:id      /manager/brands          |
|  /manager/guidelines   /published-content       |
|  /analytics                                     |
+--------------------+--------------------------+
                     | Bearer JWT (HTTPS)
+--------------------v--------------------------+
|          Flask REST API (Gunicorn)             |
|  /api/auth/*      /api/brands/*                |
|  /api/guidelines/*  /api/submissions/*         |
|  /api/analytics     /api/health                |
+----+----------+-----------+-----------------+
     |          |           |                 |
  AuthSvc  BrandSvc  ComplianceSvc      ReviewSvc
     |          |           |                 |
+----v----------v-----------v-----------------v--+
|            SQLite / PostgreSQL                  |
|  users  brands  brand_memberships               |
|  brand_guidelines  content_submissions          |
|  content_revisions  compliance_analyses         |
|  compliance_findings  review_decisions          |
+-------------------------------------------------+
                     |
          +----------v----------+
          | Google Gemini 2.5   |
          | Flash (google-genai)|
          | JSON output mode    |
          | Temperature 0.1     |
          +---------------------+
```

### Complete Governance Workflow

1. **Brand Manager** configures brand profile + guidelines (tone, terminology, prohibited claims, approved facts)
2. **Content Creator** drafts promotional copy. Every save snapshots an immutable `ContentRevision`
3. **AI Compliance Check** — Gemini evaluates copy against active guidelines and returns structured findings with severity, guideline citations, and suggested corrections
4. **Stale Report Protection** — if copy is edited after an audit, prior report is flagged `is_outdated=True` and must be re-run before submission
5. **Submit for Approval** — if high/critical findings exist, creator must explicitly acknowledge before escalating
6. **Manager Review Queue** — manager sees pending submissions with AI findings attached; records `Approved` or `Changes Requested` with mandatory comments
7. **Publishing** — only Brand Managers can publish `Approved` content; sets `published_at` and `published_by_id`
8. **Audit Trail** — every decision, revision, and analysis permanently persisted in the database

---

## Quickstart

### Prerequisites
- Python 3.10+ (tested on 3.12)
- Node.js 18+ and npm 9+
- Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 1. Clone
```bash
git clone <your-repository-url>
cd "BRAND GUARD"
```

### 2. Backend Setup
```powershell
cd BACKEND
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit BACKEND/.env and set your GEMINI_API_KEY
python run.py
```
Backend runs at `http://localhost:5000`. Health check: `http://localhost:5000/api/health`

### 3. Frontend Setup
```powershell
cd FRONTEND
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

### 4. (Optional) Seed Demo Data
```powershell
cd BACKEND
python seed_demo.py
```
Creates the CloudNova brand with 6 guidelines and two ready-to-test submissions.

**Seeded judge accounts:**

| Role | Email | Password |
|:---|:---|:---|
| Brand Manager | `judge.manager@brandguard.ai` | `DemoPassword123!` |
| Content Creator | `judge.creator@brandguard.ai` | `DemoPassword123!` |

**One-click demo accounts** (auto-created on first use from the Login page):

| Role | Email | Password |
|:---|:---|:---|
| Brand Manager | `manager@brandguard.ai` | `Password123!` |
| Content Creator | `creator@brandguard.ai` | `Password123!` |

---

## Environment Variables

### Backend (`BACKEND/.env`)

| Variable | Description | Default |
|:---|:---|:---|
| `FLASK_ENV` | `development` / `production` / `testing` | `development` |
| `PORT` | HTTP port | `5000` |
| `SECRET_KEY` | Flask session secret (32+ chars in production) | dev value |
| `JWT_SECRET_KEY` | JWT signing secret | dev value |
| `DATABASE_URL` | SQLAlchemy URI | `sqlite:///brandguard.db` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins or `*` | `*` |
| `GEMINI_API_KEY` | Google Gemini API key | *(required for AI checks)* |
| `GEMINI_MODEL` | Model identifier | `gemini-2.5-flash` |

### Frontend (`FRONTEND/.env`)

| Variable | Description | Default |
|:---|:---|:---|
| `VITE_API_BASE_URL` | Backend base URL | `/api` (proxied to port 5000) |

---

## REST API Reference

| Method | Endpoint | Auth | Role | Description |
|:---|:---|:---|:---|:---|
| `GET` | `/api/health` | None | Public | Health status + DB connectivity |
| `POST` | `/api/auth/register` | None | Public | Create account (admin or creator) |
| `POST` | `/api/auth/login` | None | Public | Authenticate + return JWT |
| `POST` | `/api/auth/demo-login` | None | Public | One-click demo login (idempotent) |
| `GET` | `/api/auth/me` | JWT | Any | Current user profile |
| `GET` | `/api/brands` | JWT | Any | List accessible brands |
| `POST` | `/api/brands` | JWT | admin | Create brand profile |
| `GET` | `/api/brands/:id` | JWT | Member | Brand details + guideline count |
| `POST` | `/api/brands/:id/members` | JWT | admin | Assign creator to brand |
| `GET` | `/api/guidelines?brand_id=X` | JWT | Member | List guidelines |
| `POST` | `/api/guidelines` | JWT | admin | Create guideline rule |
| `PUT` | `/api/guidelines/:id` | JWT | admin | Update guideline |
| `DELETE` | `/api/guidelines/:id` | JWT | admin | Delete guideline |
| `POST` | `/api/guidelines/:id/toggle-active` | JWT | admin | Toggle guideline active state |
| `POST` | `/api/guidelines/extract-text` | JWT | admin | Extract text from .txt/.pdf upload |
| `GET` | `/api/submissions` | JWT | Any | List submissions (role-filtered) |
| `POST` | `/api/submissions` | JWT | Any | Create draft submission |
| `GET` | `/api/submissions/:id` | JWT | Member | Submission + revisions + decisions |
| `PUT` | `/api/submissions/:id` | JWT | creator | Revise copy (snapshots new revision) |
| `POST` | `/api/submissions/:id/analyze` | JWT | Member | Trigger Gemini AI compliance check |
| `GET` | `/api/submissions/:id/analysis` | JWT | Member | Latest AI report + findings |
| `GET` | `/api/submissions/:id/analysis/history` | JWT | Member | All past analyses |
| `POST` | `/api/submissions/:id/submit-approval` | JWT | creator | Submit for manager review |
| `GET` | `/api/submissions/queue` | JWT | admin | Manager approval queue |
| `POST` | `/api/submissions/:id/review` | JWT | admin | Record Approved / Changes Requested |
| `GET` | `/api/submissions/:id/decisions` | JWT | Member | Decision audit trail |
| `POST` | `/api/submissions/:id/publish` | JWT | admin | Publish approved content |
| `GET` | `/api/analytics` | JWT | Any | Governance analytics data |

---

## Testing

```powershell
cd BACKEND
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### Verified Results — 39/39 Passing (2026-10-24)

```
platform win32 -- Python 3.12.9, pytest-9.1.1
collected 39 items

tests/test_auth.py (11 tests)                   PASSED
tests/test_hackathon_upgrades.py (9 tests)       PASSED
tests/test_phase2.py (3 tests)                   PASSED
tests/test_phase3.py (5 tests)                   PASSED
tests/test_phase4.py (2 tests)                   PASSED
tests/test_production_workflows.py (3 tests)     PASSED
tests/test_publishing.py (6 tests)               PASSED

39 passed in 21.72s
```

### Frontend Production Build (2026-10-24)

```
vite v5.4.21 building for production...
1642 modules transformed.
dist/assets/index-*.css   35.59 kB | gzip:   6.46 kB
dist/assets/index-*.js   411.99 kB | gzip: 106.82 kB
built in 5.94s
```
Zero errors, zero warnings.

---

## Known Limitations

1. **In-App Publishing Only** — "Publish" marks content as Published in the platform database. It does not push to external social media, CMS, or ad networks.
2. **Text Content Only** — AI compliance review operates on plain text only. Images, video, audio, and rich HTML are not analyzed.
3. **Scanned PDF / OCR** — The `extract-text` endpoint uses `pypdf`. Scanned (image-only) PDFs without embedded text return empty or incomplete extraction.
4. **Demo Login Security** — `/api/auth/demo-login` auto-creates demo accounts for evaluator convenience. Not suitable for production deployment without restriction.
5. **Rate Limits** — Heavy concurrent use may hit Gemini API free-tier rate limits. Backend returns a descriptive 429 error.

---

## Repository Structure

```
BRAND GUARD/
├── BACKEND/
│   ├── app/
│   │   ├── __init__.py          # App factory, blueprint registration, DB migration
│   │   ├── config.py            # Environment-based config classes
│   │   ├── models/              # SQLAlchemy models (7 files)
│   │   ├── routes/              # Flask blueprints (6 files)
│   │   ├── services/            # Business logic (7 files)
│   │   └── utils/               # Auth decorators
│   ├── tests/                   # 39 pytest integration tests (7 files)
│   ├── seed_demo.py             # Idempotent demo data seeder
│   ├── run.py                   # Dev server entry point
│   ├── requirements.txt
│   └── .env.example
├── FRONTEND/
│   ├── src/
│   │   ├── pages/               # 13 page components
│   │   ├── components/          # Sidebar, ProtectedRoute
│   │   ├── context/             # AuthContext
│   │   ├── services/            # api.js (Axios + JWT interceptors)
│   │   └── App.jsx              # Route definitions
│   ├── vite.config.js
│   └── vercel.json
├── docs/
│   ├── ROUND2_PROJECT_REPORT.md
│   ├── ROUND2_DEMO_GUIDE.md
│   ├── ROUND2_TEST_REPORT.md
│   ├── ROUND3_ROADMAP.md
│   └── DEPLOYMENT_GUIDE.md
├── .env.example
├── .gitignore
└── README.md
```

---

## License & Attribution

Built for the **Inkloom AI Hackathon Round 2**.  
Powered by Google Gemini 2.5 Flash via the official `google-genai` SDK (Apache 2.0).  
AI coding assistance: Google Antigravity IDE utilized for architecture, code generation, test writing, and documentation. All code verified against automated test suites and production build tools.  
MIT License.
