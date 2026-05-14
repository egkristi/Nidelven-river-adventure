"""
River flow calculator.
Generates a river trajectory following the DEM elevation gradient,
creating a natural path from high to low elevation.

Supports two algorithms:
- Gradient descent (original): fast but easily stuck in flat areas
- D8 flow accumulation: standard hydrological algorithm, finds realistic valleys
"""

from pathlib import Path

import numpy as np
from scipy.interpolate import splev, splprep
from scipy.ndimage import gaussian_filter

# D8 direction offsets: N, NE, E, SE, S, SW, W, NW
_D8_OFFSETS = np.array([(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)])
_D8_DISTANCES = np.array([1.0, np.sqrt(2), 1.0, np.sqrt(2), 1.0, np.sqrt(2), 1.0, np.sqrt(2)])


def compute_flow_direction_d8(dem: np.ndarray) -> np.ndarray:
    """
    Compute D8 flow direction for each cell.

    For each cell, finds the steepest downhill neighbor (drop / distance).
    Returns an array of direction indices (0-7) or -1 for sinks/flats.

    The D8 directions are:
        7  0  1
        6  X  2
        5  4  3
    """
    h, w = dem.shape
    flow_dir = np.full((h, w), -1, dtype=np.int8)

    # Pad DEM to avoid boundary checks
    padded = np.pad(dem, 1, mode="edge")

    for d in range(8):
        dy, dx = _D8_OFFSETS[d]
        # Neighbor values shifted
        neighbor = padded[1 + dy : h + 1 + dy, 1 + dx : w + 1 + dx]
        # Slope = drop / distance
        slope = (dem - neighbor) / _D8_DISTANCES[d]

        # Update where this direction has steepest slope
        mask = slope > 0
        # Compare with current best
        current_best = np.where(flow_dir >= 0, np.zeros((h, w)), -np.inf)
        for dd in range(8):
            ddy, ddx = _D8_OFFSETS[dd]
            nb = padded[1 + ddy : h + 1 + ddy, 1 + ddx : w + 1 + ddx]
            s = (dem - nb) / _D8_DISTANCES[dd]
            update = flow_dir == dd
            current_best = np.where(update, s, current_best)

        better = mask & (slope > current_best)
        flow_dir = np.where(better, d, flow_dir)

    return flow_dir


def compute_flow_direction_d8_fast(dem: np.ndarray) -> np.ndarray:
    """
    Vectorized D8 flow direction computation.

    For each cell, finds the neighbor with steepest downhill slope.
    Returns direction index (0-7) or -1 for pits/flats.
    """
    h, w = dem.shape
    padded = np.pad(dem, 1, mode="edge")

    # Compute slope to all 8 neighbors at once
    slopes = np.full((8, h, w), -np.inf)
    for d in range(8):
        dy, dx = _D8_OFFSETS[d]
        neighbor = padded[1 + dy : h + 1 + dy, 1 + dx : w + 1 + dx]
        slopes[d] = (dem - neighbor) / _D8_DISTANCES[d]

    # Find direction with max positive slope
    max_slope = np.max(slopes, axis=0)
    flow_dir = np.argmax(slopes, axis=0).astype(np.int8)

    # Mark flats/pits (no downhill neighbor) as -1
    flow_dir[max_slope <= 0] = -1

    return flow_dir


def compute_flow_accumulation(dem: np.ndarray, flow_dir: np.ndarray | None = None) -> np.ndarray:
    """
    Compute flow accumulation using D8 flow directions.

    Each cell gets a count of how many upstream cells drain through it.
    High values indicate river channels (convergent flow).

    Args:
        dem: 2D elevation array
        flow_dir: Pre-computed flow directions (optional, computed if None)

    Returns:
        2D array of flow accumulation values (cell counts)
    """
    if flow_dir is None:
        flow_dir = compute_flow_direction_d8_fast(dem)

    h, w = dem.shape
    accumulation = np.ones((h, w), dtype=np.float64)

    # Sort cells by elevation (highest first) for topological processing
    flat_indices = np.argsort(dem.ravel())[::-1]

    for idx in flat_indices:
        row = idx // w
        col = idx % w
        d = flow_dir[row, col]
        if d < 0:
            continue

        dy, dx = _D8_OFFSETS[d]
        nr, nc = row + dy, col + dx
        if 0 <= nr < h and 0 <= nc < w:
            accumulation[nr, nc] += accumulation[row, col]

    return accumulation


