# Nidelven River Adventure — Roadmap & Project Audit

Last updated: 2026-05-14 (Phase 2 nearly complete, Phase 3+4 complete)

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

---

## Executive Summary

The project has a **complete Unity codebase** (16 fully implemented scripts, URP shader, scene) and a **working Python terrain pipeline** (DEM download, mesh generation, river tracing, preview rendering). CI/CD is operational with automated Windows + Linux builds.

However, the two halves are **not connected** — the Python pipeline output is not automatically imported into Unity. The game will compile and build, but the player will only experience a synthetic terrain until the real DEM data integration is completed.

> ✅ **Phase 0 complete** — security issues fixed, Python lint clean, critical bugs resolved (see Resolved Issues below).
> ✅ **Phase 1 complete** — boat+camera wired to terrain, Input System fixed, integration pipeline working, CI producing playable builds.

---

## Current Status

| Component | State | Confidence |
|-----------|-------|-----------|
| Python MVP pipeline | ✅ Functional | DEM download, mesh gen, river flow, renderer, lint clean |
| Unity scripts (16) | ✅ Compile & build | All logic implemented, all bugs fixed |
| CI — Python | ✅ Passing | Lint (strict), format, tests, pipeline run |
| CI — Unity Test | ✅ Passing | Compiles in game-ci Docker (6000.4.5f1) |
| CI — Unity Build | ✅ Producing artifacts | Win64 + Linux64 + macOS, 7-day retention |
| CodeQL | ✅ Passing | Python security scanning |
| Integration (Python→Unity) | ✅ RAW export pipeline | `export_unity_raw()` → StreamingAssets auto-load |
| Playable experience | ✅ First playable | Boat+camera on real DEM terrain, CI build artifacts |

---

## ~~🔴 Critical — Security~~ ✅ RESOLVED

| # | Issue | Resolution |
|---|-------|------------|
| S1 | Unity license key committed to repo | ✅ Removed from CI_SETUP.md, replaced with safe instructions |
| S2 | Secrets exposed to all CI jobs | ✅ Scoped to unity-test and unity-build jobs only |
| S3 | Unity `.alf` activation file | ✅ Added `*.alf`/`*.ulf` to .gitignore (was never tracked) |

---

## 🟠 Bugs — Must Fix Before Playtest

### Python MVP

| # | Bug | File | Impact |
|---|-----|------|--------|
| P1 | ~~Broken package imports~~ | ✅ Fixed — all relative imports |
| P2 | ~~Wrong BBOX~~ | ✅ Fixed — (8.45, 58.38, 8.85, 58.62) covers Nidelva |
| P3 | ~~NaN fill broken~~ | ✅ Fixed — uses distance_transform_edt indices correctly |
| P4 | ~~Interactive renderer never loads data~~ | ✅ Fixed — `__init__` now reads class attrs from `run_renderer()` |
| P5 | ~~River start logic inverted~~ | ✅ Fixed — uses `argmax` (highest = headwater) instead of `argmin` |
| P6 | ~~Missing `import math`~~ | ✅ Fixed |

### Unity

| # | Bug | File | Impact |
|---|-----|------|--------|
| U1 | ~~RiverController `riverWidths` IndexOutOfRange~~ | ✅ Fixed — added initial width/speed for point 0 |
| U2 | ~~Shader property `_FlowOffset` not declared~~ | ✅ Fixed — added to shader Properties + CBUFFER |
| U3 | ~~SaveManager.lastPosition not initialized~~ | ✅ Fixed — initialized from boatController in Awake() |
| U4 | ~~WildlifeSpawner compares progress to distance~~ | ✅ Fixed — now computes actual world distance to river path |

---

## 🟡 Warnings — Should Fix

### Architecture

