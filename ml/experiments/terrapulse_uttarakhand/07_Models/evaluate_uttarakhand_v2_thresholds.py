"""
TerraPulse SIH 2026
Uttarakhand V2 Threshold Evaluation

Purpose:
    Evaluate the already-trained Uttarakhand V2 ensemble model
    across multiple probability thresholds.

IMPORTANT:
    - Does NOT retrain the model.
    - Does NOT modify the dataset.
    - Does NOT overwrite the trained V2 models.
    - Uses the saved V2 test predictions generated during training.
    - Because the V2 dataset contains synthetic river/weather
      prototype features, results must be treated as prototype
      evaluation only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_DIR = PROJECT_ROOT / "07_Models"
REPORT_DIR = PROJECT_ROOT / "08_Reports"

PREDICTIONS_FILE = (
    MODEL_DIR
    / "ensemble_v2_test_predictions.csv"
)

OUTPUT_FILE = (
    MODEL_DIR
    / "ensemble_v2_threshold_evaluation.csv"
)

SUMMARY_FILE = (
    REPORT_DIR
    / "uttarakhand_v2_threshold_summary.json"
)

REPORT_MD_FILE = (
    REPORT_DIR
    / "uttarakhand_v2_threshold_analysis.md"
)


# ============================================================
# 2. CONFIGURATION
# ============================================================

# Full threshold sweep.
THRESHOLDS = np.round(
    np.arange(
        0.01,
        1.00,
        0.01,
    ),
    2,
)


# ============================================================
# 3. METRICS FUNCTION
# ============================================================

def evaluate_threshold(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> dict:
    """
    Calculate classification metrics for a single threshold.
    """

    predictions = (
        probabilities >= threshold
    ).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[0, 1],
    ).ravel()

    precision = precision_score(
        y_true,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        predictions,
        zero_division=0,
    )

    accuracy = (
        (tn + tp)
        / max(tn + fp + fn + tp, 1)
    )

    # False Positive Rate
    fpr = (
        fp
        / max(fp + tn, 1)
    )

    # False Negative Rate
    fnr = (
        fn
        / max(fn + tp, 1)
    )

    # Positive prediction rate
    predicted_positive_rate = (
        (tp + fp)
        / max(tn + fp + fn + tp, 1)
    )

    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_positive_rate": float(fpr),
        "false_negative_rate": float(fnr),
        "predicted_positive_rate": float(
            predicted_positive_rate
        ),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


# ============================================================
# 4. BEST THRESHOLD HELPERS
# ============================================================

def choose_best(
    results_df: pd.DataFrame,
    primary_metric: str,
    secondary_metric: str,
    tertiary_metric: str,
) -> pd.Series:
    """
    Choose threshold using descending metric priority.
    Lower threshold wins final tie.
    """

    ordered = results_df.sort_values(
        by=[
            primary_metric,
            secondary_metric,
            tertiary_metric,
            "threshold",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
    )

    return ordered.iloc[0]


# ============================================================
# 5. MAIN
# ============================================================

def main():

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 80)
    print("TERRAPULSE V3 — UTTARAKHAND V2 THRESHOLD ANALYSIS")
    print("=" * 80)

    print("\nProject root:")
    print(PROJECT_ROOT)

    print("\nPredictions file:")
    print(PREDICTIONS_FILE)

    # --------------------------------------------------------
    # LOAD SAVED TEST PREDICTIONS
    # --------------------------------------------------------

    if not PREDICTIONS_FILE.exists():

        raise FileNotFoundError(
            "\nV2 test predictions file was not found:\n"
            f"{PREDICTIONS_FILE}\n\n"
            "Run the V2 training script first."
        )

    df = pd.read_csv(
        PREDICTIONS_FILE
    )

    print(
        "\nSaved test predictions loaded successfully."
    )

    print(
        f"Rows: {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    required_columns = [
        "actual_flood_label",
        "ensemble_probability",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Required columns missing from prediction file:\n"
            + "\n".join(
                f" - {column}"
                for column in missing_columns
            )
        )

    # --------------------------------------------------------
    # CLEAN TARGET / PROBABILITIES
    # --------------------------------------------------------

    y_true = pd.to_numeric(
        df["actual_flood_label"],
        errors="coerce",
    )

    probabilities = pd.to_numeric(
        df["ensemble_probability"],
        errors="coerce",
    )

    valid = (
        y_true.notna()
        & probabilities.notna()
    )

    if not valid.all():

        invalid_count = int(
            (~valid).sum()
        )

        print(
            f"\nWARNING: "
            f"{invalid_count} invalid rows removed "
            "from threshold analysis."
        )

    y_true = (
        y_true.loc[valid]
        .astype(int)
        .to_numpy()
    )

    probabilities = (
        probabilities.loc[valid]
        .astype(float)
        .to_numpy()
    )

    if len(y_true) == 0:

        raise ValueError(
            "No valid evaluation rows remain."
        )

    unique_targets = np.unique(
        y_true
    )

    if len(unique_targets) < 2:

        raise ValueError(
            "Test data contains only one target class."
        )

    # --------------------------------------------------------
    # BASELINE PROBABILITY METRIC
    # --------------------------------------------------------

    pr_auc = average_precision_score(
        y_true,
        probabilities,
    )

    print("\n" + "=" * 80)
    print("TEST PROBABILITY QUALITY")
    print("=" * 80)

    print(
        f"PR-AUC: {pr_auc:.4f}"
    )

    print(
        f"Actual positive cases: "
        f"{int(y_true.sum())}"
    )

    print(
        f"Actual negative cases: "
        f"{int((y_true == 0).sum())}"
    )

    print(
        f"Positive rate: "
        f"{(y_true.mean() * 100):.2f}%"
    )

    print(
        f"Probability min: "
        f"{probabilities.min():.6f}"
    )

    print(
        f"Probability median: "
        f"{np.median(probabilities):.6f}"
    )

    print(
        f"Probability mean: "
        f"{probabilities.mean():.6f}"
    )

    print(
        f"Probability max: "
        f"{probabilities.max():.6f}"
    )

    # --------------------------------------------------------
    # THRESHOLD SWEEP
    # --------------------------------------------------------

    results = []

    print("\n" + "=" * 80)
    print("THRESHOLD SWEEP")
    print("=" * 80)

    print(
        "\nThreshold | Precision | Recall | F1 | FPR | TP | FP | FN | TN"
    )
    print("-" * 80)

    for threshold in THRESHOLDS:

        metrics = evaluate_threshold(
            y_true=y_true,
            probabilities=probabilities,
            threshold=float(threshold),
        )

        metrics["pr_auc"] = float(
            pr_auc
        )

        results.append(
            metrics
        )

        print(
            f"{threshold:9.2f} | "
            f"{metrics['precision']:9.4f} | "
            f"{metrics['recall']:6.4f} | "
            f"{metrics['f1']:6.4f} | "
            f"{metrics['false_positive_rate']:5.4f} | "
            f"{metrics['true_positive']:2d} | "
            f"{metrics['false_positive']:3d} | "
            f"{metrics['false_negative']:2d} | "
            f"{metrics['true_negative']:4d}"
        )

    results_df = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # OPERATING POINTS
    # --------------------------------------------------------

    # Best F1
    best_f1 = choose_best(
        results_df,
        primary_metric="f1",
        secondary_metric="recall",
        tertiary_metric="precision",
    )

    # Best recall while keeping threshold >= 0.10
    recall_candidates = results_df[
        results_df["threshold"] >= 0.10
    ]

    best_recall = choose_best(
        recall_candidates,
        primary_metric="recall",
        secondary_metric="f1",
        tertiary_metric="precision",
    )

    # Best precision
    best_precision = choose_best(
        results_df,
        primary_metric="precision",
        secondary_metric="f1",
        tertiary_metric="recall",
    )

    # Lowest false-positive rate
    lowest_fpr = (
    results_df
    .sort_values(
        by=[
            "false_positive_rate",
            "false_negative_rate",
            "threshold",
        ],
        ascending=[
            True,
            True,
            False,
        ],
    )
    .iloc[0]
)

    # --------------------------------------------------------
    # EXISTING V2 THRESHOLD
    # --------------------------------------------------------

    existing_threshold = 0.38

    existing_matches = results_df[
        np.isclose(
            results_df["threshold"],
            existing_threshold,
        )
    ]

    if not existing_matches.empty:

        existing_result = (
            existing_matches.iloc[0]
        )

    else:

        existing_result = None

    # --------------------------------------------------------
    # SAVE COMPLETE RESULTS
    # --------------------------------------------------------

    results_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # PRINT BEST OPERATING POINTS
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("BEST OPERATING POINTS")
    print("=" * 80)

    print(
        "\n1. BEST F1 THRESHOLD"
    )

    print(
        f"Threshold : "
        f"{best_f1['threshold']:.2f}"
    )

    print(
        f"Precision : "
        f"{best_f1['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{best_f1['recall']:.4f}"
    )

    print(
        f"F1        : "
        f"{best_f1['f1']:.4f}"
    )

    print(
        f"FPR       : "
        f"{best_f1['false_positive_rate']:.4f}"
    )

    print(
        f"TP/FP/FN/TN: "
        f"{int(best_f1['true_positive'])}/"
        f"{int(best_f1['false_positive'])}/"
        f"{int(best_f1['false_negative'])}/"
        f"{int(best_f1['true_negative'])}"
    )

    print(
        "\n2. BEST RECALL THRESHOLD "
        "(threshold >= 0.10)"
    )

    print(
        f"Threshold : "
        f"{best_recall['threshold']:.2f}"
    )

    print(
        f"Precision : "
        f"{best_recall['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{best_recall['recall']:.4f}"
    )

    print(
        f"F1        : "
        f"{best_recall['f1']:.4f}"
    )

    print(
        f"FPR       : "
        f"{best_recall['false_positive_rate']:.4f}"
    )

    print(
        "\n3. BEST PRECISION THRESHOLD"
    )

    print(
        f"Threshold : "
        f"{best_precision['threshold']:.2f}"
    )

    print(
        f"Precision : "
        f"{best_precision['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{best_precision['recall']:.4f}"
    )

    print(
        f"F1        : "
        f"{best_precision['f1']:.4f}"
    )

    print(
        f"FPR       : "
        f"{best_precision['false_positive_rate']:.4f}"
    )

    print(
        "\n4. LOWEST FALSE-POSITIVE-RATE THRESHOLD"
    )

    print(
        f"Threshold : "
        f"{lowest_fpr['threshold']:.2f}"
    )

    print(
        f"Precision : "
        f"{lowest_fpr['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{lowest_fpr['recall']:.4f}"
    )

    print(
        f"F1        : "
        f"{lowest_fpr['f1']:.4f}"
    )

    print(
        f"FPR       : "
        f"{lowest_fpr['false_positive_rate']:.4f}"
    )

    # --------------------------------------------------------
    # EXISTING THRESHOLD REPORT
    # --------------------------------------------------------

    if existing_result is not None:

        print(
            "\n" + "=" * 80
        )

        print(
            "CURRENT V2 THRESHOLD CHECK"
        )

        print(
            "=" * 80
        )

        print(
            f"\nExisting threshold: "
            f"{existing_threshold:.2f}"
        )

        print(
            f"Precision: "
            f"{existing_result['precision']:.4f}"
        )

        print(
            f"Recall: "
            f"{existing_result['recall']:.4f}"
        )

        print(
            f"F1: "
            f"{existing_result['f1']:.4f}"
        )

        print(
            f"FPR: "
            f"{existing_result['false_positive_rate']:.4f}"
        )

        print(
            f"TP: {int(existing_result['true_positive'])}"
        )

        print(
            f"FP: {int(existing_result['false_positive'])}"
        )

        print(
            f"FN: {int(existing_result['false_negative'])}"
        )

        print(
            f"TN: {int(existing_result['true_negative'])}"
        )

    # --------------------------------------------------------
    # DECISION SUPPORT
    # --------------------------------------------------------

    # For a flood early-warning system, recall is important,
    # but a threshold causing enormous false alarms is undesirable.
    #
    # We therefore define a practical candidate pool using:
    #   - recall >= 0.50
    #   - precision >= 0.05
    #
    # If no threshold satisfies this, we report that honestly.

    practical_candidates = results_df[
        (results_df["recall"] >= 0.50)
        & (results_df["precision"] >= 0.05)
    ]

    if not practical_candidates.empty:

        practical = choose_best(
            practical_candidates,
            primary_metric="f1",
            secondary_metric="recall",
            tertiary_metric="precision",
        )

        practical_status = (
            "PRACTICAL_CANDIDATE_FOUND"
        )

    else:

        practical = None

        practical_status = (
            "NO_PRACTICAL_THRESHOLD_FOUND"
        )

    print(
        "\n" + "=" * 80
    )

    print(
        "EARLY-WARNING OPERATING POINT"
    )

    print(
        "=" * 80
    )

    print(
        f"\nStatus: {practical_status}"
    )

    if practical is not None:

        print(
            f"Threshold : "
            f"{practical['threshold']:.2f}"
        )

        print(
            f"Precision : "
            f"{practical['precision']:.4f}"
        )

        print(
            f"Recall    : "
            f"{practical['recall']:.4f}"
        )

        print(
            f"F1        : "
            f"{practical['f1']:.4f}"
        )

        print(
            f"FPR       : "
            f"{practical['false_positive_rate']:.4f}"
        )

    else:

        print(
            "\nNo threshold simultaneously achieved "
            "the configured minimum precision and recall."
        )

        print(
            "This suggests the current V2 model "
            "needs model/data improvement rather "
            "than threshold adjustment alone."
        )

    # --------------------------------------------------------
    # SUMMARY JSON
    # --------------------------------------------------------

    summary = {

        "project":
            "TerraPulse SIH 2026",

        "region":
            "Uttarakhand",

        "model_version":
            "V2",

        "test_rows":
            int(len(y_true)),

        "actual_positive_cases":
            int(y_true.sum()),

        "actual_negative_cases":
            int((y_true == 0).sum()),

        "positive_rate":
            float(y_true.mean()),

        "pr_auc":
            float(pr_auc),

        "current_threshold":
            existing_threshold,

        "best_f1": {
            key: (
                float(value)
                if isinstance(
                    value,
                    (np.integer, np.floating)
                )
                else int(value)
                if isinstance(
                    value,
                    np.integer,
                )
                else value
            )
            for key, value in best_f1.to_dict().items()
        },

        "best_recall": {
            key: (
                float(value)
                if isinstance(
                    value,
                    (np.integer, np.floating)
                )
                else int(value)
                if isinstance(
                    value,
                    np.integer,
                )
                else value
            )
            for key, value in best_recall.to_dict().items()
        },

        "best_precision": {
            key: (
                float(value)
                if isinstance(
                    value,
                    (np.integer, np.floating)
                )
                else int(value)
                if isinstance(
                    value,
                    np.integer,
                )
                else value
            )
            for key, value in best_precision.to_dict().items()
        },

        "lowest_fpr": {
            key: (
                float(value)
                if isinstance(
                    value,
                    (np.integer, np.floating)
                )
                else int(value)
                if isinstance(
                    value,
                    np.integer,
                )
                else value
            )
            for key, value in lowest_fpr.to_dict().items()
        },

        "practical_threshold_status":
            practical_status,

        "practical_threshold":
            (
                float(practical["threshold"])
                if practical is not None
                else None
            ),

        "note":
            (
                "River and weather features in the V2 "
                "training dataset are synthetic prototype "
                "inputs. Threshold results are therefore "
                "for software/model demonstration and "
                "must not be interpreted as real-world "
                "operational flood-warning performance."
            ),
    }

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        import json

        json.dump(
            summary,
            file,
            indent=4,
            default=float,
        )

    # --------------------------------------------------------
    # MARKDOWN REPORT
    # --------------------------------------------------------

    report_lines = [

        "# TerraPulse V3 — Uttarakhand V2 Threshold Analysis",
        "",
        "## Dataset",
        "",
        f"- Test predictions: `{PREDICTIONS_FILE.relative_to(PROJECT_ROOT)}`",
        f"- Test rows: `{len(y_true):,}`",
        f"- Actual flood cases: `{int(y_true.sum()):,}`",
        f"- Actual non-flood cases: `{int((y_true == 0).sum()):,}`",
        f"- PR-AUC: `{pr_auc:.4f}`",
        "",
        "## Current V2 Threshold",
        "",
        f"- Threshold: `{existing_threshold:.2f}`",
    ]

    if existing_result is not None:

        report_lines.extend(
            [
                f"- Precision: `{existing_result['precision']:.4f}`",
                f"- Recall: `{existing_result['recall']:.4f}`",
                f"- F1: `{existing_result['f1']:.4f}`",
                f"- FPR: `{existing_result['false_positive_rate']:.4f}`",
            ]
        )

    report_lines.extend(
        [
            "",
            "## Best F1 Threshold",
            "",
            f"- Threshold: `{best_f1['threshold']:.2f}`",
            f"- Precision: `{best_f1['precision']:.4f}`",
            f"- Recall: `{best_f1['recall']:.4f}`",
            f"- F1: `{best_f1['f1']:.4f}`",
            f"- FPR: `{best_f1['false_positive_rate']:.4f}`",
            "",
            "## Best Recall Threshold",
            "",
            f"- Threshold: `{best_recall['threshold']:.2f}`",
            f"- Precision: `{best_recall['precision']:.4f}`",
            f"- Recall: `{best_recall['recall']:.4f}`",
            f"- F1: `{best_recall['f1']:.4f}`",
            f"- FPR: `{best_recall['false_positive_rate']:.4f}`",
            "",
            "## Best Precision Threshold",
            "",
            f"- Threshold: `{best_precision['threshold']:.2f}`",
            f"- Precision: `{best_precision['precision']:.4f}`",
            f"- Recall: `{best_precision['recall']:.4f}`",
            f"- F1: `{best_precision['f1']:.4f}`",
            f"- FPR: `{best_precision['false_positive_rate']:.4f}`",
            "",
            "## Practical Early-Warning Candidate",
            "",
            f"- Status: `{practical_status}`",
        ]
    )

    if practical is not None:

        report_lines.extend(
            [
                f"- Threshold: `{practical['threshold']:.2f}`",
                f"- Precision: `{practical['precision']:.4f}`",
                f"- Recall: `{practical['recall']:.4f}`",
                f"- F1: `{practical['f1']:.4f}`",
                f"- FPR: `{practical['false_positive_rate']:.4f}`",
            ]
        )

    else:

        report_lines.append(
            "- No practical threshold met both minimum precision and recall criteria."
        )

    report_lines.extend(
        [
            "",
            "## Important Interpretation",
            "",
            "Threshold optimization cannot create predictive signal that is absent from the model.",
            "Because the V2 river and weather variables are synthetic prototype inputs, these results are suitable for software demonstration only.",
            "",
            "## Complete Threshold Sweep",
            "",
            "See `ensemble_v2_threshold_evaluation.csv` for all thresholds from 0.01 to 0.99.",
            "",
        ]
    )

    REPORT_MD_FILE.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------------

    print(
        "\n" + "=" * 80
    )

    print(
        "THRESHOLD ANALYSIS COMPLETE"
    )

    print(
        "=" * 80
    )

    print(
        "\nGenerated files:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        SUMMARY_FILE
    )

    print(
        REPORT_MD_FILE
    )

    print(
        "\nNo model was retrained."
    )

    print(
        "No source dataset was modified."
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "V2 river/weather features are synthetic "
        "prototype inputs."
    )

    print(
        "Do not present threshold results as "
        "real-world operational flood-warning accuracy."
    )


if __name__ == "__main__":
    main()