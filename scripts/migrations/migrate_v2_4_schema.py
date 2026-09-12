"""
scripts/migrate_v2_4_schema.py
Flowshield — Database Schema Additive Migration (v2.4 EXPAND Step)
Safely adds new physical features, provenance, and data-state columns to environmental_observations
across all local database instances without data loss. Creates backups prior to modification.
"""

import os
import shutil
import sqlite3
from typing import List, Tuple

NEW_COLUMNS: List[Tuple[str, str]] = [
    ("rainfall_12h", "REAL"),
    ("rainfall_72h", "REAL"),
    ("deep_soil_moisture", "REAL"),
    ("soil_moisture_change", "REAL"),
    ("river_level_change_1h", "REAL"),
    ("river_level_rate", "REAL"),
    ("temperature", "REAL"),
    ("humidity", "REAL"),
    ("surface_pressure", "REAL"),
    ("wind_speed", "REAL"),
    ("source_type", "VARCHAR(40) DEFAULT 'AUTOMATED_STATION'"),
    ("data_state", "VARCHAR(30) DEFAULT 'OBSERVED'"),
    ("data_quality_status", "VARCHAR(30) DEFAULT 'VALID'"),
    ("data_quality_score", "REAL DEFAULT 1.0"),
    ("source_timestamp", "TIMESTAMP"),
    ("retrieved_at", "TIMESTAMP"),
]

TARGET_DATABASES = [
    "flowshield.db",
    "apps/api/flowshield.db",
    "test_flowshield.db",
    "apps/api/test_flowshield.db",
]


def migrate_db(db_path: str):
    if not os.path.exists(db_path):
        print(f"Skipping {db_path} (does not exist)")
        return

    backup_path = f"{db_path}.bak"
    shutil.copy2(db_path, backup_path)
    print(f"Created backup: {backup_path}")

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.execute("PRAGMA table_info(environmental_observations)")
    existing_cols = {row[1] for row in cur.fetchall()}

    added = 0
    for col_name, col_type in NEW_COLUMNS:
        if col_name not in existing_cols:
            alter_stmt = f"ALTER TABLE environmental_observations ADD COLUMN {col_name} {col_type};"
            cur.execute(alter_stmt)
            added += 1
            print(f"  + Added column: {col_name} ({col_type})")

    con.commit()
    con.close()
    print(f"Completed migration for {db_path}: {added} new columns added.\n")


if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("================================================================================")
    print("FLOWSHIELD — DATABASE EXPAND MIGRATION (v2.4)")
    print("================================================================================")
    for rel_path in TARGET_DATABASES:
        full_path = os.path.join(repo_root, rel_path)
        migrate_db(full_path)
    print("All databases successfully migrated!")
