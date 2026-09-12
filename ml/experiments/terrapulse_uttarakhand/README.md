# TerraPulse SIH 2026 — ML Model & System Flow

> **Project:** TerraPulse
> **SIH Problem:** Flash Flood Prediction System for Hilly Regions using Multi-Source Data
> **Primary working region:** Uttarakhand
> **Future hill regions:** Himachal Pradesh, Sikkim, Arunachal Pradesh, Jammu & Kashmir, Ladakh

---

## 1. Purpose of This README

This document explains exactly:

- what data TerraPulse receives,
- how the data is transformed into model features,
- how the ML model produces a flood-risk result,
- what the backend API returns,
- what the dashboard displays,
- which parts are currently ML-powered,
- and how the additional Himalayan hill regions are being represented in the prototype.

The purpose is to keep the **ML team, backend team, frontend team, and SIH presentation** aligned to the same architecture.

---

# 2. Current TerraPulse Architecture

```text
                    USER / DASHBOARD
                           |
                           v
              +---------------------------+
              | Input Environmental Data  |
              +---------------------------+
                           |
             +-------------+-------------+
             |                           |
             v                           v
      30-Day Rainfall              Soil Moisture
             |                           |
             +-------------+-------------+
                           |
                           v
                  Feature Engineering
                           |
                           v
                 Uttarakhand ML Model
                           |
              +------------+------------+
              |                         |
              v                         v
       Logistic Regression       Random Forest
              |                         |
              +------------+------------+
                           |
                           v
                  Average Probability
                           |
                           v
                    Risk Threshold
                       0.30
                           |
            +--------------+--------------+
            |              |              |
            v              v              v
           LOW          MODERATE         HIGH
            |              |              |
            +--------------+--------------+
                           |
                           v
                    Early Warning
                           |
                           v
                     Dashboard UI
```

---

# 3. Primary ML Region: Uttarakhand

The **currently working ML prediction flow is Uttarakhand-focused**.

The dashboard supports the 13 Uttarakhand districts:

1. Almora
2. Bageshwar
3. Chamoli
4. Champawat
5. Dehra Dun
6. Haridwar
7. Naini Tal
8. Pauri Garhwal
9. Pithoragarh
10. Rudra Prayag
11. Tehri Garhwal
12. Udham Singh Nagar
13. Uttarkashi

The current map uses the Uttarakhand district GeoJSON and the selected district is highlighted on the risk map.

---

# 4. Data Given to the Current Prediction API

The current Flask API endpoint is:

```text
POST http://127.0.0.1:5000/predict
```

## Required input

The frontend sends three primary inputs:

```json
{
  "district": "Chamoli",
  "rainfall_history": [
    5, 8, 12, 0, 4, 7, 15, 10, 3, 0,
    6, 9, 11, 14, 5, 2, 8, 13, 20, 18,
    4, 6, 9, 12, 15, 22, 30, 40, 55, 80
  ],
  "soil_moisture": 0.32
}
```

## Input meaning

### `district`

The selected Uttarakhand district.

Example:

```text
Chamoli
```

### `rainfall_history`

Exactly **30 daily rainfall observations**, ordered from oldest to newest.

Example:

```text
Day 1 ... Day 30
```

The backend derives multiple rainfall features from these 30 values.

### `soil_moisture`

A normalized soil-moisture value between:

```text
0 and 1
```

Example:

```text
0.32
```

---

# 5. Input Validation

The backend validates the following conditions before prediction:

- district must be present,
- district must be valid,
- rainfall history must be a list,
- exactly 30 rainfall values must be provided,
- rainfall values must be numeric,
- rainfall values cannot be negative,
- soil moisture must be numeric,
- soil moisture must be between 0 and 1.

Invalid input returns an API error instead of running the model.

---

# 6. Feature Engineering

The 30-day rainfall series is converted into model-ready rainfall features.

Current rainfall-derived features include:

