"""
scripts/seed_regional_model_villages.py
Flowshield — Seed Regional ML Model Stations as Settlements
Smart India Hackathon 2026 (PS ID: 26192)

Extracts all monitoring stations across the 10 regional ML model configs
(ml/configs/regions/*.yaml) and inserts them into the villages table,
ensuring all 10 model states/UTs appear in the cascading dropdown
and are fully selectable for real-time multi-horizon ML inference.
"""

import os
import sys
import yaml
from pathlib import Path

# Add paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "apps" / "api"))
sys.path.append(str(ROOT / "ml"))

from app.database import SessionLocal, engine, Base
from app.models.village import Village

STATION_METADATA = {
    # Arunachal Pradesh
    "ITN_SNG_01": {"district": "Papum Pare", "tehsil": "Itanagar", "state": "Arunachal Pradesh", "pop": 59490},
    "PSG_SNG_02": {"district": "East Siang", "tehsil": "Pasighat", "state": "Arunachal Pradesh", "pop": 24656},
    "ALN_SUB_03": {"district": "West Siang", "tehsil": "Aalo", "state": "Arunachal Pradesh", "pop": 20680},
    "DPR_SUB_04": {"district": "Upper Subansiri", "tehsil": "Daporijo", "state": "Arunachal Pradesh", "pop": 15468},
    "SEP_KMG_05": {"district": "East Kameng", "tehsil": "Seppa", "state": "Arunachal Pradesh", "pop": 18184},
    "TWN_LOH_06": {"district": "Lohit", "tehsil": "Tezu", "state": "Arunachal Pradesh", "pop": 18184},

    # Jammu & Kashmir
    "SRN_JHL_01": {"district": "Srinagar", "tehsil": "Srinagar South", "state": "Jammu & Kashmir", "pop": 1180000},
    "ANN_CHN_02": {"district": "Anantnag", "tehsil": "Anantnag", "state": "Jammu & Kashmir", "pop": 158000},
    "BRM_CHN_03": {"district": "Ramban", "tehsil": "Banihal", "state": "Jammu & Kashmir", "pop": 34000},
    "JMU_TWI_04": {"district": "Jammu", "tehsil": "Jammu", "state": "Jammu & Kashmir", "pop": 502197},
    "PHL_CHN_05": {"district": "Doda", "tehsil": "Doda", "state": "Jammu & Kashmir", "pop": 21605},
    "BRH_KSH_06": {"district": "Baramulla", "tehsil": "Baramulla", "state": "Jammu & Kashmir", "pop": 167986},

    # Leh & Ladakh
    "LEH_IND_01": {"district": "Leh", "tehsil": "Leh", "state": "Leh & Ladakh", "pop": 30870},
    "KRU_SHY_02": {"district": "Leh", "tehsil": "Karu", "state": "Leh & Ladakh", "pop": 4200},
    "KHL_ZAN_03": {"district": "Leh", "tehsil": "Khalsi", "state": "Leh & Ladakh", "pop": 5100},
    "NUB_NUB_04": {"district": "Leh", "tehsil": "Diskit", "state": "Leh & Ladakh", "pop": 8400},
    "CHL_LEH_05": {"district": "Leh", "tehsil": "Choglamsar", "state": "Leh & Ladakh", "pop": 10765},

    # Manipur
    "IMP_IMP_01": {"district": "Imphal West", "tehsil": "Lamphelpat", "state": "Manipur", "pop": 268243},
    "BIS_IRL_02": {"district": "Bishnupur", "tehsil": "Bishnupur", "state": "Manipur", "pop": 16264},
    "CHR_BRK_03": {"district": "Churachandpur", "tehsil": "Churachandpur", "state": "Manipur", "pop": 45850},
    "JRB_IRL_04": {"district": "Jiribam", "tehsil": "Jiribam", "state": "Manipur", "pop": 7343},
    "TMN_IMP_05": {"district": "Thoubal", "tehsil": "Thoubal", "state": "Manipur", "pop": 45947},

    # Meghalaya
    "SHL_UMI_01": {"district": "East Khasi Hills", "tehsil": "Mylliem", "state": "Meghalaya", "pop": 143229},
    "CHR_MYN_02": {"district": "East Khasi Hills", "tehsil": "Sohra", "state": "Meghalaya", "pop": 11722},
    "DWK_UMN_03": {"district": "West Jaintia Hills", "tehsil": "Amlarem", "state": "Meghalaya", "pop": 3800},
    "TUR_SMS_04": {"district": "West Garo Hills", "tehsil": "Rongram", "state": "Meghalaya", "pop": 74858},
    "JWI_UMI_05": {"district": "West Jaintia Hills", "tehsil": "Thadlaskein", "state": "Meghalaya", "pop": 28430},
    "NNG_UMI_06": {"district": "West Khasi Hills", "tehsil": "Nongstoin", "state": "Meghalaya", "pop": 28742},

    # Mizoram
    "AZL_TLW_01": {"district": "Aizawl", "tehsil": "Aizawl", "state": "Mizoram", "pop": 293416},
    "KLH_TUR_02": {"district": "Kolasib", "tehsil": "Kolasib", "state": "Mizoram", "pop": 24272},
    "LWG_CHH_03": {"district": "Lunglei", "tehsil": "Lunglei", "state": "Mizoram", "pop": 57011},
    "SMR_TLW_04": {"district": "Saiha", "tehsil": "Saiha", "state": "Mizoram", "pop": 25110},
    "CHM_BRK_05": {"district": "Champhai", "tehsil": "Champhai", "state": "Mizoram", "pop": 32734},

    # Nagaland
    "KHM_DHN_01": {"district": "Kohima", "tehsil": "Kohima", "state": "Nagaland", "pop": 99039},
    "DMP_DOY_02": {"district": "Dimapur", "tehsil": "Dimapur", "state": "Nagaland", "pop": 122834},
    "MOK_DOY_03": {"district": "Mokokchung", "tehsil": "Ongpangkong", "state": "Nagaland", "pop": 35913},
    "WKH_TIZ_04": {"district": "Wokha", "tehsil": "Wokha", "state": "Nagaland", "pop": 35004},
    "ZHT_TIZ_05": {"district": "Zunheboto", "tehsil": "Zunheboto", "state": "Nagaland", "pop": 22633},

    # Sikkim
    "GNG_TST_01": {"district": "East Sikkim", "tehsil": "Gangtok", "state": "Sikkim", "pop": 100286},
    "SNG_TST_02": {"district": "East Sikkim", "tehsil": "Singtam", "state": "Sikkim", "pop": 5868},
    "MNG_RNG_03": {"district": "North Sikkim", "tehsil": "Mangan", "state": "Sikkim", "pop": 4644},
    "CHG_GLF_04": {"district": "North Sikkim", "tehsil": "Chungthang", "state": "Sikkim", "pop": 3950},
    "JRT_TST_05": {"district": "South Sikkim", "tehsil": "Jorethang", "state": "Sikkim", "pop": 9009},

    # Tripura
    "AGR_GMT_01": {"district": "West Tripura", "tehsil": "Agartala Sadar", "state": "Tripura", "pop": 400004},
    "DMB_MNU_02": {"district": "North Tripura", "tehsil": "Dharmanagar", "state": "Tripura", "pop": 40595},
    "UDP_GMT_03": {"district": "Gomati", "tehsil": "Udaipur", "state": "Tripura", "pop": 32758},
    "BLN_DEO_04": {"district": "South Tripura", "tehsil": "Belonia", "state": "Tripura", "pop": 19996},
    "JMP_JMP_05": {"district": "North Tripura", "tehsil": "Jampui Hills", "state": "Tripura", "pop": 11200},

    # Himachal Pradesh
    "MND_URBAN_01": {"district": "Mandi", "tehsil": "Mandi Sadar", "state": "Himachal Pradesh", "pop": 26400},
    "PND_DAM_02": {"district": "Mandi", "tehsil": "Sadar Mandi", "state": "Himachal Pradesh", "pop": 5200},
    "AUT_JNC_03": {"district": "Mandi", "tehsil": "Thalout", "state": "Himachal Pradesh", "pop": 3800},
    "THL_GRG_04": {"district": "Mandi", "tehsil": "Thalout", "state": "Himachal Pradesh", "pop": 2900},
    "JGN_VLY_05": {"district": "Mandi", "tehsil": "Joginder Nagar", "state": "Himachal Pradesh", "pop": 12500},
    "DHR_KHD_06": {"district": "Mandi", "tehsil": "Dharampur", "state": "Himachal Pradesh", "pop": 8700},
    "SDR_BSN_07": {"district": "Mandi", "tehsil": "Sundernagar", "state": "Himachal Pradesh", "pop": 24500},
}


