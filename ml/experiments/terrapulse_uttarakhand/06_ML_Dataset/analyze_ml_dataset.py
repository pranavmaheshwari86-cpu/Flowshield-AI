import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parent

ML_FILE = (
    BASE /
    "terrapulse_ml_dataset_2020_2023.csv"
)

# ============================================================
# EXPECTED VALUES
# ============================================================

EXPECTED_DISTRICTS = sorted([
    "Almora",
    "Bageshwar", "Chamoli",
    "Champawat", "Dehra Dun",
    "Haridwar", "Naini Tal",
    "Pauri Garhwal", "Pithoragarh",
    "Rudra Prayag", "Tehri Garhwal",
    "Udham Singh Nagar", "Uttarkashi",
])

FEATURE_COLUMNS = [
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "soil_moisture",
    "mean_elevation",
    "mean_slope",
]

# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "#" * 70)
    print("TERRAPULSE — ML DATASET ANALYSIS")
    print("#" * 70)

    # ========================================================
    # LOAD DATASET
    # ========================================================

    if not ML_FILE.exists():

        print(f"\n❌ Dataset not found:\n{ML_FILE}")

        return

    df = pd.read_csv(
        ML_FILE
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    print("\nDataset loaded successfully.")

    print("Shape:", df.shape)

    # ========================================================
    # BASIC INFORMATION
    # ========================================================

    print("\n" + "=" * 70)
    print("1. BASIC DATASET INFORMATION")
    print("=" * 70)

    print("\nColumns:")

    for column in df.columns:

        print(
            f"  - {column}"
        )

    print(
        "\nDate range:",
        df["date"].min(),
        "→",
        df["date"].max()
    )

    print("Unique dates:",df["date"].nunique())

    print( "Unique districts:", df["district"].nunique())

    # ========================================================
    # DISTRICT VALIDATION
    # ========================================================

    print("\n" + "=" * 70)
    print("2. DISTRICT ANALYSIS")
    print("=" * 70)

    districts = sorted(
        df["district"].unique()
    )

    print("\nDistricts:")

    for district in districts:

        print(f"  - {district}")

    if districts == EXPECTED_DISTRICTS:
        print("\n✅ All 13 expected districts are present.")
    else:
        print("\n⚠️ District list differs from expected list.")

    district_counts = (
        df["district"]
        .value_counts()
        .sort_index()
    )

    print("\nRows per district:")

    print(district_counts)

    # ========================================================
    # MISSING VALUE CHECK
    # ========================================================

    print("\n" + "=" * 70)
    print("3. MISSING VALUE ANALYSIS")
    print("=" * 70)

    missing = df.isna().sum()

    print(missing)

    if missing.sum() == 0:

        print("\n✅ No missing values.")

    else:

        print("\n❌ Missing values detected.")

    # ========================================================
    # DUPLICATE CHECK
    # ========================================================

    print("\n" + "=" * 70)
    print("4. DUPLICATE ANALYSIS")
    print("=" * 70)

    duplicate_rows = df.duplicated().sum()

    duplicate_keys = df.duplicated(
        subset=[
            "date",
            "district"
        ]
    ).sum()

    print(
        "Duplicate complete rows:",
        duplicate_rows
    )

    print(
        "Duplicate date-district rows:",
        duplicate_keys
    )

    if duplicate_rows == 0:

        print("✅ No duplicate complete rows.")

    else:

        print("⚠️ Duplicate complete rows found.")

    if duplicate_keys == 0:

        print("✅ No duplicate date-district keys.")

    else:

        print("❌ Duplicate date-district keys found.")

    # ========================================================
    # FEATURE STATISTICS
    # ========================================================

    print("\n" + "=" * 70)
    print("5. FEATURE STATISTICS")
    print("=" * 70)

    print(
        "\nDescriptive statistics:"
    )

    print(
        df[
            FEATURE_COLUMNS
        ].describe().round(4)
    )

    # ========================================================
    # FLOOD LABEL DISTRIBUTION
    # ========================================================

    print("\n" + "=" * 70)
    print("6. FLOOD LABEL DISTRIBUTION")
    print("=" * 70)

    label_counts = (
        df["flood_label"]
        .value_counts()
        .sort_index()
    )

    print(
        "\nLabel counts:"
    )

    print(
        label_counts
    )

    total_rows = len(df)

    positive = int(
        label_counts.get(1, 0)
    )

    negative = int(
        label_counts.get(0, 0)
    )

    positive_percentage = (
        positive / total_rows
    ) * 100

    negative_percentage = (
        negative / total_rows
    ) * 100

    print(
        f"\nNon-flood samples (0): "
        f"{negative} "
        f"({negative_percentage:.4f}%)"
    )

    print(
        f"Flood-warning samples (1): "
        f"{positive} "
        f"({positive_percentage:.4f}%)"
    )

    # ========================================================
    # YEAR-WISE LABEL DISTRIBUTION
    # ========================================================

    print("\n" + "=" * 70)
    print("7. YEAR-WISE LABEL DISTRIBUTION")
    print("=" * 70)

    df["year"] = df["date"].dt.year

    yearly_labels = pd.crosstab(
        df["year"],
        df["flood_label"]
    )

    print("\nRows by year and label:")

    print(yearly_labels)

    # Ensure columns 0 and 1 exist
    for label in [0, 1]:

        if label not in yearly_labels.columns:

            yearly_labels[label] = 0

    yearly_labels = yearly_labels[
        [0, 1]
    ]

    yearly_labels["positive_rate_percent"] = (
        yearly_labels[1]
        /
        yearly_labels.sum(axis=1)
        *
        100
    )

    print("\nPositive rate by year (%):")

    print(
        yearly_labels[
            "positive_rate_percent"
        ].round(4)
    )

    # ========================================================
    # DISTRICT-WISE FLOOD LABEL DISTRIBUTION
    # ========================================================

    print("\n" + "=" * 70)
    print("8. DISTRICT-WISE FLOOD LABEL DISTRIBUTION")
    print("=" * 70)

    district_labels = pd.crosstab(
        df["district"],
        df["flood_label"]
    )

    for label in [0, 1]:

        if label not in district_labels.columns:

            district_labels[label] = 0

    district_labels = district_labels[
        [0, 1]
    ]

    district_labels[
        "positive_rate_percent"
    ] = (
        district_labels[1]
        /
        district_labels.sum(axis=1)
        *
        100
    )

    print(district_labels.round(4))

    # ========================================================
    # POSITIVE SAMPLE DETAILS
    # ========================================================

    print("\n" + "=" * 70)
    print("9. FLOOD-WARNING SAMPLE DETAILS")
    print("=" * 70)

    positive_df = df[
        df["flood_label"] == 1
    ].copy()

    print(
        "\nTotal positive rows:",
        len(positive_df)
    )

    if len(positive_df) > 0:

        print("\nPositive samples by district:")

        print(
            positive_df[
                "district"
            ]
            .value_counts()
            .sort_index()
        )

        print("\nPositive samples by year:")

        print(
            positive_df[
                "year"
            ]
            .value_counts()
            .sort_index()
        )

        print("\nFirst 20 positive samples:")

        print(
            positive_df[
                [
                    "date",
                    "district",
                    "rainfall_1d",
                    "rainfall_3d",
                    "rainfall_7d",
                    "soil_moisture",
                    "flood_label",
                ]
            ]
            .head(20)
            .to_string(index=False)
        )

    # ========================================================
    # FEATURE CORRELATION WITH LABEL
    # ========================================================

    print("\n" + "=" * 70)
    print("10. FEATURE-TO-LABEL CORRELATION")
    print("=" * 70)

    correlations = (
        df[
            FEATURE_COLUMNS +
            ["flood_label"]
        ]
        .corr()["flood_label"]
        .drop("flood_label")
        .sort_values(
            ascending=False
        )
    )

    print("\nPearson correlation with flood_label:")

    print(correlations.round(4))

    print("\n⚠️ Correlation is descriptive only.")

    print("It does NOT prove causation or model performance.")

    # ========================================================
    # CHRONOLOGICAL TRAIN / TEST SPLIT PREVIEW
    # ========================================================

    print("\n" + "=" * 70)
    print("11. CHRONOLOGICAL TRAIN / TEST SPLIT")
    print("=" * 70)

    train = df[
        df["year"] <= 2022
    ].copy()

    test = df[
        df["year"] == 2023
    ].copy()

    print("\nTRAIN PERIOD:")

    print("2020-01-07 → 2022-12-31")

    print("Training rows:", len(train))

    print(
        "Training positive labels:",
        int(
            train["flood_label"].sum()
        )
    )

    print("\nTEST PERIOD:")

    print("2023-01-01 → 2023-12-31")

    print("Testing rows:" ,len(test))

    print(
        "Testing positive labels:",
        int(
            test["flood_label"].sum()
        )
    )

    # ========================================================
    # TRAIN / TEST CLASS DISTRIBUTION
    # ========================================================

    print("\n" + "=" * 70)
    print("12. TRAIN / TEST CLASS DISTRIBUTION")
    print("=" * 70)

    print("\nTraining labels:")

    print(
        train[
            "flood_label"
        ]
        .value_counts()
        .sort_index()
    )

    print("\nTesting labels:")

    print(
        test[
            "flood_label"
        ]
        .value_counts()
        .sort_index()
    )

    # ========================================================
    # TEMPORAL LEAKAGE CHECK
    # ========================================================

    print("\n" + "=" * 70)
    print("13. TEMPORAL LEAKAGE CHECK")
    print("=" * 70)

    train_max_date = train["date"].max()
    test_min_date = test["date"].min()

    print("Latest training date:", train_max_date)

    print("Earliest testing date:" ,test_min_date)

    if train_max_date < test_min_date:
        print("✅ No temporal overlap between train and test.")
    else:
        print("❌ Temporal overlap detected.")

    # ========================================================
    # DISTRICT BALANCE CHECK
    # ========================================================

    print("\n" + "=" * 70)
    print("14. DISTRICT BALANCE CHECK")
    print("=" * 70)

    train_district_counts = (
        train["district"]
        .value_counts()
        .sort_index()
    )

    test_district_counts = (
        test["district"]
        .value_counts()
        .sort_index()
    )

    district_balance = pd.DataFrame({
        "train_rows":
            train_district_counts,

        "test_rows":
            test_district_counts,
    })

    print(district_balance)

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n" + "#" * 70)
    print("ANALYSIS SUMMARY")
    print("#" * 70)

    print(f"\nTotal rows: {len(df)}")

    print(f"Total features: {len(FEATURE_COLUMNS)}")

    print(f"Positive samples: {positive}")

    print(f"Positive rate: {positive_percentage:.4f}%")

    print(f"Training rows: {len(train)}")

    print(f"Testing rows: {len(test)}")

    print(
        f"Training positives: "
        f"{int(train['flood_label'].sum())}"
    )

    print(
        f"Testing positives: "
        f"{int(test['flood_label'].sum())}"
    )

    print("\n" + "=" * 70)
    print(
        "🎯 ML DATASET ANALYSIS COMPLETED"
    )
    print("=" * 70)

if __name__ == "__main__":
    main()