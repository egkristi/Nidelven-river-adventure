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


class TestKartverketDem:
    def test_wgs84_to_utm33n_known_point(self):
        """Test WGS84→UTM33N conversion against a known point (Arendal)."""
        from mvp.kartverket_dem import wgs84_to_utm33n

        # Arendal city center: approximately 8.77°E, 58.46°N
        # UTM33N (central meridian 15°E): E~136800, N~6488000
        easting, northing = wgs84_to_utm33n(8.77, 58.46)
        assert 130000 < easting < 145000
        assert 6485000 < northing < 6500000

    def test_wgs84_to_utm33n_bbox_order(self):
        """Test that UTM coordinates maintain correct spatial ordering."""
        from mvp.kartverket_dem import wgs84_to_utm33n

        # East should have higher easting, North should have higher northing
        e_min, n_min = wgs84_to_utm33n(8.45, 58.38)
        e_max, n_max = wgs84_to_utm33n(8.85, 58.62)
        assert e_max > e_min
        assert n_max > n_min

    def test_download_kartverket_dtm_returns_none_on_bad_bbox(self):
        """Test that invalid bbox returns None gracefully."""
        from mvp.kartverket_dem import download_kartverket_dtm

        # Use an impossibly small bbox that's outside Norway
        result = download_kartverket_dtm(
            bbox=(0.0, 0.0, 0.01, 0.01),
            max_retries=1,
        )
        # Should return None (either network error or WCS exception)
        assert result is None

    def test_get_kartverket_dem_cache_miss(self, tmp_path):
        """Test that get_kartverket_dem handles missing cache gracefully."""
        from mvp.kartverket_dem import get_kartverket_dem

        # With no network and no cache, should return None
        result = get_kartverket_dem(tmp_path, bbox=(0.0, 0.0, 0.01, 0.01), resolution=100.0)
        assert result is None


class TestNorgeIBilder:
    """Tests for Norge i bilder WMTS orthophoto client."""

    def test_wgs84_to_tile_known_point(self):
        """Test coordinate-to-tile conversion for known values."""
        from mvp.norgeibilder import wgs84_to_tile

        # Oslo (59.9°N, 10.7°E) at zoom 10
        x, y = wgs84_to_tile(10.7, 59.9, 10)
        # Should be roughly in the expected range for Norway
        assert 500 < x < 600
        assert 270 < y < 320

    def test_tile_to_wgs84_roundtrip(self):
        """Test that tile_to_wgs84 is inverse of wgs84_to_tile."""
        from mvp.norgeibilder import tile_to_wgs84, wgs84_to_tile

        lon, lat = 8.6, 58.5  # Nidelven area
        zoom = 15
        x, y = wgs84_to_tile(lon, lat, zoom)
        lon2, lat2 = tile_to_wgs84(x, y, zoom)
        # Should be close to original (within one tile)
        assert abs(lon2 - lon) < 0.02
        assert abs(lat2 - lat) < 0.02

    def test_get_tile_bounds_nidelven(self):
        """Test tile bounds for Nidelven area."""
        from mvp.norgeibilder import NIDELVEN_BBOX, get_tile_bounds

        x_min, y_min, x_max, y_max = get_tile_bounds(NIDELVEN_BBOX, zoom=15)
        # Should have a reasonable number of tiles
        num_x = x_max - x_min + 1
        num_y = y_max - y_min + 1
        assert 1 <= num_x <= 50
        assert 1 <= num_y <= 50
        # x_min < x_max and y_min < y_max
        assert x_min <= x_max
        assert y_min <= y_max

    def test_get_tile_bounds_small_area(self):
        """Test tile bounds for a very small bounding box."""
        from mvp.norgeibilder import get_tile_bounds

        # Tiny area — should result in 1 tile
        bbox = (8.6, 58.5, 8.601, 58.501)
        x_min, y_min, x_max, y_max = get_tile_bounds(bbox, zoom=10)
        num_tiles = (x_max - x_min + 1) * (y_max - y_min + 1)
        assert num_tiles >= 1

    def test_download_orthophoto_exceeds_max_tiles(self):
        """Test that exceeding max_tiles raises ValueError."""
        import pytest

        from mvp.norgeibilder import NIDELVEN_BBOX, download_orthophoto

        # Very low max_tiles should trigger the safety limit
        with pytest.raises(ValueError, match="exceeding max_tiles"):
            download_orthophoto(NIDELVEN_BBOX, zoom=18, max_tiles=5)

    def test_download_tile_returns_none_on_invalid(self):
        """Test that download_tile handles network failure gracefully."""
        from mvp.norgeibilder import download_tile

        # Use zoom 0, tile 0,0 — unlikely to have Norge i bilder data
        # but also tests network failure handling
        result = download_tile(0, 0, zoom=0, timeout=2)
        # May return None or an image depending on network availability
        assert result is None or hasattr(result, "size")

    def test_export_terrain_texture_no_network(self, tmp_path):
        """Test export_terrain_texture handles download failure gracefully."""
        from mvp.norgeibilder import export_terrain_texture

        # Use a bbox far from Norway where tiles don't exist
        result = export_terrain_texture(
            bbox=(0.0, 0.0, 0.001, 0.001),
            output_dir=tmp_path,
            zoom=10,
            texture_size=256,
        )
        # Should return None when no tiles can be downloaded
        # (or a path if somehow tiles exist)
        assert result is None or (result is not None and result.exists())


