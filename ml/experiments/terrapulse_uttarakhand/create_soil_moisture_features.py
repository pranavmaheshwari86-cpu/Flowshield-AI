import pandas as pd
from pathlib import Path

# ============================================================
# TERRAPULSE SIH 2026
# SOIL MOISTURE FEATURE PREPARATION
#
# Source:
# NASA SMAP L4
#
# Important:
# These are regional Uttarakhand values,
# NOT district-specific observations.
#
# Main feature:
# soil_moisture = soil_moisture_rootzone
#
# Output:
# 05_Features/soil_moisture_features_2020_2023.csv
# ============================================================


# ------------------------------------------------------------
# 1. PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

SOIL_DIR = (
    BASE_DIR
    / "02_Soil_Moisture"
)

FEATURES_DIR = (
    BASE_DIR
    / "05_Features"
)

FEATURES_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    FEATURES_DIR
    / "soil_moisture_features_2020_2023.csv"
)


YEARS = [2020, 2021, 2022, 2023]


print("=" * 80)
print("TERRAPULSE SIH 2026")
print("SOIL MOISTURE FEATURE PREPARATION")
print("=" * 80)

print("\nInput directory:")
print(SOIL_DIR)

print("\nOutput file:")
print(OUTPUT_FILE)


# ------------------------------------------------------------
# 2. CHECK INPUT DIRECTORY
# ------------------------------------------------------------

if not SOIL_DIR.exists():

    raise FileNotFoundError(
        f"\nSoil moisture directory not found:\n{SOIL_DIR}"
    )


# ------------------------------------------------------------
# 3. LOAD ALL YEARS
# ------------------------------------------------------------

all_data = []


