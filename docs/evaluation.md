# KisanSathi Rajasthan: Evaluation Methodology & Metrics

Scientific rigor requires robust cross-validation schemes that mirror real-world agricultural decision cycles rather than naive random train/test splits.

---

## 1. District Yield Model Evaluation

### Cross-Validation Strategy:
1. **Leave-One-Year-Out (LOYO)**:
   - For a dataset spanning years $Y_1 \dots Y_n$, each year $Y_i$ serves as the unseen test fold while the remaining $n-1$ years form the training set.
   - Prevents temporal data leakage and evaluates model robustness against climate fluctuations (e.g. drought years).
2. **Leave-One-District-Out (LODO)**:
   - Evaluates spatial generalization by training on $D-1$ districts and evaluating on the held-out district.

### Evaluation Metrics:
- Root Mean Squared Error (RMSE) in $kg/ha$
- Mean Absolute Error (MAE) in $kg/ha$
- Percentage Improvement over Baseline (5-year rolling district historical mean):
  $$\text{Gain}_{\%} = \frac{\text{MAE}_{\text{baseline}} - \text{MAE}_{\text{model}}}{\text{MAE}_{\text{baseline}}} \times 100$$

---

## 2. Mandi Price Time-Series Evaluation

### Walk-Forward Validation:
- Evaluates forecasting horizons of 14 days and 28 days.
- Rolling origin: Training window expands incrementally, producing forecasts at $t+14$ and $t+28$.
- Benchmarked strictly against the persistence baseline ($P_{t+h} = P_t$).

### Evaluation Metrics:
- MAE and RMSE in ₹/Quintal.
- Directional Accuracy ($\%$ of correct predictions on whether the price increases or decreases over the horizon).

---

## 3. Crop Disease Vision Evaluation

### Evaluation Protocol:
- Test image set from Rajasthan crops with verified ground-truth labels.
- Evaluated on exported ONNX Runtime Web graph.

### Evaluation Metrics:
- Per-class Precision, Recall, and F1-Score:
  $$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}, \quad F_1 = 2 \times \frac{P \times R}{P + R}$$
- Multiclass Confusion Matrix.
- **KVK Referral Rate**: Verification that image queries with confidence $< 0.70$ consistently fall back to KVK referral advice rather than hallucinating an incorrect diagnosis.

---

## 4. RAG & Advisor Chat Evaluation

### Grounding & Safety Metrics:
- **Citation Grounding Rate**: Percentage of answers containing at least one verified reference citation.
- **Hallucination Rate**: Checks whether chemical pesticides or numeric dosages appear that do not exist in the retrieved knowledge chunk. Target: 0.0%.
- **Safety Fallback Accuracy**: For ambiguous, hazardous, or out-of-domain queries, verifying that the system successfully returns the KVK referral response.
