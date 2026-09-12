import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parent

FILES = {
    "rainfall": BASE / "rainfall_features_2020_2023.csv",
    "soil_moisture": BASE / "soil_moisture_features_2020_2023.csv",
    "terrain": BASE / "terrain_features_uttarakhand.csv",
    "labels": BASE / "flood_labels_2020_2023.csv",
}


# ============================================================
# VALIDATE INDIVIDUAL FILE
# ============================================================

def validate_file(name, path):

    print("\n" + "=" * 70)
    print(f"VALIDATING: {name}")
    print("=" * 70)

    # Check file exists
    if not path.exists():
        print(f"❌ FILE NOT FOUND: {path}")
        return None

    # Read CSV
    df = pd.read_csv(path)

    print(f"File: {path.name}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    print("\nMissing values:")
    print(df.isna().sum())

    # --------------------------------------------------------
    # Date validation
    # --------------------------------------------------------

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        print("\nDate information:")
        print("Min date:", df["date"].min())
        print("Max date:", df["date"].max())
        print("Unique dates:", df["date"].nunique())

    # --------------------------------------------------------
    # District validation
    # --------------------------------------------------------

    if "district" in df.columns:

        print("\nDistrict information:")
        print("Unique districts:", df["district"].nunique())

        print(
            sorted(
                df["district"]
                .dropna()
                .unique()
            )
        )

        # Date + district duplicate check
        # Only for files containing a date column
        if "date" in df.columns:

            duplicate_keys = df.duplicated(
                subset=["date", "district"]
            ).sum()

            print(
                "Duplicate date-district rows:",
                duplicate_keys
            )

        # Terrain has no date column
        else:

            duplicate_districts = df["district"].duplicated().sum()

            print(
                "Duplicate district rows:",
                duplicate_districts
            )

    # --------------------------------------------------------
    # Numeric summary
    # --------------------------------------------------------

    print("\nNumeric summary:")

    numeric_columns = df.select_dtypes(
        include="number"
    )

    if not numeric_columns.empty:
        print(numeric_columns.describe())
    else:
        print("No numeric columns found.")

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "#" * 70)
    print("TERRAPULSE — ML INPUT VALIDATION")
    print("#" * 70)

    data = {}

    # --------------------------------------------------------
    # Validate all files
    # --------------------------------------------------------

    for name, path in FILES.items():

        df = validate_file(
            name,
            path
        )

        if df is None:

            print(
                f"\n❌ Validation stopped because "
                f"{name} file is missing."
            )

            return

        data[name] = df

    # ========================================================
    # EXPECTED COLUMNS
    # ========================================================

    expected_columns = {

        "rainfall": [
            "date",
            "district",
            "rainfall_1d",
            "rainfall_3d",
            "rainfall_7d",
        ],

        "soil_moisture": [
            "date",
            "soil_moisture",
        ],

        "terrain": [
            "district",
            "mean_elevation",
            "mean_slope",
        ],

        "labels": [
            "date",
            "district",
            "flood_label",
        ],
    }

    print("\n" + "=" * 70)
    print("COLUMN VALIDATION")
    print("=" * 70)

    all_columns_ok = True

    for name, expected in expected_columns.items():

        actual = list(data[name].columns)

        missing = [
            column
            for column in expected
            if column not in actual
        ]

        if missing:

            print(
                f"❌ {name}: Missing columns -> {missing}"
            )

            all_columns_ok = False

        else:

            print(
                f"✅ {name}: All expected columns present"
            )

    if not all_columns_ok:

        print("\n❌ Column validation failed.")

        return

    # ========================================================
    # DATE RANGE VALIDATION
    # ========================================================

    print("\n" + "=" * 70)
    print("DATE RANGE VALIDATION")
    print("=" * 70)

    expected_start = pd.Timestamp(
        "2020-01-01"
    )

    expected_end = pd.Timestamp(
        "2023-12-31"
    )

    for name in [
        "rainfall",
        "soil_moisture",
        "labels"
    ]:

        df = data[name]

        min_date = df["date"].min()
        max_date = df["date"].max()

        if (
            min_date == expected_start
            and max_date == expected_end
        ):

            print(
                f"✅ {name}: Correct date range"
            )

        else:

            print(
                f"❌ {name}: "
                f"Expected "
                f"{expected_start.date()} → "
                f"{expected_end.date()}, "
                f"got "
                f"{min_date} → {max_date}"
            )

    # ========================================================
    # RAINFALL WARM-UP VALIDATION
    # ========================================================

    print("\n" + "=" * 70)
    print("RAINFALL WARM-UP VALIDATION")
    print("=" * 70)

    rainfall = data["rainfall"]

    nan_3d = rainfall[
        "rainfall_3d"
    ].isna().sum()

    nan_7d = rainfall[
        "rainfall_7d"
    ].isna().sum()

    expected_nan_3d = 13 * 2
    expected_nan_7d = 13 * 6

    print(
        f"rainfall_3d missing: {nan_3d}"
    )

    print(
        f"Expected: {expected_nan_3d}"
    )

    print(
        f"rainfall_7d missing: {nan_7d}"
    )

    print(
        f"Expected: {expected_nan_7d}"
    )

    if nan_3d == expected_nan_3d:

        print(
            "✅ rainfall_3d warm-up values are correct"
        )

    else:

        print(
            "❌ Unexpected rainfall_3d missing values"
        )

    if nan_7d == expected_nan_7d:

        print(
            "✅ rainfall_7d warm-up values are correct"
        )

    else:

        print(
            "❌ Unexpected rainfall_7d missing values"
        )

    # ========================================================
    # FLOOD LABEL VALIDATION
    # ========================================================

    print("\n" + "=" * 70)
    print("FLOOD LABEL VALIDATION")
    print("=" * 70)

    labels = data["labels"]

    print("Label counts:")

    print(
        labels[
            "flood_label"
        ]
        .value_counts()
        .sort_index()
    )

    invalid_labels = labels[
        ~labels["flood_label"].isin([0, 1])
    ]

    if len(invalid_labels) == 0:

        print(
            "✅ Labels contain only 0 and 1"
        )

    else:

        print(
            f"❌ Found "
            f"{len(invalid_labels)} "
            f"invalid label rows"
        )

    # ========================================================
    # TERRAIN VALIDATION
    # ========================================================

    print("\n" + "=" * 70)
    print("TERRAIN VALIDATION")
    print("=" * 70)

    terrain = data["terrain"]

    # Elevation missing
    if (
        terrain["mean_elevation"]
        .isna()
        .sum()
        == 0
    ):

        print(
            "✅ No missing elevation values"
        )

    else:

        print(
            "❌ Missing elevation values found"
        )

    # Slope missing
    if (
        terrain["mean_slope"]
        .isna()
        .sum()
        == 0
    ):

        print(
            "✅ No missing slope values"
        )

    else:

        print(
            "❌ Missing slope values found"
        )

    # Elevation negative
    if (
        terrain["mean_elevation"] < 0
    ).sum() == 0:

        print(
            "✅ No negative elevation values"
        )

    else:

        print(
            "❌ Negative elevation values found"
        )

    # Slope range
    invalid_slope = (
        (terrain["mean_slope"] < 0)
        |
        (terrain["mean_slope"] > 90)
    ).sum()

    if invalid_slope == 0:

        print(
            "✅ Slope values are within 0–90 degrees"
        )

    else:

        print(
            "❌ Invalid slope values found"
        )

    # ========================================================
    # SOIL MOISTURE VALIDATION
    # ========================================================

    print("\n" + "=" * 70)
    print("SOIL MOISTURE VALIDATION")
    print("=" * 70)

    soil = data["soil_moisture"]

    # Missing values
    if (
        soil["soil_moisture"]
        .isna()
        .sum()
        == 0
    ):

        print(
            "✅ No missing soil moisture values"
        )

    else:

        print(
            "❌ Missing soil moisture values found"
        )

    # Negative values
    if (
        soil["soil_moisture"] < 0
    ).sum() == 0:

        print(
            "✅ No negative soil moisture values"
        )

    else:

        print(
            "❌ Negative soil moisture values found"
        )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n" + "#" * 70)
    print("VALIDATION SUMMARY")
    print("#" * 70)

    print(
        "Rainfall rows:",
        len(data["rainfall"])
    )

    print(
        "Soil moisture rows:",
        len(data["soil_moisture"])
    )

    print(
        "Terrain rows:",
        len(data["terrain"])
    )

    print(
        "Label rows:",
        len(data["labels"])
    )

    print("\nExpected districts: 13")

    for name in [
        "rainfall",
        "labels"
    ]:

        print(
            f"{name} districts:",
            data[name]["district"].nunique()
        )

    print("\n" + "=" * 70)
    print("🎯 ML INPUT VALIDATION COMPLETED")
    print("=" * 70)

    print(
        "\nNext step: "
        "Merge all validated features into "
        "the final ML dataset."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()