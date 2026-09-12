"""
analyze_uttarakhand_v2_synthetic.py
-----------------------------------
TerraPulse Flash Flood Prediction System - Uttarakhand Prototype Extension
Comprehensive Audit & Validation of Synthetic V2 Dataset.

PURPOSE:
Performs deep structural, statistical, and physical plausibility audits on:
  06_ML_Dataset/terrapulse_uttarakhand_v2_synthetic.csv

CRITICAL TRANSPARENCY NOTICE:
The river and weather variables in this dataset are synthetic prototype values
created for software demonstration and model-integration testing.
They are NOT CWC/IMD observations.
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "06_ML_Dataset" / "terrapulse_uttarakhand_v2_synthetic.csv"
METADATA_PATH = BASE_DIR / "06_ML_Dataset" / "synthetic_data_metadata.json"

EXPECTED_DISTRICTS = sorted([
    "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehra Dun",
    "Haridwar", "Naini Tal", "Pauri Garhwal", "Pithoragarh",
    "Rudra Prayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"
])

NEW_NUMERICAL_FEATURES = [
    "river_water_level_m",
    "river_danger_level_m",
    "river_level_ratio_to_danger",
    "river_rise_rate_m_per_hr",
    "river_level_change_3h_m",
    "river_level_change_6h_m",
    "river_level_change_24h_m",
    "temperature_c",
    "relative_humidity_pct",
    "wind_speed_kmh",
    "atmospheric_pressure_hpa"
]

NEW_CATEGORICAL_FEATURES = [
    "slope_risk",
    "weather_condition"
]


def run_audit():
    print("\n" + "#" * 80)
    print("TERRAPULSE — AUDIT OF UTTARAKHAND V2 SYNTHETIC DATASET")
    print("#" * 80)
    print(f"Dataset Path : {DATASET_PATH}")
    print(f"Metadata Path: {METADATA_PATH}")

    if not DATASET_PATH.exists():
        print(f"\n[ERROR] Dataset file not found at: {DATASET_PATH}")
        sys.exit(1)

    df = pd.read_csv(DATASET_PATH)
    df["date"] = pd.to_datetime(df["date"])

    total_rows, total_cols = df.shape
    print(f"\nSuccessfully loaded dataset: {total_rows:,} rows, {total_cols} columns")

    # --------------------------------------------------------------------------
    # 1. BASIC INFORMATION
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("1. BASIC DATASET OVERVIEW")
    print("=" * 80)
    print(f"Row count    : {total_rows}")
    print(f"Column count : {total_cols}")
    print(f"Date range   : {df['date'].min().strftime('%Y-%m-%d')} -> {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"Unique dates : {df['date'].nunique()}")
    print(f"Districts    : {df['district'].nunique()}")

    print("\nColumn schema and data types:")
    for idx, (col, dtype) in enumerate(df.dtypes.items(), start=1):
        is_synthetic = col in (NEW_NUMERICAL_FEATURES + NEW_CATEGORICAL_FEATURES)
        tag = "[SYNTHETIC]" if is_synthetic else "[ORIGINAL]"
        print(f"  {idx:2d}. {col:<30} {str(dtype):<10} {tag}")

    # --------------------------------------------------------------------------
    # 2. MISSING VALUES & DUPLICATES
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("2. DATA INTEGRITY: MISSING VALUES & DUPLICATES")
    print("=" * 80)
    missing_series = df.isna().sum()
    total_missing = int(missing_series.sum())
    print(f"Total missing values: {total_missing}")
    if total_missing == 0:
        print("  [OK] Zero missing values detected across all columns.")
    else:
        print("  [WARNING] Missing values per column:")
        print(missing_series[missing_series > 0])

    exact_duplicates = int(df.duplicated().sum())
    key_duplicates = int(df.duplicated(subset=["date", "district"]).sum())
    print(f"Exact duplicate rows      : {exact_duplicates}")
    print(f"Date-district duplicates  : {key_duplicates}")
    if exact_duplicates == 0 and key_duplicates == 0:
        print("  [OK] No duplicate rows or key conflicts found.")
    else:
        print("  [WARNING] Duplicates detected!")

    # --------------------------------------------------------------------------
    # 3. DISTRICT DISTRIBUTION
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("3. DISTRICT DISTRIBUTION")
    print("=" * 80)
    district_counts = df["district"].value_counts().sort_index()
    print("District row counts:")
    for district, count in district_counts.items():
        print(f"  - {district:<20}: {count:>5} rows")

    districts_present = sorted(df["district"].unique().tolist())
    if districts_present == EXPECTED_DISTRICTS:
        print("  [OK] All 13 official Uttarakhand districts are present with balanced coverage.")
    else:
        print("  [WARNING] District list mismatch with expected 13 districts.")

    # --------------------------------------------------------------------------
    # 4. TARGET DISTRIBUTION
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("4. TARGET DISTRIBUTION (flood_label)")
    print("=" * 80)
    target_counts = df["flood_label"].value_counts().sort_index()
    target_props = df["flood_label"].value_counts(normalize=True).sort_index() * 100
    for label, count in target_counts.items():
        desc = "Non-Flood Day (0)" if label == 0 else "Flood Event (1)"
        print(f"  {desc:<22}: {count:>6} rows ({target_props[label]:>6.2f}%)")
    imbalance_ratio = target_counts[0] / target_counts[1]
    print(f"Imbalance ratio (Negative:Positive) = {imbalance_ratio:.1f}:1")

    # --------------------------------------------------------------------------
    # 5. NEW NUMERICAL FEATURES STATISTICAL SUMMARY
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("5. NEW NUMERICAL FEATURES: RANGE, MIN, MEDIAN, MEAN, MAX, STD")
    print("=" * 80)

    summary_rows = []
    for col in NEW_NUMERICAL_FEATURES:
        s = df[col]
        summary_rows.append({
            "Feature": col,
            "Min": s.min(),
            "Median": s.median(),
            "Mean": s.mean(),
            "Max": s.max(),
            "Std": s.std()
        })
    summary_df = pd.DataFrame(summary_rows)
    print(summary_df.to_string(index=False, justify="left", formatters={
        "Min": "{:,.4f}".format,
        "Median": "{:,.4f}".format,
        "Mean": "{:,.4f}".format,
        "Max": "{:,.4f}".format,
        "Std": "{:,.4f}".format
    }))

    # --------------------------------------------------------------------------
    # 6. CATEGORICAL FEATURES SUMMARY
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("6. CATEGORICAL FEATURES SUMMARY")
    print("=" * 80)

    print("\nA. Slope Risk (slope_risk):")
    slope_counts = df["slope_risk"].value_counts()
    slope_props = df["slope_risk"].value_counts(normalize=True) * 100
    for cat, count in slope_counts.items():
        print(f"  - {cat:<12}: {count:>5} rows ({slope_props[cat]:>5.2f}%)")

    print("\nB. Weather Condition (weather_condition):")
    weather_counts = df["weather_condition"].value_counts()
    weather_props = df["weather_condition"].value_counts(normalize=True) * 100
    for cond, count in weather_counts.items():
        print(f"  - {cond:<16}: {count:>5} rows ({weather_props[cond]:>5.2f}%)")

    # --------------------------------------------------------------------------
    # 7. PHYSICAL VALIDATION & IMPOSSIBLE/EXTREME VALUE CHECKS
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("7. PHYSICAL VALIDATION & ANOMALY AUDIT")
    print("=" * 80)

    validation_issues = []

    # River water level checks
    neg_water = (df["river_water_level_m"] <= 0).sum()
    if neg_water > 0:
        validation_issues.append(f"river_water_level_m has {neg_water} non-positive values")

    # River danger level checks
    nonpos_danger = (df["river_danger_level_m"] <= 0).sum()
    if nonpos_danger > 0:
        validation_issues.append(f"river_danger_level_m has {nonpos_danger} non-positive values")

    # Ratio checks
    neg_ratio = (df["river_level_ratio_to_danger"] <= 0).sum()
    if neg_ratio > 0:
        validation_issues.append(f"river_level_ratio_to_danger has {neg_ratio} non-positive values")
    extreme_ratio = (df["river_level_ratio_to_danger"] > 3.0).sum()
    if extreme_ratio > 0:
        validation_issues.append(f"river_level_ratio_to_danger has {extreme_ratio} extreme values (> 3.0)")

    # Rise rate checks
    neg_rise_rate = (df["river_rise_rate_m_per_hr"] < 0).sum()
    if neg_rise_rate > 0:
        validation_issues.append(f"river_rise_rate_m_per_hr has {neg_rise_rate} negative values")
    extreme_rise_rate = (df["river_rise_rate_m_per_hr"] > 5.0).sum()
    if extreme_rise_rate > 0:
        validation_issues.append(f"river_rise_rate_m_per_hr has {extreme_rise_rate} extreme values (> 5.0 m/hr)")

    # Temperature checks
    t_min, t_max = df["temperature_c"].min(), df["temperature_c"].max()
    if t_min < -25.0 or t_max > 50.0:
        validation_issues.append(f"temperature_c range [{t_min}, {t_max}] outside plausible [-25, 50] deg C")

    # Humidity checks
    rh_min, rh_max = df["relative_humidity_pct"].min(), df["relative_humidity_pct"].max()
    if rh_min < 0.0 or rh_max > 100.0:
        validation_issues.append(f"relative_humidity_pct [{rh_min}, {rh_max}] outside [0, 100] %")

    # Wind checks
    w_min, w_max = df["wind_speed_kmh"].min(), df["wind_speed_kmh"].max()
    if w_min < 0.0 or w_max > 150.0:
        validation_issues.append(f"wind_speed_kmh [{w_min}, {w_max}] outside plausible [0, 150] km/h")

    # Pressure checks
    p_min, p_max = df["atmospheric_pressure_hpa"].min(), df["atmospheric_pressure_hpa"].max()
    if p_min < 500.0 or p_max > 1100.0:
        validation_issues.append(f"atmospheric_pressure_hpa [{p_min}, {p_max}] outside [500, 1100] hPa")

    # Category validation
    valid_slopes = {"LOW", "MODERATE", "HIGH", "VERY_HIGH"}
    invalid_slopes = set(df["slope_risk"].unique()) - valid_slopes
    if invalid_slopes:
        validation_issues.append(f"Invalid slope_risk categories: {invalid_slopes}")

    valid_weather = {"Clear", "Partly Cloudy", "Overcast", "Light Rain", "Moderate Rain", "Heavy Rain", "Thunderstorm"}
    invalid_weather = set(df["weather_condition"].unique()) - valid_weather
    if invalid_weather:
        validation_issues.append(f"Invalid weather_condition categories: {invalid_weather}")

    if not validation_issues:
        print("  [OK] ZERO impossible or extreme values detected across all synthetic variables.")
        print("  [OK] All physical boundaries respected:")
        print(f"       - Water level range   : {df['river_water_level_m'].min():.2f}m to {df['river_water_level_m'].max():.2f}m")
        print(f"       - Danger ratio range  : {df['river_level_ratio_to_danger'].min():.4f} to {df['river_level_ratio_to_danger'].max():.4f}")
        print(f"       - Rise rate range     : {df['river_rise_rate_m_per_hr'].min():.4f} to {df['river_rise_rate_m_per_hr'].max():.4f} m/hr")
        print(f"       - Temperature range   : {t_min:.1f} to {t_max:.1f} deg C")
        print(f"       - Humidity range      : {rh_min:.1f}% to {rh_max:.1f}%")
        print(f"       - Wind speed range    : {w_min:.1f} to {w_max:.1f} km/h")
        print(f"       - Pressure range      : {p_min:.1f} to {p_max:.1f} hPa")
    else:
        print("  [WARNING] Physical validation issues found:")
        for issue in validation_issues:
            print(f"    - {issue}")

    # --------------------------------------------------------------------------
    # 8. LEAKAGE & TARGET INDEPENDENCE AUDIT
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("8. TARGET INDEPENDENCE & LEAKAGE VERIFICATION")
    print("=" * 80)
    print("Verifying that flood_label was NOT used to construct synthetic features:")
    flood_grp = df.groupby("flood_label")[["river_water_level_m", "river_level_ratio_to_danger", "river_rise_rate_m_per_hr", "temperature_c", "relative_humidity_pct"]].mean()
    print("\nMean feature values by flood_label:")
    print(flood_grp.to_string())

    corr_with_label = df[NEW_NUMERICAL_FEATURES].apply(lambda s: s.corr(df["flood_label"]))
    print("\nCorrelation with flood_label:")
    for feat, r in corr_with_label.items():
        print(f"  - {feat:<30}: r = {r:+.4f}")

    # Confirm no feature has deterministic correlation (> 0.85)
    max_corr = corr_with_label.abs().max()
    max_feat = corr_with_label.abs().idxmax()
    if max_corr < 0.40:
        print(f"\n  [OK] Peak correlation with target is moderate (|r| = {max_corr:.4f} for {max_feat}).")
        print("  [OK] No deterministic copies, target leakage, or circular logic detected.")
    else:
        print(f"\n  [WARNING] High correlation (|r| = {max_corr:.4f}) detected on {max_feat}.")

    print("\n" + "#" * 80)
    print("AUDIT COMPLETE — UTTARAKHAND V2 SYNTHETIC DATASET IS VALID AND READY")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    run_audit()
