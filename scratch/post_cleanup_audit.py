import os

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"
dir_summary = {}

for item in sorted(os.listdir(repo_root)):
    item_path = os.path.join(repo_root, item)
    if os.path.isdir(item_path):
        count = 0
        total_size = 0
        for root, dirs, files in os.walk(item_path):
            if 'node_modules' in root or '.git' in root or 'dist' in root or '.pytest_cache' in root:
                continue
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(fp)
                    count += 1
                except:
                    pass
        dir_summary[item] = (count, total_size)
    else:
        try:
            sz = os.path.getsize(item_path)
            dir_summary[item] = (1, sz)
        except:
            pass

print(f"=== POST-CLEANUP DIRECTORY & ROOT FILE SUMMARY (excluding .git, node_modules, dist) ===")
total_all_files = 0
total_all_size = 0
for k, v in sorted(dir_summary.items(), key=lambda x: x[1][1], reverse=True):
    sz_mb = v[1] / (1024 * 1024)
    total_all_files += v[0]
    total_all_size += v[1]
    print(f"{k:<35} | {v[0]:>5} files | {sz_mb:>8.2f} MB")

print("-" * 65)
print(f"TOTAL REPOSITORY CONTENT: {total_all_files} files | {total_all_size / (1024*1024):.2f} MB")
