import os
import re

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

search_targets = [
    # 9 removed components
    "DemoBanner", "AlertFeed", "HistoricalFloodView", "KPICards",
    "ModelOpsBadge", "NationalLiveWatchBanner", "SimulationControls", "MapView", "MapLegend",
    # old screenshot locations in root
    "rainfall_filter_verified.png", "no_big_circle_overview.png", "active_rain_filter_verified.png",
    "raipur_zoomed_no_circle.png", "india_map_fullpage.png", "overview_returned.png"
]

ignore_dirs = ['node_modules', '.git', '.pytest_cache', '__pycache__', 'scratch', 'dist']

broken_refs = []

for root, dirs, files in os.walk(repo_root):
    if any(ig in root for ig in ignore_dirs):
        continue
    for f in files:
        # Check source code, docs, and config
        if f.endswith(('.ts', '.tsx', '.py', '.json', '.yaml', '.yml', '.html', '.css')):
            fp = os.path.join(root, f)
            rel_path = os.path.relpath(fp, repo_root)
            # Skip documentation screenshots directory itself
            if "docs\\assets\\screenshots" in rel_path or "docs/assets/screenshots" in rel_path:
                continue
            # Skip test logs
            if ".system_generated" in rel_path:
                continue
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                    for line_idx, line in enumerate(fh):
                        for target in search_targets:
                            if target in line:
                                broken_refs.append((rel_path, line_idx + 1, target, line.strip()[:100]))
            except Exception as e:
                pass

print(f"=== BROKEN REFERENCES SCAN RESULTS ({len(broken_refs)} found) ===")
if broken_refs:
    for path, line_no, target, snippet in broken_refs:
        print(f"  {path}:{line_no} -> '{target}' | {snippet}")
else:
    print("  ZERO broken references found across all TypeScript, Python, HTML, CSS, JSON, and YAML files!")
