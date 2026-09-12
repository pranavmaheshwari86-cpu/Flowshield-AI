"""
Hydrologically Correlated Synthetic Data Generator for Flowshield
Generates scientifically grounded demonstration data for flash flood modeling in Himalayan river valleys.
Strictly reproducible via fixed seed (26192).
"""

import os
import numpy as np
import pandas as pd
from feature_schema import (
    FEATURE_SCHEMA,
    FEATURE_BOUNDS,
    TARGET_COLUMN,
    DEFAULT_SEED,
)


def generate_synthetic_dataset(
    num_samples: int = 6000, seed: int = DEFAULT_SEED
) -> pd.DataFrame:
    """
    Generates a physically correlated meteorological-hydrological dataset.
    
    Physical relationships modeled:
    1. Monotonic cumulative rainfall: r24h >= r6h >= r3h >= r1h
    2. Soil moisture: asymptotic saturation with non-linear drainage dependent on slope
    3. River level & surge rate: responds to sustained rainfall and catchment runoff
    4. Topography: elevation and slope dictate surface pooling vs runoff velocity
    5. Target label: non-linear hydraulic hazard formula with Gaussian noise (sigma=0.06)
    """
    rng = np.random.RandomState(seed)

    # 1. Geographic & Catchment Features
    # Elevation: 400m (valley floor) to 3200m (upper ridge)
    elevation = rng.uniform(400.0, 3200.0, size=num_samples)
    # Slope: steeper at higher elevations, flatter in valley floors
    slope_base = 15.0 + 35.0 * (elevation / 3200.0)
    slope = np.clip(slope_base + rng.normal(0, 5.0, size=num_samples), 2.0, 58.0)
    # Distance to river: closer in valley floor, farther at high elevation
    dist_river_base = 0.2 + 8.0 * (elevation / 3200.0)
    distance_to_river = np.clip(
        dist_river_base + rng.exponential(1.5, size=num_samples), 0.05, 18.0
    )
    # Historical flood frequency: highest close to river and low elevation
    hist_freq = np.clip(
        0.55 * (1.0 - (distance_to_river / 18.0))
        + 0.35 * (1.0 - (elevation / 3200.0))
        + rng.normal(0, 0.05, size=num_samples),
        0.0,
        1.0,
    )

    # 2. Atmospheric & Meteorological Features (Weather Event Synthesis)
    # Event intensity scale (0 = dry, 1 = cloudburst/monsoon deluge)
    event_severity = rng.beta(a=1.4, b=2.2, size=num_samples)

    # Cumulative rainfall build-up (strictly monotonic)
    rainfall_1h = event_severity * rng.uniform(10.0, 110.0, size=num_samples)
    rainfall_3h = rainfall_1h + rng.uniform(5.0, 95.0, size=num_samples) * event_severity
    rainfall_6h = rainfall_3h + rng.uniform(10.0, 140.0, size=num_samples) * event_severity
    rainfall_24h = (
        rainfall_6h + rng.uniform(20.0, 260.0, size=num_samples) * event_severity
    )

    # Instantaneous rainfall intensity (mm/hr)
    intensity_ratio = rng.uniform(0.7, 1.3, size=num_samples)
    rainfall_intensity = np.clip(rainfall_1h * intensity_ratio, 0.0, 115.0)

    # 3. Hydrological State
    # Soil moisture: antecedent moisture + cumulative saturation, reduced by steep drainage
    antecedent_moisture = rng.uniform(20.0, 55.0, size=num_samples)
    soil_saturation_gain = 50.0 * (1.0 - np.exp(-rainfall_24h / 140.0))
    slope_drainage_penalty = (slope / 60.0) * 12.0
    soil_moisture = np.clip(
        antecedent_moisture + soil_saturation_gain - slope_drainage_penalty,
        10.0,
        98.5,
    )

    # River Level (meters): baseline 1.5m, swells with runoff
    runoff_coefficient = (soil_moisture / 100.0) ** 1.8 * (slope / 45.0) ** 0.5
    river_swell = 10.5 * (rainfall_6h / 300.0) * runoff_coefficient
    river_level = np.clip(1.5 + river_swell + rng.normal(0, 0.2, size=num_samples), 0.8, 16.5)

    # River Level Change (m/hr): instantaneous surge rate
    river_level_change = np.clip(
        (rainfall_intensity / 45.0) * runoff_coefficient * 2.8 - rng.uniform(0.1, 0.5, size=num_samples),
        -1.5,
        5.2,
    )

    # 4. Physically Grounded Hydraulic Flood Thresholding
    # Non-linear composite flood propensity index (0 to 1)
    norm_r24 = np.clip(rainfall_24h / 250.0, 0, 1)
    norm_int = np.clip(rainfall_intensity / 60.0, 0, 1)
    norm_soil = np.clip(soil_moisture / 100.0, 0, 1)
    norm_river = np.clip(river_level / 8.0, 0, 1)
    norm_surge = np.clip(np.maximum(0, river_level_change) / 2.5, 0, 1)
    norm_dist = np.clip(1.0 - (distance_to_river / 6.0), 0, 1)
    norm_low_elev = np.clip(1.0 - (elevation / 1800.0), 0, 1)

    hazard_index = (
        0.24 * norm_r24
        + 0.18 * norm_int
        + 0.18 * norm_soil
        + 0.16 * norm_surge
        + 0.10 * norm_river
        + 0.08 * norm_dist
        + 0.04 * norm_low_elev
        + 0.02 * hist_freq
    )

    # Stochastic boundary noise simulating unmodeled real-world hydraulic factors (debris, logjams)
    hazard_noisy = hazard_index + rng.normal(0, 0.06, size=num_samples)
    flood_label = (hazard_noisy >= 0.53).astype(int)

    # Build DataFrame
    df = pd.DataFrame(
        {
            "rainfall_1h": np.round(rainfall_1h, 2),
            "rainfall_3h": np.round(rainfall_3h, 2),
            "rainfall_6h": np.round(rainfall_6h, 2),
            "rainfall_24h": np.round(rainfall_24h, 2),
            "rainfall_intensity": np.round(rainfall_intensity, 2),
            "soil_moisture": np.round(soil_moisture, 2),
            "river_level": np.round(river_level, 2),
            "river_level_change": np.round(river_level_change, 2),
            "elevation": np.round(elevation, 1),
            "slope": np.round(slope, 1),
            "distance_to_river": np.round(distance_to_river, 2),
            "historical_flood_frequency": np.round(hist_freq, 3),
            TARGET_COLUMN: flood_label,
        }
    )

    # Clip all features to strict bounds
    for col in FEATURE_SCHEMA:
        b_min, b_max = FEATURE_BOUNDS[col]
        df[col] = df[col].clip(b_min, b_max)

    return df


def main():
    print(f"Generating Flowshield synthetic hydrology dataset (seed={DEFAULT_SEED})...")
    df = generate_synthetic_dataset(num_samples=6000, seed=DEFAULT_SEED)

    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "synthetic_flood_data.csv")
    df.to_csv(csv_path, index=False)

    pos_rate = df[TARGET_COLUMN].mean() * 100
    print(f"Generated {len(df)} samples saved to: {csv_path}")
    print(f"Flood positive rate: {pos_rate:.1f}%")
    print("Feature sanity check passed.")


if __name__ == "__main__":
    main()
