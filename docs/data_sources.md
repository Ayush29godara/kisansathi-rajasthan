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
- **Source**: Open-Meteo Historical & Forecast Weather API / Indian Meteorological Department (IMD) Agromet Advisories.
- **Physics Equations**: FAO-56 Penman-Monteith equation for reference evapotranspiration ($ET_0$) combined with stage-specific crop coefficients ($K_c$).
