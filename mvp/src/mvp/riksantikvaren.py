"""
Riksantikvaren Askeladden cultural heritage client.

Queries cultural heritage sites along Nidelva from the national
heritage database for discovery gameplay and info panels.

API: https://askeladden.ra.no/ (WMS free, details require login)
License: NLOD (free for any use with attribution)

Heritage categories:
- Industrial: mills, dams, power stations, forges
- Religious: churches, chapels, burial grounds
- Agricultural: farms, barns, granaries
- Maritime: wharves, boathouses, lighthouses
- Residential: manor houses, cottages
"""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Riksantikvaren Askeladden WMS/API
ASKELADDEN_WMS_URL = (
    "https://kart.ra.no/arcgis/services/Kulturminner/Kulturminner/MapServer/WMSServer"
)
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Nidelva bounding box (Agder, Norway) — WGS84
NIDELVA_BBOX = {
    "min_lon": 8.45,
    "min_lat": 58.38,
    "max_lon": 8.85,
    "max_lat": 58.62,
}

# Heritage category mapping for Unity POI types
HERITAGE_CATEGORIES = {
    "industrial": {
        "icon": "POI_Industrial",
        "color": "#8B4513",
        "description": "Industrial heritage — mills, forges, power stations",
    },
    "religious": {
        "icon": "POI_Religious",
        "color": "#DAA520",
        "description": "Religious heritage — churches, chapels",
    },
    "agricultural": {
        "icon": "POI_Agricultural",
        "color": "#228B22",
        "description": "Agricultural heritage — farms, barns",
    },
    "maritime": {
        "icon": "POI_Maritime",
        "color": "#4169E1",
        "description": "Maritime heritage — wharves, boathouses",
    },
    "residential": {
        "icon": "POI_Residential",
        "color": "#CD853F",
        "description": "Residential heritage — manor houses, cottages",
    },
    "transport": {
        "icon": "POI_Transport",
        "color": "#696969",
        "description": "Transport heritage — bridges, roads, railways",
    },
}

# Offline curated heritage sites along Nidelva
# Based on documented historical sites in the Nidelva valley
NIDELVA_HERITAGE_SITES = [
    {
        "name": "Bøylefoss kraftstasjon",
        "category": "industrial",
        "latitude": 58.531,
        "longitude": 8.605,
        "year_built": 1913,
        "protected": True,
        "description": "Hydroelectric power station built 1913. One of the earliest "
        "power plants on Nidelva. Landmark industrial architecture.",
        "info_url": "https://no.wikipedia.org/wiki/Bøylefoss_kraftstasjon",
    },
    {
        "name": "Rykene kraftstasjon",
        "category": "industrial",
        "latitude": 58.445,
        "longitude": 8.605,
        "year_built": 1896,
        "protected": True,
        "description": "Historic power station from 1896, among the oldest in Norway. "
        "Powered Arendal as one of the first electric cities in the country.",
        "info_url": "https://no.wikipedia.org/wiki/Rykene_kraftstasjon",
    },
    {
        "name": "Froland jernverk",
        "category": "industrial",
        "latitude": 58.505,
        "longitude": 8.575,
        "year_built": 1763,
        "protected": True,
        "description": "Iron works established 1763. Significant part of Agder's "
        "industrial history. Used Nidelva for water power and transport.",
        "info_url": "https://no.wikipedia.org/wiki/Frolands_Jernverk",
    },
    {
        "name": "Froland kirke",
        "category": "religious",
        "latitude": 58.508,
        "longitude": 8.580,
        "year_built": 1637,
        "protected": True,
        "description": "Timber church built 1637, rebuilt in stone 1796. "
        "Listed building overlooking the Nidelva valley.",
        "info_url": "https://no.wikipedia.org/wiki/Froland_kirke",
    },
    {
        "name": "Helle gård",
        "category": "agricultural",
        "latitude": 58.440,
        "longitude": 8.650,
        "year_built": 1750,
        "protected": False,
        "description": "Historic farm along Nidelva. Traditional Agder architecture "
        "with main house, barn, and storehouse from the 18th century.",
    },
    {
        "name": "Bøylefoss fisketrapp",
        "category": "industrial",
        "latitude": 58.530,
        "longitude": 8.607,
        "year_built": 1912,
        "protected": True,
        "description": "Fish ladder built 1912 to allow Atlantic salmon passage past "
        "the Bøylefoss dam. One of Norway's oldest operational fish ladders.",
        "info_url": "https://no.wikipedia.org/wiki/Bøylefoss",
    },
    {
        "name": "Nes Jernverk",
        "category": "industrial",
        "latitude": 58.475,
        "longitude": 8.590,
        "year_built": 1665,
        "protected": True,
        "description": "Iron works founded 1665 by Ove Giedde. Used Nidelva water "
        "power for smelting. Important part of Agder's mining heritage.",
        "info_url": "https://no.wikipedia.org/wiki/Nes_Jernverk",
    },
    {
        "name": "Arendal bryggeanlegg",
        "category": "maritime",
        "latitude": 58.461,
        "longitude": 8.769,
        "year_built": 1800,
        "protected": True,
        "description": "Historic wooden wharf district at the mouth of Nidelva. "
        "Timber export heritage from the sailing ship era (1700-1900).",
    },
]


def get_heritage_sites() -> list[dict]:
    """Get offline heritage site list for Nidelva.

    Returns:
        List of heritage site dicts with position, category, and metadata.
    """
    return NIDELVA_HERITAGE_SITES.copy()


