"""
DEM downloader for Kartverket Høydedata.
Downloads simplified 10m DEM for the Nidelven river area.
"""

import requests
import os
from pathlib import Path
import json
from typing import Tuple, Optional
import time

# Nidelven river bounding box (approximate, covers full river)
# Format: (min_lon, min_lat, max_lon, max_lat)
NIDELVEN_BBOX = (8.2, 58.3, 8.9, 58.9)

# Kartverket WCS endpoint for DTM 10m
KARTVERKET_WCS_URL = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm10"

def download_dem_geonorge(
    bbox: Tuple[float, float, float, float],
    output_path: Path,
    resolution: int = 10,
    max_retries: int = 3
) -> Optional[Path]:
    """
    Download DEM from Kartverket using WCS GetCoverage.
    
    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat) in WGS84
        output_path: Where to save the GeoTIFF
        resolution: Resolution in meters (10 for DTM10)
        max_retries: Number of retries on failure
    
    Returns:
        Path to downloaded file, or None if failed
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    
    # Calculate grid size based on resolution
    # At this latitude (~58.6°N), 1 degree lon ≈ 32km, 1 degree lat ≈ 111km
    width_m = (max_lon - min_lon) * 32000  # approximate
    height_m = (max_lat - min_lat) * 111000
    
    width_px = int(width_m / resolution)
    height_px = int(height_m / resolution)
    
    # Cap at reasonable size for MVP
    max_size = 2048
    if width_px > max_size or height_px > max_size:
        scale = max(width_px, height_px) / max_size
        width_px = int(width_px / scale)
        height_px = int(height_px / scale)
        print(f"  Resizing to {width_px}x{height_px} for MVP preview")
    
    # WCS GetCoverage request
    params = {
        "SERVICE": "WCS",
        "REQUEST": "GetCoverage",
        "VERSION": "2.0.1",
        "COVERAGEID": f"dtm{resolution}",
        "SUBSET": [
            f"x({min_lon},{max_lon})",
            f"y({min_lat},{max_lat})"
        ],
        "FORMAT": "image/tiff",
        "OUTSIZE": f"{width_px},{height_px}"
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            print(f"  Downloading DEM (attempt {attempt + 1}/{max_retries})...")
            response = requests.get(
                KARTVERKET_WCS_URL,
                params=params,
                timeout=120,
                stream=True
            )
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size = output_path.stat().st_size
                print(f"  ✓ Downloaded: {file_size / 1024 / 1024:.1f} MB")
                return output_path
            else:
                print(f"  ✗ HTTP {response.status_code}: {response.text[:200]}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
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
        print("  Attempting to download real DEM from Kartverket...")
        result = download_dem_geonorge(NIDELVEN_BBOX, dem_path)
        if result:
            return result
        print("  Falling back to synthetic DEM...")
    
    return create_sample_dem(dem_path)


if __name__ == "__main__":
    import sys
    
    data_dir = Path(__file__).parent / "data"
    
    # Check for --sample flag
    prefer_real = "--sample" not in sys.argv
    
    dem_path = get_dem_path(data_dir, prefer_real=prefer_real)
    print(f"\nDEM ready: {dem_path}")
