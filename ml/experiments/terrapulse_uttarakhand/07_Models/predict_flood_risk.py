# Flow --

# User/Dashboard Input
#         ↓
# Rainfall + Soil Moisture + Terrain
#         ↓
# Feature Engineering
#         ↓
# Logistic Regression ─┐
#                       ├── Average Probability
# Random Forest ────────┘
#         ↓
# Probability
#         ↓
# Threshold = 0.30
#         ↓
# LOW / MODERATE / HIGH

import os
import json
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "final_model_config.json")
LOGISTIC_FILE = os.path.join(BASE_DIR, "ensemble_logistic_model.joblib")
RF_FILE = os.path.join(BASE_DIR, "ensemble_random_forest_model.joblib")

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

logistic_model = joblib.load(LOGISTIC_FILE)
rf_model = joblib.load(RF_FILE)

THRESHOLD = config["threshold"]

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

def predict_flood_risk(input_data):
    row = pd.DataFrame([input_data])

    missing = [feature for feature in FEATURES if feature not in row.columns]

    if missing:
        raise ValueError(f"Missing features: {missing}")

    row = row[FEATURES]

    logistic_probability = logistic_model.predict_proba(row)[0][1]
    rf_probability = rf_model.predict_proba(row)[0][1]

    ensemble_probability = (logistic_probability + rf_probability) / 2

    if ensemble_probability >= THRESHOLD:
        risk_level = "HIGH"
        warning = "Flash flood risk detected. Early warning recommended."
    elif ensemble_probability >= THRESHOLD * 0.5:
        risk_level = "MODERATE"
        warning = "Elevated flood risk. Continue monitoring conditions."
    else:
        risk_level = "LOW"
        warning = "Low predicted flash flood risk."

    return {
        "district": input_data["district"],
        "probability": round(float(ensemble_probability), 4),
        "probability_percent": round(float(ensemble_probability * 100), 2),
        "risk_level": risk_level,
        "warning": warning,
        "threshold": THRESHOLD
    }

def predict_from_csv(csv_file, row_number=0):
    df = pd.read_csv(csv_file)

    if row_number >= len(df):
        raise ValueError(f"Row number {row_number} is outside the dataset.")

    input_data = df.iloc[row_number][FEATURES].to_dict()

    return predict_flood_risk(input_data)

if __name__ == "__main__":
    dataset_file = os.path.join(
        BASE_DIR,
        "..",
        "06_ML_Dataset",
        "terrapulse_improved_ml_dataset_2020_2023.csv"
    )

    result = predict_from_csv(dataset_file, row_number=1000)

    print("\n===== TerraPulse Flood Risk Prediction =====")
    print(f"District: {result['district']}")
    print(f"Probability: {result['probability_percent']}%")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Threshold: {result['threshold']}")
    print(f"Warning: {result['warning']}")