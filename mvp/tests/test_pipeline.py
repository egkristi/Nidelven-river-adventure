"""Tests for the MVP terrain pipeline."""

import json
from pathlib import Path

import numpy as np

from mvp.dem_downloader import create_sample_dem
from mvp.minimal import create_sample_dem_ascii
from mvp.river_flow import (
    calculate_flow_properties,
    find_start_point,
    smooth_path,
    trace_river_path,
)
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


class TestRiverFlowAdvanced:
    """Additional tests for river_flow functions."""

    def test_find_start_point_all_sides(self):
        """Test finding start point from each edge."""
        dem = np.random.rand(32, 32).astype(np.float32) * 50 + 50
        # Set known high points on each edge
        dem[0, 10] = 200  # top
        dem[31, 20] = 200  # bottom
        dem[15, 0] = 200  # left
        dem[25, 31] = 200  # right

        assert find_start_point(dem, "top") == (0, 10)
        assert find_start_point(dem, "bottom") == (31, 20)
        assert find_start_point(dem, "left") == (15, 0)
        assert find_start_point(dem, "right") == (25, 31)

    def test_trace_river_path_goes_downhill(self):
        """Verify river path follows downhill gradient."""
        dem = np.zeros((64, 64), dtype=np.float32)
        for i in range(64):
            dem[i, :] = 200 - i * 3  # Simple north-to-south slope
        # Start inside boundary margin (>= 2 from edge)
        start = (3, 32)
        path = trace_river_path(dem, start=start, max_steps=100)
        # Should move south (increasing row)
        assert len(path) > 5
        assert path[-1][0] > path[0][0]

    def test_trace_river_path_with_valley(self):
        """Test that river follows a valley."""
        dem = np.zeros((64, 64), dtype=np.float32)
        for i in range(64):
            for j in range(64):
                # Create a valley in the center column
                dist_from_center = abs(j - 32)
                dem[i, j] = 200 - i * 2 + dist_from_center * 2
        # Start inside boundary margin
        start = (3, 32)
        path = trace_river_path(dem, start=start, max_steps=200)
        # River should stay near column 32 (the valley)
        cols = [p[1] for p in path]
        assert np.mean(np.abs(np.array(cols) - 32)) < 10

    def test_smooth_path_basic(self):
        """Test path smoothing produces correct output shape."""
        # Create a jagged path
        path = [(i, 32 + (i % 3)) for i in range(20)]
        smoothed = smooth_path(path, smoothness=5.0, num_points=50)
        assert smoothed.shape == (50, 2)

    def test_smooth_path_short(self):
        """Test smooth_path with very few points."""
        path = [(0, 0), (10, 10)]
        smoothed = smooth_path(path, num_points=20)
        assert smoothed.shape == (20, 2)
        # First and last should be near original points
        assert abs(smoothed[0, 0] - 0) < 1
        assert abs(smoothed[-1, 0] - 10) < 1

    def test_calculate_flow_properties(self):
        """Test flow property calculation."""
        dem = np.zeros((64, 64), dtype=np.float32)
        for i in range(64):
            dem[i, :] = 200 - i * 3
        path = np.array([(i, 32) for i in range(50)], dtype=float)
        metadata = {"bbox": (8.2, 58.3, 8.9, 58.9), "resolution": (1.0, 1.0)}
        props = calculate_flow_properties(path, dem, metadata)
        assert "elevations" in props
        assert "velocities" in props
        assert "widths" in props
        assert len(props["elevations"]) == 50
        # Elevations should decrease along path
        assert props["elevations"][0] > props["elevations"][-1]