class TestQgisExport:
    """Tests for QGIS export module."""

    def _make_dem_and_river(self):
        """Create a simple test DEM and river path."""
        dem = np.zeros((64, 64), dtype=np.float32)
        # Simple valley: high on edges, low in center
        for y in range(64):
            for x in range(64):
                dem[y, x] = 100 + abs(x - 32) * 5 - y * 0.5
        # River path down the center
        river_path = [(y, 32) for y in range(5, 60)]
        return dem, river_path

    def test_export_dem_geotiff(self, tmp_path):
        """Test DEM export as GeoTIFF."""
        from mvp.qgis_export import export_dem_geotiff

        dem, _ = self._make_dem_and_river()
        output = tmp_path / "test_dem.tif"
        result = export_dem_geotiff(dem, output)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_export_river_geojson(self, tmp_path):
        """Test river path export as GeoJSON."""
        from mvp.qgis_export import export_river_geojson

        dem, river_path = self._make_dem_and_river()
        output = tmp_path / "test_river.geojson"
        result = export_river_geojson(river_path, dem, output)
        assert result.exists()

        with open(result) as f:
            geojson = json.load(f)

        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 1
        feature = geojson["features"][0]
        assert feature["geometry"]["type"] == "LineString"
        coords = feature["geometry"]["coordinates"]
        assert len(coords) == len(river_path)
        # Each coordinate should have [lon, lat, elevation]
        assert len(coords[0]) == 3
        # Properties should include metadata
        assert "name" in feature["properties"]
        assert feature["properties"]["num_points"] == len(river_path)

    def test_export_river_geojson_with_widths(self, tmp_path):
        """Test GeoJSON export includes width/speed properties."""
        from mvp.qgis_export import export_river_geojson

        dem, river_path = self._make_dem_and_river()
        widths = [5.0] * len(river_path)
        speeds = [1.5] * len(river_path)
        output = tmp_path / "river_props.geojson"
        export_river_geojson(river_path, dem, output, widths=widths, speeds=speeds)

        with open(output) as f:
            geojson = json.load(f)

        props = geojson["features"][0]["properties"]
        assert props["avg_width_m"] == 5.0
        assert props["avg_speed_ms"] == 1.5

    def test_generate_qgis_project(self, tmp_path):
        """Test QGIS project file generation."""
        from mvp.qgis_export import (
            export_dem_geotiff,
            export_river_geojson,
            generate_qgis_project,
        )

        dem, river_path = self._make_dem_and_river()

        # Create source files
        dem_tif = tmp_path / "dem.tif"
        export_dem_geotiff(dem, dem_tif)
        river_geojson = tmp_path / "river.geojson"
        export_river_geojson(river_path, dem, river_geojson)

        # Generate project
        result = generate_qgis_project(tmp_path, dem_path=dem_tif, river_path=river_geojson)
        assert result.exists()
        assert result.suffix == ".qgs"

        # Should be valid XML
        import xml.etree.ElementTree as ET

        tree = ET.parse(result)
        root = tree.getroot()
        assert root.tag == "qgis"
        assert root.get("projectname") == "Nidelven River Adventure"

    def test_export_for_qgis_full(self, tmp_path):
        """Test the complete export_for_qgis pipeline."""
        from mvp.qgis_export import export_for_qgis

        dem, river_path = self._make_dem_and_river()
        flow_acc = np.ones_like(dem) * 10  # Dummy flow accumulation

        result = export_for_qgis(
            dem=dem,
            river_path_pixels=river_path,
            output_dir=tmp_path,
            flow_accumulation=flow_acc,
        )

        assert "dem" in result
        assert "river" in result
        assert "flow_accumulation" in result
        assert "project" in result

        # All files should exist
        for path in result.values():
            assert path.exists()

        # QGIS dir should be created
        qgis_dir = tmp_path / "qgis"
        assert qgis_dir.exists()

    def test_export_for_qgis_minimal(self, tmp_path):
        """Test export with empty river path."""
        from mvp.qgis_export import export_for_qgis

        dem = np.random.default_rng(42).uniform(50, 200, (32, 32)).astype(np.float32)

        result = export_for_qgis(
            dem=dem,
            river_path_pixels=[],
            output_dir=tmp_path,
        )

        assert "dem" in result
        assert "river" in result
        assert "project" in result


class TestCLI:
    """Integration tests for the CLI entry point (main.py)."""

    def test_main_sample_skip_render(self, tmp_path, monkeypatch):
        """Test --sample --skip-render produces terrain + river outputs."""
        import sys

        monkeypatch.setattr(
            sys, "argv", ["nidelven", "--sample", "--skip-render", "--output-dir", str(tmp_path)]
        )
        from mvp.main import main

        main()

        # Should produce terrain files
        assert (tmp_path / "terrain.obj").exists()
        assert (tmp_path / "terrain.raw").exists()
        assert (tmp_path / "terrain_metadata.json").exists()
        # Should produce river files
        assert (tmp_path / "river_path.csv").exists()

    def test_main_sample_skip_all(self, tmp_path, monkeypatch):
        """Test --sample --skip-terrain --skip-river --skip-render runs without error."""
        import sys

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "nidelven",
                "--sample",
                "--skip-terrain",
                "--skip-river",
                "--skip-render",
                "--output-dir",
                str(tmp_path),
            ],
        )
        from mvp.main import main

        main()
        # Should not crash; output dir may be empty since everything was skipped

    def test_main_sample_with_qgis(self, tmp_path, monkeypatch):
        """Test --sample --qgis --skip-render produces QGIS outputs."""
        import sys

        monkeypatch.setattr(
            sys,
            "argv",
            ["nidelven", "--sample", "--qgis", "--skip-render", "--output-dir", str(tmp_path)],
        )
        from mvp.main import main

        main()

        qgis_dir = tmp_path / "qgis"
        assert qgis_dir.exists()
        assert (qgis_dir / "dem_elevation.tif").exists()
        assert (qgis_dir / "river_path.geojson").exists()
        assert (qgis_dir / "nidelven.qgs").exists()

    def test_main_sample_produces_unity_raw(self, tmp_path, monkeypatch):
        """Test that --sample exports Unity-ready RAW heightmap + metadata."""
        import sys

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "nidelven",
                "--sample",
                "--skip-river",
                "--skip-render",
                "--output-dir",
                str(tmp_path),
            ],
        )
        from mvp.main import main

        main()

        assert (tmp_path / "terrain.raw").exists()
        metadata_file = tmp_path / "terrain_metadata.json"
        assert metadata_file.exists()

        import json

        metadata = json.loads(metadata_file.read_text())
        assert "resolution" in metadata
        assert "min_elevation_m" in metadata

    def test_main_sample_river_path_json(self, tmp_path, monkeypatch):
        """Test that river pipeline produces river_path.json for Unity."""
        import sys

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "nidelven",
                "--sample",
                "--skip-terrain",
                "--skip-render",
                "--output-dir",
                str(tmp_path),
            ],
        )
        from mvp.main import main

        main()

        river_csv = tmp_path / "river_path.csv"
        assert river_csv.exists()
        # CSV should have content (header + at least 1 data row)
        lines = river_csv.read_text().strip().split("\n")
        assert len(lines) >= 2


