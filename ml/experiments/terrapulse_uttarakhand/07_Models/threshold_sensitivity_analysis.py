import os
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "06_ML_Dataset", "terrapulse_improved_ml_dataset_2020_2023.csv")
LR_PATH = os.path.join(BASE_DIR, "07_Models", "ensemble_logistic_model.joblib")
RF_PATH = os.path.join(BASE_DIR, "07_Models", "ensemble_random_forest_model.joblib")
REPORT_DIR = os.path.join(BASE_DIR, "08_Reports")

FEATURES = [
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
    "district"
]

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"])

validation_df = df[df["date"].dt.year == 2022].copy()
test_df = df[df["date"].dt.year == 2023].copy()

X_val = validation_df[FEATURES]
y_val = validation_df["flood_label"].astype(int)

X_test = test_df[FEATURES]
y_test = test_df["flood_label"].astype(int)

logistic_model = joblib.load(LR_PATH)
rf_model = joblib.load(RF_PATH)

val_lr_prob = logistic_model.predict_proba(X_val)[:, 1]
val_rf_prob = rf_model.predict_proba(X_val)[:, 1]
val_prob = (val_lr_prob + val_rf_prob) / 2

test_lr_prob = logistic_model.predict_proba(X_test)[:, 1]
test_rf_prob = rf_model.predict_proba(X_test)[:, 1]
test_prob = (test_lr_prob + test_rf_prob) / 2

thresholds = np.arange(0.05, 0.91, 0.05)

rows = []

for threshold in thresholds:
    val_pred = (val_prob >= threshold).astype(int)
    test_pred = (test_prob >= threshold).astype(int)

    val_tn, val_fp, val_fn, val_tp = confusion_matrix(
        y_val, val_pred, labels=[0, 1]
    ).ravel()

    test_tn, test_fp, test_fn, test_tp = confusion_matrix(
        y_test, test_pred, labels=[0, 1]
    ).ravel()

    val_precision = precision_score(y_val, val_pred, zero_division=0)
    val_recall = recall_score(y_val, val_pred, zero_division=0)
    val_f1 = f1_score(y_val, val_pred, zero_division=0)

    test_precision = precision_score(y_test, test_pred, zero_division=0)
    test_recall = recall_score(y_test, test_pred, zero_division=0)
    test_f1 = f1_score(y_test, test_pred, zero_division=0)

    rows.append({
        "threshold": round(float(threshold), 2),
        "validation_precision": val_precision,
        "validation_recall": val_recall,
        "validation_f1": val_f1,
        "validation_TP": val_tp,
        "validation_FP": val_fp,
        "validation_FN": val_fn,
        "test_precision": test_precision,
        "test_recall": test_recall,
        "test_f1": test_f1,
        "test_TP": test_tp,
        "test_FP": test_fp,
        "test_FN": test_fn,
        "test_predicted_floods": int(test_pred.sum())
    })

results = pd.DataFrame(rows)

output_path = os.path.join(
    REPORT_DIR,
    "threshold_sensitivity_analysis.csv"
)

results.to_csv(output_path, index=False)

best_validation = results.loc[
    results["validation_f1"].idxmax()
]

print("=" * 70)
print("TERRAPULSE THRESHOLD SENSITIVITY ANALYSIS")
print("=" * 70)

print("\nVALIDATION PERIOD: 2022")
print(f"Best threshold by validation F1: {best_validation['threshold']:.2f}")
print(f"Validation Precision: {best_validation['validation_precision']:.4f}")
print(f"Validation Recall: {best_validation['validation_recall']:.4f}")
print(f"Validation F1: {best_validation['validation_f1']:.4f}")

print("\nTHRESHOLD COMPARISON")
print(
    results[
        [
            "threshold",
            "validation_precision",
            "validation_recall",
            "validation_f1",
            "test_precision",
            "test_recall",
            "test_f1",
            "test_TP",
            "test_FP",
            "test_FN",
            "test_predicted_floods"
        ]
    ].to_string(index=False)
)

print("\nREPORT SAVED")
print("08_Reports/threshold_sensitivity_analysis.csv")

print("=" * 70)