def trace_river_d8(
    dem: np.ndarray,
    flow_dir: np.ndarray | None = None,
    accumulation: np.ndarray | None = None,
    min_accumulation: float | None = None,
    start: tuple[int, int] | None = None,
) -> list[tuple[int, int]]:
    """
    Trace river path using D8 flow directions, starting from the cell
    with highest flow accumulation (or a specified start point).

    This produces more realistic river paths than gradient descent because
    it follows the natural drainage network.

    Args:
        dem: 2D elevation array
        flow_dir: Pre-computed D8 directions (computed if None)
        accumulation: Pre-computed flow accumulation (computed if None)
        min_accumulation: Minimum accumulation threshold for river start.
                         If None, uses top 0.1% of cells.
        start: Optional explicit start point (row, col).
               If None, starts from highest-accumulation cell on boundary.

    Returns:
        List of (row, col) points along the river (high to low elevation)
    """
    if flow_dir is None:
        flow_dir = compute_flow_direction_d8_fast(dem)
    if accumulation is None:
        accumulation = compute_flow_accumulation(dem, flow_dir)

    h, w = dem.shape

    if start is None:
        # Find start: highest-elevation cell that has significant accumulation.
        # This gives us a river source point to trace downstream from.
        if min_accumulation is None:
            # Use top 1% of accumulation as "river" threshold
            min_accumulation = np.percentile(accumulation, 99)

        # Mask cells with enough accumulation (they're on a river)
        river_mask = accumulation >= min_accumulation

        if not np.any(river_mask):
            # Fallback: use cell with absolute max accumulation
            max_idx = np.argmax(accumulation)
            start = (max_idx // w, max_idx % w)
        else:
            # Among river cells, pick the one with highest elevation (source)
            river_elevations = np.where(river_mask, dem, -np.inf)
            max_idx = np.argmax(river_elevations)
            start = (max_idx // w, max_idx % w)

    # Trace downstream from start
    path = [start]
    visited = set()
    visited.add(start)

    row, col = start
    for _ in range(max(h, w) * 4):
        d = flow_dir[row, col]
        if d < 0:
            break

        dy, dx = _D8_OFFSETS[d]
        nr, nc = row + dy, col + dx

        if nr < 0 or nr >= h or nc < 0 or nc >= w:
            break
        if (nr, nc) in visited:
            break

        visited.add((nr, nc))
        path.append((nr, nc))
        row, col = nr, nc

    return path


def trace_river_upstream_d8(
    dem: np.ndarray,
    flow_dir: np.ndarray | None = None,
    accumulation: np.ndarray | None = None,
    start: tuple[int, int] | None = None,
) -> list[tuple[int, int]]:
    """
    Trace river from outlet (highest accumulation on boundary) upstream,
    always following the tributary with the highest accumulation.

    This gives a complete river from source to outlet, following the
    main channel at every junction.

    Returns:
        List of (row, col) from source (high elevation) to outlet (low elevation)
    """
    if flow_dir is None:
        flow_dir = compute_flow_direction_d8_fast(dem)
    if accumulation is None:
        accumulation = compute_flow_accumulation(dem, flow_dir)

    h, w = dem.shape

    if start is None:
        # Find outlet: highest accumulation cell on boundary
        boundary_mask = np.zeros((h, w), dtype=bool)
        boundary_mask[0, :] = True
        boundary_mask[-1, :] = True
        boundary_mask[:, 0] = True
        boundary_mask[:, -1] = True

        boundary_acc = np.where(boundary_mask, accumulation, 0)
        max_idx = np.argmax(boundary_acc)
        start = (max_idx // w, max_idx % w)

    # Build reverse flow: for each cell, find which cells flow INTO it
    # Then trace upstream always following the branch with highest accumulation
    path = [start]
    visited = set()
    visited.add(start)

    row, col = start
    for _ in range(max(h, w) * 4):
        # Find all cells that flow into (row, col)
        best_acc = -1
        best_upstream = None

        for d in range(8):
            dy, dx = _D8_OFFSETS[d]
            nr, nc = row + dy, col + dx
            if nr < 0 or nr >= h or nc < 0 or nc >= w:
                continue
            if (nr, nc) in visited:
                continue
            # Check if that cell flows TO (row, col): it must have opposite direction
            opposite_d = (d + 4) % 8
            if flow_dir[nr, nc] == opposite_d and accumulation[nr, nc] > best_acc:
                best_acc = accumulation[nr, nc]
                best_upstream = (nr, nc)

        if best_upstream is None:
            break

        visited.add(best_upstream)
        path.append(best_upstream)
        row, col = best_upstream

    # Reverse so path goes source → outlet (high → low elevation)
    path.reverse()
    return path


def compute_river_widths_from_accumulation(
    accumulation: np.ndarray,
    path: list[tuple[int, int]],
    cell_size: float = 30.0,
    min_width: float = 5.0,
    max_width: float = 80.0,
    exponent: float = 0.4,
) -> np.ndarray:
    """
    Compute river width from upstream drainage area using Leopold & Maddock (1953)
    power-law relationship: width ~ A^exponent

    Args:
        accumulation: Flow accumulation grid
        path: River path as list of (row, col)
        cell_size: Size of each DEM cell in meters
        min_width: Minimum river width (m)
        max_width: Maximum river width (m)
        exponent: Power law exponent (typically 0.3-0.5)

    Returns:
        Array of widths (one per path point)
    """
    # Sample accumulation along path
    acc_values = np.array([accumulation[r, c] for r, c in path], dtype=np.float64)

    # Convert cell count to drainage area (km²)
    area_km2 = acc_values * (cell_size**2) / 1e6

    # Leopold & Maddock: w = a * A^b
    # Calibrated for Norwegian rivers: a ≈ 3.0, b ≈ 0.4
    widths = 3.0 * np.power(np.maximum(area_km2, 0.01), exponent)

    return np.clip(widths, min_width, max_width)


def find_start_point(dem: np.ndarray, start_side: str = "top") -> tuple[int, int]:
    """
    Find the river starting point on one edge of the DEM.
    Uses the HIGHEST point on the chosen edge (headwater/source),
    since the river traces downhill from start.

    Args:
        dem: 2D elevation array
        start_side: Which edge to start from ("top", "bottom", "left", "right")

    Returns:
        (row, col) of start point (highest elevation on that edge)
    """
    h, w = dem.shape

    if start_side == "top":
        edge = dem[0, :]
        col = int(np.argmax(edge))
        return (0, col)
    elif start_side == "bottom":
        edge = dem[-1, :]
        col = int(np.argmax(edge))
        return (h - 1, col)
    elif start_side == "left":
        edge = dem[:, 0]
        row = int(np.argmax(edge))
        return (row, 0)
    elif start_side == "right":
        edge = dem[:, -1]
        row = int(np.argmax(edge))
        return (row, w - 1)
    else:
        # Default: find global maximum on boundary (highest source point)
        boundary = np.concatenate(
            [dem[0, :], dem[-1, :], dem[:, 0], dem[:, -1]]  # top  # bottom  # left  # right
        )
        max_val = np.max(boundary)

        # Find where it is
        if max_val in dem[0, :]:
            col = int(np.argmax(dem[0, :]))
            return (0, col)
        elif max_val in dem[-1, :]:
            col = int(np.argmax(dem[-1, :]))
            return (h - 1, col)
        else:
            row = int(np.argmax(dem[:, 0]))
            return (row, 0)


def calculate_gradient(dem: np.ndarray, sigma: float = 2.0) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculate smoothed elevation gradient.

    Returns:
        (gradient_y, gradient_x) - slope in each direction
    """
    # Smooth the DEM to avoid noise-induced direction changes
    smoothed = gaussian_filter(dem, sigma=sigma)

    # Calculate gradients
    grad_y, grad_x = np.gradient(smoothed)

    return grad_y, grad_x


def trace_river_path(
    dem: np.ndarray,
    start: tuple[int, int],
    step_size: float = 1.0,
    max_steps: int = 10000,
    min_elevation_diff: float = 0.1,
    boundary_margin: int = 2,
) -> list[tuple[int, int]]:
    """
    Trace river path following the negative gradient (downhill).

    Args:
        dem: 2D elevation array
        start: (row, col) starting point
        step_size: How many pixels to move per step
        max_steps: Maximum path length
        min_elevation_diff: Stop if elevation change is too small
        boundary_margin: Stop if within this many pixels of edge

    Returns:
        List of (row, col) points along the river
    """
    grad_y, grad_x = calculate_gradient(dem)

    h, w = dem.shape
    path = [start]

    current = (float(start[0]), float(start[1]))
    prev_elevation = dem[start[0], start[1]]

    for _ in range(max_steps):
        row, col = int(round(current[0])), int(round(current[1]))

        # Check boundaries
        if (
            row < boundary_margin
            or row >= h - boundary_margin
            or col < boundary_margin
            or col >= w - boundary_margin
        ):
            break

        # Get gradient at current position (interpolated)
        gy = grad_y[row, col]
        gx = grad_x[row, col]

        # Gradient magnitude
        grad_mag = np.sqrt(gy**2 + gx**2)

        if grad_mag < 1e-6:
            # Flat area - try to continue in previous direction or search locally
            if len(path) > 1:
                prev = path[-2]
                dy = current[0] - prev[0]
                dx = current[1] - prev[1]
                direction = np.array([dy, dx])
                direction = direction / (np.linalg.norm(direction) + 1e-10)
            else:
                break
        else:
            # Follow negative gradient (downhill)
            direction = np.array([-gy, -gx]) / grad_mag

        # Move in that direction
        current = (current[0] + direction[0] * step_size, current[1] + direction[1] * step_size)

        # Check if we've reached a minimum or are oscillating
        new_row, new_col = int(round(current[0])), int(round(current[1]))
        new_row = np.clip(new_row, 0, h - 1)
        new_col = np.clip(new_col, 0, w - 1)

        current_elevation = dem[new_row, new_col]

        if abs(current_elevation - prev_elevation) < min_elevation_diff:
            # Try to find a better direction by looking around
            found_better = False
            for angle in np.linspace(0, 2 * np.pi, 16, endpoint=False):
                test_dir = np.array([np.sin(angle), np.cos(angle)])
                test_pos = (
                    current[0] + test_dir[0] * step_size,
                    current[1] + test_dir[1] * step_size,
                )
                test_row = int(round(test_pos[0]))
                test_col = int(round(test_pos[1]))
                test_row = np.clip(test_row, 0, h - 1)
                test_col = np.clip(test_col, 0, w - 1)

                if dem[test_row, test_col] < current_elevation - min_elevation_diff:
                    current = test_pos
                    found_better = True
                    break

            if not found_better:
                break

        prev_elevation = current_elevation
        path.append((new_row, new_col))

        # Remove duplicates
        if len(path) > 1 and path[-1] == path[-2]:
            path.pop()

    return path


def smooth_path(
    path: list[tuple[int, int]], smoothness: float = 3.0, num_points: int = 500
) -> np.ndarray:
    """
    Smooth a pixel path using spline interpolation.

    Args:
        path: List of (row, col) points
        smoothness: Spline smoothing factor
        num_points: Number of output points

    Returns:
        Nx2 array of smoothed (row, col) points
    """
    if len(path) < 4:
        # Too few points, just return as-is with interpolation
        pts = np.array(path, dtype=float)
        if len(pts) < 2:
            return pts

        t = np.linspace(0, 1, len(pts))
        t_new = np.linspace(0, 1, num_points)

        rows = np.interp(t_new, t, pts[:, 0])
        cols = np.interp(t_new, t, pts[:, 1])

        return np.column_stack([rows, cols])

    pts = np.array(path, dtype=float).T  # 2 x N

    # Fit spline
    try:
        tck, u = splprep(pts, s=smoothness, k=min(3, len(path) - 1))
        u_new = np.linspace(0, 1, num_points)
        smoothed = splev(u_new, tck)
        return np.column_stack(smoothed)
    except Exception:
        # Fallback to simple smoothing
        from scipy.ndimage import gaussian_filter1d

        pts_array = pts.T
        smoothed = np.zeros_like(pts_array)
        smoothed[:, 0] = gaussian_filter1d(pts_array[:, 0], sigma=2)
        smoothed[:, 1] = gaussian_filter1d(pts_array[:, 1], sigma=2)

        # Resample
        t = np.linspace(0, 1, len(smoothed))
        t_new = np.linspace(0, 1, num_points)
        rows = np.interp(t_new, t, smoothed[:, 0])
        cols = np.interp(t_new, t, smoothed[:, 1])

        return np.column_stack([rows, cols])


def calculate_flow_properties(path: np.ndarray, dem: np.ndarray, metadata: dict) -> dict:
    """
    Calculate river flow properties along the path.

    Returns:
        Dict with 'elevations', 'gradients', 'velocities', 'widths'
    """
    h, w = dem.shape

    # Sample elevations along path
    elevations = []
    for row, col in path:
        r = int(np.clip(round(row), 0, h - 1))
        c = int(np.clip(round(col), 0, w - 1))
        elevations.append(dem[r, c])

    elevations = np.array(elevations)

    # Calculate gradient (elevation change per step)
    gradients = np.gradient(elevations)

    # Calculate approximate flow velocity
    # Simplified: v ~ sqrt(slope) * depth_factor
    # Negative gradient means downhill
    slopes = -gradients
    slopes[slopes < 0] = 0  # No uphill flow

    # Add small base flow
    base_velocity = 0.5  # m/s minimum
    velocities = base_velocity + np.sqrt(slopes * 10)  # simplified
    velocities = np.clip(velocities, 0.1, 5.0)  # Cap at 5 m/s

    # River width varies with velocity (faster = narrower in rapids)
    base_width = 20.0  # meters
    widths = base_width / (1 + (velocities - base_velocity) * 0.5)
    widths = np.clip(widths, 5.0, 50.0)

    return {
        "elevations": elevations,
        "gradients": gradients,
        "velocities": velocities,
        "widths": widths,
        "path": path,
    }


def generate_river_mesh(
    flow_data: dict, dem_data: np.ndarray, mesh_data: dict, width_scale: float = 0.5
) -> dict:
    """
    Generate a 3D mesh for the river surface.

    Returns mesh dict with vertices, indices, normals, uvs.
    """
    path = flow_data["path"]
    widths = flow_data["widths"]

    vertices = []
    indices = []
    uvs = []
    normals = []

    # Generate cross-sections along the path
    num_cross_sections = len(path)

    for i, (row, col) in enumerate(path):
        # Calculate direction (tangent)
        if i == 0:
            direction = path[1] - path[0]
        elif i == len(path) - 1:
            direction = path[-1] - path[-2]
        else:
            direction = path[i + 1] - path[i - 1]

        direction = direction / (np.linalg.norm(direction) + 1e-10)

        # Perpendicular direction (cross product with up)
        perp = np.array([-direction[1], direction[0]])

        # Width at this point
        width = widths[i] * width_scale

        # Two vertices: left and right bank
        left = np.array([row, col]) + perp * width / 2
        right = np.array([row, col]) - perp * width / 2

        # Get 3D positions from terrain mesh
        # Simple approach: sample DEM height
        for point in [left, right]:
            r = int(np.clip(round(point[0]), 0, dem_data.shape[0] - 1))
            c = int(np.clip(round(point[1]), 0, dem_data.shape[1] - 1))

            # Water surface is slightly below terrain at banks
            height = dem_data[r, c] - 1.0  # 1m depth

            # Convert to world coordinates (same as terrain)
            bbox = mesh_data["metadata"]["bbox"]
            world_width = bbox[2] - bbox[0]
            world_height = bbox[3] - bbox[1]
            lat_center = (bbox[1] + bbox[3]) / 2

            x = (c / dem_data.shape[1]) * world_width * 32000 * np.cos(np.radians(lat_center))
            z = (r / dem_data.shape[0]) * world_height * 111320

            # Center
            x -= dem_data.shape[1] * (world_width * 32000 * np.cos(np.radians(lat_center))) / 2
            z -= dem_data.shape[0] * world_height * 111320 / 2

            # Apply height scale from terrain mesh
            height_scale = 0.01
            y = height * height_scale

            vertices.append([x, y, z])
            normals.append([0, 1, 0])  # Upward normal
            uvs.append([i / num_cross_sections, 0 if point is left else 1])

    vertices = np.array(vertices, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32)
    uvs = np.array(uvs, dtype=np.float32)

    # Generate indices for triangle strips
    for i in range(num_cross_sections - 1):
        base = i * 2
        # Two triangles per segment
        indices.append([base, base + 1, base + 2])
        indices.append([base + 1, base + 3, base + 2])

    indices = np.array(indices, dtype=np.uint32).flatten()

    return {
        "vertices": vertices,
        "indices": indices,
        "normals": normals,
        "uvs": uvs,
        "path_3d": vertices,
    }


def create_river_from_dem(
    dem_path: Path,
    output_dir: Path,
    start_side: str = "top",
    num_points: int = 500,
    smoothness: float = 3.0,
) -> dict:
    """
    Complete pipeline: DEM -> river path -> flow properties.

    Returns flow data dict.
    """
    from .terrain_mesh import load_dem

    print(f"Loading DEM: {dem_path}")
    dem_data, metadata = load_dem(dem_path)

    print(f"  Size: {metadata['width']}x{metadata['height']}")
    print(f"  Elevation range: {dem_data.min():.1f}m - {dem_data.max():.1f}m")

    # Find start point (highest elevation on starting edge)
    print(f"\nFinding river start point ({start_side})...")
    start = find_start_point(dem_data, start_side)
    print(f"  Start: row={start[0]}, col={start[1]}, elevation={dem_data[start[0], start[1]]:.1f}m")

    # Trace path downhill
    print("\nTracing river path...")
    path = trace_river_path(dem_data, start)
    print(f"  Raw path length: {len(path)} points")

    if len(path) < 2:
        print("  Warning: Path too short, using diagonal fallback")
        # Fallback: create a simple diagonal path
        h, w = dem_data.shape
        path = [(int(h * i / num_points), int(w * i / num_points)) for i in range(num_points)]

    # Smooth path
    print("\nSmoothing path...")
    smooth_path_pts = smooth_path(path, smoothness=smoothness, num_points=num_points)
    print(f"  Smoothed path: {len(smooth_path_pts)} points")

    # Calculate flow properties
    print("\nCalculating flow properties...")
    flow_data = calculate_flow_properties(smooth_path_pts, dem_data, metadata)
    print(
        f"  Velocity range: {flow_data['velocities'].min():.1f} - {flow_data['velocities'].max():.1f} m/s"
    )
    print(f"  Width range: {flow_data['widths'].min():.1f} - {flow_data['widths'].max():.1f} m")

    # Save path visualization
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as CSV
        csv_path = output_dir / "river_path.csv"
        with open(csv_path, "w") as f:
            f.write("index,row,col,elevation,velocity,width\n")
            for i, (row, col) in enumerate(smooth_path_pts):
                f.write(
                    f"{i},{row:.2f},{col:.2f},"
                    f"{flow_data['elevations'][i]:.2f},"
                    f"{flow_data['velocities'][i]:.2f},"
                    f"{flow_data['widths'][i]:.2f}\n"
                )

        print(f"\n  ✓ River path saved: {csv_path}")

    return flow_data, metadata


def export_river_path_json(
    flow_data: dict,
    metadata: dict,
    output_path: Path,
    spacing: float = 30.0,
) -> Path:
    """
    Export river path as JSON for Unity RiverController.

    Converts DEM row/col coordinates to world-space X/Y/Z that Unity expects.
    Format: { "points": [{"x": ..., "y": ..., "z": ...}, ...], "widths": [...], "speeds": [...] }

    Args:
        flow_data: Output from calculate_flow_properties()
        metadata: DEM metadata with 'width', 'height', 'bbox'
        output_path: Where to write the JSON
        spacing: DEM pixel spacing in meters

    Returns:
        Path to the written JSON
    """
    import json

    path = flow_data["path"]
    elevations = flow_data["elevations"]
    widths = flow_data["widths"]
    velocities = flow_data["velocities"]

    h = metadata["height"]
    w = metadata["width"]

    # Convert row/col to world coordinates centered at origin
    # col → X, elevation → Y, row → Z (matching terrain_mesh convention)
    points = []
    for i, (row, col) in enumerate(path):
        x = (col - w / 2.0) * spacing
        y = float(elevations[i])
        z = (row - h / 2.0) * spacing
        points.append({"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)})

    data = {
        "points": points,
        "widths": [round(float(w), 2) for w in widths],
        "speeds": [round(float(v), 2) for v in velocities],
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f)

    print(f"  River path JSON: {output_path} ({len(points)} points)")
    return output_path


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
    flow_data, metadata = create_river_from_dem(dem_path, output_dir)

    print("\nRiver flow data ready:")
    print(f"  Path length: {len(flow_data['path'])} points")
    print(
        f"  Total elevation drop: {flow_data['elevations'].max() - flow_data['elevations'].min():.1f}m"
    )
