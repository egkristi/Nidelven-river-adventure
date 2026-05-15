"""
xeno-canto bird call client.

Queries the xeno-canto API for bird recordings of species
present along Nidelva. Provides audio metadata and download URLs
for use in Unity's AudioManager bird soundscape layer.

API: https://xeno-canto.org/api/2/recordings
License: CC-BY-NC-SA (individual recordings), free API access
Documentation: https://xeno-canto.org/explore/api

Key species for audio in the Nidelven game:
- Fossekall (Cinclus cinclus) — the iconic dipper song near waterfalls
- Isfugl (Alcedo atthis) — sharp kingfisher call
- Gråhegre (Ardea cinerea) — harsh heron croak
- Stokkand (Anas platyrhynchos) — familiar mallard quack
- Vintererle (Motacilla cinerea) — wagtail "tzit-tzit" call
- Laksand (Mergus merganser) — merganser rattle
"""

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# xeno-canto API v2
XENOCANTO_API_URL = "https://xeno-canto.org/api/2/recordings"

# Required user agent
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Bird species present along Nidelva that we want audio for
# Maps scientific name → game audio metadata
NIDELVA_BIRD_AUDIO = [
    {
        "scientific_name": "Cinclus cinclus",
        "norwegian_name": "Fossekall",
        "english_name": "White-throated dipper",
        "call_type": "song",
        "habitat_zone": "waterfall",
        "volume_weight": 0.8,
        "loop": True,
        "priority": 1,
    },
    {
        "scientific_name": "Alcedo atthis",
        "norwegian_name": "Isfugl",
        "english_name": "Common kingfisher",
        "call_type": "call",
        "habitat_zone": "river",
        "volume_weight": 0.5,
        "loop": False,
        "priority": 2,
    },
    {
        "scientific_name": "Ardea cinerea",
        "norwegian_name": "Gråhegre",
        "english_name": "Grey heron",
        "call_type": "call",
        "habitat_zone": "river_bank",
        "volume_weight": 0.6,
        "loop": False,
        "priority": 3,
    },
    {
        "scientific_name": "Anas platyrhynchos",
        "norwegian_name": "Stokkand",
        "english_name": "Mallard",
        "call_type": "call",
        "habitat_zone": "river",
        "volume_weight": 0.7,
        "loop": False,
        "priority": 2,
    },
    {
        "scientific_name": "Motacilla cinerea",
        "norwegian_name": "Vintererle",
        "english_name": "Grey wagtail",
        "call_type": "song",
        "habitat_zone": "river_bank",
        "volume_weight": 0.6,
        "loop": True,
        "priority": 3,
    },
    {
        "scientific_name": "Mergus merganser",
        "norwegian_name": "Laksand",
        "english_name": "Common merganser",
        "call_type": "call",
        "habitat_zone": "river",
        "volume_weight": 0.4,
        "loop": False,
        "priority": 4,
    },
]

# Audio quality filters for xeno-canto queries
QUALITY_FILTER = "A"  # A = highest quality rating
COUNTRY_FILTER = "Norway"
MAX_RESULTS_PER_SPECIES = 3


def get_bird_audio_list() -> list[dict[str, Any]]:
    """Return the curated offline list of bird audio entries for Nidelva."""
    return [entry.copy() for entry in NIDELVA_BIRD_AUDIO]


def fetch_recordings(
    scientific_name: str,
    country: str = COUNTRY_FILTER,
    quality: str = QUALITY_FILTER,
    call_type: str | None = None,
    max_results: int = MAX_RESULTS_PER_SPECIES,
) -> list[dict[str, Any]]:
    """
    Query xeno-canto API for recordings of a species.

    Args:
        scientific_name: Latin species name (e.g. "Cinclus cinclus")
        country: Country filter (default: Norway)
        quality: Quality rating filter (A=best, B=good, C=ok)
        call_type: Optional filter: "song", "call", "alarm"
        max_results: Maximum recordings to return per species

    Returns:
        List of recording metadata dicts with keys:
        - id, url, file_url, duration_s, quality, recordist, license
    """
    # Build query string
    query_parts = [scientific_name]
    if country:
        query_parts.append(f"cnt:{country}")
    if quality:
        query_parts.append(f"q:{quality}")
    if call_type:
        query_parts.append(f"type:{call_type}")

    query = " ".join(query_parts)
    url = f"{XENOCANTO_API_URL}?query={quote(query)}"

    logger.info(f"Querying xeno-canto: {scientific_name} (country={country})")

    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.warning(f"xeno-canto API request failed for {scientific_name}: {e}")
        return []

    recordings = data.get("recordings", [])
    results = []

    for rec in recordings[:max_results]:
        results.append(_parse_recording(rec))

    logger.info(f"  Found {len(results)} recordings for {scientific_name}")
    return results


