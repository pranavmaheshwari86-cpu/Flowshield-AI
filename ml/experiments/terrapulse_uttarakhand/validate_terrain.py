import numpy as np
import rasterio
from pathlib import Path

# ============================================================
# TERRAPULSE SIH 2026
# SOURCE DATA VALIDATION
# SRTM TERRAIN
#
# Files:
#   TerraPulse_SRTM_Elevation_Uttarakhand.tif
#   TerraPulse_SRTM_Slope_Uttarakhand.tif
#
# No files are modified.
# ============================================================


# ------------------------------------------------------------
# 1. PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

TERRAIN_DIR = BASE_DIR / "03_Terrain"

ELEVATION_FILE = (
    TERRAIN_DIR /
    "TerraPulse_SRTM_Elevation_Uttarakhand.tif"
)

SLOPE_FILE = (
    TERRAIN_DIR /
    "TerraPulse_SRTM_Slope_Uttarakhand.tif"
)


print("=" * 80)
print("TERRAPULSE SIH 2026")
print("SRTM TERRAIN VALIDATION")
print("=" * 80)

print("\nTerrain directory:")
print(TERRAIN_DIR)


# ------------------------------------------------------------
# 2. CHECK FILES
# ------------------------------------------------------------

if not TERRAIN_DIR.exists():

    raise FileNotFoundError(
        f"Terrain directory not found:\n{TERRAIN_DIR}"
    )


files = {
    "Elevation": ELEVATION_FILE,
    "Slope": SLOPE_FILE
}


for name, path in files.items():

    print("\n" + "-" * 80)
    print(f"{name.upper()} FILE")
    print("-" * 80)

    print(path)

    if path.exists():

        print("✓ File exists")

        size_mb = (
            path.stat().st_size
            / (1024 * 1024)
        )

        print(
            f"File size: {size_mb:.2f} MB"
        )

    else:

        print("❌ FILE NOT FOUND")


# ------------------------------------------------------------
# 3. FUNCTION TO VALIDATE RASTER
# ------------------------------------------------------------

def validate_raster(
    name,
    raster_path
):

    print("\n" + "#" * 80)
    print(f"VALIDATING: {name.upper()}")
    print("#" * 80)

    if not raster_path.exists():

        print(
            f"❌ Cannot validate missing file:\n"
            f"{raster_path}"
        )

        return


    # --------------------------------------------------------
    # Open raster
    # --------------------------------------------------------

    try:

        with rasterio.open(raster_path) as src:

            print("\n1. BASIC RASTER INFORMATION")
            print("-" * 40)

            print(
                f"Driver       : {src.driver}"
            )

            print(
                f"Raster width : {src.width}"
            )

            print(
                f"Raster height: {src.height}"
            )

            print(
                f"Band count   : {src.count}"
            )

            print(
                f"Data type    : {src.dtypes}"
            )


            # ------------------------------------------------
            # CRS
            # ------------------------------------------------

            print("\n2. COORDINATE REFERENCE SYSTEM")
            print("-" * 40)

            print(
                f"CRS: {src.crs}"
            )


            # ------------------------------------------------
            # Resolution
            # ------------------------------------------------

            print("\n3. RESOLUTION")
            print("-" * 40)

            print(
                f"X resolution: {src.res[0]}"
            )

            print(
                f"Y resolution: {src.res[1]}"
            )


            # ------------------------------------------------
            # Bounds
            # ------------------------------------------------

            print("\n4. SPATIAL BOUNDS")
            print("-" * 40)

            print(
                f"Left   : {src.bounds.left}"
            )

            print(
                f"Bottom : {src.bounds.bottom}"
            )

            print(
                f"Right  : {src.bounds.right}"
            )

            print(
                f"Top    : {src.bounds.top}"
            )


            # ------------------------------------------------
            # Transform
            # ------------------------------------------------

            print("\n5. AFFINE TRANSFORM")
            print("-" * 40)

            print(src.transform)


            # ------------------------------------------------
            # NoData
            # ------------------------------------------------

            print("\n6. NODATA")
            print("-" * 40)

            print(
                f"NoData value: {src.nodata}"
            )


            # ------------------------------------------------
            # Read first band
            # ------------------------------------------------

            data = src.read(
                1,
                masked=True
            )


            print("\n7. DATA ARRAY")
            print("-" * 40)

            print(
                f"Array shape: {data.shape}"
            )

            print(
                f"Masked pixels: "
                f"{np.ma.count_masked(data)}"
            )


            # ------------------------------------------------
            # Statistics
            # ------------------------------------------------

            valid_values = data.compressed()


            if len(valid_values) == 0:

                print(
                    "❌ No valid raster pixels found."
                )

                return


            print("\n8. RASTER VALUE STATISTICS")
            print("-" * 40)

            print(
                f"Valid pixels: "
                f"{len(valid_values):,}"
            )

            print(
                f"Minimum: "
                f"{valid_values.min():.4f}"
            )

            print(
                f"Maximum: "
                f"{valid_values.max():.4f}"
            )

            print(
                f"Mean: "
                f"{valid_values.mean():.4f}"
            )

            print(
                f"Median: "
                f"{np.median(valid_values):.4f}"
            )

            print(
                f"Standard deviation: "
                f"{valid_values.std():.4f}"
            )


            # ------------------------------------------------
            # Infinite / NaN check
            # ------------------------------------------------

            finite_values = valid_values[
                np.isfinite(valid_values)
            ]

            invalid_numeric = (
                len(valid_values)
                - len(finite_values)
            )

            print(
                f"\nNon-finite valid pixels: "
                f"{invalid_numeric}"
            )

            # ------------------------------------------------
            # Basic interpretation
            # ------------------------------------------------

            print("\n9. BASIC INTERPRETATION")
            print("-" * 40)

            if name.lower() == "elevation":

                print(
                    "Raster interpreted as elevation."
                )

                print(
                    "Expected unit is generally "
                    "metres for SRTM elevation."
                )

                if valid_values.min() < -100:

                    print(
                        "⚠ Very low elevation values "
                        "detected — inspect further."
                    )

                else:
                    print(
                        "✓ Elevation range does not "
                        "show an obvious invalid extreme."
                    )

            elif name.lower() == "slope":

                print(
                    "Raster interpreted as slope."
                )

                print(
                    "Slope should normally be "
                    "non-negative."
                )

                negative_count = (
                    valid_values < 0
                ).sum()

                print(
                    f"Negative slope pixels: "
                    f"{negative_count:,}"
                )
                if negative_count == 0:

                    print(
                        "✓ No negative slope values."
                    )
                else:
                    print(
                        "⚠ Negative slope values detected."
                    )
            print("\n✓ Raster opened and inspected successfully.")

    except Exception as e:

        print(
            f"\n❌ ERROR while reading {name}:"
        )
        print(e)


# ------------------------------------------------------------
# 4. VALIDATE ELEVATION
# ------------------------------------------------------------

validate_raster("Elevation",ELEVATION_FILE)

# 5. VALIDATE SLOPE

validate_raster(
    "Slope",
    SLOPE_FILE
)

# 6. FINAL MESSAGE

print("\n" + "=" * 80)
print("TERRAIN VALIDATION COMPLETE")
print("=" * 80)

print("\nIMPORTANT:")

print("No terrain files were modified.")

print(
    "District-level terrain statistics will be "
    "calculated only after this validation."
)