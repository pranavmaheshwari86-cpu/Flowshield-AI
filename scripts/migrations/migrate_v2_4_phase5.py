"""
scripts/migrate_v2_4_phase5.py
Applies additive EXPAND migrations for Phase 5:
- alerts table: is_advisory INTEGER DEFAULT 1, policy_version TEXT DEFAULT '2.4.0', requires_authority_coordination INTEGER DEFAULT 0
- routes table: hazard_cost_multiplier REAL DEFAULT 1.0
- unique index on alerts(village_id, dedup_key, status)
"""

import sqlite3
import os

DB_PATHS = [
    "flowshield.db",
    "test_flowshield.db",
    "apps/api/flowshield.db",
    "apps/api/test_flowshield.db",
]

def migrate(db_path: str):
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Update alerts table
    alert_cols = [r[1] for r in cur.execute("PRAGMA table_info(alerts)").fetchall()]
    if "is_advisory" not in alert_cols:
        cur.execute("ALTER TABLE alerts ADD COLUMN is_advisory INTEGER DEFAULT 1")
    if "policy_version" not in alert_cols:
        cur.execute("ALTER TABLE alerts ADD COLUMN policy_version TEXT DEFAULT '2.4.0'")
    if "requires_authority_coordination" not in alert_cols:
        cur.execute("ALTER TABLE alerts ADD COLUMN requires_authority_coordination INTEGER DEFAULT 0")

    # Deduplicate existing historical duplicates before creating the unique constraint
    cur.execute("""
        DELETE FROM alerts 
        WHERE id NOT IN (
            SELECT max(id) FROM alerts GROUP BY village_id, dedup_key, status
        )
    """)

    # Create unique index for concurrency safety
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_alerts_village_dedup_status ON alerts(village_id, dedup_key, status)")

    # 2. Update routes table
    route_cols = [r[1] for r in cur.execute("PRAGMA table_info(routes)").fetchall()]
    if "hazard_cost_multiplier" not in route_cols:
        cur.execute("ALTER TABLE routes ADD COLUMN hazard_cost_multiplier REAL DEFAULT 1.0")

    conn.commit()
    conn.close()
    print(f"Phase 5 schema migration completed for {db_path}")

if __name__ == "__main__":
    for p in DB_PATHS:
        migrate(p)
