import os
import hashlib
import json
from collections import defaultdict

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

def get_hash(path):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"error: {e}"

# 1. Inventory ML Model
ml_model_dir = os.path.join(repo_root, "ML Model")
ml_model_inventory = []
for root, dirs, files in os.walk(ml_model_dir):
    if '__pycache__' in root:
        continue
    for f in files:
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, repo_root)
        sz = os.path.getsize(fp)
        ml_model_inventory.append({
            "path": rel,
            "filename": f,
            "size_bytes": sz,
            "size_mb": round(sz / (1024 * 1024), 3),
            "sha256": get_hash(fp)
        })

print(f"Total files in ML Model: {len(ml_model_inventory)}")

# 2. Inventory ml/
ml_dir = os.path.join(repo_root, "ml")
ml_inventory = []
for root, dirs, files in os.walk(ml_dir):
    if '__pycache__' in root:
        continue
    for f in files:
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, repo_root)
        sz = os.path.getsize(fp)
        ml_inventory.append({
            "path": rel,
            "filename": f,
            "size_bytes": sz,
            "size_mb": round(sz / (1024 * 1024), 3),
            "sha256": get_hash(fp)
        })

print(f"Total files in ml/: {len(ml_inventory)}")

# 3. Check references to ml/ modules across the repo
incoming_refs = defaultdict(list)
search_dirs = ['apps', 'scripts', 'tests', 'ml']
for sdir in search_dirs:
    dp = os.path.join(repo_root, sdir)
    for root, dirs, files in os.walk(dp):
        if any(x in root for x in ['node_modules', '.git', '__pycache__', 'scratch', '.pytest_cache']):
            continue
        for f in files:
            if f.endswith(('.py', '.json', '.yaml', '.yml', '.ts', '.tsx')):
                fp = os.path.join(root, f)
                rel_src = os.path.relpath(fp, repo_root)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                        content = fh.read()
                        for item in ml_inventory:
                            fn = item['filename']
                            if fn.endswith('.py') and fn[:-3] in content:
                                mod_stem = fn[:-3]
                                if f"ml.{mod_stem}" in content or f"from {mod_stem} import" in content or f"import {mod_stem}" in content:
                                    incoming_refs[item['path']].append(rel_src)
                            elif fn.endswith('.joblib') and fn in content:
                                incoming_refs[item['path']].append(rel_src)
                            elif fn.endswith('.json') and fn in content:
                                incoming_refs[item['path']].append(rel_src)
                except Exception:
                    pass

print("\n=== TOP INCOMING REFERENCES TO ml/ ARTIFACTS ===")
for path, refs in sorted(incoming_refs.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
    print(f"  {path} ({len(set(refs))} consumer files):")
    for r in list(set(refs))[:3]:
        print(f"     <- {r}")

# Save detailed inventory to scratch
with open(os.path.join(repo_root, "scratch", "ml_consolidation_audit.json"), "w") as f:
    json.dump({
        "ml_model_count": len(ml_model_inventory),
        "ml_count": len(ml_inventory),
        "ml_model_files": ml_model_inventory,
        "ml_files": ml_inventory,
        "incoming_refs": {k: list(set(v)) for k, v in incoming_refs.items()}
    }, f, indent=2)

print("\nFull audit written to scratch/ml_consolidation_audit.json")
