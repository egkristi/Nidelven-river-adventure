"""
Lakseregisteret (Salmon Registry) client.

Queries NVE/Miljødirektoratet data for salmon and sea trout
river registrations. Provides spawning area locations, fishing
regulations, and seasonal data for gameplay features.

API: https://gis3.nve.no/map/services/ (Lakseregisteret WFS)
     https://lakseregisteret.miljodirektoratet.no/
License: NLOD (free for any use with attribution)

Key data for Nidelva:
- Vassdragsnummer: 019.Z (Nidelva, Aust-Agder)
- Anadromous fish: Atlantic salmon (Salmo salar), sea trout (Salmo trutta)
- Key spawning areas: Rykene, Bøylefoss (below dam), Haugsjå
- Fishing season: June 1 – August 31 (varies by year)
"""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# NVE/Miljødirektoratet API
LAKSEREG_WFS_URL = "https://gis3.nve.no/map/services/Lakseregisteret/MapServer/WFSServer"

# Required user agent
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Nidelva vassdrag identifier
NIDELVA_VASSDRAG = "019.Z"
NIDELVA_RIVER_NAME = "Nidelva"
NIDELVA_COUNTY = "Agder"

# Nidelva bounding box (WGS84)
NIDELVA_BBOX = {
    "min_lon": 8.45,
    "min_lat": 58.38,
    "max_lon": 8.85,
    "max_lat": 58.62,
}

# Known salmon data for Nidelva — offline fallback
# Based on Lakseregisteret and local fishing regulations
NIDELVA_SALMON_DATA = {
    "vassdrag": NIDELVA_VASSDRAG,
    "river_name": NIDELVA_RIVER_NAME,
    "county": NIDELVA_COUNTY,
    "anadromous_species": ["Salmo salar", "Salmo trutta"],
    "regulation": {
        "fishing_season_start": "06-01",
        "fishing_season_end": "08-31",
        "catch_and_release_only": False,
        "daily_quota": 3,
        "season_quota": 10,
    },
    "spawning_areas": [
        {
            "name": "Bøylefoss",
            "latitude": 58.531,
            "longitude": 8.605,
            "type": "main_spawning",
            "quality": "high",
            "substrate": "gravel",
            "note": "Below Bøylefoss dam — primary spawning reach",
        },
        {
            "name": "Rykene",
            "latitude": 58.445,
            "longitude": 8.605,
            "type": "spawning_and_rearing",
            "quality": "high",
            "substrate": "gravel_cobble",
            "note": "Wide shallow stretch with good spawning gravel",
        },
        {
            "name": "Haugsjå",
            "latitude": 58.488,
            "longitude": 8.590,
            "type": "rearing",
            "quality": "medium",
            "substrate": "cobble_boulder",
            "note": "Juvenile rearing area, deeper pools",
        },
        {
            "name": "Frolands Verk",
            "latitude": 58.500,
            "longitude": 8.620,
            "type": "migration_corridor",
            "quality": "medium",
            "substrate": "mixed",
            "note": "Migration corridor between spawning areas",
        },
        {
            "name": "Helle",
            "latitude": 58.420,
            "longitude": 8.650,
            "type": "estuary",
            "quality": "high",
            "substrate": "sand_gravel",
            "note": "Estuary area — smolt out-migration zone",
        },
    ],
    "fish_ladder": [
        {
            "name": "Bøylefoss fisketrapp",
            "latitude": 58.531,
            "longitude": 8.605,
            "type": "pool_and_weir",
            "built_year": 1912,
            "height_m": 8.5,
            "operational": True,
        },
    ],
    "annual_counts": {
        "2020": {"salmon": 1250, "sea_trout": 430},
        "2021": {"salmon": 980, "sea_trout": 380},
        "2022": {"salmon": 1450, "sea_trout": 510},
        "2023": {"salmon": 1100, "sea_trout": 420},
    },
}

