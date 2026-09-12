"""
ml/src/models/__init__.py
Flowshield — Core Machine Learning Models Package
"""

from .factory import create_model, ModelFactory
from .train import train_production_champion
from .calibrate import calibrate_model
from .explain import ModelExplainer, generate_explanations
from .predict import predict_flood_risk, load_inference_artifacts, get_explainer
from .registry import generate_manifest
from .retrain import RetrainingPipeline

__all__ = [
    "create_model",
    "ModelFactory",
    "train_production_champion",
    "calibrate_model",
    "ModelExplainer",
    "generate_explanations",
    "predict_flood_risk",
    "load_inference_artifacts",
    "get_explainer",
    "generate_manifest",
    "RetrainingPipeline",
]
