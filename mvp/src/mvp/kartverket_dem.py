"""
Kartverket DTM 1m downloader for Nidelven River Adventure.

Downloads high-resolution (1m) LiDAR DEM data from Kartverket's
høydedata.no WCS service. Falls back to Copernicus 30m if unavailable.

API: https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833
License: CC BY 4.0 / NLOD (Norwegian public geodata)
"""

import time
from io import BytesIO
from pathlib import Path

import numpy as np
import requests

from .dem_downloader import NIDELVEN_BBOX

# Kartverket WCS endpoint for DTM 1m (EPSG:25833 — UTM zone 33N)
KARTVERKET_WCS_URL = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833"

# UTM33N approximate conversion for Nidelven area (58.5°N, 8.6°E)
# More accurate than simple formulas; derived from proj4 for this locality
UTM33_ORIGIN_E = 452000  # Easting for ~8.45°E
UTM33_ORIGIN_N = 6472000  # Northing for ~58.38°N

# User-Agent for API requests (required by Kartverket terms)
USER_AGENT = "NidelvenRiverAdventure/0.1 (github.com/egkristi/Nidelven-river-adventure)"


def wgs84_to_utm33n(lon: float, lat: float) -> tuple[float, float]:
    """
    Convert WGS84 (lon, lat) to approximate UTM zone 33N (EPSG:25833).

    Uses a simplified conversion accurate to ~1m for the Nidelven area.
    For production use, consider pyproj for exact transformation.
    """
    import math

    # WGS84 ellipsoid parameters
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2 * f - f * f

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lon0_rad = math.radians(15.0)  # Central meridian for UTM zone 33

    n = a / math.sqrt(1 - e2 * math.sin(lat_rad) ** 2)
    t = math.tan(lat_rad)
    c = (e2 / (1 - e2)) * math.cos(lat_rad) ** 2
    aa = (lon_rad - lon0_rad) * math.cos(lat_rad)

    # Meridian arc length
    e4 = e2 * e2
    e6 = e4 * e2
    m = a * (
        (1 - e2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * lat_rad
        - (3 * e2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * math.sin(2 * lat_rad)
        + (15 * e4 / 256 + 45 * e6 / 1024) * math.sin(4 * lat_rad)
        - (35 * e6 / 3072) * math.sin(6 * lat_rad)
    )

    # UTM coordinates
    easting = 500000 + 0.9996 * n * (
        aa + (1 - t**2 + c) * aa**3 / 6 + (5 - 18 * t**2 + t**4) * aa**5 / 120
    )
    northing = 0.9996 * (m + n * t * (aa**2 / 2 + (5 - t**2 + 9 * c + 4 * c**2) * aa**4 / 24))

    return easting, northing


def download_kartverket_dtm(
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX,
    output_path: Path | None = None,
    resolution: float = 1.0,
    max_size: int = 2048,
    max_retries: int = 3,
) -> np.ndarray | None:
    """
    Download 1m DTM from Kartverket WCS service.

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat) in WGS84
        output_path: Optional path to save the result as GeoTIFF
        resolution: Desired resolution in meters (default 1.0)
        max_size: Maximum dimension in pixels (WCS limit)
        max_retries: Number of retries on failure

    Returns:
        numpy array of elevation data, or None if download failed
    """
    min_lon, min_lat, max_lon, max_lat = bbox

    # Convert WGS84 bbox to UTM33N
    easting_min, northing_min = wgs84_to_utm33n(min_lon, min_lat)
    easting_max, northing_max = wgs84_to_utm33n(max_lon, max_lat)

    # Calculate pixel dimensions
    width_m = easting_max - easting_min
    height_m = northing_max - northing_min
    width_px = int(width_m / resolution)
    height_px = int(height_m / resolution)

    # Clamp to max_size (WCS services often limit response size)
    if width_px > max_size or height_px > max_size:
        scale = max_size / max(width_px, height_px)
        width_px = int(width_px * scale)
        height_px = int(height_px * scale)
        effective_res = width_m / width_px
        print(f"  Note: Clamping to {max_size}px (effective resolution: {effective_res:.1f}m)")
    else:
        effective_res = resolution

    print("  Requesting Kartverket DTM 1m...")
    print(f"  Area: {width_m:.0f}m x {height_m:.0f}m")
    print(f"  Pixels: {width_px} x {height_px} ({effective_res:.1f}m/px)")
    print(f"  UTM33N: E{easting_min:.0f}-{easting_max:.0f}, N{northing_min:.0f}-{northing_max:.0f}")

    # WCS 2.0.1 GetCoverage request
    params = {
        "service": "WCS",
        "version": "2.0.1",
        "request": "GetCoverage",
        "CoverageId": "nhm_dtm_topo_25833",
        "format": "image/tiff",
        "subset": [
            f"x({easting_min:.1f},{easting_max:.1f})",
            f"y({northing_min:.1f},{northing_max:.1f})",
        ],
        "scalesize": f"x({width_px}),y({height_px})",
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(
                KARTVERKET_WCS_URL,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=120,
            )

            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "tiff" in content_type or "image" in content_type:
                    return _parse_geotiff_response(response.content, output_path)
                elif "xml" in content_type or "exception" in content_type.lower():
                    # WCS exception response
                    print(f"  ✗ WCS exception: {response.text[:200]}")
                    return None
                else:
                    # Try parsing as TIFF anyway
                    return _parse_geotiff_response(response.content, output_path)
            else:
                print(f"  ✗ HTTP {response.status_code} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

        except requests.Timeout:
            print(f"  ✗ Timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
        except requests.RequestException as e:
            print(f"  ✗ Network error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)

    print("  ✗ Failed to download Kartverket DTM after all retries")
    return None


def _parse_geotiff_response(data: bytes, output_path: Path | None = None) -> np.ndarray | None:
    """Parse GeoTIFF response bytes into numpy array."""
    try:
        import rasterio

        with rasterio.open(BytesIO(data)) as src:
            dem = src.read(1).astype(np.float32)

            # Handle nodata values
            nodata = src.nodata
            if nodata is not None:
                mask = dem == nodata
                if mask.any():
                    from scipy.ndimage import distance_transform_edt

                    indices = distance_transform_edt(
                        mask, return_distances=False, return_indices=True
                    )
                    dem[mask] = dem[tuple(indices[:, mask])]

            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(data)
                print(f"  ✓ Saved: {output_path}")

        print(f"  ✓ Kartverket DTM: {dem.shape[1]}x{dem.shape[0]} px")
        print(f"  ✓ Elevation range: {dem.min():.1f} - {dem.max():.1f} m")
        return dem

    except ImportError:
        print("  ✗ rasterio not installed — cannot parse GeoTIFF")
        print("    Install with: uv pip install rasterio")
        return None
    except Exception as e:
        print(f"  ✗ Error parsing GeoTIFF: {e}")
        return None


def get_kartverket_dem(
    data_dir: Path,
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX,
    resolution: float = 1.0,
) -> np.ndarray | None:
    """
    Get Kartverket 1m DEM, using cache if available.

    Args:
        data_dir: Directory for cached DEM files
        bbox: Bounding box in WGS84
        resolution: Desired resolution in meters

    Returns:
        numpy array of elevation data, or None if unavailable
    """
    cache_path = data_dir / "kartverket_dtm1m.tif"

    if cache_path.exists():
        print(f"  Using cached Kartverket DTM: {cache_path}")
        try:
            import rasterio

            with rasterio.open(cache_path) as src:
                dem = src.read(1).astype(np.float32)
            print(f"  ✓ Loaded: {dem.shape[1]}x{dem.shape[0]} px")
            return dem
        except Exception as e:
            print(f"  ✗ Cache load failed: {e}, re-downloading...")

    data_dir.mkdir(parents=True, exist_ok=True)
    return download_kartverket_dtm(bbox, output_path=cache_path, resolution=resolution)
