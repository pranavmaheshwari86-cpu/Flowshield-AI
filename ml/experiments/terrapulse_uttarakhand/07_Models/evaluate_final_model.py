import os
import joblib
import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET = os.path.join(
    BASE_DIR,
    "..",
    "06_ML_Dataset",
    "terrapulse_improved_ml_dataset_2020_2023.csv"
)

LOGISTIC_MODEL = os.path.join(
    BASE_DIR,
    "ensemble_logistic_model.joblib"
)

RF_MODEL = os.path.join(
    BASE_DIR,
    "ensemble_random_forest_model.joblib"
)

THRESHOLD = 0.30

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

df = pd.read_csv(DATASET)
df["date"] = pd.to_datetime(df["date"])

test_df = df[df["date"].dt.year == 2023].copy()

X_test = test_df[FEATURES]
y_test = test_df["flood_label"]

logistic_model = joblib.load(LOGISTIC_MODEL)
rf_model = joblib.load(RF_MODEL)

logistic_probability = logistic_model.predict_proba(X_test)[:, 1]
rf_probability = rf_model.predict_proba(X_test)[:, 1]

ensemble_probability = (
    logistic_probability + rf_probability
) / 2

y_pred = (ensemble_probability >= THRESHOLD).astype(int)

tn, fp, fn, tp = confusion_matrix(
    y_test,
    y_pred,
    labels=[0, 1]
).ravel()

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    ensemble_probability
)

pr_auc = average_precision_score(
    y_test,
    ensemble_probability
)

print("\n===== TerraPulse Final Model Evaluation =====")
print(f"Test period: 2023")
print(f"Test samples: {len(test_df)}")
print(f"Actual positive cases: {int(y_test.sum())}")
print(f"Threshold: {THRESHOLD}")

print("\n===== Confusion Matrix =====")
print(f"True Negatives : {tn}")
print(f"False Positives: {fp}")
print(f"False Negatives: {fn}")
print(f"True Positives : {tp}")

print("\n===== Metrics =====")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")
print(f"ROC-AUC  : {roc_auc:.4f}")
print(f"PR-AUC   : {pr_auc:.4f}")

print("\n===== Classification Report =====")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=["No Flood", "Flood"],
        zero_division=0
    )
)

print("\n===== Prediction Summary =====")
print(f"Predicted LOW/negative : {(y_pred == 0).sum()}")
print(f"Predicted HIGH/positive: {(y_pred == 1).sum()}")

print("\nEvaluation completed successfully.")