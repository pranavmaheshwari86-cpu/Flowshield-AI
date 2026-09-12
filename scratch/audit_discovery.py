import os
import hashlib
import json
from collections import defaultdict

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

# 1. Search for references to ML Model / TerraPulse in active codebase
search_dirs = ['apps', 'ml', 'scripts', 'tests', 'data', 'config', 'docs']
targets = ['ML Model', 'TerraPulse', 'terrapulse', '01_Rainfall', '06_ML_Dataset', '07_Models', '08_Backend', '09_Dashboard', '02_Soil_Moisture', '03_Terrain']

findings = []
for sdir in search_dirs:
    dir_path = os.path.join(repo_root, sdir)
    if not os.path.exists(dir_path):
        continue
    for root, dirs, files in os.walk(dir_path):
        if any(x in root for x in ['node_modules', '.git', '__pycache__', '.pytest_cache']):
            continue
        for f in files:
            fp = os.path.join(root, f)
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()
                    for t in targets:
                        if t in content:
                            findings.append((os.path.relpath(fp, repo_root), t))
            except Exception as e:
                pass

print("=== 1. REFERENCES TO 'ML Model' / TerraPulse IN ACTIVE CODEBASE ===")
if findings:
    for f, t in sorted(set(findings)):
        print(f"  {f} -> contains '{t}'")
else:
    print("  NONE! Zero references in apps/, ml/, scripts/, tests/, data/, config/, docs/")

# 2. Check root loose files
print("\n=== 2. ROOT DIRECTORY FILES ===")
for f in sorted(os.listdir(repo_root)):
    fp = os.path.join(repo_root, f)
    if os.path.isfile(fp):
        size_kb = os.path.getsize(fp) / 1024
        print(f"  {f:<35} | {size_kb:>8.2f} KB")

# 3. Duplicate files by MD5 across repo (excluding node_modules, .git, .pytest_cache)
print("\n=== 3. DUPLICATE FILES BY MD5 HASH (size > 1KB) ===")
hash_map = defaultdict(list)
for root, dirs, files in os.walk(repo_root):
    if any(x in root for x in ['node_modules', '.git', '.pytest_cache', '__pycache__']):
        continue
    for f in files:
        fp = os.path.join(root, f)
        try:
            sz = os.path.getsize(fp)
            if sz > 1024:
                with open(fp, 'rb') as fh:
                    h = hashlib.md5(fh.read()).hexdigest()
                hash_map[(h, sz)].append(os.path.relpath(fp, repo_root))
        except:
            pass

duplicates = {k: v for k, v in hash_map.items() if len(v) > 1}
for (h, sz), paths in duplicates.items():
    print(f"  Hash {h[:8]} ({sz/1024:.1f} KB):")
    for p in paths:
        print(f"    - {p}")

# 4. Compare code-review-graph vs .code-review-graph
print("\n=== 4. code-review-graph vs .code-review-graph ===")
crg = os.path.join(repo_root, 'code-review-graph')
dot_crg = os.path.join(repo_root, '.code-review-graph')
if os.path.exists(crg) and os.path.exists(dot_crg):
    crg_files = set(os.listdir(crg))
    dot_crg_files = set(os.listdir(dot_crg))
    print(f"  code-review-graph files count: {len(crg_files)}")
    print(f"  .code-review-graph files count: {len(dot_crg_files)}")
    diff1 = crg_files - dot_crg_files
    diff2 = dot_crg_files - crg_files
    print(f"  in code-review-graph but not in .code-review-graph: {diff1}")
    print(f"  in .code-review-graph but not in code-review-graph: {diff2}")

# 5. Check graphify-out, memory, .playwright-mcp
print("\n=== 5. CHECK OTHER TOOL-GENERATED DIRS ===")
for d in ['graphify-out', 'memory', '.playwright-mcp']:
    dp = os.path.join(repo_root, d)
    if os.path.exists(dp):
        count = sum([len(files) for r, ds, files in os.walk(dp)])
        sz = sum([sum([os.path.getsize(os.path.join(r, f)) for f in files]) for r, ds, files in os.walk(dp)]) / 1024
        print(f"  {d}: {count} files, {sz:.1f} KB")

# 6. Check data directory contents
print("\n=== 6. DATA DIRECTORY TREE ===")
data_dir = os.path.join(repo_root, 'data')
for root, dirs, files in os.walk(data_dir):
    rel = os.path.relpath(root, repo_root)
    print(f"  {rel}/ ({len(files)} files)")
    for f in files:
        fp = os.path.join(root, f)
        print(f"    - {f} ({os.path.getsize(fp)/1024:.1f} KB)")

# 7. Check ml directory contents
print("\n=== 7. ML DIRECTORY BREAKDOWN ===")
ml_dir = os.path.join(repo_root, 'ml')
for root, dirs, files in os.walk(ml_dir):
    rel = os.path.relpath(root, repo_root)
    py_files = [f for f in files if f.endswith('.py')]
    other_files = [f for f in files if not f.endswith('.py')]
    if files:
        print(f"  {rel}/: {len(py_files)} py, {len(other_files)} non-py")
        for f in files:
            fp = os.path.join(root, f)
            print(f"    - {f} ({os.path.getsize(fp)/1024:.1f} KB)")

# 8. Check scripts directory contents
print("\n=== 8. SCRIPTS DIRECTORY BREAKDOWN ===")
scripts_dir = os.path.join(repo_root, 'scripts')
for f in sorted(os.listdir(scripts_dir)):
    fp = os.path.join(scripts_dir, f)
    if os.path.isfile(fp):
        print(f"    - {f} ({os.path.getsize(fp)/1024:.1f} KB)")