class TestTerrainMeshAdvanced:
    """Additional mesh generation tests."""

    def test_generate_mesh_with_nan(self):
        """Test that NaN values are handled in mesh generation."""
        dem_data = np.random.rand(16, 16).astype(np.float32) * 100
        dem_data[5, 5] = np.nan
        dem_data[10, 10] = np.nan
        metadata = {"bbox": (8.2, 58.3, 8.9, 58.9), "resolution": (1.0, 1.0)}
        mesh = generate_mesh(dem_data, metadata)
        # Should not have NaN in output vertices
        assert not np.any(np.isnan(mesh["vertices"]))

    def test_generate_mesh_dimensions(self):
        """Test mesh output dimensions for various input sizes."""
        for size in [8, 16, 32]:
            dem_data = np.random.rand(size, size).astype(np.float32) * 100
            metadata = {"bbox": (8.0, 58.0, 9.0, 59.0), "resolution": (1.0, 1.0)}
            mesh = generate_mesh(dem_data, metadata)
            assert mesh["vertices"].shape[0] == size * size
            assert mesh["vertices"].shape[1] == 3
            # Indices: (size-1)*(size-1)*2 triangles * 3 vertices
            expected_indices = (size - 1) * (size - 1) * 6
            assert len(mesh["indices"]) == expected_indices


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_pipeline_sample(self, tmp_path):
        """Test the full pipeline from sample DEM to Unity export."""
        from mvp.terrain_mesh import create_terrain_from_dem

        # Create sample DEM
        dem_path = tmp_path / "sample.tif"
        create_sample_dem(dem_path, size=32)

        # Generate terrain mesh
        mesh = create_terrain_from_dem(str(dem_path))
        assert mesh is not None
        assert "vertices" in mesh
        assert "normals" in mesh
        assert mesh["vertices"].shape[0] > 0

        # Export to Unity format
        output_dir = tmp_path / "unity_output"
        raw_path = export_unity_raw(dem_path, output_dir, resolution=33)
        assert raw_path.exists()

        # Verify metadata
        with open(output_dir / "terrain_metadata.json") as f:
            meta = json.load(f)
        assert meta["format"] == "raw16_little_endian"

    def test_river_on_sample_dem(self, tmp_path):
        """Test river tracing on a sample DEM from the downloader."""
        from mvp.terrain_mesh import load_dem

        dem_path = tmp_path / "river_test.tif"
        create_sample_dem(dem_path, size=64)

        dem_data, metadata = load_dem(str(dem_path))
        # Start inside boundary margin to avoid immediate exit
        start = find_start_point(dem_data, start_side="top")
        # Move start inside if it's on the boundary
        start = (max(start[0], 3), max(min(start[1], dem_data.shape[1] - 4), 3))
        path = trace_river_path(dem_data, start=start, max_steps=500)

        assert len(path) >= 2
        # Path should generally go downhill
        start_elev = dem_data[path[0][0], path[0][1]]
        end_elev = dem_data[path[-1][0], path[-1][1]]
        assert end_elev <= start_elev


class TestNveRiver:
    """Tests for NVE ELVIS river import module."""

    def test_extract_river_path_single_linestring(self):
        """Test extracting path from single LineString feature."""
        from mvp.nve_river import extract_river_path

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [570000, 7035000, 0],
                            [570100, 7035100, 0],
                            [570200, 7035200, 0],
                        ],
                    },
                    "properties": {"elvenavn": "Nidelva"},
                }
            ],
        }

        path = extract_river_path(geojson)
        assert path.shape == (3, 2)
        assert path[0, 0] == 570000
        assert path[2, 1] == 7035200

    def test_extract_river_path_multi_segments(self):
        """Test merging multiple segments into continuous path."""
        from mvp.nve_river import extract_river_path

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[100, 0], [200, 0], [300, 0]],
                    },
                    "properties": {},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[300, 0], [400, 0], [500, 0]],
                    },
                    "properties": {},
                },
            ],
        }

        path = extract_river_path(geojson)
        assert len(path) == 6
        # Should be continuous (ordered)
        assert path[0, 0] == 100 or path[-1, 0] == 100

    def test_extract_river_path_empty(self):
        """Test handling empty feature collection."""
        from mvp.nve_river import extract_river_path

        geojson = {"type": "FeatureCollection", "features": []}
        path = extract_river_path(geojson)
        assert path.shape == (0, 2)

    def test_save_and_load_river_path(self, tmp_path):
        """Test saving and loading river path."""
        from mvp.nve_river import load_river_path, save_river_path

        original = np.array([[570000, 7035000], [570100, 7035100]], dtype=np.float64)
        path_file = tmp_path / "test_path.npy"

        save_river_path(original, path_file)
        loaded = load_river_path(path_file)

        np.testing.assert_array_equal(original, loaded)

    def test_merge_segments_reversal(self):
        """Test that segment merging handles reversed segments."""
        from mvp.nve_river import _merge_segments

        # Second segment is reversed relative to first
        segments = [
            np.array([[0, 0], [10, 0], [20, 0]]),
            np.array([[50, 0], [40, 0], [30, 0]]),  # reversed
        ]

        path = _merge_segments(segments)
        assert len(path) == 6
        # Should form continuous line from 0 to 50 (or 50 to 0)
        diffs = np.abs(np.diff(path[:, 0]))
        assert np.all(diffs == 10)  # all steps are 10


