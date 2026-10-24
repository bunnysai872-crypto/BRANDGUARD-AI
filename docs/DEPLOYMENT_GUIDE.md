# BrandGuard AI – Production Deployment Guide

This guide provides step-by-step instructions for deploying BrandGuard AI to production using **Render** for the Python Flask backend and **Vercel** for the React + Vite frontend, backed by a managed **PostgreSQL** database.

---

## 📋 Architecture Overview

- **Frontend**: React 18 + Vite SPA hosted on **Vercel** (Global Edge CDN, automatic HTTPS, SPA rewrites).
- **Backend**: Python Flask 3 Application Factory hosted on **Render** (Gunicorn WSGI web service).
- **Database**: Managed **PostgreSQL** (Render PostgreSQL, Neon, or Supabase).
- **AI Engine**: Google Gemini API via official `google-genai` Python SDK.

---

## 🗄️ Step 1: Push Code to GitHub

> **CRITICAL SECURITY NOTE**: Verify that `.env` files and `brandguard.db` are strictly excluded in `.gitignore` before pushing. Never commit API keys or database files.

```bash
cd "C:\Documents\BRAND GUARD"

# 1. Check git status to ensure .env is untracked
git status

# 2. Add files and commit
git add .
git commit -m "feat: complete Phase 1-5 production-ready BrandGuard AI"

# 3. Create a GitHub repository (e.g. 'brandguard-ai') and push
git remote add origin https://github.com/<your-github-username>/brandguard-ai.git
git branch -M main
git push -u origin main
```

---

## 🐘 Step 2: Create a Hosted PostgreSQL Database

You can use **Render PostgreSQL** (built-in) or a cloud provider like **Neon** or **Supabase**:

