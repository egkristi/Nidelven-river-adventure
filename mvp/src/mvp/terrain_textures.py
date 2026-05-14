"""
Terrain texture generator.

Generates splatmap data for Unity terrain based on:
- Elevation zones (water, beach, grass, forest, rock, snow)
- Slope angle (steep = rock, flat = grass/forest)
- Flow accumulation (river channels)

Exports a splatmap PNG (RGBA channels = 4 terrain layers) for Unity TerrainLayer.
"""

from pathlib import Path

import numpy as np
from PIL import Image


def compute_slope(dem: np.ndarray, cell_size: float = 30.0) -> np.ndarray:
    """
    Compute slope angle in degrees from DEM.

    Args:
        dem: 2D elevation array
        cell_size: Size of each DEM cell in meters

    Returns:
        2D array of slope angles in degrees (0 = flat, 90 = vertical)
    """
    grad_y, grad_x = np.gradient(dem, cell_size)
    slope_rad = np.arctan(np.sqrt(grad_x**2 + grad_y**2))
    return np.degrees(slope_rad)


def generate_splatmap(
    dem: np.ndarray,
    slope: np.ndarray | None = None,
    accumulation: np.ndarray | None = None,
    cell_size: float = 30.0,
    water_level: float | None = None,
    snow_line: float | None = None,
) -> np.ndarray:
    """
    Generate a 4-channel splatmap from DEM data.

    Channels (matching Unity TerrainLayer order):
        R = Grass/Meadow (flat areas, mid-elevation)
        G = Forest (mid-elevation, moderate slope)
        B = Rock/Cliff (steep areas or high elevation)
        A = Sand/Shore (near water level or river banks)

    Args:
        dem: 2D elevation array
        slope: Pre-computed slope (degrees). Computed if None.
        accumulation: Flow accumulation grid (for river detection)
        cell_size: DEM cell size in meters
        water_level: Elevation of water surface. Defaults to 10th percentile.
        snow_line: Elevation above which rock/snow dominates. Defaults to 90th percentile.

    Returns:
        HxWx4 uint8 array (RGBA splatmap)
    """
    if slope is None:
        slope = compute_slope(dem, cell_size)

    h, w = dem.shape

    if water_level is None:
        water_level = np.percentile(dem, 10)
    if snow_line is None:
        snow_line = np.percentile(dem, 90)

    # Normalize elevation to 0-1 range
    elev_min = dem.min()
    elev_range = dem.max() - elev_min
    if elev_range < 1e-6:
        elev_range = 1.0
    elev_norm = (dem - elev_min) / elev_range

    # Initialize channels
    grass = np.zeros((h, w), dtype=np.float32)
    forest = np.zeros((h, w), dtype=np.float32)
    rock = np.zeros((h, w), dtype=np.float32)
    sand = np.zeros((h, w), dtype=np.float32)

    # --- Sand/Shore: near water level ---
    shore_band = elev_range * 0.05  # 5% of elevation range
    near_water = dem < (water_level + shore_band)
    sand[near_water] = 1.0
    # Fade out sand with distance from water
    sand_fade = np.clip(1.0 - (dem - water_level) / shore_band, 0, 1)
    sand = np.maximum(sand, sand_fade * 0.5)

    # --- Rock: steep slopes or high elevation ---
    steep_mask = slope > 35.0  # > 35 degrees = cliff
    rock[steep_mask] = 1.0
    # Moderate steep (25-35 degrees) = partial rock
    moderate_steep = (slope > 25.0) & (slope <= 35.0)
    rock[moderate_steep] = (slope[moderate_steep] - 25.0) / 10.0
    # High elevation = rock
    high_elev = dem > snow_line
    rock[high_elev] = np.maximum(rock[high_elev], 0.8)

    # --- Forest: mid-elevation, moderate slope ---
    mid_elev = (dem > water_level + shore_band) & (dem < snow_line * 0.85)
    gentle_slope = slope < 30.0
    forest_zone = mid_elev & gentle_slope
    forest[forest_zone] = 0.8
    # Elevation-based density (denser at mid elevations)
    forest_density = np.clip((elev_norm - 0.2) * 2.0, 0, 1) * np.clip((0.8 - elev_norm) * 2.0, 0, 1)
    forest = forest * forest_density

    # --- Grass: flat areas at lower-mid elevation ---
    flat_mask = slope < 15.0
    low_mid_elev = (dem > water_level + shore_band) & (dem < snow_line * 0.7)
    grass_zone = flat_mask & low_mid_elev
    grass[grass_zone] = 1.0
    # Grass fades with slope
    grass_slope_fade = np.clip(1.0 - slope / 20.0, 0, 1)
    grass = grass * grass_slope_fade

    # --- River channels (if accumulation provided) ---
    if accumulation is not None:
        river_threshold = np.percentile(accumulation, 98)
        river_mask = accumulation > river_threshold
        sand[river_mask] = 0.8  # River banks are sandy
        grass[river_mask] = 0.0
        forest[river_mask] = 0.0

    # Default: pixels with no assigned terrain get grass
    no_coverage = (grass + forest + rock + sand) < 1e-6
    grass[no_coverage] = 1.0

    # Normalize so channels sum to 1.0
    total = grass + forest + rock + sand
    total[total < 1e-6] = 1.0  # Avoid division by zero
    grass /= total
    forest /= total
    rock /= total
    sand /= total

    # Convert to uint8
    splatmap = np.stack([grass, forest, rock, sand], axis=-1)
    splatmap = (splatmap * 255).astype(np.uint8)

    return splatmap


def export_splatmap(
    dem: np.ndarray,
    output_path: Path,
    accumulation: np.ndarray | None = None,
    cell_size: float = 30.0,
    resolution: int | None = None,
) -> Path:
    """
    Generate and save terrain splatmap as PNG.

    Args:
        dem: 2D elevation array
        output_path: Path for output PNG
        accumulation: Optional flow accumulation for river detection
        cell_size: DEM cell size in meters
        resolution: Output resolution (resamples if different from DEM).
                   Defaults to DEM size.

    Returns:
        Path to saved PNG
    """
    splatmap = generate_splatmap(dem, accumulation=accumulation, cell_size=cell_size)

    if resolution is not None and resolution != dem.shape[0]:
        # Resample to target resolution
        img = Image.fromarray(splatmap, mode="RGBA")
        img = img.resize((resolution, resolution), Image.BILINEAR)
    else:
        img = Image.fromarray(splatmap, mode="RGBA")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)

    print(f"  Splatmap: {output_path} ({img.size[0]}x{img.size[1]})")
    print("  Channels: R=Grass, G=Forest, B=Rock, A=Sand/Shore")
    return output_path
