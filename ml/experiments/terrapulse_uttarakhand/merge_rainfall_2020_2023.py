import pandas as pd
from pathlib import Path

# ============================================================
# TERRAPULSE SIH 2026
# MERGE VALIDATED DISTRICT RAINFALL
# 2020-2023
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

RAINFALL_DIR = BASE_DIR / "01_Rainfall" / "District"
CLEANED_DIR = RAINFALL_DIR / "Cleaned"

FEATURES_DIR = BASE_DIR / "05_Features"
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = FEATURES_DIR / "rainfall_district_daily_2020_2023.csv"


print("=" * 80)
print("TERRAPULSE SIH 2026")
print("MERGING VALIDATED DISTRICT RAINFALL")
print("=" * 80)


# ------------------------------------------------------------
# Load 2020
# ------------------------------------------------------------

file_2020 = (
    RAINFALL_DIR /
    "TerraPulse_GPM_District_Rainfall_2020.csv"
)

print("\nLoading 2020...")
df_2020 = pd.read_csv(file_2020)

# Keep only required columns
df_2020 = df_2020[
    ["date", "district", "mean"]
].copy()

df_2020 = df_2020.rename(
    columns={
        "mean": "rainfall_mm"
    }
)

print(f"2020 rows: {len(df_2020)}")


# ------------------------------------------------------------
# Load 2021-2023 cleaned files
# ------------------------------------------------------------

dataframes = [df_2020]

for year in [2021, 2022, 2023]:

    file_path = (
        CLEANED_DIR /
        f"rainfall_district_{year}_clean.csv"
    )

    print(f"\nLoading {year}...")
    print(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Missing cleaned rainfall file:\n{file_path}"
        )

    df = pd.read_csv(file_path)

    # Keep only required columns
    df = df[
        ["date", "district", "rainfall_mm"]
    ].copy()

    print(f"{year} rows: {len(df)}")

    dataframes.append(df)


# ------------------------------------------------------------
# Combine
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("COMBINING DATA")
print("=" * 80)

rainfall = pd.concat(
    dataframes,
    ignore_index=True
)


# ------------------------------------------------------------
# Clean data types
# ------------------------------------------------------------

rainfall["date"] = pd.to_datetime(
    rainfall["date"],
    errors="coerce"
)

rainfall["district"] = (
    rainfall["district"]
    .astype(str)
    .str.strip()
)

rainfall["rainfall_mm"] = pd.to_numeric(
    rainfall["rainfall_mm"],
    errors="coerce"
)


# ------------------------------------------------------------
# Sort
# ------------------------------------------------------------

rainfall = rainfall.sort_values(
    ["date", "district"]
).reset_index(drop=True)


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("FINAL COMBINED RAINFALL VALIDATION")
print("=" * 80)


print("\nShape:")
print(rainfall.shape)


print("\nColumns:")
print(list(rainfall.columns))


# Missing values

print("\nMissing values:")
print(rainfall.isnull().sum())


# Duplicate district-date records

duplicates = rainfall.duplicated(
    subset=["date", "district"]
).sum()

print(
    f"\nDuplicate district-date records: {duplicates}"
)


# Unique districts

unique_districts = sorted(
    rainfall["district"]
    .dropna()
    .unique()
)

print(
    f"\nUnique districts: {len(unique_districts)}"
)

print("\nDistricts:")

for district in unique_districts:
    print(f"  - {district}")


# Dates

print("\nDate information:")

print(
    f"Minimum date: {rainfall['date'].min().date()}"
)

print(
    f"Maximum date: {rainfall['date'].max().date()}"
)

print(
    f"Unique dates: {rainfall['date'].nunique()}"
)


# Expected total rows

expected_rows = (
    13 * 366 +
    13 * 365 +
    13 * 365 +
    13 * 365
)

print("\nExpected rows:")
print(expected_rows)

print("\nActual rows:")
print(len(rainfall))


# Negative rainfall

negative_values = (
    rainfall["rainfall_mm"] < 0
).sum()

print(
    f"\nNegative rainfall values: "
    f"{negative_values}"
)


# Year distribution

print("\nRows by year:")

year_counts = (
    rainfall["date"]
    .dt.year
    .value_counts()
    .sort_index()
)

print(year_counts)


# District distribution

print("\nRows per district:")

district_counts = (
    rainfall["district"]
    .value_counts()
    .sort_index()
)

print(district_counts)


# ------------------------------------------------------------
# Validate expected structure
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("VALIDATION CHECKS")
print("=" * 80)

checks = {
    "Row count correct": len(rainfall) == expected_rows,
    "13 districts": rainfall["district"].nunique() == 13,
    "0 missing values": rainfall.isnull().sum().sum() == 0,
    "0 duplicate district-date": duplicates == 0,
    "0 negative rainfall": negative_values == 0,
    "Correct start date": (
        rainfall["date"].min()
        == pd.Timestamp("2020-01-01")
    ),
    "Correct end date": (
        rainfall["date"].max()
        == pd.Timestamp("2023-12-31")
    )
}

all_passed = True

for check_name, result in checks.items():

    if result:
        print(f"✓ {check_name}")
    else:
        print(f"✗ {check_name}")
        all_passed = False


# ------------------------------------------------------------
# Save only if validation passes
# ------------------------------------------------------------

if not all_passed:

    raise ValueError(
        "\nValidation failed. "
        "Combined rainfall dataset was NOT saved."
    )


rainfall.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# Final output
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("SUCCESS")
print("=" * 80)

print("\nFinal rainfall dataset saved to:")

print(OUTPUT_FILE)

print("\nFinal shape:")
print(rainfall.shape)

print("\nFirst 10 rows:")
print(
    rainfall.head(10).to_string(index=False)
)

print("\nLast 10 rows:")
print(
    rainfall.tail(10).to_string(index=False)
)

print("\nOriginal source files were NOT modified.")