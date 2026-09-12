import os
import joblib
import pandas as pd

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
logistic_model = joblib.load(LOGISTIC_MODEL)
rf_model = joblib.load(RF_MODEL)

positive_cases = df[df["flood_label"] == 1].copy()
negative_cases = df[df["flood_label"] == 0].copy()

test_cases = pd.concat([
    positive_cases.head(10),
    negative_cases.head(10)
])

X = test_cases[FEATURES]

logistic_prob = logistic_model.predict_proba(X)[:, 1]
rf_prob = rf_model.predict_proba(X)[:, 1]

ensemble_prob = (logistic_prob + rf_prob) / 2

results = pd.DataFrame({
    "date": test_cases["date"].values,
    "district": test_cases["district"].values,
    "actual_label": test_cases["flood_label"].values,
    "probability_percent": (ensemble_prob * 100).round(2)
})

results["predicted_risk"] = results["probability_percent"].apply(
    lambda x: "HIGH" if x >= 30 else "MODERATE" if x >= 15 else "LOW"
)

print("\n===== TerraPulse Historical Prediction Test =====")
print(results.to_string(index=False))

print("\n===== Summary =====")
print(f"Total test cases: {len(results)}")
print(f"Actual flood cases: {(results['actual_label'] == 1).sum()}")
print(f"Actual non-flood cases: {(results['actual_label'] == 0).sum()}")
print(f"Predicted HIGH: {(results['predicted_risk'] == 'HIGH').sum()}")
print(f"Predicted MODERATE: {(results['predicted_risk'] == 'MODERATE').sum()}")
print(f"Predicted LOW: {(results['predicted_risk'] == 'LOW').sum()}")