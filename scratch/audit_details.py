import os
import subprocess

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

# 1. Screenshot references
screenshots = [
    'rainfall_filter_verified.png',
    'no_big_circle_overview.png',
    'active_rain_filter_verified.png',
    'raipur_zoomed_no_circle.png',
    'india_map_fullpage.png',
    'overview_returned.png'
]

refs = {s: [] for s in screenshots}
for root, dirs, files in os.walk(repo_root):
    if any(x in root for x in ['node_modules', '.git', '.pytest_cache', '__pycache__', 'scratch']):
        continue
    for f in files:
        fp = os.path.join(root, f)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
                for s in screenshots:
                    if s in content:
                        refs[s].append(os.path.relpath(fp, repo_root))
        except:
            pass

print("=== 1. SCREENSHOT REFERENCES ===")
for s, r in refs.items():
    print(f"  {s}: {r if r else 'NO REFERENCES IN CODE OR DOCS'}")

# 2. Check root database and backup files references
db_files = [
    'flowshield.db',
    'flowshield.db.bak',
    'test_flowshield.db',
    'test_flowshield.db.bak',
    'test_regression.db'
]
db_refs = {db: [] for db in db_files}
for root, dirs, files in os.walk(repo_root):
    if any(x in root for x in ['node_modules', '.git', '.pytest_cache', '__pycache__', 'scratch']):
        continue
    for f in files:
        fp = os.path.join(root, f)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
                for db in db_files:
                    if db in content:
                        db_refs[db].append(os.path.relpath(fp, repo_root))
        except:
            pass

print("\n=== 2. DATABASE / BACKUP FILE REFERENCES ===")
for db, r in db_refs.items():
    print(f"  {db}: {r}")

# 3. Check PRD.md and TRD.md diff between root and docs/
print("\n=== 3. PRD.md & TRD.md COMPARISON ===")
for doc in ['PRD.md', 'TRD.md']:
    p_root = os.path.join(repo_root, doc)
    p_docs = os.path.join(repo_root, 'docs', doc)
    if os.path.exists(p_root) and os.path.exists(p_docs):
        with open(p_root, 'rb') as f1, open(p_docs, 'rb') as f2:
            match = f1.read() == f2.read()
        print(f"  {doc} in root vs docs/{doc}: {'EXACT IDENTICAL MATCH' if match else 'DIFFERENT'}")

# 4. Check .playwright-mcp contents
print("\n=== 4. .playwright-mcp DETAILS ===")
pw_dir = os.path.join(repo_root, '.playwright-mcp')
if os.path.exists(pw_dir):
    exts = {}
    for f in os.listdir(pw_dir):
        ext = os.path.splitext(f)[1]
        exts[ext] = exts.get(ext, 0) + 1
    print(f"  Files by extension in .playwright-mcp: {exts}")

# 5. Check ml/ legacy files
print("\n=== 5. ML V1 LEGACY FILES AUDIT ===")
for f in ['evaluate.py', 'feature_schema.py', 'generate_data.py', 'train.py']:
    fp = os.path.join(repo_root, 'ml', f)
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8') as fh:
            lines = [fh.readline() for _ in range(10)]
            print(f"  ml/{f}: first 3 lines:")
            for l in lines[:3]:
                print(f"    {l.strip()}")

# 6. Check tests breakdown
print("\n=== 6. TESTS BREAKDOWN ===")
for tdir in ['tests', r'apps\api\tests']:
    tp = os.path.join(repo_root, tdir)
    if os.path.exists(tp):
        files = os.listdir(tp)
        print(f"  {tdir}/ ({len(files)} items):")
        for f in files:
            print(f"    - {f}")
