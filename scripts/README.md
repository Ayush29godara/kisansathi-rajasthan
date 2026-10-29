# KisanSathi Rajasthan - Data Ingestion & Evaluation Scripts

This directory contains standalone CLI scripts for:
1. Knowledge base ingestion and pgvector embedding generation (`build_kb.py`)
2. Mandi price data collection and synchronization (`collect_mandi.py`)
3. Honest model evaluation pipelines (`evaluate_*.py`)

## Honest Data Rule (No Fabricated Datasets)
In compliance with project standards, no synthetic or hallucinated benchmark files are packaged as production datasets. All scripts process user-supplied real-world data files or official government sources.

---

## 1. Knowledge Base Builder (`build_kb.py`)
Processes agricultural advisory PDFs/Text documents, splits them into semantic chunks, generates 768-dimensional text embeddings via Google Gemini Embedding API, and upserts them into Supabase `kb_chunks`.

### Input Required:
- Directory: `data/kb_documents/`
- Format: PDF or UTF-8 `.txt` files (e.g. Package of Practices for Rajasthan Crops from ICAR-CAZRI, SKNAU Jobner, AU Kota).
- Run:
  ```bash
  python scripts/build_kb.py --input-dir data/kb_documents --language hi
  ```

---

## 2. Mandi Price Collector (`collect_mandi.py`)
Fetches and sanitizes official daily commodity arrivals and prices from Agmarknet / data.gov.in APIs or processes historical CSV dumps.

### Input Format (if using CSV dump):
- Path: `data/mandi_raw.csv`
- Required Columns: `mandi,commodity,price_date,min_price,max_price,modal_price,arrivals`
- Run:
  ```bash
  python scripts/collect_mandi.py --input data/mandi_raw.csv --upsert-db
  ```

---

## 3. Yield Model Evaluation (`evaluate_yield.py`)
Evaluates tabular yield models strictly against user-supplied historical records using:
- **Leave-One-Year-Out (LOYO) Cross-Validation**: Trains on all years except year $Y$, evaluates generalization on year $Y$.
- **Leave-One-District-Out (LODO) Cross-Validation**: Trains on all districts except district $D$, evaluates spatial transferability to district $D$.
- Computes Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and baseline comparison against 5-year rolling district means.

### Input Required:
- Path: `data/yield_history.csv`
- Columns: `district,crop,season,year,area_ha,production,yield_kg_ha`
- Run:
  ```bash
  python scripts/evaluate_yield.py --input data/yield_history.csv --crop mustard
  ```

---

## 4. Mandi Price Evaluation (`evaluate_price.py`)
Evaluates time-series price forecast models using **Walk-Forward Validation** (rolling test windows) across 14-day and 28-day forecasting horizons.
- Benchmarks model against the persistence baseline ("same as last week" / moving average).
- Outputs MAE, RMSE, and Directional Accuracy (percentage of correct price movement predictions: bullish/bearish).

### Input Required:
- Path: `data/mandi_prices_history.csv`
- Columns: `mandi,commodity,price_date,modal_price`
- Run:
  ```bash
  python scripts/evaluate_price.py --input data/mandi_prices_history.csv --commodity mustard --mandi Alwar
  ```

---

## 5. Disease Classifier Evaluation (`evaluate_disease.py`)
Evaluates browser-compatible ONNX models on real test images:
- Outputs per-class Precision, Recall, F1-Score, and a complete Confusion Matrix.
- Verifies behavior below the 0.70 confidence threshold (KVK referral accuracy).

### Input Required:
- Directory: `data/disease_test/` (organized as `<crop>_<disease_name>/<image_hash>.jpg`)
- Model: `backend/ml/models/disease_classifier.onnx`
- Run:
  ```bash
  python scripts/evaluate_disease.py --data-dir data/disease_test --model backend/ml/models/disease_classifier.onnx
  ```

---

## 6. RAG Groundedness Evaluation (`evaluate_rag.py`)
Benchmarks **Gemini-alone vs Gemini + RAG Knowledge Base** on an evaluation question file.
- Checks Citation Grounding: Does the answer cite a real retrieved source?
- Hallucination Check: Does the answer introduce unverified chemical names or dosage numbers?
- KVK Fallback Accuracy: For out-of-domain or unanswerable queries, does it correctly trigger KVK fallback?

### Input Required:
- Path: `data/rag_eval_questions.json`
- Schema: List of objects: `[{"question": "...", "expected_intent": "...", "unanswerable": false}]`
- Run:
  ```bash
  python scripts/evaluate_rag.py --eval-file data/rag_eval_questions.json
  ```
