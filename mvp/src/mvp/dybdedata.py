"""
Kartverket Dybdedata (bathymetry) client.

Queries Kartverket's depth data services for river/fjord bottom
topography along Nidelva's lower reaches. Provides underwater
terrain for realistic water depth rendering and boat physics.

API: https://wms.geonorge.no/skwms1/wms.dybdedata (WMS)
     https://kartkatalog.geonorge.no/metadata/dybdedata (metadata)
License: NLOD (free for any use with attribution)
Documentation: https://www.kartverket.no/til-sjoes/dybdedata

Coverage for Nidelva:
- Lower Nidelva (estuary): Good bathymetry data (Arendal harbor area)
- Mid-section: Limited (interpolated from cross-sections)
- Upper reaches: No official bathymetry (use terrain-based estimation)
"""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Kartverket Dybdedata WMS
DYBDEDATA_WMS_URL = "https://wms.geonorge.no/skwms1/wms.dybdedata"

# WCS for actual depth grid downloads
DYBDEDATA_WCS_URL = "https://wcs.geonorge.no/skwms1/wcs.dybdedata"

# Required user agent
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Nidelva bounding box — lower section with bathymetry coverage (WGS84)
NIDELVA_ESTUARY_BBOX = {
    "min_lon": 8.72,
    "min_lat": 58.38,
    "max_lon": 8.80,
    "max_lat": 58.43,
}

# Full Nidelva bounding box
NIDELVA_FULL_BBOX = {
    "min_lon": 8.45,
    "min_lat": 58.38,
    "max_lon": 8.85,
    "max_lat": 58.62,
}

# Known depth profiles for Nidelva — offline fallback
# Based on available charted data and cross-section measurements
NIDELVA_DEPTH_PROFILES = [
    {
        "name": "Arendal havn (utløp)",
        "latitude": 58.390,
        "longitude": 8.770,
        "max_depth_m": 12.0,
        "avg_depth_m": 6.5,
        "width_m": 120.0,
        "substrate": "mud_sand",
        "has_official_data": True,
        "section": "estuary",
    },
    {
        "name": "Narestø (nedre elv)",
        "latitude": 58.400,
        "longitude": 8.755,
        "max_depth_m": 8.0,
        "avg_depth_m": 4.0,
        "width_m": 80.0,
        "substrate": "sand_gravel",
        "has_official_data": True,
        "section": "lower",
    },
    {
        "name": "Helle",
        "latitude": 58.420,
        "longitude": 8.650,
        "max_depth_m": 5.0,
        "avg_depth_m": 2.5,
        "width_m": 45.0,
        "substrate": "gravel_cobble",
        "has_official_data": False,
        "section": "mid",
    },
    {
        "name": "Rykene",
        "latitude": 58.445,
        "longitude": 8.605,
        "max_depth_m": 3.5,
        "avg_depth_m": 1.8,
        "width_m": 35.0,
        "substrate": "gravel_cobble",
        "has_official_data": False,
        "section": "mid",
    },
    {
        "name": "Haugsjå",
        "latitude": 58.488,
        "longitude": 8.590,
        "max_depth_m": 6.0,
        "avg_depth_m": 3.0,
        "width_m": 40.0,
        "substrate": "cobble_boulder",
        "has_official_data": False,
        "section": "upper_mid",
    },
    {
        "name": "Frolands Verk",
        "latitude": 58.500,
        "longitude": 8.620,
        "max_depth_m": 4.0,
        "avg_depth_m": 2.2,
        "width_m": 30.0,
        "substrate": "cobble_boulder",
        "has_official_data": False,
        "section": "upper_mid",
    },
    {
        "name": "Bøylefoss (nedenfor dam)",
        "latitude": 58.531,
        "longitude": 8.605,
        "max_depth_m": 8.0,
        "avg_depth_m": 4.5,
        "width_m": 50.0,
        "substrate": "bedrock_boulder",
        "has_official_data": False,
        "section": "upper",
    },
]

# Depth interpolation parameters for river sections without official data
DEPTH_ESTIMATION_PARAMS = {
    "estuary": {"depth_factor": 1.0, "width_factor": 1.0},
    "lower": {"depth_factor": 0.8, "width_factor": 0.7},
    "mid": {"depth_factor": 0.5, "width_factor": 0.4},
    "upper_mid": {"depth_factor": 0.6, "width_factor": 0.35},
    "upper": {"depth_factor": 0.7, "width_factor": 0.45},
}