for year in YEARS:

    print("\n" + "#" * 80)
    print(f"LOADING YEAR: {year}")
    print("#" * 80)

    file_path = (
        SOIL_DIR
        / f"SMAP_Uttarakhand_Daily_{year}.csv"
    )

    if not file_path.exists():

        raise FileNotFoundError(
            f"\nMissing file:\n{file_path}"
        )

    print("\nFile:")
    print(file_path)

    df = pd.read_csv(file_path)

    print(
        f"Original shape: {df.shape}"
    )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "date",
        "soil_moisture_rootzone"
    ]

    missing_columns = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"\nMissing columns in {year}: "
            f"{missing_columns}"
        )

    # --------------------------------------------------------
    # Keep only required columns
    # --------------------------------------------------------

    df = df[
        [
            "date",
            "soil_moisture_rootzone"
        ]
    ].copy()

    # --------------------------------------------------------
    # Rename feature
    # --------------------------------------------------------

    df = df.rename(
        columns={
            "soil_moisture_rootzone":
            "soil_moisture"
        }
    )

    # --------------------------------------------------------
    # Convert data types
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["soil_moisture"] = pd.to_numeric(
        df["soil_moisture"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    invalid_dates = (
        df["date"].isna().sum()
    )

    invalid_soil = (
        df["soil_moisture"].isna().sum()
    )

    negative_soil = (
        df["soil_moisture"] < 0
    ).sum()

    duplicate_dates = (
        df["date"].duplicated().sum()
    )

    print("\nValidation:")

    print(
        f"Invalid dates       : {invalid_dates}"
    )

    print(
        f"Invalid soil values : {invalid_soil}"
    )

    print(
        f"Negative values     : {negative_soil}"
    )

    print(
        f"Duplicate dates     : {duplicate_dates}"
    )

    if (
        invalid_dates > 0
        or invalid_soil > 0
        or negative_soil > 0
        or duplicate_dates > 0
    ):

        raise ValueError(
            f"\nValidation failed for {year}. "
            "Processing stopped."
        )

    # --------------------------------------------------------
    # Check year
    # --------------------------------------------------------

    years_found = sorted(
        df["date"]
        .dt.year
        .unique()
        .tolist()
    )

    print(
        f"Years found: {years_found}"
    )

    if years_found != [year]:

        raise ValueError(
            f"\nUnexpected year found in {year}: "
            f"{years_found}"
        )

    # --------------------------------------------------------
    # Add to list
    # --------------------------------------------------------

    all_data.append(df)


# ------------------------------------------------------------
# 4. COMBINE
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("COMBINING SOIL MOISTURE DATA")
print("=" * 80)

soil = pd.concat(
    all_data,
    ignore_index=True
)

soil = soil.sort_values(
    "date"
).reset_index(drop=True)


# ------------------------------------------------------------
# 5. FINAL VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("FINAL SOIL MOISTURE VALIDATION")
print("=" * 80)


print("\nShape:")
print(soil.shape)


print("\nColumns:")
print(list(soil.columns))


# ------------------------------------------------------------
# Missing values
# ------------------------------------------------------------

print("\nMissing values:")

print(soil.isnull().sum())


# ------------------------------------------------------------
# Duplicate dates
# ------------------------------------------------------------

duplicate_dates = (
    soil["date"].duplicated().sum()
)

print(
    f"\nDuplicate dates: "
    f"{duplicate_dates}"
)


# ------------------------------------------------------------
# Date range
# ------------------------------------------------------------

print("\nDate range:")

print(
    f"Minimum date: "
    f"{soil['date'].min().date()}"
)

print(
    f"Maximum date: "
    f"{soil['date'].max().date()}"
)


# ------------------------------------------------------------
# Unique dates
# ------------------------------------------------------------

unique_dates = (
    soil["date"].nunique()
)

print(
    f"\nUnique dates: "
    f"{unique_dates}"
)


# ------------------------------------------------------------
# Expected rows
# ------------------------------------------------------------

expected_rows = 1461

print(
    f"\nExpected rows: "
    f"{expected_rows}"
)

print(
    f"Actual rows:   "
    f"{len(soil)}"
)

# Year distribution

print("\nRows by year:")

year_counts = (
    soil["date"]
    .dt.year
    .value_counts()
    .sort_index()
)

print(year_counts)

# Soil moisture statistics

print("\nSoil moisture statistics:")

print(soil["soil_moisture"].describe())

# Negative values

negative_values = (
    soil["soil_moisture"] < 0
).sum()

print(
    f"\nNegative soil moisture values: "
    f"{negative_values}"
)

# Check daily continuity

print("\nChecking daily date continuity...")

expected_dates = pd.date_range(
    start="2020-01-01",
    end="2023-12-31",
    freq="D"
)

actual_dates = pd.DatetimeIndex(
    soil["date"]
)

missing_dates = (
    expected_dates
    .difference(actual_dates)
)

extra_dates = (
    actual_dates
    .difference(expected_dates))

print(f"Missing dates: {len(missing_dates)}")

print(f"Unexpected dates: {len(extra_dates)}")

# Final checks

print("\n" + "=" * 80)
print("FINAL CHECKS")
print("=" * 80)


checks = {

    "1461 total rows":
        len(soil) == 1461,

    "1461 unique dates":
        soil["date"].nunique() == 1461,

    "0 missing values":
        soil.isnull().sum().sum() == 0,

    "0 duplicate dates":
        duplicate_dates == 0,

    "Correct start date":
        soil["date"].min()
        == pd.Timestamp("2020-01-01"),

    "Correct end date":
        soil["date"].max()
        == pd.Timestamp("2023-12-31"),

    "0 negative values":
        negative_values == 0,

    "0 missing calendar dates":
        len(missing_dates) == 0,

    "0 unexpected calendar dates":
        len(extra_dates) == 0
}

all_passed = True

for check_name, result in checks.items():

    if result:
        print(f"✓ {check_name}")
    else:
        print(f"✗ {check_name}")

        all_passed = False


# ------------------------------------------------------------
# Save only after validation
# ------------------------------------------------------------

if not all_passed:

    raise ValueError(
        "\nFinal validation failed. "
        "Output file was NOT saved."
    )


soil.to_csv(
    OUTPUT_FILE,index=False
)

# Final output

print("\n" + "=" * 80)
print("SUCCESS")
print("=" * 80)

print("\nClean soil moisture feature file saved to:")

print(OUTPUT_FILE)

print("\nFinal shape:")
print(soil.shape)

print("\nFinal columns:")
print(list(soil.columns))

print("\nFirst 10 rows:")
print(soil.head(10).to_string(index=False))

print("\nLast 10 rows:")

print(soil.tail(10).to_string(index=False))

print("\nIMPORTANT:")
print(
    "soil_moisture is a regional Uttarakhand "
    "root-zone soil moisture feature."
)

print("It is NOT district-specific.")

print("\nOriginal SMAP source files were NOT modified.")