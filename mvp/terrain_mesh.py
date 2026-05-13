"""
Terrain mesh generator from DEM data.
Converts elevation raster to 3D mesh for rendering.
"""

import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import json


def load_dem(dem_path: Path) -> Tuple[np.ndarray, dict]:
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
                'width': src.width,
                'height': src.height,
                'bbox': bbox,
                'resolution': (res_x, res_y),
                'crs': str(src.crs),
                'nodata': src.nodata
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
            'width': data.shape[1],
            'height': data.shape[0],
            'bbox': (0, 0, 1, 1),  # normalized
            'resolution': (1.0 / data.shape[1], 1.0 / data.shape[0]),
            'crs': 'unknown',
            'nodata': None
        }
        
        return data, metadata


def generate_mesh(
    dem_data: np.ndarray,
    metadata: dict,
    max_size: int = 512,
    height_scale: float = 0.01  # Scale factor for visual height
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
            dem_data[mask] = distance_transform_edt(mask, return_distances=False, 
                                                      return_indices=True)
    
    # Generate vertices
    # Scale to reasonable world coordinates
    bbox = metadata['bbox']
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
    
    vertices = []
    uvs = []
    
    for y in range(height):
        for x in range(width):
            px = x * x_scale + x_offset
            py = dem_data[y, x] * height_scale
            pz = y * z_scale + z_offset
            vertices.append([px, py, pz])
            uvs.append([x / (width - 1), y / (height - 1)])
    
    vertices = np.array(vertices, dtype=np.float32)
    uvs = np.array(uvs, dtype=np.float32)
    
    # Generate triangle indices
    indices = []
    for y in range(height - 1):
        for x in range(width - 1):
            # Two triangles per quad
            i0 = y * width + x
            i1 = y * width + (x + 1)
            i2 = (y + 1) * width + x
            i3 = (y + 1) * width + (x + 1)
            
            # Triangle 1: top-left, top-right, bottom-left
            indices.append([i0, i1, i2])
            # Triangle 2: top-right, bottom-right, bottom-left
            indices.append([i1, i3, i2])
    
    indices = np.array(indices, dtype=np.uint32)
    
    # Calculate normals
    normals = calculate_normals(vertices, indices, width, height)
    
    # Calculate bounds
    bounds = {
        'x': (vertices[:, 0].min(), vertices[:, 0].max()),
        'y': (vertices[:, 1].min(), vertices[:, 1].max()),
        'z': (vertices[:, 2].min(), vertices[:, 2].max()),
    }
    
    return {
        'vertices': vertices,
        'indices': indices.flatten(),
        'uvs': uvs,
        'normals': normals,
        'bounds': bounds,
        'width': width,
        'height': height,
        'metadata': metadata
    }


def calculate_normals(
    vertices: np.ndarray,
    indices: np.ndarray,
    width: int,
    height: int
) -> np.ndarray:
    """Calculate per-vertex normals using cross product."""
    normals = np.zeros_like(vertices)
    
    # For each triangle
    for i in range(0, len(indices), 3):
        i0, i1, i2 = indices[i], indices[i + 1], indices[i + 2]
        
        v0 = vertices[i0]
        v1 = vertices[i1]
        v2 = vertices[i2]
        
        # Edge vectors
        e1 = v1 - v0
        e2 = v2 - v0
        
        # Cross product
        normal = np.cross(e1, e2)
        
        # Normalize
        length = np.linalg.norm(normal)
        if length > 0:
            normal = normal / length
        
        # Add to all three vertices
        normals[i0] += normal
        normals[i1] += normal
        normals[i2] += normal
    
    # Normalize per-vertex normals
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1  # Avoid division by zero
    normals = normals / lengths
    
    return normals.astype(np.float32)


def save_mesh_obj(mesh_data: dict, output_path: Path):
    """Save mesh as Wavefront OBJ file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    vertices = mesh_data['vertices']
    normals = mesh_data['normals']
    uvs = mesh_data['uvs']
    indices = mesh_data['indices']
    
    with open(output_path, 'w') as f:
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
    dem_path: Path,
    output_dir: Optional[Path] = None,
    save_obj: bool = True
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


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        dem_path = Path(sys.argv[1])
    else:
        dem_path = Path(__file__).parent / "data" / "dem.tif"
    
    if not dem_path.exists():
        print(f"DEM not found: {dem_path}")
        print("Run dem_downloader.py first")
        sys.exit(1)
    
    output_dir = Path(__file__).parent / "output"
    mesh = create_terrain_from_dem(dem_path, output_dir)