class TestNveHydapi:
    """Tests for NVE HydAPI river flow client."""

    def test_get_seasonal_flow_default(self):
        """Test seasonal flow returns valid structure."""
        from mvp.nve_hydapi import get_seasonal_flow

        result = get_seasonal_flow(month=6)
        assert "discharge_m3s" in result
        assert "stage_m" in result
        assert "flow_speed_ms" in result
        assert "river_width_m" in result
        assert result["source"] == "climate_normals"
        assert result["month"] == 6

    def test_get_seasonal_flow_all_months(self):
        """Test seasonal flow for all 12 months."""
        from mvp.nve_hydapi import get_seasonal_flow

        for month in range(1, 13):
            result = get_seasonal_flow(month=month)
            assert result["discharge_m3s"] > 0
            assert result["stage_m"] > 0
            assert result["flow_speed_ms"] > 0
            assert result["river_width_m"] > 20

    def test_get_seasonal_flow_spring_flood(self):
        """Test that spring months have higher discharge."""
        from mvp.nve_hydapi import get_seasonal_flow

        spring = get_seasonal_flow(month=5)  # May = peak snowmelt
        winter = get_seasonal_flow(month=2)  # Feb = low flow
        assert spring["discharge_m3s"] > winter["discharge_m3s"]

    def test_build_river_physics_params(self):
        """Test conversion to Unity physics parameters."""
        from mvp.nve_hydapi import build_river_physics_params

        flow_data = {
            "discharge_m3s": 50.0,
            "stage_m": 1.5,
            "flow_speed_ms": 1.2,
            "river_width_m": 37.5,
            "temp_c": 14.0,
            "source": "test",
        }
        params = build_river_physics_params(flow_data)
        assert "flow_speed" in params
        assert "river_width" in params
        assert "water_depth" in params
        assert "turbulence" in params
        assert "current_strength" in params
        assert "water_clarity" in params
        assert 0.3 <= params["flow_speed"] <= 3.0
        assert 0.0 <= params["turbulence"] <= 1.0
        assert 0.0 <= params["current_strength"] <= 1.0
        assert 0.0 <= params["water_clarity"] <= 1.0

    def test_build_river_physics_params_extreme_flow(self):
        """Test physics params with extreme discharge values."""
        from mvp.nve_hydapi import build_river_physics_params

        # Very high flow (flood)
        flood = build_river_physics_params(
            {"discharge_m3s": 200.0, "flow_speed_ms": 4.0, "river_width_m": 60.0}
        )
        assert flood["flow_speed"] == 3.0  # Clamped to max
        assert flood["turbulence"] >= 0.9

        # Very low flow
        low = build_river_physics_params(
            {"discharge_m3s": 5.0, "flow_speed_ms": 0.1, "river_width_m": 30.0}
        )
        assert low["flow_speed"] == 0.3  # Clamped to min
        assert low["turbulence"] < 0.1

    def test_export_flow_json(self, tmp_path):
        """Test JSON export with seasonal data (no network)."""
        from mvp.nve_hydapi import export_flow_json

        result = export_flow_json(tmp_path, fetch_live=False, month=7)
        assert result.exists()
        assert result.name == "flow_data.json"

        data = json.loads(result.read_text())
        assert "flow_data" in data
        assert "physics_params" in data
        assert "stations" in data
        assert data["flow_data"]["source"] == "climate_normals"

    def test_default_statistics(self):
        """Test fallback statistics."""
        from mvp.nve_hydapi import _default_statistics

        stats = _default_statistics()
        assert stats["mean_discharge_m3s"] > 0
        assert stats["min_discharge_m3s"] < stats["max_discharge_m3s"]


