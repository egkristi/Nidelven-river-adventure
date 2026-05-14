"""Tests for the MVP terrain pipeline."""

import json

import numpy as np

from mvp.dem_downloader import create_sample_dem
from mvp.minimal import create_sample_dem_ascii
from mvp.river_flow import find_start_point, trace_river_path
from mvp.terrain_mesh import calculate_normals, export_unity_raw, generate_mesh


class TestMinimal:
    def test_create_sample_dem_ascii(self):
        dem = create_sample_dem_ascii(size=32)
        assert len(dem) == 32
        assert len(dem[0]) == 32
        assert all(isinstance(v, float) for row in dem for v in row)

    def test_dem_has_valley(self):
        dem = create_sample_dem_ascii(size=64)
        # Center should be lower than edges (river valley)
        center_avg = np.mean([dem[y][32] for y in range(64)])
        edge_avg = np.mean([dem[y][0] for y in range(64)])
        assert center_avg < edge_avg


class TestTerrainMesh:
    def test_generate_mesh_basic(self):
        dem_data = np.random.rand(16, 16).astype(np.float32) * 100
        metadata = {
            "bbox": (8.2, 58.3, 8.9, 58.9),
            "resolution": (1.0, 1.0),
        }
        mesh = generate_mesh(dem_data, metadata)
        assert "vertices" in mesh
        assert "indices" in mesh
        assert "normals" in mesh
        assert mesh["vertices"].shape[0] == 16 * 16
        assert mesh["normals"].shape == mesh["vertices"].shape

    def test_calculate_normals_shape(self):
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]], dtype=np.float32)
        indices = np.array([0, 1, 2, 1, 3, 2], dtype=np.uint32)
        normals = calculate_normals(vertices, indices, 2, 2)
        assert normals.shape == vertices.shape


class TestRiverFlow:
    def test_find_start_point(self):
        dem = np.zeros((32, 32), dtype=np.float32)
        for i in range(32):
            dem[i, :] = 100 - i * 3
        # Make a high point at top row (river source = highest point)
        dem[0, 16] = 200
        start = find_start_point(dem, start_side="top")
        assert start[0] == 0  # Top row
        assert start[1] == 16  # Highest point on that edge

    def test_trace_river_path(self):
        # Simple slope: high at top, low at bottom
        dem = np.zeros((32, 32), dtype=np.float32)
        for i in range(32):
            dem[i, :] = 100 - i * 3
        start = find_start_point(dem, start_side="top")
        path = trace_river_path(dem, start=start)
        assert len(path) >= 1


class TestDemDownloader:
    def test_create_sample_dem(self, tmp_path):
        output_file = tmp_path / "test_dem.tif"
        dem_path = create_sample_dem(output_file, size=32)
        assert dem_path.exists()
        assert dem_path.suffix == ".tif"


class TestUnityExport:
    def test_export_unity_raw(self, tmp_path):
        """Test that export_unity_raw produces valid RAW + metadata."""
        # Create a sample DEM first
        dem_path = tmp_path / "test_dem.tif"
        create_sample_dem(dem_path, size=32)

        # Export as Unity RAW
        output_dir = tmp_path / "output"
        raw_path = export_unity_raw(dem_path, output_dir, resolution=33)

        # Check files exist
        assert raw_path.exists()
        assert (output_dir / "terrain_metadata.json").exists()

        # Check RAW file size (33*33 pixels * 2 bytes)
        assert raw_path.stat().st_size == 33 * 33 * 2

        # Check metadata contents
        with open(output_dir / "terrain_metadata.json") as f:
            meta = json.load(f)
        assert meta["format"] == "raw16_little_endian"
        assert meta["resolution"] == 33
        assert meta["min_elevation_m"] < meta["max_elevation_m"]
        assert len(meta["unity_terrain_size"]) == 3
