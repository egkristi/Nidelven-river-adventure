"""
NIBIO AR5 land cover classification client.

Downloads land use/land cover data from NIBIO's WFS service.
Provides classification for accurate vegetation placement in Unity
(forest type, farmland, wetland, water, built-up areas).

API: https://wfs.nibio.no/wfs/ar5
License: NLOD (free for any use with attribution)
Documentation: https://kilden.nibio.no/

AR5 classes (arealtype):
- 10: Built-up / developed
- 20: Agricultural (cropland)
- 30: Forest (skog)
- 50: Open land (hei/myr/fjell)
- 60: Wetland / bog
- 70: Glacier / permanent snow
- 80: Freshwater (rivers, lakes)
- 81: Saltwater / sea
- 99: Unclassified

Forest subtypes (treslag):
- 31: Spruce (gran)
- 32: Pine (furu)
- 33: Deciduous (løvskog) — birch, oak, etc.
- 39: Mixed forest

Forest density (skogbonitet):
- 6-8: Low (sparse forest)
- 11: Medium
- 14-17: High (dense)
"""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np

logger = logging.getLogger(__name__)

# NIBIO AR5 WFS endpoint
AR5_WFS_URL = "https://wfs.nibio.no/wfs/ar5"

# Required user agent
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Nidelven bounding box (WGS84)
NIDELVEN_BBOX_WGS84 = (8.45, 58.38, 8.85, 58.62)

# AR5 land cover class definitions
AR5_CLASSES = {
    10: "built_up",
    20: "agriculture",
    30: "forest",
    50: "open_land",
    60: "wetland",
    70: "glacier",
    80: "freshwater",
    81: "saltwater",
    99: "unclassified",
}

# Forest subtypes
FOREST_TYPES = {
    31: "spruce",
    32: "pine",
    33: "deciduous",
    39: "mixed",
}

# Mapping AR5 classes to Unity vegetation parameters
VEGETATION_PARAMS = {
    "forest": {
        "tree_density": 0.8,
        "grass_density": 0.3,
        "rock_density": 0.05,
    },
    "agriculture": {
        "tree_density": 0.02,
        "grass_density": 0.9,
        "rock_density": 0.0,
    },
    "open_land": {
        "tree_density": 0.1,
        "grass_density": 0.6,
        "rock_density": 0.15,
    },
    "wetland": {
        "tree_density": 0.05,
        "grass_density": 0.7,
        "rock_density": 0.0,
    },
    "built_up": {
        "tree_density": 0.05,
        "grass_density": 0.2,
        "rock_density": 0.0,
    },
    "freshwater": {
        "tree_density": 0.0,
        "grass_density": 0.0,
        "rock_density": 0.0,
    },
}


def fetch_land_cover(
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX_WGS84,
    srs: str = "EPSG:4326",
    max_features: int = 5000,
    timeout: int = 30,
) -> dict:
    """
    Fetch AR5 land cover data from NIBIO WFS.

    Args:
        bbox: Bounding box (minx, miny, maxx, maxy) in WGS84
        srs: Coordinate reference system
        max_features: Maximum features to return
        timeout: Request timeout in seconds

    Returns:
        GeoJSON FeatureCollection dict
    """
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": "ar5:Arealressursflate",
        "outputFormat": "application/json",
        "srsName": srs,
        "count": str(max_features),
        "bbox": f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]},{srs}",
    }

    url = f"{AR5_WFS_URL}?{urlencode(params)}"
    logger.info(f"Fetching NIBIO AR5: bbox={bbox}")

    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))

    feature_count = len(data.get("features", []))
    logger.info(f"  Received {feature_count} AR5 features")
    print(f"  Received {feature_count} AR5 land cover polygons")

    return data


