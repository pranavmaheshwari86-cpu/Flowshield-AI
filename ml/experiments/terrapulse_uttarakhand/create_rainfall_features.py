import pandas as pd
from pathlib import Path

# ============================================================
# TERRAPULSE SIH 2026
# RAINFALL FEATURE ENGINEERING
#
# Input:
# 05_Features/rainfall_district_daily_2020_2023.csv
#
# Output:
# 05_Features/rainfall_features_2020_2023.csv
#
# Features:
# rainfall_1d
# rainfall_3d
# rainfall_7d
# ============================================================


# ------------------------------------------------------------
# 1. PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR
    / "05_Features"
    / "rainfall_district_daily_2020_2023.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "05_Features"
    / "rainfall_features_2020_2023.csv"
)


print("=" * 80)
print("TERRAPULSE SIH 2026")
print("RAINFALL FEATURE ENGINEERING")
print("=" * 80)


# ------------------------------------------------------------
# 2. CHECK INPUT
# ------------------------------------------------------------

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"\nInput rainfall dataset not found:\n{INPUT_FILE}"
    )

print("\nInput file:")
print(INPUT_FILE)


# ------------------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("\nOriginal shape:")
print(df.shape)

print("\nOriginal columns:")
print(list(df.columns))


# ------------------------------------------------------------
# 4. BASIC INPUT VALIDATION
# ------------------------------------------------------------

required_columns = [
    "date",
    "district",
    "rainfall_mm"
]

missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing_columns:

    raise ValueError(
        f"\nMissing required columns: {missing_columns}"
    )


# ------------------------------------------------------------
# 5. DATA TYPES
# ------------------------------------------------------------

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df["district"] = (
    df["district"]
    .astype(str)
    .str.strip()
)

df["rainfall_mm"] = pd.to_numeric(
    df["rainfall_mm"],
    errors="coerce"
)


# ------------------------------------------------------------
# 6. CHECK INVALID VALUES
# ------------------------------------------------------------

invalid_dates = df["date"].isna().sum()
invalid_rainfall = df["rainfall_mm"].isna().sum()
negative_rainfall = (
    df["rainfall_mm"] < 0
).sum()

duplicate_records = df.duplicated(
    subset=["date", "district"]
).sum()

print("\nInput validation:")
print(f"Invalid dates              : {invalid_dates}")
print(f"Invalid rainfall values    : {invalid_rainfall}")
print(f"Negative rainfall values   : {negative_rainfall}")
print(f"Duplicate district-date    : {duplicate_records}")


if (
    invalid_dates > 0
    or invalid_rainfall > 0
    or negative_rainfall > 0
    or duplicate_records > 0
):

    raise ValueError(
        "\nInput validation failed. "
        "Feature engineering stopped."
    )


# ------------------------------------------------------------
# 7. SORT BY DISTRICT + DATE
# ------------------------------------------------------------

df = df.sort_values(
    ["district", "date"]
).reset_index(drop=True)


# ------------------------------------------------------------
# 8. CREATE FEATURES
# ------------------------------------------------------------

# Today's rainfall
df["rainfall_1d"] = df["rainfall_mm"]


# Previous 2 days + today
df["rainfall_3d"] = (
    df.groupby("district")["rainfall_mm"]
    .transform(
        lambda x: x.rolling(
            window=3,
            min_periods=3
        ).sum()
    )
)


# Previous 6 days + today
df["rainfall_7d"] = (
    df.groupby("district")["rainfall_mm"]
    .transform(
        lambda x: x.rolling(
            window=7,
            min_periods=7
        ).sum()
    )
)


# ------------------------------------------------------------
# 9. REMOVE RAW COLUMN
# ------------------------------------------------------------

df = df[
    [
        "date",
        "district",
        "rainfall_1d",
        "rainfall_3d",
        "rainfall_7d"
    ]
]


# ------------------------------------------------------------
# 10. VALIDATE FEATURE DATASET
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("FEATURE VALIDATION")
print("=" * 80)

