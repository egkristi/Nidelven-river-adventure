"""
Kartverket DEM importer for Nidelven River Adventure.
Downloads real elevation data from Kartverket Høydedata API.
"""

import json
import math
import time
from pathlib import Path

import requests

# Kartverket WCS endpoints
KARTVERKET_WCS_URL = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm10"
KARTVERKET_WCS_1M = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm1"

# Nidelven river bounding box (approximate)
# Format: (min_lon, min_lat, max_lon, max_lat) in WGS84
NIDELVEN_BBOX = {
    "full": (8.2, 58.3, 8.9, 58.9),  # Full river
    "amli": (8.4, 58.7, 8.6, 58.8),  # Åmli area (test)
}


def download_dem_kartverket(
    bbox: tuple[float, float, float, float],
    output_path: Path,
    resolution: int = 10,  # 10 for DTM10, 1 for DTM1
    max_retries: int = 3,
) -> Path | None:
    """
    Download DEM from Kartverket WCS service.

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat) in WGS84
        output_path: Where to save the GeoTIFF
        resolution: 10 for 10m or 1 for 1m resolution
        max_retries: Number of retries on failure

    Returns:
        Path to downloaded file, or None if failed
    """
    min_lon, min_lat, max_lon, max_lat = bbox

    # Calculate grid size
    # At latitude ~58.6°N, 1° lon ≈ 32km, 1° lat ≈ 111km
    width_km = (max_lon - min_lon) * 32000 * math.cos(math.radians((min_lat + max_lat) / 2))
    height_km = (max_lat - min_lat) * 111000

    width_px = int(width_km / resolution)
    height_px = int(height_km / resolution)

    # Cap at reasonable size
    max_size = 4096
    if width_px > max_size or height_px > max_size:
        scale = max(width_px, height_px) / max_size
        width_px = int(width_px / scale)
        height_px = int(height_px / scale)
        print(f"  Resizing to {width_px}x{height_px} for download")

    # WCS GetCoverage request
    coverage_id = f"dtm{resolution}"

    params = {
        "SERVICE": "WCS",
        "REQUEST": "GetCoverage",
        "VERSION": "2.0.1",
        "COVERAGEID": coverage_id,
        "SUBSET": [f"x({min_lon},{max_lon})", f"y({min_lat},{max_lat})"],
        "FORMAT": "image/tiff",
        "OUTSIZE": f"{width_px},{height_px}",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    url = KARTVERKET_WCS_1M if resolution == 1 else KARTVERKET_WCS_URL

    for attempt in range(max_retries):
        try:
            print(f"  Downloading DEM (attempt {attempt + 1}/{max_retries})...")
            response = requests.get(url, params=params, timeout=120, stream=True)

            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                file_size = output_path.stat().st_size
                print(f"  ✓ Downloaded: {file_size / 1024 / 1024:.1f} MB")
                print(f"  ✓ Resolution: {resolution}m")
                print(f"  ✓ Size: {width_px}x{height_px}")
                return output_path
            else:
                print(f"  ✗ HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

        except Exception as e:
            print(f"  ✗ Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)

    return None


def convert_to_unity_raw(
    geotiff_path: Path, output_path: Path, height_scale: float = 1000.0
) -> bool:
    """
    Convert GeoTIFF DEM to Unity RAW format (16-bit grayscale).

    Args:
        geotiff_path: Path to input GeoTIFF
        output_path: Path to output RAW file
        height_scale: Maximum height in meters for normalization

    Returns:
        True if successful
    """
    try:
        import numpy as np
        from osgeo import gdal

        # Open GeoTIFF
        ds = gdal.Open(str(geotiff_path))
        if ds is None:
            print("  ✗ Failed to open GeoTIFF")
            return False

        # Read elevation data
        band = ds.GetRasterBand(1)
        data = band.ReadAsArray()

        # Get stats
        min_val = band.GetMinimum()
        max_val = band.GetMaximum()

        if min_val is None or max_val is None:
            min_val, max_val, _, _ = band.GetStatistics(True, True)

        print(f"  Elevation range: {min_val:.1f}m - {max_val:.1f}m")

        # Normalize to 16-bit (0-65535)
        # Unity expects 16-bit raw files
        normalized = ((data - min_val) / (max_val - min_val) * 65535).astype(np.uint16)

        # Write raw file (big-endian for Unity)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        normalized.byteswap().tofile(output_path)

        # Save metadata
        meta_path = output_path.with_suffix(".json")
        metadata = {
            "source": str(geotiff_path),
            "width": ds.RasterXSize,
            "height": ds.RasterYSize,
            "elevation_min": float(min_val),
            "elevation_max": float(max_val),
            "height_scale": height_scale,
            "depth": 16,
            "byte_order": "big_endian",
        }

        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"  ✓ Converted to Unity RAW: {output_path}")
        print(f"  ✓ Metadata saved: {meta_path}")

        ds = None
        return True

    except ImportError:
        print("  ✗ GDAL not available. Install with: pip install GDAL")
        return False
    except Exception as e:
        print(f"  ✗ Conversion error: {e}")
        return False


def import_nidelven_dem(
    area: str = "full", resolution: int = 10, output_dir: Path | None = None
) -> Path | None:
    """
    Complete pipeline: Download and convert DEM for Nidelven.

    Args:
        area: "full" for whole river or "amli" for test area
        resolution: 10 for 10m or 1 for 1m
        output_dir: Where to save files

    Returns:
        Path to Unity RAW file, or None if failed
    """

    if output_dir is None:
        output_dir = Path(__file__).parent / "data" / "dem"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bbox = NIDELVEN_BBOX.get(area, NIDELVEN_BBOX["amli"])

    print("=" * 60)
    print("Kartverket DEM Import - Nidelven River")
    print("=" * 60)
    print(f"Area: {area}")
    print(f"Resolution: {resolution}m")
    print(f"BBox: {bbox}")
    print()

    # Download GeoTIFF
    geotiff_path = output_dir / f"nidelven_{area}_{resolution}m.tif"

    if geotiff_path.exists():
        print(f"Using existing: {geotiff_path}")
    else:
        print("Step 1: Downloading from Kartverket...")
        result = download_dem_kartverket(bbox, geotiff_path, resolution)
        if result is None:
            print("\n✗ Download failed")
            return None

    # Convert to Unity RAW
    print("\nStep 2: Converting to Unity RAW...")
    raw_path = output_dir / f"nidelven_{area}_{resolution}m.raw"

    if convert_to_unity_raw(geotiff_path, raw_path):
        print("\n" + "=" * 60)
        print("✓ Import complete!")
        print("=" * 60)
        print(f"GeoTIFF: {geotiff_path}")
        print(f"Unity RAW: {raw_path}")
        print()
        print("Import into Unity:")
        print("  1. Copy .raw file to Assets/StreamingAssets/")
        print("  2. Set TerrainGenerator.demFilePath")
        print("  3. Disable useSyntheticFallback")
        return raw_path
    else:
        print("\n✗ Conversion failed")
        return None


if __name__ == "__main__":
    import sys

    area = sys.argv[1] if len(sys.argv) > 1 else "amli"
    resolution = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    result = import_nidelven_dem(area, resolution)
    sys.exit(0 if result else 1)
