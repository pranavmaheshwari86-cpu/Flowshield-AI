import os
import json

regions = sorted(os.listdir('ml/models/flood'))
print(f"Total regions in ml/models/flood: {len(regions)}")
for r in regions:
    r_dir = os.path.join('ml/models/flood', r)
    meta_path = os.path.join(r_dir, 'metadata.json')
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
    model_path = os.path.join(r_dir, 'model.joblib')
    size_kb = os.path.getsize(model_path) / 1024 if os.path.exists(model_path) else 0
    algo = meta.get("algorithm", "N/A")
    status = meta.get("production_status", "N/A")
    auc = meta.get("holdout_roc_auc", "N/A")
    rec = meta.get("holdout_recall", "N/A")
    f1 = meta.get("holdout_f1", "N/A")
    thresh = meta.get("selected_threshold", "N/A")
    print(f"{r:20} | Algo: {algo:20} | Status: {status:18} | Thresh: {str(thresh):6} | AUC: {str(auc):6} | Rec: {str(rec):6} | F1: {str(f1):6} | Size: {size_kb:6.1f} KB")
