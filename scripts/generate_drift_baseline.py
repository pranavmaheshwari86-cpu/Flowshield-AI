"""
scripts/generate_drift_baseline.py
Flowshield — Generates Baseline Feature Distributions & 10-Bin Reference for Drift Monitoring (Phase 17)
"""

import os
import sys
import json
import numpy as np
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES

TRAIN_SPLIT_PATH = os.path.join(REPO_ROOT, "ml", "data", "splits", "train_split.csv")
REAL_DATA_PATH = os.path.join(REPO_ROOT, "data", "real", "mandi_real_hydrology_features.csv")
OUTPUT_PATH = os.path.join(REPO_ROOT, "ml", "reports", "drift_baseline_reference.json")


def generate_drift_baseline():
    if os.path.exists(TRAIN_SPLIT_PATH):
        source_path = TRAIN_SPLIT_PATH
        print(f"Loading training split from {TRAIN_SPLIT_PATH}")
    else:
        source_path = REAL_DATA_PATH
        print(f"Loading real hydrology data from {REAL_DATA_PATH}")

    df = pd.read_csv(source_path)
    print(f"Dataset shape: {df.shape}")

    baseline_data = {
        "source_dataset": os.path.basename(source_path),
        "total_training_samples": len(df),
        "feature_count": len(CANONICAL_FEATURE_NAMES),
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "features": {},
    }

    for feat in CANONICAL_FEATURE_NAMES:
        if feat not in df.columns:
            print(f"Warning: {feat} not in columns, skipping.")
            continue

        s = df[feat].dropna()
        vals = s.values

        # Quantiles (deciles 10%, 20%, ..., 90%)
        deciles = [float(np.percentile(vals, p)) for p in range(10, 100, 10)]

        # 10 equal-width or quantile bin edges
        hist, bin_edges = np.histogram(vals, bins=10)
        bin_proportions = (hist / len(vals)).tolist()

        baseline_data["features"][feat] = {
            "mean": round(float(np.mean(vals)), 4),
            "std": round(float(np.std(vals)), 4) if np.std(vals) > 1e-6 else 1.0,
            "min": round(float(np.min(vals)), 4),
            "max": round(float(np.max(vals)), 4),
            "median": round(float(np.median(vals)), 4),
            "p25": round(float(np.percentile(vals, 25)), 4),
            "p75": round(float(np.percentile(vals, 75)), 4),
            "deciles": [round(d, 4) for d in deciles],
            "bin_edges": [round(float(b), 4) for b in bin_edges],
            "bin_proportions": [round(float(p), 4) for p in bin_proportions],
        }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(baseline_data, f, indent=2)

    print(f"Drift baseline reference saved to {OUTPUT_PATH}")
    print(f"Features parameterized: {len(baseline_data['features'])}")


if __name__ == "__main__":
    generate_drift_baseline()
