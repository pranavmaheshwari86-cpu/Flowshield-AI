"""
apps/api/app/services/scenarios/scenario_runner.py
Flowshield — Deterministic Scenario Replay Runner (v2.4)

Provides reproducible, scientifically honest demonstration replay of multi-hazard
disaster scenarios with pinned random seeds, logical clock ticks, and cryptographic
state verification (SHA-256 trace digest).
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from ...models.village import Village
from ...models.shelter import Shelter
from ...models.route import Route
from ...models.alert import Alert
from ..model_integrity import model_integrity_checker
from ..prediction_service import prediction_service
from ..risk_engine import risk_engine
from ..alert_engine import alert_engine
from ..route_service import route_service


class ScenarioReplayRunner:
    """
    Deterministic replay harness for Smart India Hackathon demonstrations.
    Executes logical clock progression over simulated catchment telemetry,
    recording an immutable audit trace and computing an execution digest.
    """

    DEFAULT_SEED: int = 26192
    DEFAULT_STEPS: int = 20
    STEP_INTERVAL_MINUTES: int = 15

    def __init__(self, seed: int = DEFAULT_SEED):
        self.seed = seed

    def run_replay(
        self,
        db: Session,
        steps: int = DEFAULT_STEPS,
        seed: Optional[int] = None,
        base_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Executes an isolated, deterministic simulation run across all monitored settlements.
        Returns the step-by-step telemetry trace and a cryptographic SHA-256 fingerprint.
        """
        run_seed = seed if seed is not None else self.seed
        clock = base_time or datetime(2026, 9, 11, 6, 0, 0, tzinfo=timezone.utc)

        # 1. Verify model integrity before running replay
        integrity_ok, msg = model_integrity_checker.verify_integrity()
        if not integrity_ok:
            raise RuntimeError(f"Cannot execute deterministic scenario replay: {msg}")

        villages = db.query(Village).filter(Village.state.ilike("%Uttarakhand%")).order_by(Village.id).all()
        if not villages:
            villages = db.query(Village).order_by(Village.id).all()
        if not villages:
            raise ValueError("No settlement data found in database to replay scenario.")

        replay_trace: List[Dict[str, Any]] = []

        # Replay loop over discrete logical clock ticks
        for step_idx in range(steps):
            step_time = clock + timedelta(minutes=step_idx * self.STEP_INTERVAL_MINUTES)
            stage_idx = step_idx // 4

            # Dedicated PRNG for this step
            rng = np.random.RandomState(run_seed + step_idx * 100)

            step_settlement_records = []
            alerts_in_step = 0

            for v in villages:
                # Geographic modifiers
                river_dist_factor = max(0.0, 1.0 - (float(v.distance_to_river or 250.0) / 4000.0))
                slope_deg = float(v.slope or 28.0)
                elev_m = float(v.elevation or 850.0)

                # Synthetic physical observations based on stage
                if stage_idx == 0:
                    r1h = float(rng.uniform(4.0, 9.0))
                    r24h = float(r1h * 3.5 + rng.uniform(5.0, 12.0))
                    soil = float(np.clip(25.0 + r24h * 0.3, 15.0, 45.0))
                    river_lvl = float(np.clip(1.2 + river_dist_factor * 0.4, 0.8, 2.0))
                    surge = float(rng.uniform(-0.02, 0.05))
                elif stage_idx == 1:
                    r1h = float(rng.uniform(25.0, 45.0) + river_dist_factor * 10.0)
                    r24h = float(r1h * 2.8 + rng.uniform(20.0, 40.0))
                    soil = float(np.clip(45.0 + (step_idx - 4) * 6.0, 40.0, 68.0))
                    river_lvl = float(np.clip(2.0 + (step_idx - 4) * 0.5 * river_dist_factor, 1.5, 3.5))
                    surge = float(rng.uniform(0.2, 0.6) * river_dist_factor)
                elif stage_idx == 2:
                    r1h = float(rng.uniform(45.0, 75.0))
                    r24h = float(120.0 + (step_idx - 8) * 30.0 + rng.uniform(10, 25))
                    soil = float(np.clip(70.0 + (step_idx - 8) * 4.5, 68.0, 88.0))
                    river_lvl = float(np.clip(3.5 + (step_idx - 8) * 0.8 * river_dist_factor, 2.5, 5.8))
                    surge = float(np.clip(0.6 + (step_idx - 8) * 0.3 * river_dist_factor, 0.3, 1.5))
                elif stage_idx == 3:
                    r1h = float(rng.uniform(70.0, 110.0))
                    r24h = float(220.0 + (step_idx - 12) * 45.0 + rng.uniform(15, 30))
                    soil = float(np.clip(88.0 + (step_idx - 12) * 2.0, 85.0, 96.0))
                    river_lvl = float(np.clip(5.5 + (step_idx - 12) * 1.2 * river_dist_factor, 4.0, 8.5))
                    surge = float(np.clip(1.4 + (step_idx - 12) * 0.5 * river_dist_factor, 0.8, 3.2))
                else:  # Stage 4: Critical
                    r1h = float(rng.uniform(90.0, 140.0))
                    r24h = float(380.0 + (step_idx - 16) * 60.0 + rng.uniform(20, 40))
                    soil = float(np.clip(94.0 + (step_idx - 16) * 1.0, 92.0, 99.0))
                    river_lvl = float(np.clip(8.0 + (step_idx - 16) * 1.5 * river_dist_factor, 6.0, 14.5))
                    surge = float(np.clip(2.5 + (step_idx - 16) * 0.8 * river_dist_factor, 1.5, 4.8))

                r3h = float(r1h * 1.8)
                r6h = float(r1h * 2.5)
                intensity = float(r1h * 1.1)

                feature_dict = {
                    "rainfall_1h_mm": round(r1h, 2),
                    "rainfall_3h_mm": round(r3h, 2),
                    "rainfall_6h_mm": round(r6h, 2),
                    "rainfall_24h_mm": round(r24h, 2),
                    "rainfall_72h_mm": round(r24h * 1.5, 2),
                    "soil_saturation_pct": round(soil, 2),
                    "deep_soil_saturation_pct": round(soil * 0.95, 2),
                    "temperature_c": 22.5,
                    "relative_humidity_pct": 82.0,
                    "surface_pressure_hpa": 915.0,
                    "wind_speed_kmh": 14.0,
                    "elevation_m": elev_m,
                    "catchment_slope_deg": slope_deg,
                    "distance_to_river_m": float(v.distance_to_river or 250.0),
                    "drainage_density_km_km2": 1.45,
                }

                # Predict with canonical V2 calibrated pipeline
                calibrated_prob, quality, _ = prediction_service.predict(
                    feature_dict, data_quality_score=1.0, freshness_seconds=10
                )

                # Policy operational risk score
                risk_score, severity, _, _ = risk_engine.compute_operational_risk(
                    flood_probability=calibrated_prob,
                    trend_factor=1.0 + (0.05 * step_idx),
                    vulnerability_index=float(v.vulnerability_index or 0.5),
                    data_quality_score=1.0,
                    freshness_seconds=10,
                )

                if severity in ("HIGH", "CRITICAL"):
                    alerts_in_step += 1

                step_settlement_records.append({
                    "village_id": str(v.id),
                    "calibrated_prob": round(float(calibrated_prob), 4),
                    "risk_score": round(float(risk_score), 2),
                    "severity": severity,
                })

            step_settlement_records.sort(key=lambda x: x["village_id"])

            replay_trace.append({
                "step": step_idx,
                "logical_time": step_time.isoformat(),
                "stage": stage_idx,
                "alerts_triggered": alerts_in_step,
                "settlement_count": len(step_settlement_records),
                "settlements": step_settlement_records,
            })

        # Compute deterministic SHA-256 fingerprint across all steps
        canonical_json = json.dumps(replay_trace, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        return {
            "seed": run_seed,
            "steps": steps,
            "start_time": clock.isoformat(),
            "model_version": "flowshield-flood-risk-v2 (xgb-v1-compatible)",
            "decision_threshold": 0.08,
            "execution_sha256_digest": digest,
            "trace": replay_trace,
        }


scenario_replay_runner = ScenarioReplayRunner()
