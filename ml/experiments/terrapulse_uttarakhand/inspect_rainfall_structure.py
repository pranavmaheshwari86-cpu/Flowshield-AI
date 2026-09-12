import pandas as pd
from pathlib import Path

# ============================================================
# TERRAPULSE — RAINFALL STRUCTURE INSPECTION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
RAINFALL_DIR = BASE_DIR / "01_Rainfall" / "District"

YEARS = [2021, 2022, 2023]

print("=" * 80)
print("TERRAPULSE RAINFALL STRUCTURE INSPECTION")
print("=" * 80)

for year in YEARS:

    print("\n" + "#" * 80)
    print(f"INSPECTING YEAR: {year}")
    print("#" * 80)

    file_path = RAINFALL_DIR / f"TerraPulse_GPM_District_Rainfall_{year}.csv"

    print(f"\nFILE: {file_path}")

    if not file_path.exists():
        print("❌ FILE NOT FOUND")
        continue

    # --------------------------------------------------------
    # Load file
    # --------------------------------------------------------
    df = pd.read_csv(file_path)

    print("\n1. BASIC SHAPE")
    print("-" * 40)
    print(f"Rows    : {df.shape[0]}")
    print(f"Columns : {df.shape[1]}")

    # --------------------------------------------------------
    # First 10 columns
    # --------------------------------------------------------
    print("\n2. FIRST 10 COLUMNS")
    print("-" * 40)

    for i, col in enumerate(df.columns[:10], start=1):
        print(f"{i}. {col}")

    # --------------------------------------------------------
    # Last 15 columns
    # --------------------------------------------------------
    print("\n3. LAST 15 COLUMNS")
    print("-" * 40)

    start = max(0, len(df.columns) - 15)

    for i, col in enumerate(df.columns[start:], start=start + 1):
        print(f"{i}. {col}")

    # --------------------------------------------------------
    # Rainfall date columns
    # --------------------------------------------------------
    print("\n4. RAINFALL DATE COLUMNS")
    print("-" * 40)

    rainfall_cols = [
        col for col in df.columns
        if str(col).endswith("_rainfall")
    ]

    print(f"Rainfall columns found: {len(rainfall_cols)}")

    if rainfall_cols:
        print(f"First rainfall column: {rainfall_cols[0]}")
        print(f"Last rainfall column : {rainfall_cols[-1]}")

        print("\nFirst 5 rainfall columns:")
        for col in rainfall_cols[:5]:
            print(f"  {col}")

        print("\nLast 5 rainfall columns:")
        for col in rainfall_cols[-5:]:
            print(f"  {col}")

    # --------------------------------------------------------
    # Possible district metadata columns
    # --------------------------------------------------------
    print("\n5. POSSIBLE DISTRICT COLUMNS")
    print("-" * 40)

    district_candidates = [
        col for col in df.columns
        if any(
            keyword in str(col).lower()
            for keyword in [
                "district",
                "adm2",
                "name_2",
                "name2"
            ]
        )
    ]

    if district_candidates:
        for col in district_candidates:
            print(f"  {col}")
    else:
        print("No obvious district column found.")

    # --------------------------------------------------------
    # ADM columns
    # --------------------------------------------------------
    print("\n6. ADMINISTRATIVE COLUMNS")
    print("-" * 40)

    admin_candidates = [
        col for col in df.columns
        if str(col).upper().startswith("ADM")
    ]

    if admin_candidates:
        for col in admin_candidates:
            print(f"  {col}")
    else:
        print("No ADM columns found.")

    # --------------------------------------------------------
    # Data types
    # --------------------------------------------------------
    print("\n7. DATA TYPES — IMPORTANT METADATA COLUMNS")
    print("-" * 40)

    metadata_cols = []

    for col in df.columns:
        col_lower = str(col).lower()

        if (
            "district" in col_lower
            or "adm" in col_lower
            or "name" in col_lower
            or "code" in col_lower
            or "system:index" in col_lower
        ):
            metadata_cols.append(col)

    for col in metadata_cols:
        print(f"{col} -> {df[col].dtype}")

    # --------------------------------------------------------
    # Sample rows
    # --------------------------------------------------------
    print("\n8. SAMPLE DATA — FIRST 3 ROWS")
    print("-" * 40)

    print(df.head(3).to_string())

    # --------------------------------------------------------
    # Non-null counts for metadata
    # --------------------------------------------------------
    print("\n9. NON-NULL COUNTS — METADATA")
    print("-" * 40)

    for col in metadata_cols:
        print(
            f"{col}: "
            f"{df[col].notna().sum()} / {len(df)} non-null"
        )

    # --------------------------------------------------------
    # Unique values of likely district columns
    # --------------------------------------------------------
    print("\n10. UNIQUE VALUES — POSSIBLE DISTRICT COLUMNS")
    print("-" * 40)

    for col in district_candidates:

        unique_values = df[col].dropna().astype(str).unique()

        print(f"\nColumn: {col}")
        print(f"Unique values: {len(unique_values)}")

        if len(unique_values) <= 30:
            print(list(unique_values))
        else:
            print(list(unique_values[:30]))
            print("...")

    # --------------------------------------------------------
    # Check rainfall values
    # --------------------------------------------------------
    print("\n11. RAINFALL VALUE CHECK")
    print("-" * 40)

    if rainfall_cols:

        rainfall_data = df[rainfall_cols]

        numeric_data = rainfall_data.apply(
            pd.to_numeric,
            errors="coerce"
        )

        invalid_count = (
            rainfall_data.notna() & numeric_data.isna()
        ).sum().sum()

        negative_count = (
            (numeric_data < 0)
        ).sum().sum()

        print(f"Invalid/non-numeric rainfall cells : {invalid_count}")
        print(f"Negative rainfall cells            : {negative_count}")

        print("\nRainfall numeric summary:")
        print(
            numeric_data.stack()
            .describe()
        )

    # --------------------------------------------------------
    # Expected structure
    # --------------------------------------------------------
    print("\n12. STRUCTURE INTERPRETATION")
    print("-" * 40)

    print(
        f"This file currently contains {len(df)} rows "
        f"and {len(rainfall_cols)} rainfall date columns."
    )

    print(
        "We will NOT modify this source file during inspection."
    )

print("\n" + "=" * 80)
print("INSPECTION COMPLETE")
print("=" * 80)
print("IMPORTANT: No source files were modified.")