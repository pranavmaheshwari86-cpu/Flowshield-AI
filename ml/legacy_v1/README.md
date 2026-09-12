# FlowShield V1 Legacy Synthetic Artifacts

This directory contains the historical V1 synthetic ML pipeline files:
- `generate_data.py`: Synthetic hydrology data generator (V1 demonstration).
- `train.py`: V1 XGBoost synthetic model trainer.
- `evaluate.py`: V1 synthetic model evaluation script.
- `feature_schema.py`: Legacy 12-feature synthetic schema.
- `synthetic_flood_data.csv`: Historical synthetic demonstration dataset.

### Production Pipeline
The certified production ML pipeline is located in:
- `ml/features/feature_definitions.py`: Canonical 15-feature definitions.
- `ml/training/train_flood_model.py`: Production Calibrated Logistic Regression model.
- `ml/inference/predict.py`: Production inference engine.
- `data/real/mandi_real_hydrology_features.csv`: Authoritative ERA5-Land reanalysis dataset.