| # | Issue | Impact |
|---|-------|--------|
| A1 | ~~Two unconnected terrain importers~~ | ✅ Fixed — removed `KartverketDemImporter`, single RAW pipeline |
| A2 | `TerrainGenerator.LoadGeoTiff()` doesn't parse TIFF headers — reads raw bytes | Will produce garbage with real GeoTIFF files |
| A3 | ~~Legacy Input API + New Input System~~ | ✅ Fixed — `activeInputHandler` set to 2 (Both) |
| A4 | ~~Escape key handled by both `GameManager` and `SettingsMenu`~~ | ✅ Fixed — SettingsMenu only consumes Escape when panel is open |
| A5 | ~~Python `kartverket_dem.py` is dead code~~ | ✅ Fixed — removed |
| A6 | ~~`scripts/` directory appears orphaned~~ | ✅ Fixed — removed |

### Performance

| # | Issue | Impact |
|---|-------|--------|
| PF1 | ~~`terrain_mesh.py` vertex generation uses Python for-loops (262k iterations)~~ | ✅ Vectorized with numpy |
| PF2 | ~~`VegetationGenerator.RenderInstanced()` allocates arrays every frame~~ | ✅ Fixed — pre-allocated batches |
| PF3 | `PhotoMode.ApplyFilters()` iterates every pixel on CPU | Multi-second freeze on capture at 2x resolution |
| PF4 | ~~`AudioManager` moves its own transform to player position~~ | ✅ Fixed — uses child objects |

### CI/CD

| # | Issue | Impact |
|---|-------|--------|
| C1 | Unity version mismatch: project is 6000.4.6f1, CI uses 6000.4.5f1 | Potential shader/serialization differences |
| C2 | Lint/format steps use `\|\| true` — never fail | No code quality gate |
| C3 | No uv/pip caching in Python job | ~30s wasted per run |
| C4 | No artifact retention configured (90-day default) | Storage cost for 500MB+ builds |
| C5 | ~~Release workflow deadlocks when Unity secrets are missing~~ | ✅ Fixed — `if: always()` condition added |

---

## 📊 Test Coverage

| Module | Covered | Not Covered |
|--------|---------|-------------|
| `minimal.py` | `create_sample_dem_ascii` | `trace_river_path`, `render_ascii`, `render_html` |
| `terrain_mesh.py` | `generate_mesh`, `calculate_normals`, `export_unity_raw`, NaN handling, multi-size | `load_dem` (partial), `save_mesh_obj` |
| `river_flow.py` | `find_start_point` (all sides), `trace_river_path`, `smooth_path`, `calculate_flow_properties`, D8 flow direction, accumulation, trace, upstream, widths | `generate_river_mesh` |
| `terrain_textures.py` | `compute_slope`, `generate_splatmap`, `export_splatmap` | — |
| `weather.py` | `get_seasonal_weather`, `build_weather_data`, `export_weather_json`, `unity_params` | `fetch_live_weather`, `fetch_historical_weather` (network) |
| `dem_downloader.py` | `create_sample_dem` | `download_dem_copernicus`, `get_dem_path` |
| `nve_river.py` | `extract_river_path`, `_merge_segments`, `save/load_river_path` | `fetch_river_geometry` (network), `get_nidelva_path` |
| `headless_renderer.py` | ❌ | All (rendering, hard to unit test) |
| `renderer.py` | ❌ | All (OpenGL, hard to unit test) |
| `camera.py` | ❌ | All (OpenGL, hard to unit test) |
| `main.py` | ❌ | All (CLI orchestration) |

**Core module coverage: terrain_mesh 69%, river_flow 46%, dem_downloader 30%+.** 44 tests passing. Integration test included.

---

## Resolved Issues (Historical)

| Issue | Title | Resolution |
|-------|-------|------------|
| #19 | CI: Scope secrets, pin version, add caching | Secrets scoped, 6000.4.6f1, UV cache, lint gate |
| #18 | Fix Unity bugs: RiverController + shader | riverWidths fix + _FlowOffset in shader |
| #17 | Fix Python MVP: imports, BBOX, NaN fill | Relative imports, correct coords, NaN fix |
| #16 | Security: Remove credential leak | Credentials removed from CI_SETUP.md |
| #15 | Add interactive 3D renderer | ModernGL renderer as optional dep |
| #14 | Download real DEM data | Copernicus GLO-30 from AWS S3 |
| #13 | Remove large terrain.obj from history | git-filter-repo |
| #12 | Add Unity scene to enable builds | MainScene.unity + EditorBuildSettings |

---

## Roadmap

### Phase 0: Critical Fixes ✅ COMPLETE

- [x] **S1** Remove credentials from CI_SETUP.md
- [x] **S2** Scope CI secrets to Unity jobs only
- [x] **S3** Add `*.alf`/`*.ulf` to .gitignore
- [x] **P1** Fix bare imports → relative imports
- [x] **P2** Correct BBOX to Nidelva (8.45, 58.38, 8.85, 58.62)
- [x] **P3** Fix NaN fill in terrain_mesh.py
- [x] **P6** Add missing `import math` in kartverket_dem.py
- [x] **U1** Fix RiverController riverWidths index-out-of-range
- [x] **U2** Add `_FlowOffset` property to SimpleWater.shader
- [x] **C1** Pin CI Unity version to 6000.4.6f1
- [x] **C2** Remove `|| true` from lint/format steps
- [x] **C3** Add UV caching to Python CI job
- [x] **C4** Add 7-day artifact retention
- [x] Auto-fix 500+ lint issues, all code now passes ruff + black

### Phase 1: Playable Scene (v0.1.0)

- [x] Create main Unity scene
- [x] Enable Unity build in CI
- [x] Fix remaining Unity bugs (U3, U4)
- [x] Fix `TerrainGenerator.LoadGeoTiff()` — replaced with RAW format auto-load from StreamingAssets
- [x] Build pipeline: Python `export_unity_raw()` → Unity StreamingAssets auto-load
- [x] Fix Input System configuration (set to "Both")
- [x] Add test for `export_unity_raw` (8 tests passing)
- [x] Wire up boat + camera with real terrain in scene
- [x] First playable build with real terrain (CI produces Win64 + Linux64 artifacts)

### Phase 2: Data Quality (v0.2.0)

- [x] Download real DEM (Copernicus GLO-30, 30m)
- [x] Fix NaN handling in terrain_mesh.py
- [x] D8 flow accumulation algorithm for river tracing ✔️ (b21800d)
- [x] River widths from upstream drainage area (Leopold-Maddock) ✔️ (b21800d)
- [x] Implement proper river path from NVE ELVIS data ✔️
- [x] Export river path JSON for Unity RiverController ✔️
- [x] Procedural terrain splatmap (slope/elevation/flow-based) ✔️ (0ee1826)
- [x] Add DEM integrity verification (checksum) ✔️
- [x] Vectorize terrain mesh generation (eliminate Python for-loops) ✔️
- [ ] Upgrade DEM to Kartverket DTM 1m LiDAR (where available)
- [x] Import river geometry from NVE Elvenett / ELVIS ✔️
- [x] Auto-generate terrain.raw + river_path.json + splatmap in CI builds ✔️
- [x] Weather integration (MET Norway Locationforecast + Frost + seasonal) ✔️ (980ae49)

### Phase 3: Polish (v0.3.0) ✅ COMPLETE

- [x] Fix water shader flow animation (_FlowOffset)
- [x] Add `DepthOnly` pass to water shader ✔️
- [x] Fix vegetation GPU instancing (pre-allocate batches) ✔️
- [x] Fix AudioManager 3D spatialization (child objects for sources) ✔️
- [x] Remove debug OnGUI overlays (gated behind `#if UNITY_EDITOR`) ✔️
- [x] Add proper water depth/transparency (depth texture sampling) ✔️
- [x] Particle effects (splash, foam, mist) ✔️
- [x] LOD system for vegetation (distance-based culling) ✔️

### Phase 4: CI/CD Hardening ✅ COMPLETE

