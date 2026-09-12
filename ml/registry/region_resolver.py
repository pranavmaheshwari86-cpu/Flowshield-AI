"""
ml/registry/region_resolver.py
Flowshield — Multi-Region Resolver & Configuration Manager

Maps region slugs to canonical names, configs, and validates region identifiers.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

_ML_ROOT = Path(__file__).resolve().parent.parent
_REGIONS_CONFIG_DIR = _ML_ROOT / "configs" / "regions"

# Canonical region slugs
SUPPORTED_REGIONS: List[str] = [
    "himachal_pradesh",
    "jammu_kashmir",
    "leh_ladakh",
    "sikkim",
    "arunachal_pradesh",
    "nagaland",
    "manipur",
    "mizoram",
    "meghalaya",
    "tripura",
]
ALL_REGIONS = SUPPORTED_REGIONS

# Display name mapping
REGION_DISPLAY_NAMES: Dict[str, str] = {
    "himachal_pradesh": "Himachal Pradesh",
    "jammu_kashmir": "Jammu & Kashmir",
    "leh_ladakh": "Leh & Ladakh",
    "sikkim": "Sikkim",
    "arunachal_pradesh": "Arunachal Pradesh",
    "nagaland": "Nagaland",
    "manipur": "Manipur",
    "mizoram": "Mizoram",
    "meghalaya": "Meghalaya",
    "tripura": "Tripura",
}

# State name → region slug mapping (for DB Village.state lookups)
STATE_TO_REGION: Dict[str, str] = {
    "Himachal Pradesh": "himachal_pradesh",
    "Jammu & Kashmir": "jammu_kashmir",
    "Jammu and Kashmir": "jammu_kashmir",
    "Leh": "leh_ladakh",
    "Ladakh": "leh_ladakh",
    "Leh & Ladakh": "leh_ladakh",
    "Leh and Ladakh": "leh_ladakh",
    "Sikkim": "sikkim",
    "Arunachal Pradesh": "arunachal_pradesh",
    "Nagaland": "nagaland",
    "Manipur": "manipur",
    "Mizoram": "mizoram",
    "Meghalaya": "meghalaya",
    "Tripura": "tripura",
}


def get_region_config_path(region_slug: str) -> Path:
    """Returns path to the region YAML config file."""
    return _REGIONS_CONFIG_DIR / f"{region_slug}.yaml"


class RegionResolver:
    """Resolves region identifiers to configs and validates region slugs."""

    def __init__(self, config_dir: Optional[Path] = None):
        self._config_dir = config_dir or _REGIONS_CONFIG_DIR
        self._cache: Dict[str, Dict[str, Any]] = {}

    def is_valid_region(self, region_slug: str) -> bool:
        return region_slug in SUPPORTED_REGIONS

    def resolve_from_state(self, state_name: str) -> Optional[str]:
        """Maps a Village.state value to a region slug."""
        return STATE_TO_REGION.get(state_name)

    def get_display_name(self, region_slug: str) -> str:
        return REGION_DISPLAY_NAMES.get(region_slug, region_slug.replace("_", " ").title())

    def list_regions(self) -> List[Dict[str, str]]:
        """Returns list of all supported regions with slugs and display names."""
        return [
            {"slug": slug, "display_name": self.get_display_name(slug)}
            for slug in SUPPORTED_REGIONS
        ]

    def load_config(self, region_slug: str) -> Dict[str, Any]:
        """Loads and caches region YAML config."""
        if not self.is_valid_region(region_slug):
            raise ValueError(
                f"Unknown region '{region_slug}'. "
                f"Supported: {SUPPORTED_REGIONS}"
            )

        if region_slug in self._cache:
            return self._cache[region_slug]

        config_path = self._config_dir / f"{region_slug}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(
                f"Region config not found: {config_path}. "
                f"Create ml/configs/regions/{region_slug}.yaml"
            )

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        config["_slug"] = region_slug
        config["_display_name"] = self.get_display_name(region_slug)
        self._cache[region_slug] = config
        return config

    def get_stations(self, region_slug: str) -> Dict[str, Dict[str, Any]]:
        """Returns monitoring station definitions for a region."""
        config = self.load_config(region_slug)
        return config.get("stations", {})

    def get_boundary(self, region_slug: str) -> Dict[str, float]:
        """Returns lat/lon bounding box for a region."""
        config = self.load_config(region_slug)
        return config.get("boundary", {})

    def get_training_period(self, region_slug: str) -> Dict[str, str]:
        """Returns training temporal window for a region."""
        config = self.load_config(region_slug)
        return config.get("training_period", {})

    def get_holdout_period(self, region_slug: str) -> Dict[str, str]:
        """Returns holdout temporal window for a region."""
        config = self.load_config(region_slug)
        return config.get("holdout_period", {})

    def clear_cache(self):
        self._cache.clear()


# Module-level singleton
region_resolver = RegionResolver()
