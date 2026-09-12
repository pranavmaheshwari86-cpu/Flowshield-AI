import json
import os

import joblib
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

from dashboard_predict import calculate_features


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_DIR = os.path.dirname(
    BASE_DIR
)

MODEL_DIR = os.path.join(
    PROJECT_DIR,
    "07_Models"
)


# ============================================================
# LOAD MODEL CONFIG
# ============================================================

CONFIG_FILE = os.path.join(
    MODEL_DIR,
    "final_model_config.json"
)

if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(
        f"Model config not found:\n{CONFIG_FILE}"
    )

with open(
    CONFIG_FILE,
    "r",
    encoding="utf-8"
) as f:
    config = json.load(f)


# ============================================================
# LOAD EXISTING V1 MODELS
# ============================================================

LOGISTIC_FILE = os.path.join(
    MODEL_DIR,
    config["logistic_model"]
)

RF_FILE = os.path.join(
    MODEL_DIR,
    config["random_forest_model"]
)

if not os.path.exists(LOGISTIC_FILE):
    raise FileNotFoundError(
        f"Logistic model not found:\n{LOGISTIC_FILE}"
    )

if not os.path.exists(RF_FILE):
    raise FileNotFoundError(
        f"Random Forest model not found:\n{RF_FILE}"
    )


logistic_model = joblib.load(
    LOGISTIC_FILE
)

rf_model = joblib.load(
    RF_FILE
)

THRESHOLD = float(
    config["threshold"]
)


# ============================================================
# ORIGINAL V1 MODEL FEATURES
# ============================================================

# IMPORTANT:
# The existing V1 model was trained using exactly these
# features. New river/weather/slope-context fields are NOT
# passed to this model yet.

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


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# CORS
# ============================================================

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500",
                "http://127.0.0.1:5173",
                "http://localhost:5173"
            ],
            "methods": [
                "GET",
                "POST",
                "OPTIONS"
            ],
            "allow_headers": [
                "Content-Type"
            ]
        }
    }
)


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "project": "TerraPulse SIH 2026",
        "region": "Uttarakhand",
        "status": "Backend is running",
        "model": config["model_type"],
        "model_version": "V1",
        "threshold": THRESHOLD,
        "data_mode": "PROTOTYPE_SIMULATED_CONTEXT",
        "message": (
            "Existing Uttarakhand flood model is active. "
            "River and weather values are prototype "
            "context fields and are not CWC/IMD observations."
        )
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "healthy",
        "model_loaded": True,
        "model": config["model_type"],
        "model_version": "V1",
        "threshold": THRESHOLD,
        "region": "Uttarakhand"
    })


# ============================================================
# PREDICTION ENDPOINT
# ============================================================