- [x] Remove `|| true` from lint/format CI steps
- [x] Add uv caching to Python job
- [x] Configure artifact retention (7 days CI)
- [x] Fix release workflow deadlock (needs: with proper `if:`)
- [x] Pin Unity version in release.yml ✔️
- [x] Add integration test (full pipeline end-to-end)
- [x] Increase test coverage — 23 tests, core modules 46-69%
- [x] Remove dead code (kartverket_dem.py, scripts/, KartverketDemImporter.cs)
- [x] Fix architecture warnings (A1, A4, A5, A6)

### Phase 5: Game Experience (v1.0.0)

- [ ] Complete tutorial flow with real terrain
- [ ] Balance boat physics + stamina
- [ ] Sound design pass (real recordings or quality samples)
- [ ] Multiple save slots with preview screenshots
- [ ] Steam achievements for river milestones
- [ ] Settings menu with URP quality presets
- [ ] Localization (Norwegian / English)
- [x] Performance profiling + optimization pass ✔️

---

## Geolocated Data Sources

Free, open data sources that can improve terrain, textures, river accuracy, and environmental detail for the Nidelven valley (Agder, Norway).

| Source | Data Type | Resolution | Access | Use Case |
|--------|-----------|-----------|--------|----------|
| **Kartverket DTM** (høydedata.no) | LiDAR DEM | 1m | Free WCS/download | Replace 30m Copernicus DEM with 1m terrain |
| **Norge i bilder** (norgeibilder.no) | Aerial orthophoto | 10-25 cm | Free WMS/WMTS | Terrain texturing — real ground cover |
| **Sentinel-2** (Copernicus) | Multispectral satellite | 10m | Free (AWS S3) | Terrain color, vegetation classification |
| **NVE Elvenett / ELVIS** | River centerlines + catchments | Vector | Free GeoJSON/WFS | Accurate river path (replaces gradient descent) |
| **Kartverket N50** | Topographic vector map | 1:50000 | Free WFS | Roads, buildings, water bodies, land use |
| **OpenStreetMap** | Crowd-sourced vector | Variable | Free (Overpass API) | River path, bridges, points of interest |
| **Kartverket sjøkart** | Bathymetry | 1-5m | Free WMS | River depth data for realistic water |
| **NIBIO AR5** | Land cover classification | 1:5000 | Free WFS | Forest type, farmland, wetland → vegetation placement |
| **Met.no Frost API** | Weather/climate | Station data | Free REST API | Realistic weather patterns, seasonal variation |

### Integration Plan

1. **Terrain (Priority):** Kartverket DTM 1m via høydedata.no WCS → drastically better terrain than current 30m
2. **Textures (Priority):** Norge i bilder WMTS → real aerial photo as terrain texture (splatmap from NIBIO AR5 for procedural detail)
3. **River path:** NVE ELVIS GeoJSON → import exact Nidelva centerline, width, and flow direction
4. **Vegetation:** NIBIO AR5 land cover → place correct tree species (pine/spruce/birch) by zone
5. **Fallback:** Sentinel-2 10m satellite as lower-quality texture alternative (no auth needed, global coverage)

### API Endpoints (Nidelven area: ~8.45°E, 58.38°N to 8.85°E, 58.62°N)

```
# Kartverket DTM 1m (WCS)
https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?service=WCS&version=2.0.1&request=GetCoverage

# Norge i bilder orthophoto (WMTS)
https://opencache.statkart.no/gatekeeper/gk/gk.open_nib_web_mercator_wmts_v2?SERVICE=WMTS

# NVE ELVIS river network (WFS)
https://gis3.nve.no/map/services/Elvenett/MapServer/WFSServer

# NIBIO AR5 land cover (WFS)
https://wfs.nibio.no/wfs/ar5?service=WFS&version=2.0.0&request=GetFeature

# Sentinel-2 (AWS S3, no auth)
s3://sentinel-cogs/sentinel-s2-l2a-cogs/{year}/{tile}/
```

