"""
Kartverket FKB-Bygning building client.

Fetches building footprints from Kartverket's FKB-Bygning WFS
for the Nidelva river corridor. Provides building positions, heights,
types, and footprints for placing 3D landmarks along the river.

API: https://wfs.geonorge.no/skwms1/wfs.matrikkelen-bygningspunkt
License: NLOD (free for any use with attribution)
Data: FKB-Bygning (building footprints with 2.5D heights)

Building types (SOSI/Matrikkelen codes):
- 111-199: Residential
- 211-299: Industrial/commercial
- 311-399: Office/business
- 411-449: Transport (stations, garages)
- 511-539: Hotels/restaurants
- 611-659: Culture/research
- 700-799: Health/social
- 800-899: Correctional
"""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Kartverket WFS endpoint for building points
WFS_URL = "https://wfs.geonorge.no/skwms1/wfs.matrikkelen-bygningspunkt"

# User agent for API requests
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Nidelva bounding box (Agder, Norway) — WGS84
NIDELVA_BBOX = {
    "min_lon": 8.45,
    "min_lat": 58.38,
    "max_lon": 8.85,
    "max_lat": 58.62,
}

# Building type classification (SOSI bygningstypekode)
BUILDING_CLASSES = {
    "residential": range(111, 200),
    "industrial": range(211, 300),
    "commercial": range(311, 400),
    "transport": range(411, 450),
    "hospitality": range(511, 540),
    "cultural": range(611, 660),
    "health": range(700, 800),
    "other": range(800, 1000),
}

# Unity prefab mapping
BUILDING_PREFABS = {
    "residential": "BuildingResidential",
    "industrial": "BuildingIndustrial",
    "commercial": "BuildingCommercial",
    "transport": "BuildingTransport",
    "hospitality": "BuildingHospitality",
    "cultural": "BuildingCultural",
    "health": "BuildingHealth",
    "other": "BuildingGeneric",
}

# Default building heights by type (meters)
DEFAULT_HEIGHTS = {
    "residential": 7.0,
    "industrial": 10.0,
    "commercial": 12.0,
    "transport": 5.0,
    "hospitality": 15.0,
    "cultural": 8.0,
    "health": 12.0,
    "other": 6.0,
}

# Known buildings along Nidelva (offline fallback)
NIDELVA_BUILDINGS = [
    {
        "name": "Rykene kraftstasjon",
        "type_code": 211,
        "latitude": 58.4435,
        "longitude": 8.5225,
        "height_m": 8.0,
        "footprint_m2": 400.0,
        "year_built": 1931,
    },
    {
        "name": "Bøylefoss kraftstasjon",
        "type_code": 211,
        "latitude": 58.5240,
        "longitude": 8.6430,
        "height_m": 10.0,
        "footprint_m2": 600.0,
        "year_built": 1913,
    },
    {
        "name": "Froland kirke",
        "type_code": 671,
        "latitude": 58.5060,
        "longitude": 8.6380,
        "height_m": 18.0,
        "footprint_m2": 200.0,
        "year_built": 1798,
    },
    {
        "name": "Helle gård (fjøs)",
        "type_code": 241,
        "latitude": 58.4510,
        "longitude": 8.5600,
        "height_m": 6.0,
        "footprint_m2": 300.0,
        "year_built": 1890,
    },
    {
        "name": "Simonstad bru bolighus",
        "type_code": 111,
        "latitude": 58.4650,
        "longitude": 8.5850,
        "height_m": 7.0,
        "footprint_m2": 120.0,
        "year_built": 1960,
    },
    {
        "name": "Bøylefoss handelsbod",
        "type_code": 321,
        "latitude": 58.5235,
        "longitude": 8.6420,
        "height_m": 5.0,
        "footprint_m2": 80.0,
        "year_built": 1925,
    },
]


def get_building_list() -> list[dict]:
    """Return the curated offline building list for Nidelva."""
    return list(NIDELVA_BUILDINGS)


def fetch_buildings(
    bbox: dict[str, float] | None = None,
    max_features: int = 100,
) -> list[dict]:
    """
    Fetch buildings from Kartverket WFS within bounding box.

    Args:
        bbox: Bounding box dict with min_lon, min_lat, max_lon, max_lat.
              Defaults to NIDELVA_BBOX.
        max_features: Maximum number of features to request.

    Returns:
        List of building dicts with position, type, and dimensions.
    """
    if bbox is None:
        bbox = NIDELVA_BBOX

    # WFS GetFeature request
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": "app:Bygning",
        "outputFormat": "application/json",
        "count": str(max_features),
        "srsName": "EPSG:4326",
        "bbox": f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']},EPSG:4326",
    }

    url = f"{WFS_URL}?{urlencode(params)}"
    logger.info(f"Fetching buildings from: {url}")

    try:
        req = Request(url)
        req.add_header("User-Agent", USER_AGENT)

        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        features = data.get("features", [])
        logger.info(f"Received {len(features)} building features")

        buildings = []
        for feature in features:
            building = _parse_building_feature(feature)
            if building:
                buildings.append(building)

        return buildings

    except Exception as e:
        logger.warning(f"WFS request failed: {e}")
        return []


