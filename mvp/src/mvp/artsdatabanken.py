"""
Artsdatabanken species observation client.

Queries the Artsdatabanken/GBIF occurrence API for species observations
in the Nidelva area. Provides accurate wildlife data for spawning
birds, fish, and mammals in Unity.

API: https://api.artsdatabanken.no/ (Species API)
     https://artskart.artsdatabanken.no/ (occurrence search)
License: CC-BY 4.0
Documentation: https://artsdatabanken.no/Pages/232788/

Key species groups for Nidelva (Agder):
- Fish: Atlantic salmon (Salmo salar), sea trout (Salmo trutta)
- Birds: Kingfisher (Alcedo atthis), dipper (Cinclus cinclus),
         grey heron (Ardea cinerea), mallard (Anas platyrhynchos)
- Mammals: Otter (Lutra lutra), beaver (Castor fiber),
           roe deer (Capreolus capreolus), red fox (Vulpes vulpes)
"""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Artsdatabanken Species API
SPECIES_API_URL = "https://api.artsdatabanken.no"

# GBIF occurrence API (includes Norwegian data from Artsdatabanken)
GBIF_API_URL = "https://api.gbif.org/v1"

# Required user agent
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Nidelva bounding box (Agder, Norway) — WGS84
NIDELVA_BBOX = {
    "min_lon": 8.45,
    "min_lat": 58.38,
    "max_lon": 8.85,
    "max_lat": 58.62,
}

# GBIF dataset key for Artsdatabanken (Species Map Service)
ARTSDATABANKEN_DATASET_KEY = "b124e1e0-4755-430f-9eab-894f25a9b59c"

# Taxonomic groups relevant for the game
TAXONOMIC_GROUPS = {
    "birds": {"class_key": 212, "kingdom": "Animalia"},  # Aves
    "fish": {"class_key": 204, "kingdom": "Animalia"},  # Actinopterygii
    "mammals": {"class_key": 359, "kingdom": "Animalia"},  # Mammalia
}

# Known species for Nidelva — offline fallback data
# Based on documented observations in Agder county along Nidelva
NIDELVA_SPECIES = {
    "birds": [
        {
            "scientific_name": "Cinclus cinclus",
            "norwegian_name": "Fossekall",
            "english_name": "White-throated dipper",
            "habitat": "river",
            "abundance": "common",
            "spawn_weight": 0.8,
        },
        {
            "scientific_name": "Alcedo atthis",
            "norwegian_name": "Isfugl",
            "english_name": "Common kingfisher",
            "habitat": "river",
            "abundance": "rare",
            "spawn_weight": 0.2,
        },
        {
            "scientific_name": "Ardea cinerea",
            "norwegian_name": "Gråhegre",
            "english_name": "Grey heron",
            "habitat": "river_bank",
            "abundance": "common",
            "spawn_weight": 0.6,
        },
        {
            "scientific_name": "Anas platyrhynchos",
            "norwegian_name": "Stokkand",
            "english_name": "Mallard",
            "habitat": "river",
            "abundance": "very_common",
            "spawn_weight": 1.0,
        },
        {
            "scientific_name": "Motacilla cinerea",
            "norwegian_name": "Vintererle",
            "english_name": "Grey wagtail",
            "habitat": "river_bank",
            "abundance": "common",
            "spawn_weight": 0.7,
        },
        {
            "scientific_name": "Mergus merganser",
            "norwegian_name": "Laksand",
            "english_name": "Common merganser",
            "habitat": "river",
            "abundance": "uncommon",
            "spawn_weight": 0.4,
        },
    ],
    "fish": [
        {
            "scientific_name": "Salmo salar",
            "norwegian_name": "Atlantisk laks",
            "english_name": "Atlantic salmon",
            "habitat": "river",
            "abundance": "common",
            "spawn_weight": 0.9,
            "seasonal": {"peak_months": [6, 7, 8, 9]},
        },
        {
            "scientific_name": "Salmo trutta",
            "norwegian_name": "Ørret",
            "english_name": "Brown trout / sea trout",
            "habitat": "river",
            "abundance": "common",
            "spawn_weight": 0.8,
            "seasonal": {"peak_months": [5, 6, 7, 8, 9, 10]},
        },
        {
            "scientific_name": "Anguilla anguilla",
            "norwegian_name": "Ål",
            "english_name": "European eel",
            "habitat": "river",
            "abundance": "rare",
            "spawn_weight": 0.2,
        },
        {
            "scientific_name": "Perca fluviatilis",
            "norwegian_name": "Abbor",
            "english_name": "European perch",
            "habitat": "river",
            "abundance": "common",
            "spawn_weight": 0.7,
        },
    ],
    "mammals": [
        {
            "scientific_name": "Lutra lutra",
            "norwegian_name": "Oter",
            "english_name": "Eurasian otter",
            "habitat": "river_bank",
            "abundance": "uncommon",
            "spawn_weight": 0.3,
        },
        {
            "scientific_name": "Castor fiber",
            "norwegian_name": "Bever",
            "english_name": "Eurasian beaver",
            "habitat": "river_bank",
            "abundance": "common",
            "spawn_weight": 0.6,
        },
        {
            "scientific_name": "Capreolus capreolus",
            "norwegian_name": "Rådyr",
            "english_name": "Roe deer",
            "habitat": "forest_edge",
            "abundance": "common",
            "spawn_weight": 0.7,
        },
        {
            "scientific_name": "Vulpes vulpes",
            "norwegian_name": "Rødrev",
            "english_name": "Red fox",
            "habitat": "forest_edge",
            "abundance": "common",
            "spawn_weight": 0.5,
        },
        {
            "scientific_name": "Alces alces",
            "norwegian_name": "Elg",
            "english_name": "Moose",
            "habitat": "forest",
            "abundance": "uncommon",
            "spawn_weight": 0.2,
        },
    ],
}

