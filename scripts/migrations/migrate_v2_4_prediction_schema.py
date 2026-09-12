"""
scripts/migrate_v2_4_prediction_schema.py
Applies additive EXPAND migration for Phase 2 Prediction table columns:
- calibrated_probability REAL
- decision_threshold REAL DEFAULT 0.08
- threshold_exceeded INTEGER DEFAULT 0
- model_integrity_status TEXT DEFAULT 'MODEL_READY'
"""

import sqlite3
import os

DB_PATHS = [
    "flowshield.db",
    "test_flowshield.db",
    "apps/api/flowshield.db",
    "apps/api/test_flowshield.db",
]

NEW_COLUMNS = [
    ("calibrated_probability", "REAL"),
    ("decision_threshold", "REAL DEFAULT 0.08"),
    ("threshold_exceeded", "INTEGER DEFAULT 0"),
    ("model_integrity_status", "TEXT DEFAULT 'MODEL_READY'"),
]

def migrate_db(db_path: str):
    if not os.path.exists(db_path):
        return
    print(f"Checking {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check if predictions table exists
    tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "predictions" not in tables:
        print(f"  'predictions' table not in {db_path}, skipping.")
        conn.close()
        return

    existing_cols = [row[1] for row in cur.execute("PRAGMA table_info(predictions)").fetchall()]
    added = 0
    for col_name, col_def in NEW_COLUMNS:
        if col_name not in existing_cols:
            sql = f"ALTER TABLE predictions ADD COLUMN {col_name} {col_def}"
            cur.execute(sql)
            print(f"  Added column: {col_name}")
            added += 1
        else:
            print(f"  Column already exists: {col_name}")
            
    conn.commit()
    conn.close()
    print(f"Finished {db_path} ({added} columns added).")

if __name__ == "__main__":
    for p in DB_PATHS:
        migrate_db(p)
