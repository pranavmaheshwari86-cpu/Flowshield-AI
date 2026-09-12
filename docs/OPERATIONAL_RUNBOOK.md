# FlowShield Production Operational Runbook (v2.5)

**System:** FlowShield Flash Flood Decision Support System  
**Audience:** Site Reliability Engineers (SRE), MLOps Engineers, Incident Commanders, Emergency Operations Centers (EOC)  
**Last Updated:** September 2026  
**Status:** Active Production  

---

## 1. Routine Health & Telemetry Verification

### 1.1 Core Health Endpoints
Verify all system subsystems via the automated health endpoints:

| Endpoint | Method | Expected Output | Purpose |
|---|---|---|---|
| `/health` | `GET` | `{"status": "healthy", "model": {"loaded": true}}` | Basic liveness and model presence |
| `/api/v1/system/status` | `GET` | Full telemetry and simulation status | Verifies database, 15-feature telemetry count, and model version |
| `/api/v1/system/drift` | `GET` | Population Stability Index (PSI) & Z-shifts | Evaluates covariate shift across 15 features |

### 1.2 Verification Command
```bash
curl -s http://localhost:8000/api/v1/system/status | jq .model
```
Expected output:
```json
{
  "status": "loaded",
  "version": "flowshield-flood-risk-v2 (xgb-v1-compatible)",
  "feature_count": 15,
  "drift_level": "HEALTHY",
  "drift_score": 0.02
}
```

---

## 2. Drift Monitoring & Covariate Shift Triage

FlowShield continuously tracks live 48-hour telemetry distributions against frozen training baseline deciles and histograms stored in `ml/reports/drift_baseline_reference.json`.

### 2.1 Drift Triage Matrix

| Drift Level | PSI Range / Trigger | Severity | Operational Response |
|---|---|---|---|
| **HEALTHY** | $\text{PSI} < 0.10$ and $Z < 1.5$ | Green | Routine monitoring. No action required. |
| **MONITORING** | $0.10 \le \text{PSI} < 0.25$ or single feature $Z \ge 1.5$ | Yellow | Inspect weather radar for localized seasonal anomalies. Check sensor calibration. |
| **DRIFT_ALERT** | $\text{PSI} \ge 0.25$ or $\ge 2$ features drifted ($Z \ge 2.5$) | Orange | Trigger MLOps review. Evaluate recent rainfall sensor telemetry for physical drift or sensor displacement. Schedule pipeline re-tuning. |

### 2.2 Re-computing Baseline Histograms
If permanent climate or station network changes occur:
```bash
python scripts/generate_drift_baseline.py
```

---

## 3. Emergency Model Rollback Playbook (<60s MTTR)

If model corruption, runtime inference latency spike, or unexpected edge-case failure occurs:

### 3.1 Step 1: Execute Instantaneous Rollback
Execute the certified rollback script from the repository root:
```bash
python scripts/rollback_to_baseline.py
```
This command automatically:
1. Restores verified Phase 0 baseline model, calibrator, preprocessor, and manifest from `ml/models/baseline_backup/`.
2. Restores baseline `EXPECTED_CHECKSUMS` in `apps/api/app/services/model_integrity.py`.
3. Runs `ModelIntegrityChecker` to verify `MODEL_READY` status.
4. Execution SLA: **< 10 seconds** (Verified MTTR: 0.02s).

### 3.2 Step 2: Verify Backend Status
```bash
curl -s http://localhost:8000/health
```
Ensure `"status": "healthy"` and `"loaded": true`.

---

## 4. Retraining & Promotion Workflow

When new ground-truth seasonal flood observations are validated by the district administration:

### 4.1 Ingestion & Splitting
1. Append new observations to `data/real/mandi_real_hydrology_features.csv`.
2. Generate fresh chronological non-overlapping splits:
   ```bash
   python scripts/compile_historical_flood_inventory.py
   ```

### 4.2 Candidate Tournament & Calibration
1. Run multi-model tournament across candidates:
   ```bash
   python ml/training/run_tournament.py
   ```
2. Fit isotonic calibration on calibration split:
   ```bash
   python ml/training/run_calibration.py
   ```
3. Optimize decision threshold $\tau$:
   ```bash
   python ml/training/run_threshold_optimization.py
   ```

### 4.3 Atomic Promotion
Promote the winning candidate to production:
```bash
python scripts/promote_model.py
```
Verify output confirms `Model Integrity State: MODEL_READY`.

---

## 5. Automated Regression Test Suite

Always execute the regression suite before deploying changes to staging or production:
```bash
pytest tests/ -v
```
All 11 test cases across `test_ml_pipeline.py`, `test_simulation_regression.py`, and `test_adversarial_telemetry.py` must pass with 0 failures.