def get_depth_profiles() -> list[dict[str, Any]]:
    """Return the curated offline depth profiles for Nidelva."""
    return [profile.copy() for profile in NIDELVA_DEPTH_PROFILES]


def get_depth_at_position(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Estimate river depth at a given position by interpolating between
    known cross-section profiles.

    Args:
        latitude: WGS84 latitude
        longitude: WGS84 longitude

    Returns:
        Dict with estimated depth, width, and substrate
    """
    profiles = NIDELVA_DEPTH_PROFILES

    # Find nearest two profiles for interpolation
    distances = []
    for i, p in enumerate(profiles):
        dist = ((p["latitude"] - latitude) ** 2 + (p["longitude"] - longitude) ** 2) ** 0.5
        distances.append((dist, i))

    distances.sort()

    if len(distances) < 2:
        return {"depth_m": 2.0, "width_m": 30.0, "substrate": "unknown"}

    # Linear interpolation between two nearest profiles
    d1, i1 = distances[0]
    d2, i2 = distances[1]
    total = d1 + d2

    w = 0.5 if total == 0 else d2 / total  # Weight: closer profile gets higher weight

    p1 = profiles[i1]
    p2 = profiles[i2]

    return {
        "avg_depth_m": p1["avg_depth_m"] * w + p2["avg_depth_m"] * (1 - w),
        "max_depth_m": p1["max_depth_m"] * w + p2["max_depth_m"] * (1 - w),
        "width_m": p1["width_m"] * w + p2["width_m"] * (1 - w),
        "substrate": p1["substrate"] if w > 0.5 else p2["substrate"],
        "nearest_profile": p1["name"],
    }


def fetch_bathymetry(
    bbox: dict[str, float] | None = None,
    width_px: int = 256,
    height_px: int = 256,
) -> dict[str, Any]:
    """
    Query Kartverket Dybdedata WMS for depth imagery.

    Args:
        bbox: Bounding box (default: Nidelva estuary)
        width_px: Image width in pixels
        height_px: Image height in pixels

    Returns:
        Dict with WMS request metadata and capabilities info
    """
    if bbox is None:
        bbox = NIDELVA_ESTUARY_BBOX

    # WMS GetCapabilities to check available layers
    params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetCapabilities",
    }

    url = f"{DYBDEDATA_WMS_URL}?{urlencode(params)}"
    logger.info("Querying Kartverket Dybdedata WMS capabilities")

    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=15) as response:
            content = response.read().decode("utf-8")
    except Exception as e:
        logger.warning(f"Dybdedata WMS request failed: {e}")
        return {"success": False, "error": str(e), "layers": []}

    # Parse available layer names from GetCapabilities XML
    layers = _extract_layer_names(content)

    # Build GetMap URL for depth data
    bbox_str = f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']}"
    get_map_params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": "dybdedata",
        "styles": "",
        "crs": "EPSG:4326",
        "bbox": bbox_str,
        "width": str(width_px),
        "height": str(height_px),
        "format": "image/png",
    }

    get_map_url = f"{DYBDEDATA_WMS_URL}?{urlencode(get_map_params)}"

    return {
        "success": True,
        "layers": layers,
        "get_map_url": get_map_url,
        "bbox": bbox,
        "resolution_m": _estimate_resolution(bbox, width_px, height_px),
    }


def _extract_layer_names(capabilities_xml: str) -> list[str]:
    """Extract layer names from WMS GetCapabilities XML (simple parsing)."""
    layers = []
    # Simple regex-free extraction
    parts = capabilities_xml.split("<Name>")
    for part in parts[1:]:  # Skip first split (before first <Name>)
        end = part.find("</Name>")
        if end > 0:
            name = part[:end].strip()
            if name and len(name) < 100:
                layers.append(name)
    return layers[:20]  # Cap at 20 layers


def _estimate_resolution(bbox: dict[str, float], width_px: int, height_px: int) -> float:
    """Estimate spatial resolution in meters for the given request."""
    # Approximate degrees to meters at 58°N latitude
    lat_range = bbox["max_lat"] - bbox["min_lat"]
    lon_range = bbox["max_lon"] - bbox["min_lon"]
    lat_m = lat_range * 111320  # meters per degree latitude
    lon_m = lon_range * 111320 * 0.53  # cos(58°) ≈ 0.53
    avg_m = (lat_m / height_px + lon_m / width_px) / 2
    return round(avg_m, 1)


def build_depth_grid(
    profiles: list[dict[str, Any]] | None = None,
    grid_points: int = 50,
) -> dict[str, Any]:
    """
    Build a simplified depth grid along the river path for Unity.

    Interpolates between known cross-section profiles to create
    a continuous depth model for buoyancy physics and underwater rendering.

    Args:
        profiles: Depth profiles (defaults to offline data)
        grid_points: Number of interpolation points along river

    Returns:
        Dict with depth_grid array for Unity TerrainGenerator
    """
    if profiles is None:
        profiles = NIDELVA_DEPTH_PROFILES

    # Sort profiles by latitude (upstream to downstream)
    sorted_profiles = sorted(profiles, key=lambda p: -p["latitude"])

    grid = []
    for i in range(grid_points):
        t = i / max(1, grid_points - 1)

        # Find surrounding profiles
        profile_idx = t * (len(sorted_profiles) - 1)
        idx_low = int(profile_idx)
        idx_high = min(idx_low + 1, len(sorted_profiles) - 1)
        frac = profile_idx - idx_low

        p_low = sorted_profiles[idx_low]
        p_high = sorted_profiles[idx_high]

        # Interpolate
        lat = p_low["latitude"] * (1 - frac) + p_high["latitude"] * frac
        lon = p_low["longitude"] * (1 - frac) + p_high["longitude"] * frac
        depth = p_low["avg_depth_m"] * (1 - frac) + p_high["avg_depth_m"] * frac
        max_depth = p_low["max_depth_m"] * (1 - frac) + p_high["max_depth_m"] * frac
        width = p_low["width_m"] * (1 - frac) + p_high["width_m"] * frac

        grid.append(
            {
                "index": i,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "avg_depth_m": round(depth, 2),
                "max_depth_m": round(max_depth, 2),
                "width_m": round(width, 1),
                "t": round(t, 4),
            }
        )

    return {
        "grid_points": grid_points,
        "profiles_used": len(sorted_profiles),
        "depth_range_m": {
            "min": min(p["avg_depth_m"] for p in sorted_profiles),
            "max": max(p["max_depth_m"] for p in sorted_profiles),
        },
        "grid": grid,
    }


def export_bathymetry_json(
    output_path: str | Path | None = None,
    fetch_live: bool = False,
    grid_points: int = 50,
) -> dict[str, Any]:
    """
    Export bathymetry data as JSON for Unity.

    Args:
        output_path: Path to write JSON (default: StreamingAssets/bathymetry.json)
        fetch_live: If True, query Kartverket WMS for capabilities check
        grid_points: Number of interpolation points in depth grid

    Returns:
        The exported data dict
    """
    if output_path is None:
        output_path = Path("Assets/StreamingAssets/bathymetry.json")
    else:
        output_path = Path(output_path)

    profiles = get_depth_profiles()
    wms_info: dict[str, Any] = {}

    if fetch_live:
        logger.info("Checking Kartverket Dybdedata WMS availability...")
        wms_info = fetch_bathymetry()
        if wms_info.get("success"):
            logger.info(f"  WMS available, {len(wms_info.get('layers', []))} layers")
        else:
            logger.warning(f"  WMS unavailable: {wms_info.get('error', 'unknown')}")
    else:
        logger.info("Using offline bathymetry profiles (no API calls)")

    depth_grid = build_depth_grid(profiles=profiles, grid_points=grid_points)

    export_data = {
        "version": "1.0",
        "source": "Kartverket Dybdedata + estimated cross-sections",
        "license": "NLOD",
        "coverage": {
            "official_bathymetry": "estuary only (Arendal harbor area)",
            "estimated": "mid and upper sections (interpolated from known profiles)",
        },
        "profiles": profiles,
        "depth_grid": depth_grid,
        "wms_info": wms_info if wms_info else None,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Bathymetry data exported to {output_path}")
    logger.info(
        f"  {len(profiles)} profiles, {grid_points} grid points, "
        f"depth range: {depth_grid['depth_range_m']['min']}-"
        f"{depth_grid['depth_range_m']['max']}m"
    )

    return export_data