def _parse_building_feature(feature: dict[str, Any]) -> dict | None:
    """Parse a GeoJSON feature into a building dict."""
    props = feature.get("properties", {})
    geometry = feature.get("geometry", {})

    if not geometry:
        return None

    # Extract coordinates
    coords = geometry.get("coordinates", [])
    geom_type = geometry.get("type", "")

    lat, lon = _extract_centroid(coords, geom_type)
    if lat is None:
        return None

    # Extract building properties
    type_code = _safe_int(props.get("bygningstype", props.get("byggTypKode")))
    height = _safe_float(props.get("hoyde", props.get("bygningshøyde")))
    area = _safe_float(props.get("bebygdAreal", props.get("bruksareal")))

    return {
        "name": props.get("bygningsnavn", props.get("navn", "")),
        "type_code": type_code or 999,
        "latitude": lat,
        "longitude": lon,
        "height_m": height or 0.0,
        "footprint_m2": area or 0.0,
        "year_built": _safe_int(props.get("byggeaar", props.get("opprinneligByggeaar"))),
    }


def _extract_centroid(coords: list, geom_type: str) -> tuple[float | None, float | None]:
    """Extract centroid from GeoJSON coordinates."""
    if not coords:
        return None, None

    if geom_type == "Point":
        if len(coords) >= 2:
            return coords[1], coords[0]  # GeoJSON is [lon, lat]
        return None, None

    if geom_type == "MultiPoint":
        if not coords:
            return None, None
        lats = [c[1] for c in coords if len(c) >= 2]
        lons = [c[0] for c in coords if len(c) >= 2]
        if lats and lons:
            return sum(lats) / len(lats), sum(lons) / len(lons)
        return None, None

    if geom_type in ("Polygon", "MultiPolygon"):
        # Flatten all coordinate rings
        all_points = _flatten_polygon_coords(coords, geom_type)
        if all_points:
            lats = [p[1] for p in all_points]
            lons = [p[0] for p in all_points]
            return sum(lats) / len(lats), sum(lons) / len(lons)

    return None, None


def _flatten_polygon_coords(coords: list, geom_type: str) -> list:
    """Flatten polygon/multipolygon coordinates to a list of [lon, lat] points."""
    points = []
    if geom_type == "Polygon":
        for ring in coords:
            points.extend(ring)
    elif geom_type == "MultiPolygon":
        for polygon in coords:
            for ring in polygon:
                points.extend(ring)
    return points


def classify_building(type_code: int | None) -> str:
    """Classify a building type code into a category."""
    if type_code is None:
        return "other"

    for category, code_range in BUILDING_CLASSES.items():
        if type_code in code_range:
            return category

    return "other"


def build_building_data(buildings: list[dict] | None = None) -> dict:
    """
    Build Unity-ready building data from a list of buildings.

    Args:
        buildings: List of building dicts. If None, uses offline data.

    Returns:
        Dict ready for JSON export to Unity.
    """
    if buildings is None:
        buildings = get_building_list()

    entries = []
    for b in buildings:
        category = classify_building(b.get("type_code"))
        height = b.get("height_m", 0.0) or DEFAULT_HEIGHTS.get(category, 6.0)
        footprint = b.get("footprint_m2", 0.0) or 100.0

        # Estimate width from footprint (assume roughly square)
        width = footprint**0.5

        entry = {
            "name": b.get("name", ""),
            "position": {
                "latitude": b["latitude"],
                "longitude": b["longitude"],
            },
            "dimensions": {
                "height": height,
                "width": round(width, 1),
                "footprint_m2": footprint,
            },
            "category": category,
            "prefab": BUILDING_PREFABS.get(category, "BuildingGeneric"),
            "type_code": b.get("type_code", 999),
            "year_built": b.get("year_built"),
            "is_landmark": _is_landmark(b),
        }
        entries.append(entry)

    return {
        "version": "1.0",
        "source": "Kartverket FKB-Bygning (Matrikkelen)",
        "license": "NLOD",
        "bbox": NIDELVA_BBOX,
        "building_count": len(entries),
        "buildings": entries,
    }


def _is_landmark(building: dict) -> bool:
    """Determine if a building is a notable landmark."""
    # Named buildings are landmarks
    if building.get("name"):
        return True
    # Large or tall buildings are landmarks
    if (building.get("height_m") or 0) > 12.0:
        return True
    return (building.get("footprint_m2") or 0) > 500.0


def export_building_json(
    output_path: Path,
    fetch_live: bool = True,
) -> Path:
    """
    Export building data as JSON for Unity.

    Args:
        output_path: Directory to write building_data.json to.
        fetch_live: Whether to attempt live WFS query.

    Returns:
        Path to the exported JSON file.
    """
    buildings = None

    if fetch_live:
        logger.info("Fetching live building data from Kartverket WFS...")
        live_buildings = fetch_buildings()
        if live_buildings:
            buildings = live_buildings
            logger.info(f"Using {len(buildings)} live buildings")
        else:
            logger.info("Live fetch returned no results, using offline data")

    if buildings is None:
        buildings = get_building_list()
        logger.info(f"Using {len(buildings)} offline buildings")

    data = build_building_data(buildings)

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "building_data.json"

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Exported {data['building_count']} buildings to {output_file}")
    print(f"  ✓ Exported {data['building_count']} buildings to {output_file}")

    return output_file


def _safe_float(value: Any) -> float | None:
    """Safely convert a value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value: Any) -> int | None:
    """Safely convert a value to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
