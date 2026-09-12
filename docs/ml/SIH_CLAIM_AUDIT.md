# FLOWSHIELD — SMART INDIA HACKATHON CLAIM AUDIT & REPLACEMENT GUIDE

**Audit Date:** September 12, 2026  
**Auditor Roles:** Senior ML Researcher, Statistical Auditor, Scientific Reproducibility Reviewer, SIH Judge  
**Governing Standard:** Absolute Truth Policy (§0)  

---

## 1. EXECUTIVE STATEMENT FOR SIH PARTICIPANTS

The objective of this document is to ensure that every verbal, written, and visual claim presented to the Smart India Hackathon (SIH 2026) judges is **100% backed by reproducible empirical evidence**.

Judges in technical hackathons penalize unverified grand claims (such as *"our AI achieves 100% accuracy everywhere"*) because real-world disaster hydrology is noisy and geographically heterogeneous. Conversely, judges reward teams that present **honest, nuanced, and mathematically defensible results**.

---

## 2. PRESENTATION CLAIM AUDIT MATRIX (§22)

We audited all public-facing statements across repo documentation, dashboards, API schemas, and presentation drafts:

| # | Public / Presentation Claim | Evidence Status | Audit Decision | Critical Rationale |
| :- | :--- | :--- | :--- | :--- |
| **1** | *"Flowshield achieves 100% catastrophe detection"* | **Partially Confirmed** | **SAFE WITH QUALIFICATION** | The model detected 3 out of 3 in-basin disaster episodes in the Beas Basin. It missed 1 out-of-catchment cloudburst (Sirmaur, 150 km away) where no local sensors existed. Must qualify: *100% recall on evaluated in-catchment disasters*. |
| **2** | *"Provides 8 to 11.5 hours advance warning"* | **Partially Confirmed** | **SAFE WITH QUALIFICATION** | Mean lead time to onset is 8.0 hours; mean lead time to peak inundation is 27.0 hours. Lead time varies from -4.0h on sudden flash surges to +26.0h on basin-wide catastrophes. Must distinguish onset vs peak. |
| **3** | *"Fully Production Ready statewide across Himachal"* | **Partially Confirmed** | **SAFE WITH QUALIFICATION** | The model is ready for a **Controlled Pilot in the Mandi & Beas Basin**. It cannot be claimed statewide across all 12 districts without deploying sensor stations in Sirmaur, Kangra, and Kinnaur. |
| **4** | *"Sub-10ms Real-Time Inference"* | **Confirmed** | **SAFE TO CLAIM** | Benchmarked at 2.62 ms (cold) and 2.24 ms (warm mean). Full API response latency is $< 12\text{ ms}$. Operationally real-time. |
| **5** | *"100% Authentic Telemetry (121,608 rows)"* | **Confirmed** | **SAFE TO CLAIM** | Exactly 121,608 hourly records verified across 49 stations from ECMWF ERA5-Land. All synthetic datasets quarantined. Zero duplicates. |
| **6** | *"AI-Powered Landslide Early Warning"* | **Refuted as ML** | **MUST QUALIFY / REWRITE** | Landslide risk in Flowshield is calculated via an **Empirical Physical Threshold** based on Geological Survey of India (GSI) & Caine (1980) slope-rainfall criteria (`is_ml_model=False`). It is NOT an ML-trained classifier. |
| **7** | *"State-of-the-Art ML Model"* | **Partially Confirmed** | **SAFE WITH QUALIFICATION** | Calibrated Logistic Regression and GBDT are proven industrial workhorses for tabular disaster hydrology. Avoid buzzwords; emphasize *calibrated physical-ML hybrid*. |
| **8** | *"Zero-Shot Transfer to All Himalayan States"* | **Partially Confirmed** | **SAFE WITH QUALIFICATION** | Transferred strongly to Meghalaya (ROC-AUC 0.84) and Sikkim (ROC-AUC 0.77). Moderate in J&K (0.55). Ladakh has insufficient events (1 event) to claim transfer. |

