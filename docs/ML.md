# Flowshield — Machine Learning & Explainability Documentation

## 1. Overview
Flowshield models flash flood risk in mountainous terrains using an **XGBoost (Extreme Gradient Boosting)** binary classification model coupled with a local **SHAP (SHapley Additive exPlanations)** TreeExplainer.

## 2. Feature Schema & Canonical Contract
All components strictly adhere to the 12-feature schema defined in `ml/feature_schema.py`:

| Feature | Unit | Min | Max | Physical Significance |
|---|---|---|---|---|
| `rainfall_1h` | mm | 0.0 | 200.0 | Short-term cloudburst rainfall accumulation |
| `rainfall_3h` | mm | 0.0 | 350.0 | Intermediate storm volume |
| `rainfall_6h` | mm | 0.0 | 500.0 | Prolonged precipitation volume |
| `rainfall_24h` | mm | 0.0 | 800.0 | Total antecedent rainfall |
| `rainfall_intensity` | mm/hr | 0.0 | 120.0 | Instantaneous precipitation rate |
| `soil_moisture` | % | 0.0 | 100.0 | Catchment saturation level |
| `river_level` | m | 0.5 | 18.0 | River stage height at nearest gauge |
| `river_level_change` | m/hr | -3.0 | 6.0 | Gauge surge velocity |
| `elevation` | m | 300.0 | 3500.0 | Settlement elevation above sea level |
| `slope` | deg | 0.0 | 60.0 | Catchment terrain inclination |
| `distance_to_river` | km | 0.02 | 20.0 | Distance to nearest major watercourse |
| `historical_flood_frequency`| 0-1 | 0.0 | 1.0 | Annualized empirical flood recurrence probability |

## 3. Training & Evaluation Methodology
- **Split**: Stratified 80/20 train/test split.
- **Leakage Elimination**: Tree models operate directly on unscaled features, completely removing fitted scaler leakage.
- **Honest Metric Reporting**: Evaluated on held-out test data. Accuracy, Precision, Recall, F1 Score, and ROC-AUC are calculated directly and persisted to `model_metadata.json`.
- **Reproducibility**: Global seed `26192` ensures identical train/test splits and weight initialization.

## 4. Explainable AI with SHAP
- Uses `shap.TreeExplainer(model)`.
- For each prediction, local feature attribution values sum up to the model's margin output:
  $$f(x) = E[f(x)] + \sum_{i=1}^{M} \phi_i$$
- **Operational Wording**: Labeled **"Top Predictive Contributors"** in all user interfaces, disclaiming physical causation.

## 5. Scientific Limitations & Synthetic Data Disclosure
- All training and demonstration data is **synthetic**, generated via physically grounded hydrological simulation.
- Not calibrated against verified real-world telemetry from CWC or IMD. Future integrations will ingest live government telemetry via the standardized `source` schema.