```text
rainfall_1d
rainfall_3d
rainfall_7d
rainfall_14d
rainfall_30d
rainfall_max_3d
rainfall_max_7d
rainy_days_7d
rainfall_1d_to_7d
rainfall_3d_to_7d
```

Additional district-level features come from the terrain data:

```text
soil_moisture
mean_elevation
mean_slope
district
```

The working V1 prediction interface therefore expects the following 14 model-facing fields:

```text
rainfall_1d
rainfall_3d
rainfall_7d
rainfall_14d
rainfall_30d
rainfall_max_3d
rainfall_max_7d
rainy_days_7d
rainfall_1d_to_7d
rainfall_3d_to_7d
soil_moisture
mean_elevation
mean_slope
district
```

---

# 7. Model Architecture

The current prediction architecture is an ensemble of two classifiers.

## Model 1 — Logistic Regression

- Logistic Regression classifier
- Balanced class weighting
- Numeric features scaled
- District handled as a categorical feature

## Model 2 — Random Forest

- Random Forest classifier
- Balanced class weighting
- Multiple decision trees
- District handled as a categorical feature

## Ensemble

Both models produce a probability for the positive flood class.

```text
Logistic Probability
        +
Random Forest Probability
        |
        v
      / 2
        |
        v
Ensemble Flood Probability
```

The current backend uses **average probability** as the ensemble method.

---

# 8. Risk Classification

The current configured threshold is:

```text
0.30 = 30%
```

The risk logic is:

```text
Probability >= 0.30
        -> HIGH

Probability >= 0.15 and < 0.30
        -> MODERATE

Probability < 0.15
        -> LOW
```

The dashboard therefore converts the model probability into a user-facing risk level.

---

# 9. What the Model Outputs

The `/predict` endpoint returns the model result in JSON form.

Representative structure:

```json
{
  "project": "TerraPulse SIH 2026",
  "district": "Chamoli",
  "probability": 0.4535,
  "probability_percent": 45.35,
  "risk_level": "HIGH",
  "warning": "Flash flood risk detected. Early warning recommended.",
  "threshold": 0.3,
  "model": "Ensemble",
  "model_version": "V1",
  "lead_target": "3 Days",
  "logistic_probability": 0.907,
  "random_forest_probability": 0.0,
  "features_used": { },
  "environment": { }
}
```

## Important output fields

### Probability

The ensemble flood probability.

Example:

```text
0.4535
```

or:

```text
45.35%
```

### Risk level

One of:

```text
LOW
MODERATE
HIGH
```

### Warning

A human-readable message based on the risk level.

### Threshold

Current configured decision threshold:

```text
30%
```

### Model

Current model label:

```text
Ensemble
```

### Lead target

Current dashboard label:

```text
Up to 3 Days
```

---

# 10. Environmental Context Returned to the Dashboard

The backend also returns an `environment` object containing broader environmental context.

The dashboard currently exposes:

```text
Rainfall
Soil
Terrain
River
Weather
```

## Rainfall context

The dashboard shows:

- 1-day rainfall
- 3-day rainfall
- 7-day rainfall
- 14-day rainfall
- 30-day rainfall
- rainfall chart
- cumulative rainfall
- rainfall build-up
- rainy-day count

## Soil context

The dashboard shows the soil-moisture value and a visual moisture indicator.

## Terrain context

The dashboard shows:

- mean elevation,
- mean slope,
- slope risk.

## River context

The dashboard currently shows:

- river water level,
- river danger level,
- level/danger ratio,
- river rise rate,
- river trend.

## Weather context

The dashboard currently shows:

- weather condition,
- temperature,
- humidity,
- wind speed,
- atmospheric pressure.

---

# 11. Important Distinction: Model Inputs vs Environmental Context

This distinction is critical for technical correctness.

The current V1 model prediction interface is based on:

```text
Rainfall-derived features
Soil moisture
Elevation
Slope
District
```

