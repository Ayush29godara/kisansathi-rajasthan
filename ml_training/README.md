# ML Training Pipelines (Google Colab Friendly)

This directory contains end-to-end training notebooks for tabular yield prediction, mandi price forecasting, and client-side ONNX model export for crop disease detection.

## Critical Production Architecture Rules
1. **Never Train on the Production Server**: Render free tier has 512 MB RAM and an ephemeral filesystem. Training must occur exclusively in Google Colab or external compute environments.
2. **Lightweight Deployment**:
   - Tabular yield and price models export to compact `.joblib` artifacts (< 10 MB) loaded by scikit-learn/LightGBM in the backend.
   - Disease vision models export to quantized `.onnx` models (< 15 MB) delivered to the browser and executed by ONNX Runtime Web client-side. Zero PyTorch or torchvision on the server!
3. **Honest Baseline Fallback**:
   - Until trained `.joblib` or `.onnx` artifacts are placed into `backend/ml/models/` or `frontend/public/models/`, the application runs transparent baseline estimators with `model_version = "baseline"`.

---

## Notebooks Overview

### `01_yield_prediction.ipynb`
- **Objective**: Predict district crop yield ($kg/ha$) using historical weather aggregates, rainfall deviation, irrigation ratio, and soil characteristics.
- **Algorithms**: Ridge Regression, Random Forest, XGBoost / LightGBM.
- **Explainability**: TreeSHAP feature attributions exported for top positive/negative yield drivers.
- **Validation**: Leave-One-Year-Out (LOYO) and Leave-One-District-Out (LODO).
- **Export**: `yield_xgb.joblib`.

### `02_mandi_price_forecast.ipynb`
- **Objective**: Multi-step time series forecast (14-day and 28-day price horizons) for Rajasthan APMC mandis.
- **Algorithms**: AutoARIMA / SARIMAX (Statsmodels), LightGBM with lag features (t-1, t-7, t-14, t-28, rolling moving averages).
- **Validation**: Rolling Walk-Forward cross-validation against the persistence baseline ("same as last week").
- **Export**: `price_lgb.joblib`.

### `03_disease_model_export.ipynb`
- **Objective**: Train a lightweight convolutional model (MobileNetV3-Small / EfficientNet-Lite) for key Rajasthan crop diseases (Mustard White Rust, Bajra Blast, Wheat Rust).
- **Export**: Quantized FP16/INT8 ONNX format (`crop_disease.onnx`) for browser execution via ONNX Runtime Web.
- **Evaluation**: Per-class Precision, Recall, F1-score, and confusion matrix.
