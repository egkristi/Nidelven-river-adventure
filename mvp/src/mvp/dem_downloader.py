"""
DEM downloader for Nidelven River Adventure.
Downloads real elevation data from Copernicus GLO-30 DEM (30m resolution).
Falls back to synthetic DEM if download fails.
"""

import requests
import os
import math
from pathlib import Path
from typing import Tuple, Optional
import time

# Nidelven river bounding box (approximate, covers full river)
# Format: (min_lon, min_lat, max_lon, max_lat)
NIDELVEN_BBOX = (8.2, 58.3, 8.9, 58.9)

# Copernicus GLO-30 DEM on AWS (free, no auth required)
COPERNICUS_BASE_URL = "https://copernicus-dem-30m.s3.amazonaws.com"


def _copernicus_tile_url(lat: int, lon: int) -> str:
    """Get the URL for a Copernicus GLO-30 DEM tile by its SW corner."""
    lat_prefix = "N" if lat >= 0 else "S"
    lon_prefix = "E" if lon >= 0 else "W"
    lat_str = f"{lat_prefix}{abs(lat):02d}"
    lon_str = f"{lon_prefix}{abs(lon):03d}"
    tile_name = f"Copernicus_DSM_COG_10_{lat_str}_00_{lon_str}_00_DEM"
    return f"{COPERNICUS_BASE_URL}/{tile_name}/{tile_name}.tif"


