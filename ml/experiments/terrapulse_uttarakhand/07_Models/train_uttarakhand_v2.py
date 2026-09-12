from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "06_ML_Dataset"
    / "terrapulse_uttarakhand_v2_synthetic.csv"
)

MODEL_DIR = PROJECT_ROOT / "07_Models"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 2. DATASET / TARGET CONFIGURATION
# ============================================================

TARGET = "flood_label"

DATE_COLUMN = "date"

# Existing categorical columns + new V2 categorical columns.
CATEGORICAL_FEATURES = [
    "district",
    "slope_risk",
    "weather_condition",
]

NUMERICAL_FEATURES = [
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "rainfall_14d",
    "rainfall_30d",
    "rainfall_max_3d",
    "rainfall_max_7d",
    "rainy_days_7d",
    "rainfall_1d_to_7d",
    "rainfall_3d_to_7d",
    "soil_moisture",
    "mean_elevation",
    "mean_slope",
    "river_water_level_m",
    "river_danger_level_m",
    "river_level_ratio_to_danger",
    "river_rise_rate_m_per_hr",
    "river_level_change_3h_m",
    "river_level_change_6h_m",
    "river_level_change_24h_m",
    "temperature_c",
    "relative_humidity_pct",
    "wind_speed_kmh",
    "atmospheric_pressure_hpa",
]

FEATURES = (
    NUMERICAL_FEATURES
    + CATEGORICAL_FEATURES
)


# ============================================================
# 3. VALIDATION
# ============================================================

EXPECTED_COLUMNS = (
    [DATE_COLUMN]
    + FEATURES
    + [TARGET]
)


def validate_dataset(df: pd.DataFrame) -> None:
    """Validate required schema before training."""

    missing = [
        column
        for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns:\n"
            + "\n".join(
                f" - {column}"
                for column in missing
            )
        )

    unexpected_target_values = sorted(
        set(df[TARGET].dropna().unique())
        - {0, 1}
    )

    if unexpected_target_values:
        raise ValueError(
            "Target contains values other than 0/1: "
            f"{unexpected_target_values}"
        )


# ============================================================
# 4. ONE-HOT ENCODER COMPATIBILITY
# ============================================================

def create_one_hot_encoder():
    """Support multiple scikit-learn versions."""

    try:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=True,
        )
    except TypeError:
        return OneHotEncoder(
            handle_unknown="ignore",
            sparse=True,
        )


# ============================================================
# 5. PREPROCESSOR
# ============================================================

def create_preprocessor():
    """Create numeric + categorical preprocessing."""

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "onehot",
                create_one_hot_encoder(),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERICAL_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    return preprocessor


# ============================================================
# 6. MODEL BUILDERS
# ============================================================

