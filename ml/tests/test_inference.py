"""
ml/tests/test_inference.py
Tests for inference engine, risk level classification, and explainability.
"""

import pytest
from ml.src.models.predict import predict_flood_risk, load_inference_artifacts
from ml.src.models.explain import ModelExplainer


def test_predict_flood_risk_valid(valid_feature_dict):
    result = predict_flood_risk(valid_feature_dict, generate_explanation=True)
    assert result["status"] == "SUCCESS"
    assert result["risk_level"] in ["LOW", "WATCH", "HIGH", "CRITICAL"]
    assert 0.0 <= result["calibrated_probability"] <= 1.0
    assert "explanation" in result
    assert result["explanation"]["method"] in ["ExactLinearLogOdds", "TreeSHAP"]
    assert len(result["explanation"]["top_drivers"]) > 0


def test_predict_flood_risk_insufficient_data(corrupt_feature_dict):
    result = predict_flood_risk(corrupt_feature_dict)
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["risk_level"] == "INSUFFICIENT_DATA"
    assert result["calibrated_probability"] == 0.0


def test_model_explainer_linear(valid_feature_dict):
    model, calibrator, preprocessor, _ = load_inference_artifacts()
    explainer = ModelExplainer(model=model, preprocessor=preprocessor)
    explanation = explainer.explain_prediction(
        features_dict=valid_feature_dict,
        calibrated_probability=0.75,
        top_k=4,
    )
    assert len(explanation["top_drivers"]) <= 4
    for driver in explanation["top_drivers"]:
        assert "feature" in driver
        assert "attribution" in driver
        assert "direction" in driver
