"""
apps/api/app/services/providers/__init__.py
Flowshield — Data Providers Module (v2.4)
"""

from .base import DataProvider, FreshnessPolicy, LocationTarget
from .open_meteo import OpenMeteoProvider
from .open_weather import OpenWeatherProvider
from .cwc_gauge import CwcRiverGaugeProvider, VERIFIED_CWC_GAUGES
from .replay import HistoricalReplayProvider
from .ai_provider import (
    AIProvider,
    GeminiProvider,
    OpenRouterProvider,
    FallbackProvider,
    CompositeAIProvider,
    ai_provider,
)

__all__ = [
    "DataProvider",
    "FreshnessPolicy",
    "LocationTarget",
    "OpenMeteoProvider",
    "OpenWeatherProvider",
    "CwcRiverGaugeProvider",
    "VERIFIED_CWC_GAUGES",
    "HistoricalReplayProvider",
    "AIProvider",
    "GeminiProvider",
    "OpenRouterProvider",
    "FallbackProvider",
    "CompositeAIProvider",
    "ai_provider",
]
