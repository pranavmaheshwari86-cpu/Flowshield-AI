import os
import re

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"
api_app = os.path.join(repo_root, "apps", "api", "app")

api_files = []
for root, dirs, files in os.walk(api_app):
    if '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            api_files.append(os.path.relpath(os.path.join(root, f), api_app))

print(f"Total Python files in apps/api/app: {len(api_files)}")

# Check each file to see if it is imported anywhere in apps/api or tests/
for af in sorted(api_files):
    mod_name = os.path.splitext(af)[0].replace('\\', '.')
    file_base = os.path.splitext(os.path.basename(af))[0]
    if file_base in ['__init__', 'main']:
        continue
    
    # search across apps/api and tests/
    referenced = False
    ref_locations = []
    for sdir in [os.path.join(repo_root, 'apps', 'api'), os.path.join(repo_root, 'tests')]:
        for root, dirs, files in os.walk(sdir):
            if '__pycache__' in root or '.pytest_cache' in root:
                continue
            for f in files:
                if f.endswith('.py'):
                    fp = os.path.join(root, f)
                    if os.path.normpath(fp) == os.path.normpath(os.path.join(api_app, af)):
                        continue
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                        content = fh.read()
                        if file_base in content:
                            referenced = True
                            ref_locations.append(os.path.relpath(fp, repo_root))
                            break
            if referenced:
                break
    
    if not referenced:
        print(f"  [UNREFERENCED] {af}")
    else:
        # print first ref
        pass

print("Audit of apps/api/app complete.")
