from pathlib import Path
import pandas as pd


# ============================================================
# TerraPulse SIH 2026
# Flood Event Dataset Inspection
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

FLOOD_FILE = (
    PROJECT_DIR
    / "04_Flood_Events"
    / "Uttarakhand_Flood_Events.csv"
)


print("=" * 80)
print("TERRAPULSE — FLOOD EVENT DATASET INSPECTION")
print("=" * 80)


# ------------------------------------------------------------
# 1. FILE CHECK
# ------------------------------------------------------------

print("\n1. FILE CHECK")
print("-" * 50)

print("File:", FLOOD_FILE)

if not FLOOD_FILE.exists():
    raise FileNotFoundError(
        f"Flood event file not found:\n{FLOOD_FILE}"
    )

print("✓ File exists")


# ------------------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------------------

print("\n2. LOADING DATASET")
print("-" * 50)

df = pd.read_csv(FLOOD_FILE)

print("Rows:", len(df))
print("Columns:", len(df.columns))


# ------------------------------------------------------------
# 3. COLUMN NAMES
# ------------------------------------------------------------

print("\n3. COLUMN NAMES")
print("-" * 50)

for i, column in enumerate(df.columns, start=1):
    print(f"{i:2d}. {column}")


# ------------------------------------------------------------
# 4. FIRST ROWS
# ------------------------------------------------------------

print("\n4. FIRST 5 ROWS")
print("-" * 80)

print(df.head().to_string(index=False))


# ------------------------------------------------------------
# 5. DATA TYPES
# ------------------------------------------------------------

print("\n5. DATA TYPES")
print("-" * 50)

print(df.dtypes.to_string())


# ------------------------------------------------------------
# 6. MISSING VALUES
# ------------------------------------------------------------

print("\n6. MISSING VALUES")
print("-" * 50)

missing = df.isna().sum()

print(
    missing[
        missing > 0
    ].to_string()
    if (missing > 0).any()
    else "No missing values"
)


# ------------------------------------------------------------
# 7. UNIQUE VALUES FOR TEXT COLUMNS
# ------------------------------------------------------------

print("\n7. UNIQUE VALUES — TEXT/CATEGORICAL COLUMNS")
print("-" * 80)

text_columns = df.select_dtypes(
    include=["object", "string", "category"]
).columns

for column in text_columns:

    unique_values = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    print(f"\n{column}")
    print("-" * 40)
    print("Unique values:", len(unique_values))

    # Show all values when reasonable
    if len(unique_values) <= 100:
        for value in sorted(unique_values):
            print(" -", value)
    else:
        print(
            "Too many unique values to display."
        )


# ------------------------------------------------------------
# 8. POSSIBLE DATE COLUMNS
# ------------------------------------------------------------

print("\n8. POSSIBLE DATE COLUMNS")
print("-" * 80)

for column in df.columns:

    if "date" in column.lower():

        print(f"\nColumn: {column}")

        parsed = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        valid_count = parsed.notna().sum()
        invalid_count = parsed.isna().sum()

        print("Valid dates:", valid_count)
        print("Invalid dates:", invalid_count)

        if valid_count > 0:
            print(
                "Minimum:",
                parsed.min()
            )
            print(
                "Maximum:",
                parsed.max()
            )


# ------------------------------------------------------------
# 9. 2020–2023 DATE ANALYSIS
# ------------------------------------------------------------

print("\n9. 2020–2023 DATE ANALYSIS")
print("-" * 80)

for column in df.columns:

    if "date" in column.lower():

        parsed = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        valid = parsed.dropna()

        if len(valid) == 0:
            continue

        period = valid[
            (valid.dt.year >= 2020)
            & (valid.dt.year <= 2023)
        ]

        if len(period) > 0:

            print(f"\nDate column: {column}")

            print(
                "2020–2023 records:",
                len(period)
            )

            print(
                "Year distribution:"
            )

            print(
                period.dt.year
                .value_counts()
                .sort_index()
                .to_string()
            )


# ------------------------------------------------------------
# 10. POSSIBLE DISTRICT COLUMNS
# ------------------------------------------------------------

print("\n10. POSSIBLE DISTRICT COLUMNS")
print("-" * 80)

for column in df.columns:

    name = column.lower()

    if (
        "district" in name
        or "admin" in name
        or "state" in name
        or "location" in name
    ):

        print(f"\nColumn: {column}")

        values = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
        )

        print(
            "Unique values:",
            len(values)
        )

        if len(values) <= 100:

            for value in sorted(values):
                print(" -", value)


# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("FLOOD EVENT DATASET INSPECTION COMPLETE")
print("=" * 80)

print(
    "\nIMPORTANT:"
    "\nNo flood-event files were modified."
    "\nThis script only inspected the dataset."
)