class TestNibioAr5:
    """Tests for NIBIO AR5 land cover client."""

    def test_classify_features_empty(self):
        """Test classification with empty feature collection."""
        from mvp.nibio_ar5 import classify_features

        result = classify_features({"type": "FeatureCollection", "features": []})
        assert result == []

    def test_classify_features_basic(self):
        """Test classification of a simple forest polygon."""
        from mvp.nibio_ar5 import classify_features

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"arealtype": 30, "treslag": 31},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[8.5, 58.4], [8.6, 58.4], [8.6, 58.5], [8.5, 58.5], [8.5, 58.4]]
                        ],
                    },
                }
            ],
        }
        result = classify_features(geojson)
        assert len(result) == 1
        assert result[0]["class"] == "forest"
        assert result[0]["forest_type"] == "spruce"
        assert result[0]["arealtype"] == 30

    def test_classify_features_multiple(self):
        """Test classification with multiple land cover types."""
        from mvp.nibio_ar5 import classify_features

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"arealtype": 30, "treslag": 32},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [8.5, 58.5],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {"arealtype": 20, "treslag": 0},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [8.6, 58.5],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {"arealtype": 80, "treslag": 0},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [8.55, 58.45],
                    },
                },
            ],
        }
        result = classify_features(geojson)
        assert len(result) == 3
        classes = [r["class"] for r in result]
        assert "forest" in classes
        assert "agriculture" in classes
        assert "freshwater" in classes

    def test_get_vegetation_params(self):
        """Test vegetation parameter lookup."""
        from mvp.nibio_ar5 import get_vegetation_params

        forest = get_vegetation_params("forest")
        assert forest["tree_density"] > 0.5
        assert forest["grass_density"] < forest["tree_density"]

        water = get_vegetation_params("freshwater")
        assert water["tree_density"] == 0.0
        assert water["grass_density"] == 0.0

        # Unknown class returns defaults
        unknown = get_vegetation_params("martian_landscape")
        assert "tree_density" in unknown

    def test_generate_vegetation_map(self):
        """Test rasterized vegetation map generation."""
        from mvp.nibio_ar5 import generate_vegetation_map

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"arealtype": 30},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [8.5, 58.4],
                                [8.6, 58.4],
                                [8.6, 58.5],
                                [8.5, 58.5],
                                [8.5, 58.4],
                            ]
                        ],
                    },
                }
            ],
        }
        veg_map = generate_vegetation_map(
            geojson,
            dem_shape=(64, 64),
            bbox=(8.45, 58.38, 8.85, 58.62),
        )
        assert veg_map.shape == (64, 64)
        assert veg_map.dtype == np.uint8
        # Should have some forest (30) cells
        assert np.any(veg_map == 30)

    def test_build_unity_vegetation_data(self):
        """Test Unity vegetation data structure."""
        from mvp.nibio_ar5 import build_unity_vegetation_data, classify_features

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"arealtype": 30, "treslag": 31},
                    "geometry": {"type": "Point", "coordinates": [8.5, 58.5]},
                },
                {
                    "type": "Feature",
                    "properties": {"arealtype": 20, "treslag": 0},
                    "geometry": {"type": "Point", "coordinates": [8.6, 58.5]},
                },
            ],
        }
        classified = classify_features(geojson)
        data = build_unity_vegetation_data(classified)

        assert "class_distribution" in data
        assert "forest_types" in data
        assert "zones" in data
        assert data["source"] == "nibio_ar5"
        assert len(data["zones"]) == 2

    def test_export_vegetation_json_offline(self, tmp_path):
        """Test JSON export without network (default data)."""
        from mvp.nibio_ar5 import export_vegetation_json

        result = export_vegetation_json(tmp_path, fetch_live=False)
        assert result.exists()
        assert result.name == "vegetation_data.json"

        data = json.loads(result.read_text())
        assert "class_distribution" in data
        assert "forest_types" in data
        assert data["source"] == "default_estimate"

    def test_default_vegetation_data(self):
        """Test default vegetation data structure."""
        from mvp.nibio_ar5 import _default_vegetation_data

        data = _default_vegetation_data((8.45, 58.38, 8.85, 58.62))
        assert data["source"] == "default_estimate"
        assert "forest" in data["class_distribution"]
        assert data["class_distribution"]["forest"] > 0

    def test_extract_coordinates_multipolygon(self):
        """Test coordinate extraction from MultiPolygon."""
        from mvp.nibio_ar5 import _extract_coordinates

        geometry = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[8.5, 58.4], [8.6, 58.4], [8.6, 58.5], [8.5, 58.5], [8.5, 58.4]]],
                [[[8.7, 58.4], [8.8, 58.4], [8.8, 58.5], [8.7, 58.5], [8.7, 58.4]]],
            ],
        }
        coords = _extract_coordinates(geometry)
        assert len(coords) == 10  # 5 + 5 points


