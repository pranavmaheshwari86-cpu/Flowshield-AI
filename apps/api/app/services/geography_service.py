"""
apps/api/app/services/geography_service.py
Flowshield — Centralized Geographic Authority & Regional Hierarchy Service
Synchronized with ML Model Coverage & Telemetry Basins:
- Uttarakhand (Mandakini & Alaknanda basins: Rudraprayag, Chamoli, Pauri Garhwal, Dehradun)
- Himachal Pradesh (Beas River basin: Mandi, Kullu, Kangra, Shimla)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.village import Village
from ..models.shelter import Shelter
from ..models.route import Route
from ..models.model_coverage import ModelCoverage
from .shelter_ingestion_service import DISTRICT_BOUNDS


# District Centers for Map Viewport Snapping
DISTRICT_CENTERS: Dict[str, Dict[str, Any]] = {
    "Rudraprayag": {
        "lat": 30.500,
        "lon": 79.030,
        "zoom": 11,
        "basin": "Mandakini River Valley",
        "description": "Kedarnath, Gaurikund, Sonprayag, Guptkashi, Agastyamuni corridor",
    },
    "Chamoli": {
        "lat": 30.450,
        "lon": 79.400,
        "zoom": 10,
        "basin": "Alaknanda River Valley",
        "description": "Joshimath, Gopeshwar, Karnaprayag mountain catchment",
    },
    "Pauri Garhwal": {
        "lat": 30.150,
        "lon": 78.780,
        "zoom": 10,
        "basin": "Lower Alaknanda / Ganga Basin",
        "description": "Srinagar Garhwal valley and transit links",
    },
    "Dehradun": {
        "lat": 30.316,
        "lon": 78.032,
        "zoom": 10,
        "basin": "Doon Valley & Song River",
        "description": "State capital & emergency coordination center",
    },
    "Mandi": {
        "lat": 31.708,
        "lon": 76.932,
        "zoom": 11,
        "basin": "Beas River Basin",
        "description": "Mandi Urban, Pandoh Dam, Aut, Thalout, Sundernagar calibrated corridor",
    },
    "Kullu": {
        "lat": 31.957,
        "lon": 77.109,
        "zoom": 10,
        "basin": "Upper Beas & Parvati Valley",
        "description": "Kullu-Manali high hazard alpine basin",
    },
    "Kangra": {
        "lat": 32.100,
        "lon": 76.270,
        "zoom": 10,
        "basin": "Beas Foothill Catchment",
        "description": "Dharamshala & Kangra valley",
    },
    "Shimla": {
        "lat": 31.104,
        "lon": 77.173,
        "zoom": 10,
        "basin": "Sutlej River Basin",
        "description": "Himachal Pradesh State EOC & Shimla hills",
    },
}


class GeographyService:
    """Provides geographic hierarchy and ensures no unsupported combinations are served."""

    @staticmethod
    def get_supported_states(db: Session) -> List[Dict[str, Any]]:
        """Returns states that have actual ML model and data support."""
        states_query = (
            db.query(ModelCoverage.state)
            .filter(ModelCoverage.is_supported == True)
            .distinct()
            .all()
        )
        supported_state_names = [s[0] for s in states_query]
        if not supported_state_names:
            supported_state_names = ["Uttarakhand", "Himachal Pradesh"]

        results = []
        for state in sorted(supported_state_names):
            district_count = (
                db.query(ModelCoverage.district)
                .filter(ModelCoverage.state == state, ModelCoverage.is_supported == True)
                .distinct()
                .count()
            )
            shelter_count = db.query(Shelter).filter(Shelter.state == state).count()
            results.append({
                "state": state,
                "districts_count": district_count,
                "shelters_count": shelter_count,
                "is_active": True,
                "coverage_status": "ML_CALIBRATED_ACTIVE",
            })

        return results

    @staticmethod
    def get_districts_by_state(db: Session, state: str) -> List[Dict[str, Any]]:
        """Returns verified districts for a selected state."""
        coverage_records = (
            db.query(ModelCoverage)
            .filter(
                func.lower(ModelCoverage.state) == state.strip().lower(),
                ModelCoverage.is_supported == True,
            )
            .all()
        )

        results = []
        for cov in coverage_records:
            d_name = cov.district
            center_info = DISTRICT_CENTERS.get(d_name, {
                "lat": 30.500,
                "lon": 79.000,
                "zoom": 10,
                "basin": "Mountain River Basin",
                "description": cov.description or "Himalayan disaster management zone",
            })
            bounds = DISTRICT_BOUNDS.get(d_name, {"lat": (30.0, 31.0), "lon": (78.0, 79.0)})

            settlement_count = db.query(Village).filter(
                func.lower(Village.state) == state.strip().lower(),
                func.lower(Village.district) == d_name.lower(),
            ).count()

            shelter_count = db.query(Shelter).filter(
                func.lower(Shelter.state) == state.strip().lower(),
                func.lower(Shelter.district) == d_name.lower(),
            ).count()

            route_count = db.query(Route).filter(
                func.lower(Route.state) == state.strip().lower(),
                func.lower(Route.district) == d_name.lower(),
            ).count()

            results.append({
                "district": d_name,
                "state": cov.state,
                "center_lat": center_info["lat"],
                "center_lon": center_info["lon"],
                "default_zoom": center_info["zoom"],
                "river_basin": center_info["basin"],
                "description": center_info["description"],
                "bounds": {
                    "min_lat": bounds["lat"][0],
                    "max_lat": bounds["lat"][1],
                    "min_lon": bounds["lon"][0],
                    "max_lon": bounds["lon"][1],
                },
                "settlement_count": settlement_count,
                "shelter_count": shelter_count,
                "route_count": route_count,
                "has_prediction": cov.has_prediction,
                "has_shelter_data": cov.has_shelter_data,
            })

        return results

    @staticmethod
    def get_settlements_by_district(db: Session, state: str, district: str) -> List[Dict[str, Any]]:
        """Returns settlements / villages in a given district."""
        villages = (
            db.query(Village)
            .filter(
                func.lower(Village.state) == state.strip().lower(),
                func.lower(Village.district) == district.strip().lower(),
            )
            .order_by(Village.population.desc())
            .all()
        )

        results = []
        for v in villages:
            results.append({
                "id": v.id,
                "name": v.name,
                "tehsil": v.tehsil,
                "district": v.district,
                "state": v.state,
                "latitude": v.latitude,
                "longitude": v.longitude,
                "population": v.population,
                "elevation_m": v.elevation,
                "slope_deg": v.slope,
                "distance_to_river_km": v.distance_to_river,
                "vulnerability_index": v.vulnerability_index,
            })

        return results

    @staticmethod
    def get_coverage_summary(db: Session) -> Dict[str, Any]:
        """Returns overall registry coverage overview."""
        coverage_records = db.query(ModelCoverage).all()
        return {
            "total_districts": len(coverage_records),
            "supported_districts": [c.district for c in coverage_records if c.is_supported],
            "states": sorted(list({c.state for c in coverage_records})),
            "records": [
                {
                    "state": c.state,
                    "district": c.district,
                    "is_supported": c.is_supported,
                    "has_training_data": c.has_training_data,
                    "has_prediction": c.has_prediction,
                    "has_shelter_data": c.has_shelter_data,
                    "has_route_data": c.has_route_data,
                    "description": c.description,
                    "last_updated": c.last_updated.isoformat() if c.last_updated else None,
                }
                for c in coverage_records
            ],
        }


geography_service = GeographyService()
