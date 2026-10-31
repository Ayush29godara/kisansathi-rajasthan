# District-Level Agricultural Yield Dataset Specification (`data/yield_data/`)

This directory documents the official data format, sources, and boundary mapping rules for district crop yield models in **KisanSathi Rajasthan**.

---

## 1. Fixed District Boundary Decision: The 33-District Standard

### Background & Justification
- Prior to August 2023, Rajasthan comprised **33 administrative districts**.
- In August 2023, the Government of Rajasthan carved out new districts (e.g., Anupgarh from Sri Ganganagar/Bikaner, Balotra from Barmer, Kotputli-Behror and Jaipur Rural from Jaipur, Khairthal-Tijara from Alwar, Phalodi from Jodhpur, Salumber from Udaipur, Sanchore from Jalore, Didwana-Kuchaman from Nagaur, Shahpura from Bhilwara, Kekri and Beawar from Ajmer).
- **Critical Statistical Constraint**: Official agricultural yield statistics from the Directorate of Economics and Statistics (DES), Ministry of Agriculture (DES-APY / ICRISAT DLD) are compiled historically at the **33-district boundary level** from 1997 through 2023. Newly created districts lack independent multi-decade yield time series.
- **Decision**: All machine learning models, baseline statistics, and spatial cross-validation in KisanSathi are calibrated on the **fixed 33-district historical boundary standard**.
- When a farmer selects any of the 41/50 current administrative districts, KisanSathi deterministically maps the selection to its parent historical statistical district using the mapping table below.

### Administrative District to Statistical District Mapping

| Current Administrative District | Historical Statistical District | Agro-Climatic Zone |
| :--- | :--- | :--- |
| **Jaipur Urban**, **Jaipur Rural**, **Dudu** | **Jaipur** | Semi-Arid Eastern Plain (III-A) |
| **Kotputli-Behror**, **Alwar** | **Alwar** | Flood Prone Eastern Plain (III-B) |
| **Khairthal-Tijara** | **Alwar** | Flood Prone Eastern Plain (III-B) |
| **Jodhpur Urban**, **Jodhpur Rural** | **Jodhpur** | Arid Western Plain (I-A) |
| **Phalodi** | **Jodhpur** | Arid Western Plain (I-A) |
| **Balotra**, **Barmer** | **Barmer** | Arid Western Plain (I-A) |
| **Anupgarh**, **Sri Ganganagar** | **Sri Ganganagar** | Irrigated North-Western Plain (I-B) |
| **Didwana-Kuchaman**, **Nagaur** | **Nagaur** | Transitional Plain of Inland Drainage (II-A) |
| **Beawar**, **Kekri**, **Ajmer** | **Ajmer** | Semi-Arid Eastern Plain (III-A) |
| **Salumber**, **Udaipur** | **Udaipur** | Sub-Humid Southern Plain (IV-A) |
| **Sanchore**, **Jalore** | **Jalore** | Transitional Plain of Luni Basin (II-B) |
| **Shahpura**, **Bhilwara** | **Bhilwara** | Sub-Humid Southern Plain (IV-A) |
| **Deeg**, **Bharatpur** | **Bharatpur** | Flood Prone Eastern Plain (III-B) |
| **Gangapur City**, **Sawai Madhopur** | **Sawai Madhopur** | Flood Prone Eastern Plain (III-B) |

*(All other districts retain their direct 1:1 mapping).*

---

## 2. Expected Raw Data Format (`raw_yield.csv`)

Please place the historical yield CSV downloaded from [data.gov.in](https://data.gov.in) or [aps.dac.gov.in](https://aps.dac.gov.in) at `data/yield_data/raw_yield.csv`.

Required column headers:

```csv
State,District,Crop,Year,Season,Area_Hectares,Production_Tonnes,Yield_Kg_Per_Hectare
Rajasthan,Alwar,Mustard,2022,Rabi,312450,562410,1800.0
Rajasthan,Jaipur,Bajra,2022,Kharif,245000,441000,1800.0
Rajasthan,Sri Ganganagar,Wheat,2022,Rabi,289000,1213800,4200.0
```

### Fields Description
1. `State`: Must be "Rajasthan" (or filtered during cleaning).
2. `District`: District name in Rajasthan (standard or local spelling).
3. `Crop`: Target crop (Mustard / सरसों, Bajra / बाजरा, Wheat / गेहूं, Soybean / सोयाबीन, Guar / ग्वार, Gram / चना).
4. `Year`: Agricultural year (e.g. 2022 represents 2022-23).
5. `Season`: Crop season (`Kharif`, `Rabi`, or `Whole Year`).
6. `Area_Hectares`: Total cultivated area under the crop in hectares.
7. `Production_Tonnes`: Total harvest production in metric tonnes.
8. `Yield_Kg_Per_Hectare`: Production yield in $kg/ha$. If missing, calculated as:
   $$\text{Yield} = \frac{\text{Production (Tonnes)} \times 1000}{\text{Area (Hectares)}}$$

---

## 3. Data Cleaning Pipeline

Run the automated cleaning script to normalize district boundaries, validate values, and filter outliers:

```bash
# Clean raw yield dataset
python scripts/clean_yield_data.py --input data/yield_data/raw_yield.csv --output data/yield_data/cleaned_yield.csv

# If you haven't supplied raw data yet, run with --synthetic to generate verified statistical mock data for testing
python scripts/clean_yield_data.py --synthetic --output data/yield_data/cleaned_yield.csv
```

The script outputs `data/yield_data/cleaned_yield.csv`.