class TestArtsdatabanken:
    """Tests for the Artsdatabanken species observation client."""

    def test_get_species_list_all(self):
        """Test getting full species list."""
        from mvp.artsdatabanken import get_species_list

        species = get_species_list()
        assert "birds" in species
        assert "fish" in species
        assert "mammals" in species
        assert len(species["birds"]) >= 4
        assert len(species["fish"]) >= 3
        assert len(species["mammals"]) >= 4

    def test_get_species_list_filtered(self):
        """Test getting species list for a single group."""
        from mvp.artsdatabanken import get_species_list

        birds = get_species_list("birds")
        assert "birds" in birds
        assert "fish" not in birds
        assert "mammals" not in birds

    def test_get_species_list_unknown_group(self):
        """Test unknown group returns all species."""
        from mvp.artsdatabanken import get_species_list

        result = get_species_list("aliens")
        assert "birds" in result
        assert "fish" in result

    def test_build_wildlife_spawn_data(self):
        """Test building Unity spawn data from species list."""
        from mvp.artsdatabanken import build_wildlife_spawn_data

        data = build_wildlife_spawn_data()
        assert "categories" in data
        assert "version" in data
        assert data["source"] == "Artsdatabanken/GBIF"

        # Check birds category
        birds = data["categories"]["birds"]
        assert birds["prefab_type"] == "Bird"
        assert birds["species_count"] >= 4
        assert birds["flight_capable"] is True
        assert birds["despawn_distance"] == 150.0

        # Check fish category
        fish = data["categories"]["fish"]
        assert fish["prefab_type"] == "Fish"
        assert fish["spawn_height_offset"] == -0.5

        # Check spawn probabilities sum to ~1.0
        for group, cat in data["categories"].items():
            total_prob = sum(s["spawn_probability"] for s in cat["species"])
            assert 0.99 <= total_prob <= 1.01, f"{group} probabilities sum to {total_prob}"

    def test_build_wildlife_spawn_data_seasonal_filter(self):
        """Test seasonal filtering removes off-season species."""
        from mvp.artsdatabanken import build_wildlife_spawn_data

        # January — salmon not in peak season (peak: Jun-Sep)
        winter_data = build_wildlife_spawn_data(month=1)
        fish_species = [s["scientific_name"] for s in winter_data["categories"]["fish"]["species"]]
        assert "Salmo salar" not in fish_species

        # July — salmon in peak season
        summer_data = build_wildlife_spawn_data(month=7)
        fish_species = [s["scientific_name"] for s in summer_data["categories"]["fish"]["species"]]
        assert "Salmo salar" in fish_species

    def test_build_wildlife_spawn_data_custom_species(self):
        """Test with custom species data."""
        from mvp.artsdatabanken import build_wildlife_spawn_data

        custom = {
            "birds": [
                {
                    "scientific_name": "Testus birdus",
                    "english_name": "Test bird",
                    "norwegian_name": "Testfugl",
                    "habitat": "river",
                    "abundance": "common",
                    "spawn_weight": 1.0,
                }
            ]
        }
        data = build_wildlife_spawn_data(species_data=custom)
        assert data["categories"]["birds"]["species_count"] == 1
        assert data["categories"]["birds"]["species"][0]["spawn_probability"] == 1.0

    def test_export_wildlife_json(self, tmp_path):
        """Test JSON export of wildlife data."""
        from mvp.artsdatabanken import export_wildlife_json

        result = export_wildlife_json(tmp_path, fetch_live=False)
        assert result.exists()
        assert result.name == "wildlife_data.json"

        with open(result) as f:
            data = json.load(f)

        assert "categories" in data
        assert "birds" in data["categories"]
        assert "fish" in data["categories"]
        assert "mammals" in data["categories"]
        total = sum(c["species_count"] for c in data["categories"].values())
        assert total >= 10  # We have at least 10 curated species

    def test_merge_with_offline(self):
        """Test merging live observations with offline data."""
        from mvp.artsdatabanken import _merge_with_offline

        live_obs = [
            {"scientific_name": "Cinclus cinclus", "english_name": "Dipper"},
            {"scientific_name": "Picus viridis", "english_name": "Green woodpecker"},
        ]
        merged = _merge_with_offline("birds", live_obs)

        # Should include all offline birds + the new live one
        names = [s["scientific_name"] for s in merged]
        assert "Cinclus cinclus" in names  # Already in offline
        assert "Picus viridis" in names  # New from live
        # Should not duplicate
        assert names.count("Cinclus cinclus") == 1

    def test_spawner_categories(self):
        """Test spawner category configuration."""
        from mvp.artsdatabanken import SPAWNER_CATEGORIES

        assert "birds" in SPAWNER_CATEGORIES
        assert "fish" in SPAWNER_CATEGORIES
        assert "mammals" in SPAWNER_CATEGORIES

        # Verify sensible values
        assert SPAWNER_CATEGORIES["birds"]["max_count"] > 0
        assert SPAWNER_CATEGORIES["fish"]["spawn_height_offset"] < 0  # underwater
        assert SPAWNER_CATEGORIES["mammals"]["spawn_height_offset"] == 0.0


class TestNvdbBridges:
    """Tests for the NVDB bridge data client."""

    def test_get_bridge_list(self):
        """Test getting offline bridge list."""
        from mvp.nvdb_bridges import get_bridge_list

        bridges = get_bridge_list()
        assert len(bridges) >= 4
        for bridge in bridges:
            assert "name" in bridge
            assert "latitude" in bridge
            assert "longitude" in bridge
            assert "length_m" in bridge
            assert bridge["latitude"] > 58.0
            assert bridge["longitude"] > 8.0

    def test_build_bridge_data(self):
        """Test building Unity-ready bridge data."""
        from mvp.nvdb_bridges import build_bridge_data

        data = build_bridge_data()
        assert data["version"] == "1.0"
        assert data["source"] == "NVDB (Statens vegvesen)"
        assert data["license"] == "NLOD"
        assert data["bridge_count"] >= 4

        for bridge in data["bridges"]:
            assert "name" in bridge
            assert "position" in bridge
            assert "dimensions" in bridge
            assert "prefab" in bridge
            assert bridge["dimensions"]["length"] > 0
            assert bridge["dimensions"]["width"] > 0
            assert bridge["dimensions"]["clearance"] > 0

    def test_build_bridge_data_custom(self):
        """Test building data from custom bridge list."""
        from mvp.nvdb_bridges import build_bridge_data

        custom = [
            {
                "name": "Test Bridge",
                "road": "E18",
                "latitude": 58.45,
                "longitude": 8.6,
                "length_m": 100.0,
                "width_m": 10.0,
                "clearance_m": 2.0,
                "bridge_type": "arch",
                "material": "stone",
            }
        ]
        data = build_bridge_data(custom)
        assert data["bridge_count"] == 1
        assert data["bridges"][0]["prefab"] == "BridgeArch"
        assert data["bridges"][0]["is_obstacle"] is True

    def test_bridge_obstacle_detection(self):
        """Test that low-clearance bridges are flagged as obstacles."""
        from mvp.nvdb_bridges import build_bridge_data

        low = [
            {
                "name": "Low",
                "road": "FV1",
                "latitude": 58.5,
                "longitude": 8.5,
                "length_m": 30.0,
                "width_m": 5.0,
                "clearance_m": 2.5,
                "bridge_type": "beam",
                "material": "concrete",
            }
        ]
        high = [
            {
                "name": "High",
                "road": "E18",
                "latitude": 58.5,
                "longitude": 8.5,
                "length_m": 100.0,
                "width_m": 12.0,
                "clearance_m": 8.0,
                "bridge_type": "beam",
                "material": "concrete",
            }
        ]
        assert build_bridge_data(low)["bridges"][0]["is_obstacle"] is True
        assert build_bridge_data(high)["bridges"][0]["is_obstacle"] is False

    def test_classify_bridge_type(self):
        """Test bridge type classification."""
        from mvp.nvdb_bridges import _classify_bridge_type

        assert _classify_bridge_type({"Konstruksjon": "Buebru"}) == "arch"
        assert _classify_bridge_type({"Konstruksjon": "Hengebru"}) == "suspension"
        assert _classify_bridge_type({"Konstruksjon": "Fagverksbru"}) == "truss"
        assert _classify_bridge_type({"Konstruksjon": "Platebru"}) == "beam"
        assert _classify_bridge_type({}) == "beam"

    def test_parse_wkt_centroid(self):
        """Test WKT geometry centroid extraction."""
        from mvp.nvdb_bridges import _parse_wkt_centroid

        wkt = "LINESTRING (8.5 58.4, 8.6 58.5)"
        lat, lon = _parse_wkt_centroid(wkt)
        assert abs(lat - 58.45) < 0.01
        assert abs(lon - 8.55) < 0.01

        lat, lon = _parse_wkt_centroid("")
        assert lat is None
        assert lon is None

    def test_export_bridge_json(self, tmp_path):
        """Test JSON export of bridge data."""
        from mvp.nvdb_bridges import export_bridge_json

        result = export_bridge_json(tmp_path, fetch_live=False)
        assert result.exists()
        assert result.name == "bridge_data.json"

        with open(result) as f:
            data = json.load(f)

        assert "bridges" in data
        assert data["bridge_count"] >= 4
        assert data["bridges"][0]["position"]["latitude"] > 58.0

    def test_safe_conversions(self):
        """Test safe float/int conversion helpers."""
        from mvp.nvdb_bridges import _safe_float, _safe_int

        assert _safe_float("3.14") == 3.14
        assert _safe_float(None) is None
        assert _safe_float("not_a_number") is None
        assert _safe_int("42") == 42
        assert _safe_int(None) is None
        assert _safe_int("abc") is None