The current dashboard also displays:

```text
River level
River rise rate
Temperature
Humidity
Wind
Pressure
Weather condition
```

These additional values are currently **environmental context / prototype simulation inputs** and should not automatically be described as direct model features unless the trained model is explicitly retrained to use them.

Therefore, presentations should say:

> **Multi-source environmental monitoring + ensemble flood-risk prediction**

rather than claiming that every dashboard signal is directly consumed by the current V1 model.

---

# 12. Current Prototype Data Notice

The current river and weather values used by the prototype backend are synthetic demonstration values.

They must not be presented as:

- live CWC observations,
- live IMD observations,
- official disaster-warning values,
- or operational forecast results.

Recommended UI wording:

> **Prototype data:** River and weather values shown in the current demonstration are simulated inputs and are not live CWC/IMD observations.

---

# 13. Model Training Work Completed

The model-development work completed so far includes:

### Dataset and data workflow

- cleaned ML datasets were created,
- target/leakage audits were performed,
- train/validation/test splits were checked,
- temporal ordering was checked,
- feature types were validated,
- model-ready datasets were produced.

### Baseline work

Two baseline models were trained:

```text
Logistic Regression
Random Forest
```

The baseline work produced model comparison reports and model artifacts.

### Uttarakhand V2 research model

A separate Uttarakhand V2 synthetic prototype dataset was created and audited.

Dataset summary:

```text
Rows:              18,616
Columns:           29
Districts:         13
Date range:        2020-01-30 to 2023-12-31
Flood rows:        121
Non-flood rows:    18,495
Flood rate:        0.65%
```

The V2 dataset audit reported:

- zero missing values,
- zero exact duplicates,
- zero date-district duplicates,
- physical-range checks passed,
- no deterministic target copies detected in the audited synthetic environmental variables.

However, the flood target is highly imbalanced and the V2 test performance was not strong enough to describe the model as an operational warning system.

---

# 14. Uttarakhand V2 Model Results

The V2 training experiment produced:

```text
Validation threshold: 0.38
```

Validation metrics:

```text
Accuracy : 0.9031
Precision: 0.0111
Recall   : 0.2778
F1       : 0.0213
ROC-AUC  : 0.6639
PR-AUC   : 0.0074
```

Final 2023 test metrics:

```text
Accuracy : 0.8967
Precision: 0.0343
Recall   : 0.2909
F1       : 0.0613
ROC-AUC  : 0.7880
PR-AUC   : 0.0385
```

Threshold analysis showed there was **no practical threshold that simultaneously achieved strong precision and recall** for the current V2 prototype.

Therefore:

> V2 is a research/prototype artifact and should not be presented as validated operational flood-warning accuracy.

---

# 15. Current Demonstration Path

For the current SIH prototype, the safer presentation flow is:

```text
Uttarakhand
    |
    v
Select District
    |
    v
Enter 30-day rainfall + soil moisture
    |
    v
Backend feature engineering
    |
    v
Ensemble prediction
    |
    v
Flood probability
    |
    v
LOW / MODERATE / HIGH
    |
    v
Interactive dashboard + risk map + explanation
```

The current dashboard has already been connected to the Flask `/predict` endpoint and successfully tested.

---

# 16. Dashboard Input Example

A demonstration can use:

```text
District: Chamoli
Soil Moisture: 0.32

Rainfall History:
5,8,12,0,4,7,15,10,3,0,
6,9,11,14,5,2,8,13,20,18,
4,6,9,12,15,22,30,40,55,80
```

The backend derives the rolling rainfall features automatically.

For this example, the feature-engineering layer produced values such as:

```text
rainfall_1d       = 80.0
rainfall_3d       = 175.0
rainfall_7d       = 254.0
rainfall_14d      = 332.0
rainfall_30d      = 443.0
rainy_days_7d     = 7
soil_moisture      = 0.32
mean_elevation     = 3582.92 m
mean_slope         = 30.56 degrees
```