def classify_heritage(site_type: str) -> str:
    """Classify a heritage site type string into a standard category.

    Args:
        site_type: Heritage type description from API response.

    Returns:
        Category string: industrial, religious, agricultural, maritime,
        residential, transport, or unknown.
    """
    site_type_lower = (site_type or "").lower()

    industrial_keywords = [
        "kraft",
        "jernverk",
        "mølle",
        "sag",
        "dam",
        "fabrikk",
        "smie",
        "trapp",
        "industri",
    ]
    religious_keywords = ["kirke", "kapell", "gravplass", "kirkegård"]
    agricultural_keywords = ["gård", "gard", "låve", "stabbur", "kvern"]
    maritime_keywords = ["brygge", "naust", "kai", "sjøhus", "fyr", "havn"]
    transport_keywords = ["bru", "vei", "bane", "stasjon"]
    residential_keywords = ["hus", "bolig", "herregård", "stue"]

    for kw in industrial_keywords:
        if kw in site_type_lower:
            return "industrial"
    for kw in religious_keywords:
        if kw in site_type_lower:
            return "religious"
    for kw in maritime_keywords:
        if kw in site_type_lower:
            return "maritime"
    for kw in agricultural_keywords:
        if kw in site_type_lower:
            return "agricultural"
    for kw in transport_keywords:
        if kw in site_type_lower:
            return "transport"
    for kw in residential_keywords:
        if kw in site_type_lower:
            return "residential"
    return "unknown"


def get_heritage_icon(category: str) -> str:
    """Get Unity POI icon name for a heritage category.

    Args:
        category: Heritage category string.

    Returns:
        Unity icon/prefab name.
    """
    cat_info = HERITAGE_CATEGORIES.get(category)
    if cat_info:
        return cat_info["icon"]
    return "POI_Generic"


def fetch_heritage_sites(
    bbox: dict | None = None,
) -> list[dict[str, Any]]:
    """Fetch heritage sites from Riksantikvaren WMS GetFeatureInfo.

    Note: Full Askeladden data requires authenticated access.
    This uses the public WMS for basic feature detection.

    Args:
        bbox: Bounding box dict. Defaults to NIDELVA_BBOX.

    Returns:
        List of heritage site records.
    """
    if bbox is None:
        bbox = NIDELVA_BBOX

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": "0",
        "SRS": "EPSG:4326",
        "BBOX": f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']}",
        "WIDTH": "256",
        "HEIGHT": "256",
        "FORMAT": "application/json",
    }

    url = f"{ASKELADDEN_WMS_URL}?{urlencode(params)}"

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

        sites = []
        features = data.get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [0, 0])

            site = {
                "name": props.get("Navn", props.get("navn", "Ukjent")),
                "category": classify_heritage(props.get("Kategori", "")),
                "latitude": _safe_float(coords[1] if len(coords) > 1 else 0),
                "longitude": _safe_float(coords[0] if len(coords) > 0 else 0),
                "year_built": _safe_int(props.get("Datering", 0)),
                "protected": bool(props.get("Fredet", False)),
                "description": props.get("Beskrivelse", ""),
            }
            sites.append(site)

        logger.info(f"  Fetched {len(sites)} heritage sites from Riksantikvaren")
        return sites
    except Exception as e:
        logger.warning(f"Askeladden WMS request failed: {e}")
        return []


def build_heritage_data(
    sites: list[dict] | None = None,
) -> dict[str, Any]:
    """Build Unity-ready heritage POI data.

    Args:
        sites: List of heritage site dicts. Uses offline data if None.

    Returns:
        Dict with site list, categories, and POI config.
    """
    if sites is None:
        sites = NIDELVA_HERITAGE_SITES

    site_entries = []
    for s in sites:
        category = s.get("category", "unknown")
        entry = {
            "name": s.get("name", "Ukjent kulturminne"),
            "category": category,
            "icon": get_heritage_icon(category),
            "position": {
                "latitude": s.get("latitude", 0),
                "longitude": s.get("longitude", 0),
            },
            "year_built": s.get("year_built", 0),
            "protected": s.get("protected", False),
            "description": s.get("description", ""),
            "info_url": s.get("info_url", ""),
            "discovery_radius_m": 100.0 if s.get("protected", False) else 50.0,
            "poi_visible_distance_m": 500.0,
        }
        site_entries.append(entry)

    # Category summary
    cat_counts: dict[str, int] = {}
    for s in site_entries:
        c = s["category"]
        cat_counts[c] = cat_counts.get(c, 0) + 1

    protected_count = sum(1 for s in site_entries if s["protected"])

    return {
        "source": "Riksantikvaren Askeladden / offline curated",
        "license": "NLOD (free for any use with attribution)",
        "area": "Nidelva valley, Agder",
        "bbox": NIDELVA_BBOX,
        "site_count": len(site_entries),
        "protected_count": protected_count,
        "category_summary": cat_counts,
        "categories": HERITAGE_CATEGORIES,
        "sites": site_entries,
    }


def export_heritage_json(
    output_path: Path,
    fetch_live: bool = False,
) -> Path:
    """Export heritage site data as JSON for Unity.

    Args:
        output_path: Output directory.
        fetch_live: If True, attempt to fetch from Riksantikvaren first.

    Returns:
        Path to the exported JSON file.
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "heritage_sites.json"

    sites = None

    if fetch_live:
        logger.info("Fetching heritage sites from Riksantikvaren...")
        live_sites = fetch_heritage_sites()
        if live_sites:
            sites = live_sites
        else:
            logger.info("  Askeladden unavailable, using offline fallback")

    heritage_data = build_heritage_data(sites)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(heritage_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Heritage sites exported: {json_path}")
    print(
        f"    {heritage_data['site_count']} sites "
        f"({heritage_data['protected_count']} protected)"
    )
    for s in heritage_data["sites"]:
        prot = " [FREDET]" if s["protected"] else ""
        print(f"    - {s['name']} ({s['category']}, {s['year_built']}){prot}")

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
