import pandas as pd
from pathlib import Path

# ============================================================
# TERRAPULSE SIH 2026
# SOURCE DATA VALIDATION
# SOIL MOISTURE - SMAP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SOIL_DIR = BASE_DIR / "02_Soil_Moisture"

YEARS = [2020, 2021, 2022, 2023]


print("=" * 80)
print("TERRAPULSE SIH 2026")
print("SMAP SOIL MOISTURE VALIDATION")
print("=" * 80)

print("\nSoil moisture directory:")
print(SOIL_DIR)


# ------------------------------------------------------------
# Check directory
# ------------------------------------------------------------

if not SOIL_DIR.exists():

    raise FileNotFoundError(
        f"Soil moisture directory not found:\n{SOIL_DIR}"
    )

print("\n✓ Soil moisture directory found")


# ------------------------------------------------------------
# Validate each year
# ------------------------------------------------------------

results = []


for year in YEARS:

    print("\n" + "#" * 80)
    print(f"VALIDATING YEAR: {year}")
    print("#" * 80)

    filename = f"SMAP_Uttarakhand_Daily_{year}.csv"

    file_path = SOIL_DIR / filename

    print("\nFile:")
    print(file_path)


    # --------------------------------------------------------
    # File existence
    # --------------------------------------------------------

    if not file_path.exists():

        print("❌ FILE NOT FOUND")
        continue

    print("✓ File exists")


    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = pd.read_csv(file_path)

    print("\n1. SHAPE")
    print("-" * 40)

    print(f"Rows    : {df.shape[0]}")
    print(f"Columns : {df.shape[1]}")


    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    print("\n2. COLUMNS")
    print("-" * 40)

    for i, col in enumerate(df.columns, 1):

        print(f"{i}. {col}")


    # --------------------------------------------------------
    # First rows
    # --------------------------------------------------------

    print("\n3. FIRST 5 ROWS")
    print("-" * 40)

    print(
        df.head().to_string(index=False)
    )


    # --------------------------------------------------------
    # Data types
    # --------------------------------------------------------

    print("\n4. DATA TYPES")
    print("-" * 40)

    print(df.dtypes)


    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    print("\n5. MISSING VALUES")
    print("-" * 40)

    print(df.isnull().sum())

    total_missing = df.isnull().sum().sum()

    print(
        f"\nTotal missing values: {total_missing}"
    )


    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    print("\n6. DUPLICATE ROWS")
    print("-" * 40)

    duplicate_rows = df.duplicated().sum()

    print(
        f"Duplicate complete rows: "
        f"{duplicate_rows}"
    )


    # --------------------------------------------------------
    # Detect date column
    # --------------------------------------------------------

    date_candidates = [
        col
        for col in df.columns
        if "date" in str(col).lower()
    ]

    print("\n7. DATE COLUMN DETECTION")
    print("-" * 40)

    print(
        f"Possible date columns: "
        f"{date_candidates}"
    )

    date_col = None

    if date_candidates:

        date_col = date_candidates[0]

        parsed_dates = pd.to_datetime(
            df[date_col],
            errors="coerce"
        )

        invalid_dates = parsed_dates.isna().sum()

        print(
            f"Selected date column: "
            f"{date_col}"
        )

        print(
            f"Invalid dates: "
            f"{invalid_dates}"
        )

        if parsed_dates.notna().any():

            print(
                f"Minimum date: "
                f"{parsed_dates.min().date()}"
            )

            print(
                f"Maximum date: "
                f"{parsed_dates.max().date()}"
            )

            print(
                f"Unique dates: "
                f"{parsed_dates.nunique()}"
            )


    # --------------------------------------------------------
    # Detect soil moisture column
    # --------------------------------------------------------

    print("\n8. SOIL MOISTURE COLUMN DETECTION")
    print("-" * 40)

    soil_keywords = [
        "soil",
        "moisture",
        "sm"
    ]

    soil_candidates = [
        col
        for col in df.columns
        if any(
            keyword in str(col).lower()
            for keyword in soil_keywords
        )
        and "date" not in str(col).lower()
    ]

    print(
        f"Possible soil moisture columns: "
        f"{soil_candidates}"
    )

    soil_col = None

    if soil_candidates:

        # Prefer columns containing both soil/moisture
        preferred = [
            col
            for col in soil_candidates
            if (
                "soil" in str(col).lower()
                or "moisture" in str(col).lower()
            )
        ]

        if preferred:

            soil_col = preferred[0]

        else:

            soil_col = soil_candidates[0]

        print(
            f"Selected soil moisture column: "
            f"{soil_col}"
        )

        soil_numeric = pd.to_numeric(
            df[soil_col],
            errors="coerce"
        )

        invalid_soil = soil_numeric.isna().sum()

        print(
            f"Invalid/non-numeric values: "
            f"{invalid_soil}"
        )

        print("\nSoil moisture statistics:")

        print(
            soil_numeric.describe()
        )


        # ----------------------------------------------------
        # Check negative values
        # ----------------------------------------------------

        negative_soil = (
            soil_numeric < 0
        ).sum()

        print(
            f"\nNegative soil moisture values: "
            f"{negative_soil}"
        )


    # --------------------------------------------------------
    # Year consistency
    # --------------------------------------------------------

    print("\n9. YEAR CONSISTENCY")
    print("-" * 40)

    years_found = []

    if date_col is not None:

        parsed_dates = pd.to_datetime(
            df[date_col],
            errors="coerce"
        )

        years_found = sorted(
            parsed_dates
            .dropna()
            .dt.year
            .unique()
            .tolist()
        )

        print(
            f"Years found: {years_found}"
        )

        if years_found == [year]:

            print(
                f"✓ All dates belong to {year}"
            )

        else:

            print(
                "⚠ Unexpected year values detected"
            )


    # --------------------------------------------------------
    # Store result
    # --------------------------------------------------------

    results.append({

        "year": year,

        "rows": len(df),

        "columns": len(df.columns),

        "missing_values": int(
            total_missing
        ),

        "duplicate_rows": int(
            duplicate_rows
        ),

        "unique_dates": (
            parsed_dates.nunique()
            if date_col is not None
            else None
        ),

        "date_column": date_col,

        "soil_moisture_column": soil_col
    })


# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------

print("\n\n")
print("=" * 80)
print("FINAL SOIL MOISTURE VALIDATION SUMMARY")
print("=" * 80)


if results:

    summary_df = pd.DataFrame(results)

    print(
        summary_df.to_string(index=False)
    )

else:

    print(
        "No soil moisture files could be validated."
    )


print("\n" + "=" * 80)
print("SOIL MOISTURE VALIDATION COMPLETE")
print("=" * 80)

print(
    "\nIMPORTANT:"
)

print(
    "These files represent regional Uttarakhand "
    "soil moisture, not district-specific observations."
)

print(
    "No source files were modified."
)