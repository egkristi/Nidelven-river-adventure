"""
NVE ELVIS river network importer.

Downloads river centerline geometry from NVE's WFS service (Elvenett).
Provides accurate Nidelva path data to replace gradient-descent river tracing.

API: https://gis3.nve.no/map/services/Elvenett/MapServer/WFSServer
License: NLOD (free for any use)
"""

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np

# NVE ELVIS WFS endpoint
ELVIS_WFS_URL = "https://gis3.nve.no/map/services/Elvenett/MapServer/WFSServer"

# Nidelva bounding box (UTM33N / EPSG:25833)
# Covers the stretch from Nedre Leirfoss to Trondheim Fjord
NIDELVA_BBOX_UTM33 = (569000, 7032000, 573000, 7040000)

# Default river name filter
NIDELVA_NAME = "Nidelva"


def fetch_river_geometry(
    bbox: tuple[float, float, float, float] = NIDELVA_BBOX_UTM33,
    river_name: str | None = NIDELVA_NAME,
    srs: str = "EPSG:25833",
    max_features: int = 100,
    timeout: int = 30,
) -> dict:
    """
    Fetch river geometry from NVE ELVIS WFS.

    Args:
        bbox: Bounding box (minx, miny, maxx, maxy) in the given SRS
        river_name: Optional river name filter
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
        "typeName": "Elvenett:Elv",
        "outputFormat": "geojson",
        "srsName": srs,
        "count": str(max_features),
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},{srs}",
    }

    if river_name:
        params["CQL_FILTER"] = f"elvenavn='{river_name}'"

    url = f"{ELVIS_WFS_URL}?{urlencode(params)}"

    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        data = json.loads(response.read().decode("utf-8"))

    return data


def extract_river_path(geojson: dict) -> np.ndarray:
    """
    Extract a continuous river path from GeoJSON features.

    Merges LineString geometries into a single path, ordered upstream to downstream.

    Args:
        geojson: GeoJSON FeatureCollection from fetch_river_geometry

    Returns:
        Nx2 array of coordinates (easting, northing) in the source CRS
    """
    features = geojson.get("features", [])
    if not features:
        return np.empty((0, 2), dtype=np.float64)

    # Collect all line segments
    segments = []
    for feature in features:
        geom = feature.get("geometry", {})
        geom_type = geom.get("type", "")
        coords = geom.get("coordinates", [])

        if geom_type == "LineString":
            segments.append(np.array(coords)[:, :2])  # Take only x, y
        elif geom_type == "MultiLineString":
            for line in coords:
                segments.append(np.array(line)[:, :2])

    if not segments:
        return np.empty((0, 2), dtype=np.float64)

    # Sort segments to form a continuous path (greedy nearest-endpoint)
    path = _merge_segments(segments)
    return path


def _merge_segments(segments: list[np.ndarray]) -> np.ndarray:
    """
    Merge line segments into a continuous path by connecting nearest endpoints.

    Uses greedy approach: start with longest segment, repeatedly attach
    the segment whose endpoint is closest to either end of the current path.
    """
    if len(segments) == 1:
        return segments[0]

    # Start with the longest segment
    lengths = [len(s) for s in segments]
    current_idx = int(np.argmax(lengths))
    path = segments[current_idx].copy()
    remaining = [i for i in range(len(segments)) if i != current_idx]

    while remaining:
        best_idx = -1
        best_dist = float("inf")
        best_reverse = False
        best_end = "tail"  # attach to tail or head

        path_head = path[0]
        path_tail = path[-1]

        for i in remaining:
            seg = segments[i]
            seg_start = seg[0]
            seg_end = seg[-1]

            # Try all 4 connection options
            d_tail_start = np.linalg.norm(path_tail - seg_start)
            d_tail_end = np.linalg.norm(path_tail - seg_end)
            d_head_start = np.linalg.norm(path_head - seg_start)
            d_head_end = np.linalg.norm(path_head - seg_end)

            options = [
                (d_tail_start, False, "tail"),
                (d_tail_end, True, "tail"),
                (d_head_end, False, "head"),
                (d_head_start, True, "head"),
            ]

            for dist, reverse, end in options:
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i
                    best_reverse = reverse
                    best_end = end

        # Attach best segment
        seg = segments[best_idx]
        if best_reverse:
            seg = seg[::-1]

        path = np.vstack([path, seg]) if best_end == "tail" else np.vstack([seg, path])

        remaining.remove(best_idx)

    return path


def save_river_geojson(geojson: dict, output_path: Path) -> None:
    """Save raw GeoJSON response to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(geojson, f, indent=2)


def save_river_path(path: np.ndarray, output_path: Path) -> None:
    """Save extracted river path as numpy binary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, path)


def load_river_path(path_file: Path) -> np.ndarray:
    """Load river path from numpy binary."""
    return np.load(path_file)


def get_nidelva_path(
    cache_dir: Path | None = None,
    force_download: bool = False,
) -> np.ndarray:
    """
    Get Nidelva river path, using cache if available.

    Args:
        cache_dir: Directory to cache downloaded data (default: mvp/data/)
        force_download: Force re-download even if cached

    Returns:
        Nx2 array of UTM33 coordinates (easting, northing)
    """
    if cache_dir is None:
        cache_dir = Path(__file__).parent.parent.parent / "data"

    cache_file = cache_dir / "nidelva_path.npy"
    geojson_file = cache_dir / "nidelva_elvis.geojson"

    if not force_download and cache_file.exists():
        return load_river_path(cache_file)

    print("  Downloading Nidelva geometry from NVE ELVIS...")
    geojson = fetch_river_geometry()

    feature_count = len(geojson.get("features", []))
    print(f"  ✓ Received {feature_count} river segments")

    # Save raw GeoJSON
    save_river_geojson(geojson, geojson_file)

    # Extract and save path
    path = extract_river_path(geojson)
    print(f"  ✓ Extracted river path: {len(path)} points")

    if len(path) > 0:
        save_river_path(path, cache_file)

    return path