def classify_features(geojson: dict) -> list[dict[str, Any]]:
    """
    Extract and classify AR5 features into game-usable categories.

    Args:
        geojson: GeoJSON FeatureCollection from fetch_land_cover()

    Returns:
        List of dicts with class, forest_type, centroid, area info
    """
    classified = []

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        # AR5 uses 'arealtype' for main class
        arealtype = props.get("arealtype", 99)
        treslag = props.get("treslag", 0)

        # Map to our class names
        land_class = AR5_CLASSES.get(arealtype, "unclassified")
        forest_type = FOREST_TYPES.get(treslag) if land_class == "forest" else None

        # Calculate centroid from geometry
        centroid = _geometry_centroid(geometry)

        classified.append(
            {
                "class": land_class,
                "arealtype": arealtype,
                "forest_type": forest_type,
                "treslag": treslag,
                "centroid": centroid,
                "geometry_type": geometry.get("type", ""),
            }
        )

    return classified


def generate_vegetation_map(
    geojson: dict,
    dem_shape: tuple[int, int],
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX_WGS84,
) -> np.ndarray:
    """
    Rasterize AR5 data into a vegetation classification grid.

    Creates a 2D array matching DEM dimensions where each cell contains
    the dominant land cover class ID for vegetation placement.

    Args:
        geojson: GeoJSON FeatureCollection from fetch_land_cover()
        dem_shape: (rows, cols) shape of the DEM array
        bbox: Bounding box matching the DEM extent

    Returns:
        2D numpy array (uint8) with AR5 class IDs
    """
    rows, cols = dem_shape
    veg_map = np.full((rows, cols), 50, dtype=np.uint8)  # Default: open land

    min_lon, min_lat, max_lon, max_lat = bbox
    lon_range = max_lon - min_lon
    lat_range = max_lat - min_lat

    if lon_range <= 0 or lat_range <= 0:
        return veg_map

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        arealtype = props.get("arealtype", 50)

        # Get all coordinates from the geometry
        coords = _extract_coordinates(geometry)
        if not coords:
            continue

        # Rasterize: mark cells that fall within this feature's coordinates
        for lon, lat in coords:
            col = int((lon - min_lon) / lon_range * (cols - 1))
            row = int((max_lat - lat) / lat_range * (rows - 1))

            if 0 <= row < rows and 0 <= col < cols:
                veg_map[row, col] = arealtype

    return veg_map


def get_vegetation_params(land_class: str) -> dict:
    """
    Get vegetation placement parameters for a land cover class.

    Args:
        land_class: One of 'forest', 'agriculture', 'open_land', etc.

    Returns:
        Dict with tree_density, grass_density, rock_density (0-1)
    """
    return VEGETATION_PARAMS.get(
        land_class,
        {"tree_density": 0.1, "grass_density": 0.4, "rock_density": 0.1},
    )


def build_unity_vegetation_data(
    classified: list[dict],
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX_WGS84,
) -> dict:
    """
    Build vegetation data structure for Unity VegetationGenerator.

    Args:
        classified: List from classify_features()
        bbox: Bounding box

    Returns:
        Dict with zones and vegetation parameters for Unity
    """
    # Count land cover distribution
    class_counts: dict[str, int] = {}
    forest_type_counts: dict[str, int] = {}

    for item in classified:
        cls = item["class"]
        class_counts[cls] = class_counts.get(cls, 0) + 1
        if item["forest_type"]:
            ft = item["forest_type"]
            forest_type_counts[ft] = forest_type_counts.get(ft, 0) + 1

    # Build vegetation zones with params
    zones = []
    for item in classified:
        if item["centroid"] is None:
            continue

        params = get_vegetation_params(item["class"])
        zones.append(
            {
                "position": item["centroid"],
                "class": item["class"],
                "forest_type": item.get("forest_type"),
                "tree_density": params["tree_density"],
                "grass_density": params["grass_density"],
                "rock_density": params["rock_density"],
            }
        )

    return {
        "bbox": list(bbox),
        "total_features": len(classified),
        "class_distribution": class_counts,
        "forest_types": forest_type_counts,
        "zones": zones,
        "source": "nibio_ar5",
    }


