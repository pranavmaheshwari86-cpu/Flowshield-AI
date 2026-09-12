"""
apps/api/app/services/agro_monitoring_service.py
Flowshield — AgroMonitoring API Service for Soil Moisture Telemetry

Handles official AgroMonitoring REST API communication:
- Polygon Registration & Lifecycle Management
- Soil Moisture Satellite Observation Retrieval
- Rate Limiting, Exponential Backoff & Controlled Concurrency
- Subscription Quota Limit Protection (Graceful HTTP 422 handling)
- Local Database Caching & Deduplication
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models.monitoring_polygon import MonitoringPolygon, SoilObservation
from .agro_grid_service import agro_grid_service

logger = logging.getLogger("flowshield.agro_monitoring")


# Soil Moisture Classification Tiers (m3/m3)
# Based on hydrological soil saturation indices:
# < 0.15: Low / Dry (drought risk)
# 0.15 - 0.30: Moderate / Healthy agricultural baseline
# 0.30 - 0.45: High / Elevated saturation
# > 0.45: Very High / Saturated (Flash flood runoff vulnerability)
def classify_soil_moisture_tier(moisture: Optional[float]) -> str:
    if moisture is None:
        return "UNKNOWN"
    if moisture < 0.15:
        return "LOW"
    if moisture < 0.30:
        return "MODERATE"
    if moisture < 0.45:
        return "HIGH"
    return "VERY_HIGH"


class AgroMonitoringService:
    def __init__(self):
        self.base_url = settings.AGRO_API_BASE_URL.rstrip("/")
        self.api_key = settings.AGRO_API_KEY.strip()
        self.client_timeout = 15.0
        self.concurrency_limit = asyncio.Semaphore(5)

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Tuple[int, Optional[Any], Optional[str]]:
        """
        Executes HTTP request to AgroMonitoring API with exponential backoff.
        Returns: (status_code, json_data, error_message)
        """
        if not self.is_configured():
            return 401, None, "AgroMonitoring API key is not configured in backend environment."

        url = f"{self.base_url}{path}"
        req_params = dict(params or {})
        req_params["appid"] = self.api_key

        backoff = 1.0
        for attempt in range(max_retries):
            try:
                async with self.concurrency_limit:
                    async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                        resp = await client.request(
                            method=method,
                            url=url,
                            params=req_params,
                            json=json_body,
                        )

                        # Success
                        if resp.status_code in (200, 201, 204):
                            try:
                                return resp.status_code, resp.json() if resp.status_code != 204 else None, None
                            except Exception:
                                return resp.status_code, None, None

                        # Quota exceeded or validation error from AgroMonitoring
                        if resp.status_code == 422:
                            error_text = resp.text
                            logger.warning("AgroMonitoring 422: %s", error_text)
                            return 422, None, f"AgroMonitoring rejected request (Quota or Constraint limit): {error_text}"

                        # Rate limited or server error -> backoff and retry
                        if resp.status_code in (429, 500, 502, 503, 504):
                            if attempt < max_retries - 1:
                                await asyncio.sleep(backoff)
                                backoff *= 2.0
                                continue
                            return resp.status_code, None, f"AgroMonitoring server busy ({resp.status_code})."

                        return resp.status_code, None, f"AgroMonitoring error {resp.status_code}: {resp.text}"

            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue
                return 408, None, "AgroMonitoring request timed out."
            except Exception as e:
                logger.error("AgroMonitoring request exception: %s", str(e))
                return 500, None, f"Network error communicating with AgroMonitoring: {type(e).__name__}"

        return 500, None, "Max retries exceeded"

    async def list_remote_polygons(self) -> List[Dict[str, Any]]:
        """List all registered polygons in the AgroMonitoring account."""
        status, data, err = await self._request_with_retry("GET", "/polygons")
        if status == 200 and isinstance(data, list):
            return data
        return []

    async def register_polygon(self, name: str, geojson_geometry: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Creates/registers a new polygon in AgroMonitoring.
        Returns: (agro_polygon_id, error_message)
        """
        body = {
            "name": name,
            "geo_json": {
                "type": "Feature",
                "properties": {},
                "geometry": geojson_geometry,
            },
        }

        status, data, err = await self._request_with_retry("POST", "/polygons", json_body=body)
        if status in (200, 201) and isinstance(data, dict):
            agro_id = data.get("id")
            return agro_id, None

        return None, err or f"HTTP {status}"

    async def delete_remote_polygon(self, agro_id: str) -> bool:
        """Deletes a polygon from AgroMonitoring by ID."""
        status, _, _ = await self._request_with_retry("DELETE", f"/polygons/{agro_id}")
        return status in (200, 204)

    async def fetch_soil_data(self, agro_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Retrieves real-time soil moisture and temperatures from /agro/1.0/soil endpoint.
        Returns: ({moisture, t10, t0, dt}, error_message)
        """
        status, data, err = await self._request_with_retry("GET", "/soil", params={"polyid": agro_id})
        if status == 200 and isinstance(data, dict):
            return data, None
        return None, err or f"HTTP {status}"

    async def initialize_grid_in_db(
        self,
        db: Session,
        scope: str = "district",
        state_name: Optional[str] = "Himachal Pradesh",
        district_name: Optional[str] = "Mandi",
        register_with_agro: bool = True,
        batch_limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Generates compliant grid polygons for the specified scope, persists them to the database,
        and safely registers up to `batch_limit` missing polygons with AgroMonitoring.
        """
        # 1. Generate compliant grid cells
        raw_cells = agro_grid_service.generate_grid_cells(
            scope=scope,
            state_name=state_name,
            district_name=district_name,
        )

        cells_generated = len(raw_cells)
        existing_polys = db.query(MonitoringPolygon).all()
        existing_by_name = {p.name: p for p in existing_polys}

        newly_inserted = 0
        already_existing = 0
        limit_hit = False
        plan_notice = None

        created_poly_records: List[MonitoringPolygon] = []

        # 2. Persist any unpersisted polygons into local DB first
        for cell in raw_cells:
            name = cell["name"]
            if name in existing_by_name:
                already_existing += 1
                created_poly_records.append(existing_by_name[name])
            else:
                new_poly = MonitoringPolygon(
                    name=name,
                    country=cell["country"],
                    state=cell["state"],
                    district=cell["district"],
                    area_hectares=cell["area_hectares"],
                    centroid_lat=cell["centroid_lat"],
                    centroid_lon=cell["centroid_lon"],
                    geometry_geojson=json.dumps(cell["geometry"]),
                    status="PENDING",
                )
                db.add(new_poly)
                created_poly_records.append(new_poly)
                newly_inserted += 1

        db.commit()

        # 3. Register missing polygons with AgroMonitoring (up to batch_limit)
        newly_registered = 0
        if register_with_agro and self.is_configured():
            pending_polys = [p for p in created_poly_records if not p.agro_polygon_id and p.status != "LIMIT_EXCEEDED"]
            to_register = pending_polys[:batch_limit]

            for poly in to_register:
                geom = json.loads(poly.geometry_geojson)
                agro_id, err = await self.register_polygon(poly.name, geom)

                if agro_id:
                    poly.agro_polygon_id = agro_id
                    poly.status = "REGISTERED"
                    poly.error_message = None
                    newly_registered += 1
                else:
                    if err and ("422" in err or "limit" in err.lower()):
                        poly.status = "LIMIT_EXCEEDED"
                        poly.error_message = err
                        limit_hit = True
                        plan_notice = (
                            "AgroMonitoring account plan limit reached for concurrent polygons. "
                            "Existing registered polygons are active and monitored."
                        )
                        break
                    else:
                        poly.status = "FAILED"
                        poly.error_message = err

                db.commit()

        # 4. Refresh soil moisture telemetry for any registered polygons
        await self.sync_soil_observations(db)

        return {
            "scope": scope,
            "state": state_name,
            "district": district_name,
            "total_cells_generated": cells_generated,
            "already_existing_in_db": already_existing,
            "newly_inserted_in_db": newly_inserted,
            "newly_registered_with_agro": newly_registered,
            "limit_hit": limit_hit,
            "plan_notice": plan_notice,
        }

    async def sync_soil_observations(self, db: Session, max_polygons: int = 50) -> int:
        """
        Fetches latest satellite soil moisture observations for registered polygons
        and writes records to `soil_observations`.
        """
        if not self.is_configured():
            return 0

        registered_polys = (
            db.query(MonitoringPolygon)
            .filter(MonitoringPolygon.agro_polygon_id.isnot(None))
            .filter(MonitoringPolygon.status == "REGISTERED")
            .limit(max_polygons)
            .all()
        )

        updates_count = 0
        for poly in registered_polys:
            data, err = await self.fetch_soil_data(poly.agro_polygon_id)
            if data:
                obs_dt = datetime.fromtimestamp(data.get("dt", 0), tz=timezone.utc)
                moisture = data.get("moisture", 0.0)
                t10 = data.get("t10")
                t0 = data.get("t0")

                obs = SoilObservation(
                    polygon_id=poly.id,
                    agro_polygon_id=poly.agro_polygon_id,
                    soil_moisture=float(moisture),
                    soil_temperature=float(t10) if t10 is not None else None,
                    surface_temperature=float(t0) if t0 is not None else None,
                    observation_timestamp=obs_dt,
                )
                db.add(obs)
                poly.last_soil_update = datetime.now(timezone.utc)
                updates_count += 1
            elif err:
                poly.error_message = err

        db.commit()
        return updates_count


# Singleton instance
agro_monitoring_service = AgroMonitoringService()
