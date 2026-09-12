"""
apps/api/app/services/soil_forecast_service.py
Flowshield — Soil Moisture Forecast Prototype Service (v2.4)
Delivers decoupled 1D water-balance projections tagged strictly as PROTOTYPE_BASELINE.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.village import Village
from ..models.observation import EnvironmentalObservation
from ..schemas.hazard import SoilMoistureForecastHorizon, SoilMoistureForecastResponse


class SoilMoistureForecastService:
    """
    Simulates 1D water-balance soil saturation dynamics across forecast horizons.
    Strictly isolated from ML flood model; tagged as PROTOTYPE_BASELINE.
    """

    HORIZONS_HOURS = [1, 3, 6, 12, 24, 48]

    def get_soil_moisture_forecast(
        self, village: Village, db: Optional[Session] = None
    ) -> SoilMoistureForecastResponse:
        now = datetime.now(timezone.utc)

        # Baseline soil moisture from current observation
        current_sat = 55.0
        current_rain = 2.0
        if db:
            latest = (
                db.query(EnvironmentalObservation)
                .filter(EnvironmentalObservation.village_id == village.id)
                .order_by(EnvironmentalObservation.timestamp.desc())
                .first()
            )
            if latest:
                current_sat = float(latest.soil_moisture or 55.0)
                current_rain = float(latest.rainfall_1h or 2.0)

        horizons: List[SoilMoistureForecastHorizon] = []
        sat = current_sat

        for h in self.HORIZONS_HOURS:
            # Simple 1D bucket dynamics: rain increases saturation, drainage/ET reduces it
            # Assumes 0.45 m3/m3 capacity (~450mm profile), drainage rate ~0.8%/hr, ET ~0.3%/hr
            added = min(15.0, current_rain * 0.8)
            drained = 0.8 * (h / 6.0)
            sat = max(10.0, min(100.0, sat + added - drained))

            horizons.append(
                SoilMoistureForecastHorizon(
                    lead_time_hours=h,
                    projected_soil_saturation_pct=round(sat, 1),
                    model_type="1D_WATER_BALANCE_BUCKET",
                    status="PROTOTYPE_BASELINE",
                    is_ml_model=False,
                )
            )

        return SoilMoistureForecastResponse(
            village_id=village.id,
            village_name=village.name,
            generated_at=now,
            horizons=horizons,
            status="PROTOTYPE_BASELINE",
            is_ml_model=False,
        )


soil_moisture_forecast_service = SoilMoistureForecastService()