The current backend test successfully returned a flood-risk prediction and the associated environmental context.

---

# 17. Additional Hill Regions — Presentation Strategy

The SIH problem is focused on **hilly regions**, not only Uttarakhand.

Therefore the final frontend is planned around:

```text
Uttarakhand
Himachal Pradesh
Sikkim
Arunachal Pradesh
Jammu & Kashmir
Ladakh
```

## Current implementation strategy

### Uttarakhand

```text
FULL ML DEMONSTRATION
```

It has:

- district selector,
- trained model integration,
- prediction API,
- rainfall inputs,
- soil input,
- terrain context,
- flood-risk map,
- risk explanation,
- early-warning UI.

### Other hill regions

For the current SIH prototype, the other regions can be represented as:

```text
REGIONAL SITUATION SNAPSHOT
```

rather than claiming unsupported ML predictions.

Potential regions:

```text
Himachal Pradesh
Sikkim
Arunachal Pradesh
Jammu & Kashmir
Ladakh
```

Their frontend can show curated/prototype situational information such as:

- rainfall activity,
- terrain/slope context,
- river condition,
- weather condition,
- regional risk status,
- map visualization.

The UI should clearly distinguish:

```text
MODEL ACTIVE
```

from:

```text
REGIONAL SNAPSHOT
```

---

# 18. Recommended Multi-Region Dashboard Flow

```text
                    TERRAPULSE
                         |
                   REGION SELECT
                         |
       +-----------------+------------------+
       |                 |                  |
       v                 v                  v
 Uttarakhand        Himachal             Sikkim
       |             Pradesh               |
       |                 |                  |
       v                 v                  v
  ML Prediction    Situation View     Situation View
       |
       v
 District Selection
       |
       v
 Rainfall + Soil + Terrain
       |
       v
 Ensemble ML
       |
       v
 Probability + Risk
```

Future model expansion can then follow the same architecture for the additional hill states.

---

# 19. Current Frontend Components

The current dashboard contains:

```text
1. Environmental Conditions
2. Flood Risk Assessment
3. Flood Probability Gauge
4. Multi-Window Rainfall
5. River / Water Level
6. Current Weather
7. Slope Risk
8. River Trend
9. 30-Day Rainfall Pattern
10. Cumulative Rainfall
11. Terrain Intelligence
12. Environmental Indicators
13. Model Interpretation
14. Early Warning
15. Uttarakhand District Map
16. System Workflow
17. System Status
18. Prototype Data Disclaimer
```

---

# 20. Backend Flow

The current backend structure is:

```text
08_Backend/
├── app.py
├── dashboard_predict.py
└── requirements.txt
```

### `dashboard_predict.py`

Responsible for:

- validating district,
- reading district terrain data,
- calculating rainfall features,
- combining rainfall + soil + terrain values,
- producing the model-ready feature dictionary.

### `app.py`

Responsible for:

- loading model artifacts,
- exposing `/health`,
- exposing `/predict`,
- validating incoming JSON,
- running the ensemble,
- assigning risk level,
- returning dashboard-ready JSON.

---

# 21. Model Artifacts

The model directory currently contains multiple research and production/prototype artifacts.

Important current V1 runtime artifacts include:

```text
07_Models/
├── ensemble_logistic_model.joblib
├── ensemble_random_forest_model.joblib
├── final_model_config.json
└── predict_flood_risk.py
```

The Uttarakhand V2 experimental artifacts include files such as:

```text
ensemble_v2_logistic_model.joblib
ensemble_v2_random_forest_model.joblib
ensemble_v2_threshold.txt
final_model_v2_config.json
ensemble_v2_test_predictions.csv
```

These should be kept distinguishable from the currently connected V1 runtime model.

---

# 22. API Health Check

The backend health endpoint is:

```text
GET http://127.0.0.1:5000/health
```

