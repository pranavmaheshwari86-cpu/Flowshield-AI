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


# District Centers for Map Viewport Snapping & Basin Identification across all 11 ML Models
DISTRICT_CENTERS: Dict[str, Dict[str, Any]] = {
    # 1. Uttarakhand (Baseline Model Corridor)
    "Rudraprayag": {"lat": 30.500, "lon": 79.030, "zoom": 11, "basin": "Mandakini River Valley", "description": "Kedarnath, Gaurikund, Sonprayag, Guptkashi, Agastyamuni corridor"},
    "Chamoli": {"lat": 30.450, "lon": 79.400, "zoom": 10, "basin": "Alaknanda River Valley", "description": "Joshimath, Gopeshwar, Karnaprayag mountain catchment"},
    "Pauri Garhwal": {"lat": 30.150, "lon": 78.780, "zoom": 10, "basin": "Lower Alaknanda / Ganga Basin", "description": "Srinagar Garhwal valley and transit links"},
    "Dehradun": {"lat": 30.316, "lon": 78.032, "zoom": 10, "basin": "Doon Valley & Song River", "description": "State capital & emergency coordination center"},

    # 2. Himachal Pradesh (Western Himalayas ML Model)
    "Mandi": {"lat": 31.708, "lon": 76.932, "zoom": 11, "basin": "Beas River Basin", "description": "Mandi Urban, Pandoh Dam, Aut, Thalout, Sundernagar calibrated corridor"},
    "Kullu": {"lat": 31.957, "lon": 77.109, "zoom": 10, "basin": "Upper Beas & Parvati Valley", "description": "Kullu-Manali high hazard alpine basin"},
    "Kangra": {"lat": 32.100, "lon": 76.270, "zoom": 10, "basin": "Beas Foothill Catchment", "description": "Dharamshala & Kangra valley"},
    "Shimla": {"lat": 31.104, "lon": 77.173, "zoom": 10, "basin": "Sutlej River Basin", "description": "Himachal Pradesh State EOC & Shimla hills"},

    # 3. Arunachal Pradesh (Eastern Himalayas ML Model)
    "Papum Pare": {"lat": 27.084, "lon": 93.605, "zoom": 10, "basin": "Dikrong / Subansiri Basin", "description": "Itanagar capital complex and Dikrong river corridor"},
    "East Siang": {"lat": 28.065, "lon": 95.328, "zoom": 10, "basin": "Siang River Basin", "description": "Pasighat foothill deluge zone"},
    "West Siang": {"lat": 28.170, "lon": 94.790, "zoom": 10, "basin": "Siyom River Catchment", "description": "Aalo river valley and steep gorge drainage"},
    "Upper Subansiri": {"lat": 27.990, "lon": 94.220, "zoom": 10, "basin": "Subansiri River Basin", "description": "Daporijo high montane catchment"},
    "East Kameng": {"lat": 27.340, "lon": 92.970, "zoom": 10, "basin": "Kameng River Basin", "description": "Seppa mountain flash flood corridor"},
    "Lohit": {"lat": 27.920, "lon": 96.160, "zoom": 10, "basin": "Lohit River Catchment", "description": "Tezu floodplain and eastern drainage"},

    # 4. Jammu & Kashmir (Western Himalayas ML Model)
    "Srinagar": {"lat": 34.084, "lon": 74.797, "zoom": 11, "basin": "Jhelum River Basin", "description": "Srinagar urban valley and Dal lake floodplain"},
    "Anantnag": {"lat": 33.731, "lon": 75.155, "zoom": 10, "basin": "Upper Jhelum River Basin", "description": "South Kashmir headwater surge corridor"},
    "Ramban": {"lat": 33.440, "lon": 75.198, "zoom": 10, "basin": "Chenab River Gorge", "description": "NH-44 landslide and Chenab flash flood corridor"},
    "Jammu": {"lat": 32.727, "lon": 74.857, "zoom": 11, "basin": "Tawi River Basin", "description": "Tawi river urban drainage and flash flood zone"},
    "Doda": {"lat": 33.150, "lon": 75.770, "zoom": 10, "basin": "Middle Chenab Basin", "description": "Chenab mountain gorge and steep tributaries"},
    "Baramulla": {"lat": 34.199, "lon": 74.344, "zoom": 10, "basin": "Lower Jhelum Basin", "description": "North Kashmir outflow corridor"},

    # 5. Leh & Ladakh (Trans-Himalayas ML Model)
    "Leh": {"lat": 34.253, "lon": 77.503, "zoom": 10, "basin": "Indus & Nubra River Basin", "description": "Leh valley, Khalsi, Karu, and Nubra glacial outburst corridor"},

    # 6. Manipur (Northeast Hills ML Model)
    "Imphal West": {"lat": 24.817, "lon": 93.937, "zoom": 11, "basin": "Imphal River Basin", "description": "Imphal capital valley and Nambul river catchment"},
    "Bishnupur": {"lat": 24.631, "lon": 93.782, "zoom": 10, "basin": "Loktak Lake Catchment", "description": "Loktak peripheral inundation zone"},
    "Churachandpur": {"lat": 24.334, "lon": 93.680, "zoom": 10, "basin": "Barak River Headwaters", "description": "Southern hill catchment and Tuitha river corridor"},
    "Jiribam": {"lat": 24.793, "lon": 93.126, "zoom": 10, "basin": "Jiri River Basin", "description": "Assam-Manipur border low-lying river corridor"},
    "Thoubal": {"lat": 24.634, "lon": 94.093, "zoom": 10, "basin": "Thoubal River Basin", "description": "Thoubal river confluence and urban plain"},

    # 7. Meghalaya (Shillong Plateau ML Model)
    "East Khasi Hills": {"lat": 25.424, "lon": 91.802, "zoom": 10, "basin": "Umiam & Umshyrpi Basin", "description": "Shillong hills, Cherrapunji / Sohra extreme rainfall corridor"},
    "West Jaintia Hills": {"lat": 25.320, "lon": 92.111, "zoom": 10, "basin": "Myntdu & Umngot Basin", "description": "Jowai and Dawki border river catchment"},
    "West Garo Hills": {"lat": 25.516, "lon": 90.219, "zoom": 10, "basin": "Someswari River Basin", "description": "Tura hills and Jinjiram river plain"},
    "West Khasi Hills": {"lat": 25.519, "lon": 91.262, "zoom": 10, "basin": "Kynshi River Basin", "description": "Nongstoin high plateau drainage"},

    # 8. Mizoram (Mizo Hills ML Model)
    "Aizawl": {"lat": 23.727, "lon": 92.718, "zoom": 11, "basin": "Tlawng River Basin", "description": "Aizawl ridge and Tlawng valley drainage"},
    "Kolasib": {"lat": 24.226, "lon": 92.678, "zoom": 10, "basin": "Serlui River Basin", "description": "Northern transport and river corridor"},
    "Lunglei": {"lat": 22.881, "lon": 92.745, "zoom": 10, "basin": "Khawthlangtuipui Basin", "description": "Southern hill terrain and river valley"},
    "Saiha": {"lat": 22.486, "lon": 92.978, "zoom": 10, "basin": "Chhimtuipui River Basin", "description": "Kaladan / Chhimtuipui international river basin"},
    "Champhai": {"lat": 23.460, "lon": 93.328, "zoom": 10, "basin": "Tuipui River Basin", "description": "Eastern valley and cross-border catchment"},

    # 9. Nagaland (Naga Hills ML Model)
    "Kohima": {"lat": 25.670, "lon": 94.110, "zoom": 11, "basin": "Dhansiri River Basin", "description": "State capital ridge and high mountain catchment"},
    "Dimapur": {"lat": 25.907, "lon": 93.727, "zoom": 11, "basin": "Chathe / Dhansiri Plain", "description": "Foothill gateway and river plain deluge zone"},
    "Mokokchung": {"lat": 26.322, "lon": 94.521, "zoom": 10, "basin": "Doyang River Basin", "description": "Central hill ridge and agricultural catchment"},
    "Wokha": {"lat": 26.105, "lon": 94.260, "zoom": 10, "basin": "Doyang Hydro Dam Catchment", "description": "Doyang reservoir surge and flood management area"},
    "Zunheboto": {"lat": 25.960, "lon": 94.520, "zoom": 10, "basin": "Tizu River Basin", "description": "Central montane river basin"},

    # 10. Sikkim (Eastern Himalayas ML Model)
    "East Sikkim": {"lat": 27.287, "lon": 88.555, "zoom": 11, "basin": "Teesta River Basin", "description": "Gangtok, Singtam, Rangpo Teesta river corridor"},
    "North Sikkim": {"lat": 27.565, "lon": 88.577, "zoom": 10, "basin": "Upper Teesta & Lachen Basin", "description": "Mangan, Chungthang GLOF and glacial surge zone"},
    "South Sikkim": {"lat": 27.090, "lon": 88.320, "zoom": 10, "basin": "Rangit River Basin", "description": "Jorethang, Namchi Rangit confluence"},

    # 11. Tripura (Tripura Basin ML Model)
    "West Tripura": {"lat": 23.832, "lon": 91.287, "zoom": 11, "basin": "Haora River Basin", "description": "Agartala urban floodplain and Haora river surge zone"},
    "North Tripura": {"lat": 24.267, "lon": 92.186, "zoom": 10, "basin": "Juri & Deo Basin", "description": "Dharmanagar floodplain and Jampui hills catchment"},
    "Gomati": {"lat": 23.533, "lon": 91.488, "zoom": 10, "basin": "Gomati River Basin", "description": "Udaipur and Maharani barrage surge zone"},
    "South Tripura": {"lat": 23.235, "lon": 91.452, "zoom": 10, "basin": "Muhuri & Feni Basin", "description": "Belonia border river basin"},
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
            center_info = DISTRICT_CENTERS.get(d_name)
            if not center_info:
                v_avg = (
                    db.query(func.avg(Village.latitude), func.avg(Village.longitude))
                    .filter(
                        func.lower(Village.state) == state.strip().lower(),
                        func.lower(Village.district) == d_name.lower(),
                    )
                    .first()
                )
                lat = v_avg[0] if (v_avg and v_avg[0]) else 30.500
                lon = v_avg[1] if (v_avg and v_avg[1]) else 79.000
                center_info = {
                    "lat": round(lat, 4),
                    "lon": round(lon, 4),
                    "zoom": 10,
                    "basin": "Regional Mountain Basin",
                    "description": cov.description or f"{d_name} disaster management corridor",
                }

            if d_name in DISTRICT_BOUNDS:
                bounds = DISTRICT_BOUNDS[d_name]
            else:
                c_lat = center_info["lat"]
                c_lon = center_info["lon"]
                bounds = {
                    "lat": (round(c_lat - 0.45, 4), round(c_lat + 0.45, 4)),
                    "lon": (round(c_lon - 0.45, 4), round(c_lon + 0.45, 4)),
                }

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
