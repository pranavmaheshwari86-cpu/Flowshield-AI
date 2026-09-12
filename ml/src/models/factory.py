"""
ml/src/models/factory.py
Flowshield — Model Architecture Factory
"""

from typing import Any, Dict
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


def create_model(model_type: str = "logistic_regression", **kwargs) -> Any:
    """Instantiates model with specified hyperparameters."""
    m_type = model_type.lower()
    if m_type in ["logistic_regression", "lr", "champion"]:
        params = {
            "C": 0.01,
            "solver": "lbfgs",
            "max_iter": 1000,
            "class_weight": "balanced",
            "random_state": 26192,
        }
        params.update(kwargs)
        return LogisticRegression(**params)
        
    elif m_type in ["random_forest", "rf"]:
        params = {
            "n_estimators": 100,
            "max_depth": 6,
            "min_samples_leaf": 20,
            "class_weight": "balanced",
            "random_state": 26192,
            "n_jobs": -1,
        }
        params.update(kwargs)
        return RandomForestClassifier(**params)
        
    elif m_type in ["xgboost", "xgb"]:
        if not HAS_XGBOOST:
            raise ImportError("XGBoost is not installed.")
        params = {
            "n_estimators": 100,
            "max_depth": 4,
            "learning_rate": 0.05,
            "scale_pos_weight": 23.35,
            "subsample": 0.8,
            "random_state": 26192,
            "eval_metric": "logloss",
        }
        params.update(kwargs)
        return XGBClassifier(**params)
    else:
        raise ValueError(f"Unknown model type: {model_type}")


class ModelFactory:
    """Factory interface for instantiating model architectures."""
    create = staticmethod(create_model)
    create_model = staticmethod(create_model)

