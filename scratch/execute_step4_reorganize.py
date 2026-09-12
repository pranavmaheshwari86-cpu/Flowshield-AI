import os
import shutil

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

print("=== STEP 4: REORGANIZE SCREENSHOTS & MIGRATION SCRIPTS ===")

# 1. Screenshots -> docs/assets/screenshots/
ss_dir = os.path.join(repo_root, "docs", "assets", "screenshots")
os.makedirs(ss_dir, exist_ok=True)

screenshots = [
    'rainfall_filter_verified.png',
    'no_big_circle_overview.png',
    'active_rain_filter_verified.png',
    'raipur_zoomed_no_circle.png',
    'india_map_fullpage.png',
    'overview_returned.png'
]

for ss in screenshots:
    src = os.path.join(repo_root, ss)
    dst = os.path.join(ss_dir, ss)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"[MOVED SCREENSHOT] {ss} -> docs/assets/screenshots/{ss}")

# 2. Migrations -> scripts/migrations/
mig_dir = os.path.join(repo_root, "scripts", "migrations")
os.makedirs(mig_dir, exist_ok=True)

migrations = [
    "apply_timeline_migration.py",
    "migrate_v2_4_landslide.py",
    "migrate_v2_4_phase5.py",
    "migrate_v2_4_prediction_schema.py",
    "migrate_v2_4_schema.py",
    "migrate_v2_4_sync_logs.py"
]

for mig in migrations:
    src = os.path.join(repo_root, "scripts", mig)
    dst = os.path.join(mig_dir, mig)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"[MOVED MIGRATION] {mig} -> scripts/migrations/{mig}")

# Create an __init__.py in scripts/migrations
with open(os.path.join(mig_dir, "__init__.py"), "w") as f:
    f.write('"""FlowShield Database Migration Utilities"""\n')

# 3. Add .gitkeep to data/user_provided/
up_dir = os.path.join(repo_root, "data", "user_provided")
os.makedirs(up_dir, exist_ok=True)
gitkeep = os.path.join(up_dir, ".gitkeep")
if not os.path.exists(gitkeep):
    with open(gitkeep, "w") as f:
        f.write("")
    print("[CREATED] data/user_provided/.gitkeep")

print("Step 4 completed.")
