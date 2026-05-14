"""
Terrain mesh generator from DEM data.
Converts elevation raster to 3D mesh for rendering.
"""

from pathlib import Path

import numpy as np


def load_dem(dem_path: Path) -> tuple[np.ndarray, dict]:
    """
    Load DEM from file.

    Returns:
        (height_array, metadata)
        height_array: 2D numpy array of elevations in meters
        metadata: dict with 'width', 'height', 'bbox', 'resolution'
    """
    try:
        import rasterio

        with rasterio.open(dem_path) as src:
            data = src.read(1)

            # Get bounds
            bounds = src.bounds
            bbox = (bounds.left, bounds.bottom, bounds.right, bounds.top)

            # Calculate resolution
            res_x = (bounds.right - bounds.left) / src.width
            res_y = (bounds.top - bounds.bottom) / src.height

            metadata = {
                "width": src.width,
                "height": src.height,
                "bbox": bbox,
                "resolution": (res_x, res_y),
                "crs": str(src.crs),
                "nodata": src.nodata,
            }

            # Handle nodata
            if src.nodata is not None:
                data = np.where(data == src.nodata, np.nan, data)

            return data.astype(np.float32), metadata

    except ImportError:
        # Fallback: load as plain image
        from PIL import Image

        img = Image.open(dem_path)
        data = np.array(img).astype(np.float32)

        # If 16-bit, scale appropriately
        if data.max() > 255:
            data = data / 65535.0 * 1000  # approximate scaling

        metadata = {
            "width": data.shape[1],
            "height": data.shape[0],
            "bbox": (0, 0, 1, 1),  # normalized
            "resolution": (1.0 / data.shape[1], 1.0 / data.shape[0]),
            "crs": "unknown",
            "nodata": None,
        }

        return data, metadata


def generate_mesh(
    dem_data: np.ndarray,
    metadata: dict,
    max_size: int = 512,
    height_scale: float = 0.01,  # Scale factor for visual height
) -> dict:
    """
    Generate 3D mesh from DEM.

    Returns dict with:
        'vertices': Nx3 array of positions
        'indices': Mx3 array of triangle indices
        'uvs': Nx2 array of texture coordinates
        'normals': Nx3 array of vertex normals
        'bounds': (min, max) tuples for x, y, z
    """
    height, width = dem_data.shape

    # Downsample if too large
    if max(height, width) > max_size:
        scale = max_size / max(height, width)
        new_h = int(height * scale)
        new_w = int(width * scale)

        # Simple downsampling
        from scipy.ndimage import zoom

        dem_data = zoom(dem_data, (new_h / height, new_w / width), order=1)
        height, width = dem_data.shape

    # Handle NaN values
    if np.any(np.isnan(dem_data)):
        # Fill with nearest valid value
        from scipy.ndimage import distance_transform_edt

        mask = np.isnan(dem_data)
        if np.all(mask):
            dem_data = np.zeros_like(dem_data)
        else:
            # Get indices of nearest valid pixel for each NaN pixel
            indices = distance_transform_edt(mask, return_distances=False, return_indices=True)
            dem_data[mask] = dem_data[indices[0][mask], indices[1][mask]]

    # Scale to reasonable world coordinates
    bbox = metadata["bbox"]
    world_width = bbox[2] - bbox[0]
    world_height = bbox[3] - bbox[1]

    # Aspect ratio correction (latitude)
    lat_center = (bbox[1] + bbox[3]) / 2
    lon_scale = np.cos(np.radians(lat_center)) * 111320  # meters per degree lon
    lat_scale = 111320  # meters per degree lat

    x_scale = lon_scale * world_width / width
    z_scale = lat_scale * world_height / height

    # Center the terrain
    x_offset = -width * x_scale / 2
    z_offset = -height * z_scale / 2

    # Generate vertices (vectorized)
    x_coords = np.arange(width, dtype=np.float32) * x_scale + x_offset
    z_coords = np.arange(height, dtype=np.float32) * z_scale + z_offset

    # Create 2D grids
    xx, zz = np.meshgrid(x_coords, z_coords)
    yy = dem_data * height_scale

    # Flatten to Nx3 vertices
    vertices = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()]).astype(np.float32)

    # UVs
    u = np.linspace(0, 1, width, dtype=np.float32)
    v = np.linspace(0, 1, height, dtype=np.float32)
    uu, vv = np.meshgrid(u, v)
    uvs = np.column_stack([uu.ravel(), vv.ravel()]).astype(np.float32)

    # Generate triangle indices (vectorized)
    rows = np.arange(height - 1)
    cols = np.arange(width - 1)
    rr, cc = np.meshgrid(rows, cols, indexing="ij")
    rr = rr.ravel()
    cc = cc.ravel()

    i0 = rr * width + cc
    i1 = rr * width + (cc + 1)
    i2 = (rr + 1) * width + cc
    i3 = (rr + 1) * width + (cc + 1)

    # Two triangles per quad
    tri1 = np.column_stack([i0, i1, i2])
    tri2 = np.column_stack([i1, i3, i2])
    indices = np.empty((len(i0) * 2, 3), dtype=np.uint32)
    indices[0::2] = tri1
    indices[1::2] = tri2

    # Calculate normals
    normals = calculate_normals(vertices, indices, width, height)

    # Calculate bounds
    bounds = {
        "x": (vertices[:, 0].min(), vertices[:, 0].max()),
        "y": (vertices[:, 1].min(), vertices[:, 1].max()),
        "z": (vertices[:, 2].min(), vertices[:, 2].max()),
    }

    return {
        "vertices": vertices,
        "indices": indices.flatten(),
        "uvs": uvs,
        "normals": normals,
        "bounds": bounds,
        "width": width,
        "height": height,
        "metadata": metadata,
    }


