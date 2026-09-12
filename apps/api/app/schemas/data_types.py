"""Canonical data types, freshness statuses, and capability enums for FlowShield.

Enforces zero-fabrication standards and clean separation of:
- Observed data vs NWP numerical weather forecast vs ML prediction
- Real-time telemetry vs cached official bulletins vs stale data
- Model regional support status
"""

from enum import Enum


class DataType(str, Enum):
    """Authoritative physical classification of every data point."""
    OBSERVED = "OBSERVED"              # Direct measurement from sensor/station/API
    FORECAST_NWP = "FORECAST_NWP"      # Numerical Weather Prediction (e.g., ECMWF via Open-Meteo)
    ML_PREDICTION = "ML_PREDICTION"    # Output of validated and calibrated machine learning model
    DERIVED_ESTIMATE = "DERIVED_ESTIMATE"  # Calculated via published formula (e.g., soil saturation)
    STATIC = "STATIC"                  # Static terrain/elevation/geographic database attributes
    CACHED = "CACHED"                  # Stored snapshot past its nominal freshness cycle
    UNAVAILABLE = "UNAVAILABLE"        # Genuinely missing data (never zero-filled)


class FreshnessStatus(str, Enum):
    """Data freshness lifecycle states with strict temporal definitions."""
    LIVE = "LIVE"                      # Automated sensor data < 60 mins old
    RECENT = "RECENT"                  # Sensor observation 1-3 hours old
    VERIFIED_CACHE = "VERIFIED_CACHE"  # Official CWC/WRD bulletin within validity cycle (< 24h)
    STALE = "STALE"                    # Data older than validity cycle (> 24h)
    UNAVAILABLE = "UNAVAILABLE"        # Sensor offline or provider failed


class ModelSupport(str, Enum):
    """Machine learning model support status for a specific geographic location."""
    SUPPORTED = "SUPPORTED"            # Validated model exists, trained for this specific region
    UNSUPPORTED = "UNSUPPORTED"        # No validated model for this location (never proxy other regions!)
    VALIDATION_ONLY = "VALIDATION_ONLY"  # Experimental model undergoing validation, not for operational use


class DataAvailability(str, Enum):
    """General capability availability status."""
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
