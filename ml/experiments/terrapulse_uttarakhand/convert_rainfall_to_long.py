import pandas as pd
from pathlib import Path

# ============================================================
# TERRAPULSE SIH 2026
# CONVERT DISTRICT RAINFALL FROM WIDE -> LONG FORMAT
#
# Source:
# 01_Rainfall/District/
#
# Output:
# 01_Rainfall/District/Cleaned/
#
# IMPORTANT:
# Original source files are NOT modified.
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

INPUT_DIR = BASE_DIR / "01_Rainfall" / "District"
OUTPUT_DIR = INPUT_DIR / "Cleaned"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 2. YEARS TO CONVERT
# ------------------------------------------------------------

YEARS = [2021, 2022, 2023]


print("=" * 80)
print("TERRAPULSE SIH 2026")
print("DISTRICT RAINFALL: WIDE -> LONG CONVERSION")
print("=" * 80)

print(f"\nInput directory:")
print(INPUT_DIR)

print(f"\nOutput directory:")
print(OUTPUT_DIR)


# ------------------------------------------------------------
# 3. PROCESS EACH YEAR
# ------------------------------------------------------------

for year in YEARS:

    print("\n" + "#" * 80)
    print(f"PROCESSING YEAR: {year}")
    print("#" * 80)

    input_file = (
        INPUT_DIR /
        f"TerraPulse_GPM_District_Rainfall_{year}.csv"
    )

    output_file = (
        OUTPUT_DIR /
        f"rainfall_district_{year}_clean.csv"
    )

    # --------------------------------------------------------
    # Check source file
    # --------------------------------------------------------

    if not input_file.exists():
        print(f"ERROR: Source file not found:")
        print(input_file)
        continue

    print(f"\nSource file:")
    print(input_file)

    # --------------------------------------------------------
    # Read source file
    # --------------------------------------------------------

    df = pd.read_csv(input_file)

    print("\nOriginal shape:")
    print(df.shape)

    # --------------------------------------------------------
    # Detect rainfall columns
    # --------------------------------------------------------

    rainfall_columns = [
        col
        for col in df.columns
        if str(col).strip().lower().endswith("_rainfall")
    ]

    print(
        f"\nRainfall date columns detected: "
        f"{len(rainfall_columns)}"
    )

    if len(rainfall_columns) == 0:
        raise ValueError(
            f"No rainfall columns found in {input_file}"
        )

    # --------------------------------------------------------
    # Detect district column
    #
    # We specifically prefer ADM2_NAME because the GEE
    # export contains administrative district information.
    # --------------------------------------------------------

    district_candidates = [
        "ADM2_NAME",
        "district",
        "District",
        "district_name"
    ]

    district_column = None

    for candidate in district_candidates:

        if candidate in df.columns:
            district_column = candidate
            break

    if district_column is None:

        # Fallback: search case-insensitively
        for col in df.columns:

            if str(col).strip().lower() in [
                "adm2_name",
                "district",
                "district_name"
            ]:
                district_column = col
                break

    if district_column is None:
        raise ValueError(
            "Could not identify district column. "
            "No source file was modified."
        )

    print(f"District column selected: {district_column}")

    # --------------------------------------------------------
    # Show districts before conversion
    # --------------------------------------------------------

    districts = (
        df[district_column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    unique_districts = sorted(districts.unique())

    print(
        f"\nUnique districts before conversion: "
        f"{len(unique_districts)}"
    )

    for district in unique_districts:
        print(f"  - {district}")

    # --------------------------------------------------------
    # Convert wide -> long
    # --------------------------------------------------------

    long_df = df[
        [district_column] + rainfall_columns
    ].melt(
        id_vars=[district_column],
        value_vars=rainfall_columns,
        var_name="rainfall_date",
        value_name="rainfall_mm"
    )

    # --------------------------------------------------------
    # Rename district column
    # --------------------------------------------------------

    long_df = long_df.rename(
        columns={
            district_column: "district"
        }
    )

    # --------------------------------------------------------
    # Extract actual date from:
    #
    # 2021-01-01_rainfall
    #
    # -> 2021-01-01
    # --------------------------------------------------------

    long_df["date"] = (
        long_df["rainfall_date"]
        .astype(str)
        .str.replace(
            "_rainfall",
            "",
            regex=False
        )
    )

    # --------------------------------------------------------
    # Convert date
    # --------------------------------------------------------

    long_df["date"] = pd.to_datetime(
        long_df["date"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Convert rainfall to numeric
    # --------------------------------------------------------

    long_df["rainfall_mm"] = pd.to_numeric(
        long_df["rainfall_mm"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Keep only required columns
    # --------------------------------------------------------

    long_df = long_df[
        [
            "date",
            "district",
            "rainfall_mm"
        ]
    ]

    # --------------------------------------------------------
    # Clean district text
    # --------------------------------------------------------

    long_df["district"] = (
        long_df["district"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Sort data
    # --------------------------------------------------------

    long_df = long_df.sort_values(
        ["date", "district"]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    print("\n" + "-" * 80)
    print("VALIDATING CONVERTED DATA")
    print("-" * 80)

    print(f"\nShape: {long_df.shape}")

    print(
        f"Expected rows: "
        f"{13 * (366 if year % 4 == 0 else 365)}"
    )

    print(
        f"Actual rows:   "
        f"{len(long_df)}"
    )

    # Date validation

    invalid_dates = long_df["date"].isna().sum()

    print(
        f"\nInvalid dates: "
        f"{invalid_dates}"
    )

    if len(long_df) > 0:

        print(
            f"Minimum date: "
            f"{long_df['date'].min().date()}"
        )

        print(
            f"Maximum date: "
            f"{long_df['date'].max().date()}"
        )

        print(
            f"Unique dates: "
            f"{long_df['date'].nunique()}"
        )

    # District validation

    print(
        f"Unique districts: "
        f"{long_df['district'].nunique()}"
    )

    # Missing values

    print("\nMissing values:")

    print(
        long_df.isnull().sum()
    )

    # Negative rainfall

    negative_values = (
        long_df["rainfall_mm"] < 0
    ).sum()

    print(
        f"\nNegative rainfall values: "
        f"{negative_values}"
    )

    # District-date duplicates

    duplicate_district_dates = (
        long_df.duplicated(
            subset=["date", "district"]
        ).sum()
    )

    print(
        f"Duplicate district-date records: "
        f"{duplicate_district_dates}"
    )

    # Year consistency

    years_found = sorted(
        long_df["date"]
        .dropna()
        .dt.year
        .unique()
    )

    print(
        f"Years found in data: "
        f"{years_found}"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    long_df.to_csv(
        output_file,
        index=False
    )

    print(f"\n✓ CLEAN FILE SAVED:")
    print(output_file)

    print("\nFirst 10 rows:")

    print(
        long_df.head(10).to_string(index=False)
    )


# ------------------------------------------------------------
# FINAL MESSAGE
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("RAINFALL CONVERSION COMPLETE")
print("=" * 80)

print("\nOriginal source files were NOT modified.")

print(
    "\nCleaned files are stored in:"
)

print(OUTPUT_DIR)