class TestDemIntegrity:
    """Tests for DEM checksum verification."""

    def test_compute_file_checksum(self, tmp_path):
        """Test that checksum is computed consistently."""
        from mvp.dem_downloader import compute_file_checksum

        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"hello world")
        checksum1 = compute_file_checksum(test_file)
        checksum2 = compute_file_checksum(test_file)
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length

    def test_verify_dem_integrity_first_download(self, tmp_path):
        """Test that first verification records checksum."""
        from mvp.dem_downloader import verify_dem_integrity

        dem_file = tmp_path / "test.tif"
        dem_file.write_bytes(b"fake dem data")
        checksums_file = tmp_path / "checksums.json"

        result = verify_dem_integrity(dem_file, checksums_file)
        assert result is True
        assert checksums_file.exists()
        checksums = json.loads(checksums_file.read_text())
        assert "test.tif" in checksums

    def test_verify_dem_integrity_valid(self, tmp_path):
        """Test that valid file passes verification."""
        from mvp.dem_downloader import compute_file_checksum, verify_dem_integrity

        dem_file = tmp_path / "test.tif"
        dem_file.write_bytes(b"valid dem data")
        checksums_file = tmp_path / "checksums.json"

        # Pre-record correct checksum
        checksum = compute_file_checksum(dem_file)
        checksums_file.write_text(json.dumps({"test.tif": checksum}))

        result = verify_dem_integrity(dem_file, checksums_file)
        assert result is True

    def test_verify_dem_integrity_corrupted(self, tmp_path):
        """Test that corrupted file fails verification."""
        from mvp.dem_downloader import verify_dem_integrity

        dem_file = tmp_path / "test.tif"
        dem_file.write_bytes(b"original data")
        checksums_file = tmp_path / "checksums.json"
        checksums_file.write_text(json.dumps({"test.tif": "wrong_checksum_value"}))

        result = verify_dem_integrity(dem_file, checksums_file)
        assert result is False


class TestTerrainTextures:
    """Tests for terrain splatmap generation."""

    def test_compute_slope_flat(self):
        """Flat DEM should have zero slope."""
        from mvp.terrain_textures import compute_slope

        dem = np.ones((32, 32)) * 100.0
        slope = compute_slope(dem)
        assert np.allclose(slope, 0.0, atol=0.01)

    def test_compute_slope_tilted(self):
        """Tilted DEM should have non-zero slope."""
        from mvp.terrain_textures import compute_slope

        dem = np.arange(32).reshape(1, -1).repeat(32, axis=0).astype(float) * 10.0
        slope = compute_slope(dem, cell_size=10.0)
        # Interior cells should have consistent slope
        assert np.all(slope[1:-1, 1:-1] > 0)

    def test_splatmap_shape(self):
        """Splatmap should have correct shape (HxWx4)."""
        from mvp.terrain_textures import generate_splatmap

        dem = np.random.rand(64, 64) * 100 + 50
        splatmap = generate_splatmap(dem)
        assert splatmap.shape == (64, 64, 4)
        assert splatmap.dtype == np.uint8

    def test_splatmap_channels_sum(self):
        """Splatmap channels should approximately sum to 255 per pixel."""
        from mvp.terrain_textures import generate_splatmap

        dem = np.random.rand(32, 32) * 200 + 50
        splatmap = generate_splatmap(dem)
        channel_sum = splatmap.astype(int).sum(axis=-1)
        # Rounding from float→uint8 loses up to 4 per pixel (1 per channel)
        assert np.all(channel_sum >= 251)
        assert np.all(channel_sum <= 259)

    def test_export_splatmap_creates_file(self):
        """export_splatmap should create a PNG file."""
        import tempfile

        from mvp.terrain_textures import export_splatmap

        dem = np.random.rand(64, 64) * 100 + 50
        out = Path(tempfile.mkdtemp()) / "splatmap.png"
        result = export_splatmap(dem, out)
        assert result.exists()
        assert result.suffix == ".png"


