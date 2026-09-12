import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from ..models.simulation import Simulation
from ..models.village import Village
from ..models.observation import EnvironmentalObservation
from ..models.prediction import Prediction
from ..models.risk_snapshot import RiskSnapshot
from ..models.alert import Alert
from ..models.shelter import Shelter
from ..models.route import Route
from .prediction_service import prediction_service
from .risk_engine import risk_engine
from .alert_engine import alert_engine
from .shelter_service import shelter_service
from .route_service import route_service


STAGE_NAMES = {
    0: "Normal Baseline Conditions",
    1: "Heavy Monsoon Inception",
    2: "Catchment Soil Saturation",
    3: "Rapid River Gauge Surge",
    4: "Critical Inundation & Road Blockage",
}


class SimulationEngine:
    """
    Deterministic 20-Substep Server-Side Simulation Engine.
    Executes the entire environmental-intelligence-to-action pipeline on backend models.
    """

    DEFAULT_SEED = 26192

    @classmethod
    def get_or_create_simulation(cls, db: Session, scenario: str = "GRADUAL_MONSOON", seed: int = DEFAULT_SEED) -> Simulation:
        sim = db.query(Simulation).first()
        if not sim:
            sim = Simulation(
                scenario_name=scenario,
                status="IDLE",
                current_stage=0,
                current_substep=0,
                total_steps=20,
                seed=seed,
            )
            db.add(sim)
            db.commit()
            db.refresh(sim)
        return sim

    @classmethod
    def start_simulation(cls, db: Session, scenario: str = "GRADUAL_MONSOON", seed: int = DEFAULT_SEED) -> Simulation:
        sim = cls.get_or_create_simulation(db, scenario, seed)
        sim.status = "RUNNING"
        sim.scenario_name = scenario
        sim.seed = seed
        sim.current_stage = 0
        sim.current_substep = 0
        sim.started_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(sim)
        return sim

    @classmethod
    def pause_simulation(cls, db: Session) -> Simulation:
        sim = cls.get_or_create_simulation(db)
        sim.status = "PAUSED"
        db.commit()
        db.refresh(sim)
        return sim

    @classmethod
    def step_simulation(cls, db: Session) -> Dict[str, Any]:
        sim = cls.get_or_create_simulation(db)
        
        # Advance substep (0 to 19, wraps or caps at 19)
        next_substep = min(19, sim.current_substep + 1)
        sim.current_substep = next_substep
        sim.current_stage = next_substep // 4
        if next_substep >= 19:
            sim.status = "COMPLETED"
            sim.completed_at = datetime.now(timezone.utc)
        else:
            sim.status = "RUNNING"
        db.commit()

        stage = sim.current_stage
        substep = sim.current_substep

        # Deterministic PRNG seeded specifically for this step
        step_rng = np.random.RandomState(sim.seed + substep * 100)

        # Target Uttarakhand Himalayan settlements for PS-26192 cloudburst scenario
        villages = db.query(Village).filter(Village.state.ilike("%Uttarakhand%")).all()
        if not villages:
            villages = db.query(Village).all()
        new_alerts_count = 0
        now = datetime.now(timezone.utc)

        # Update physical entities for all 20 settlements
        for v in villages:
            # Physical scaling factors per settlement geography
            river_dist_factor = max(0.0, 1.0 - (v.distance_to_river / 4.0))
            elevation_drain_factor = (v.elevation - 400.0) / 3200.0
            slope_runoff_factor = v.slope / 45.0

            # 1. Generate Synthetic Telemetry for this step
            if stage == 0:
                r1h = float(step_rng.uniform(4.0, 9.0))
                r3h = float(r1h * 1.8 + step_rng.uniform(1.0, 3.0))
                r6h = float(r3h * 1.4 + step_rng.uniform(2.0, 5.0))
                r24h = float(r1h * 3.5 + step_rng.uniform(5.0, 12.0))
                r72h = float(r24h * 1.5 + step_rng.uniform(8.0, 15.0))
                intensity = float(r1h * step_rng.uniform(0.8, 1.2))
                soil = float(np.clip(25.0 + r24h * 0.3 - slope_runoff_factor * 5.0, 15.0, 45.0))
                deep_soil = float(np.clip(soil * 0.90, 12.0, 42.0))
                river_lvl = float(np.clip(1.2 + river_dist_factor * 0.4 + step_rng.uniform(-0.1, 0.1), 0.8, 2.0))
                surge = float(step_rng.uniform(-0.02, 0.05))
            elif stage == 1:
                r1h = float(step_rng.uniform(25.0, 45.0) + river_dist_factor * 10.0)
                r3h = float(r1h * 2.0 + step_rng.uniform(8.0, 15.0))
                r6h = float(r3h * 1.5 + step_rng.uniform(10.0, 20.0))
                r24h = float(r1h * 2.8 + step_rng.uniform(20.0, 40.0))
                r72h = float(r24h * 1.6 + (substep - 4) * 15.0 + step_rng.uniform(15.0, 25.0))
                intensity = float(r1h * step_rng.uniform(1.0, 1.3))
                soil = float(np.clip(45.0 + (substep - 4) * 6.0 + step_rng.uniform(0, 5), 40.0, 68.0))
                deep_soil = float(np.clip(soil * 0.88 + (substep - 4) * 2.0, 35.0, 65.0))
                river_lvl = float(np.clip(2.0 + (substep - 4) * 0.5 * river_dist_factor, 1.5, 3.5))
                surge = float(step_rng.uniform(0.2, 0.6) * river_dist_factor)
            elif stage == 2:
                r1h = float(step_rng.uniform(45.0, 75.0))
                r3h = float(r1h * 2.2 + step_rng.uniform(15.0, 30.0))
                r6h = float(r3h * 1.5 + step_rng.uniform(20.0, 40.0))
                r24h = float(120.0 + (substep - 8) * 30.0 + step_rng.uniform(10, 25))
                r72h = float(r24h * 1.7 + (substep - 8) * 25.0 + step_rng.uniform(20.0, 40.0))
                intensity = float(r1h * step_rng.uniform(1.1, 1.4))
                soil = float(np.clip(70.0 + (substep - 8) * 4.5 + step_rng.uniform(0, 4), 68.0, 88.0))
                deep_soil = float(np.clip(soil * 0.92 + (substep - 8) * 1.5, 65.0, 85.0))
                river_lvl = float(np.clip(3.5 + (substep - 8) * 0.8 * river_dist_factor, 2.5, 5.8))
                surge = float(np.clip(0.6 + (substep - 8) * 0.3 * river_dist_factor, 0.3, 1.5))
            elif stage == 3:
                r1h = float(step_rng.uniform(70.0, 110.0))
                r3h = float(r1h * 2.4 + step_rng.uniform(25.0, 50.0))
                r6h = float(r3h * 1.5 + step_rng.uniform(30.0, 60.0))
                r24h = float(220.0 + (substep - 12) * 45.0 + step_rng.uniform(15, 30))
                r72h = float(r24h * 1.8 + (substep - 12) * 35.0 + step_rng.uniform(30.0, 50.0))
                intensity = float(r1h * step_rng.uniform(1.2, 1.5))
                soil = float(np.clip(88.0 + (substep - 12) * 2.0, 85.0, 96.0))
                deep_soil = float(np.clip(soil * 0.94 + (substep - 12) * 1.0, 82.0, 94.0))
                river_lvl = float(np.clip(5.5 + (substep - 12) * 1.2 * river_dist_factor, 4.0, 8.5))
                surge = float(np.clip(1.4 + (substep - 12) * 0.5 * river_dist_factor, 0.8, 3.2))
            else:  # Stage 4 (Critical)
                r1h = float(step_rng.uniform(90.0, 140.0))
                r3h = float(r1h * 2.6 + step_rng.uniform(35.0, 65.0))
                r6h = float(r3h * 1.5 + step_rng.uniform(40.0, 70.0))
                r24h = float(380.0 + (substep - 16) * 60.0 + step_rng.uniform(20, 40))
                r72h = float(r24h * 1.9 + (substep - 16) * 40.0 + step_rng.uniform(40.0, 60.0))
                intensity = float(r1h * step_rng.uniform(1.3, 1.6))
                soil = float(np.clip(94.0 + (substep - 16) * 1.0, 92.0, 99.0))
                deep_soil = float(np.clip(soil * 0.96 + (substep - 16) * 0.5, 90.0, 98.0))
                river_lvl = float(np.clip(8.0 + (substep - 16) * 1.5 * river_dist_factor, 6.0, 14.5))
                surge = float(np.clip(2.5 + (substep - 16) * 0.8 * river_dist_factor, 1.5, 4.8))

            # Atmospheric & Topographic modeling
            temperature_c = float(round(26.0 - (0.0065 * v.elevation) - (r1h * 0.04), 1))
            relative_humidity_pct = float(round(np.clip(68.0 + (r1h * 0.25) + (soil * 0.1), 45.0, 100.0), 1))
            surface_pressure_hpa = float(round(1013.25 * ((1.0 - 2.25577e-5 * v.elevation) ** 5.25588), 1))
            wind_speed_kmh = float(round(np.clip(12.0 + stage * 5.0 + step_rng.uniform(-2, 4), 5.0, 90.0), 1))

            elevation_m = float(v.elevation)
            catchment_slope_deg = float(v.slope)
            dist_to_river_m = float(v.distance_to_river * 1000.0 if v.distance_to_river <= 20.0 else v.distance_to_river)
            upstream_drainage_sqkm = float(getattr(v, "upstream_drainage_sqkm", 3500.0) or 3500.0)

            # Persist observation with all canonical features
            obs = EnvironmentalObservation(
                village_id=v.id,
                timestamp=now,
                rainfall_1h=round(r1h, 2),
                rainfall_3h=round(r3h, 2),
                rainfall_6h=round(r6h, 2),
                rainfall_24h=round(r24h, 2),
                rainfall_72h=round(r72h, 2),
                rainfall_intensity=round(intensity, 2),
                soil_moisture=round(soil, 2),
                deep_soil_moisture=round(deep_soil, 2),
                temperature=temperature_c,
                humidity=relative_humidity_pct,
                surface_pressure=surface_pressure_hpa,
                wind_speed=wind_speed_kmh,
                river_level=round(river_lvl, 2),
                river_level_change=round(surge, 2),
                source="Flowshield Simulation Telemetry (Canonical 15-Feature)",
                is_simulated=True,
                quality_score=0.98,
                freshness_seconds=10,
            )
            db.add(obs)
            db.flush()

            # 2. Run Prediction Service with Canonical 15 Features
            canonical_sim_features = {
                "rainfall_1h_mm": obs.rainfall_1h,
                "rainfall_3h_mm": obs.rainfall_3h,
                "rainfall_6h_mm": obs.rainfall_6h,
                "rainfall_24h_mm": obs.rainfall_24h,
                "rainfall_72h_mm": obs.rainfall_72h,
                "soil_saturation_pct": obs.soil_moisture,
                "deep_soil_saturation_pct": obs.deep_soil_moisture,
                "temperature_c": obs.temperature,
                "relative_humidity_pct": obs.humidity,
                "surface_pressure_hpa": obs.surface_pressure,
                "wind_speed_kmh": obs.wind_speed,
                "elevation_m": elevation_m,
                "catchment_slope_deg": catchment_slope_deg,
                "dist_to_river_m": dist_to_river_m,
                "upstream_drainage_sqkm": upstream_drainage_sqkm,
                "vulnerability_index": v.vulnerability_index,
            }

            # Check recent snapshots for trend
            past_snaps = (
                db.query(RiskSnapshot)
                .filter(RiskSnapshot.village_id == v.id)
                .order_by(RiskSnapshot.timestamp.desc())
                .limit(3)
                .all()
            )
            past_scores = [s.risk_score for s in reversed(past_snaps)] if past_snaps else []
            trend_factor, trend_str = risk_engine.calculate_trend_factor(past_scores)
            canonical_sim_features["trend_factor"] = trend_factor

            full_pred = prediction_service.predict_full(
                canonical_sim_features, obs.quality_score, obs.freshness_seconds
            )
            flood_prob = full_pred["flood_probability"]
            pred_quality = full_pred["prediction_quality"]
            top_contribs = full_pred["top_contributing_factors"]
            risk_score = full_pred["risk_score"]
            risk_lvl = full_pred["risk_level"]

            # Persist Prediction
            pred = Prediction(
                village_id=v.id,
                observation_id=obs.id,
                flood_probability=flood_prob,
                calibrated_probability=full_pred["calibrated_probability"],
                decision_threshold=full_pred["decision_threshold"],
                threshold_exceeded=full_pred["threshold_exceeded"],
                model_integrity_status=full_pred["model_integrity_status"],
                prediction_quality=pred_quality,
                model_version=prediction_service.metadata.get("model_version", "flowshield-flood-risk-v2"),
                feature_contributions=top_contribs,
            )
            db.add(pred)
            db.flush()

            # 3. Persist Risk Snapshot
            snapshot = RiskSnapshot(
                village_id=v.id,
                prediction_id=pred.id,
                risk_score=risk_score,
                risk_level=risk_lvl,
                trend=trend_str,
                timestamp=now,
            )
            db.add(snapshot)

            # 4. Trigger Alert Engine
            alert = alert_engine.evaluate_and_create_alert(
                db=db,
                village=v,
                risk_score=risk_score,
                risk_level=risk_lvl,
                prediction_id=pred.id,
                top_contributors=top_contribs,
                simulation_substep=substep,
            )
            if alert:
                new_alerts_count += 1

        # 5. Dynamic updates to Shelters and Routes
        shelter_service.update_occupancy_for_simulation(db, stage, substep)
        route_service.update_route_blockages_for_simulation(db, stage, substep)

        db.commit()

        # Build Summary
        active_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").all()
        critical_count = (
            db.query(RiskSnapshot)
            .filter(RiskSnapshot.risk_level == "CRITICAL", RiskSnapshot.timestamp == now)
            .count()
        )
        high_count = (
            db.query(RiskSnapshot)
            .filter(RiskSnapshot.risk_level == "HIGH", RiskSnapshot.timestamp == now)
            .count()
        )
        mod_count = (
            db.query(RiskSnapshot)
            .filter(RiskSnapshot.risk_level == "MODERATE", RiskSnapshot.timestamp == now)
            .count()
        )
        low_count = (
            db.query(RiskSnapshot)
            .filter(RiskSnapshot.risk_level == "LOW", RiskSnapshot.timestamp == now)
            .count()
        )

        return {
            "simulation_id": sim.id,
            "stage": stage,
            "stage_name": STAGE_NAMES[stage],
            "substep": substep,
            "total_steps": 20,
            "progress_percentage": round((substep / 19.0) * 100.0, 1),
            "villages_updated": len(villages),
            "new_alerts_triggered": new_alerts_count,
            "system_summary": {
                "critical_count": critical_count,
                "high_count": high_count,
                "moderate_count": mod_count,
                "low_count": low_count,
                "active_alerts": len(active_alerts),
            },
            "active_alerts": [
                {
                    "id": a.id,
                    "village_id": a.village_id,
                    "severity": a.severity,
                    "headline": a.headline,
                    "trigger_reason": a.trigger_reason,
                    "created_at": a.created_at.isoformat(),
                }
                for a in active_alerts[:5]
            ],
        }

    @classmethod
    def reset_simulation(cls, db: Session) -> Dict[str, Any]:
        """
        Resets all simulation-generated records and restores baseline green conditions.
        """
        # 1. Reset Simulation state record
        sim = cls.get_or_create_simulation(db)
        sim.current_stage = 0
        sim.current_substep = 0
        sim.status = "IDLE"
        sim.completed_at = None

        # 2. Clear simulation-generated alerts only (retain live national crisis alerts)
        db.query(Alert).filter(
            (Alert.headline.ilike("%mandakini%")) |
            (Alert.trigger_reason.ilike("%simulat%")) |
            (Alert.trigger_reason.ilike("%ps-26192%"))
        ).delete(synchronize_session=False)

        # 3. Reset shelters to baseline available
        shelters = db.query(Shelter).all()
        for s in shelters:
            cap = s.capacity or s.total_capacity
            if cap is not None:
                s.current_occupancy = int(cap * 0.10)
            else:
                s.current_occupancy = None
            s.status = "AVAILABLE"

        # 4. Reset routes to unblocked
        routes = db.query(Route).all()
        for r in routes:
            r.is_blocked = False
            r.blockage_reason = None
            r.assessed_risk_score = 10

        # 5. Clean up simulated predictions and snapshots
        db.query(RiskSnapshot).delete()
        db.query(Prediction).delete()
        db.query(EnvironmentalObservation).filter(EnvironmentalObservation.is_simulated == True).delete()

        db.commit()

        # 6. Re-seed baseline observations from initial_observations.json
        import sys, os
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        from scripts.seed_db import seed_initial_observations_and_baseline_predictions
        seed_initial_observations_and_baseline_predictions(db)
        try:
            from scripts.seed_national_flood_data import seed_national_flood_data
            seed_national_flood_data(db=db)
        except Exception as e:
            print("Note: national flood data reseed skipped:", e)

        return {
            "status": "RESET_SUCCESSFUL",
            "message": "All simulation data reverted. System restored to baseline normal conditions.",
            "current_stage": 0,
            "current_substep": 0,
        }


simulation_engine = SimulationEngine()