def _parse_recording(rec: dict[str, Any]) -> dict[str, Any]:
    """Parse a xeno-canto recording response into our format."""
    # Duration can be "0:45" or "1:23" format
    duration_s = _parse_duration(rec.get("length", "0:00"))

    return {
        "id": rec.get("id", ""),
        "url": f"https://xeno-canto.org/{rec.get('id', '')}",
        "file_url": rec.get("file", ""),
        "file_name": rec.get("file-name", ""),
        "duration_s": duration_s,
        "quality": rec.get("q", ""),
        "type": rec.get("type", ""),
        "recordist": rec.get("rec", ""),
        "license": rec.get("lic", ""),
        "country": rec.get("cnt", ""),
        "locality": rec.get("loc", ""),
        "latitude": float(rec["lat"]) if rec.get("lat") else None,
        "longitude": float(rec["lng"]) if rec.get("lng") else None,
    }


def _parse_duration(length_str: str) -> float:
    """Parse xeno-canto duration string 'M:SS' or 'H:MM:SS' to seconds."""
    parts = length_str.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, IndexError):
        pass
    return 0.0


def build_audio_manifest(
    recordings_by_species: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """
    Build a Unity-compatible audio manifest from fetched recordings.

    Args:
        recordings_by_species: Dict mapping scientific_name → list of recordings

    Returns:
        Audio manifest dict with bird_calls list for Unity AudioManager
    """
    bird_calls = []

    for entry in NIDELVA_BIRD_AUDIO:
        species = entry["scientific_name"]
        recordings = recordings_by_species.get(species, [])

        call_entry = {
            "species": species,
            "norwegian_name": entry["norwegian_name"],
            "english_name": entry["english_name"],
            "habitat_zone": entry["habitat_zone"],
            "call_type": entry["call_type"],
            "volume_weight": entry["volume_weight"],
            "loop": entry["loop"],
            "priority": entry["priority"],
            "recordings": [],
        }

        if recordings:
            for rec in recordings:
                call_entry["recordings"].append(
                    {
                        "id": rec["id"],
                        "file_url": rec["file_url"],
                        "duration_s": rec["duration_s"],
                        "quality": rec["quality"],
                        "license": rec["license"],
                        "recordist": rec["recordist"],
                    }
                )
        else:
            # Use placeholder for offline mode
            call_entry["recordings"].append(
                {
                    "id": f"offline_{species.replace(' ', '_').lower()}",
                    "file_url": "",
                    "duration_s": 0,
                    "quality": "offline",
                    "license": "CC-BY-NC-SA",
                    "recordist": "offline_fallback",
                }
            )

        bird_calls.append(call_entry)

    return {
        "version": "1.0",
        "source": "xeno-canto.org",
        "license": "CC-BY-NC-SA (individual recordings)",
        "species_count": len(bird_calls),
        "bird_calls": bird_calls,
    }


def export_bird_audio_json(
    output_path: str | Path | None = None,
    fetch_live: bool = False,
) -> dict[str, Any]:
    """
    Export bird audio manifest as JSON for Unity AudioManager.

    Args:
        output_path: Path to write JSON (default: StreamingAssets/bird_audio.json)
        fetch_live: If True, query xeno-canto API for real recordings

    Returns:
        The audio manifest dict
    """
    if output_path is None:
        output_path = Path("Assets/StreamingAssets/bird_audio.json")
    else:
        output_path = Path(output_path)

    recordings_by_species: dict[str, list[dict[str, Any]]] = {}

    if fetch_live:
        logger.info("Fetching bird recordings from xeno-canto...")
        for entry in NIDELVA_BIRD_AUDIO:
            species = entry["scientific_name"]
            recs = fetch_recordings(
                scientific_name=species,
                call_type=entry["call_type"],
            )
            recordings_by_species[species] = recs
    else:
        logger.info("Using offline bird audio manifest (no API calls)")

    manifest = build_audio_manifest(recordings_by_species)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"Bird audio manifest exported to {output_path}")
    logger.info(f"  {manifest['species_count']} species, license: {manifest['license']}")

    return manifest
