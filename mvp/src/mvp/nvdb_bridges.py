"""
NVDB (Nasjonal Vegdatabank) bridge client.

Queries NVDB API V4 for bridge objects crossing Nidelva.
Provides bridge positions, dimensions, and types for placing
recognizable landmarks and navigation obstacles in Unity.

API: https://nvdbapiles.atlas.vegvesen.no/
License: NLOD (free for any use with attribution)
Documentation: https://nvdbapiles-v4.atlas.vegvesen.no/dokumentasjon/

Bridge object type: 60 (Bru)
Key properties:
- Navn (name)
- Lengde (length in meters)
- Breddeklasse (width class)
- Byggeår (construction year)
- Seilingshøyde (clearance height for boats)
"""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# NVDB API V4 base URL
NVDB_API_URL = "https://nvdbapiles-v4.atlas.vegvesen.no"

# Required headers
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"
NVDB_CLIENT = "Nidelven River Adventure"

# Nidelva bounding box (Agder, Norway) — WGS84
NIDELVA_BBOX = {
    "min_lon": 8.45,
    "min_lat": 58.38,
    "max_lon": 8.85,
    "max_lat": 58.62,
}

# NVDB object type IDs
OBJTYPE_BRIDGE = 60  # Bru
OBJTYPE_TUNNEL = 67  # Tunnel
OBJTYPE_FERRY = 64  # Ferjekai

# Known bridges on Nidelva (Agder) — offline fallback data
# Based on documented road infrastructure crossings
NIDELVA_BRIDGES = [
    {
        "name": "Rykene bru",
        "road": "FV42",
        "latitude": 58.445,
        "longitude": 8.605,
        "length_m": 85.0,
        "width_m": 8.5,
        "clearance_m": 5.0,
        "year_built": 1985,
        "bridge_type": "beam",
        "material": "concrete",
    },
    {
        "name": "Helle bru",
        "road": "E18",
        "latitude": 58.432,
        "longitude": 8.655,
        "length_m": 120.0,
        "width_m": 12.0,
        "clearance_m": 6.5,
        "year_built": 1978,
        "bridge_type": "beam",
        "material": "concrete",
    },
    {
        "name": "Jernbanebru Nidelva",
        "road": "Sørlandsbanen",
        "latitude": 58.438,
        "longitude": 8.635,
        "length_m": 95.0,
        "width_m": 6.0,
        "clearance_m": 4.5,
        "year_built": 1938,
        "bridge_type": "arch",
        "material": "stone",
    },
    {
        "name": "Bøylefoss bru",
        "road": "FV415",
        "latitude": 58.520,
        "longitude": 8.565,
        "length_m": 65.0,
        "width_m": 7.0,
        "clearance_m": 4.0,
        "year_built": 1960,
        "bridge_type": "beam",
        "material": "concrete",
    },
    {
        "name": "Froland bru",
        "road": "FV42",
        "latitude": 58.505,
        "longitude": 8.575,
        "length_m": 72.0,
        "width_m": 8.0,
        "clearance_m": 5.5,
        "year_built": 1992,
        "bridge_type": "beam",
        "material": "concrete",
    },
]

# Bridge type mapping for Unity prefab selection
BRIDGE_PREFABS = {
    "beam": "BridgeBeam",
    "arch": "BridgeArch",
    "suspension": "BridgeSuspension",
    "truss": "BridgeTruss",
    "unknown": "BridgeBeam",
}


def get_bridge_list() -> list[dict]:
    """Get the offline bridge list for Nidelva.

    Returns:
        List of bridge dicts with position, dimensions, and metadata.
    """
    return NIDELVA_BRIDGES.copy()


def fetch_bridges(
    bbox: dict | None = None,
    objtype: int = OBJTYPE_BRIDGE,
) -> list[dict[str, Any]]:
    """Fetch bridge objects from NVDB API V4.

    Args:
        bbox: Bounding box dict with min_lon, min_lat, max_lon, max_lat.
              Defaults to NIDELVA_BBOX.
        objtype: NVDB object type ID (default: 60 for bridges).

    Returns:
        List of bridge records with geometry and properties.
    """
    if bbox is None:
        bbox = NIDELVA_BBOX

    # NVDB uses kartutsnitt parameter for bbox filtering
    kartutsnitt = f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"

    params = {
        "kartutsnitt": kartutsnitt,
        "srid": "4326",
        "inkluder": "egenskaper,geometri,lokasjon",
    }

    url = f"{NVDB_API_URL}/vegobjekter/{objtype}?{urlencode(params)}"
    logger.info(f"Fetching bridges from NVDB: {url}")

    try:
        req = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "X-Client": NVDB_CLIENT,
                "Accept": "application/vnd.vegvesen.nvdb-v4-rev1+json",
            },
        )
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        objects = data.get("objekter", [])
        logger.info(f"Got {len(objects)} bridge objects from NVDB")

        bridges = []
        for obj in objects:
            bridge = _parse_nvdb_bridge(obj)
            if bridge:
                bridges.append(bridge)

        return bridges

    except Exception as e:
        logger.warning(f"NVDB API request failed: {e}")
        return []