class TestKartverketBuildings:
    """Tests for the Kartverket FKB-Bygning building client."""

    def test_get_building_list(self):
        """Test getting offline building list."""
        from mvp.kartverket_buildings import get_building_list

        buildings = get_building_list()
        assert len(buildings) >= 5
        for b in buildings:
            assert "name" in b
            assert "latitude" in b
            assert "longitude" in b
            assert "type_code" in b
            assert b["latitude"] > 58.0
            assert b["longitude"] > 8.0

    def test_build_building_data(self):
        """Test building Unity-ready data."""
        from mvp.kartverket_buildings import build_building_data

        data = build_building_data()
        assert data["version"] == "1.0"
        assert data["source"] == "Kartverket FKB-Bygning (Matrikkelen)"
        assert data["license"] == "NLOD"
        assert data["building_count"] >= 5

        for b in data["buildings"]:
            assert "name" in b
            assert "position" in b
            assert "dimensions" in b
            assert "prefab" in b
            assert "category" in b
            assert b["dimensions"]["height"] > 0
            assert b["dimensions"]["width"] > 0

    def test_build_building_data_custom(self):
        """Test building data from custom list."""
        from mvp.kartverket_buildings import build_building_data

        custom = [
            {
                "name": "Test House",
                "type_code": 111,
                "latitude": 58.5,
                "longitude": 8.6,
                "height_m": 8.0,
                "footprint_m2": 100.0,
                "year_built": 2000,
            }
        ]
        data = build_building_data(custom)
        assert data["building_count"] == 1
        assert data["buildings"][0]["category"] == "residential"
        assert data["buildings"][0]["prefab"] == "BuildingResidential"
        assert data["buildings"][0]["dimensions"]["height"] == 8.0

    def test_classify_building(self):
        """Test building type classification."""
        from mvp.kartverket_buildings import classify_building

        assert classify_building(111) == "residential"
        assert classify_building(150) == "residential"
        assert classify_building(211) == "industrial"
        assert classify_building(321) == "commercial"
        assert classify_building(411) == "transport"
        assert classify_building(520) == "hospitality"
        assert classify_building(611) == "cultural"
        assert classify_building(750) == "health"
        assert classify_building(999) == "other"
        assert classify_building(None) == "other"

    def test_is_landmark(self):
        """Test landmark detection logic."""
        from mvp.kartverket_buildings import _is_landmark

        # Named building is landmark
        assert _is_landmark({"name": "Froland kirke"}) is True
        # Unnamed building is not landmark
        assert _is_landmark({"name": ""}) is False
        # Tall building is landmark
        assert _is_landmark({"name": "", "height_m": 15.0}) is True
        # Large footprint is landmark
        assert _is_landmark({"name": "", "footprint_m2": 600.0}) is True
        # Small unnamed is not
        assert _is_landmark({"name": "", "height_m": 5.0, "footprint_m2": 50.0}) is False

    def test_extract_centroid_point(self):
        """Test centroid extraction from Point geometry."""
        from mvp.kartverket_buildings import _extract_centroid

        lat, lon = _extract_centroid([8.5, 58.4], "Point")
        assert abs(lat - 58.4) < 0.01
        assert abs(lon - 8.5) < 0.01

    def test_extract_centroid_polygon(self):
        """Test centroid extraction from Polygon geometry."""
        from mvp.kartverket_buildings import _extract_centroid

        coords = [[[8.5, 58.4], [8.6, 58.4], [8.6, 58.5], [8.5, 58.5], [8.5, 58.4]]]
        lat, lon = _extract_centroid(coords, "Polygon")
        assert abs(lat - 58.44) < 0.05
        assert abs(lon - 8.54) < 0.05

    def test_extract_centroid_empty(self):
        """Test centroid extraction with empty data."""
        from mvp.kartverket_buildings import _extract_centroid

        lat, lon = _extract_centroid([], "Point")
        assert lat is None
        assert lon is None

    def test_export_building_json(self, tmp_path):
        """Test JSON export of building data."""
        from mvp.kartverket_buildings import export_building_json

        result = export_building_json(tmp_path, fetch_live=False)
        assert result.exists()
        assert result.name == "building_data.json"

        with open(result) as f:
            data = json.load(f)

        assert "buildings" in data
        assert data["building_count"] >= 5
        assert data["buildings"][0]["position"]["latitude"] > 58.0

    def test_safe_conversions(self):
        """Test safe float/int conversion helpers."""
        from mvp.kartverket_buildings import _safe_float, _safe_int

        assert _safe_float("3.14") == 3.14
        assert _safe_float(None) is None
        assert _safe_int("42") == 42
        assert _safe_int(None) is None


