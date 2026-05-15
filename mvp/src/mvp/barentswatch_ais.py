"""
Barentswatch AIS (Automatic Identification System) client.

Provides vessel traffic data near Arendal harbor at the mouth
of Nidelva for ambient ship animations in Unity.

API: https://ais.barentswatch.no/
License: Open (delayed public data, 3-min delay)

Vessel types (AIS ShipType codes):
- 30: Fishing
- 60-69: Passenger (ferries)
- 70-79: Cargo
- 80-89: Tanker
- 36-37: Sailing/Pleasure craft
"""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Barentswatch AIS API
AIS_API_URL = "https://live.ais.barentswatch.no/v1/combined"
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Arendal harbor / Nidelva estuary area — WGS84
ARENDAL_HARBOR_BBOX = {
    "min_lon": 8.72,
    "min_lat": 58.44,
    "max_lon": 8.80,
    "max_lat": 58.47,
}

# AIS vessel type ranges
VESSEL_TYPES = {
    "fishing": {"codes": range(30, 33), "prefab": "VesselFishing"},
    "cargo": {"codes": range(70, 80), "prefab": "VesselCargo"},
    "tanker": {"codes": range(80, 90), "prefab": "VesselTanker"},
    "passenger": {"codes": range(60, 70), "prefab": "VesselPassenger"},
    "sailing": {"codes": range(36, 38), "prefab": "VesselSailing"},
    "pleasure": {"codes": [37], "prefab": "VesselPleasure"},
    "tug": {"codes": range(31, 33), "prefab": "VesselTug"},
}

# Offline curated vessel traffic patterns at Arendal harbor
# Based on typical maritime activity for a Norwegian coastal town
ARENDAL_VESSEL_TRAFFIC = [
    {
        "name": "Arendal-Hisøy ferge",
        "vessel_type": "passenger",
        "mmsi": "258000001",
        "latitude": 58.462,
        "longitude": 8.768,
        "heading": 180.0,
        "speed_knots": 8.0,
        "length_m": 25.0,
        "route": "harbor_ferry",
        "frequency": "high",
        "description": "Local passenger ferry crossing Galtesund",
    },
    {
        "name": "Fiskebåt Nidelva",
        "vessel_type": "fishing",
        "mmsi": "258000002",
        "latitude": 58.455,
        "longitude": 8.775,
        "heading": 270.0,
        "speed_knots": 5.0,
        "length_m": 12.0,
        "route": "estuary_patrol",
        "frequency": "medium",
        "description": "Small fishing vessel near river mouth",
    },
    {
        "name": "MS Øya",
        "vessel_type": "passenger",
        "mmsi": "258000003",
        "latitude": 58.460,
        "longitude": 8.760,
        "heading": 90.0,
        "speed_knots": 10.0,
        "length_m": 30.0,
        "route": "island_service",
        "frequency": "medium",
        "description": "Island ferry serving Merdø and Sandvigen",
    },
    {
        "name": "Cargo vessel Arendal",
        "vessel_type": "cargo",
        "mmsi": "258000004",
        "latitude": 58.458,
        "longitude": 8.780,
        "heading": 0.0,
        "speed_knots": 3.0,
        "length_m": 85.0,
        "route": "harbor_approach",
        "frequency": "low",
        "description": "Cargo ship approaching Arendal port",
    },
    {
        "name": "Seilbåt Tromøysund",
        "vessel_type": "sailing",
        "mmsi": "258000005",
        "latitude": 58.465,
        "longitude": 8.755,
        "heading": 135.0,
        "speed_knots": 4.0,
        "length_m": 10.0,
        "route": "leisure",
        "frequency": "seasonal",
        "description": "Pleasure sailing craft in Tromøysund",
    },
]

# Route patterns for Unity vessel animation
ROUTE_PATTERNS = {
    "harbor_ferry": {
        "waypoints": [
            {"lat": 58.462, "lon": 8.768},
            {"lat": 58.458, "lon": 8.772},
            {"lat": 58.462, "lon": 8.768},
        ],
        "loop": True,
        "interval_minutes": 15,
    },
    "estuary_patrol": {
        "waypoints": [
            {"lat": 58.455, "lon": 8.775},
            {"lat": 58.450, "lon": 8.770},
            {"lat": 58.448, "lon": 8.765},
            {"lat": 58.455, "lon": 8.775},
        ],
        "loop": True,
        "interval_minutes": 45,
    },
    "island_service": {
        "waypoints": [
            {"lat": 58.460, "lon": 8.760},
            {"lat": 58.470, "lon": 8.750},
            {"lat": 58.460, "lon": 8.760},
        ],
        "loop": True,
        "interval_minutes": 60,
    },
    "harbor_approach": {
        "waypoints": [
            {"lat": 58.450, "lon": 8.800},
            {"lat": 58.458, "lon": 8.780},
            {"lat": 58.460, "lon": 8.770},
        ],
        "loop": False,
        "interval_minutes": 240,
    },
    "leisure": {
        "waypoints": [
            {"lat": 58.465, "lon": 8.755},
            {"lat": 58.468, "lon": 8.740},
            {"lat": 58.465, "lon": 8.755},
        ],
        "loop": True,
        "interval_minutes": 90,
    },
}

# Frequency to spawn probability mapping
FREQUENCY_WEIGHTS = {
    "high": 0.8,
    "medium": 0.5,
    "low": 0.2,
    "seasonal": 0.3,
}


