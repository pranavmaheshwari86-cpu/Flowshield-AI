"""
Generate ml/migration_manifest.json mapping all 183 files from the pre-migration audit.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = REPO_ROOT / "scratch" / "ml_consolidation_audit.json"
MANIFEST_PATH = REPO_ROOT / "ml" / "migration_manifest.json"

with open(AUDIT_PATH, "r", encoding="utf-8") as f:
    audit = json.load(f)

mappings = []

# Map ML Model files (107 files)
for item in audit["ml_model_files"]:
    old_rel = item["path"]
    sha = item["sha256"]
    fname = item["filename"]
    
    # Destination classification
    if old_rel.startswith("ML Model\\01_Rainfall"):
        new_rel = "ml/data/raw/rainfall/terrapulse/" + old_rel.replace("ML Model\\01_Rainfall\\", "").replace("\\", "/")
        category = "DATA_RAW_RAINFALL"
    elif old_rel.startswith("ML Model\\02_Soil_Moisture"):
        new_rel = "ml/data/raw/soil_moisture/terrapulse/" + old_rel.replace("ML Model\\02_Soil_Moisture\\", "").replace("\\", "/")
        category = "DATA_RAW_SOIL_MOISTURE"
    elif old_rel.startswith("ML Model\\03_Terrain"):
        new_rel = "ml/data/raw/terrain/terrapulse/" + old_rel.replace("ML Model\\03_Terrain\\", "").replace("\\", "/")
        category = "DATA_RAW_TERRAIN"
    elif old_rel.startswith("ML Model\\04_Flood_Events"):
        new_rel = "ml/data/raw/events/terrapulse_events/" + old_rel.replace("ML Model\\04_Flood_Events\\", "").replace("\\", "/")
        category = "DATA_RAW_EVENTS"
    elif old_rel.startswith("ML Model\\04_River_Level"):
        new_rel = "ml/data/raw/events/terrapulse_river_level/" + old_rel.replace("ML Model\\04_River_Level\\", "").replace("\\", "/")
        category = "DATA_RAW_RIVER_LEVEL"
    elif old_rel.startswith("ML Model\\06_ML_Dataset") and "synthetic" in fname:
        new_rel = "ml/data/synthetic/" + fname
        category = "DATA_SYNTHETIC"
    else:
        new_rel = "ml/experiments/terrapulse_uttarakhand/" + old_rel.replace("ML Model\\", "").replace("\\", "/")
        category = "EXPERIMENT_TERRAPULSE_UTTARAKHAND"

    mappings.append({
        "original_path": old_rel.replace("\\", "/"),
        "migrated_path": new_rel,
        "category": category,
        "sha256": sha,
        "size_bytes": item["size_bytes"],
        "status": "CONSOLIDATED"
    })

# Map ml/ files (76 files)
for item in audit["ml_files"]:
    old_rel = item["path"]
    sha = item["sha256"]
    fname = item["filename"]

    if "legacy_v1" in old_rel and "synthetic" in fname:
        new_rel = "ml/data/synthetic/synthetic_flood_data_v1.csv"
        category = "DATA_SYNTHETIC"
    elif "tournament" in old_rel:
        new_rel = "ml/models/candidates/" + fname
        category = "MODEL_CANDIDATE"
    elif "v2_" in fname:
        new_rel = old_rel.replace("\\", "/")
        category = "PRODUCTION_CERTIFIED_CHAMPION"
    elif "splits" in old_rel:
        new_rel = old_rel.replace("\\", "/")
        category = "DATA_SPLITS_LOCKED"
    else:
        new_rel = old_rel.replace("\\", "/")
        category = "CANONICAL_ML_MODULE"

    mappings.append({
        "original_path": old_rel.replace("\\", "/"),
        "migrated_path": new_rel,
        "category": category,
        "sha256": sha,
        "size_bytes": item["size_bytes"],
        "status": "PRESERVED_AND_INDEXED"
    })

manifest = {
    "manifest_version": "1.0.0",
    "migration_timestamp": datetime.now(timezone.utc).isoformat(),
    "total_files_audited": len(mappings),
    "source_repositories": ["ml/", "ML Model/"],
    "target_repository": "ml/",
    "invariants": {
        "catastrophe_recall_gate": ">= 0.85 (85.0%)",
        "canonical_features": 15,
        "zero_synthetic_data_in_production": True,
        "zero_breaking_changes": True
    },
    "mappings": mappings
}

with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"Generated {MANIFEST_PATH} with {len(mappings)} mapped files.")
