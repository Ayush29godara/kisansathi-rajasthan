# KisanSathi Rajasthan (किसान साथी राजस्थान)
**AI-Assisted Decision-Support System for Smallholder Farmers in Rajasthan, India**
*Academic Final-Year Capstone Project*

[![CI Pipeline](https://github.com/ayush/kisansathi-rajasthan/actions/workflows/ci.yml/badge.svg)](https://github.com/ayush/kisansathi-rajasthan/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.115-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Vite_6-61DAFB.svg?logo=react)](https://react.dev)
[![Supabase](https://img.shields.io/badge/Database-Supabase_Postgres_%2B_pgvector-3ECF8E.svg?logo=supabase)](https://supabase.com)
[![Render Target](https://img.shields.io/badge/Deploy-Render_Free_Tier_(512MB)-46E3B7.svg?logo=render)](https://render.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌾 1. Product Overview
Smallholder farmers in Rajasthan face extreme climate variability, localized pest attacks, water scarcity, and fluctuating market prices. **KisanSathi Rajasthan** provides actionable, grounded, and bilingual (Hindi default, English supported) decision support without black-box hallucinations.

### Core Features (in priority order)
1. **Farm Profile**: Captures district, tehsil, primary crop, land size (hectares/bigha), irrigation source, and sowing date to personalize all insights.
2. **Advisor Chat**: Grounded text and voice conversational assistant utilizing RAG over verified Rajasthan agricultural manuals (ICAR-CAZRI, SKNAU, AU Kota). Every answer transparently cites its sources.
3. **Crop Disease Detection**: Real-time leaf diagnosis executed **inside the farmer's browser** via ONNX Runtime Web. Confidence $< 70\%$ falls back safely to "Not sure, contact your nearest KVK".
4. **District Yield Outlook**: Forecasts district crop yields ($kg/ha$) with SHAP feature driver explanations, backed by verified historical baselines.
5. **Mandi Price Trend & Forecast**: APMC mandi price history and 2-4 week forecast ranges across Rajasthan trading hubs.
6. **Weather & Irrigation Advisory**: Regional agro-weather alerts paired with a 100% deterministic **FAO-56 Penman-Monteith Evapotranspiration ($ET_0$)** irrigation scheduler.

*Explicitly Out of Scope*: Satellite imagery, SMS/IVR gateways, payment gateways, native mobile apps.

---

## 🏛️ 2. System Architecture & Free-Tier Constraints

```
┌────────────────────────────────────────────────────────────────────────┐
│                     CLIENT: Mobile-First React PWA                     │
│  - Vite + React + TypeScript + Tailwind CSS                            │
│  - react-i18next (Hindi default, English supported)                    │
│  - ONNX Runtime Web (In-browser disease classification)                │
│  - Service Worker (Offline caching of profile, advice, and prices)    │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTPS + Supabase JWT
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│             BACKEND: FastAPI on Render Free Tier (512 MB RAM)          │
│  - Python 3.11-slim Docker Container (Single uvicorn worker)          │
│  - Strict CORS: Configured origin only (Never "*")                     │
│  - Rule-Based Intent Classifier (Zero LLM overhead)                    │
│  - FAO-56 ET0 Irrigation Engine (Deterministic physics)                │
│  - Zero PyTorch/Transformers on server (Protects 512MB RAM budget)     │
│  - Ephemeral Disk: In-memory image processing, EXIF stripping          │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│       Supabase Cloud Services        │  │     Google Gemini 1.5 Flash  │
│  - Postgres with pgvector extension  │  │  - Used SOLELY for grounded  │
│  - Supabase Auth (Email / Google)    │  │    language synthesis and    │
│  - Row Level Security (RLS) on all   │  │    explanation from context. │
│    tables (auth.uid() = user_id)     │  │  - NEVER invents doses or    │
│  - Supabase Storage (Opt-in only)    │  │    chemical numbers.         │
└──────────────────────────────────────┘  └──────────────────────────────┘
```

---

## 📋 3. Whole-Project Roadmap & Phases

- [x] **Phase 0: Scaffold, Architecture & Environment Setup** *(Completed)*
  - Monorepo directory layout, Dockerfile, render.yaml, CI workflow, .env templates.
  - Pydantic contracts, SQLAlchemy connection layer, Supabase JWT verification.
  - Full SQL migration with tables, pgvector index, and Row Level Security (RLS) policies.
  - Reference data for Rajasthan districts, crops, mandis, and thresholds.
  - Colab training notebooks and evaluation scripts (`evaluate_*.py`).
  - Mobile-first React + Vite frontend scaffold with i18n and PWA service worker.
- [ ] **Phase 1: Database, Supabase Auth & Farm Profile Management**
  - Live Supabase connection, schema deployment, Auth flows (Email & Google).
  - Farm profile onboarding with Bigha-to-Hectare converter and personal context caching.
- [ ] **Phase 2: RAG Knowledge Base & Gemini Advisor Chat**
  - Document chunking and 768-dim vector embeddings via Gemini Embedding API in `kb_chunks`.
  - Intent router and pgvector cosine search.
  - Strict grounding prompt: zero hallucinated dosages, automatic KVK fallback.
  - Voice recording and transcription integration.
- [ ] **Phase 3: In-Browser Crop Disease Diagnosis**
  - Browser-side ONNX Runtime Web model loader and image preprocessor.
  - Client canvas rendering, EXIF stripping, $< 70\%$ confidence threshold fallback.
  - Optional user opt-in photo storage in Supabase.
- [ ] **Phase 4: District Crop Yield Outlook**
  - Colab XGBoost/LightGBM training on DES Rajasthan data with LOYO/LODO cross-validation.
  - Compact joblib model export and TreeSHAP feature attribution explanations.
  - Transparent fallback to 5-year rolling district means (`model_version = "baseline"`).
- [ ] **Phase 5: Mandi Price Trends & Forecasting**
  - Agmarknet daily price ingestion pipeline.
  - Time-series model (LightGBM lag features / SARIMAX) with walk-forward validation.
  - 2-4 week forecast ranges with persistence baseline fallback.
- [ ] **Phase 6: Weather Advisory & FAO-56 Evapotranspiration Irrigation**
  - Open-Meteo weather API integration.
  - Penman-Monteith reference evapotranspiration ($ET_0$) and crop coefficient ($K_c$) engine.
  - Extreme weather alerts (heatwave, frost, unseasonal rainfall).
- [ ] **Phase 7: History, Offline PWA, Feedback & Polish**
  - Offline sync with Service Worker and IndexedDB/localStorage.
  - User feedback loop (`/feedback`) linked to chat and diagnoses.
  - Full About page displaying real model metrics and academic attribution.

---

## 🔒 4. Hard Security & Safety Rules

1. **No Frontend Secrets**: `VITE_` variables hold only the public Supabase URL and public anon key. The database connection string, service role key, and Gemini API key exist strictly as backend environment variables.
2. **Strict CORS**: The FastAPI CORS middleware permits only the configured `FRONTEND_ORIGIN`. Wildcards (`"*"`) are explicitly rejected.
3. **Privacy & Upload Safety**: Images are checked for JPEG/PNG format, limited to 5 MB, and completely stripped of EXIF GPS coordinates. Photos are never stored unless the user checks the explicit opt-in box.
4. **Scoping**: All database operations check `auth.uid() = user_id`. No user can query or alter another farmer's profile, questions, or diagnosis records.
5. **No Hallucinated Doses**: Gemini is restricted to retrieved passages for pesticide names or doses. If no matching treatment exists in the knowledge base, it outputs:
   > *"मुझे इस विषय में पूरी जानकारी नहीं है, कृपया अपने नजदीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"*

---

## 📊 5. Scientific Honesty & Baseline Fallbacks

Per academic standards, synthetic data and fake model accuracies are forbidden:
- **Missing Models**: When trained `.joblib` or `.onnx` models are not loaded, the application transparently runs deterministic baseline algorithms:
  - Yield: District 5-year rolling historical mean.
  - Price: Persistence baseline ("Same as last week" / lag-7 value).
  - Disease: Low confidence ($< 0.70$) KVK referral.
- **Reporting**: Any response generated by a baseline algorithm reports:
  ```json
  "model_version": "baseline"
  ```
- **Real Evaluation**: Evaluation scripts (`scripts/evaluate_*.py`) execute real mathematical validations (LOYO/LODO, Walk-forward, Confusion matrix) on real datasets.

---

## 🚀 6. Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+ & npm

### Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your Supabase credentials and Gemini API Key

# 5. Run tests
pytest -v tests/

# 6. Start development server
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

### Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY

# 4. Start Vite dev server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## ☁️ 7. Production Deployment Instructions

### Backend (Render Free Web Service)
1. Push this repository to GitHub.
2. In Render Dashboard, click **New > Blueprint** and select your repository (it automatically reads `render.yaml`).
3. Set the required sensitive environment variables (`SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, `GEMINI_API_KEY`, `FRONTEND_ORIGIN`).
4. Render deploys the Docker container (`Dockerfile`) using Python 3.11-slim with health check target `/health`.

### Frontend (Vercel or Netlify)
1. Connect repository to Vercel or Netlify.
2. Root directory: `frontend`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Set environment variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_BASE_URL` (URL of your deployed Render service)

---

## ⚖️ 8. Advisory Disclaimer
> **सूचना / Disclaimer**: यह पोर्टल केवल निर्णय-सहायता मार्गदर्शन प्रदान करता है। किसी भी गंभीर फसल रोग, रासायनिक छिड़काव या वित्तीय निर्णय के लिए सदैव अपने निकटतम कृषि विज्ञान केंद्र (KVK) अथवा प्रमाणित कृषि विशेषज्ञ से प्रत्यक्ष परामर्श लें।
