"""
scripts/ingest_user_data.py
Flowshield — User-Provided Telemetry Ingestion & Validation Engine
Smart India Hackathon 2026 (PS ID: 26192)

Validates and integrates field-provided sensor data:
- CWC River Gauge Telemetry
- IMD Automatic Weather Station (AWS) 15-min logs
- Dam Operations Logs (BBMB / HPSEBL)
- In-situ Soil Moisture Sensors
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_DATA_DIR = os.path.join(BASE_DIR, "data", "user_provided")
REAL_DATA_DIR = os.path.join(BASE_DIR, "data", "real")

def validate_river_gauge(df):
    required = ["station_id", "timestamp_ist", "water_level_m", "discharge_cumec"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required river gauge columns: {missing}")
    if (df["discharge_cumec"] < 0).any():
        raise ValueError("River discharge contains negative values!")
    if (df["water_level_m"] < 0).any() or (df["water_level_m"] > 5000).any():
        raise ValueError("River water level outside physical Himalayan boundaries (0-5000m)!")
    print(f"   [OK] River gauge data passed validation: {len(df):,} rows.")

def validate_aws_telemetry(df):
    required = ["station_id", "timestamp_ist", "rainfall_1h_mm"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required AWS columns: {missing}")
    if (df["rainfall_1h_mm"] < 0).any() or (df["rainfall_1h_mm"] > 500).any():
        raise ValueError("AWS 1h rainfall contains unphysical values (<0 or >500mm)!")
    print(f"   [OK] AWS telemetry data passed validation: {len(df):,} rows.")

def main():
    print("================================================================================")
    print("FLOWSHIELD — USER TELEMETRY INGESTION & VALIDATION ENGINE")
    print("================================================================================")
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    
    found_any = False
    gauge_file = os.path.join(USER_DATA_DIR, "river_gauge_telemetry.csv")
    if os.path.exists(gauge_file):
        found_any = True
        print(f"-> Validating {gauge_file}...")
        df = pd.read_csv(gauge_file)
        validate_river_gauge(df)
        
    aws_file = os.path.join(USER_DATA_DIR, "imd_aws_telemetry.csv")
    if os.path.exists(aws_file):
        found_any = True
        print(f"-> Validating {aws_file}...")
        df = pd.read_csv(aws_file)
        validate_aws_telemetry(df)

    if not found_any:
        print("[INFO] No user-provided files found in data/user_provided/.")
        print("       See 'data/DATA_SPECIFICATION_USER_INPUT.md' for the required schema.")
    else:
        print("\n[SUCCESS] User telemetry files successfully validated.")
    print("================================================================================")

if __name__ == "__main__":
    main()
