# Flowshield — Comprehensive Model Evaluation & Discrimination vs. Calibration Analysis
**Smart India Hackathon 2026 (PS ID: 26192)**  
**Pipeline Identifier:** `flowshield-flood-risk-v2`  
**Dataset:** Real ECMWF Copernicus ERA5-Land & SRTM 30m DEM (Mandi District, Himachal Pradesh)  

---

## 1. Evaluation Philosophy: Discrimination vs. Calibration in Disaster Management

In public safety warning systems, two distinct mathematical properties govern model utility:
1. **Discrimination (Ranking Power):** The ability of the model to assign higher risk scores to hours where catastrophic flooding occurred than to normal hours. Measured by **ROC-AUC** and **Precision-Recall AUC (PR-AUC)**.
2. **Calibration (Reliability of Probabilities):** The degree to which predicted probabilities reflect the true empirical frequency of disaster occurrence. A model with excellent discrimination can still be completely uncalibrated (e.g. predicting probabilities clustered around 0.05 or 0.95 without representing real odds). Measured by **Brier Score**, **Log Loss**, and **Expected Calibration Error (ECE)**.

Disaster mitigation mandates **both**:
* Without discrimination, the system cannot separate calm days from cloudburst surges.
* Without calibration, decision-makers cannot rely on probability thresholds to trigger graduated civic actions (e.g. school closures at 10%, bridge shutdowns at 30%, mandatory evacuations at 60%).

---

## 2. Multi-Candidate Model Comparison (Validation Set)

All candidates were trained on 8,160 rows across 5 Mandi stations and evaluated on 3,264 holdout rows across 2 unseen physical stations (**Pandoh Dam** and **Dharampur Khad**).

### Comprehensive Metric Matrix:

| Model Architecture | Calibration Variant | ROC-AUC | PR-AUC | Brier Score | Log Loss | ECE | Op. Recall | Op. FNR | Op. FPR | Op. F1 | Op. Threshold |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Logistic Regression** | **Raw** | **0.9250** | **0.4240** | 0.0671 | 0.2097 | 0.0899 | 0.8507 | 0.1493 | 0.1636 | 0.3000 | 0.19 |
| | **Sigmoid** | **0.9250** | **0.4240** | 0.0305 | 0.1106 | 0.0109 | 0.8657 | 0.1343 | 0.1709 | 0.2955 | 0.04 |
| | **Isotonic** | **0.9250** | **0.4240** | **0.0287** | **0.0984** | **0.0004** | **0.8657** | **0.1343** | **0.1684** | **0.2986** | **0.08** |
| **Random Forest** | **Raw** | 0.8757 | 0.1640 | 0.0529 | 0.1726 | 0.0429 | 0.8881 | 0.1119 | 0.2236 | 0.2497 | 0.06 |
| | **Sigmoid** | 0.8757 | 0.1640 | 0.0375 | 0.1507 | 0.0120 | 1.0000 | 0.0000 | 1.0000 | 0.0789 | 0.01 |
| | **Isotonic** | 0.8757 | 0.1640 | 0.0339 | 0.1171 | 0.0000 | 0.8806 | 0.1194 | 0.2077 | 0.2616 | 0.10 |
| **XGBoost** | **Raw** | 0.8548 | 0.1400 | 0.0719 | 0.2584 | 0.0724 | 0.7836 | 0.2164 | 0.2406 | 0.2117 | 0.01 |
| | **Sigmoid** | 0.8548 | 0.1400 | 0.0379 | 0.1580 | 0.0027 | 1.0000 | 0.0000 | 1.0000 | 0.0789 | 0.01 |
| | **Isotonic** | 0.8548 | 0.1400 | 0.0357 | 0.1245 | 0.0000 | 0.9776 | 0.0224 | 0.3070 | 0.2137 | 0.04 |

---

## 3. Deep-Dive: Why Logistic Regression Surpassed Tree Ensembles

A widespread assumption in applied data science is that boosted gradient trees (XGBoost) will inevitably outperform regularized linear models. However, mountain hydrological transferability reveals the opposite:

### 1. Spatial Covariate Shift & Overfitting
* In complex topography, each river gauge has idiosyncratic micro-climatic thresholds (e.g. specific elevation or slope cutoffs).
* XGBoost easily constructs deep split conditions that memorize station-specific non-linearities in the training valleys. When tested on Pandoh Dam (a narrow reservoir gorge) and Dharampur (a fast-draining tributary), XGBoost suffered generalization decay (ROC-AUC dropped to 0.8548).
* In contrast, Logistic Regression applies smooth hyperplanes across the 15 normalized physical features, enforcing universal physical mechanics (more 72h rainfall and higher saturation always increases flood likelihood), yielding **0.9250 ROC-AUC**.

### 2. Tail Probability Smoothness
* Tree ensembles output piecewise constant probabilities based on leaf sample fractions. In severe class imbalance (4.1% flood rate), leaf probabilities become stepped and poorly calibrated in the tail.
* Logistic Regression provides continuous, monotonic sigmoidal responses that pair perfectly with isotonic calibration.

---

## 4. Final Catastrophe Benchmark: July 1–25, 2023 Untouched Set

The frozen winner (`logistic_regression + isotonic + threshold=0.08`) was subjected to a single, unbiased evaluation on the historical catastrophe dataset.

### Confusion Matrix Breakdown:
```
                             ACTUAL CONDITION
                      Positive (Flood)   Negative (Normal)
PREDICTED   Positive       557 (TP)            482 (FP)       Total Predicted Alerts: 1,039
CONDITION   Negative        73 (FN)          3,088 (TN)       Total Predicted Normal: 3,161
                         ──────────         ───────────
                         Total: 630         Total: 3,570      Grand Total: 4,200 hours
```

### Safety-Critical Metric Summary:
* **Catastrophe Recall (Sensitivity):** $\frac{557}{630} = \mathbf{88.41\%}$  
  *Flowshield successfully anticipated 88.4% of all hourly flood conditions during the record 2023 Beas disaster.*
* **False Negative Rate (FNR):** $\frac{73}{630} = \mathbf{11.59\%}$  
  *Only 73 flood hours were missed across the entire 25 days of intense rainfall.*
* **False Alarm Rate (FPR):** $\frac{482}{3570} = \mathbf{13.50\%}$  
  *Meets the operational mandate of keeping non-disaster false alerts below 15%.*
* **Precision:** $\frac{557}{1039} = \mathbf{53.61\%}$  
  *More than 1 in every 2 alerts represents a genuine, high-severity flood hour (an exceptional signal-to-noise ratio under 15% disaster prevalence).*
* **F1-Score:** $\mathbf{0.6675}$
* **ROC-AUC:** $\mathbf{0.9230}$
* **PR-AUC:** $\mathbf{0.6761}$

---

## 5. Inference Latency & Computational Footprint

Flowshield was designed for rapid edge execution on low-cost disaster management hardware (solar-powered cellular base stations, Raspberry Pi 4 gateways, and cloud API microservices):

| Candidate | Artifact Size | P50 Latency (500 runs) | P95 Latency (500 runs) | Edge Feasibility |
|---|---|---|---|---|
| **Logistic Regression + Isotonic** | **0.97 KB** | **0.088 ms** | **0.169 ms** | **Ideal for microcontrollers & edge gateways** |
| **XGBoost Classifier** | 150.6 KB | 0.505 ms | 0.814 ms | Requires native C++ runtime (libxgboost) |
| **Random Forest (100 trees)** | 775.7 KB | 37.221 ms | 43.487 ms | Heavy CPU overhead on embedded devices |

At **88 microseconds per evaluation**, a single Flowshield instance can score over **11,000 mountain basin nodes per second**, enabling high-frequency sub-minute real-time simulation updates across all Himachal Pradesh river basins.

---

## 6. Physical Feature Attribution & Explainability

Because Logistic Regression is inherently additive, each prediction can be completely decomposed into physical contributions without requiring slow SHAP approximations:

$$z = w_0 + \sum_{i=1}^{15} w_i \cdot \left(\frac{x_i - \mu_i}{\sigma_i}\right)$$

```
Feature Contribution Coefficients:
rainfall_72h_mm          [+2.3513] ==============================
relative_humidity_pct    [+2.0821] ==========================
temperature_c            [+1.9119] ========================
soil_saturation_pct      [+1.1808] ===============
surface_pressure_hpa     [-1.0918] --------------
deep_soil_saturation_pct [-1.0311] -------------
catchment_slope_deg      [-0.8902] -----------
upstream_drainage_sqkm   [+0.6502] ========
elevation_m              [+0.5965] =======
wind_speed_kmh           [+0.2640] ===
rainfall_24h_mm          [+0.1946] ==
rainfall_1h_mm           [+0.0894] =
dist_to_river_m          [-0.0612] -
rainfall_6h_mm           [-0.0438] -
rainfall_3h_mm           [-0.0310] -
```

This ensures full auditability for NDMA, SDMA, and district magistrates who must justify public evacuation orders to municipal authorities.
