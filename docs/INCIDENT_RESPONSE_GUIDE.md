# FlowShield Incident Response Guide (v2.5)

**Operational Domain:** Mandi District Flash Flood Early Warning System  
**Audience:** Emergency Response Leads, Incident Commanders, Duty Officers, ML Reliability Engineers  
**Classification:** Operational Safety Standard  

---

## 1. Incident Severity Classifications

| Severity | Incident Definition | Trigger Conditions | Maximum Response SLA | Target MTTR |
|---|---|---|---|---|
| **P1 - CRITICAL** | Full system failure, model corruption, or total upstream telemetry loss | Checksum mismatch (`MODEL_ARTIFACT_INVALID`), HTTP 500 on `/predictions`, or zero sensor updates for >2 hours during active monsoon | **15 minutes** | **< 60 seconds** (Rollback) |
| **P2 - HIGH** | Significant covariate drift, spatial node failure, or calibration degradation | `DRIFT_ALERT` status (PSI $\ge 0.25$), >3 regional stations offline, or sudden false positive surge | **30 minutes** | **< 2 hours** |
| **P3 - MEDIUM** | Mild telemetry delay, minor API latency increase, or single sensor anomaly | `MONITORING` drift level, API p99 latency > 250ms, or single village station reading stale | **2 hours** | **< 6 hours** |

---

## 2. P1 Incident Playbook: Model Corruption or Integrity Failure

### Immediate Symptoms
- Dashboard shows red banner: *"Model Unavailable / Degraded State"*
- `/health` endpoint returns `"model": {"loaded": false}`
- Logs display: `Checksum mismatch for v2_selected_model.joblib`

### Response Procedure
1. **Declare Incident:** Notify EOC Commander that ML automated inference is temporarily degraded; default conservative risk protocols engaged.
2. **Execute Emergency Rollback:**
   ```bash
   python scripts/rollback_to_baseline.py
   ```
3. **Verify Restoration:**
   ```bash
   python -c "from apps.api.app.services.model_integrity import model_integrity_checker; print(model_integrity_checker.verify_integrity())"
   ```
   Confirm output displays `MODEL_READY`.
4. **Broadcast Notification:** Issue all-clear to EOC; automated predictions restored.

---

## 3. P2 Incident Playbook: Significant Covariate Drift Alert

### Immediate Symptoms
- `/api/v1/system/drift` triggers `DRIFT_ALERT`
- $\ge 2$ features exceed $Z \ge 2.5$ or overall $\text{PSI} \ge 0.25$

### Response Procedure
1. **Inspect Drift Vectors:** Run detailed drift diagnostic:
   ```bash
   python -c "from apps.api.app.database import SessionLocal; from apps.api.app.services.drift_monitor import drift_monitor; db = SessionLocal(); res = drift_monitor.compute_drift_metrics(db); db.close(); print(res['drifted_features'])"
   ```
2. **Cross-Check Real Weather:** Validate whether drift corresponds to an extreme meteorological event (e.g. 150mm cloudburst event in Aut or Larji) or sensor hardware failure.
3. **Hardware vs Climate:**
   - If real extreme weather: **Do not rollback**. The model is operating in extreme hazard territory. Operational policy score will escalate to `CRITICAL` alert appropriately.
   - If sensor malfunction (e.g. rain gauge stuck reporting 999mm): mark station `data_quality_status = "DEGRADED"` in database, which caps operational risk and isolates faulty sensor.

---

## 4. Escalation Matrix

| Role | Responsibility | Contact Channel |
|---|---|---|
| **Incident Commander** | Evacuation & tactical responder decisions | Radio / Secure Hotline |
| **Lead ML Engineer** | Model verification, retraining, rollback | PagerDuty / Telegram Ops |
| **SRE Lead** | Server uptime, API health, database sync | SRE Emergency Bridge |
| **District Liaison** | District Magistrate & SDMA coordination | Emergency Dispatch Phone |

---

## 5. Post-Incident Review (PIR) Protocol

Within 24 hours of resolving any P1 or P2 incident:
1. Preserve all logs under `brain/<conversation-id>/.system_generated/logs/` and database snapshots.
2. Complete Post-Incident Review document including root cause, timeline of events, detection latency, time to resolution, and preventative actions.
3. Update `EXPECTED_CHECKSUMS` and tests if new edge cases were identified.