> **Note:** All Norwegian public geodata listed above is free for any use (CC BY 4.0 or NLOD). Sentinel-2 is CC BY-SA 3.0 IGO.

---

## Technical Debt Register

| Item | Severity | Effort | Notes |
|------|----------|--------|-------|
| ~~Dead code: `kartverket_dem.py`~~ | ~~Low~~ | — | ✅ Removed |
| ~~Dead code: `scripts/` directory~~ | ~~Low~~ | — | ✅ Removed |
| ~~Duplicate dev deps in pyproject.toml~~ | ~~Low~~ | — | ✅ Fixed (ruff+black added to dependency-groups) |
| ~~`--size` and `--download` CLI args unused~~ | ~~Low~~ | — | ✅ Removed |
| ~~`camera.py` coordinate mismatch~~ | ~~Medium~~ | — | ✅ Fixed (col→X, row→Z) |
| ~~Python for-loop mesh generation~~ | ~~Medium~~ | — | ✅ Vectorized with numpy |
| Frame-rate-dependent camera smoothing | Low | 15 min | Use `SmoothDamp` instead of `Lerp` |
| Legacy UI (UnityEngine.UI) vs TMPro | Low | 2 hr | Migrate to TextMeshPro when ready |
| Cinemachine 2.x → 3.x | Low | 2 hr | Optional; 2.x still works in Unity 6 |

---

## Architecture Notes

```
┌─────────────────────────────────────────────────────┐
│ Python MVP Pipeline (mvp/src/mvp/)                  │
│                                                     │
│  dem_downloader.py → terrain_mesh.py → river_flow.py│
│       ↓                    ↓               ↓       │
│  Copernicus S3       OBJ mesh         CSV path     │
│  (30m GeoTIFF)       + normals        + velocity   │
│       ↓                    ↓               ↓       │
│  headless_renderer.py (preview images)              │
│  renderer.py (interactive 3D viewer, optional)      │
│  export_unity_raw() → terrain.raw + metadata.json   │
└────────────────────────┬────────────────────────────┘
                         │ ← StreamingAssets/terrain.raw
┌────────────────────────▼────────────────────────────┐
│ Unity Game (Assets/)                                 │
│                                                     │
│  TerrainGenerator ← loads DEM → generates terrain   │
│  RiverController  ← generates river mesh + flow     │
│  BoatController   ← physics on river                │
│  RiverCamera      ← follows boat/river              │
│  VegetationGenerator, WildlifeSpawner, DayNight...  │
└─────────────────────────────────────────────────────┘
```

**Integration: CONNECTED** — Python `export_unity_raw()` exports RAW 16-bit heightmap + JSON metadata → Unity `StreamingAssets/` → `TerrainGenerator` auto-loads at runtime via `LoadRawDem()`. Pipeline tested end-to-end.

---

## PC Requirements

### Minimum
- OS: Windows 10/11 64-bit
- CPU: Intel i5-8400 / AMD Ryzen 5 2600
- RAM: 16 GB
- GPU: GTX 1060 6GB / RX 580
- Storage: 2 GB SSD

### Build
```bash
git clone https://github.com/egkristi/Nidelven-river-adventure.git
cd Nidelven-river-adventure
# Open in Unity 6000 LTS
# File → Build Settings → Build
```

---

## Next Steps (Optional)

