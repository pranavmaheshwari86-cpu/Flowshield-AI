"""
scripts/migrate_v2_4_landslide.py
Creates landslide_assessments table across all databases for Phase 4.
"""

import sqlite3
import os

DB_PATHS = [
    "flowshield.db",
    "test_flowshield.db",
    "apps/api/flowshield.db",
    "apps/api/test_flowshield.db",
]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS landslide_assessments (
    id VARCHAR(36) PRIMARY KEY,
    village_id VARCHAR(36) NOT NULL,
    timestamp DATETIME NOT NULL,
    trigger_index REAL NOT NULL,
    susceptibility_level VARCHAR(30) NOT NULL,
    methodology VARCHAR(100) DEFAULT 'Empirical Rainfall-Slope Threshold (GSI / Caine 1980)',
    status VARCHAR(50) DEFAULT 'PROTOTYPE_EMPIRICAL_THRESHOLD',
    is_ml_model INTEGER DEFAULT 0,
    advisory_notice TEXT,
    FOREIGN KEY(village_id) REFERENCES villages(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_landslide_assessments_village_id ON landslide_assessments(village_id);
"""

def migrate(db_path: str):
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()
    print(f"landslide_assessments table verified/created in {db_path}")

if __name__ == "__main__":
    for p in DB_PATHS:
        migrate(p)
