import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parent.parent
FEATURES = BASE / "05_Features"
OUTPUT_DIR = BASE / "06_ML_Dataset"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INPUT FILES
# ============================================================

RAINFALL_FILE = (
    FEATURES /
    "rainfall_features_2020_2023.csv"
)

SOIL_FILE = (
    FEATURES /
    "soil_moisture_features_2020_2023.csv"
)

TERRAIN_FILE = (
    FEATURES /
    "terrain_features_uttarakhand.csv"
)

LABEL_FILE = (
    FEATURES /
    "flood_labels_2020_2023.csv"
)


OUTPUT_FILE = (
    OUTPUT_DIR /
    "terrapulse_ml_dataset_2020_2023.csv"
)


# ============================================================
# EXPECTED DISTRICTS
# ============================================================

EXPECTED_DISTRICTS = sorted([
    "Almora",
    "Bageshwar",
    "Chamoli",
    "Champawat",
    "Dehra Dun",
    "Haridwar",
    "Naini Tal",
    "Pauri Garhwal",
    "Pithoragarh",
    "Rudra Prayag",
    "Tehri Garhwal",
    "Udham Singh Nagar",
    "Uttarkashi",
])


# ============================================================
# HELPER FUNCTION
# ============================================================

def check_file(path):

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "#" * 70)
    print("TERRAPULSE — BUILD FINAL ML DATASET")
    print("#" * 70)

    # --------------------------------------------------------
    # Check input files
    # --------------------------------------------------------

    print("\nChecking input files...")

    for file_path in [
        RAINFALL_FILE,
        SOIL_FILE,
        TERRAIN_FILE,
        LABEL_FILE,
    ]:

        check_file(file_path)

        print(
            f"✅ Found: {file_path.name}"
        )

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("LOADING DATASETS")
    print("=" * 70)

    rainfall = pd.read_csv(
        RAINFALL_FILE
    )

    soil = pd.read_csv(
        SOIL_FILE
    )

    terrain = pd.read_csv(
        TERRAIN_FILE
    )

    labels = pd.read_csv(
        LABEL_FILE
    )

    print(
        "Rainfall:",
        rainfall.shape
    )

    print(
        "Soil moisture:",
        soil.shape
    )

    print(
        "Terrain:",
        terrain.shape
    )

    print(
        "Labels:",
        labels.shape
    )

    # --------------------------------------------------------
    # Convert dates
    # --------------------------------------------------------

    rainfall["date"] = pd.to_datetime(
        rainfall["date"]
    )

    soil["date"] = pd.to_datetime(
        soil["date"]
    )

    labels["date"] = pd.to_datetime(
        labels["date"]
    )

    # ========================================================
    # VALIDATE DISTRICTS
    # ========================================================

    print("\n" + "=" * 70)
    print("DISTRICT VALIDATION")
    print("=" * 70)

    rainfall_districts = sorted(
        rainfall["district"].unique()
    )

    label_districts = sorted(
        labels["district"].unique()
    )

    terrain_districts = sorted(
        terrain["district"].unique()
    )

    if rainfall_districts != EXPECTED_DISTRICTS:

        raise ValueError(
            "Rainfall districts do not match expected districts."
        )

    print(
        "✅ Rainfall: 13 expected districts"
    )

    if label_districts != EXPECTED_DISTRICTS:

        raise ValueError(
            "Label districts do not match expected districts."
        )

    print(
        "✅ Labels: 13 expected districts"
    )

    if terrain_districts != EXPECTED_DISTRICTS:

        raise ValueError(
            "Terrain districts do not match expected districts."
        )

    print(
        "✅ Terrain: 13 expected districts"
    )

    # ========================================================
    # VALIDATE DUPLICATES BEFORE MERGING
    # ========================================================

    print("\n" + "=" * 70)
    print("PRE-MERGE DUPLICATE CHECK")
    print("=" * 70)

    rainfall_duplicates = rainfall.duplicated(
        subset=["date", "district"]
    ).sum()

    label_duplicates = labels.duplicated(
        subset=["date", "district"]
    ).sum()

    soil_duplicates = soil.duplicated(
        subset=["date"]
    ).sum()

    terrain_duplicates = terrain.duplicated(
        subset=["district"]
    ).sum()

    print(
        "Rainfall duplicate date-district rows:",
        rainfall_duplicates
    )

    print(
        "Label duplicate date-district rows:",
        label_duplicates
    )

    print(
        "Soil duplicate date rows:",
        soil_duplicates
    )

    print(
        "Terrain duplicate district rows:",
        terrain_duplicates
    )

    if rainfall_duplicates != 0:
        raise ValueError(
            "Duplicate rainfall date-district rows found."
        )

    if label_duplicates != 0:
        raise ValueError(
            "Duplicate label date-district rows found."
        )

    if soil_duplicates != 0:
        raise ValueError(
            "Duplicate soil moisture dates found."
        )

    if terrain_duplicates != 0:
        raise ValueError(
            "Duplicate terrain districts found."
        )

    print(
        "✅ No duplicate keys found"
    )

    # ========================================================
    # MERGE RAINFALL + SOIL MOISTURE
    # ========================================================

    print("\n" + "=" * 70)
    print("MERGE 1 — RAINFALL + SOIL MOISTURE")
    print("=" * 70)

    dataset = rainfall.merge(
        soil,
        on="date",
        how="left",
        validate="many_to_one"
    )

    print(
        "Rows after merge:",
        len(dataset)
    )

    print(
        "Columns after merge:",
        list(dataset.columns)
    )

    # --------------------------------------------------------
    # Soil moisture coverage check
    # --------------------------------------------------------

    missing_soil = dataset[
        "soil_moisture"
    ].isna().sum()

    print(
        "Missing soil moisture after merge:",
        missing_soil
    )

    if missing_soil != 0:

        raise ValueError(
            "Missing soil moisture values after merge."
        )

    print(
        "✅ Soil moisture merge successful"
    )

    # ========================================================
    # MERGE TERRAIN
    # ========================================================

    print("\n" + "=" * 70)
    print("MERGE 2 — ADD TERRAIN FEATURES")
    print("=" * 70)

    dataset = dataset.merge(
        terrain,
        on="district",
        how="left",
        validate="many_to_one"
    )

    print(
        "Rows after merge:",
        len(dataset)
    )

    missing_elevation = dataset[
        "mean_elevation"
    ].isna().sum()

    missing_slope = dataset[
        "mean_slope"
    ].isna().sum()

    print(
        "Missing elevation after merge:",
        missing_elevation
    )

    print(
        "Missing slope after merge:",
        missing_slope
    )

    if missing_elevation != 0:

        raise ValueError(
            "Missing terrain elevation after merge."
        )

    if missing_slope != 0:

        raise ValueError(
            "Missing terrain slope after merge."
        )

    print(
        "✅ Terrain merge successful"
    )

    # ========================================================
    # MERGE FLOOD LABELS
    # ========================================================

    print("\n" + "=" * 70)
    print("MERGE 3 — ADD FLOOD LABEL")
    print("=" * 70)

    dataset = dataset.merge(
        labels,
        on=["date", "district"],
        how="left",
        validate="one_to_one"
    )

    print(
        "Rows after merge:",
        len(dataset)
    )

    missing_labels = dataset[
        "flood_label"
    ].isna().sum()

    print(
        "Missing flood labels after merge:",
        missing_labels
    )

    if missing_labels != 0:

        raise ValueError(
            "Missing flood labels after merge."
        )

    print(
        "✅ Flood label merge successful"
    )

    # ========================================================
    # REMOVE RAINFALL WARM-UP ROWS
    # ========================================================

    print("\n" + "=" * 70)
    print("REMOVING RAINFALL WARM-UP ROWS")
    print("=" * 70)

    rows_before = len(dataset)

    warmup_rows = dataset[
        dataset[
            [
                "rainfall_3d",
                "rainfall_7d"
            ]
        ].isna().any(axis=1)
    ]

    print(
        "Warm-up rows identified:",
        len(warmup_rows)
    )

    dataset = dataset.dropna(
        subset=[
            "rainfall_3d",
            "rainfall_7d"
        ]
    ).copy()

    rows_after = len(dataset)

    print(
        "Rows before warm-up removal:",
        rows_before
    )

    print(
        "Rows after warm-up removal:",
        rows_after
    )

    print(
        "Rows removed:",
        rows_before - rows_after
    )

    # ========================================================
    # FINAL COLUMN ORDER
    # ========================================================

    final_columns = [
        "date",
        "district",
        "rainfall_1d",
        "rainfall_3d",
        "rainfall_7d",
        "soil_moisture",
        "mean_elevation",
        "mean_slope",
        "flood_label",
    ]

    dataset = dataset[
        final_columns
    ]

    # ========================================================
    # SORT DATA
    # ========================================================

    dataset = dataset.sort_values(
        by=[
            "date",
            "district"
        ]
    ).reset_index(
        drop=True
    )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    print("\n" + "#" * 70)
    print("FINAL ML DATASET VALIDATION")
    print("#" * 70)

    print(
        "\nShape:",
        dataset.shape
    )

    print(
        "\nColumns:"
    )

    print(
        list(dataset.columns)
    )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    print("\nMissing values:")

    print(
        dataset.isna().sum()
    )

    if dataset.isna().sum().sum() != 0:

        raise ValueError(
            "Final dataset still contains missing values."
        )

    print(
        "✅ No missing values"
    )

    # --------------------------------------------------------
    # Duplicate check
    # --------------------------------------------------------

    duplicates = dataset.duplicated(
        subset=[
            "date",
            "district"
        ]
    ).sum()

    print(
        "\nDuplicate date-district rows:",
        duplicates
    )

    if duplicates != 0:

        raise ValueError(
            "Duplicate date-district rows found."
        )

    print(
        "✅ No duplicate date-district rows"
    )

    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------

    print(
        "\nDate range:",
        dataset["date"].min(),
        "→",
        dataset["date"].max()
    )

    # --------------------------------------------------------
    # District count
    # --------------------------------------------------------

    print(
        "Unique districts:",
        dataset["district"].nunique()
    )

    if dataset["district"].nunique() != 13:

        raise ValueError(
            "Final dataset does not contain 13 districts."
        )

    print(
        "✅ All 13 districts present"
    )

    # --------------------------------------------------------
    # Label validation
    # --------------------------------------------------------

    print(
        "\nFlood label distribution:"
    )

    print(
        dataset[
            "flood_label"
        ]
        .value_counts()
        .sort_index()
    )

    invalid_labels = dataset[
        ~dataset["flood_label"].isin([0, 1])
    ]

    if len(invalid_labels) != 0:

        raise ValueError(
            "Invalid flood labels found."
        )

    print(
        "✅ Flood labels valid"
    )

    # --------------------------------------------------------
    # Rainfall validation
    # --------------------------------------------------------

    rainfall_columns = [
        "rainfall_1d",
        "rainfall_3d",
        "rainfall_7d"
    ]

    negative_rainfall = (
        dataset[rainfall_columns] < 0
    ).sum().sum()

    if negative_rainfall != 0:

        raise ValueError("Negative rainfall values found.")

    print("✅ Rainfall values valid")

    # --------------------------------------------------------
    # Terrain validation
    # --------------------------------------------------------

    if (
        dataset["mean_elevation"] < 0
    ).any():

        raise ValueError("Negative elevation found.")

    if (
        (dataset["mean_slope"] < 0)
        |
        (dataset["mean_slope"] > 90)
    ).any():

        raise ValueError("Invalid slope value found.")

    print("✅ Terrain values valid")

    # --------------------------------------------------------
    # Soil moisture validation
    # --------------------------------------------------------

    if (
        dataset["soil_moisture"] < 0
    ).any():

        raise ValueError("Negative soil moisture found.")

    print("✅ Soil moisture values valid")

    # ========================================================
    # YEAR-WISE COUNTS
    # ========================================================

    print("\n" + "=" * 70)
    print("YEAR-WISE ROW COUNTS")
    print("=" * 70)

    year_counts = (
        dataset["date"]
        .dt.year
        .value_counts()
        .sort_index()
    )

    print(year_counts)

    # SAVE FINAL DATASET

    dataset.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "#" * 70)
    print("SUCCESS")
    print("#" * 70)

    print(f"\n✅ Final ML dataset saved to: {OUTPUT_FILE}")

    print(
        "\nFinal rows:",
        len(dataset)
    )

    print(
        "Final columns:",
        len(dataset.columns)
    )

    print("\n🎯 ML DATASET BUILD COMPLETED")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()