def create_logistic_model():
    """Build Logistic Regression pipeline."""

    return Pipeline(
        steps=[
            (
                "preprocessor",
                create_preprocessor(),
            ),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=3000,
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )


def create_random_forest_model():
    """Build Random Forest pipeline."""

    return Pipeline(
        steps=[
            (
                "preprocessor",
                create_preprocessor(),
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=500,
                    class_weight="balanced",
                    max_features="sqrt",
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


# ============================================================
# 7. METRICS
# ============================================================

def calculate_metrics(
    y_true,
    probabilities,
    threshold,
):
    """Calculate binary classification metrics."""

    y_true = np.asarray(
        y_true,
        dtype=int,
    )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    predictions = (
        probabilities >= threshold
    ).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[0, 1],
    ).ravel()

    return {
        "threshold": float(threshold),

        "accuracy": float(
            accuracy_score(
                y_true,
                predictions,
            )
        ),

        "precision": float(
            precision_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),

        "recall": float(
            recall_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),

        "f1": float(
            f1_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),

        "roc_auc": float(
            roc_auc_score(
                y_true,
                probabilities,
            )
        ),

        "pr_auc": float(
            average_precision_score(
                y_true,
                probabilities,
            )
        ),

        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


# ============================================================
# 8. THRESHOLD SEARCH
# ============================================================

def find_best_threshold(
    y_true,
    probabilities,
):
    """
    Select threshold using validation-set F1.

    Tie breaking:
        1. Higher F1
        2. Higher recall
        3. Higher precision
        4. Lower threshold
    """

    thresholds = np.arange(
        0.01,
        1.00,
        0.01,
    )

    results = []

    for threshold in thresholds:

        metrics = calculate_metrics(
            y_true,
            probabilities,
            threshold,
        )

        results.append(metrics)

    results_df = pd.DataFrame(
        results
    )

    results_df = results_df.sort_values(
        by=[
            "f1",
            "recall",
            "precision",
            "threshold",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
    ).reset_index(
        drop=True
    )

    best = results_df.iloc[0]

    return (
        float(best["threshold"]),
        results_df,
    )


# ============================================================
# 9. MAIN
# ============================================================

def main():

    print("=" * 75)
    print("TERRAPULSE V3 — UTTARAKHAND V2 ENSEMBLE TRAINING")
    print("=" * 75)

    print("\nProject root:")
    print(PROJECT_ROOT)

    print("\nDataset:")
    print(DATA_FILE)

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"\nDataset not found:\n{DATA_FILE}"
        )

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    df = pd.read_csv(
        DATA_FILE
    )

    print(
        f"\nDataset loaded successfully."
    )

    print(
        f"Rows:    {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    validate_dataset(df)

    # --------------------------------------------------------
    # DATE PROCESSING
    # --------------------------------------------------------

    df[DATE_COLUMN] = pd.to_datetime(
        df[DATE_COLUMN],
        errors="coerce",
    )

    if df[DATE_COLUMN].isna().any():
        raise ValueError(
            "Invalid date values detected."
        )

    df = df.sort_values(
        by=DATE_COLUMN
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # DATA INTEGRITY
    # --------------------------------------------------------

    print("\n" + "=" * 75)
    print("DATASET INTEGRITY")
    print("=" * 75)

    print(
        "Missing values:",
        int(df[FEATURES + [TARGET]].isna().sum().sum()),
    )

    print(
        "Duplicate rows:",
        int(df.duplicated().sum()),
    )

    print(
        "\nDate range:"
    )

    print(
        df[DATE_COLUMN].min(),
        "→",
        df[DATE_COLUMN].max(),
    )

    print(
        "\nTarget distribution:"
    )

    print(
        df[TARGET]
        .value_counts()
        .sort_index()
        .to_string()
    )

    flood_count = int(
        (df[TARGET] == 1).sum()
    )

    non_flood_count = int(
        (df[TARGET] == 0).sum()
    )

    print(
        f"\nFlood rate: "
        f"{(flood_count / len(df)) * 100:.2f}%"
    )

    print(
        f"Imbalance ratio: "
        f"{non_flood_count / max(flood_count, 1):.2f}:1"
    )

    # --------------------------------------------------------
    # TEMPORAL SPLIT
    # --------------------------------------------------------

    train_df = df[
        df[DATE_COLUMN].dt.year
        <= 2021
    ].copy()

    validation_df = df[
        df[DATE_COLUMN].dt.year
        == 2022
    ].copy()

    test_df = df[
        df[DATE_COLUMN].dt.year
        == 2023
    ].copy()

    if (
        train_df.empty
        or validation_df.empty
        or test_df.empty
    ):
        raise ValueError(
            "One or more temporal splits are empty."
        )

    print("\n" + "=" * 75)
    print("TEMPORAL SPLIT")
    print("=" * 75)

    print(
        "\nTRAIN:"
    )
    print(
        f"Rows: {len(train_df):,}"
    )
    print(
        f"Date: "
        f"{train_df[DATE_COLUMN].min()} "
        f"→ "
        f"{train_df[DATE_COLUMN].max()}"
    )
    print(
        f"Floods: "
        f"{int(train_df[TARGET].sum()):,}"
    )

    print(
        "\nVALIDATION:"
    )
    print(
        f"Rows: {len(validation_df):,}"
    )
    print(
        f"Date: "
        f"{validation_df[DATE_COLUMN].min()} "
        f"→ "
        f"{validation_df[DATE_COLUMN].max()}"
    )
    print(
        f"Floods: "
        f"{int(validation_df[TARGET].sum()):,}"
    )

    print(
        "\nTEST:"
    )
    print(
        f"Rows: {len(test_df):,}"
    )
    print(
        f"Date: "
        f"{test_df[DATE_COLUMN].min()} "
        f"→ "
        f"{test_df[DATE_COLUMN].max()}"
    )
    print(
        f"Floods: "
        f"{int(test_df[TARGET].sum()):,}"
    )

    # --------------------------------------------------------
    # EXPLICIT TEMPORAL ORDER CHECK
    # --------------------------------------------------------

    temporal_order_passed = (
        train_df[DATE_COLUMN].max()
        < validation_df[DATE_COLUMN].min()
        and
        validation_df[DATE_COLUMN].max()
        < test_df[DATE_COLUMN].min()
    )

    print("\n" + "=" * 75)
    print("TEMPORAL ORDER CHECK")
    print("=" * 75)

    print(
        "Temporal order:",
        "PASSED"
        if temporal_order_passed
        else "FAILED",
    )

    if not temporal_order_passed:
        raise ValueError(
            "Temporal ordering failed."
        )

    # --------------------------------------------------------
    # FEATURE MATRICES
    # --------------------------------------------------------

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET].astype(int)

    X_validation = validation_df[
        FEATURES
    ]
    y_validation = validation_df[
        TARGET
    ].astype(int)

    X_test = test_df[FEATURES]
    y_test = test_df[TARGET].astype(int)

    print("\n" + "=" * 75)
    print("FEATURE MATRIX")
    print("=" * 75)

    print(
        "Total ML features:",
        len(FEATURES),
    )

    print(
        "\nNumerical features:",
        len(NUMERICAL_FEATURES),
    )

    print(
        "Categorical features:",
        len(CATEGORICAL_FEATURES),
    )

    print(
        "\nX_train:",
        X_train.shape,
    )

    print(
        "X_validation:",
        X_validation.shape,
    )

    print(
        "X_test:",
        X_test.shape,
    )

    # --------------------------------------------------------
    # V1 STYLE ENSEMBLE: LOGISTIC + RF
    # --------------------------------------------------------

    print("\n" + "=" * 75)
    print("BASELINE V2 TRAINING")
    print("=" * 75)

    print(
        "\nTraining Logistic Regression..."
    )

    logistic_model = (
        create_logistic_model()
    )

    logistic_model.fit(
        X_train,
        y_train,
    )

    print(
        "Logistic Regression training complete."
    )

    print(
        "\nTraining Random Forest..."
    )

    rf_model = (
        create_random_forest_model()
    )

    rf_model.fit(
        X_train,
        y_train,
    )

    print(
        "Random Forest training complete."
    )

    # --------------------------------------------------------
    # VALIDATION PROBABILITIES
    # --------------------------------------------------------

    logistic_val_probability = (
        logistic_model
        .predict_proba(
            X_validation
        )[:, 1]
    )

    rf_val_probability = (
        rf_model
        .predict_proba(
            X_validation
        )[:, 1]
    )

    ensemble_val_probability = (
        logistic_val_probability
        + rf_val_probability
    ) / 2.0

    # --------------------------------------------------------
    # THRESHOLD OPTIMIZATION
    # --------------------------------------------------------

    print("\n" + "=" * 75)
    print("VALIDATION THRESHOLD OPTIMIZATION")
    print("=" * 75)

    best_threshold, threshold_df = (
        find_best_threshold(
            y_validation,
            ensemble_val_probability,
        )
    )

    threshold_report_file = (
        MODEL_DIR
        / "ensemble_v2_threshold_analysis.csv"
    )

    threshold_df.to_csv(
        threshold_report_file,
        index=False,
    )

    print(
        f"\nBest validation threshold: "
        f"{best_threshold:.2f}"
    )

    best_validation_metrics = (
        threshold_df.iloc[0].to_dict()
    )

    print(
        f"Validation Accuracy: "
        f"{best_validation_metrics['accuracy']:.4f}"
    )

    print(
        f"Validation Precision: "
        f"{best_validation_metrics['precision']:.4f}"
    )

    print(
        f"Validation Recall: "
        f"{best_validation_metrics['recall']:.4f}"
    )

    print(
        f"Validation F1: "
        f"{best_validation_metrics['f1']:.4f}"
    )

    print(
        f"Validation ROC-AUC: "
        f"{best_validation_metrics['roc_auc']:.4f}"
    )

    print(
        f"Validation PR-AUC: "
        f"{best_validation_metrics['pr_auc']:.4f}"
    )

    print(
        "\nValidation confusion matrix:"
    )

    print(
        f"TN: "
        f"{int(best_validation_metrics['true_negative'])}"
    )

    print(
        f"FP: "
        f"{int(best_validation_metrics['false_positive'])}"
    )

    print(
        f"FN: "
        f"{int(best_validation_metrics['false_negative'])}"
    )

    print(
        f"TP: "
        f"{int(best_validation_metrics['true_positive'])}"
    )

    # --------------------------------------------------------
    # FINAL TRAINING ON TRAIN + VALIDATION
    # --------------------------------------------------------

    print("\n" + "=" * 75)
    print("FINAL V2 TRAINING")
    print("=" * 75)

    X_final = pd.concat(
        [
            X_train,
            X_validation,
        ],
        axis=0,
    )

    y_final = pd.concat(
        [
            y_train,
            y_validation,
        ],
        axis=0,
    )

    print(
        "\nFinal training rows:",
        len(X_final),
    )

    print(
        "Final training flood rows:",
        int(y_final.sum()),
    )

    final_logistic = (
        create_logistic_model()
    )

    final_rf = (
        create_random_forest_model()
    )

    print(
        "\nTraining final Logistic Regression..."
    )

    final_logistic.fit(
        X_final,
        y_final,
    )

    print(
        "Done."
    )

    print(
        "\nTraining final Random Forest..."
    )

    final_rf.fit(
        X_final,
        y_final,
    )

    print(
        "Done."
    )

    # --------------------------------------------------------
    # TEST EVALUATION
    # --------------------------------------------------------

    logistic_test_probability = (
        final_logistic
        .predict_proba(
            X_test
        )[:, 1]
    )

    rf_test_probability = (
        final_rf
        .predict_proba(
            X_test
        )[:, 1]
    )

    ensemble_test_probability = (
        logistic_test_probability
        + rf_test_probability
    ) / 2.0

    test_metrics = calculate_metrics(
        y_test,
        ensemble_test_probability,
        best_threshold,
    )

    print("\n" + "=" * 75)
    print("2023 FINAL V2 TEST RESULTS")
    print("=" * 75)

    print(
        f"Threshold: "
        f"{best_threshold:.2f}"
    )

    print(
        f"Accuracy: "
        f"{test_metrics['accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{test_metrics['precision']:.4f}"
    )

    print(
        f"Recall: "
        f"{test_metrics['recall']:.4f}"
    )

    print(
        f"F1: "
        f"{test_metrics['f1']:.4f}"
    )

    print(
        f"ROC-AUC: "
        f"{test_metrics['roc_auc']:.4f}"
    )

    print(
        f"PR-AUC: "
        f"{test_metrics['pr_auc']:.4f}"
    )

    print(
        "\nConfusion matrix:"
    )

    print(
        f"TN: "
        f"{test_metrics['true_negative']}"
    )

    print(
        f"FP: "
        f"{test_metrics['false_positive']}"
    )

    print(
        f"FN: "
        f"{test_metrics['false_negative']}"
    )

    print(
        f"TP: "
        f"{test_metrics['true_positive']}"
    )

    # --------------------------------------------------------
    # SAVE MODELS
    # --------------------------------------------------------

    logistic_output = (
        MODEL_DIR
        / "ensemble_v2_logistic_model.joblib"
    )

    rf_output = (
        MODEL_DIR
        / "ensemble_v2_random_forest_model.joblib"
    )

    threshold_output = (
        MODEL_DIR
        / "ensemble_v2_threshold.txt"
    )

    config_output = (
        MODEL_DIR
        / "final_model_v2_config.json"
    )

    joblib.dump(
        final_logistic,
        logistic_output,
    )

    joblib.dump(
        final_rf,
        rf_output,
    )

    threshold_output.write_text(
        str(best_threshold),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # SAVE CONFIGURATION
    # --------------------------------------------------------

    config = {

        "project":
            "TerraPulse SIH 2026",

        "region":
            "Uttarakhand",

        "model_version":
            "V2",

        "model_type":
            "Ensemble",

        "ensemble_method":
            "Average Probability",

        "logistic_model":
            logistic_output.name,

        "random_forest_model":
            rf_output.name,

        "threshold":
            best_threshold,

        "training_period":
            "2020-2021",

        "validation_period":
            "2022",

        "test_period":
            "2023",

        "features":
            FEATURES,

        "numerical_features":
            NUMERICAL_FEATURES,

        "categorical_features":
            CATEGORICAL_FEATURES,

        "synthetic_features": [
            "slope_risk",
            "river_water_level_m",
            "river_danger_level_m",
            "river_level_ratio_to_danger",
            "river_rise_rate_m_per_hr",
            "river_level_change_3h_m",
            "river_level_change_6h_m",
            "river_level_change_24h_m",
            "temperature_c",
            "relative_humidity_pct",
            "wind_speed_kmh",
            "atmospheric_pressure_hpa",
            "weather_condition",
        ],

        "target":
            TARGET,

        "best_validation_metrics":
            {
                key: float(value)
                for key, value
                in best_validation_metrics.items()
                if isinstance(
                    value,
                    (int, float, np.integer, np.floating),
                )
            },

        "test_metrics":
            test_metrics,

        "data_note":
            (
                "River and weather variables are "
                "synthetic prototype values created "
                "for demonstration and integration "
                "testing. They are not CWC/IMD "
                "observations."
            ),

        "random_state":
            42,
    }

    with open(
        config_output,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            config,
            file,
            indent=4,
        )

    # --------------------------------------------------------
    # SAVE TEST PREDICTIONS
    # --------------------------------------------------------

    predictions_output = (
        MODEL_DIR
        / "ensemble_v2_test_predictions.csv"
    )

    predictions_df = pd.DataFrame(
        {
            "date":
                test_df[DATE_COLUMN].values,

            "district":
                test_df["district"].values,

            "actual_flood_label":
                y_test.values,

            "logistic_probability":
                logistic_test_probability,

            "random_forest_probability":
                rf_test_probability,

            "ensemble_probability":
                ensemble_test_probability,

            "predicted_flood_label":
                (
                    ensemble_test_probability
                    >= best_threshold
                ).astype(int),
        }
    )

    predictions_df.to_csv(
        predictions_output,
        index=False,
    )

    # --------------------------------------------------------
    # SAVE METRICS REPORT
    # --------------------------------------------------------

    metrics_output = (
        PROJECT_ROOT
        / "08_Reports"
        / "uttarakhand_v2_model_metrics.json"
    )

    metrics_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {

        "model_version":
            "V2",

        "region":
            "Uttarakhand",

        "validation":
            best_validation_metrics,

        "test":
            test_metrics,

        "training_rows":
            len(X_train),

        "validation_rows":
            len(X_validation),

        "test_rows":
            len(X_test),

        "final_training_rows":
            len(X_final),

        "features":
            FEATURES,

        "synthetic_data_note":
            (
                "River and weather variables are "
                "synthetic prototype inputs and "
                "must not be represented as live "
                "CWC/IMD observations."
            ),
    }

    with open(
        metrics_output,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            default=float,
        )

    # --------------------------------------------------------
    # SAVE MODEL COMPARISON
    # --------------------------------------------------------

    comparison_output = (
        PROJECT_ROOT
        / "08_Reports"
        / "uttarakhand_v2_model_summary.csv"
    )

    comparison_rows = [

        {
            "model":
                "logistic_regression",

            "validation_roc_auc":
                roc_auc_score(
                    y_validation,
                    logistic_val_probability,
                ),

            "validation_pr_auc":
                average_precision_score(
                    y_validation,
                    logistic_val_probability,
                ),

            "test_roc_auc":
                roc_auc_score(
                    y_test,
                    logistic_test_probability,
                ),

            "test_pr_auc":
                average_precision_score(
                    y_test,
                    logistic_test_probability,
                ),
        },

        {
            "model":
                "random_forest",

            "validation_roc_auc":
                roc_auc_score(
                    y_validation,
                    rf_val_probability,
                ),

            "validation_pr_auc":
                average_precision_score(
                    y_validation,
                    rf_val_probability,
                ),

            "test_roc_auc":
                roc_auc_score(
                    y_test,
                    rf_test_probability,
                ),

            "test_pr_auc":
                average_precision_score(
                    y_test,
                    rf_test_probability,
                ),
        },

        {
            "model":
                "ensemble",

            "validation_roc_auc":
                roc_auc_score(
                    y_validation,
                    ensemble_val_probability,
                ),

            "validation_pr_auc":
                average_precision_score(
                    y_validation,
                    ensemble_val_probability,
                ),

            "test_roc_auc":
                test_metrics["roc_auc"],

            "test_pr_auc":
                test_metrics["pr_auc"],
        },
    ]

    pd.DataFrame(
        comparison_rows
    ).to_csv(
        comparison_output,
        index=False,
    )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print("\n" + "=" * 75)
    print("UTTARAKHAND V2 TRAINING COMPLETE")
    print("=" * 75)

    print(
        "\nSaved models:"
    )

    print(
        logistic_output
    )

    print(
        rf_output
    )

    print(
        threshold_output
    )

    print(
        config_output
    )

    print(
        predictions_output
    )

    print(
        "\nSaved reports:"
    )

    print(metrics_output)

    print(comparison_output )

    print(threshold_report_file)

    print( "\nIMPORTANT:")

    print(
        "V2 river/weather features are synthetic "
        "prototype inputs."
    )

    print(
        "Do not present them as real CWC/IMD "
        "observations."
    )


if __name__ == "__main__":
    main()