def download_dem_copernicus(
    bbox: Tuple[float, float, float, float],
    output_path: Path,
    max_retries: int = 3,
) -> Optional[Path]:
    """
    Download DEM from Copernicus GLO-30 (30m resolution) and crop to bbox.

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat) in WGS84
        output_path: Where to save the cropped GeoTIFF
        max_retries: Number of retries on failure

    Returns:
        Path to downloaded file, or None if failed
    """
    import numpy as np

    min_lon, min_lat, max_lon, max_lat = bbox

    # Determine which 1x1 degree tiles we need
    lat_start = int(math.floor(min_lat))
    lat_end = int(math.floor(max_lat))
    lon_start = int(math.floor(min_lon))
    lon_end = int(math.floor(max_lon))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tile_dir = output_path.parent / "tiles"
    tile_dir.mkdir(exist_ok=True)

    tile_paths = []
    for lat in range(lat_start, lat_end + 1):
        for lon in range(lon_start, lon_end + 1):
            tile_url = _copernicus_tile_url(lat, lon)
            tile_file = tile_dir / f"copernicus_n{lat}_e{lon}.tif"

            if tile_file.exists():
                print(f"  Using cached tile: N{lat} E{lon}")
                tile_paths.append(tile_file)
                continue

            for attempt in range(max_retries):
                try:
                    print(f"  Downloading Copernicus GLO-30 tile N{lat} E{lon}"
                          f" (attempt {attempt + 1}/{max_retries})...")
                    response = requests.get(tile_url, timeout=120, stream=True)

                    if response.status_code == 200:
                        with open(tile_file, "wb") as f:
                            for chunk in response.iter_content(chunk_size=65536):
                                f.write(chunk)
                        file_size = tile_file.stat().st_size
                        print(f"  ✓ Downloaded: {file_size / 1024 / 1024:.1f} MB")
                        tile_paths.append(tile_file)
                        break
                    else:
                        print(f"  ✗ HTTP {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
            else:
                print(f"  ✗ Failed to download tile N{lat} E{lon}")
                return None

    if not tile_paths:
        return None

    # Crop to bbox and save
    try:
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.transform import from_bounds as transform_from_bounds

        # For single tile (most common case for Nidelven)
        if len(tile_paths) == 1:
            with rasterio.open(tile_paths[0]) as src:
                window = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
                data = src.read(1, window=window)
                transform = src.window_transform(window)
        else:
            # Multiple tiles: merge then crop
            from rasterio.merge import merge
            datasets = [rasterio.open(p) for p in tile_paths]
            merged, merged_transform = merge(datasets)
            for ds in datasets:
                ds.close()
            # Crop merged result
            from rasterio.transform import rowcol
            row_start, col_start = rowcol(merged_transform, min_lon, max_lat)
            row_end, col_end = rowcol(merged_transform, max_lon, min_lat)
            data = merged[0, row_start:row_end, col_start:col_end]
            transform = transform_from_bounds(
                min_lon, min_lat, max_lon, max_lat, data.shape[1], data.shape[0]
            )

        # Save cropped DEM
        with rasterio.open(
            output_path, 'w', driver='GTiff',
            height=data.shape[0], width=data.shape[1],
            count=1, dtype=data.dtype,
            crs='EPSG:4326', transform=transform,
        ) as dst:
            dst.write(data, 1)

        print(f"  ✓ Cropped DEM: {data.shape[1]}x{data.shape[0]} px")
        print(f"  ✓ Elevation range: {data.min():.1f} - {data.max():.1f} m")
        print(f"  ✓ Saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"  ✗ Error processing tiles: {e}")
        return None


def create_sample_dem(output_path: Path, size: int = 512) -> Path:
    """
    Create a sample synthetic DEM for testing when real data is unavailable.
    Simulates a river valley with surrounding hills.
    """
    import numpy as np
    from PIL import Image
    
    print(f"  Creating sample DEM ({size}x{size})...")
    
    # Create synthetic terrain: river valley running diagonally
    x = np.linspace(0, 1, size)
    y = np.linspace(0, 1, size)
    X, Y = np.meshgrid(x, y)
    
    # River path (sine wave down the middle)
    river_x = 0.5 + 0.15 * np.sin(Y * np.pi * 3)
    distance_from_river = np.abs(X - river_x)
    
    # Height: low at river, higher at edges
    base_height = 50  # meters
    river_depth = 30
    hill_height = 200
    
    height = base_height + river_depth * np.exp(-distance_from_river * 20)
    height += hill_height * (distance_from_river ** 2)
    
    # Add some noise
    np.random.seed(42)
    height += np.random.normal(0, 2, height.shape)
    
    # Add a waterfall feature
    waterfall_y = int(size * 0.6)
    height[waterfall_y:waterfall_y+5, :] += 15  # elevation drop
    
    # Save as 16-bit TIFF (standard for DEM)
    height_uint16 = np.clip(height, 0, 65535).astype(np.uint16)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save with rasterio if available, otherwise PIL
    try:
        import rasterio
        from rasterio.transform import from_bounds
        
        # GeoTIFF with proper georeferencing
        transform = from_bounds(*NIDELVEN_BBOX, width=size, height=size)
        
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=size,
            width=size,
            count=1,
            dtype=height_uint16.dtype,
            crs='EPSG:4326',
            transform=transform,
        ) as dst:
            dst.write(height_uint16, 1)
            dst.update_tags(AREA_OR_POINT='Point')
    
    except ImportError:
        # Fallback: save as plain TIFF with PIL
        Image.fromarray(height_uint16).save(output_path)
        print("  (Saved without georeferencing - install rasterio for full support)")
    
    print(f"  ✓ Sample DEM saved: {output_path}")
    return output_path


def get_dem_path(data_dir: Path, prefer_real: bool = True) -> Path:
    """
    Get path to DEM file, downloading if necessary.
    Falls back to synthetic data if download fails.
    """
    dem_path = data_dir / "dem.tif"
    
    if dem_path.exists():
        print(f"  Using existing DEM: {dem_path}")
        return dem_path
    
    if prefer_real:
        print("  Attempting to download real DEM from Copernicus GLO-30...")
        result = download_dem_copernicus(NIDELVEN_BBOX, dem_path)
        if result:
            return result
        print("  Download failed. Falling back to synthetic DEM...")
    
    return create_sample_dem(dem_path)


if __name__ == "__main__":
    import sys
    
    data_dir = Path(__file__).parent / "data"
    
    # Check for --sample flag
    prefer_real = "--sample" not in sys.argv
    
    dem_path = get_dem_path(data_dir, prefer_real=prefer_real)
    print(f"\nDEM ready: {dem_path}")
