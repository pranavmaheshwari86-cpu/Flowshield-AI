import os
import subprocess

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, cwd=repo_root, capture_output=True, text=True)
    return res.stdout.strip()

print("=== GIT TRACKED STATUS OF SUSPECT DIRECTORIES ===")
for path in [
    'apps/web/dist',
    '.playwright-mcp',
    'code-review-graph',
    '.code-review-graph',
    'graphify-out',
    'memory',
    'ML Model',
    'flowshield.db',
    'flowshield.db.bak',
    'test_flowshield.db',
    'test_flowshield.db.bak',
    'test_regression.db',
    'rainfall_filter_verified.png',
    'PRD.md',
    'TRD.md'
]:
    tracked = run_cmd(f'git ls-files "{path}"')
    lines = [l for l in tracked.split('\n') if l]
    print(f"{path:<30} -> {len(lines)} tracked files in git")

print("\n=== .gitignore CONTENTS ===")
with open(os.path.join(repo_root, '.gitignore'), 'r') as f:
    print(f.read())
