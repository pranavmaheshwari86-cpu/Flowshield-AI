import os
import re

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"
web_src = os.path.join(repo_root, "apps", "web", "src")

all_files = []
for root, dirs, files in os.walk(web_src):
    for f in files:
        if f.endswith(('.tsx', '.ts', '.css')):
            all_files.append(os.path.join(root, f))

print(f"Total TS/TSX/CSS files in apps/web/src: {len(all_files)}")

# Check for unused components
components = []
comp_dir = os.path.join(web_src, "components")
for root, dirs, files in os.walk(comp_dir):
    for f in files:
        if f.endswith(('.tsx', '.ts')):
            base = os.path.splitext(f)[0]
            components.append((base, os.path.relpath(os.path.join(root, f), web_src)))

print(f"Total components found: {len(components)}")

unused = []
for base, rel in components:
    # Skip index or types or setup
    if base in ['index', 'types']:
        continue
    # Search across all_files
    referenced = False
    for af in all_files:
        if os.path.normpath(af) == os.path.normpath(os.path.join(web_src, rel)):
            continue
        try:
            with open(af, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
                if base in content:
                    referenced = True
                    break
        except:
            pass
    if not referenced:
        unused.append((base, rel))

print(f"Potentially unreferenced components ({len(unused)}):")
for b, r in unused:
    print(f"  - {b} ({r})")
