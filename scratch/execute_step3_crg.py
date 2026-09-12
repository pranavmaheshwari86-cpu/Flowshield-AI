import os
import shutil

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

print("=== STEP 3: KNOWLEDGE GRAPH DEDUPLICATION & DOC PRESERVATION ===")

docs_audit = os.path.join(repo_root, "docs", "audit")
os.makedirs(docs_audit, exist_ok=True)

crg_dir = os.path.join(repo_root, "code-review-graph")
dot_crg_dir = os.path.join(repo_root, ".code-review-graph")

# Move valuable markdown reports to docs/audit/
for doc_file in ["code-review-findings.md", "architecture-overview.md"]:
    src = os.path.join(crg_dir, doc_file)
    dst = os.path.join(docs_audit, doc_file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"[PRESERVED DOC] {doc_file} -> docs/audit/{doc_file}")

# Remove redundant code-review-graph directory
if os.path.exists(crg_dir):
    total_size = sum(os.path.getsize(os.path.join(r, f)) for r, d, fs in os.walk(crg_dir) for f in fs)
    shutil.rmtree(crg_dir)
    print(f"[REMOVED DIR]  code-review-graph ({total_size / (1024*1024):.2f} MB)")

# Verify .code-review-graph is intact
if os.path.exists(dot_crg_dir):
    files = os.listdir(dot_crg_dir)
    print(f"[ACTIVE GRAPH] .code-review-graph preserved with {len(files)} files/folders: {files}")

print("Step 3 completed.")
