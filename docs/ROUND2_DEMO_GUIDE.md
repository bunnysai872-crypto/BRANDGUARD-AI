# BrandGuard AI — Round 2 Demo Guide
### Step-by-Step Instructions for Hackathon Judges

**Application:** CloudNova BrandGuard AI  
**Local URL:** `http://localhost:5173` (frontend) · `http://localhost:5000` (backend API)  
**Estimated Demo Time:** 3–5 minutes for the complete workflow  

---

## Before You Start: Quick Setup Checklist

1. **Backend running?** Open a terminal in `BRAND GUARD/BACKEND` and run:
   ```powershell
   .\venv\Scripts\Activate.ps1
   python run.py
   ```
   Verify: `http://localhost:5000/api/health` returns `{"status": "healthy"}`

2. **Frontend running?** Open a second terminal in `BRAND GUARD/FRONTEND` and run:
   ```powershell
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

3. **(Optional) Seed realistic demo data:**
   ```powershell
   cd BACKEND
   python seed_demo.py
   ```
   This creates the CloudNova brand with 6 policy guidelines and two ready-to-demo submissions.

---

## Navigation Map

| What you want to do | Where to go |
|:---|:---|
| Sign in | `/login` |
| See your submissions | `/creator/submissions` (creator role) |
| Create a new draft | `/creator/submissions/new` |
| Run AI compliance check | `/submissions/:id` → "Run AI Compliance Check" button |
| View AI findings + apply corrections | `/submissions/:id` → Compliance Results section |
| Submit for manager approval | `/submissions/:id` → "Submit for Manager Approval" button |
| View approval queue (manager) | `/manager/approvals` |
| Approve or request changes | `/manager/approvals` → open submission → review panel |
| Publish approved content | `/manager/approvals` or `/submissions/:id` → "Publish" button |
| View published content | `/published-content` |
| Manage brand guidelines | `/manager/guidelines` |
| View governance analytics | `/analytics` |

---

## 3-Minute Demo Script

### Part 1: One-Click Login (30 seconds)

1. Go to `http://localhost:5173` — you will be redirected to `/login`
2. In the **"One-Click Hackathon Evaluator Login"** panel at the bottom, click **"Content Creator"**
   - This calls `/api/auth/demo-login` which idempotently creates the demo creator account and issues a JWT
   - You are redirected to the Creator Dashboard
3. Note the sidebar navigation: My Submissions, Create Content, Brand Guidelines, Published Content, Analytics

---

### Part 2: Review a Draft with AI Compliance Issues (1 minute)

4. Click **"My Submissions"** in the sidebar
5. Open **"Q4 Enterprise Infrastructure Campaign (Un-audited Draft)"**
   - Notice the status badge: **Draft** (blue)
   - Read the copy — it contains deliberate violations: `"100% downtime-proof guarantee"`, `"cloudnova is the cheapest in the market"`, `"magical orchestration"`, incorrect customer count `"100,000"` vs. approved `"45,000"`

6. Click **"Run AI Compliance Check"**
   - The button shows a loading spinner while calling Gemini 2.5 Flash
   - Within 5–10 seconds, the **AI Compliance Results** panel appears with:
     - **Review Status badge** (e.g., "Violations Detected" in red)
     - Severity summary: Critical / High / Medium / Low counts
     - Each **finding card** shows:
       - The exact quoted phrase from the copy
       - Which brand guideline was violated (linked by name and category)
       - Severity badge (color-coded)
       - Detailed explanation of why this violates brand rules
       - **Suggested Correction** — Gemini's compliant rewrite
       - A **"Apply to Editor"** button for one-click correction

7. Click **"Apply to Editor"** on one of the findings — the suggestion populates the content editor

---

### Part 3: Revise & Resubmit (45 seconds)

8. Click **"Edit Copy"** to open the content editor
9. Replace the content with the compliant copy:
   > *"Accelerate mission-critical workloads with CloudNova Kubernetes Service. Architected for resilience with an audited 99.99% multi-region uptime SLA, CloudNova powers over 45,000 enterprise organizations across 32 global availability regions. Independent audit reports and SOC 2 Type II attestation available upon NDA request."*
10. Enter a revision reason: `"Corrected prohibited claims and verified customer count"` → click **Save Revision**
    - Status resets to **Draft**; the previous AI report is automatically flagged **Outdated**
    - **Revision #2** appears in the Revision History tab

11. Click **"Run AI Compliance Check"** again on the revised copy
    - Gemini should return **"Compliant"** status (green) with 0 findings

