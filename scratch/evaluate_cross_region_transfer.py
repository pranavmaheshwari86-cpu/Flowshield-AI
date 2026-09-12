import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import roc_auc_score, average_precision_score, recall_score, precision_score, f1_score, brier_score_loss
from ml.features.feature_definitions import CANONICAL_FEATURE_NAMES
from ml.inference.predict import load_inference_artifacts

REPO_ROOT = Path(__file__).resolve().parent.parent

# Load Production model & calibrator
model, calibrator, preprocessor, pipeline_info = load_inference_artifacts()
tau = pipeline_info.get("operational_threshold", 0.08)

cross_region_results = {}

for slug in ["jammu_kashmir", "sikkim", "arunachal_pradesh", "meghalaya", "leh_ladakh"]:
    p = REPO_ROOT / "ml" / "data" / "processed" / slug / f"{slug}_processed_dataset.csv"
    if not p.exists():
        continue
    df = pd.read_csv(p)
    y_true = df["flood_occurred"].values
    if len(np.unique(y_true)) < 2:
        continue
    
    X_feat = df[CANONICAL_FEATURE_NAMES]
    if hasattr(model, "named_steps"):
        raw_probs = model.predict_proba(X_feat)[:, 1]
    else:
        X_scaled = preprocessor.transform(X_feat)
        raw_probs = model.predict_proba(X_scaled)[:, 1]
        
    if calibrator is not None:
        est = getattr(calibrator, "estimator", None)
        if hasattr(est, "estimator"):
            est = est.estimator
        if hasattr(est, "named_steps"):
            probs = calibrator.predict_proba(X_feat)[:, 1]
        else:
            X_scaled = preprocessor.transform(X_feat)
            probs = calibrator.predict_proba(X_scaled)[:, 1]
    else:
        probs = raw_probs
        
    preds = (probs >= tau).astype(int)
    
    roc = float(roc_auc_score(y_true, probs))
    pr = float(average_precision_score(y_true, probs))
    rec = float(recall_score(y_true, preds, zero_division=0))
    prec = float(precision_score(y_true, preds, zero_division=0))
    f1 = float(f1_score(y_true, preds, zero_division=0))
    brier = float(brier_score_loss(y_true, probs))
    
    cross_region_results[slug] = {
        "total_samples": len(df),
        "flood_hours": int(np.sum(y_true)),
        "prevalence_pct": round(float(np.mean(y_true) * 100), 2),
        "roc_auc": round(roc, 4),
        "pr_auc": round(pr, 4),
        "recall_at_tau": round(rec, 4),
        "precision_at_tau": round(prec, 4),
        "f1_at_tau": round(f1, 4),
        "brier": round(brier, 4),
    }

print("Zero-Shot Cross-Region Transfer of Himachal Champion Model:")
print(json.dumps(cross_region_results, indent=2))

with open(REPO_ROOT / "scratch" / "cross_region_transfer_results.json", "w") as f:
    json.dump(cross_region_results, f, indent=2)
