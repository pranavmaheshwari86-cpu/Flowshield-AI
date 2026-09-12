import os
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "06_ML_Dataset", "terrapulse_improved_ml_dataset_2020_2023.csv")
LR_PATH = os.path.join(BASE_DIR, "07_Models", "ensemble_logistic_model.joblib")
RF_PATH = os.path.join(BASE_DIR, "07_Models", "ensemble_random_forest_model.joblib")
THRESHOLD_PATH = os.path.join(BASE_DIR, "07_Models", "ensemble_threshold.txt")
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

test_df = df[df["date"].dt.year == 2023].copy()
X_test = test_df[FEATURES]
y_test = test_df["flood_label"].astype(int)

logistic_model = joblib.load(LR_PATH)
rf_model = joblib.load(RF_PATH)

logistic_prob = logistic_model.predict_proba(X_test)[:, 1]
rf_prob = rf_model.predict_proba(X_test)[:, 1]
ensemble_prob = (logistic_prob + rf_prob) / 2

with open(THRESHOLD_PATH, "r") as f:
    threshold = float(f.read().strip())

y_pred = (ensemble_prob >= threshold).astype(int)

test_df["probability"] = ensemble_prob
test_df["prediction"] = y_pred
test_df["actual"] = y_test.values
test_df["month"] = test_df["date"].dt.month
test_df["month_name"] = test_df["date"].dt.strftime("%B")

tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)
roc_auc = roc_auc_score(y_test, ensemble_prob)
pr_auc = average_precision_score(y_test, ensemble_prob)

actual_floods = int(y_test.sum())
predicted_floods = int(y_pred.sum())
false_alarm_rate = fp / (fp + tn) if (fp + tn) else 0
flood_detection_rate = tp / (tp + fn) if (tp + fn) else 0

print("=" * 60)
print("TERRAPULSE FINAL MODEL ERROR ANALYSIS")
print("=" * 60)
print(f"Test Period: 2023")
print(f"Test Samples: {len(test_df)}")
print(f"Threshold: {threshold:.2f}")
print()
print("CONFUSION MATRIX")
print(f"TN: {tn}")
print(f"FP: {fp}")
print(f"FN: {fn}")
print(f"TP: {tp}")
print()
print("OVERALL METRICS")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")
print(f"ROC-AUC: {roc_auc:.4f}")
print(f"PR-AUC: {pr_auc:.4f}")
print(f"Flood Detection Rate: {flood_detection_rate:.4f}")
print(f"False Alarm Rate: {false_alarm_rate:.4f}")
print(f"Actual Flood Cases: {actual_floods}")
print(f"Predicted Flood Cases: {predicted_floods}")

monthly_rows = []

for month in range(1, 13):
    m = test_df[test_df["month"] == month]
    if len(m) == 0:
        continue

    actual = m["actual"].values
    pred = m["prediction"].values

    m_tn, m_fp, m_fn, m_tp = confusion_matrix(actual, pred, labels=[0, 1]).ravel()

    monthly_rows.append({
        "month": month,
        "month_name": m["month_name"].iloc[0],
        "samples": len(m),
        "actual_floods": int(actual.sum()),
        "predicted_floods": int(pred.sum()),
        "TP": m_tp,
        "FP": m_fp,
        "FN": m_fn,
        "TN": m_tn,
        "recall": m_tp / (m_tp + m_fn) if (m_tp + m_fn) else 0,
        "false_alarm_rate": m_fp / (m_fp + m_tn) if (m_fp + m_tn) else 0
    })

monthly_df = pd.DataFrame(monthly_rows)

district_rows = []

for district in sorted(test_df["district"].unique()):
    d = test_df[test_df["district"] == district]
    actual = d["actual"].values
    pred = d["prediction"].values

    d_tn, d_fp, d_fn, d_tp = confusion_matrix(actual, pred, labels=[0, 1]).ravel()

    district_rows.append({
        "district": district,
        "samples": len(d),
        "actual_floods": int(actual.sum()),
        "predicted_floods": int(pred.sum()),
        "TP": d_tp,
        "FP": d_fp,
        "FN": d_fn,
        "TN": d_tn,
        "recall": d_tp / (d_tp + d_fn) if (d_tp + d_fn) else 0,
        "false_alarm_rate": d_fp / (d_fp + d_tn) if (d_fp + d_tn) else 0
    })

district_df = pd.DataFrame(district_rows)

false_positives = test_df[
    (test_df["actual"] == 0) &
    (test_df["prediction"] == 1)
].copy()

false_negatives = test_df[
    (test_df["actual"] == 1) &
    (test_df["prediction"] == 0)
].copy()

fp_columns = [
    "date",
    "district",
    "probability",
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "rainfall_14d",
    "rainfall_30d",
    "rainfall_max_3d",
    "rainfall_max_7d",
    "rainy_days_7d",
    "soil_moisture",
    "mean_elevation",
    "mean_slope"
]

fn_columns = fp_columns

false_positives = false_positives.sort_values("probability", ascending=False)
false_negatives = false_negatives.sort_values("probability", ascending=True)

false_positives[fp_columns].to_csv(
    os.path.join(REPORT_DIR, "final_false_positives_2023.csv"),
    index=False
)

false_negatives[fn_columns].to_csv(
    os.path.join(REPORT_DIR, "final_false_negatives_2023.csv"),
    index=False
)

monthly_df.to_csv(
    os.path.join(REPORT_DIR, "final_monthly_performance_2023.csv"),
    index=False
)

district_df.to_csv(
    os.path.join(REPORT_DIR, "final_district_performance_2023.csv"),
    index=False
)

error_df = test_df[
    (test_df["actual"] != test_df["prediction"])
].copy()

error_df["error_type"] = np.where(
    error_df["actual"] == 1,
    "False Negative",
    "False Positive"
)

error_df = error_df.sort_values("probability", ascending=False)

error_df[
    [
        "date",
        "district",
        "actual",
        "prediction",
        "probability",
        "error_type",
        "rainfall_1d",
        "rainfall_3d",
        "rainfall_7d",
        "rainfall_14d",
        "rainfall_30d",
        "soil_moisture",
        "mean_elevation",
        "mean_slope"
    ]
].to_csv(
    os.path.join(REPORT_DIR, "final_model_error_analysis_2023.csv"),
    index=False
)

print()
print("MONTH-WISE PERFORMANCE")
print(monthly_df.to_string(index=False))

print()
print("DISTRICT-WISE PERFORMANCE")
print(district_df.to_string(index=False))

print()
print("TOP 10 FALSE POSITIVES")
print(false_positives[["date", "district", "probability"]].head(10).to_string(index=False))

print()
print("ALL FALSE NEGATIVES")
print(false_negatives[["date", "district", "probability"]].to_string(index=False))

print()
print("REPORT FILES SAVED")
print("08_Reports/final_false_positives_2023.csv")
print("08_Reports/final_false_negatives_2023.csv")
print("08_Reports/final_monthly_performance_2023.csv")
print("08_Reports/final_district_performance_2023.csv")
print("08_Reports/final_model_error_analysis_2023.csv")
print("=" * 60)