12. Click **"Submit for Manager Approval"**
    - If no high/critical findings: submission moves to **Pending Manager Approval** immediately
    - If findings remain: an **Acknowledgement Modal** appears requiring explicit confirmation
    - Content editing is now **locked**

---

### Part 4: Manager Review & Approval (45 seconds)

13. Click your avatar / "Sign Out" and return to `/login`
14. Click **"Brand Manager"** in the One-Click Login panel
    - You are redirected to the Manager Dashboard showing pending approval counts

15. Click **"Approval Queue"** in the sidebar
16. Open the pending submission
    - You see: full content, AI compliance summary, all findings with severity, revision history
17. In the **Review Decision** panel:
    - Enter comments: `"Approved. All claims verified against CloudNova enterprise SLA documentation."`
    - Click **"Approve Content"**
    - Status changes to **Approved** (green badge, permanently locked)

18. Click **"Publish Content"** (visible to Brand Managers on Approved submissions)
    - Status changes to **Published**; `published_at` timestamp is recorded

---

### Part 5: Published Archive & Analytics (30 seconds)

19. Click **"Published Content"** in the sidebar
    - The published submission appears in the in-app archive with metadata

20. Click **"Governance Analytics"** in the sidebar
    - Dashboard shows: total submissions, approved/published counts, violation category distribution, severity breakdown, common flagged phrases, timeline trends
    - All data is computed live from the database — no mock data

---

## Key Features to Highlight During Demo

| Feature | Where to Demo | What to Show |
|:---|:---|:---|
| Structured AI findings | `/submissions/:id` after analysis | Guideline citations, severity, suggested corrections |
| Stale report detection | Edit copy after analysis | "Outdated" badge on prior report |
| Hallucination prevention | Check findings | Guidelines cited only from registered DB rules |
| Acknowledgement gate | Submit with high-severity findings | Warning modal before escalation |
| Immutable revision history | Revision History tab | Every version preserved with timestamp and reason |
| Role-based access | Try manager URL as creator | 403 Forbidden response |
| Decision audit trail | Decision History tab | Reviewer name, timestamp, comments, revision number |
| In-app publishing | Manager view of Approved submission | "Publish" button, `published_at` set |

---

## Sample Test Content

### Content with Deliberate Violations (for AI review demo)
```
Migrate your enterprise workloads to CloudNova today! Our revolutionary cloud 
architecture offers a 100% downtime-proof guarantee with zero cost forever on 
foundational tiers. Serving over 100,000 customers with magical orchestration, 
cloudnova is the cheapest in the market. Unhackable encryption comes standard.
```
**Expected findings:** Prohibited claims ("100% downtime-proof", "zero cost forever", "unhackable"), restricted terms ("magical", "cheapest in the market"), incorrect customer count, brand name capitalization violation.

### Compliant Content (for clean AI review)
```
Accelerate mission-critical workloads with CloudNova Kubernetes Service. 
Architected for resilience with an audited 99.99% multi-region uptime SLA, 
CloudNova powers over 45,000 enterprise organizations across 32 global 
availability regions. Independent audit reports and SOC 2 Type II attestation 
available upon NDA request.
```
**Expected result:** "Compliant" status, 0 findings.

---

## Known Limitations (to disclose during demo)

1. **AI response time:** Gemini API calls take 3–10 seconds depending on content length and network latency
2. **In-app publishing only:** The "Publish" action records status in the database; it does not post to external platforms
3. **Text only:** Image and video assets are not supported by the AI compliance engine
4. **Scanned PDFs:** PDF text extraction requires embedded text layers; scanned/image PDFs are not supported
5. **Demo accounts:** One-click demo login creates convenience accounts not suitable for production security
6. **Rate limits:** Rapid consecutive AI checks may hit Gemini free-tier rate limits (429 error returned)

---

## Troubleshooting

| Problem | Solution |
|:---|:---|
| Login button shows error | Ensure backend is running at `localhost:5000`; check `BACKEND/.env` has a valid `GEMINI_API_KEY` |
| AI check returns "Gemini API key not configured" | Edit `BACKEND/.env`, set `GEMINI_API_KEY=AIzaSy...`, restart backend |
| AI check returns 429 | Gemini free-tier rate limit hit; wait 30 seconds and retry |
| "No guidelines configured" error | Run `python seed_demo.py` in BACKEND directory to create sample guidelines |
| Approval Queue is empty | Log in as a Creator first and submit a submission for manager approval |
| Cannot edit submission | Submission is in Pending/Approved/Published status — editing is intentionally locked |