def get_vessel_traffic() -> list[dict]:
    """Get offline vessel traffic data for Arendal harbor.

    Returns:
        List of vessel dicts with position, type, and route data.
    """
    return ARENDAL_VESSEL_TRAFFIC.copy()


def classify_vessel_type(ship_type_code: int) -> str:
    """Classify AIS ship type code into category.

    Args:
        ship_type_code: AIS ship type number (0-99).

    Returns:
        Category string: fishing, cargo, tanker, passenger, sailing, or unknown.
    """
    for category, info in VESSEL_TYPES.items():
        if ship_type_code in info["codes"]:
            return category
    return "unknown"


def get_vessel_prefab(vessel_type: str) -> str:
    """Get Unity prefab name for a vessel type.

    Args:
        vessel_type: Vessel category string.

    Returns:
        Unity prefab name.
    """
    for category, info in VESSEL_TYPES.items():
        if category == vessel_type:
            return info["prefab"]
    return "VesselGeneric"


def fetch_ais_data(
    bbox: dict | None = None,
) -> list[dict[str, Any]]:
    """Fetch vessel positions from Barentswatch AIS API.

    Note: Requires authentication (client_id + client_secret).
    Falls back to offline data if API is unavailable.

    Args:
        bbox: Bounding box dict. Defaults to ARENDAL_HARBOR_BBOX.

    Returns:
        List of AIS vessel records.
    """
    if bbox is None:
        bbox = ARENDAL_HARBOR_BBOX

    params = {
        "Xmin": bbox["min_lon"],
        "Ymin": bbox["min_lat"],
        "Xmax": bbox["max_lon"],
        "Ymax": bbox["max_lat"],
    }

    url = f"{AIS_API_URL}?{urlencode(params)}"

    try:
        req = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
        )
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        vessels = []
        if isinstance(data, list):
            for record in data:
                vessel = {
                    "name": record.get("name", "Unknown"),
                    "mmsi": str(record.get("mmsi", "")),
                    "vessel_type": classify_vessel_type(_safe_int(record.get("shipType", 0))),
                    "latitude": _safe_float(record.get("latitude", 0)),
                    "longitude": _safe_float(record.get("longitude", 0)),
                    "heading": _safe_float(record.get("courseOverGround", 0)),
                    "speed_knots": _safe_float(record.get("speedOverGround", 0)),
                    "length_m": _safe_float(record.get("shipLength", 0)),
                }
                vessels.append(vessel)

        logger.info(f"  Fetched {len(vessels)} vessels from Barentswatch AIS")
        return vessels
    except Exception as e:
        logger.warning(f"AIS API request failed: {e}")
        return []


def build_vessel_traffic_data(
    vessels: list[dict] | None = None,
) -> dict[str, Any]:
    """Build Unity-ready vessel traffic data.

    Args:
        vessels: List of vessel dicts. Uses offline data if None.

    Returns:
        Dict with vessel list, route patterns, and spawn config.
    """
    if vessels is None:
        vessels = ARENDAL_VESSEL_TRAFFIC

    vessel_entries = []
    for v in vessels:
        route_name = v.get("route", "leisure")
        route = ROUTE_PATTERNS.get(route_name, ROUTE_PATTERNS["leisure"])
        freq = v.get("frequency", "medium")

        entry = {
            "name": v.get("name", "Unknown Vessel"),
            "vessel_type": v.get("vessel_type", "unknown"),
            "prefab": get_vessel_prefab(v.get("vessel_type", "unknown")),
            "position": {
                "latitude": v.get("latitude", 0),
                "longitude": v.get("longitude", 0),
            },
            "heading": v.get("heading", 0),
            "speed_knots": v.get("speed_knots", 0),
            "length_m": v.get("length_m", 10),
            "route": {
                "name": route_name,
                "waypoints": route["waypoints"],
                "loop": route["loop"],
                "interval_minutes": route["interval_minutes"],
            },
            "spawn_probability": FREQUENCY_WEIGHTS.get(freq, 0.3),
            "description": v.get("description", ""),
        }
        vessel_entries.append(entry)

    # Category summary
    type_counts: dict[str, int] = {}
    for v in vessel_entries:
        t = v["vessel_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "source": "Barentswatch AIS / offline curated",
        "license": "Open (delayed public data)",
        "area": "Arendal harbor / Nidelva estuary",
        "bbox": ARENDAL_HARBOR_BBOX,
        "vessel_count": len(vessel_entries),
        "type_summary": type_counts,
        "vessels": vessel_entries,
        "route_patterns": ROUTE_PATTERNS,
    }


def export_vessel_traffic_json(
    output_path: Path,
    fetch_live: bool = False,
) -> Path:
    """Export vessel traffic data as JSON for Unity.

    Args:
        output_path: Output directory.
        fetch_live: If True, attempt to fetch from Barentswatch API first.

    Returns:
        Path to the exported JSON file.
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "vessel_traffic.json"

    vessels = None

    if fetch_live:
        logger.info("Fetching live AIS data from Barentswatch...")
        live_vessels = fetch_ais_data()
        if live_vessels:
            vessels = live_vessels
        else:
            logger.info("  No live AIS data, using offline fallback")

    traffic_data = build_vessel_traffic_data(vessels)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(traffic_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Vessel traffic exported: {json_path}")
    print(f"    {traffic_data['vessel_count']} vessels in Arendal harbor area")
    for v in traffic_data["vessels"]:
        print(f"    - {v['name']} ({v['vessel_type']}, {v['length_m']:.0f}m)")

    return json_path


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely convert a value to int."""
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default