A successful response confirms that the backend and configured model are loaded.

Example:

```json
{
  "model": "Ensemble",
  "model_loaded": true,
  "model_version": "V1",
  "region": "Uttarakhand",
  "status": "healthy",
  "threshold": 0.3
}
```

---

# 23. Demo Run Order

## Start backend

```powershell
python 08_Backend/app.py
```

## Open dashboard

Run the frontend through VS Code Live Server or another static web server.

## Check backend

Open:

```text
http://127.0.0.1:5000/health
```

## Run prediction

Select a district, enter:

- 30 rainfall values,
- soil moisture,

then click:

```text
ANALYZE FLOOD RISK
```

The dashboard sends the values to `/predict` and updates the result cards, charts, warning section, environmental context, and map.

---

# 24. How to Explain the Model to a Mentor/Judge

Recommended explanation:

> TerraPulse is a mountain-region flood-risk intelligence platform. Our primary working ML region is Uttarakhand. The system accepts a selected district, 30 days of rainfall history, and soil moisture. The backend converts the rainfall history into multiple temporal features such as 1-day, 3-day, 7-day, 14-day and 30-day accumulation, combines them with district terrain information, and sends the feature vector through Logistic Regression and Random Forest models. Their probabilities are averaged to obtain the ensemble flood probability. A configurable threshold is then used to classify the risk as Low, Moderate, or High. The dashboard additionally presents broader environmental context such as river and weather conditions, while clearly distinguishing prototype-simulated environmental values from actual live observations.

---

# 25. What Is Completed

```text
Data cleaning / preparation       ✅
Leakage / target audit            ✅
Temporal split validation         ✅
Baseline model training           ✅
Ensemble architecture             ✅
Uttarakhand model integration     ✅
Flask prediction API              ✅
API health check                  ✅
API prediction test               ✅
Dashboard integration             ✅
Rainfall analytics                ✅
Terrain intelligence              ✅
River prototype context           ✅
Weather prototype context         ✅
Uttarakhand risk map              ✅
Early-warning UI                  ✅
```

---

# 26. Current Limitations

The current system is a **research and demonstration prototype**, not an operational disaster-warning system.

Current limitations include:

- V1 prediction is primarily demonstrated for Uttarakhand.
- River and weather values currently shown in the prototype are simulated inputs.
- The current V2 synthetic training experiment has limited predictive performance.
- Additional hill states do not yet have equivalent validated ML models.
- Official operational warning decisions must rely on authoritative government and forecasting systems.

---

# 27. Future Expansion Plan

```text
PHASE 1
Uttarakhand
    ↓
Working ML Demonstration

PHASE 2
Himachal Pradesh
Sikkim
Arunachal Pradesh
Jammu & Kashmir
Ladakh
    ↓
Regional Data + Feature Pipelines

PHASE 3
Multi-Hill-State ML
    ↓
Unified TerraPulse Platform
```

The frontend is being designed so that new states can be added through configuration and region-specific map/data modules rather than rewriting the entire application.

---

# 28. Core Message

TerraPulse is not just a single ML prediction page.

It is intended as a **multi-source mountain flood intelligence platform** combining:

```text
Rainfall
+
Soil Moisture
+
Terrain
+
River Context
+
Weather Context
+
Geospatial Risk Map
+
Ensemble Machine Learning
+
Early Warning Interface
```

The current strongest validated demonstration path is **Uttarakhand**, while the frontend is being prepared to scale to additional Himalayan hill regions.

---

## 29. One-Line Summary

> **TerraPulse converts rainfall, soil, terrain and district information into an ensemble flood-risk probability for Uttarakhand, enriches the result with broader environmental context, visualizes risk geographically, and provides a scalable foundation for future Himalayan hill-state expansion.**

---

**Prototype notice:** TerraPulse is a research and demonstration prototype. Current river/weather values are simulated demonstration inputs and are not live CWC/IMD observations or official disaster warnings.