def calculate_normals(
    vertices: np.ndarray, indices: np.ndarray, width: int, height: int
) -> np.ndarray:
    """Calculate per-vertex normals using cross product (vectorized)."""
    normals = np.zeros_like(vertices)

    # Flatten if 2D
    flat_indices = indices.flatten() if indices.ndim == 2 else indices

    # Reshape to Nx3 triangles
    tri_idx = flat_indices.reshape(-1, 3)

    # Get triangle vertices
    v0 = vertices[tri_idx[:, 0]]
    v1 = vertices[tri_idx[:, 1]]
    v2 = vertices[tri_idx[:, 2]]

    # Edge vectors and cross products
    e1 = v1 - v0
    e2 = v2 - v0
    face_normals = np.cross(e1, e2)

    # Normalize face normals
    lengths = np.linalg.norm(face_normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1
    face_normals = face_normals / lengths

    # Accumulate face normals to vertices
    np.add.at(normals, tri_idx[:, 0], face_normals)
    np.add.at(normals, tri_idx[:, 1], face_normals)
    np.add.at(normals, tri_idx[:, 2], face_normals)

    # Normalize per-vertex normals
    vert_lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    vert_lengths[vert_lengths == 0] = 1
    normals = normals / vert_lengths

    return normals.astype(np.float32)


def save_mesh_obj(mesh_data: dict, output_path: Path):
    """Save mesh as Wavefront OBJ file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    vertices = mesh_data["vertices"]
    normals = mesh_data["normals"]
    uvs = mesh_data["uvs"]
    indices = mesh_data["indices"]

    with open(output_path, "w") as f:
        f.write("# Nidelven Terrain Mesh\n")
        f.write(f"# Generated from DEM: {mesh_data['metadata'].get('crs', 'unknown')}\n\n")

        # Vertices
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

        # Texture coordinates
        for uv in uvs:
            f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

        # Normals
        for n in normals:
            f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")

        # Faces (1-indexed in OBJ format)
        for i in range(0, len(indices), 3):
            i0, i1, i2 = indices[i] + 1, indices[i + 1] + 1, indices[i + 2] + 1
            f.write(f"f {i0}/{i0}/{i0} {i1}/{i1}/{i1} {i2}/{i2}/{i2}\n")

    print(f"  ✓ Mesh saved: {output_path}")
    print(f"    Vertices: {len(vertices)}")
    print(f"    Triangles: {len(indices) // 3}")


def create_terrain_from_dem(
    dem_path: Path, output_dir: Path | None = None, save_obj: bool = True
) -> dict:
    """
    Complete pipeline: DEM -> mesh.

    Returns mesh data dict.
    """
    print(f"Loading DEM: {dem_path}")
    dem_data, metadata = load_dem(dem_path)

    print(f"  Size: {metadata['width']}x{metadata['height']}")
    print(f"  BBox: {metadata['bbox']}")
    print(f"  Elevation range: {dem_data.min():.1f}m - {dem_data.max():.1f}m")

    print("\nGenerating mesh...")
    mesh = generate_mesh(dem_data, metadata)

    print(f"  Vertices: {len(mesh['vertices'])}")
    print(f"  Triangles: {len(mesh['indices']) // 3}")
    print(f"  Bounds: x={mesh['bounds']['x']}, y={mesh['bounds']['y']}, z={mesh['bounds']['z']}")

    if save_obj and output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        obj_path = output_dir / "terrain.obj"
        save_mesh_obj(mesh, obj_path)

    return mesh


def export_unity_raw(
    dem_path: Path,
    output_dir: Path,
    resolution: int = 513,
) -> Path:
    """
    Export DEM as 16-bit RAW heightmap for Unity Terrain import.

    Unity Terrain expects:
    - Square power-of-2+1 (e.g. 513, 1025, 2049)
    - 16-bit unsigned little-endian
    - Values 0-65535 (0 = min elevation, 65535 = max elevation)

    Also writes a metadata JSON with terrain dimensions.

    Returns:
        Path to the generated .raw file
    """
    import json

    from scipy.ndimage import zoom

    dem_data, metadata = load_dem(dem_path)

    # Handle NaN
    if np.any(np.isnan(dem_data)):
        from scipy.ndimage import distance_transform_edt

        mask = np.isnan(dem_data)
        if not np.all(mask):
            indices = distance_transform_edt(mask, return_distances=False, return_indices=True)
            dem_data[mask] = dem_data[indices[0][mask], indices[1][mask]]
        else:
            dem_data = np.zeros_like(dem_data)

    # Record real elevation range before normalization
    min_elev = float(np.nanmin(dem_data))
    max_elev = float(np.nanmax(dem_data))

    # Resample to target resolution
    h, w = dem_data.shape
    resampled = zoom(dem_data, (resolution / h, resolution / w), order=1)

    # Normalize to 0-65535
    if max_elev > min_elev:
        normalized = (resampled - min_elev) / (max_elev - min_elev)
    else:
        normalized = np.zeros_like(resampled)

    raw_data = (normalized * 65535).astype(np.uint16)

    # Write RAW file
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "terrain.raw"
    raw_data.tofile(raw_path)

    # Calculate terrain world size from BBOX
    bbox = metadata["bbox"]
    width_m = (bbox[2] - bbox[0]) * 111000 * np.cos(np.radians((bbox[1] + bbox[3]) / 2))
    depth_m = (bbox[3] - bbox[1]) * 111000
    height_m = max_elev - min_elev

    # Write metadata JSON for Unity
    unity_meta = {
        "format": "raw16_little_endian",
        "resolution": resolution,
        "min_elevation_m": min_elev,
        "max_elevation_m": max_elev,
        "height_range_m": height_m,
        "terrain_width_m": float(width_m),
        "terrain_depth_m": float(depth_m),
        "bbox": list(bbox),
        "crs": metadata.get("crs", "EPSG:4326"),
        "source_resolution_m": metadata.get("resolution", [30, 30]),
        "unity_terrain_size": [float(width_m), float(height_m), float(depth_m)],
    }

    meta_path = output_dir / "terrain_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(unity_meta, f, indent=2)

    print(f"  Unity RAW: {raw_path} ({raw_path.stat().st_size / 1024:.0f} KB)")
    print(f"  Metadata: {meta_path}")
    print(f"  Resolution: {resolution}x{resolution}")
    print(f"  Elevation: {min_elev:.1f}m → {max_elev:.1f}m (range: {height_m:.1f}m)")
    print(f"  World size: {width_m:.0f}m × {depth_m:.0f}m")

    return raw_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        dem_path = Path(sys.argv[1])
    else:
        # In src layout, data is at mvp/data/ (two levels up from src/mvp/)
        dem_path = Path(__file__).parent.parent.parent / "data" / "dem.tif"

    if not dem_path.exists():
        print(f"DEM not found: {dem_path}")
        print("Run dem_downloader.py first")
        sys.exit(1)

    output_dir = Path(__file__).parent.parent.parent / "output"
    mesh = create_terrain_from_dem(dem_path, output_dir)
