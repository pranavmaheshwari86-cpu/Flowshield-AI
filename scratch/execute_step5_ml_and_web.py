import os
import shutil

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

print("=== STEP 5: ML LEGACY ORGANIZATION & REMOVAL OF SUPERSEDED PROTOTYPES ===")
total_cleaned = 0

# 1. Remove ML Model/ directory (411.56 MB, 108 files)
ml_model_dir = os.path.join(repo_root, "ML Model")
if os.path.exists(ml_model_dir):
    sz = sum(os.path.getsize(os.path.join(r, f)) for r, d, fs in os.walk(ml_model_dir) for f in fs)
    count = sum(len(fs) for r, d, fs in os.walk(ml_model_dir))
    shutil.rmtree(ml_model_dir)
    print(f"[REMOVED DIR]  ML Model/ ({count} files, {sz / (1024*1024):.2f} MB)")
    total_cleaned += sz

# 2. Remove 9 superseded frontend components
web_components_dir = os.path.join(repo_root, "apps", "web", "src", "components")
superseded_components = [
    os.path.join("common", "DemoBanner.tsx"),
    os.path.join("dashboard", "AlertFeed.tsx"),
    os.path.join("dashboard", "HistoricalFloodView.tsx"),
    os.path.join("dashboard", "KPICards.tsx"),
    os.path.join("dashboard", "ModelOpsBadge.tsx"),
    os.path.join("dashboard", "NationalLiveWatchBanner.tsx"),
    os.path.join("dashboard", "SimulationControls.tsx"),
    os.path.join("map", "MapView.tsx"),
    os.path.join("map", "MapLegend.tsx"),
]

for sc in superseded_components:
    fp = os.path.join(web_components_dir, sc)
    if os.path.exists(fp):
        sz = os.path.getsize(fp)
        os.remove(fp)
        print(f"[REMOVED DEAD COMPONENT] apps/web/src/components/{sc} ({sz/1024:.1f} KB)")
        total_cleaned += sz

# 3. Organize legacy V1 synthetic ML files into ml/legacy_v1/
legacy_ml_dir = os.path.join(repo_root, "ml", "legacy_v1")
os.makedirs(legacy_ml_dir, exist_ok=True)

v1_files = [
    ("ml/generate_data.py", "generate_data.py"),
    ("ml/train.py", "train.py"),
    ("ml/evaluate.py", "evaluate.py"),
    ("ml/feature_schema.py", "feature_schema.py"),
    ("ml/data/synthetic_flood_data.csv", "synthetic_flood_data.csv")
]

for src_rel, dst_rel in v1_files:
    src_path = os.path.join(repo_root, src_rel.replace('/', os.sep))
    dst_path = os.path.join(legacy_ml_dir, dst_rel)
    if os.path.exists(src_path):
        shutil.move(src_path, dst_path)
        print(f"[ORGANIZED V1 LEGACY] {src_rel} -> ml/legacy_v1/{dst_rel}")

# Write a clear README.md in ml/legacy_v1/ explaining provenance
readme_content = """# FlowShield V1 Legacy Synthetic Artifacts

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
"""
with open(os.path.join(legacy_ml_dir, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme_content)

print(f"\nStep 5 completed. Total storage freed: {total_cleaned / (1024*1024):.2f} MB")
