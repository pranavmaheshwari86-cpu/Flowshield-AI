import os
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

TERRAIN_FILE = os.path.join(
    PROJECT_DIR,
    "05_Features",
    "terrain_features_uttarakhand.csv"
)


# ============================================================
# LOAD TERRAIN DATA
# ============================================================

if not os.path.exists(TERRAIN_FILE):
    raise FileNotFoundError(
        f"Terrain file not found:\n{TERRAIN_FILE}"
    )

terrain_df = pd.read_csv(TERRAIN_FILE)

if "district" not in terrain_df.columns:
    raise ValueError(
        "Terrain dataset must contain a 'district' column."
    )

DISTRICTS = (
    terrain_df["district"]
    .astype(str)
    .str.strip()
    .tolist()
)


# ============================================================
# HELPER: SLOPE RISK
# ============================================================

def calculate_slope_risk(mean_slope):
    """
    Convert numerical slope into a simple risk category.

    NOTE:
    These are prototype classification bands for dashboard
    visualization. They are not official government thresholds.
    """

    slope = float(mean_slope)

    if slope < 10:
        return "LOW"

    elif slope < 20:
        return "MODERATE"

    elif slope < 30:
        return "HIGH"

    else:
        return "VERY HIGH"


# ============================================================
# HELPER: SYNTHETIC RIVER FEATURES
# ============================================================

def calculate_prototype_river_features(
    district,
    rainfall_1d,
    rainfall_3d,
    mean_slope
):
    """
    Generate deterministic prototype river indicators for the
    dashboard.

    IMPORTANT:
    These are NOT real CWC observations.

    They are only used so the current dashboard can demonstrate
    the complete multi-source architecture before a real river
    data source is integrated.
    """

    # District-specific baseline.
    district_index = (
        DISTRICTS.index(district)
        if district in DISTRICTS
        else 0
    )

    baseline_level = (
        2.0
        + (district_index % 5) * 0.35
        + min(max(mean_slope, 0), 45) * 0.015
    )

    # Rainfall contribution.
    rainfall_effect = (
        0.012 * rainfall_1d
        + 0.004 * rainfall_3d
    )

    river_water_level = (
        baseline_level
        + rainfall_effect
    )

    # Prototype danger level.
    river_danger_level = (
        baseline_level
        + 4.5
    )

    # Avoid invalid division.
    if river_danger_level > 0:
        level_ratio = (
            river_water_level
            / river_danger_level
        )
    else:
        level_ratio = 0.0

    # Prototype rise-rate indicator.
    rise_rate = max(
        0.0,
        0.004 * rainfall_1d
        + 0.0015 * rainfall_3d
    )

    # Approximate recent change indicators.
    change_3h = rise_rate * 3
    change_6h = rise_rate * 6
    change_24h = rise_rate * 24

    return {
        "river_water_level_m": round(
            float(river_water_level),
            3
        ),
        "river_danger_level_m": round(
            float(river_danger_level),
            3
        ),
        "river_level_ratio_to_danger": round(
            float(level_ratio),
            4
        ),
        "river_rise_rate_m_per_hr": round(
            float(rise_rate),
            4
        ),
        "river_level_change_3h_m": round(
            float(change_3h),
            3
        ),
        "river_level_change_6h_m": round(
            float(change_6h),
            3
        ),
        "river_level_change_24h_m": round(
            float(change_24h),
            3
        ),
    }


# ============================================================
# HELPER: PROTOTYPE WEATHER
# ============================================================

def calculate_prototype_weather(
    rainfall_1d,
    rainfall_3d
):
    """
    Generate prototype weather indicators.

    IMPORTANT:
    These are synthetic demonstration values and are NOT
    live or historical IMD observations.
    """

    rainfall_signal = (
        rainfall_1d
        + 0.20 * rainfall_3d
    )

    # Temperature prototype.
    temperature = (
        25.0
        - min(rainfall_signal * 0.02, 8.0)
    )

    # Humidity increases during rainfall.
    humidity = (
        55.0
        + min(rainfall_signal * 0.30, 40.0)
    )

    # Wind increases with stronger rainfall conditions.
    wind_speed = (
        8.0
        + min(rainfall_signal * 0.08, 25.0)
    )

    # Pressure decreases during stronger storm conditions.
    pressure = (
        1012.0
        - min(rainfall_signal * 0.25, 40.0)
    )

    if rainfall_1d >= 80:
        condition = "Heavy Rain"

    elif rainfall_1d >= 40:
        condition = "Moderate Rain"

    elif rainfall_1d >= 10:
        condition = "Light Rain"

    elif rainfall_3d >= 30:
        condition = "Partly Cloudy"

    else:
        condition = "Clear"

    return {
        "temperature_c": round(
            float(temperature),
            1
        ),
        "relative_humidity_pct": round(
            float(
                max(
                    30.0,
                    min(
                        humidity,
                        99.0
                    )
                )
            ),
            1
        ),
        "wind_speed_kmh": round(
            float(wind_speed),
            1
        ),
        "atmospheric_pressure_hpa": round(
            float(pressure),
            1
        ),
        "weather_condition": condition,
    }


