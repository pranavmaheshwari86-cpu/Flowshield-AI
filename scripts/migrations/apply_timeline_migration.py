import sqlite3
import os

db_path = "flowshield.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Applying migration to flowshield.db...")

# 1. Compound index on environmental_observations
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_obs_village_time 
ON environmental_observations(village_id, timestamp DESC);
""")
print("[OK] Created/verified index idx_obs_village_time")

# 2. Numerical weather forecast table
cursor.execute("""
CREATE TABLE IF NOT EXISTS numerical_weather_forecasts (
    id TEXT PRIMARY KEY,
    village_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    run_timestamp TIMESTAMP NOT NULL,
    horizon_hours INTEGER NOT NULL,
    valid_at TIMESTAMP NOT NULL,
    precipitation_mm_hr REAL NOT NULL,
    cumulative_precip_mm REAL NOT NULL,
    temperature_2m_c REAL,
    surface_pressure_hpa REAL,
    fetched_at TIMESTAMP NOT NULL,
    FOREIGN KEY (village_id) REFERENCES villages(id)
);
""")
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_forecast_lookup 
ON numerical_weather_forecasts(village_id, valid_at ASC);
""")
print("[OK] Created/verified table numerical_weather_forecasts & index idx_forecast_lookup")

# 3. Dynamic watershed threshold configurations
cursor.execute("""
CREATE TABLE IF NOT EXISTS watershed_threshold_configs (
    id TEXT PRIMARY KEY,
    watershed_id TEXT NOT NULL,
    configuration_version TEXT NOT NULL,
    watch_threshold REAL NOT NULL DEFAULT 25.0,
    high_threshold REAL NOT NULL DEFAULT 50.0,
    critical_threshold REAL NOT NULL DEFAULT 75.0,
    river_danger_mark_m REAL,
    effective_from TIMESTAMP NOT NULL,
    effective_until TIMESTAMP
);
""")
print("[OK] Created/verified table watershed_threshold_configs")

# 4. Telemetry synchronization logs index
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_sync_provider_time 
ON telemetry_sync_logs(provider, timestamp DESC);
""")
print("[OK] Verified index idx_sync_provider_time on telemetry_sync_logs")

conn.commit()
conn.close()
print("Migration completed successfully!")