def export_vegetation_json(
    output_path: Path,
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX_WGS84,
    fetch_live: bool = True,
    dem_shape: tuple[int, int] | None = None,
) -> Path:
    """
    Export vegetation/land cover data as JSON for Unity.

    Args:
        output_path: Directory to write vegetation_data.json
        bbox: Bounding box for the area
        fetch_live: If True, fetch from NIBIO WFS. If False, use defaults.
        dem_shape: Optional DEM shape for rasterized map

    Returns:
        Path to the exported JSON file
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    if fetch_live:
        try:
            geojson = fetch_land_cover(bbox=bbox)
            classified = classify_features(geojson)
            veg_data = build_unity_vegetation_data(classified, bbox=bbox)

            # Optionally export rasterized vegetation map
            if dem_shape is not None:
                veg_map = generate_vegetation_map(geojson, dem_shape, bbox)
                map_path = output_path / "vegetation_map.raw"
                veg_map.tofile(map_path)
                veg_data["vegetation_map"] = str(map_path.name)
                veg_data["map_shape"] = list(dem_shape)
                print(f"  Vegetation map exported: {map_path} ({dem_shape[0]}x{dem_shape[1]})")

        except Exception as e:
            logger.warning(f"NIBIO AR5 fetch failed: {e}, using defaults")
            print(f"  NIBIO AR5 unavailable: {e}")
            veg_data = _default_vegetation_data(bbox)
    else:
        veg_data = _default_vegetation_data(bbox)

    output_file = output_path / "vegetation_data.json"
    output_file.write_text(json.dumps(veg_data, indent=2))

    print(f"  Vegetation data exported: {output_file}")
    print(f"  Total features: {veg_data.get('total_features', 0)}")
    if veg_data.get("class_distribution"):
        for cls, count in sorted(veg_data["class_distribution"].items(), key=lambda x: -x[1]):
            print(f"    {cls}: {count} polygons")

    return output_file


def _geometry_centroid(geometry: dict) -> list[float] | None:
    """Calculate approximate centroid of a GeoJSON geometry."""
    coords = _extract_coordinates(geometry)
    if not coords:
        return None

    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return [sum(lons) / len(lons), sum(lats) / len(lats)]


def _extract_coordinates(geometry: dict) -> list[tuple[float, float]]:
    """
    Extract all coordinate pairs from a GeoJSON geometry.

    Handles Point, LineString, Polygon, MultiPolygon, etc.
    """
    geo_type = geometry.get("type", "")
    coordinates = geometry.get("coordinates", [])

    if not coordinates:
        return []

    result = []

    if geo_type == "Point":
        result.append((coordinates[0], coordinates[1]))
    elif geo_type == "LineString":
        for coord in coordinates:
            if len(coord) >= 2:
                result.append((coord[0], coord[1]))
    elif geo_type == "Polygon":
        # First ring is outer boundary
        for ring in coordinates:
            for coord in ring:
                if len(coord) >= 2:
                    result.append((coord[0], coord[1]))
    elif geo_type == "MultiPolygon":
        for polygon in coordinates:
            for ring in polygon:
                for coord in ring:
                    if len(coord) >= 2:
                        result.append((coord[0], coord[1]))
    elif geo_type == "MultiLineString":
        for line in coordinates:
            for coord in line:
                if len(coord) >= 2:
                    result.append((coord[0], coord[1]))

    return result


def _default_vegetation_data(bbox: tuple[float, float, float, float]) -> dict:
    """
    Generate default vegetation data when API is unavailable.

    Based on typical Nidelva valley composition:
    ~60% forest (mostly spruce/pine), ~15% agriculture, ~10% water, ~15% open
    """
    return {
        "bbox": list(bbox),
        "total_features": 0,
        "class_distribution": {
            "forest": 60,
            "agriculture": 15,
            "freshwater": 10,
            "open_land": 10,
            "built_up": 5,
        },
        "forest_types": {
            "spruce": 35,
            "pine": 25,
            "deciduous": 20,
            "mixed": 20,
        },
        "zones": [],
        "source": "default_estimate",
    }