class TestD8FlowAccumulation:
    """Tests for D8 flow direction and accumulation algorithms."""

    def _make_sloped_dem(self, size=32):
        """Create a DEM that slopes from top-left to bottom-right with a valley."""
        rows = np.arange(size).reshape(-1, 1)
        cols = np.arange(size).reshape(1, -1)
        # Base slope: elevation decreases toward bottom-right
        dem = 100.0 - rows * 2.0 - cols * 0.5
        # Add valley in the middle column
        center = size // 2
        for c in range(size):
            dem[:, c] += 3.0 * np.exp(-((c - center) ** 2) / (2.0 * (size / 8) ** 2))
        # Invert valley (make it lower)
        dem[:, center] -= 5.0
        return dem.astype(np.float64)

    def test_flow_direction_basic(self):
        """D8 flow directions should point downhill."""
        from mvp.river_flow import compute_flow_direction_d8_fast

        dem = self._make_sloped_dem()
        flow_dir = compute_flow_direction_d8_fast(dem)
        # No cell should be unassigned except possibly pits at edges
        assert flow_dir.shape == dem.shape
        # Most cells should have a valid direction (0-7)
        valid = np.sum(flow_dir >= 0)
        assert valid > dem.size * 0.9

    def test_flow_accumulation_shape(self):
        """Flow accumulation should have same shape as DEM."""
        from mvp.river_flow import compute_flow_accumulation

        dem = self._make_sloped_dem()
        acc = compute_flow_accumulation(dem)
        assert acc.shape == dem.shape
        # All cells should have at least 1 (themselves)
        assert np.all(acc >= 1.0)

    def test_flow_accumulation_valley_has_high_values(self):
        """Valley cells should have higher accumulation than ridges."""
        from mvp.river_flow import compute_flow_accumulation

        dem = self._make_sloped_dem(size=64)
        acc = compute_flow_accumulation(dem)
        center = 32
        # Max accumulation should be near the valley center
        max_row, max_col = np.unravel_index(np.argmax(acc), acc.shape)
        assert abs(max_col - center) < 10  # Within 10 cells of center column

    def test_trace_river_d8_produces_path(self):
        """D8 river tracing should produce a non-trivial path."""
        from mvp.river_flow import trace_river_d8

        dem = self._make_sloped_dem(size=64)
        path = trace_river_d8(dem)
        assert len(path) > 10  # Should trace a meaningful path

    def test_trace_river_d8_goes_downhill(self):
        """D8 traced path should be monotonically decreasing in elevation."""
        from mvp.river_flow import trace_river_d8

        dem = self._make_sloped_dem(size=64)
        path = trace_river_d8(dem)
        elevations = [dem[r, c] for r, c in path]
        # Should be mostly non-increasing (allow tiny float errors)
        for i in range(1, len(elevations)):
            assert elevations[i] <= elevations[i - 1] + 0.01

    def test_trace_river_upstream_finds_source(self):
        """Upstream tracing should find path from source to outlet."""
        from mvp.river_flow import trace_river_upstream_d8

        dem = self._make_sloped_dem(size=64)
        path = trace_river_upstream_d8(dem)
        assert len(path) > 10
        # First point should be higher than last
        assert dem[path[0]] >= dem[path[-1]]

    def test_river_widths_from_accumulation(self):
        """Width computation should produce reasonable values."""
        from mvp.river_flow import (
            compute_flow_accumulation,
            compute_river_widths_from_accumulation,
            trace_river_d8,
        )

        dem = self._make_sloped_dem(size=64)
        acc = compute_flow_accumulation(dem)
        path = trace_river_d8(dem)
        widths = compute_river_widths_from_accumulation(acc, path)
        assert len(widths) == len(path)
        assert np.all(widths >= 5.0)
        assert np.all(widths <= 80.0)
        # Width should generally increase downstream
        assert widths[-1] >= widths[0]


class TestWeather:
    def test_get_seasonal_weather_valid_months(self):
        """Test seasonal weather returns valid data for all 12 months."""
        from mvp.weather import get_seasonal_weather

        for month in range(1, 13):
            data = get_seasonal_weather(month)
            assert "temperature_celsius" in data
            assert "wind_speed_ms" in data
            assert "cloud_cover_fraction" in data
            assert "sunrise_hour" in data
            assert "sunset_hour" in data
            assert 0.0 <= data["cloud_cover_fraction"] <= 1.0
            assert data["sunrise_hour"] < data["sunset_hour"]

    def test_get_seasonal_weather_summer_warmer(self):
        """Test that summer is warmer than winter."""
        from mvp.weather import get_seasonal_weather

        winter = get_seasonal_weather(1)
        summer = get_seasonal_weather(7)
        assert summer["temperature_celsius"] > winter["temperature_celsius"]
        assert summer["daylight_hours"] > winter["daylight_hours"]

    def test_build_weather_data_offline(self):
        """Test building weather data without network access."""
        from mvp.weather import build_weather_data

        data = build_weather_data(month=6, fetch_live=False)
        assert "seasonal" in data
        assert "active" in data
        assert "unity_params" in data
        assert data["unity_params"]["sunrise_hour"] < 6.0  # Early sunrise in June at 58N
        assert data["unity_params"]["sunset_hour"] > 20.0  # Late sunset

    def test_export_weather_json(self, tmp_path):
        """Test exporting weather data to JSON file."""
        from mvp.weather import export_weather_json

        output = tmp_path / "weather_data.json"
        export_weather_json(output, fetch_live=False, month=5)

        assert output.exists()
        data = json.loads(output.read_text())
        assert data["location"]["name"] == "Nidelven, Agder"
        assert "unity_params" in data
        assert data["unity_params"]["wind_speed"] > 0

    def test_unity_params_valid_ranges(self):
        """Test that Unity parameters are in valid ranges."""
        from mvp.weather import build_weather_data

        for month in (1, 4, 7, 10):
            data = build_weather_data(month=month, fetch_live=False)
            p = data["unity_params"]
            assert 0 <= p["fog_density"] <= 0.1
            assert 0 <= p["cloud_cover"] <= 1.0
            assert 0 <= p["sun_intensity_multiplier"] <= 2.0
            assert p["water_wave_height"] > 0
            assert p["water_wave_speed"] > 0

