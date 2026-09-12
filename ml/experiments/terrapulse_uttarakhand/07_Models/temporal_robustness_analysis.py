import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "06_ML_Dataset", "terrapulse_improved_ml_dataset_2020_2023.csv")
REPORT_DIR = os.path.join(BASE_DIR, "08_Reports")

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year

features = [
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "rainfall_14d",
    "rainfall_30d",
    "rainfall_max_3d",
    "rainfall_max_7d",
    "rainy_days_7d",
    "rainfall_1d_to_7d",
    "rainfall_3d_to_7d",
    "soil_moisture",
    "mean_elevation",
    "mean_slope"
]

print("=" * 70)
print("TERRAPULSE TEMPORAL ROBUSTNESS ANALYSIS")
print("=" * 70)

print("\nYEAR-WISE DATA DISTRIBUTION")

year_rows = []

for year in sorted(df["year"].unique()):
    d = df[df["year"] == year]

    year_rows.append({
        "year": year,
        "samples": len(d),
        "positive_cases": int(d["flood_label"].sum()),
        "positive_rate": d["flood_label"].mean(),
        "mean_rainfall_1d": d["rainfall_1d"].mean(),
        "mean_rainfall_3d": d["rainfall_3d"].mean(),
        "mean_rainfall_7d": d["rainfall_7d"].mean(),
        "mean_rainfall_30d": d["rainfall_30d"].mean(),
        "mean_soil_moisture": d["soil_moisture"].mean(),
        "max_rainfall_1d": d["rainfall_1d"].max(),
        "max_rainfall_7d": d["rainfall_7d"].max()
    })

year_df = pd.DataFrame(year_rows)

print(year_df.to_string(index=False))

print("\nFEATURE DISTRIBUTION BY YEAR")

distribution_rows = []

for year in sorted(df["year"].unique()):
    d = df[df["year"] == year]

    for feature in features:
        distribution_rows.append({
            "year": year,
            "feature": feature,
            "mean": d[feature].mean(),
            "std": d[feature].std(),
            "min": d[feature].min(),
            "median": d[feature].median(),
            "max": d[feature].max()
        })

distribution_df = pd.DataFrame(distribution_rows)

print(distribution_df.to_string(index=False))

print("\nFLOOD VS NON-FLOOD FEATURE COMPARISON")

comparison_rows = []

for year in sorted(df["year"].unique()):
    d = df[df["year"] == year]

    for label, label_name in [(0, "No Flood"), (1, "Flood")]:
        subset = d[d["flood_label"] == label]

        if len(subset) == 0:
            continue

        for feature in features:
            comparison_rows.append({
                "year": year,
                "class": label_name,
                "feature": feature,
                "mean": subset[feature].mean(),
                "median": subset[feature].median(),
                "std": subset[feature].std(),
                "count": len(subset)
            })

comparison_df = pd.DataFrame(comparison_rows)

print(comparison_df.to_string(index=False))

print("\nMONTH-WISE FLOOD DISTRIBUTION")

monthly = (
    df.assign(
        year_month=df["date"].dt.to_period("M")
    )
    .groupby("year_month")["flood_label"]
    .agg(["count", "sum"])
    .reset_index()
)

monthly["year"] = monthly["year_month"].dt.year
monthly["month"] = monthly["year_month"].dt.month

monthly = monthly.rename(
    columns={
        "count": "samples",
        "sum": "flood_cases"
    }
)

monthly = monthly[
    ["year", "month", "samples", "flood_cases"]
]

print(monthly.to_string(index=False))

os.makedirs(REPORT_DIR, exist_ok=True)

year_df.to_csv(
    os.path.join(REPORT_DIR, "temporal_year_summary.csv"),
    index=False
)

distribution_df.to_csv(
    os.path.join(REPORT_DIR, "temporal_feature_distributions.csv"),
    index=False
)

comparison_df.to_csv(
    os.path.join(REPORT_DIR, "temporal_flood_vs_nonflood.csv"),
    index=False
)

monthly.to_csv(
    os.path.join(REPORT_DIR, "temporal_monthly_flood_distribution.csv"),
    index=False
)

print("\nREPORTS SAVED")
print("08_Reports/temporal_year_summary.csv")
print("08_Reports/temporal_feature_distributions.csv")
print("08_Reports/temporal_flood_vs_nonflood.csv")
print("08_Reports/temporal_monthly_flood_distribution.csv")

print("\nTEMPORAL ROBUSTNESS ANALYSIS COMPLETED SUCCESSFULLY")
print("=" * 70)