def _parse_nvdb_bridge(obj: dict) -> dict | None:
    """Parse a single NVDB bridge object into our format.

    Args:
        obj: Raw NVDB object dict.

    Returns:
        Parsed bridge dict or None if invalid.
    """
    props = {}
    for egenskap in obj.get("egenskaper", []):
        props[egenskap.get("navn", "")] = egenskap.get("verdi")

    # Extract geometry
    geometri = obj.get("geometri", {})
    wkt = geometri.get("wkt", "")

    # Try to get centroid from lokasjon
    lokasjon = obj.get("lokasjon", {})
    geometri_punkt = lokasjon.get("geometri", {})

    lat, lon = None, None
    if geometri_punkt:
        # lokasjon.geometri may contain a point
        srid = geometri_punkt.get("srid", 4326)
        if srid == 4326 and "koordinater" in geometri_punkt:
            coords = geometri_punkt["koordinater"]
            if coords:
                lon, lat = coords[0], coords[1] if len(coords) > 1 else (None, None)

    # Fallback: parse from WKT if available
    if (lat is None or lon is None) and wkt:
        lat, lon = _parse_wkt_centroid(wkt)

    if lat is None or lon is None:
        return None

    name = props.get("Navn", props.get("navn", f"Bru {obj.get('id', 'ukjent')}"))
    length_m = _safe_float(props.get("Lengde", props.get("Totallengde")))
    width_m = _safe_float(props.get("Bredde"))
    clearance_m = _safe_float(props.get("Seilingshøyde"))
    year_built = _safe_int(props.get("Byggeår"))

    return {
        "name": name,
        "road": props.get("Vegreferanse", ""),
        "latitude": lat,
        "longitude": lon,
        "length_m": length_m or 50.0,
        "width_m": width_m or 8.0,
        "clearance_m": clearance_m or 5.0,
        "year_built": year_built,
        "bridge_type": _classify_bridge_type(props),
        "material": props.get("Materiale", "concrete").lower(),
        "nvdb_id": obj.get("id"),
    }


def _parse_wkt_centroid(wkt: str) -> tuple[float | None, float | None]:
    """Extract approximate centroid from a WKT geometry string."""
    import re

    # Find all coordinate pairs (lon lat)
    coords = re.findall(r"([\d.]+)\s+([\d.]+)", wkt)
    if not coords:
        return None, None

    lons = [float(c[0]) for c in coords]
    lats = [float(c[1]) for c in coords]

    return sum(lats) / len(lats), sum(lons) / len(lons)


def _classify_bridge_type(props: dict) -> str:
    """Classify bridge type from NVDB properties."""
    konstruksjon = str(props.get("Konstruksjon", "")).lower()
    if "bue" in konstruksjon or "hvelv" in konstruksjon:
        return "arch"
    if "henge" in konstruksjon:
        return "suspension"
    if "fagverk" in konstruksjon:
        return "truss"
    return "beam"


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


def build_bridge_data(bridges: list[dict] | None = None) -> dict[str, Any]:
    """Convert bridge list into Unity-ready format.

    Args:
        bridges: List of bridge dicts. If None, uses offline NIDELVA_BRIDGES.

    Returns:
        Dict ready for JSON export to Unity.
    """
    if bridges is None:
        bridges = NIDELVA_BRIDGES

    bridge_entries = []
    for bridge in bridges:
        prefab = BRIDGE_PREFABS.get(bridge.get("bridge_type", "beam"), "BridgeBeam")

        # Calculate rotation (bridges are perpendicular to river flow)
        # Default to 90° — Unity will align to terrain normal
        bridge_entries.append(
            {
                "name": bridge["name"],
                "position": {
                    "latitude": bridge["latitude"],
                    "longitude": bridge["longitude"],
                },
                "dimensions": {
                    "length": bridge.get("length_m", 50.0),
                    "width": bridge.get("width_m", 8.0),
                    "clearance": bridge.get("clearance_m", 5.0),
                },
                "prefab": prefab,
                "material": bridge.get("material", "concrete"),
                "road": bridge.get("road", ""),
                "year_built": bridge.get("year_built"),
                "is_obstacle": bridge.get("clearance_m", 5.0) < 3.0,
            }
        )

    return {
        "version": "1.0",
        "source": "NVDB (Statens vegvesen)",
        "license": "NLOD",
        "bbox": NIDELVA_BBOX,
        "bridge_count": len(bridge_entries),
        "bridges": bridge_entries,
    }


def export_bridge_json(
    output_path: Path,
    fetch_live: bool = False,
) -> Path:
    """Export bridge data as JSON for Unity.

    Args:
        output_path: Output directory.
        fetch_live: If True, attempt to fetch from NVDB API first.

    Returns:
        Path to the exported JSON file.
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "bridge_data.json"

    bridges = None

    if fetch_live:
        logger.info("Fetching live bridge data from NVDB...")
        bridges = fetch_bridges()
        if not bridges:
            logger.info("  No live data, using offline fallback")
            bridges = NIDELVA_BRIDGES
    else:
        logger.info("Using offline bridge data for Nidelva")
        bridges = NIDELVA_BRIDGES

    bridge_data = build_bridge_data(bridges)

    with open(json_path, "w") as f:
        json.dump(bridge_data, f, indent=2)

    print(f"  ✓ Bridge data exported: {json_path}")
    print(f"    {bridge_data['bridge_count']} bridges along Nidelva")
    for bridge in bridge_data["bridges"]:
        obstacle = " [OBSTACLE]" if bridge["is_obstacle"] else ""
        print(
            f"    - {bridge['name']} ({bridge['road']}, {bridge['dimensions']['length']:.0f}m){obstacle}"
        )

    return json_path