def seed_regional_model_villages():
    """Reads all regional configs and seeds villages table."""
    config_dir = ROOT / "ml" / "configs" / "regions"
    db = SessionLocal()
    added_count = 0
    updated_count = 0

    try:
        for yaml_file in sorted(config_dir.glob("*.yaml")):
            with open(yaml_file, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            
            reg_info = cfg.get("region", {})
            slug = reg_info.get("slug")
            state_default = reg_info.get("state", slug.replace("_", " ").title())
            stations = cfg.get("stations", {})

            for sid, s in stations.items():
                meta = STATION_METADATA.get(sid, {})
                st_name = meta.get("state", state_default)
                dist_name = meta.get("district", "General")
                tehsil_name = meta.get("tehsil", dist_name)
                pop = meta.get("pop", 25000)

                v_name = s.get("name", sid)
                lat = float(s.get("latitude", 0.0))
                lon = float(s.get("longitude", 0.0))
                elev = float(s.get("elevation_m", 500.0))
                slope = float(s.get("catchment_slope_deg", 15.0))
                dist_to_river_km = float(s.get("dist_to_river_m", 120.0)) / 1000.0

                existing = db.query(Village).filter(Village.id == sid).first()
                if not existing:
                    # Also check by name
                    existing = db.query(Village).filter(Village.name == v_name).first()

                if existing:
                    # Update fields if needed
                    existing.state = st_name
                    existing.district = dist_name
                    existing.tehsil = tehsil_name
                    existing.elevation = elev
                    existing.slope = slope
                    existing.distance_to_river = dist_to_river_km
                    existing.latitude = lat
                    existing.longitude = lon
                    existing.geometry = {"type": "Point", "coordinates": [lon, lat]}
                    updated_count += 1
                else:
                    new_v = Village(
                        id=sid,
                        name=v_name,
                        tehsil=tehsil_name,
                        district=dist_name,
                        state=st_name,
                        population=pop,
                        elevation=elev,
                        slope=slope,
                        distance_to_river=dist_to_river_km,
                        historical_flood_frequency=0.60,
                        vulnerability_index=0.50,
                        latitude=lat,
                        longitude=lon,
                        geometry={"type": "Point", "coordinates": [lon, lat]}
                    )
                    db.add(new_v)
                    added_count += 1

        db.commit()
        print(f"Successfully seeded regional ML stations: {added_count} added, {updated_count} updated.")
        
        # Verify distinct states in database
        states = [r[0] for r in db.query(Village.state).distinct().order_by(Village.state).all()]
        print(f"Total states now in database ({len(states)}): {states}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding regional model villages: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_regional_model_villages()
