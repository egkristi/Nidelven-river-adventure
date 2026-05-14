"""
Norge i bilder WMTS client for aerial orthophoto terrain textures.

Downloads high-resolution aerial orthophotos (10-25cm) from Kartverket's
Norge i bilder WMTS service. Used as terrain textures in Unity.

Endpoint: https://opencache.statkart.no/gatekeeper/gk/gk.open_nib_web_mercator_wmts_v2
License: CC BY 4.0 / NLOD (Norwegian public geodata)
"""

import math
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image

from .dem_downloader import NIDELVEN_BBOX

# WMTS endpoint for Norge i bilder (Web Mercator tiles)
NIB_WMTS_URL = "https://opencache.statkart.no/gatekeeper/gk/gk.open_nib_web_mercator_wmts_v2"

# User-Agent for API requests
USER_AGENT = "NidelvenRiverAdventure/0.1 (github.com/egkristi/Nidelven-river-adventure)"

# Tile size in pixels (standard WMTS)
TILE_SIZE = 256

# Default zoom level (15 gives ~4.7m/pixel at 58°N, good for terrain textures)
DEFAULT_ZOOM = 15


def wgs84_to_tile(lon: float, lat: float, zoom: int) -> tuple[int, int]:
    """
    Convert WGS84 coordinates to WMTS tile indices (Web Mercator).

    Args:
        lon: Longitude in degrees
        lat: Latitude in degrees
        zoom: WMTS zoom level

    Returns:
        Tuple of (tile_x, tile_y)
    """
    n = 2**zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return (x, y)


def tile_to_wgs84(x: int, y: int, zoom: int) -> tuple[float, float]:
    """
    Convert WMTS tile indices to WGS84 (top-left corner of tile).

    Args:
        x: Tile X index
        y: Tile Y index
        zoom: Zoom level

    Returns:
        Tuple of (longitude, latitude)
    """
    n = 2**zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return (lon, lat)


def get_tile_bounds(
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX,
    zoom: int = DEFAULT_ZOOM,
) -> tuple[int, int, int, int]:
    """
    Calculate the range of WMTS tiles covering a bounding box.

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat) in WGS84
        zoom: WMTS zoom level

    Returns:
        Tuple of (min_x, min_y, max_x, max_y) tile indices
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    x_min, y_max = wgs84_to_tile(min_lon, min_lat, zoom)
    x_max, y_min = wgs84_to_tile(max_lon, max_lat, zoom)
    return (x_min, y_min, x_max, y_max)


def download_tile(
    x: int,
    y: int,
    zoom: int = DEFAULT_ZOOM,
    timeout: int = 30,
) -> Image.Image | None:
    """
    Download a single WMTS tile from Norge i bilder.

    Args:
        x: Tile X index
        y: Tile Y index
        zoom: Zoom level
        timeout: Request timeout in seconds

    Returns:
        PIL Image or None if download fails
    """
    # KVP (Key-Value Pair) WMTS request
    params = {
        "SERVICE": "WMTS",
        "VERSION": "1.0.0",
        "REQUEST": "GetTile",
        "LAYER": "ortofoto",
        "STYLE": "default",
        "FORMAT": "image/png",
        "TILEMATRIXSET": "googlemaps",
        "TILEMATRIX": str(zoom),
        "TILEROW": str(y),
        "TILECOL": str(x),
    }

    try:
        response = requests.get(
            NIB_WMTS_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()

        if "image" not in response.headers.get("content-type", ""):
            return None

        return Image.open(BytesIO(response.content)).convert("RGB")
    except (requests.RequestException, OSError):
        return None


def download_orthophoto(
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX,
    zoom: int = DEFAULT_ZOOM,
    output_path: Path | None = None,
    max_tiles: int = 100,
) -> np.ndarray | None:
    """
    Download and stitch aerial orthophoto tiles for a bounding box.

    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat) in WGS84
        zoom: WMTS zoom level (higher = more detail, more tiles)
        output_path: Optional path to save the stitched image as PNG
        max_tiles: Maximum number of tiles to download (safety limit)

    Returns:
        Numpy array (H, W, 3) of RGB pixel values, or None on failure
    """
    x_min, y_min, x_max, y_max = get_tile_bounds(bbox, zoom)

    num_x = x_max - x_min + 1
    num_y = y_max - y_min + 1
    total_tiles = num_x * num_y

    if total_tiles > max_tiles:
        raise ValueError(
            f"Bounding box requires {total_tiles} tiles at zoom {zoom}, "
            f"exceeding max_tiles={max_tiles}. Reduce zoom or bbox."
        )

    if total_tiles == 0:
        return None

    # Create output image
    width = num_x * TILE_SIZE
    height = num_y * TILE_SIZE
    result = np.zeros((height, width, 3), dtype=np.uint8)

    downloaded = 0
    for ty in range(y_min, y_max + 1):
        for tx in range(x_min, x_max + 1):
            tile_img = download_tile(tx, ty, zoom)
            if tile_img is not None:
                px = (tx - x_min) * TILE_SIZE
                py = (ty - y_min) * TILE_SIZE
                tile_arr = np.array(tile_img)
                # Handle tiles that may be smaller at edges
                h, w = tile_arr.shape[:2]
                result[py : py + h, px : px + w] = tile_arr[:, :, :3]
                downloaded += 1

    if downloaded == 0:
        return None

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(result).save(str(output_path))

    return result


def export_terrain_texture(
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX,
    output_dir: Path = Path("output"),
    zoom: int = DEFAULT_ZOOM,
    texture_size: int = 1024,
) -> Path | None:
    """
    Download orthophoto and export as a Unity-ready terrain texture.

    Resizes the downloaded image to a power-of-2 texture suitable for
    Unity terrain layers.

    Args:
        bbox: Bounding box in WGS84
        output_dir: Directory to save the texture
        zoom: WMTS zoom level
        texture_size: Output texture resolution (width and height)

    Returns:
        Path to the exported texture file, or None on failure
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "orthophoto_raw.png"

    ortho = download_orthophoto(bbox, zoom, raw_path)
    if ortho is None:
        return None

    # Resize to power-of-2 for Unity
    img = Image.fromarray(ortho)
    img_resized = img.resize((texture_size, texture_size), Image.LANCZOS)

    texture_path = output_dir / "terrain_orthophoto.png"
    img_resized.save(str(texture_path))

    return texture_path