### Option A: Render PostgreSQL (Recommended)
1. Log in to [Render](https://dashboard.render.com/).
2. Click **New +** → **PostgreSQL**.
3. Set configuration:
   - **Name**: `brandguard-db`
   - **Database**: `brandguard`
   - **User**: `brandguard_user`
   - **Region**: Choose closest to your audience (e.g., `Singapore` or `Frankfurt`).
   - **Plan**: Free or Starter.
4. Click **Create Database**.
5. Once provisioned, copy the **Internal Database URL** (if backend is on Render) or **External Database URL**.
   *Note: BrandGuard AI automatically converts `postgres://` to `postgresql://`.*

---

## 🐍 Step 3: Deploy Backend to Render

1. On the Render Dashboard, click **New +** → **Web Service**.
2. Connect your GitHub repository (`brandguard-ai`).
3. Set the service settings:
   - **Name**: `brandguard-ai-backend`
   - **Region**: Same region as your database.
   - **Branch**: `main`
   - **Root Directory**: `BACKEND`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn "run:app" --workers 2 --threads 4 --timeout 120`
   - **Plan**: Free or Starter.
4. Open the **Environment Variables** tab and add:

| Key | Value | Description |
| :--- | :--- | :--- |
| `FLASK_ENV` | `production` | Enables production security & logging |
| `SECRET_KEY` | *(Generate a 32-byte hex string)* | Flask session protection |
| `JWT_SECRET_KEY` | *(Generate a 32-byte hex string)* | JWT signing key |
| `DATABASE_URL` | `postgresql://...` | Connection URI from Step 2 |
| `CORS_ORIGINS` | `*` *(Temporary until Vercel URL is known)* | Allowed frontend origins |
| `GEMINI_API_KEY` | `AIzaSy...` | Your Google Gemini API Key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model identifier |
| `PORT` | `10000` | Render default port |

> **Generate Secret Keys locally using Python**:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

5. Click **Deploy Web Service**.
6. Wait for the build to finish. Once live, note your backend URL:
   `https://brandguard-ai-backend.onrender.com`
7. Test the health check endpoint in your browser:
   `https://brandguard-ai-backend.onrender.com/api/health`
   You should receive a `200 OK` JSON response:
   ```json
   {
     "status": "healthy",
     "service": "BrandGuard AI Backend",
     "database": "connected",
     "environment": "production"
   }
   ```

---

## ⚡ Step 4: Deploy Frontend to Vercel

1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New...** → **Project**.
3. Import your GitHub repository (`brandguard-ai`).
4. In the **Configure Project** screen:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `FRONTEND`.
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
5. Expand **Environment Variables** and add:

| Key | Value |
| :--- | :--- |
| `VITE_API_BASE_URL` | `https://brandguard-ai-backend.onrender.com/api` |

6. Click **Deploy**.
7. Vercel will build and deploy the React application in ~30 seconds, generating a production URL:
   `https://brandguard-ai.vercel.app`

---

## 🔄 Step 5: Lock Down CORS on Render

Once your Vercel URL is generated:
1. Return to the **Render Dashboard** → Select `brandguard-ai-backend`.
2. Go to **Environment** variables.
3. Update `CORS_ORIGINS` with your exact Vercel frontend URL:
   `https://brandguard-ai.vercel.app`
4. Click **Save Changes** (Render will automatically redeploy with the restricted CORS policy).

---

## 👥 Step 6: Initialize Production Data (Judge / Demo Seeding)

To seed initial brand profiles, guidelines, and demo accounts on the production PostgreSQL database:

### Option 1: Run Seeder from Render Shell (Recommended)
1. On Render, go to your Web Service → Click **Shell**.
2. Run:
   ```bash
   python seed_demo.py
   ```
3. This creates:
   - **Brand Manager**: `judge.manager@brandguard.ai` / `DemoPassword123!`
   - **Content Creator**: `judge.creator@brandguard.ai` / `DemoPassword123!`
   - Brand Profile `CloudNova` with 6 core guidelines.

### Option 2: Self-Registration
Judges can also navigate to `https://brandguard-ai.vercel.app/register` and create custom Brand Manager and Content Creator accounts directly via the UI.

---

## 🔍 Step 7: Post-Deployment Verification Checklist

- [ ] **Health Check**: Open `https://<backend-url>/api/health` and verify `"database": "connected"`.
- [ ] **SPA Deep Link Refresh**: Open `https://<frontend-url>/login`, log in, navigate to `/manager/approvals`, and press browser refresh (`F5`). Verify the page loads cleanly without a 404 (handled by `vercel.json`).
- [ ] **Authentication**: Register a new user, log out, and log back in.
- [ ] **Brand Rulebook**: As Brand Manager, create or view brand guidelines.
- [ ] **AI Compliance Audit**: As Content Creator, submit marketing copy and click "Run AI Compliance Check". Confirm that Gemini returns structured findings with rule citations.
- [ ] **Approval Workflow**: Submit copy for manager approval, log in as Brand Manager, and test "Approve Content" or "Request Changes".

---

## 🛠️ Troubleshooting Common Issues

### 1. CORS Errors in Browser Console
*Symptom*: `Access to XMLHttpRequest at '...' from origin '...' has been blocked by CORS policy.`  
*Fix*: Ensure `CORS_ORIGINS` on Render matches your exact Vercel domain (including `https://` without a trailing slash).

### 2. Database Connection Error (`OperationalError`)
*Symptom*: Backend health check returns `"database": "unhealthy: database unreachable"`.  
*Fix*: Render PostgreSQL external URLs require SSL. If your connection string does not specify SSL, ensure `?sslmode=require` is appended, or use Render's Internal Database URL when both services reside in the same Render region.

### 3. Vercel Page Refresh 404
*Symptom*: Refreshing on routes like `/creator/submissions` shows `404 NOT_FOUND`.  
*Fix*: Verify that [`FRONTEND/vercel.json`](file:///c:/Documents/BRAND%20GUARD/FRONTEND/vercel.json) exists with rewrite rules forwarding all routes to `/index.html`.