@app.route(
    "/predict",
    methods=["POST", "OPTIONS"]
)
def predict():

    if request.method == "OPTIONS":
        return jsonify({
            "status": "ok"
        }), 200

    try:

        # ----------------------------------------------------
        # READ JSON
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "error": "No JSON input provided"
            }), 400


        # ----------------------------------------------------
        # REQUIRED USER INPUTS
        # ----------------------------------------------------

        required_inputs = [
            "district",
            "rainfall_history",
            "soil_moisture"
        ]

        missing = [
            item
            for item in required_inputs
            if item not in data
        ]

        if missing:

            return jsonify({
                "error":
                    "Missing required inputs",
                "missing_inputs":
                    missing
            }), 400


        # ----------------------------------------------------
        # BASIC INPUT VALIDATION
        # ----------------------------------------------------

        district = str(
            data["district"]
        ).strip()

        rainfall_history = (
            data["rainfall_history"]
        )

        try:

            soil_moisture = float(
                data["soil_moisture"]
            )

        except (
            ValueError,
            TypeError
        ):

            return jsonify({
                "error":
                    "soil_moisture must be numeric"
            }), 400


        if not district:

            return jsonify({
                "error":
                    "District cannot be empty"
            }), 400


        if not isinstance(
            rainfall_history,
            list
        ):

            return jsonify({
                "error":
                    "rainfall_history must be a list of daily rainfall values"
            }), 400


        if len(rainfall_history) != 30:

            return jsonify({
                "error":
                    "Exactly 30 daily rainfall values are required",
                "received":
                    len(rainfall_history)
            }), 400


        # ----------------------------------------------------
        # RAINFALL VALIDATION
        # ----------------------------------------------------

        try:

            rainfall_history = [
                float(value)
                for value in rainfall_history
            ]

        except (
            ValueError,
            TypeError
        ):

            return jsonify({
                "error":
                    "All rainfall values must be numeric"
            }), 400


        if any(
            value < 0
            for value in rainfall_history
        ):

            return jsonify({
                "error":
                    "Rainfall values cannot be negative"
            }), 400


        # ----------------------------------------------------
        # SOIL MOISTURE VALIDATION
        # ----------------------------------------------------

        if not (
            0 <= soil_moisture <= 1
        ):

            return jsonify({
                "error":
                    "soil_moisture must be between 0 and 1"
            }), 400


        # ----------------------------------------------------
        # CALCULATE FEATURES
        # ----------------------------------------------------

        features = calculate_features(

            district=district,

            rainfall_history=
                rainfall_history,

            soil_moisture=
                soil_moisture
        )


        # ----------------------------------------------------
        # VERIFY ORIGINAL MODEL FEATURES
        # ----------------------------------------------------

        missing_model_features = [
            feature
            for feature in FEATURES
            if feature not in features
        ]

        if missing_model_features:

            return jsonify({
                "error":
                    "Feature calculation failed",
                "missing_model_features":
                    missing_model_features
            }), 500


        # ----------------------------------------------------
        # BUILD MODEL INPUT
        # ----------------------------------------------------

        input_df = pd.DataFrame(
            [features]
        )[FEATURES]


        # ----------------------------------------------------
        # LOGISTIC PROBABILITY
        # ----------------------------------------------------

        logistic_probability = float(
            logistic_model
            .predict_proba(
                input_df
            )[0][1]
        )


        # ----------------------------------------------------
        # RANDOM FOREST PROBABILITY
        # ----------------------------------------------------

        rf_probability = float(
            rf_model
            .predict_proba(
                input_df
            )[0][1]
        )


        # ----------------------------------------------------
        # ENSEMBLE
        # ----------------------------------------------------

        ensemble_probability = (
            logistic_probability
            + rf_probability
        ) / 2.0


        # ----------------------------------------------------
        # RISK LEVEL
        # ----------------------------------------------------

        if (
            ensemble_probability
            >= THRESHOLD
        ):

            risk_level = "HIGH"

            warning = (
                "Flash flood risk detected. "
                "Early warning recommended."
            )

        elif (
            ensemble_probability
            >= THRESHOLD * 0.5
        ):

            risk_level = "MODERATE"

            warning = (
                "Elevated flood risk. "
                "Continue monitoring conditions."
            )

        else:

            risk_level = "LOW"

            warning = (
                "Low predicted flash flood risk."
            )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            # ----------------------------------------------
            # PROJECT
            # ----------------------------------------------

            "project":
                "TerraPulse SIH 2026",

            "region":
                "Uttarakhand",

            "district":
                district,


            # ----------------------------------------------
            # MODEL OUTPUT
            # ----------------------------------------------

            "probability":
                round(
                    ensemble_probability,
                    4
                ),

            "probability_percent":
                round(
                    ensemble_probability * 100,
                    2
                ),

            "risk_level":
                risk_level,

            "warning":
                warning,

            "threshold":
                THRESHOLD,

            "model":
                "Ensemble",

            "model_version":
                "V1",

            "lead_target":
                "3 Days",


            # ----------------------------------------------
            # INDIVIDUAL MODEL PROBABILITIES
            # ----------------------------------------------

            "logistic_probability":
                round(
                    logistic_probability,
                    4
                ),

            "random_forest_probability":
                round(
                    rf_probability,
                    4
                ),


            # ----------------------------------------------
            # EXISTING MODEL FEATURES
            # ----------------------------------------------

            "features_used":
                {
                    key: features[key]
                    for key in FEATURES
                },


            # ----------------------------------------------
            # NEW DASHBOARD ENVIRONMENT FEATURES
            # ----------------------------------------------

            "environment": {

                "rainfall": {

                    "rainfall_1d_mm":
                        round(
                            float(
                                features[
                                    "rainfall_1d"
                                ]
                            ),
                            2
                        ),

                    "rainfall_3d_mm":
                        round(
                            float(
                                features[
                                    "rainfall_3d"
                                ]
                            ),
                            2
                        ),

                    "rainfall_7d_mm":
                        round(
                            float(
                                features[
                                    "rainfall_7d"
                                ]
                            ),
                            2
                        ),

                    "rainfall_14d_mm":
                        round(
                            float(
                                features[
                                    "rainfall_14d"
                                ]
                            ),
                            2
                        ),

                    "rainfall_30d_mm":
                        round(
                            float(
                                features[
                                    "rainfall_30d"
                                ]
                            ),
                            2
                        )
                },


                # ------------------------------------------
                # SOIL
                # ------------------------------------------

                "soil": {

                    "moisture":
                        round(
                            float(
                                features[
                                    "soil_moisture"
                                ]
                            ),
                            4
                        ),

                    "moisture_percent":
                        round(
                            float(
                                features[
                                    "soil_moisture"
                                ]
                            ) * 100,
                            2
                        )
                },


                # ------------------------------------------
                # TERRAIN
                # ------------------------------------------

                "terrain": {

                    "elevation_m":
                        round(
                            float(
                                features[
                                    "mean_elevation"
                                ]
                            ),
                            2
                        ),

                    "mean_slope_degree":
                        round(
                            float(
                                features[
                                    "mean_slope"
                                ]
                            ),
                            2
                        ),

                    "slope_risk":
                        features[
                            "slope_risk"
                        ]
                },


                # ------------------------------------------
                # RIVER
                # ------------------------------------------

                "river": {

                    "water_level_m":
                        features[
                            "river_water_level_m"
                        ],

                    "danger_level_m":
                        features[
                            "river_danger_level_m"
                        ],

                    "level_ratio_to_danger":
                        features[
                            "river_level_ratio_to_danger"
                        ],

                    "rise_rate_m_per_hr":
                        features[
                            "river_rise_rate_m_per_hr"
                        ],

                    "level_change_3h_m":
                        features[
                            "river_level_change_3h_m"
                        ],

                    "level_change_6h_m":
                        features[
                            "river_level_change_6h_m"
                        ],

                    "level_change_24h_m":
                        features[
                            "river_level_change_24h_m"
                        ]
                },


                # ------------------------------------------
                # WEATHER
                # ------------------------------------------

                "weather": {

                    "temperature_c":
                        features[
                            "temperature_c"
                        ],

                    "relative_humidity_pct":
                        features[
                            "relative_humidity_pct"
                        ],

                    "wind_speed_kmh":
                        features[
                            "wind_speed_kmh"
                        ],

                    "atmospheric_pressure_hpa":
                        features[
                            "atmospheric_pressure_hpa"
                        ],

                    "condition":
                        features[
                            "weather_condition"
                        ]
                }
            },


            # ----------------------------------------------
            # DATA TRANSPARENCY
            # ----------------------------------------------

            "data_mode":
                "PROTOTYPE_SIMULATED",

            "data_note":
                (
                    "River and weather values are synthetic "
                    "prototype inputs for software demonstration. "
                    "They are not live CWC/IMD observations."
                )
        })


    # ========================================================
    # VALUE ERROR
    # ========================================================

    except ValueError as e:

        return jsonify({
            "error": str(e)
        }), 400


    # ========================================================
    # UNEXPECTED ERROR
    # ========================================================

    except Exception as e:

        print(
            "Prediction error:",
            repr(e)
        )

        return jsonify({
            "error":
                "Prediction failed",

            "details":
                str(e)
        }), 500


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )