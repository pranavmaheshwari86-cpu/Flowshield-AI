from pathlib import Path

import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats


# ============================================================
# TerraPulse SIH 2026
# District-Level Terrain Feature Extraction
#
# Inputs:
#   - Uttarakhand district boundaries
#   - SRTM elevation raster
#   - SRTM slope raster
#
# Outputs:
#   - 05_Features/terrain_features_uttarakhand.csv
# ============================================================


# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent

BOUNDARY_FILE = (
    PROJECT_DIR
    / "03_Terrain"
    / "Uttarakhand_Districts.geojson"
)

ELEVATION_FILE = (
    PROJECT_DIR
    / "03_Terrain"
    / "TerraPulse_SRTM_Elevation_Uttarakhand.tif"
)

SLOPE_FILE = (
    PROJECT_DIR
    / "03_Terrain"
    / "TerraPulse_SRTM_Slope_Uttarakhand.tif"
)

OUTPUT_DIR = PROJECT_DIR / "05_Features"

OUTPUT_FILE = (
    OUTPUT_DIR
    / "terrain_features_uttarakhand.csv"
)


# ------------------------------------------------------------
# EXPECTED DISTRICTS
# ------------------------------------------------------------

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
print("TERRAPULSE — DISTRICT TERRAIN FEATURE EXTRACTION")
print("=" * 80)


# ------------------------------------------------------------
# 1. CHECK INPUT FILES
# ------------------------------------------------------------

print("\n1. INPUT FILE CHECK")
print("-" * 50)

for file_path in [
    BOUNDARY_FILE,
    ELEVATION_FILE,
    SLOPE_FILE,
]:
    print(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found:\n{file_path}"
        )

    print("✓ Exists")


# ------------------------------------------------------------
# 2. LOAD DISTRICT BOUNDARIES
# ------------------------------------------------------------

print("\n2. LOADING DISTRICT BOUNDARIES")
print("-" * 50)

gdf = gpd.read_file(BOUNDARY_FILE)

print("Rows:", len(gdf))
print("CRS:", gdf.crs)

if gdf.crs is None:
    raise ValueError("Boundary CRS is missing.")

if gdf.crs.to_epsg() != 4326:
    raise ValueError(
        f"Expected EPSG:4326 but found {gdf.crs}"
    )

if "ADM2_NAME" not in gdf.columns:
    raise ValueError(
        "ADM2_NAME column not found."
    )

districts = (
    gdf["ADM2_NAME"]
    .astype(str)
    .str.strip()
)

actual_districts = set(districts)

print("Unique districts:", len(actual_districts))

if actual_districts != EXPECTED_DISTRICTS:
    missing = EXPECTED_DISTRICTS - actual_districts
    unexpected = actual_districts - EXPECTED_DISTRICTS

    print("Missing:", sorted(missing))
    print("Unexpected:", sorted(unexpected))

    raise ValueError(
        "District names do not match expected 13 districts."
    )

print("✓ All 13 expected districts found")


# ------------------------------------------------------------
# 3. CALCULATE MEAN ELEVATION
# ------------------------------------------------------------

print("\n3. CALCULATING MEAN ELEVATION")
print("-" * 50)

elevation_stats = zonal_stats(
    gdf,
    str(ELEVATION_FILE),
    stats=["mean"],
    nodata=None,
    all_touched=False,
)

elevation_values = [
    stat["mean"]
    for stat in elevation_stats
]

gdf["mean_elevation"] = elevation_values

print("✓ Mean elevation calculated")


# ------------------------------------------------------------
# 4. CALCULATE MEAN SLOPE
# ------------------------------------------------------------

print("\n4. CALCULATING MEAN SLOPE")
print("-" * 50)

slope_stats = zonal_stats(
    gdf,
    str(SLOPE_FILE),
    stats=["mean"],
    nodata=None,
    all_touched=False,
)

slope_values = [
    stat["mean"]
    for stat in slope_stats
]

gdf["mean_slope"] = slope_values

print("✓ Mean slope calculated")


# ------------------------------------------------------------
# 5. CREATE OUTPUT DATAFRAME
# ------------------------------------------------------------

print("\n5. PREPARING OUTPUT")
print("-" * 50)

terrain_df = gdf[
    [
        "ADM2_NAME",
        "mean_elevation",
        "mean_slope",
    ]
].copy()

terrain_df = terrain_df.rename(
    columns={
        "ADM2_NAME": "district"
    }
)

terrain_df["district"] = (
    terrain_df["district"]
    .astype(str)
    .str.strip()
)

# Sort alphabetically
terrain_df = terrain_df.sort_values(
    "district"
).reset_index(drop=True)


# ------------------------------------------------------------
# 6. VALIDATION
# ------------------------------------------------------------

print("\n6. OUTPUT VALIDATION")
print("-" * 50)

print("Rows:", len(terrain_df))
print("Columns:", list(terrain_df.columns))

# District count
if len(terrain_df) != 13:
    raise ValueError(
        f"Expected 13 rows, found {len(terrain_df)}"
    )

print("✓ Exactly 13 district rows")

# Duplicate check
duplicate_count = terrain_df["district"].duplicated().sum()

print("Duplicate districts:", duplicate_count)

if duplicate_count != 0:
    raise ValueError(
        "Duplicate district rows detected."
    )

print("✓ No duplicate districts")

# Missing values
missing_elevation = terrain_df["mean_elevation"].isna().sum()
missing_slope = terrain_df["mean_slope"].isna().sum()

print("Missing mean elevation:", missing_elevation)
print("Missing mean slope:", missing_slope)

if missing_elevation != 0:
    raise ValueError(
        "Missing mean elevation values detected."
    )

if missing_slope != 0:
    raise ValueError(
        "Missing mean slope values detected."
    )

print("✓ No missing terrain values")

# Finite values
if not terrain_df["mean_elevation"].apply(
    lambda x: pd.notna(x) and pd.api.types.is_number(x)
).all():
    raise ValueError(
        "Invalid elevation values detected."
    )

if not terrain_df["mean_slope"].apply(
    lambda x: pd.notna(x) and pd.api.types.is_number(x)
).all():
    raise ValueError(
        "Invalid slope values detected."
    )

print("✓ Terrain values are numeric")


# Basic physical checks
if (terrain_df["mean_elevation"] < 0).any():
    raise ValueError(
        "Negative mean elevation detected."
    )

if (terrain_df["mean_slope"] < 0).any():
    raise ValueError(
        "Negative mean slope detected."
    )

if (terrain_df["mean_slope"] > 90).any():
    raise ValueError(
        "Slope greater than 90 degrees detected."
    )

print("✓ Basic terrain range checks passed")


# ------------------------------------------------------------
# 7. DISPLAY RESULTS
# ------------------------------------------------------------

print("\n7. TERRAIN FEATURES")
print("-" * 80)

print(
    terrain_df.to_string(
        index=False,
        formatters={
            "mean_elevation": "{:.2f}".format,
            "mean_slope": "{:.2f}".format,
        },
    )
)


# ------------------------------------------------------------
# 8. SAVE OUTPUT
# ------------------------------------------------------------

print("\n8. SAVING OUTPUT")
print("-" * 50)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

terrain_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Output file:")
print(OUTPUT_FILE)

print("✓ File saved successfully")


# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("TERRAIN FEATURE EXTRACTION COMPLETE")
print("=" * 80)

print("✓ 13 districts processed")
print("✓ Mean elevation calculated")
print("✓ Mean slope calculated")
print("✓ Output validation passed")
print("✓ No source files were modified")

print("\nNext output:")
print(OUTPUT_FILE)
