import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "06_ML_Dataset", "terrapulse_improved_ml_dataset_2020_2023.csv")
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

NUMERIC_FEATURES = [
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "rainfall_14d",
    "rainfall_max_3d",
    "rainfall_max_7d",
    "rainy_days_7d",
    "rainfall_1d_to_7d",
    "rainfall_3d_to_7d",
    "soil_moisture",
    "mean_elevation",
    "mean_slope"
]

CATEGORICAL_FEATURES = ["district"]

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"])

train_2020 = df[df["date"].dt.year == 2020].copy()
val_2021 = df[df["date"].dt.year == 2021].copy()

train_2020_2021 = df[df["date"].dt.year.isin([2020, 2021])].copy()
val_2022 = df[df["date"].dt.year == 2022].copy()

numeric_transformer = Pipeline([
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline([
    ("onehot", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("num", numeric_transformer, NUMERIC_FEATURES),
    ("cat", categorical_transformer, CATEGORICAL_FEATURES)
])

logistic_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        random_state=42
    ))
])

random_forest_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        max_features="sqrt",
        min_samples_leaf=2
    ))
])

def evaluate_fold(train_df, val_df, fold_name):
    X_train = train_df[FEATURES]
    y_train = train_df["flood_label"].astype(int)

    X_val = val_df[FEATURES]
    y_val = val_df["flood_label"].astype(int)

    logistic_pipeline.fit(X_train, y_train)
    random_forest_pipeline.fit(X_train, y_train)

    lr_prob = logistic_pipeline.predict_proba(X_val)[:, 1]
    rf_prob = random_forest_pipeline.predict_proba(X_val)[:, 1]
    ensemble_prob = (lr_prob + rf_prob) / 2

    thresholds = np.arange(0.05, 0.91, 0.05)

    rows = []

    for threshold in thresholds:
        pred = (ensemble_prob >= threshold).astype(int)

        precision = precision_score(y_val, pred, zero_division=0)
        recall = recall_score(y_val, pred, zero_division=0)
        f1 = f1_score(y_val, pred, zero_division=0)

        rows.append({
            "fold": fold_name,
            "threshold": round(float(threshold), 2),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "actual_positives": int(y_val.sum()),
            "predicted_positives": int(pred.sum()),
            "roc_auc": roc_auc_score(y_val, ensemble_prob),
            "pr_auc": average_precision_score(y_val, ensemble_prob)
        })

    return pd.DataFrame(rows)

print("=" * 70)
print("TERRAPULSE WALK-FORWARD VALIDATION")
print("=" * 70)

results_2021 = evaluate_fold(
    train_2020,
    val_2021,
    "Train 2020 -> Validate 2021"
)

results_2022 = evaluate_fold(
    train_2020_2021,
    val_2022,
    "Train 2020-2021 -> Validate 2022"
)

results = pd.concat(
    [results_2021, results_2022],
    ignore_index=True
)

output_path = os.path.join(
    REPORT_DIR,
    "walk_forward_validation.csv"
)

results.to_csv(output_path, index=False)

best_2021 = results_2021.loc[
    results_2021["f1"].idxmax()
]

best_2022 = results_2022.loc[
    results_2022["f1"].idxmax()
]

print("\n2021 VALIDATION")
print(f"Actual positives: {best_2021['actual_positives']}")
print(f"Best threshold: {best_2021['threshold']:.2f}")
print(f"Precision: {best_2021['precision']:.4f}")
print(f"Recall: {best_2021['recall']:.4f}")
print(f"F1: {best_2021['f1']:.4f}")
print(f"ROC-AUC: {best_2021['roc_auc']:.4f}")
print(f"PR-AUC: {best_2021['pr_auc']:.4f}")

print("\n2022 VALIDATION")
print(f"Actual positives: {best_2022['actual_positives']}")
print(f"Best threshold: {best_2022['threshold']:.2f}")
print(f"Precision: {best_2022['precision']:.4f}")
print(f"Recall: {best_2022['recall']:.4f}")
print(f"F1: {best_2022['f1']:.4f}")
print(f"ROC-AUC: {best_2022['roc_auc']:.4f}")
print(f"PR-AUC: {best_2022['pr_auc']:.4f}")

print("\nTHRESHOLD STABILITY")
stability = results.pivot(
    index="threshold",
    columns="fold",
    values="f1"
)

print(stability.to_string())

print("\nALL VALIDATION RESULTS")
print(
    results[
        [
            "fold",
            "threshold",
            "precision",
            "recall",
            "f1",
            "actual_positives",
            "predicted_positives"
        ]
    ].to_string(index=False)
)

print("\nREPORT SAVED")
print("08_Reports/walk_forward_validation.csv")

print("=" * 70)