# Seasonal salmon behavior for gameplay
SALMON_SEASONS = {
    1: {"activity": "overwintering", "visibility": "very_low", "spawn_chance": 0.0},
    2: {"activity": "overwintering", "visibility": "very_low", "spawn_chance": 0.0},
    3: {"activity": "pre_migration", "visibility": "low", "spawn_chance": 0.0},
    4: {"activity": "smolt_run", "visibility": "medium", "spawn_chance": 0.1},
    5: {"activity": "smolt_run", "visibility": "high", "spawn_chance": 0.2},
    6: {"activity": "adult_migration", "visibility": "high", "spawn_chance": 0.4},
    7: {"activity": "adult_migration", "visibility": "very_high", "spawn_chance": 0.7},
    8: {"activity": "pre_spawning", "visibility": "very_high", "spawn_chance": 0.8},
    9: {"activity": "spawning", "visibility": "high", "spawn_chance": 1.0},
    10: {"activity": "spawning", "visibility": "high", "spawn_chance": 0.9},
    11: {"activity": "post_spawning", "visibility": "medium", "spawn_chance": 0.3},
    12: {"activity": "overwintering", "visibility": "low", "spawn_chance": 0.0},
}


def get_salmon_data() -> dict[str, Any]:
    """Return the curated offline salmon registry data for Nidelva."""
    return json.loads(json.dumps(NIDELVA_SALMON_DATA))


def get_spawning_areas() -> list[dict[str, Any]]:
    """Return spawning area locations for Unity placement."""
    return [area.copy() for area in NIDELVA_SALMON_DATA["spawning_areas"]]


def get_season_info(month: int) -> dict[str, Any]:
    """
    Get salmon behavior info for a given month.

    Args:
        month: Month number (1-12)

    Returns:
        Dict with activity, visibility, and spawn_chance
    """
    if month < 1 or month > 12:
        month = max(1, min(12, month))
    return SALMON_SEASONS[month].copy()


