from pathlib import Path
import geopandas as gpd

# ============================================================
# TerraPulse SIH 2026
# Validate Uttarakhand District Boundaries
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

BOUNDARY_FILE = (
    PROJECT_DIR
    / "03_Terrain"
    / "Uttarakhand_Districts.geojson"
)

EXPECTED_DISTRICTS = {
    "Almora",
    "Bageshwar",
    "Chamoli",
    "Champawat",
    "Dehra Dun",
    "Haridwar",
    "Naini Tal",
    "Pauri Garhwal",
    "Pithoragarh",
    "Rudra Prayag",
    "Tehri Garhwal",
    "Udham Singh Nagar",
    "Uttarkashi",
}

print("=" * 80)
print("TERRAPULSE — DISTRICT BOUNDARY VALIDATION")
print("=" * 80)

# ------------------------------------------------------------
# 1. File existence
# ------------------------------------------------------------

print("\n1. FILE CHECK")
print("-" * 40)

print("File:", BOUNDARY_FILE)

if not BOUNDARY_FILE.exists():
    raise FileNotFoundError(
        f"Boundary file not found:\n{BOUNDARY_FILE}"
    )

print("✓ File exists")

# ------------------------------------------------------------
# 2. Read GeoJSON
# ------------------------------------------------------------

print("\n2. READING GEOJSON")
print("-" * 40)

gdf = gpd.read_file(BOUNDARY_FILE)

print("Rows:", len(gdf))
print("Columns:", list(gdf.columns))

# ------------------------------------------------------------
# 3. CRS
# ------------------------------------------------------------

print("\n3. COORDINATE REFERENCE SYSTEM")
print("-" * 40)

print("CRS:", gdf.crs)

if gdf.crs is None:
    raise ValueError("CRS is missing.")

if gdf.crs.to_epsg() != 4326:
    print("⚠ CRS is not EPSG:4326.")
else:
    print("✓ CRS matches terrain rasters: EPSG:4326")

# ------------------------------------------------------------
# 4. District name column
# ------------------------------------------------------------

print("\n4. DISTRICT NAME FIELD")
print("-" * 40)

print("Available columns:")
for col in gdf.columns:
    print(" -", col)

if "ADM2_NAME" not in gdf.columns:
    raise ValueError(
        "ADM2_NAME column was not found in the boundary file."
    )

print("✓ ADM2_NAME column found")

# ------------------------------------------------------------
# 5. District names
# ------------------------------------------------------------

print("\n5. DISTRICT NAMES")
print("-" * 40)

districts = sorted(
    gdf["ADM2_NAME"]
    .dropna()
    .astype(str)
    .unique()
)

for i, district in enumerate(districts, start=1):
    print(f"{i:2d}. {district}")

print("\nNumber of unique districts:", len(districts))

if len(districts) == 13:
    print("✓ Exactly 13 districts found")
else:
    print("⚠ Expected 13 districts")

# ------------------------------------------------------------
# 6. Compare expected names
# ------------------------------------------------------------

print("\n6. DISTRICT NAME COMPARISON")
print("-" * 40)

actual_set = set(districts)

missing = EXPECTED_DISTRICTS - actual_set
unexpected = actual_set - EXPECTED_DISTRICTS

if not missing:
    print("✓ No expected districts are missing")
else:
    print("⚠ Missing districts:")
    for district in sorted(missing):
        print(" -", district)

if not unexpected:
    print("✓ No unexpected district names")
else:
    print("⚠ Unexpected district names:")
    for district in sorted(unexpected):
        print(" -", district)

# ------------------------------------------------------------
# 7. Duplicate district names
# ------------------------------------------------------------

print("\n7. DUPLICATE DISTRICT CHECK")
print("-" * 40)

duplicate_counts = (
    gdf["ADM2_NAME"]
    .value_counts()
)

duplicates = duplicate_counts[
    duplicate_counts > 1
]

if duplicates.empty:
    print("✓ No duplicate district names")
else:
    print("⚠ Duplicate district names found:")
    print(duplicates)

# ------------------------------------------------------------
# 8. Geometry validity
# ------------------------------------------------------------

print("\n8. GEOMETRY VALIDITY")
print("-" * 40)

invalid_count = (~gdf.geometry.is_valid).sum()
empty_count = gdf.geometry.is_empty.sum()
null_count = gdf.geometry.isna().sum()

print("Invalid geometries :", invalid_count)
print("Empty geometries   :", empty_count)
print("Null geometries    :", null_count)

if invalid_count == 0:
    print("✓ All geometries are valid")
else:
    print("⚠ Invalid geometries found")

if empty_count == 0:
    print("✓ No empty geometries")
else:
    print("⚠ Empty geometries found")

if null_count == 0:
    print("✓ No null geometries")
else:
    print("⚠ Null geometries found")

# ------------------------------------------------------------
# 9. Geometry types
# ------------------------------------------------------------

print("\n9. GEOMETRY TYPES")
print("-" * 40)

print(gdf.geometry.geom_type.value_counts())

# ------------------------------------------------------------
# 10. Spatial bounds
# ------------------------------------------------------------

print("\n10. SPATIAL BOUNDS")
print("-" * 40)

minx, miny, maxx, maxy = gdf.total_bounds

print("Left   :", minx)
print("Bottom :", miny)
print("Right  :", maxx)
print("Top    :", maxy)

# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("DISTRICT BOUNDARY VALIDATION COMPLETE")
print("=" * 80)

if (
    len(districts) == 13
    and not missing
    and not unexpected
    and duplicates.empty
    and invalid_count == 0
    and empty_count == 0
    and null_count == 0
):
    print("✓ BOUNDARY DATA PASSED BASIC VALIDATION")
else:
    print("⚠ BOUNDARY DATA NEEDS REVIEW")

print("\nNo boundary files were modified.")