# ============================================================
# MAIN FEATURE CALCULATION
# ============================================================

def calculate_features(
    district,
    rainfall_history,
    soil_moisture
):
    """
    Calculate the complete dashboard feature payload.

    Existing ML features are preserved.
    Additional river/weather/slope indicators are returned
    for dashboard/API use.

    IMPORTANT:
    Existing V1 model consumes only the original 14 features.
    Additional prototype features are NOT yet passed into the
    existing V1 model.
    """

    district = str(district).strip()

    if district not in DISTRICTS:
        raise ValueError(
            "Invalid district. "
            f"Available districts: {DISTRICTS}"
        )

    if not isinstance(
        rainfall_history,
        list
    ):
        raise ValueError(
            "rainfall_history must be a list."
        )

    if len(rainfall_history) < 30:
        raise ValueError(
            "At least 30 daily rainfall values are required."
        )

    try:

        rainfall_history = [
            float(value)
            for value in rainfall_history
        ]

    except (ValueError, TypeError):

        raise ValueError(
            "All rainfall values must be numeric."
        )

    if any(
        value < 0
        for value in rainfall_history
    ):
        raise ValueError(
            "Rainfall values cannot be negative."
        )

    try:
        soil_moisture = float(
            soil_moisture
        )

    except (ValueError, TypeError):

        raise ValueError(
            "soil_moisture must be numeric."
        )

    if not 0 <= soil_moisture <= 1:
        raise ValueError(
            "soil_moisture must be between 0 and 1."
        )


    # ========================================================
    # RAINFALL FEATURES
    # ========================================================

    last_30 = rainfall_history[-30:]
    last_14 = rainfall_history[-14:]
    last_7 = rainfall_history[-7:]
    last_3 = rainfall_history[-3:]
    last_1 = rainfall_history[-1:]

    rainfall_1d = sum(last_1)
    rainfall_3d = sum(last_3)
    rainfall_7d = sum(last_7)
    rainfall_14d = sum(last_14)
    rainfall_30d = sum(last_30)

    rainfall_max_3d = max(last_3)
    rainfall_max_7d = max(last_7)

    rainy_days_7d = sum(
        1
        for value in last_7
        if value > 1
    )

    rainfall_1d_to_7d = (
        rainfall_1d / rainfall_7d
        if rainfall_7d > 0
        else 0.0
    )

    rainfall_3d_to_7d = (
        rainfall_3d / rainfall_7d
        if rainfall_7d > 0
        else 0.0
    )


    # ========================================================
    # TERRAIN
    # ========================================================

    terrain_rows = terrain_df[
        terrain_df["district"].astype(str).str.strip()
        == district
    ]

    if terrain_rows.empty:
        raise ValueError(
            f"Terrain data not found for district: {district}"
        )

    terrain = terrain_rows.iloc[0]

    mean_elevation = float(
        terrain["mean_elevation"]
    )

    mean_slope = float(
        terrain["mean_slope"]
    )

    slope_risk = calculate_slope_risk(
        mean_slope
    )


    # ========================================================
    # RIVER PROTOTYPE
    # ========================================================

    river_features = (
        calculate_prototype_river_features(
            district=district,
            rainfall_1d=rainfall_1d,
            rainfall_3d=rainfall_3d,
            mean_slope=mean_slope
        )
    )


    # ========================================================
    # WEATHER PROTOTYPE
    # ========================================================

    weather_features = (
        calculate_prototype_weather(
            rainfall_1d=rainfall_1d,
            rainfall_3d=rainfall_3d
        )
    )


    # ========================================================
    # EXISTING V1 MODEL FEATURES
    # ========================================================

    features = {

        # Existing V1 ML features
        "rainfall_1d":
            rainfall_1d,

        "rainfall_3d":
            rainfall_3d,

        "rainfall_7d":
            rainfall_7d,

        "rainfall_14d":
            rainfall_14d,

        "rainfall_30d":
            rainfall_30d,

        "rainfall_max_3d":
            rainfall_max_3d,

        "rainfall_max_7d":
            rainfall_max_7d,

        "rainy_days_7d":
            rainy_days_7d,

        "rainfall_1d_to_7d":
            rainfall_1d_to_7d,

        "rainfall_3d_to_7d":
            rainfall_3d_to_7d,

        "soil_moisture":
            soil_moisture,

        "mean_elevation":
            mean_elevation,

        "mean_slope":
            mean_slope,

        "district":
            district,


        # Additional dashboard features

        "slope_risk":
            slope_risk,

        **river_features,

        **weather_features,

        # Transparency flag
        "data_mode":
            "PROTOTYPE_SIMULATED",

    }


    return features


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    sample_rainfall = [
        5, 8, 12, 0, 4, 7, 15, 10, 3, 0,
        6, 9, 11, 14, 5, 2, 8, 13, 20, 18,
        4, 6, 9, 12, 15, 22, 30, 40, 55, 80
    ]

    result = calculate_features(
        district="Chamoli",
        rainfall_history=sample_rainfall,
        soil_moisture=0.32
    )

    print(
        "\n===== TerraPulse Dashboard Features ====="
    )

    for key, value in result.items():
        print(
            f"{key}: {value}"
        )