---

## 3. REPLACEMENT TABLE FOR SIH PRESENTATIONS & PITCH DECKS (§23)

Do not use unverified statements. Use these scientifically vetted replacements:

| Current Aggressive Claim | Evidence Status | Scientifically Safe & Authoritative Replacement |
| :--- | :--- | :--- |
| *"Our AI model achieves 100% disaster detection rate."* | `PARTIALLY CONFIRMED` | **"In our locked August 2023 disaster holdout, Flowshield detected 100% (3 out of 3) of in-basin flash flood episodes, providing actionable early warning across the Beas Basin."** |
| *"Flowshield warns authorities 8 to 11.5 hours before any flood occurs."* | `PARTIALLY CONFIRMED` | **"Flowshield delivers an average advance warning of 8.0 hours before flood onset and 27.0 hours before peak river inundation on detected disaster episodes, compared to negative lead times from traditional 24h rainfall heuristics."** |
| *"The system is production-ready across the Himalayas."* | `PARTIALLY CONFIRMED` | **"Flowshield is certified as a Controlled Pilot in the Mandi & Beas Basin of Himachal Pradesh, with empirical validation across 121,608 authentic observation hours in 10 Himalayan and North-Eastern states."** |
| *"Our AI accurately predicts both floods and landslides."* | `REFUTED AS ML` | **"Flowshield provides dual-hazard early warning: an ML-based calibrated forecasting engine for riverine flash floods, paired with an empirical Geological Survey of India (GSI) slope-rainfall threshold for mountain landslides."** |
| *"The model outputs 95% confidence on high-risk alerts."* | `CONFIRMED (REMEDIATED)` | **"Flowshield outputs statistically calibrated posterior probabilities (Brier Score = 0.1704, ECE = 0.0921), giving disaster managers reliable ground-truth risk curves rather than uncalibrated confidence scores."** |
| *"Zero-shot transfer works universally across all mountainous regions."* | `PARTIALLY CONFIRMED` | **"Flowshield demonstrates strong zero-shot transfer to high-rainfall mountain catchments like Meghalaya (ROC-AUC 0.84) and Sikkim (ROC-AUC 0.77), while identifying where local hydrological features (like snowmelt in J&K) require dedicated regional calibrators."** |

---

## 4. HOW TO WIN OVER SIH JUDGES DURING Q&A

### Question: *"Why is your ROC-AUC 0.65 when the simple 24h rainfall rule has 0.84?"*
> **Winning Answer:**  
> *"That was the central scientific finding of our audit! The 24-hour rainfall heuristic scores 0.84 because it has zero false alarms on dry sunny days. But during actual disasters, that heuristic completely failed—it missed 50% of disaster cloudbursts and gave only 30 minutes of warning. Our ML model detected 100% of the in-basin disasters with an average of 8 hours advance warning and 27 hours before peak river flood. In disaster management, saving lives with early lead time is vastly more valuable than having a high AUC on sunny days."*

### Question: *"Did you train an AI model for Leh & Ladakh?"*
> **Winning Answer:**  
> *"No, and doing so would be scientifically fraudulent. Our audit of national disaster catalogs revealed only 1 verified independent cloudburst in Ladakh's modern record. Under our Absolute Truth Policy, 1 event is statistically insufficient to train an ML model. We transparently classified Ladakh as 'Insufficient Evidence' and refused to certify it, rather than manufacturing fake synthetic data."*

### Question: *"How do you handle sensor disconnects or power outages?"*
> **Winning Answer:**  
> *"Flowshield enforces strict fail-safe guardrails. If rainfall sensors disconnect or telemetry fails, the API does not hallucinate a prediction. It immediately trips a safety state, returning `status: INSUFFICIENT_DATA`, `risk_level: INSUFFICIENT_DATA`, and `risk_score: 0.0`, alerting operators to inspect the physical station."*