# Unity WildlifeSpawner categories
SPAWNER_CATEGORIES = {
    "birds": {
        "prefab_type": "Bird",
        "spawn_height_offset": 2.0,
        "despawn_distance": 150.0,
        "max_count": 12,
        "flight_capable": True,
    },
    "fish": {
        "prefab_type": "Fish",
        "spawn_height_offset": -0.5,
        "despawn_distance": 50.0,
        "max_count": 8,
        "flight_capable": False,
    },
    "mammals": {
        "prefab_type": "Mammal",
        "spawn_height_offset": 0.0,
        "despawn_distance": 200.0,
        "max_count": 6,
        "flight_capable": False,
    },
}


def get_species_list(group: str | None = None) -> dict:
    """Get the offline species list for Nidelva.

    Args:
        group: Optional filter — 'birds', 'fish', or 'mammals'.
               If None, returns all groups.

    Returns:
        Dict with species grouped by category.
    """
    if group is not None:
        if group not in NIDELVA_SPECIES:
            logger.warning(f"Unknown species group '{group}', returning all")
            return NIDELVA_SPECIES
        return {group: NIDELVA_SPECIES[group]}
    return NIDELVA_SPECIES


def fetch_species_observations(
    group: str = "birds",
    bbox: dict | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Fetch species observations from GBIF API for the Nidelva area.

    Queries GBIF (which includes Artsdatabanken data) for occurrence
    records within the bounding box.

    Args:
        group: Taxonomic group — 'birds', 'fish', or 'mammals'.
        bbox: Bounding box dict with min_lon, min_lat, max_lon, max_lat.
              Defaults to NIDELVA_BBOX.
        limit: Max number of records to return (max 300).

    Returns:
        List of occurrence records with species info.
    """
    if bbox is None:
        bbox = NIDELVA_BBOX

    if group not in TAXONOMIC_GROUPS:
        raise ValueError(f"Unknown group '{group}'. Must be one of: {list(TAXONOMIC_GROUPS)}")

    class_key = TAXONOMIC_GROUPS[group]["class_key"]

    params = {
        "decimalLatitude": f"{bbox['min_lat']},{bbox['max_lat']}",
        "decimalLongitude": f"{bbox['min_lon']},{bbox['max_lon']}",
        "classKey": class_key,
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "country": "NO",
        "limit": min(limit, 300),
    }

    url = f"{GBIF_API_URL}/occurrence/search?{urlencode(params)}"
    logger.info(f"Fetching {group} observations from GBIF: {url}")

    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("results", [])
        logger.info(f"Got {len(results)} {group} observations (total: {data.get('count', 0)})")

        # Extract relevant fields
        species_list = []
        seen_species = set()
        for record in results:
            species_name = record.get("species")
            if not species_name or species_name in seen_species:
                continue
            seen_species.add(species_name)

            species_list.append(
                {
                    "scientific_name": species_name,
                    "english_name": record.get("vernacularName", ""),
                    "latitude": record.get("decimalLatitude"),
                    "longitude": record.get("decimalLongitude"),
                    "observation_count": sum(
                        1 for r in results if r.get("species") == species_name
                    ),
                    "year": record.get("year"),
                }
            )

        return species_list

    except Exception as e:
        logger.warning(f"GBIF API request failed: {e}")
        return []


def build_wildlife_spawn_data(
    species_data: dict | None = None, month: int | None = None
) -> dict[str, Any]:
    """Convert species data into Unity WildlifeSpawner format.

    Args:
        species_data: Species dict (from get_species_list or fetch).
                      If None, uses offline NIDELVA_SPECIES.
        month: Current month (1-12) for seasonal filtering.
               If None, includes all species regardless of season.

    Returns:
        Dict ready for JSON export to Unity.
    """
    if species_data is None:
        species_data = NIDELVA_SPECIES

    spawn_data = {
        "version": "1.0",
        "source": "Artsdatabanken/GBIF",
        "license": "CC-BY 4.0",
        "bbox": NIDELVA_BBOX,
        "categories": {},
    }

    for group, species_list in species_data.items():
        category_config = SPAWNER_CATEGORIES.get(group, SPAWNER_CATEGORIES["mammals"])

        # Filter by season if month provided
        filtered_species = []
        for species in species_list:
            if month is not None and "seasonal" in species:
                peak_months = species["seasonal"].get("peak_months", [])
                if peak_months and month not in peak_months:
                    continue
            filtered_species.append(species)

        # Calculate normalized spawn weights
        total_weight = sum(s.get("spawn_weight", 0.5) for s in filtered_species)
        if total_weight == 0:
            total_weight = 1.0

        spawn_entries = []
        for species in filtered_species:
            weight = species.get("spawn_weight", 0.5)
            spawn_entries.append(
                {
                    "scientific_name": species["scientific_name"],
                    "english_name": species.get("english_name", ""),
                    "norwegian_name": species.get("norwegian_name", ""),
                    "habitat": species.get("habitat", "river"),
                    "spawn_probability": round(weight / total_weight, 3),
                    "abundance": species.get("abundance", "common"),
                }
            )

        spawn_data["categories"][group] = {
            **category_config,
            "species_count": len(spawn_entries),
            "species": spawn_entries,
        }

    return spawn_data


def export_wildlife_json(
    output_path: Path,
    fetch_live: bool = False,
    month: int | None = None,
) -> Path:
    """Export wildlife spawn data as JSON for Unity.

    Args:
        output_path: Output directory.
        fetch_live: If True, attempt to fetch from GBIF API first.
        month: Optional month for seasonal filtering.

    Returns:
        Path to the exported JSON file.
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "wildlife_data.json"

    species_data = None

    if fetch_live:
        logger.info("Fetching live species data from GBIF...")
        species_data = {}
        for group in TAXONOMIC_GROUPS:
            observations = fetch_species_observations(group=group)
            if observations:
                # Merge live data with offline metadata
                species_data[group] = _merge_with_offline(group, observations)
            else:
                logger.info(f"  No live data for {group}, using offline fallback")
                species_data[group] = NIDELVA_SPECIES[group]
    else:
        logger.info("Using offline species data for Nidelva")
        species_data = NIDELVA_SPECIES

    spawn_data = build_wildlife_spawn_data(species_data, month=month)

    with open(json_path, "w") as f:
        json.dump(spawn_data, f, indent=2)

    total_species = sum(cat["species_count"] for cat in spawn_data["categories"].values())
    print(f"  ✓ Wildlife data exported: {json_path}")
    print(f"    {total_species} species across {len(spawn_data['categories'])} categories")
    for group, cat in spawn_data["categories"].items():
        print(f"    - {group}: {cat['species_count']} species")

    return json_path


def _merge_with_offline(group: str, live_observations: list[dict]) -> list[dict]:
    """Merge live GBIF observations with offline species metadata.

    Live data provides confirmation of species presence.
    Offline data provides spawn weights, habitats, and Norwegian names.
    """
    offline = {s["scientific_name"]: s for s in NIDELVA_SPECIES.get(group, [])}
    merged = []

    # First, include all offline species (they're curated for this river)
    for species in NIDELVA_SPECIES.get(group, []):
        merged.append(species.copy())

    # Then add any live observations not in offline list
    offline_names = set(offline.keys())
    for obs in live_observations:
        name = obs.get("scientific_name", "")
        if name and name not in offline_names:
            merged.append(
                {
                    "scientific_name": name,
                    "english_name": obs.get("english_name", ""),
                    "norwegian_name": "",
                    "habitat": "river" if group == "fish" else "forest_edge",
                    "abundance": "uncommon",
                    "spawn_weight": 0.3,
                }
            )

    return merged
