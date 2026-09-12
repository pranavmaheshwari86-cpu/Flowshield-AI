"""
scripts/migrate_v2_4_sync_logs.py
Creates telemetry_sync_logs table across all databases for Phase 3 auditability.
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
CREATE TABLE IF NOT EXISTS telemetry_sync_logs (
    id VARCHAR(36) PRIMARY KEY,
    sync_id VARCHAR(36) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    timestamp DATETIME NOT NULL,
    status VARCHAR(30) NOT NULL,
    records_updated INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS ix_telemetry_sync_logs_sync_id ON telemetry_sync_logs(sync_id);
CREATE INDEX IF NOT EXISTS ix_telemetry_sync_logs_provider ON telemetry_sync_logs(provider);
"""

def migrate(db_path: str):
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()
    print(f"telemetry_sync_logs table verified/created in {db_path}")

if __name__ == "__main__":
    for p in DB_PATHS:
        migrate(p)