class TestXenoCanto:
    """Tests for xeno-canto bird audio client."""

    def test_get_bird_audio_list(self):
        from mvp.xenocanto import get_bird_audio_list

        birds = get_bird_audio_list()
        assert len(birds) == 6
        assert all("scientific_name" in b for b in birds)
        assert all("call_type" in b for b in birds)

    def test_bird_audio_species(self):
        from mvp.xenocanto import get_bird_audio_list

        birds = get_bird_audio_list()
        species = [b["scientific_name"] for b in birds]
        assert "Cinclus cinclus" in species  # Fossekall
        assert "Alcedo atthis" in species  # Isfugl

    def test_parse_duration(self):
        from mvp.xenocanto import _parse_duration

        assert _parse_duration("1:30") == 90.0
        assert _parse_duration("0:45") == 45.0
        assert _parse_duration("1:00:00") == 3600.0
        assert _parse_duration("invalid") == 0.0

    def test_build_audio_manifest_offline(self):
        from mvp.xenocanto import build_audio_manifest

        manifest = build_audio_manifest({})
        assert manifest["version"] == "1.0"
        assert manifest["species_count"] == 6
        assert len(manifest["bird_calls"]) == 6
        # Offline mode uses placeholder recordings
        for call in manifest["bird_calls"]:
            assert len(call["recordings"]) == 1
            assert call["recordings"][0]["quality"] == "offline"

    def test_build_audio_manifest_with_recordings(self):
        from mvp.xenocanto import build_audio_manifest

        recordings = {
            "Cinclus cinclus": [
                {
                    "id": "12345",
                    "file_url": "https://example.com/song.mp3",
                    "duration_s": 45.0,
                    "quality": "A",
                    "license": "CC-BY-NC-SA",
                    "recordist": "Test User",
                }
            ]
        }
        manifest = build_audio_manifest(recordings)
        dipper = next(c for c in manifest["bird_calls"] if c["species"] == "Cinclus cinclus")
        assert dipper["recordings"][0]["id"] == "12345"
        assert dipper["recordings"][0]["duration_s"] == 45.0

    def test_habitat_zones(self):
        from mvp.xenocanto import get_bird_audio_list

        birds = get_bird_audio_list()
        zones = {b["habitat_zone"] for b in birds}
        assert "river" in zones
        assert "river_bank" in zones
        assert "waterfall" in zones

    def test_volume_weights(self):
        from mvp.xenocanto import get_bird_audio_list

        birds = get_bird_audio_list()
        for bird in birds:
            assert 0.0 < bird["volume_weight"] <= 1.0

    def test_export_offline(self, tmp_path):
        from mvp.xenocanto import export_bird_audio_json

        output = tmp_path / "bird_audio.json"
        result = export_bird_audio_json(output, fetch_live=False)
        assert output.exists()
        assert result["species_count"] == 6
        with open(output) as f:
            data = json.load(f)
        assert data["source"] == "xeno-canto.org"

    def test_parse_recording(self):
        from mvp.xenocanto import _parse_recording

        rec = {
            "id": "99999",
            "file": "https://xc.org/99999/download",
            "file-name": "XC99999.mp3",
            "length": "2:15",
            "q": "A",
            "type": "song",
            "rec": "Recorder Name",
            "lic": "//creativecommons.org/licenses/by-nc-sa/4.0/",
            "cnt": "Norway",
            "loc": "Arendal",
            "lat": "58.45",
            "lng": "8.77",
        }
        parsed = _parse_recording(rec)
        assert parsed["id"] == "99999"
        assert parsed["duration_s"] == 135.0
        assert parsed["latitude"] == 58.45
        assert parsed["country"] == "Norway"


