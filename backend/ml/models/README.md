# Machine Learning Model Artifacts

This directory stores serialized model artifacts (.joblib, .json) for tabular prediction pipelines.

## Critical Honesty & Baseline Fallback Rule
In accordance with KisanSathi guidelines:
1. **Never fabricate dummy model weights or inflate accuracy claims.**
2. When trained models (`yield_xgb.joblib`, `price_lgb.joblib`) are absent, the application automatically invokes deterministic baseline algorithms (e.g., historical 5-year district rolling mean for yield, lag-7 moving average for mandi prices).
3. Any response produced by a baseline algorithm reports:
   ```json
   "model_version": "baseline"
   ```
4. Only real models evaluated on real historical datasets (via `/scripts/evaluate_*.py`) with metrics logged in `/docs/evaluation.md` may use non-baseline version tags.
