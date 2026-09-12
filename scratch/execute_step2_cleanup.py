import os
import shutil

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

def safe_remove_file(path):
    full_path = os.path.join(repo_root, path)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        os.remove(full_path)
        print(f"[REMOVED FILE] {path} ({size/1024:.1f} KB)")
        return size
    return 0

def safe_remove_dir(path):
    full_path = os.path.join(repo_root, path)
    if os.path.exists(full_path):
        total_size = sum(os.path.getsize(os.path.join(r, f)) for r, d, fs in os.walk(full_path) for f in fs)
        count = sum(len(fs) for r, d, fs in os.walk(full_path))
        shutil.rmtree(full_path)
        print(f"[REMOVED DIR]  {path} ({count} files, {total_size/(1024*1024):.2f} MB)")
        return total_size
    return 0

print("=== STEP 2: CLEANING EPHEMERAL JUNK & DUPLICATE DATABASES ===")
total_cleaned = 0

# 1. Playwright MCP artifacts
total_cleaned += safe_remove_dir(".playwright-mcp")

# 2. Duplicate / Stale DB files
stale_dbs = [
    "flowshield.db.bak",
    "test_flowshield.db",
    "test_flowshield.db.bak",
    "test_regression.db",
    os.path.join("apps", "api", "flowshield.db"),
    os.path.join("apps", "api", "flowshield.db.bak"),
    os.path.join("apps", "api", "test_flowshield.db"),
    os.path.join("apps", "api", "test_flowshield.db.bak")
]
for db in stale_dbs:
    total_cleaned += safe_remove_file(db)

# 3. Duplicate root documentation
for doc in ["PRD.md", "TRD.md"]:
    total_cleaned += safe_remove_file(doc)

# 4. Pytest caches
total_cleaned += safe_remove_dir(".pytest_cache")
total_cleaned += safe_remove_dir(os.path.join("apps", "api", ".pytest_cache"))

print(f"\nStep 2 completed. Total cleaned: {total_cleaned / (1024*1024):.2f} MB")
