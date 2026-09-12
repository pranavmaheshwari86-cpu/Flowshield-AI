"""
apps/api/app/services/landslide_service.py
Flowshield — Empirical Landslide Susceptibility Prototype Service (v2.4)

Implements the empirical rainfall-slope threshold based on Geological Survey of India (GSI)
and Caine (1980) intensity-duration relationships.
Strictly tagged as a non-ML prototype: is_ml_model = False, status = PROTOTYPE_EMPIRICAL_THRESHOLD.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.village import Village
from ..models.observation import EnvironmentalObservation
from ..models.landslide_assessment import LandslideAssessment
from ..schemas.hazard import LandslideAssessmentResponse


class LandslideService:
    """
    Evaluates empirical landslide susceptibility for steep mountain catchments.
    Decoupled from ML flood models; uses transparent physical thresholds.
    """

    METHODOLOGY = "Empirical Rainfall-Slope Threshold (GSI / Caine 1980)"
    STATUS = "PROTOTYPE_EMPIRICAL_THRESHOLD"
    IS_ML_MODEL = False

    def assess_village_landslide_hazard(
        self, village: Village, db: Optional[Session] = None
    ) -> LandslideAssessmentResponse:
        now = datetime.now(timezone.utc)

        # 1. Slope feasibility check
        slope = getattr(village, "slope", None)
        if slope is None or slope < 0.0:
            return LandslideAssessmentResponse(
                village_id=village.id,
                village_name=village.name,
                trigger_index=0.0,
                susceptibility_level="SUSCEPTIBILITY_UNAVAILABLE",
                slope_deg=0.0,
                rainfall_24h_mm=0.0,
                soil_saturation_pct=0.0,
                methodology=self.METHODOLOGY,
                status=self.STATUS,
                is_ml_model=self.IS_ML_MODEL,
                timestamp=now,
            )

        # 2. Retrieve latest observation for rainfall & soil saturation
        r24 = 0.0
        r72 = 0.0
        soil_pct = 50.0

        if db:
            latest_obs = (
                db.query(EnvironmentalObservation)
                .filter(EnvironmentalObservation.village_id == village.id)
                .order_by(EnvironmentalObservation.timestamp.desc())
                .first()
            )
            if latest_obs:
                r24 = float(latest_obs.rainfall_24h or 0.0)
                r72 = float(latest_obs.rainfall_72h or (r24 * 1.5))
                soil_pct = float(latest_obs.soil_moisture or 50.0)

        # 3. Empirical GSI / Caine Calculation
        if slope < 15.0:
            # Low gradient catchments (< 15 degrees) have minimal landslide susceptibility
            trigger_index = 0.0
            level = "LOW"
        else:
            slope_factor = min(1.0, max(0.0, (slope - 15.0) / 30.0))
            rain_factor = min(1.0, (r24 / 120.0) * 0.60 + (r72 / 250.0) * 0.40)
            soil_factor = min(1.0, max(0.0, soil_pct / 100.0))

            raw_index = slope_factor * (0.60 * rain_factor + 0.40 * soil_factor)
            trigger_index = round(min(1.0, max(0.0, raw_index)), 3)

            # Severity tier mapping
            if trigger_index >= 0.65 or (slope >= 30.0 and r24 >= 120.0):
                level = "CRITICAL"
            elif trigger_index >= 0.40 or (slope >= 25.0 and r24 >= 70.0):
                level = "HIGH"
            elif trigger_index >= 0.20:
                level = "MODERATE"
            else:
                level = "LOW"

        # 4. Optional persistence in database
        if db:
            try:
                record = LandslideAssessment(
                    village_id=village.id,
                    timestamp=now,
                    trigger_index=trigger_index,
                    susceptibility_level=level,
                    methodology=self.METHODOLOGY,
                    status=self.STATUS,
                    is_ml_model=self.IS_ML_MODEL,
                    advisory_notice=(
                        f"Slope: {slope:.1f}°, 24h Rain: {r24:.1f}mm, Saturation: {soil_pct:.1f}%. "
                        "Screening indicator only."
                    ),
                )
                db.add(record)
                db.commit()
            except Exception:
                db.rollback()

        return LandslideAssessmentResponse(
            village_id=village.id,
            village_name=village.name,
            trigger_index=trigger_index,
            susceptibility_level=level,
            slope_deg=round(slope, 1),
            rainfall_24h_mm=round(r24, 1),
            soil_saturation_pct=round(soil_pct, 1),
            methodology=self.METHODOLOGY,
            status=self.STATUS,
            is_ml_model=self.IS_ML_MODEL,
            timestamp=now,
        )


landslide_service = LandslideService()
