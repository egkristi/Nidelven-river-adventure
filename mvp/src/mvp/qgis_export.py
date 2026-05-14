"""
QGIS export module for Nidelven River Adventure pipeline results.

Exports pipeline outputs in GIS-standard formats that QGIS can open directly:
- GeoTIFF: DEM terrain with proper CRS and georeferencing
- GeoJSON: River path as a LineString with flow properties
- QGIS project file (.qgs): Pre-configured project with all layers styled

Usage:
    uv run nidelven --qgis          # Export QGIS-ready files
    uv run nidelven --sample --qgis # With synthetic DEM
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from .dem_downloader import NIDELVEN_BBOX


def export_dem_geotiff(
    dem: np.ndarray,
    output_path: Path,
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX,
    crs: str = "EPSG:4326",
) -> Path:
    """
    Export DEM array as a georeferenced GeoTIFF.

    Args:
        dem: 2D elevation array (meters)
        output_path: Path for the output .tif file
        bbox: (min_lon, min_lat, max_lon, max_lat) in WGS84
        crs: Coordinate reference system string

    Returns:
        Path to the exported GeoTIFF
    """
    try:
        import rasterio
        from rasterio.crs import CRS
        from rasterio.transform import from_bounds

        min_lon, min_lat, max_lon, max_lat = bbox
        height, width = dem.shape

        transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with rasterio.open(
            str(output_path),
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype=dem.dtype,
            crs=CRS.from_string(crs),
            transform=transform,
            nodata=-9999,
        ) as dst:
            dst.write(dem, 1)

        return output_path

    except ImportError:
        # Fallback: write raw TIFF with world file (.tfw) for georeferencing
        from PIL import Image

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Normalize to 16-bit for TIFF
        dem_norm = np.clip(dem, 0, 65535).astype(np.uint16)
        img = Image.fromarray(dem_norm, mode="I;16")
        img.save(str(output_path))

        # Write world file (.tfw) for georeferencing
        min_lon, min_lat, max_lon, max_lat = bbox
        height, width = dem.shape
        pixel_width = (max_lon - min_lon) / width
        pixel_height = -(max_lat - min_lat) / height  # Negative (top to bottom)

        tfw_path = output_path.with_suffix(".tfw")
        with open(tfw_path, "w") as f:
            f.write(f"{pixel_width}\n")
            f.write("0.0\n")
            f.write("0.0\n")
            f.write(f"{pixel_height}\n")
            f.write(f"{min_lon + pixel_width / 2}\n")
            f.write(f"{max_lat + pixel_height / 2}\n")

        # Write .prj file with WGS84 WKT
        prj_path = output_path.with_suffix(".prj")
        with open(prj_path, "w") as f:
            f.write(
                'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
                'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
                'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
            )

        return output_path


def export_river_geojson(
    river_path: list[tuple[int, int]],
    dem: np.ndarray,
    output_path: Path,
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX,
    widths: list[float] | None = None,
    speeds: list[float] | None = None,
) -> Path:
    """
    Export river path as a GeoJSON LineString with properties.

    Args:
        river_path: List of (row, col) pixel coordinates along the river
        dem: 2D elevation array for elevation lookup
        output_path: Path for the output .geojson file
        bbox: Bounding box for coordinate conversion
        widths: Optional river widths at each point (meters)
        speeds: Optional flow speeds at each point (m/s)

    Returns:
        Path to the exported GeoJSON file
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    height, width = dem.shape

    # Convert pixel coordinates to WGS84
    coordinates = []
    elevations = []
    for row, col in river_path:
        lon = min_lon + (col / max(width - 1, 1)) * (max_lon - min_lon)
        lat = max_lat - (row / max(height - 1, 1)) * (max_lat - min_lat)
        r, c = int(round(row)), int(round(col))
        elev = float(dem[r, c]) if 0 <= r < height and 0 <= c < width else 0.0
        coordinates.append([lon, lat, elev])
        elevations.append(elev)

    # Build GeoJSON FeatureCollection
    feature = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": coordinates},
        "properties": {
            "name": "Nidelva",
            "region": "Agder, Norway",
            "algorithm": "D8 flow accumulation",
            "num_points": len(river_path),
            "start_elevation_m": elevations[0] if elevations else 0,
            "end_elevation_m": elevations[-1] if elevations else 0,
            "total_drop_m": (elevations[0] - elevations[-1]) if elevations else 0,
        },
    }

    if widths:
        feature["properties"]["avg_width_m"] = sum(widths) / len(widths)
        feature["properties"]["max_width_m"] = max(widths)
    if speeds:
        feature["properties"]["avg_speed_ms"] = sum(speeds) / len(speeds)

    geojson = {
        "type": "FeatureCollection",
        "name": "Nidelva River Path",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [feature],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(geojson, f, indent=2)

    return output_path


def export_flow_accumulation_geotiff(
    flow_acc: np.ndarray,
    output_path: Path,
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX,
) -> Path:
    """
    Export flow accumulation raster as GeoTIFF for QGIS visualization.

    Args:
        flow_acc: 2D flow accumulation array
        output_path: Path for the output .tif file
        bbox: Bounding box for georeferencing

    Returns:
        Path to the exported GeoTIFF
    """
    # Log-transform for better visualization (accumulation is often exponential)
    flow_viz = np.log1p(flow_acc).astype(np.float32)
    return export_dem_geotiff(flow_viz, output_path, bbox)


def generate_qgis_project(
    output_dir: Path,
    dem_path: Path | None = None,
    river_path: Path | None = None,
    flow_acc_path: Path | None = None,
    orthophoto_path: Path | None = None,
) -> Path:
    """
    Generate a QGIS project file (.qgs) with pre-configured layers.

    Args:
        output_dir: Directory containing the exported files
        dem_path: Path to DEM GeoTIFF
        river_path: Path to river GeoJSON
        flow_acc_path: Path to flow accumulation GeoTIFF
        orthophoto_path: Path to orthophoto PNG/TIFF

    Returns:
        Path to the generated .qgs project file
    """
    project_path = output_dir / "nidelven.qgs"

    # Build minimal QGIS 3.x project XML
    qgis = ET.Element("qgis", version="3.34.0", projectname="Nidelven River Adventure")

    # Project CRS
    proj_crs = ET.SubElement(qgis, "projectCrs")
    spatial_ref = ET.SubElement(proj_crs, "spatialrefsys")
    ET.SubElement(spatial_ref, "authid").text = "EPSG:4326"

    # Map canvas extent (Nidelven area)
    map_canvas = ET.SubElement(qgis, "mapcanvas", name="theMapCanvas")
    extent = ET.SubElement(map_canvas, "extent")
    ET.SubElement(extent, "xmin").text = str(NIDELVEN_BBOX[0])
    ET.SubElement(extent, "ymin").text = str(NIDELVEN_BBOX[1])
    ET.SubElement(extent, "xmax").text = str(NIDELVEN_BBOX[2])
    ET.SubElement(extent, "ymax").text = str(NIDELVEN_BBOX[3])

    # Project layers
    layer_tree = ET.SubElement(qgis, "layer-tree-group")
    project_layers = ET.SubElement(qgis, "projectlayers")

    layer_id = 0

    # Add DEM layer
    if dem_path and dem_path.exists():
        layer_id += 1
        _add_raster_layer(
            layer_tree,
            project_layers,
            dem_path,
            f"dem_{layer_id}",
            "Terrain DEM",
            "singleband-pseudocolor",
        )

    # Add flow accumulation
    if flow_acc_path and flow_acc_path.exists():
        layer_id += 1
        _add_raster_layer(
            layer_tree,
            project_layers,
            flow_acc_path,
            f"flow_{layer_id}",
            "Flow Accumulation",
            "singleband-pseudocolor",
        )

    # Add orthophoto
    if orthophoto_path and orthophoto_path.exists():
        layer_id += 1
        _add_raster_layer(
            layer_tree,
            project_layers,
            orthophoto_path,
            f"ortho_{layer_id}",
            "Orthophoto",
            "multibandcolor",
        )

    # Add river vector layer
    if river_path and river_path.exists():
        layer_id += 1
        _add_vector_layer(layer_tree, project_layers, river_path, f"river_{layer_id}", "River Path")

    # Write project file
    output_dir.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(qgis)
    ET.indent(tree, space="  ")
    tree.write(str(project_path), encoding="utf-8", xml_declaration=True)

    return project_path


def _add_raster_layer(
    layer_tree: ET.Element,
    project_layers: ET.Element,
    file_path: Path,
    layer_id: str,
    layer_name: str,
    renderer_type: str,
) -> None:
    """Add a raster layer entry to the QGIS project."""
    # Layer tree entry
    layer_item = ET.SubElement(
        layer_tree, "layer-tree-layer", id=layer_id, name=layer_name, source=str(file_path)
    )
    layer_item.set("providerKey", "gdal")

    # Project layer definition
    maplayer = ET.SubElement(project_layers, "maplayer", type="raster")
    ET.SubElement(maplayer, "id").text = layer_id
    ET.SubElement(maplayer, "layername").text = layer_name
    ET.SubElement(maplayer, "datasource").text = str(file_path)
    ET.SubElement(maplayer, "provider").text = "gdal"
    srs = ET.SubElement(maplayer, "srs")
    spatial_ref = ET.SubElement(srs, "spatialrefsys")
    ET.SubElement(spatial_ref, "authid").text = "EPSG:4326"

    # Renderer hint
    pipe = ET.SubElement(maplayer, "pipe")
    renderer = ET.SubElement(pipe, "rasterrenderer", type=renderer_type)
    renderer.set("band", "1")


def _add_vector_layer(
    layer_tree: ET.Element,
    project_layers: ET.Element,
    file_path: Path,
    layer_id: str,
    layer_name: str,
) -> None:
    """Add a vector layer entry to the QGIS project."""
    # Layer tree entry
    layer_item = ET.SubElement(
        layer_tree, "layer-tree-layer", id=layer_id, name=layer_name, source=str(file_path)
    )
    layer_item.set("providerKey", "ogr")

    # Project layer definition
    maplayer = ET.SubElement(project_layers, "maplayer", type="vector", geometry="Line")
    ET.SubElement(maplayer, "id").text = layer_id
    ET.SubElement(maplayer, "layername").text = layer_name
    ET.SubElement(maplayer, "datasource").text = str(file_path)
    ET.SubElement(maplayer, "provider").text = "ogr"
    srs = ET.SubElement(maplayer, "srs")
    spatial_ref = ET.SubElement(srs, "spatialrefsys")
    ET.SubElement(spatial_ref, "authid").text = "EPSG:4326"

    # Blue line styling
    renderer = ET.SubElement(maplayer, "renderer-v2", type="singleSymbol")
    symbols = ET.SubElement(renderer, "symbols")
    symbol = ET.SubElement(symbols, "symbol", type="line", name="0")
    sl = ET.SubElement(symbol, "layer", **{"class": "SimpleLine"})
    ET.SubElement(sl, "Option", name="line_color", value="31,120,180,255")
    ET.SubElement(sl, "Option", name="line_width", value="1.5")


def export_for_qgis(
    dem: np.ndarray,
    river_path_pixels: list[tuple[int, int]],
    output_dir: Path,
    bbox: tuple[float, float, float, float] = NIDELVEN_BBOX,
    flow_accumulation: np.ndarray | None = None,
    widths: list[float] | None = None,
    speeds: list[float] | None = None,
    orthophoto_path: Path | None = None,
) -> dict[str, Path]:
    """
    Export all pipeline results in QGIS-friendly formats.

    Creates a complete QGIS project with:
    - DEM as GeoTIFF with hillshade-friendly pseudocolor
    - River path as GeoJSON LineString with elevation profile
    - Flow accumulation as GeoTIFF (log-scaled)
    - Orthophoto reference (if available)
    - Pre-configured .qgs project file

    Args:
        dem: 2D elevation array
        river_path_pixels: List of (row, col) along the river
        output_dir: Output directory for QGIS files
        bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
        flow_accumulation: Optional flow accumulation array
        widths: Optional river widths per point
        speeds: Optional flow speeds per point
        orthophoto_path: Optional path to existing orthophoto

    Returns:
        Dict mapping layer names to exported file paths
    """
    qgis_dir = output_dir / "qgis"
    qgis_dir.mkdir(parents=True, exist_ok=True)

    exported = {}

    # 1. DEM GeoTIFF
    dem_tif = qgis_dir / "dem_elevation.tif"
    export_dem_geotiff(dem.astype(np.float32), dem_tif, bbox)
    exported["dem"] = dem_tif
    print(f"  ✓ DEM GeoTIFF: {dem_tif}")

    # 2. River GeoJSON
    river_geojson = qgis_dir / "river_path.geojson"
    export_river_geojson(river_path_pixels, dem, river_geojson, bbox, widths, speeds)
    exported["river"] = river_geojson
    print(f"  ✓ River GeoJSON: {river_geojson}")

    # 3. Flow accumulation (if available)
    flow_tif = None
    if flow_accumulation is not None:
        flow_tif = qgis_dir / "flow_accumulation.tif"
        export_flow_accumulation_geotiff(flow_accumulation, flow_tif, bbox)
        exported["flow_accumulation"] = flow_tif
        print(f"  ✓ Flow accumulation GeoTIFF: {flow_tif}")

    # 4. QGIS project file
    project_path = generate_qgis_project(
        qgis_dir,
        dem_path=dem_tif,
        river_path=river_geojson,
        flow_acc_path=flow_tif,
        orthophoto_path=orthophoto_path,
    )
    exported["project"] = project_path
    print(f"  ✓ QGIS project: {project_path}")
    print(f"\n  Open in QGIS: qgis {project_path}")

    return exported
