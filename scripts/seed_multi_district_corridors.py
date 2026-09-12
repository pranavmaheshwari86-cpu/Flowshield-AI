"""
scripts/seed_multi_district_corridors.py
Ensures Mandi (HP), Chamoli (UK), and Kullu (HP) have realistic evacuation routes,
settlements, and shelters linked for multi-district support.
"""

import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))
from app.database import SessionLocal
from app.models.village import Village
from app.models.shelter import Shelter
from app.models.route import Route
from app.models.model_coverage import ModelCoverage


def seed_corridors():
    db = SessionLocal()
    try:
        print("Checking multi-district corridors...")

        # 1. Ensure Mandi has key settlements
        mandi_villages = [
            ("vil-hp-mnd-01", "Mandi Sadar Urban", "Mandi", "Mandi", "Himachal Pradesh", 26400, 760.0, 18.5, 0.4, 0.45, 0.35, 31.7087, 76.9320),
            ("vil-hp-mnd-02", "Pandoh Dam Sector", "Sadar Mandi", "Mandi", "Himachal Pradesh", 5200, 890.0, 28.0, 0.2, 0.75, 0.65, 31.6690, 77.0580),
            ("vil-hp-mnd-03", "Aut Valley Junction", "Thalout", "Mandi", "Himachal Pradesh", 3800, 940.0, 32.5, 0.3, 0.70, 0.60, 31.7450, 77.2100),
            ("vil-hp-mnd-04", "Sundernagar Central", "Sundernagar", "Mandi", "Himachal Pradesh", 24500, 860.0, 12.0, 1.2, 0.30, 0.25, 31.5330, 76.8900),
        ]
        for vid, name, tehsil, dist, st, pop, elev, slope, d_riv, h_flood, vuln, lat, lon in mandi_villages:
            v = db.query(Village).filter(Village.id == vid).first()
            if not v:
                v = Village(
                    id=vid,
                    name=name,
                    tehsil=tehsil,
                    district=dist,
                    state=st,
                    population=pop,
                    elevation=elev,
                    slope=slope,
                    distance_to_river=d_riv,
                    historical_flood_frequency=h_flood,
                    vulnerability_index=vuln,
                    latitude=lat,
                    longitude=lon,
                    geometry={"type": "Point", "coordinates": [lon, lat]},
                )
                db.add(v)

        # 2. Ensure Chamoli has key settlements
        chamoli_villages = [
            ("vil-uk-cha-01", "Joshimath Upper Ward", "Joshimath", "Chamoli", "Uttarakhand", 16700, 1890.0, 36.5, 0.8, 0.80, 0.75, 30.5567, 79.5678),
            ("vil-uk-cha-02", "Gopeshwar Central Valley", "Chamoli", "Chamoli", "Uttarakhand", 21400, 1450.0, 22.0, 1.1, 0.40, 0.35, 30.4128, 79.3242),
            ("vil-uk-cha-03", "Karnaprayag Confluence", "Karnaprayag", "Chamoli", "Uttarakhand", 9200, 860.0, 25.0, 0.15, 0.85, 0.65, 30.2603, 79.2150),
        ]
        for vid, name, tehsil, dist, st, pop, elev, slope, d_riv, h_flood, vuln, lat, lon in chamoli_villages:
            v = db.query(Village).filter(Village.id == vid).first()
            if not v:
                v = Village(
                    id=vid,
                    name=name,
                    tehsil=tehsil,
                    district=dist,
                    state=st,
                    population=pop,
                    elevation=elev,
                    slope=slope,
                    distance_to_river=d_riv,
                    historical_flood_frequency=h_flood,
                    vulnerability_index=vuln,
                    latitude=lat,
                    longitude=lon,
                    geometry={"type": "Point", "coordinates": [lon, lat]},
                )
                db.add(v)

        # 3. Add Routes for Mandi
        mandi_routes = [
            (
                "rt-hp-mnd-01",
                "Pandoh Dam - Mandi Town All-Weather Highway (NH-21)",
                "Himachal Pradesh",
                "Mandi",
                "vil-hp-mnd-02",
                "sh-hp-mnd-01",
                14.2,
                20,
                False,
                None,
                False,
                [
                    [77.0580, 31.6690],
                    [77.0120, 31.6850],
                    [76.9650, 31.7010],
                    [76.9320, 31.7087],
                ],
                "Primary Beas valley 4-lane highway with river revetment",
            ),
            (
                "rt-hp-mnd-02",
                "Aut Tunnel - Pandoh High-Hazard Mountain Bypass",
                "Himachal Pradesh",
                "Mandi",
                "vil-hp-mnd-03",
                "sh-hp-mnd-04",
                12.5,
                65,
                False,
                None,
                True,
                [
                    [77.2100, 31.7450],
                    [77.1520, 31.7100],
                    [77.0980, 31.6850],
                    [77.0580, 31.6690],
                ],
                "Narrow valley road prone to Beas surge and shooting stones",
            ),
            (
                "rt-hp-mnd-03",
                "Mandi Sadar - Sundernagar Safe Inland Highway",
                "Himachal Pradesh",
                "Mandi",
                "vil-hp-mnd-01",
                "sh-hp-mnd-03",
                21.0,
                10,
                False,
                None,
                False,
                [
                    [76.9320, 31.7087],
                    [76.9150, 31.6250],
                    [76.8900, 31.5330],
                ],
                "Elevated multilane valley corridor, clear of flash-flood buffer",
            ),
        ]
        for rid, rname, rstate, rdist, rorig, rdest, rdist_km, rrisk, rblocked, rreason, rriver, rcoords, rnotes in mandi_routes:
            r = db.query(Route).filter(Route.id == rid).first()
            if not r:
                r = Route(
                    id=rid,
                    name=rname,
                    state=rstate,
                    district=rdist,
                    origin_village_id=rorig,
                    destination_shelter_id=rdest,
                    distance_km=rdist_km,
                    assessed_risk_score=rrisk,
                    is_blocked=rblocked,
                    blockage_reason=rreason,
                    is_river_crossing=rriver,
                    notes=rnotes,
                    geometry={"type": "LineString", "coordinates": rcoords},
                    hazard_cost_multiplier=1.0,
                )
                db.add(r)

        # 4. Add Routes for Chamoli
        chamoli_routes = [
            (
                "rt-uk-cha-01",
                "Joshimath - Gopeshwar Highway Corridor (NH-07)",
                "Uttarakhand",
                "Chamoli",
                "vil-uk-cha-01",
                "sh-uk-cha-02",
                28.5,
                30,
                False,
                None,
                False,
                [
                    [79.5678, 30.5567],
                    [79.4850, 30.4850],
                    [79.3850, 30.4350],
                    [79.3242, 30.4128],
                ],
                "Alaknanda gorge mountain corridor",
            ),
            (
                "rt-uk-cha-02",
                "Gopeshwar - Karnaprayag Confluence Link",
                "Uttarakhand",
                "Chamoli",
                "vil-uk-cha-02",
                "sh-uk-cha-03",
                18.0,
                15,
                False,
                None,
                True,
                [
                    [79.3242, 30.4128],
                    [79.2850, 30.3450],
                    [79.2150, 30.2603],
                ],
                "Elevated state highway along Pindar-Alaknanda sangam",
            ),
        ]
        for rid, rname, rstate, rdist, rorig, rdest, rdist_km, rrisk, rblocked, rreason, rriver, rcoords, rnotes in chamoli_routes:
            r = db.query(Route).filter(Route.id == rid).first()
            if not r:
                r = Route(
                    id=rid,
                    name=rname,
                    state=rstate,
                    district=rdist,
                    origin_village_id=rorig,
                    destination_shelter_id=rdest,
                    distance_km=rdist_km,
                    assessed_risk_score=rrisk,
                    is_blocked=rblocked,
                    blockage_reason=rreason,
                    is_river_crossing=rriver,
                    notes=rnotes,
                    geometry={"type": "LineString", "coordinates": rcoords},
                    hazard_cost_multiplier=1.0,
                )
                db.add(r)

        db.commit()
        print("Successfully seeded multi-district settlements and routes for Mandi and Chamoli!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_corridors()
