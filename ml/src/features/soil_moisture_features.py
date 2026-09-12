"""
ml/src/features/soil_moisture_features.py
Flowshield — Soil Moisture Saturation Calculations
"""

from typing import Dict, Any


def calculate_soil_saturation(volumetric_moisture: float, field_capacity: float = 0.45) -> float:
    """
    Converts volumetric soil moisture (m^3/m^3) to a saturation percentage
    relative to typical Himalayan soil field capacity (~0.45 m^3/m^3).
    """
    if field_capacity <= 0:
        return 0.0
    pct = (volumetric_moisture / field_capacity) * 100.0
    return max(0.0, min(100.0, round(pct, 2)))
