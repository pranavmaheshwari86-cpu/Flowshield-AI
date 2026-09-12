"""
ml/registry/__init__.py
Flowshield — Multi-Region Model Registry Package
"""

from .model_registry import ModelRegistry, model_registry
from .region_resolver import RegionResolver, region_resolver, SUPPORTED_REGIONS
from .feature_contract import FeatureContract, feature_contract

__all__ = [
    "ModelRegistry",
    "model_registry",
    "RegionResolver",
    "region_resolver",
    "SUPPORTED_REGIONS",
    "FeatureContract",
    "feature_contract",
]
