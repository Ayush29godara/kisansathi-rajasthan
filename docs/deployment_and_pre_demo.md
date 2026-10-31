# KisanSathi Rajasthan: Deployment Guide & Pre-Demo Checklist

## 🚀 1. Step-by-Step Deployment Instructions

### A. Supabase Project Setup & Auth Configuration
1. Open the [Supabase Dashboard](https://supabase.com/dashboard) and select project `skvleyiohnbwmnzdjdvh`.
2. **Apply Migrations**:
   - The database schema is already applied via `supabase/migrations/20261029000000_initial_schema.sql` and `20261030000001_auth_trigger.sql`.
   - All 9 tables and RLS policies are active.
3. **Configure Authentication Redirects**:
   - Navigate to **Authentication > URL Configuration**.
   - Set **Site URL** to your frontend domain: e.g. `https://kisansathi-rajasthan.vercel.app` (or `http://localhost:5173` for development).
   - Under **Redirect URLs**, add:
     - `http://localhost:5173/**`
     - `https://<your-vercel-or-netlify-app>/**`
4. **Google OAuth (Optional / Production)**:
   - Navigate to **Authentication > Providers > Google**.
   - Toggle **Enable Google provider**.
   - Input your Google Cloud OAuth Client ID and Client Secret.

---

### B. Backend Deployment to Render (Free Web Service)
1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), click **New > Blueprint**.
3. Select your repository. Render automatically reads `render.yaml` and provisions the `kisansathi-backend` Docker service.
4. Supply the sensitive environment variables in Render Dashboard under **Environment**:
   | Variable | Value | Description |
   | :--- | :--- | :--- |
   | `PORT` | `8000` | Service listening port |
   | `ENVIRONMENT` | `production` | Deployment environment |
   | `LOG_LEVEL` | `INFO` | Logging verbosity |
   | `FRONTEND_ORIGIN` | `https://<your-frontend-domain>` | Strict CORS (Never allow `*`) |
   | `SUPABASE_URL` | `https://<your-project-id>.supabase.co` | Supabase API base URL |
   | `SUPABASE_SERVICE_ROLE_KEY` | `<your-service-role-key>` | Backend admin key |
   | `SUPABASE_JWT_SECRET` | `<your-jwt-secret>` | For validating auth tokens |
   | `DATABASE_URL` | `postgresql://<user>:<password>@<host>:6543/postgres?sslmode=require` | Postgres connection string |
   | `GEMINI_API_KEY` | `<your-gemini-api-key>` | Google Generative Language key |
   | `GEMINI_MODEL` | `gemini-1.5-flash` | LLM model version |
   | `DEFAULT_MODEL_VERSION` | `baseline` | Fallback version label |

5. Deploy. Once live, test `https://<your-render-url>/health`. You should receive:
   ```json
   {
     "status": "ok",
     "version": "0.1.0",
     "environment": "production",
     "database": "connected"
   }
   ```

---

### C. Frontend Deployment (Vercel or Netlify)

#### Option 1: Vercel (Recommended)
1. In [Vercel Dashboard](https://vercel.com/new), import your GitHub repository.
2. Set **Root Directory** to `frontend`.
3. Framework Preset: **Vite**.
4. Configure Environment Variables:
   - `VITE_SUPABASE_URL`: `https://skvleyiohnbwmnzdjdvh.supabase.co`
   - `VITE_SUPABASE_ANON_KEY`: `sb_publishable_oAfdd1eA7OB3-kSonYjEkQ_LjZYtZ57`
   - `VITE_API_BASE_URL`: `https://<your-render-url>` (without trailing slash)
5. Click **Deploy**. Vercel uses `frontend/vercel.json` for SPA route rewrites.

#### Option 2: Netlify
1. In [Netlify Dashboard](https://app.netlify.com), select **Add new site > Import an existing project**.
2. Base directory: `frontend`.
3. Build command: `npm run build`.
4. Publish directory: `frontend/dist`.
5. Set environment variables (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL`).
6. Deploy. Netlify reads `frontend/netlify.toml` for `/* -> /index.html 200` routing.

---

## 📋 2. Pre-Demo Checklist (Crucial for Presentations & Exams)

| Item | What could go wrong? | Action Required | Verified? |
| :--- | :--- | :--- | :---: |
| **1. Render Cold Start** | Render free tier spins down after 15 min idle. The first request takes 30-50 seconds to boot the container, looking like an error to evaluators. | **2 minutes before your demo**, open `https://<your-render-url>/health` in a browser tab to wake up the service. | [ ] |
| **2. Supabase Project Pause** | Free-tier Supabase projects automatically pause after 7 days of inactivity. | Check your Supabase dashboard 24 hours prior. If paused, click **Restore Project** (takes 1-2 minutes). | [ ] |
| **3. Strict CORS Whitelist** | If `FRONTEND_ORIGIN` on Render doesn't match your Vercel URL (e.g. missing `https://` or having a trailing `/`), the browser blocks API requests with a CORS error. | Ensure `FRONTEND_ORIGIN` is exactly `https://your-app.vercel.app` without a trailing slash. | [ ] |
| **4. Database Ping** | Database password special characters may break URI parsing if not URL-encoded. | Check `/health` endpoint output. Verify `"database": "connected"`. | [ ] |
| **5. Pre-seeded Demo Farmer** | Demonstrating with an empty profile requires filling out the form during the exam. | Create a sample farmer account beforehand (e.g. `kisan.alwar@example.com` with Mustard in Alwar) so you can showcase both the onboarding wizard and an existing populated dashboard. | [ ] |
| **6. Offline PWA Demonstration** | Evaluators test rural resilience by turning off Wi-Fi. | Load the home page, toggle Chrome DevTools Network to **Offline**, refresh the page, and show that cached farm profile and advice still load seamlessly from service worker cache. | [ ] |