print("\nShape:")
print(df.shape)

print("\nColumns:")
print(list(df.columns))


# Missing values

print("\nMissing values:")
print(df.isnull().sum())


# Why missing values exist:
#
# First 2 days of each district -> rainfall_3d unavailable
# First 6 days of each district -> rainfall_7d unavailable
#
# This is expected and NOT an error at this stage.

expected_3d_missing = 13 * 2
expected_7d_missing = 13 * 6

actual_3d_missing = df["rainfall_3d"].isna().sum()
actual_7d_missing = df["rainfall_7d"].isna().sum()

print("\nExpected rolling-feature missing values:")
print(f"rainfall_3d expected: {expected_3d_missing}")
print(f"rainfall_7d expected: {expected_7d_missing}")

print("\nActual rolling-feature missing values:")
print(f"rainfall_3d actual  : {actual_3d_missing}")
print(f"rainfall_7d actual  : {actual_7d_missing}")


# ------------------------------------------------------------
# 11. CHECK DISTRICT COUNTS
# ------------------------------------------------------------

print("\nRows per district:")

district_counts = (
    df["district"]
    .value_counts()
    .sort_index()
)

print(district_counts)


# ------------------------------------------------------------
# 12. CHECK DATE RANGE
# ------------------------------------------------------------

print("\nDate range:")
print(f"Minimum: {df['date'].min().date()}")
print(f"Maximum: {df['date'].max().date()}")


# ------------------------------------------------------------
# 13. CHECK FEATURE VALUES
# ------------------------------------------------------------

for feature in [
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d"
]:

    negative_count = (
        df[feature].dropna() < 0
    ).sum()

    print(
        f"\n{feature} negative values: "
        f"{negative_count}"
    )


# ------------------------------------------------------------
# 14. DISPLAY SAMPLE
# ------------------------------------------------------------

print("\nFirst 15 rows:")
print(
    df.head(15).to_string(index=False)
)


# ------------------------------------------------------------
# 15. DISPLAY SAMPLE FROM MIDDLE
# ------------------------------------------------------------

print("\nSample around first complete 7-day window:")

sample_district = df["district"].iloc[0]

sample = df[
    df["district"] == sample_district
].head(10)

print(
    sample.to_string(index=False)
)


# ------------------------------------------------------------
# 16. FINAL CHECKS
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("FINAL CHECKS")
print("=" * 80)

checks = {

    "18,993 total rows":
        len(df) == 18993,

    "13 districts":
        df["district"].nunique() == 13,

    "Correct start date":
        df["date"].min()
        == pd.Timestamp("2020-01-01"),

    "Correct end date":
        df["date"].max()
        == pd.Timestamp("2023-12-31"),

    "Correct rainfall_3d missing count":
        actual_3d_missing
        == expected_3d_missing,

    "Correct rainfall_7d missing count":
        actual_7d_missing
        == expected_7d_missing,

    "No negative rainfall_1d":
        (df["rainfall_1d"] < 0).sum() == 0,

    "No negative rainfall_3d":
        (df["rainfall_3d"].dropna() < 0).sum() == 0,

    "No negative rainfall_7d":
        (df["rainfall_7d"].dropna() < 0).sum() == 0
}


all_passed = True

for check_name, result in checks.items():

    if result:
        print(f"✓ {check_name}")
    else:
        print(f"✗ {check_name}")
        all_passed = False


# ------------------------------------------------------------
# 17. SAVE
# ------------------------------------------------------------

if not all_passed:

    raise ValueError(
        "\nFinal validation failed. "
        "Feature dataset was NOT saved."
    )


df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# 18. SUCCESS
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("SUCCESS")
print("=" * 80)

print("\nRainfall feature dataset saved to:")
print(OUTPUT_FILE)

print("\nFinal shape:")
print(df.shape)

print("\nFinal columns:")
print(list(df.columns))

print("\nOriginal rainfall dataset was NOT modified.")