class TestLakseregisteret:
    """Tests for Lakseregisteret salmon data client."""

    def test_get_salmon_data(self):
        from mvp.lakseregisteret import get_salmon_data

        data = get_salmon_data()
        assert data["vassdrag"] == "019.Z"
        assert data["river_name"] == "Nidelva"
        assert "Salmo salar" in data["anadromous_species"]

    def test_get_spawning_areas(self):
        from mvp.lakseregisteret import get_spawning_areas

        areas = get_spawning_areas()
        assert len(areas) == 5
        assert all("latitude" in a for a in areas)
        names = [a["name"] for a in areas]
        assert "Bøylefoss" in names
        assert "Rykene" in names

    def test_get_season_info_summer(self):
        from mvp.lakseregisteret import get_season_info

        july = get_season_info(7)
        assert july["activity"] == "adult_migration"
        assert july["visibility"] == "very_high"
        assert july["spawn_chance"] == 0.7

    def test_get_season_info_winter(self):
        from mvp.lakseregisteret import get_season_info

        jan = get_season_info(1)
        assert jan["activity"] == "overwintering"
        assert jan["spawn_chance"] == 0.0

    def test_get_season_info_spawning(self):
        from mvp.lakseregisteret import get_season_info

        sep = get_season_info(9)
        assert sep["activity"] == "spawning"
        assert sep["spawn_chance"] == 1.0

    def test_get_season_info_clamped(self):
        from mvp.lakseregisteret import get_season_info

        # Invalid month should be clamped
        result = get_season_info(0)
        assert "activity" in result
        result2 = get_season_info(13)
        assert "activity" in result2

    def test_build_gameplay_data_july(self):
        from mvp.lakseregisteret import build_gameplay_data

        data = build_gameplay_data(month=7)
        assert data["month"] == 7
        assert len(data["events"]) > 0
        assert data["visual_params"]["fish_visibility"] == "very_high"
        # Should have salmon run events in migration corridors
        event_types = [e["type"] for e in data["events"]]
        assert "salmon_run" in event_types or "fish_ladder_passage" in event_types

    def test_build_gameplay_data_spawning_season(self):
        from mvp.lakseregisteret import build_gameplay_data

        data = build_gameplay_data(month=9)
        event_types = [e["type"] for e in data["events"]]
        assert "salmon_spawning" in event_types
        assert "fish_ladder_passage" in event_types

    def test_build_gameplay_data_winter(self):
        from mvp.lakseregisteret import build_gameplay_data

        data = build_gameplay_data(month=1)
        # In winter, events may still exist but with zero intensity
        for event in data["events"]:
            assert event["intensity"] == 0.0
            assert event["fish_count"] == 0
        assert data["visual_params"]["jumping_frequency"] == 0.0

    def test_regulation_data(self):
        from mvp.lakseregisteret import get_salmon_data

        data = get_salmon_data()
        reg = data["regulation"]
        assert reg["fishing_season_start"] == "06-01"
        assert reg["fishing_season_end"] == "08-31"
        assert reg["daily_quota"] == 3

    def test_export_offline(self, tmp_path):
        from mvp.lakseregisteret import export_salmon_json

        output = tmp_path / "salmon_data.json"
        result = export_salmon_json(output, fetch_live=False, month=8)
        assert output.exists()
        assert result["vassdrag"] == "019.Z"
        with open(output) as f:
            data = json.load(f)
        assert "spawning_areas" in data
        assert "gameplay" in data


class TestDybdedata:
    """Tests for Kartverket Dybdedata (bathymetry) client."""

    def test_get_depth_profiles(self):
        from mvp.dybdedata import get_depth_profiles

        profiles = get_depth_profiles()
        assert len(profiles) == 7
        assert all("max_depth_m" in p for p in profiles)
        assert all("avg_depth_m" in p for p in profiles)

    def test_depth_profile_locations(self):
        from mvp.dybdedata import get_depth_profiles

        profiles = get_depth_profiles()
        names = [p["name"] for p in profiles]
        assert "Arendal havn (utløp)" in names
        assert "Rykene" in names
        assert "Bøylefoss (nedenfor dam)" in names

    def test_depth_ranges_realistic(self):
        from mvp.dybdedata import get_depth_profiles

        profiles = get_depth_profiles()
        for p in profiles:
            assert 0 < p["avg_depth_m"] <= p["max_depth_m"]
            assert p["max_depth_m"] <= 15.0  # River, not ocean
            assert p["width_m"] > 0

    def test_get_depth_at_position(self):
        from mvp.dybdedata import get_depth_at_position

        # Test near Rykene
        result = get_depth_at_position(58.445, 8.605)
        assert "avg_depth_m" in result
        assert "width_m" in result
        assert result["avg_depth_m"] > 0

    def test_get_depth_interpolation(self):
        from mvp.dybdedata import get_depth_at_position

        # Midpoint between two profiles should interpolate
        result = get_depth_at_position(58.460, 8.600)
        assert 1.0 < result["avg_depth_m"] < 8.0

    def test_build_depth_grid(self):
        from mvp.dybdedata import build_depth_grid

        grid_data = build_depth_grid(grid_points=20)
        assert grid_data["grid_points"] == 20
        assert grid_data["profiles_used"] == 7
        assert len(grid_data["grid"]) == 20
        assert grid_data["depth_range_m"]["min"] > 0
        assert grid_data["depth_range_m"]["max"] > grid_data["depth_range_m"]["min"]

    def test_depth_grid_continuity(self):
        from mvp.dybdedata import build_depth_grid

        grid_data = build_depth_grid(grid_points=50)
        grid = grid_data["grid"]
        # Grid should have monotonic t values
        for i in range(len(grid) - 1):
            assert grid[i]["t"] < grid[i + 1]["t"]
        # All depths positive
        for point in grid:
            assert point["avg_depth_m"] > 0
            assert point["max_depth_m"] > 0

    def test_extract_layer_names(self):
        from mvp.dybdedata import _extract_layer_names

        xml = "<Name>layer1</Name><Name>layer2</Name>"
        layers = _extract_layer_names(xml)
        assert layers == ["layer1", "layer2"]

    def test_extract_layer_names_empty(self):
        from mvp.dybdedata import _extract_layer_names

        layers = _extract_layer_names("")
        assert layers == []

    def test_estimate_resolution(self):
        from mvp.dybdedata import _estimate_resolution

        bbox = {"min_lon": 8.72, "min_lat": 58.38, "max_lon": 8.80, "max_lat": 58.43}
        res = _estimate_resolution(bbox, 256, 256)
        assert 1.0 < res < 50.0  # Should be reasonable resolution in meters

    def test_export_offline(self, tmp_path):
        from mvp.dybdedata import export_bathymetry_json

        output = tmp_path / "bathymetry.json"
        result = export_bathymetry_json(output, fetch_live=False)
        assert output.exists()
        assert result["version"] == "1.0"
        with open(output) as f:
            data = json.load(f)
        assert "profiles" in data
        assert "depth_grid" in data
        assert len(data["profiles"]) == 7