- Fix CI workflows (#11)
- Weather effects (rain, fog)
- Multiplayer co-op
- VR support
- Additional rivers

---

## Real-World Data Sources — Evaluation & Integration Plan

This section catalogs all identified real-life data sources relevant to building an authentic Nidelva river experience. Each source is rated for relevance, accessibility, and integration effort.

**Rating scale**: ★★★★★ Essential | ★★★★ High | ★★★ Medium | ★★ Low | ★ Skip

### Category 1: Terrain & Elevation

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **Kartverket DTM 10** (10m DEM) | ★★★★★ | NLOD/CC-BY | GeoTIFF | 3× better resolution than current Copernicus 30m. Available via Geonorge download |
| **Kartverket DTM 1** (1m LiDAR) | ★★★★★ | NLOD/CC-BY | GeoTIFF/LAZ | Best available terrain. LiDAR point cloud for Agder. Massive but incredible detail |
| **Copernicus GLO-30** (30m) | ★★★★ | Free | GeoTIFF | ✅ Already integrated. Adequate for MVP, upgrade to DTM 10 later |
| **Kartverket Dybdedata** (river/sea depth) | ★★★★★ | NLOD | GeoTIFF/S-57 | Critical for realistic river depth simulation and underwater terrain |

**API/Download**: https://kartkatalog.geonorge.no/ → Search "DTM 10" or "Dybdedata"

### Category 2: Hydrology & River Data

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **NVE HydAPI** (water discharge/level) | ★★★★★ | NLOD | REST JSON | Real-time & historical water flow for Nidelva stations. Drives realistic current speed |
| **NVE ELVIS Elvenett** (river network) | ★★★★★ | NLOD | GeoJSON/Shape | Authoritative river centerline geometry — replaces our gradient-descent river tracing |
| **NVE Flomsoner** (flood zones) | ★★★ | NLOD | WMS/Shape | Flood risk zones along Nidelva. Useful for dynamic flood events |
| **NVE Sildre** (hydrological viz) | ★★★ | NLOD | Web/API | Visualization of historical flow — useful for balancing river physics |
| **NVE Vannkraft** (hydropower) | ★★★★ | NLOD | WMS | Dam and power station locations on Nidelva (gameplay obstacles/landmarks) |

**API**: https://hydapi.nve.no/ (free API key required)  
**Stations on Nidelva**: Search "Nidelva" or county "Agder" in HydAPI  
**Parameters**: Discharge (1001), Water stage (1000), Water temperature (1003)

### Category 3: Aerial Imagery & Satellite

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **Norge i bilder** (aerial ortho) | ★★★★★ | Restricted | WMS/WMTS | 10-25cm resolution aerial photos of entire Nidelva corridor. Perfect terrain textures |
| **Sentinel-2** (satellite) | ★★★★ | Free/Copernicus | GeoTIFF | 10m multispectral. Good for seasonal vegetation colors, water detection |
| **Kartverket N50 Raster** | ★★★ | NLOD | TIFF | 1:50000 topographic maps — useful as minimap overlay |

**Access**: https://norgeibilder.no/ (WMS) | https://dataspace.copernicus.eu/ (Sentinel-2)

### Category 4: Infrastructure & Buildings

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **Kartverket FKB-Bygning** (buildings) | ★★★★★ | NLOD | GML/GeoJSON | Detailed 2.5D building footprints with heights. Place houses along riverbank |
| **Kartverket Matrikkelen** (building points) | ★★★★ | NLOD | GeoJSON | Building registry — type, year, size. Useful for LOD decisions |
| **NVDB API V4** (road database) | ★★★★ | NLOD | REST JSON | Roads, bridges, tunnels, barriers, guardrails. Bridges crossing Nidelva! |
| **Bane NOR** (railway) | ★★★ | Open | GeoJSON | Sørlandsbanen railway bridge crosses Nidelva — recognizable landmark |
| **OpenStreetMap** (OSM) | ★★★★ | ODbL | PBF/GeoJSON | Community-mapped paths, buildings, POIs, waterways. Good fallback |
| **Kartverket FKB-Veg** (roads detail) | ★★★★ | NLOD | GML | Road geometry including small farm roads along the river |

**API**: https://nvdbapiles.atlas.vegvesen.no/ (V4, no auth for read)  
**Overpass API** (OSM): https://overpass-api.de/

### Category 5: Wildlife & Biodiversity

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **Artsdatabanken/Artskart** (species obs.) | ★★★★★ | CC-BY | REST API | 60M+ observations. Query species seen along Nidelva — exact bird, fish, mammal lists |
| **GBIF** (global biodiversity) | ★★★★ | CC-BY/CC0 | REST/DwC-A | Includes Artsdatabanken data + international records. Good for species metadata |
| **NIBIO Dyreportalen** (wildlife) | ★★★★ | NLOD | WMS | Deer, moose, fox, otter observations with heat maps |
| **Lakseregisteret** (salmon registry) | ★★★★★ | Open | Web | Nidelva IS a famous salmon river. Spawning data, catch statistics, regulations |
| **xeno-canto** (bird sounds) | ★★★★★ | CC-BY-NC | MP3/API | Species-specific recordings. Generate authentic soundscape per location/season |
| **Fiskeridirektoratet** (fishing) | ★★★ | Open | WMS/API | Fishing regulations, catch zones along Nidelva |

**API**: https://artskart.artsdatabanken.no/ (REST, query by bounding box)  
**xeno-canto**: https://xeno-canto.org/api/2/recordings?query=cnt:norway  
**Key species for Nidelva**: Atlantic salmon, sea trout, otter, kingfisher, dipper, grey heron, beaver

### Category 6: Weather & Atmosphere

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **MET Norway Frost API** (historical) | ★★★★★ | CC-BY | REST JSON | Temperature, precipitation, wind, humidity. Drive dynamic weather system |
| **MET Norway Yr API** (forecast) | ★★★★ | CC-BY | REST JSON | Location forecast. Could drive real-time weather in game |
| **NVE SeNorge** (snow/water/temp grids) | ★★★ | NLOD | NetCDF/WMS | Gridded daily data — snow depth, soil moisture, evaporation |
| **MET Norway Thredds** (radar/satellite) | ★★ | CC-BY | NetCDF | Precipitation radar — overkill for game, but impressive visual |

**API**: https://frost.met.no/ (free, auth via client_id)  
**Yr API**: https://api.met.no/weatherapi/locationforecast/2.0/  
**Stations near Nidelva**: Arendal (SN37230), Froland (nearby stations)

### Category 7: Maritime & AIS

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **Barentswatch AIS** (ship tracking) | ★★★★ | Open (delayed) | REST/CSV | Historic ship movements in Arendal harbor/fjord. Animate real vessel traffic |
| **Kystverket Hovedled/Biled** (fairways) | ★★★ | NLOD | GeoJSON | Navigation lanes at Nidelva mouth (Arendal port) |
| **Kystverket Navigasjonsinnretninger** | ★★ | NLOD | WMS | Lighthouses, buoys, navigation marks at river mouth |

**API**: https://ais.barentswatch.no/ (requires account, 3-min delay on public)

### Category 8: Land Use & Vegetation

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **NIBIO AR5** (land resource map) | ★★★★★ | NLOD | GeoJSON/WMS | Detailed classification: forest type, bog, agriculture, water. Drives vegetation generator |
| **NIBIO Skogportalen** (forest) | ★★★★ | NLOD | WMS | Forest density, tree species, height. Accurate tree placement |
| **CORINE Land Cover** | ★★★ | Free | GeoTIFF | 100m European land cover. Too coarse for detail but good for large-scale biomes |
| **Miljødirektoratet Naturtyper** | ★★★★ | NLOD | WMS/GeoJSON | Classified nature types — wetland, forest, coastal. Ecosystem accuracy |

**Access**: https://kilden.nibio.no/ (map viewer + WMS)  
**Download**: https://kartkatalog.geonorge.no/ → "FKB-AR5"

### Category 9: Cultural Heritage & POIs

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **Riksantikvaren Askeladden** (heritage) | ★★★★ | NLOD | WMS/API | Protected cultural monuments along Nidelva — old mills, dams, iron works |
| **Miljødirektoratet Friluftsområder** | ★★★ | NLOD | GeoJSON | Mapped outdoor recreation areas — campfire spots, beaches, swimming |
| **SSB Befolkning** (population grids) | ★★ | CC-BY | CSV/Grid | Population density — useful for town sections vs wilderness |

**Access**: https://askeladden.ra.no/ (requires login for detailed data, WMS free)

### Category 10: Traffic & Transportation

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **NVDB Trafikkmengde** (AADT) | ★★★ | NLOD | REST | Average annual daily traffic on roads near river. Ambient traffic sounds |
| **Statens vegvesen Trafikkdata** | ★★★ | NLOD | REST | Real-time and historical vehicle counts at measurement points |
| **OpenSky Network** (flight ADS-B) | ★★ | CC-BY | REST/CSV | Aircraft above. Kjevik airport nearby — occasional plane flyovers |
| **Avinor** (airport data) | ★ | Mixed | API | Flight schedules — marginal relevance |

**API**: https://trafikkdata.atlas.vegvesen.no/ (GraphQL)  
**OpenSky**: https://opensky-network.org/api/ (free, rate-limited)

### Category 11: Sound & Audio

| Source | Rating | License | Format | Notes |
|--------|--------|---------|--------|-------|
| **xeno-canto** (bird songs) | ★★★★★ | CC-BY-NC | MP3 | 800k+ recordings. Filter by species present at Nidelva |
| **Freesound.org** | ★★★★ | CC-BY/CC0 | WAV/MP3 | River sounds, wind, rain, forest ambience, boat creaking |
| **BBC Sound Effects** | ★★★ | RemArc | WAV | High-quality nature recordings (requires attribution) |

### Integration Priority Order

Based on the ratings above, recommended integration order:

1. **NVE ELVIS + HydAPI** — Replace gradient-descent river path with real river geometry + flow data
2. **Kartverket DTM 10** — Upgrade terrain from 30m to 10m resolution
3. **NIBIO AR5** — Drive vegetation placement from real land-use data
4. **Artsdatabanken** — Query real species list for Nidelva → spawn accurate wildlife
5. **xeno-canto** — Download actual bird calls for species present
6. **Kartverket FKB-Bygning** — Place real buildings along riverbanks
7. **MET Frost API** — Historical weather patterns for dynamic weather system
8. **NVDB bridges** — Place real bridges as landmarks/obstacles
9. **Kartverket Dybdedata** — River depth for underwater terrain + boat physics
10. **Norge i bilder** — Aerial photos as terrain textures (if license permits)
11. **Lakseregisteret** — Salmon spawning events as gameplay feature
12. **Barentswatch AIS** — Animate ship traffic near Arendal harbor
13. **Riksantikvaren** — Cultural heritage POIs with info panels

### Data Licensing Summary

| License | Sources | Game Use |
|---------|---------|----------|
| NLOD (Norwegian Open Gov Data) | Kartverket, NVE, NIBIO, NVDB, Kystverket | ✅ Free for any use with attribution |
| CC-BY 4.0 | MET, Artsdatabanken, GBIF, OpenSky | ✅ Free with attribution |
| CC-BY-NC | xeno-canto | ⚠️ Non-commercial only (OK for indie) |
| ODbL | OpenStreetMap | ✅ Free, share-alike for derived databases |
| Copernicus | Sentinel-2, GLO-30 | ✅ Free with attribution |
| Restricted | Norge i bilder (aerial ortho) | ⚠️ Check terms — may require Norge digitalt membership |

---

## License & Data

- Code: MIT License
- Terrain DEM: © ESA/Copernicus (GLO-30), © Kartverket (DTM 10, NLOD)
- River data: © NVE (HydAPI, ELVIS), OpenStreetMap contributors
- Imagery: © ESA (Sentinel-2), © Kartverket/Norge i bilder
- Wildlife: © Artsdatabanken (CC-BY), xeno-canto (CC-BY-NC)
- Weather: © MET Norway (Frost API, CC-BY)
- Infrastructure: © Kartverket (FKB, NLOD), © Statens vegvesen (NVDB, NLOD)
- Land use: © NIBIO (AR5, NLOD)
- Maritime: © Kystverket/Barentswatch (AIS, NLOD)
- Cultural heritage: © Riksantikvaren (Askeladden, NLOD)