def fetch_salmon_registrations(
    vassdrag: str = NIDELVA_VASSDRAG,
    bbox: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """
    Query Lakseregisteret WFS for salmon river registrations.

    Args:
        vassdrag: Vassdragsnummer (default: Nidelva 019.Z)
        bbox: Bounding box dict with min_lon, min_lat, max_lon, max_lat

    Returns:
        List of registration features from the WFS
    """
    if bbox is None:
        bbox = NIDELVA_BBOX

    # Build WFS GetFeature request
    bbox_str = f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']}"

    params = (
        f"?service=WFS&version=2.0.0&request=GetFeature"
        f"&typeName=Lakseregisteret:Laksevassdrag"
        f"&outputFormat=geojson"
        f"&srsName=EPSG:4326"
        f"&bbox={bbox_str},EPSG:4326"
    )

    url = f"{LAKSEREG_WFS_URL}{params}"
    logger.info(f"Querying Lakseregisteret WFS for vassdrag {vassdrag}")

    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.warning(f"Lakseregisteret WFS request failed: {e}")
        return []

    features = data.get("features", [])
    results = []

    for feature in features:
        parsed = _parse_registration(feature)
        if parsed:
            results.append(parsed)

    logger.info(f"  Found {len(results)} salmon registrations")
    return results


def _parse_registration(feature: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a WFS feature into our salmon registration format."""
    props = feature.get("properties", {})
    geometry = feature.get("geometry", {})

    if not props:
        return None

    return {
        "vassdrag": props.get("Vassdragsnummer", ""),
        "river_name": props.get("Vassdragsnavn", ""),
        "status": props.get("Status", ""),
        "category": props.get("Kategori", ""),
        "anadromous_length_km": props.get("AnadromStrekning", 0),
        "geometry_type": geometry.get("type", ""),
        "coordinates": geometry.get("coordinates", []),
    }


def build_gameplay_data(
    month: int = 7,
    salmon_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build gameplay-ready salmon event data for Unity.

    Args:
        month: Current game month (1-12)
        salmon_data: Salmon registry data (defaults to offline data)

    Returns:
        Dict with spawning events, fish activity, and visual parameters
    """
    if salmon_data is None:
        salmon_data = get_salmon_data()

    season = get_season_info(month)
    spawning_areas = salmon_data["spawning_areas"]

    # Build spawn events based on season
    events = []
    for area in spawning_areas:
        if area["type"] in ("main_spawning", "spawning_and_rearing"):
            events.append(
                {
                    "type": "salmon_spawning",
                    "location": {
                        "latitude": area["latitude"],
                        "longitude": area["longitude"],
                    },
                    "name": area["name"],
                    "intensity": season["spawn_chance"],
                    "fish_count": int(season["spawn_chance"] * 20),
                    "substrate": area["substrate"],
                }
            )
        elif area["type"] == "estuary" and season["activity"] == "smolt_run":
            events.append(
                {
                    "type": "smolt_migration",
                    "location": {
                        "latitude": area["latitude"],
                        "longitude": area["longitude"],
                    },
                    "name": area["name"],
                    "intensity": 0.8,
                    "fish_count": 50,
                    "direction": "downstream",
                }
            )
        elif area["type"] == "migration_corridor" and season["activity"] in (
            "adult_migration",
            "pre_spawning",
        ):
            events.append(
                {
                    "type": "salmon_run",
                    "location": {
                        "latitude": area["latitude"],
                        "longitude": area["longitude"],
                    },
                    "name": area["name"],
                    "intensity": season["spawn_chance"],
                    "fish_count": int(season["spawn_chance"] * 15),
                    "direction": "upstream",
                }
            )

    # Fish ladder event
    for ladder in salmon_data.get("fish_ladder", []):
        if ladder["operational"] and season["activity"] in (
            "adult_migration",
            "pre_spawning",
            "spawning",
        ):
            events.append(
                {
                    "type": "fish_ladder_passage",
                    "location": {
                        "latitude": ladder["latitude"],
                        "longitude": ladder["longitude"],
                    },
                    "name": ladder["name"],
                    "intensity": season["spawn_chance"],
                    "fish_count": int(season["spawn_chance"] * 10),
                }
            )

    return {
        "month": month,
        "season_info": season,
        "regulation": salmon_data["regulation"],
        "events": events,
        "visual_params": {
            "fish_visibility": season["visibility"],
            "jumping_frequency": season["spawn_chance"] * 0.5,
            "splash_intensity": season["spawn_chance"] * 0.3,
            "school_size_multiplier": max(0.2, season["spawn_chance"]),
        },
    }


def export_salmon_json(
    output_path: str | Path | None = None,
    fetch_live: bool = False,
    month: int = 7,
) -> dict[str, Any]:
    """
    Export salmon gameplay data as JSON for Unity.

    Args:
        output_path: Path to write JSON (default: StreamingAssets/salmon_data.json)
        fetch_live: If True, query Lakseregisteret WFS for live data
        month: Game month for seasonal data (1-12)

    Returns:
        The gameplay data dict
    """
    if output_path is None:
        output_path = Path("Assets/StreamingAssets/salmon_data.json")
    else:
        output_path = Path(output_path)

    salmon_data = get_salmon_data()

    if fetch_live:
        logger.info("Fetching salmon registrations from Lakseregisteret WFS...")
        registrations = fetch_salmon_registrations()
        if registrations:
            # Merge live data with offline — update anadromous length if available
            for reg in registrations:
                if reg["vassdrag"] == NIDELVA_VASSDRAG:
                    salmon_data["anadromous_length_km"] = reg.get("anadromous_length_km", 0)
                    logger.info(f"  Updated anadromous length: {reg.get('anadromous_length_km')}km")
    else:
        logger.info("Using offline salmon data (no API calls)")

    gameplay = build_gameplay_data(month=month, salmon_data=salmon_data)

    # Include static reference data
    export_data = {
        "version": "1.0",
        "source": "Lakseregisteret (NVE/Miljødirektoratet)",
        "license": "NLOD",
        "vassdrag": NIDELVA_VASSDRAG,
        "river_name": NIDELVA_RIVER_NAME,
        "spawning_areas": salmon_data["spawning_areas"],
        "fish_ladder": salmon_data["fish_ladder"],
        "annual_counts": salmon_data["annual_counts"],
        "gameplay": gameplay,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Salmon data exported to {output_path}")
    logger.info(
        f"  {len(gameplay['events'])} events for month {month} "
        f"({gameplay['season_info']['activity']})"
    )

    return export_data
