# KisanSathi Rajasthan: Data Sources & Honesty Standards

## Data Honesty Commitment
In an academic and university project, scientific integrity is paramount:
- **No Fabricated Datasets**: Dummy numbers, artificial accuracy percentages, or fake agricultural advice are strictly prohibited.
- **Transparent Baselines**: When trained machine learning models are absent, baseline statistical fallbacks (district 5-year rolling means, persistence mandi prices) are explicitly tagged as `model_version = "baseline"`.

---

## 1. Primary Data Sources

### A. District Crop Production & Yield History
- **Source**: Directorate of Economics and Statistics (DES), Department of Agriculture, Government of Rajasthan / Ministry of Agriculture & Farmers Welfare (APY portal).
- **Target Table**: `public.yield_history`
- **Required Columns**:
  - `district` (e.g. Alwar, Kota, Sri Ganganagar)
  - `crop` (Mustard, Bajra, Wheat, Guar, Soybean, Gram)
  - `season` (Kharif, Rabi, Zaid)
  - `year` (1997 - 2024)
  - `area_ha` (Area under cultivation in hectares)
  - `production` (Metric tonnes)
  - `yield_kg_ha` (Calculated as $(\text{production} \times 1000) / \text{area\_ha}$)

### B. APMC Mandi Prices & Arrivals
- **Source**: Agmarknet (Agricultural Marketing Information Network) / Open Government Data Platform India (data.gov.in).
- **Target Table**: `public.mandi_prices`
- **Required Columns**:
  - `mandi` (e.g. Kota, Alwar, Surajpole Jaipur, Bikaner)
  - `commodity` (Mustard, Wheat, Bajra, Guar, Gram, Soybean)
  - `price_date` (YYYY-MM-DD)
  - `min_price` (INR / Quintal)
  - `max_price` (INR / Quintal)
  - `modal_price` (INR / Quintal)
  - `arrivals` (Tonnes)
  - Unique Constraint: `(mandi, commodity, price_date)`

### C. Agricultural Knowledge Base & Packages of Practices
- **Source**:
  - ICAR - Central Arid Zone Research Institute (CAZRI), Jodhpur
  - Swami Keshwanand Rajasthan Agricultural University (SKRAU), Bikaner
  - Sri Karan Narendra Agriculture University (SKNAU), Jobner
  - Agriculture University, Kota
  - Krishi Vigyan Kendra (KVK) advisories across Rajasthan agro-climatic zones
- **Target Table**: `public.kb_chunks`
- **Embeddings**: 768-dimensional vectors generated via Gemini Embedding API (`models/text-embedding-004`).

### D. Weather & Agro-meteorological Data
- **Live Provider**: Open-Meteo Weather API (`https://api.open-meteo.com/v1/forecast`), an open-access meteorological service operating with standard WMO physical models (ERA5 / GFS). Zero proprietary API key required.
- **District Reference**: `backend/reference/districts.json` specifying exact centroid coordinates (latitude, longitude) and elevation above sea level (meters) across all 43 administrative districts of Rajasthan (covering newly formed districts such as Balotra, Anupgarh, Kotputli-Behror, Phalodi, Salumbar, and Kekri mapped from parent jurisdictions).
- **Offline / Sandboxed Fallback**: Built-in monthly climatological normals for Rajasthan agro-climatic zones, ensuring 100% test reliability and resilience during network outages.
- **Physics Equations**: Standard FAO-56 Penman-Monteith reference evapotranspiration ($ET_0$) combined with stage-specific crop coefficients ($K_c$).

---

## 2. Agronomic Rules & Thresholds (No ML)

> [!NOTE]
> **Agronomic Rule Grounding**: Crop alert rules and irrigation decisions are strictly deterministic agronomic rules, not statistical or deep learning predictions. Each rule in `backend/reference/thresholds.json` includes an explicit `source` field referencing State Agricultural University advisories:

| Alert Category | Condition Threshold | Agronomic Action | University Source |
| :--- | :--- | :--- | :--- |
| **Frost / Cold Wave** | $T_{\min} \le 4.0^\circ\text{C}$ (Critical $\le 2.0^\circ\text{C}$) | Evening light irrigation, smoke generation on northern bunds, or 0.1% dilute sulfuric acid ($H_2SO_4$) spray | *Package of Practices, Agriculture University Kota* |
| **Terminal Heat Stress** | $T_{\max} \ge 38.0^\circ\text{C}$ (Critical $\ge 42.0^\circ\text{C}$) during flowering/grain-fill | Light sprinkler irrigation to lower canopy temperature; spray 0.2% potassium nitrate ($KNO_3$) | *ICAR-IIWBR Technical Guidelines on Terminal Heat Stress in Wheat* |
| **Cloudy/Humid Disease Outbreak** | $RH \ge 80\%$ and $10^\circ\text{C} \le T_{\min} \le 26^\circ\text{C}$ in mustard | Regular inspection for white rust / downy mildew; avoid unnecessary flood irrigation | *Directorate of Rapeseed-Mustard Research (DRMR) & SKNAU Jobner* |
| **Heavy Rainfall Withholding** | 72-hour precipitation forecast $\ge 20\text{ mm}$ | Postpone planned irrigation to prevent root hypoxia, waterlogging, and nutrient leaching | *State Department of Agriculture, Rajasthan Water Management Guidelines* |
| **High Wind Lodging** | Wind speed $\ge 28\text{ km/h}$ during heading / grain filling | Delay irrigation to avoid severe stem lodging | *State Department of Agriculture, Rajasthan Extension Manual* |
