"""
scripts/migrations/migrate_v3_0_shelters_routes.py
Flowshield — Database Schema Additive Migration (v3.0 Shelters & Routes Schema Alignment)

Safely adds all missing columns to `shelters` and `routes` tables across SQLite databases,
preventing `sqlite3.OperationalError: no such column: shelters.state` and route column drift.
Backs up target database prior to alteration.
"""

import os
import shutil
import sqlite3
from typing import List, Tuple

SHELTER_NEW_COLUMNS: List[Tuple[str, str]] = [
    ("state", "VARCHAR(100) DEFAULT 'Uttarakhand'"),
    ("district", "VARCHAR(100) DEFAULT 'Rudraprayag'"),
    ("subdistrict_block", "VARCHAR(100)"),
    ("village_town", "VARCHAR(100)"),
    ("address", "VARCHAR(255)"),
    ("capacity", "INTEGER"),
    ("operational_status", "VARCHAR(30) DEFAULT 'OPERATIONAL'"),
    ("medical_facility", "BOOLEAN DEFAULT 1"),
    ("generator_available", "BOOLEAN DEFAULT 1"),
    ("water_available", "BOOLEAN DEFAULT 1"),
    ("food_available", "BOOLEAN DEFAULT 1"),
    ("toilets_available", "BOOLEAN DEFAULT 1"),
    ("electricity_available", "BOOLEAN DEFAULT 1"),
    ("communication_available", "BOOLEAN DEFAULT 1"),
    ("wheelchair_accessible", "BOOLEAN DEFAULT 0"),
    ("pet_friendly_if_known", "BOOLEAN"),
    ("is_24x7", "BOOLEAN DEFAULT 1"),
    ("managing_authority", "VARCHAR(150)"),
    ("source_name", "VARCHAR(150)"),
    ("source_url", "VARCHAR(500)"),
    ("source_type", "VARCHAR(50)"),
    ("source_last_verified", "VARCHAR(50)"),
    ("data_last_updated", "TIMESTAMP"),
    ("verification_status", "VARCHAR(30) DEFAULT 'VERIFIED'"),
    ("confidence_score", "INTEGER DEFAULT 85"),
]

ROUTE_NEW_COLUMNS: List[Tuple[str, str]] = [
    ("state", "VARCHAR(100) DEFAULT 'Uttarakhand'"),
    ("district", "VARCHAR(100) DEFAULT 'Rudraprayag'"),
]

TARGET_DATABASES = [
    "flowshield.db",
    "apps/api/flowshield.db",
    "test_flowshield.db",
    "apps/api/test_flowshield.db",
]


def migrate_db(db_path: str):
    if not os.path.exists(db_path):
        return

    backup_path = f"{db_path}.bak"
    shutil.copy2(db_path, backup_path)
    print(f"Created backup: {backup_path}")

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # 1. Update shelters table with schema parity
    cur.execute("PRAGMA table_info(shelters)")
    shelter_existing = {row[1] for row in cur.fetchall()}
    added_shelter_cols = 0
    for col_name, col_def in SHELTER_NEW_COLUMNS:
        if col_name not in shelter_existing:
            stmt = f"ALTER TABLE shelters ADD COLUMN {col_name} {col_def};"
            cur.execute(stmt)
            added_shelter_cols += 1

    # Backfill capacity from total_capacity if capacity is null
    cur.execute("UPDATE shelters SET capacity = total_capacity WHERE capacity IS NULL AND total_capacity IS NOT NULL;")

    # Rebuild shelters table if legacy NOT NULL exists on current_occupancy
    cur.execute("PRAGMA table_info(shelters)")
    cols_info = {row[1]: row for row in cur.fetchall()}
    if cols_info.get("current_occupancy") and cols_info["current_occupancy"][3] == 1:
        cur.execute("PRAGMA foreign_keys=OFF")
        create_ddl = """
        CREATE TABLE shelters_new (
            id VARCHAR(36) NOT NULL, 
            name VARCHAR(150) NOT NULL, 
            type VARCHAR(60) NOT NULL, 
            state VARCHAR(100) NOT NULL, 
            district VARCHAR(100) NOT NULL, 
            subdistrict_block VARCHAR(100), 
            village_town VARCHAR(100), 
            address VARCHAR(255), 
            capacity INTEGER, 
            total_capacity INTEGER, 
            current_occupancy INTEGER, 
            status VARCHAR(20) NOT NULL, 
            operational_status VARCHAR(30) NOT NULL, 
            has_medical BOOLEAN NOT NULL, 
            medical_facility BOOLEAN NOT NULL, 
            has_power_backup BOOLEAN NOT NULL, 
            generator_available BOOLEAN NOT NULL, 
            water_available BOOLEAN NOT NULL, 
            food_available BOOLEAN NOT NULL, 
            toilets_available BOOLEAN NOT NULL, 
            electricity_available BOOLEAN NOT NULL, 
            communication_available BOOLEAN NOT NULL, 
            wheelchair_accessible BOOLEAN NOT NULL, 
            pet_friendly_if_known BOOLEAN, 
            is_24x7 BOOLEAN NOT NULL, 
            managing_authority VARCHAR(150), 
            contact_person VARCHAR(100), 
            contact_phone VARCHAR(30), 
            latitude FLOAT NOT NULL, 
            longitude FLOAT NOT NULL, 
            geometry JSON, 
            source_name VARCHAR(150), 
            source_url VARCHAR(500), 
            source_type VARCHAR(50), 
            source_last_verified VARCHAR(50), 
            data_last_updated DATETIME, 
            verification_status VARCHAR(30) NOT NULL, 
            confidence_score INTEGER NOT NULL, 
            created_at DATETIME, 
            PRIMARY KEY (id)
        )
        """
        cur.execute(create_ddl)
        cur.execute("PRAGMA table_info(shelters)")
        old_cols = [r[1] for r in cur.fetchall()]
        cur.execute("PRAGMA table_info(shelters_new)")
        new_cols = [r[1] for r in cur.fetchall()]
        common_cols = [c for c in old_cols if c in new_cols]
        col_str = ", ".join(common_cols)
        cur.execute(f"INSERT INTO shelters_new ({col_str}) SELECT {col_str} FROM shelters")
        cur.execute("DROP TABLE shelters")
        cur.execute("ALTER TABLE shelters_new RENAME TO shelters")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_shelters_name ON shelters (name)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_shelters_state ON shelters (state)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_shelters_district ON shelters (district)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_shelters_latitude ON shelters (latitude)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_shelters_longitude ON shelters (longitude)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_shelters_verification_status ON shelters (verification_status)")
        cur.execute("PRAGMA foreign_keys=ON")

    # 2. Update routes table
    cur.execute("PRAGMA table_info(routes)")
    route_existing = {row[1] for row in cur.fetchall()}
    added_route_cols = 0
    for col_name, col_def in ROUTE_NEW_COLUMNS:
        if col_name not in route_existing:
            stmt = f"ALTER TABLE routes ADD COLUMN {col_name} {col_def};"
            cur.execute(stmt)
            added_route_cols += 1

    con.commit()
    con.close()
    print(f"Successfully migrated {db_path}: added {added_shelter_cols} shelter columns, {added_route_cols} route columns.")


def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    for target in TARGET_DATABASES:
        full_path = os.path.join(root_dir, target)
        migrate_db(full_path)


if __name__ == "__main__":
    main()
