# Nidelven River Adventure — Roadmap & Project Audit

Last updated: 2026-05-15 (Phase 11: NVE HydAPI river flow + NIBIO AR5 land cover integration)

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

---

## Executive Summary

The project has a **complete Unity codebase** (17 scripts, 2 shaders, URP pipeline) and a **working Python terrain pipeline** (DEM download, mesh generation, D8 flow accumulation, river tracing, weather integration, splatmap generation). CI/CD produces automated Win64 + Linux64 + macOS builds on every push.

The Python pipeline exports `terrain.raw` + `river_path.json` + `weather.json` + `flow_data.json` + `vegetation_data.json` → Unity `StreamingAssets/` auto-loads at runtime. **All 11 phases complete.** v1.0.0 feature-complete.

> ✅ **Phase 0** — Security fixes, Python lint clean, critical bugs resolved
> ✅ **Phase 1** — Playable scene, boat+camera on terrain, CI builds
> ✅ **Phase 2** — Real DEM data, D8 flow, NVE river, weather, Kartverket 1m
> ✅ **Phase 3** — Water shader, particles, vegetation LOD, audio spatialization
> ✅ **Phase 4** — CI hardening, test coverage, dead code removal
> ✅ **Phase 5** — Tutorial, localization, achievements, physics, sound design
> ✅ **Phase 6** — Stabilization: all audit Critical/High issues fixed
> ✅ **Phase 7** — Norge i bilder aerial orthophoto terrain textures
> ✅ **Phase 8** — Tech debt: FixedUpdate physics, timeScale, auto-save, CI fix
> ✅ **Phase 9** — Close all open issues: flow perf, CodeQL C#, CLI tests
> ✅ **Phase 10** — CI cleanup: deduplicate workaround, upgrade action-gh-release v2
> ✅ **Phase 11** — NVE HydAPI river flow + NIBIO AR5 land cover data integration

### Full Audit (2026-05-15)

A comprehensive audit was performed covering all Unity C# scripts, Python pipeline modules, and CI/CD workflows. **58 issues** identified across all layers:

| Layer | Critical | High | Medium | Low | Total |
|-------|----------|------|--------|-----|-------|
| Unity C# | 2 | 7 | 12 | 8 | 29 |
| Python pipeline | 3 | 5 | 9 | 9 | 26 |
| CI/CD workflows | 2 | 4 | 8 | 7 | 21 |

GitHub issues filed: #26, #27, #28, #29, #30, #31, #32

---

## Current Status

| Component | State | Confidence |
|-----------|-------|-----------|
| Python MVP pipeline | ✅ Functional (82 tests) | DEM, mesh, D8 flow, river, splatmap, weather, orthophoto, QGIS export, HydAPI, AR5, CLI — all lint clean |
| Unity scripts (17) | ✅ Compile clean (0 warnings) | All logic implemented, deprecated APIs fixed |
| CI — Python | ✅ Passing | Ruff + Black + pytest + pipeline smoke test |
| CI — Unity Test | ✅ Passing | Compiles in game-ci Docker (6000.4.5f1) |
| CI — Unity Build | ✅ Producing artifacts | Win64 + Linux64 + macOS |
| CodeQL | ✅ Passing | Python + C# security scanning |
| Integration (Python→Unity) | ✅ Complete | `export_unity_raw()` + `river_path.json` + `weather.json` → StreamingAssets |
| Playable experience | ✅ Feature-complete | Tutorial, localization, achievements, physics, sound |
| Audit status | ✅ All issues resolved | 0 open issues (all 48 closed) |

---

## ~~🔴 Open Critical & High Issues (from Audit)~~ ✅ ALL RESOLVED

All Critical and High issues from the 2026-05-15 audit have been fixed:

| # | Issue | Fix Commit | GitHub |
|---|-------|-----------|--------|
| 1 | Volume slider `Mathf.Log10(0)` → `-Infinity` | 235d20b — clamp to -80dB | #26 ✅ |
| 2 | Sun intensity `*= multiplier` decays to zero | 235d20b — store base, multiply base | #27 ✅ |
| 3 | `NIDELVA_BBOX_UTM33` targets Trondheim, not Agder | 7011e2e — BBOX updated to Agder | #28 ✅ |
| 4 | CQL injection in NVE WFS query | 7011e2e — regex validation on river_name | #28 ✅ |
| 5 | `release.yml` shell injection via `${{ secrets.* }}` | 4946b48 — env: indirection | #29 ✅ |
| 6 | No `.github/dependabot.yml` | 4946b48 — added dependabot.yml | #30 ✅ |
| 7 | No concurrency groups / timeouts | 4946b48 — groups + timeout-minutes | #30 ✅ |
| 8 | River waves frozen at generation | df02f38 — removed, shader handles waves | #31 ✅ |
| 9 | `VegetationGenerator` dead batch arrays | df02f38 — removed PreAllocateBatches | #31 ✅ |
| 10 | `AudioManager.GetComponent` every frame | 0ffe037 — cached reference | #32 ✅ |
| 11 | Achievement spam every frame | 0ffe037 — guard flags | #32 ✅ |
| 12 | Recovery missing `angularVelocity` reset | 0ffe037 — zero on recovery | #32 ✅ |

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
| PF3 | ~~`PhotoMode.ApplyFilters()` iterates every pixel on CPU~~ | ✅ Fixed — GPU shader via Graphics.Blit (c2fadd4) |
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
| `norgeibilder.py` | `wgs84_to_tile`, `tile_to_wgs84`, `get_tile_bounds`, `download_tile`, `download_orthophoto`, `export_terrain_texture` | — (all core functions tested) |
| `qgis_export.py` | `export_dem_geotiff`, `export_river_geojson`, `generate_qgis_project`, `export_for_qgis` | `export_flow_accumulation_geotiff` (partial) |
| `headless_renderer.py` | ❌ | All (rendering, hard to unit test) |
| `renderer.py` | ❌ | All (OpenGL, hard to unit test) |
| `camera.py` | ❌ | All (OpenGL, hard to unit test) |
| `main.py` | `main()` with --sample, --qgis, --skip-* flags | `--interactive` (requires display), `--kartverket` (network), `--orthophoto` (network) |
| `nve_hydapi.py` | `get_seasonal_flow`, `build_river_physics_params`, `export_flow_json`, `fetch_flow_statistics` | `fetch_observations`, `fetch_current_flow` (network) |
| `nibio_ar5.py` | `classify_features`, `get_vegetation_params`, `generate_vegetation_map`, `build_unity_vegetation_data`, `export_vegetation_json` | `fetch_land_cover` (network) |

**Core module coverage: terrain_mesh 69%, river_flow 46%, dem_downloader 30%+.** 82 tests passing. Integration test included.

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
- [x] Upgrade DEM to Kartverket DTM 1m LiDAR (where available) ✔️ (b890809, --kartverket flag)
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

### Phase 5: Game Experience (v1.0.0) ✅ COMPLETE

- [x] Complete tutorial flow with real terrain ✔️ (default tutorial steps)
- [x] Balance boat physics + stamina ✔️ (721c0ea — stroke cooldown, speed caps, vessel tuning)
- [x] Sound design pass ✔️ (721c0ea — wind layer, distance attenuation, splash SFX)
- [x] Multiple save slots with preview screenshots ✔️
- [x] Steam achievements for river milestones ✔️
- [x] Settings menu with URP quality presets ✔️
- [x] Localization (Norwegian / English) ✔️
- [x] Performance profiling + optimization pass ✔️

### Phase 6: Stabilization ✅ COMPLETE

- [x] Fix SettingsMenu Log10(0) crash ✔️ (235d20b) — Fixes #26
- [x] Fix WeatherSystem sun intensity decay ✔️ (235d20b) — Fixes #27
- [x] Fix nve_river.py wrong coordinates + CQL injection ✔️ (7011e2e) — Fixes #28
- [x] Fix release.yml shell injection ✔️ (4946b48) — Fixes #29
- [x] Add dependabot.yml + concurrency groups + timeouts ✔️ (4946b48) — Fixes #30
- [x] Remove frozen wave displacement + dead batch arrays ✔️ (df02f38) — Fixes #31
- [x] Fix achievement spam + angularVelocity + cached GetComponent ✔️ (0ffe037) — Fixes #32

### Phase 7: Norge i bilder Orthophoto ✅ COMPLETE

- [x] Implement WMTS client for Norge i bilder (opencache.statkart.no) ✔️ (cfdd637)
- [x] Download and stitch aerial orthophoto tiles for Nidelven area ✔️ (cfdd637)
- [x] Export terrain texture (1024x1024 PNG) for Unity TerrainLayer ✔️ (cfdd637)
- [x] Add `--orthophoto` CLI flag to Python pipeline ✔️ (cfdd637)
- [x] Unity TerrainGenerator loads orthophoto as terrain texture ✔️ (cfdd637)
- [x] Fallback to procedural splatmap if imagery unavailable ✔️ (cfdd637)
- [x] Add 7 tests for WMTS client (coordinate conversion, bounds, safety) ✔️ (cfdd637)
- [x] Close issue #25 ✔️

### Phase 8: Tech Debt & Quality ✅ COMPLETE

- [x] Move Sprint/Brake to FixedUpdate (frame-rate-independent physics) ✔️ (006cdcd)
- [x] Resolve Space key conflict (RiverCamera vs BoatController) ✔️ (006cdcd)
- [x] Centralize Time.timeScale via RequestPause/ReleasePause API ✔️ (42141f0)
- [x] Fix SaveManager auto-save slot collision ✔️ (3272722)
- [x] Fix terrain_mesh.py __main__ wrong data path ✔️ (e6f1e57)
- [x] Deduplicate dev deps in pyproject.toml ✔️ (e6f1e57)
- [x] Add pytest-cov to dev dependencies ✔️ (e6f1e57)
- [x] Fix CI pipeline `|| echo` swallowing errors ✔️ (d2d472c)
- [x] Fix `--interactive` renderer sys.argv conflict ✔️ (56fa2a4)
- [x] Add QGIS export module + `--qgis` CLI flag ✔️ (08fc616)
- [x] Create issues for remaining work (#43, #44, #45) ✔️

### Phase 9: Close Open Issues ✅ COMPLETE

- [x] Optimize compute_flow_accumulation with pre-computed receiver array ✔️ (7c7ce9b) — Fixes #43
- [x] Add CodeQL C# scanning for Unity scripts (build-mode: none) ✔️ (787997d) — Fixes #44
- [x] Add 5 CLI integration tests for main.py entry point ✔️ (52e16d7) — Fixes #45
- [x] Fix `--interactive` renderer argv import ordering ✔️ (14c84db)

### Phase 10: CI Cleanup ✅ COMPLETE

- [x] Extract ShaderGraph workaround into `.github/scripts/prepare-ci.sh` ✔️ (2a5c2bc)
- [x] Upgrade `softprops/action-gh-release` v1 → v3 ✔️ (2a5c2bc + #37)
- [x] Merge 9 dependabot PRs (actions/checkout@v6, cache@v5, upload-artifact@v7, codeql-action@v4, black>=26, matplotlib>=3.10, moderngl>=5.12, rasterio>=1.4) ✔️
- [x] Migrate UI scripts from UnityEngine.UI to TMPro ✔️ (fc2c199)

### Phase 11: NVE HydAPI + NIBIO AR5 Data Integration ✅ COMPLETE

- [x] Implement `nve_hydapi.py` — NVE HydAPI river flow client ✔️ (1e215a8)
  - Real-time water discharge/level from station 2.145.0 (Rygenefoss)
  - Seasonal climate normals as offline fallback (NIDELVA_FLOW_NORMALS)
  - Converts to Unity physics params (flow_speed, turbulence, current_strength, water_clarity)
- [x] Implement `nibio_ar5.py` — NIBIO AR5 land cover client ✔️ (1e215a8)
  - Fetch land cover classification from NIBIO WFS
  - Classifies forest/agriculture/water/wetland with forest subtypes (spruce/pine/birch)
  - Rasterizes to vegetation map for Unity VegetationGenerator
- [x] Add `--hydapi` and `--vegetation` CLI flags to main.py ✔️ (1e215a8)
- [x] Add 16 new tests (7 HydAPI + 9 AR5), total: 82 passing ✔️ (1e215a8)
- [x] Create issues for future data integration: #46 (Artsdatabanken), #47 (FKB-Bygning), #48 (NVDB bridges)

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

### Active (remaining)

No active tech debt items. All resolved.

### Resolved (Phase 10 - CI cleanup)

| Item | Resolution | Commit |
|------|-----------|--------|
| `softprops/action-gh-release@v1` outdated | Upgraded to v3 (via v2 + dependabot) | 2a5c2bc + #37 |
| Duplicated CI workaround code (3x) | Extracted to `.github/scripts/prepare-ci.sh` | 2a5c2bc |
| Legacy UI (UnityEngine.UI) → TMPro | Migrated Text/Dropdown to TMP_Text/TMP_Dropdown | fc2c199 |

### Resolved (Phase 9 - 2026-05-14)

| Item | Resolution | Commit |
|------|-----------|--------|
| `compute_flow_accumulation` O(n) Python loop | Pre-computed receiver array, flat indexing | 7c7ce9b |
| Add CodeQL for C# | build-mode: none for Unity scripts | 787997d |
| Add CLI tests (main.py) | 5 integration tests (TestCLI class) | 52e16d7 |
| `--interactive` argv import order | Clear sys.argv before renderer import | 14c84db |

### Resolved (Phase 8 tech debt - 2026-05-14)

| Item | Resolution | Commit |
|------|-----------|--------|
| Time.timeScale competition (multiple systems) | RequestPause/ReleasePause API | 42141f0 |
| SaveManager auto-save overwrites last user slot | Dedicated slot beyond user range | 3272722 |
| Space key conflict (RiverCamera vs BoatController) | Gate behind followTarget == null | 006cdcd |
| Sprint in Update() not FixedUpdate() | Input flags + FixedUpdate forces | 006cdcd |
| Duplicate dev deps in pyproject.toml | Removed [project.optional-dependencies] dev | e6f1e57 |
| `terrain_mesh.py` `__main__` wrong data path | Resolve relative to mvp/ root | e6f1e57 |
| CI pipeline failure hidden by `|| echo` | Only ignore timeout (exit 124) | d2d472c |

### Resolved (Phase 6 stabilization - 2026-05-15)

| Item | Resolution | Commit |
|------|-----------|--------|
| SettingsMenu Log10(0) crash | Clamp to -80dB minimum | 235d20b |
| WeatherSystem intensity decay | Store base intensity, multiply base | 235d20b |
| nve_river.py wrong coordinates | BBOX updated to Agder | 7011e2e |
| CQL injection in NVE query | Regex validation on river_name | 7011e2e |
| release.yml shell injection | env: indirection for secrets | 4946b48 |
| No dependabot.yml | Added for github-actions + pip | 4946b48 |
| No concurrency groups / timeouts | Added to ci.yml + release.yml | 4946b48 |
| River waves frozen at generation | Removed, shader handles waves | df02f38 |
| VegetationGenerator dead batch arrays | Removed PreAllocateBatches | df02f38 |
| AudioManager GetComponent in update | Cached reference | 0ffe037 |
| Achievement spam every frame | Guard flags (tenKm, speedDemon) | 0ffe037 |
| Recovery missing angularVelocity reset | Zero on recovery | 0ffe037 |
| GameManager missing DontDestroyOnLoad | Added DontDestroyOnLoad | 2b045d1 |
| GameManager weak random seed (1000 values) | Use Environment.TickCount | 2b045d1 |
| DayNightCycle double-calculates sun intensity | Use cachedSunIntensity in UpdateFog | 2b045d1 |
| SteamManager debug UI renders in release | Gate behind #if UNITY_EDITOR | 2b045d1 |
| RiverController GetClosestProgress div/0 | Guard riverPath.Count <= 1 | 2b045d1 |
| SaveManager GetSlotScreenshot leaks Texture2D | Cache in screenshotCache[] | 2b045d1 |
| camera.py unconditional import of optional deps | Lazy-import glm | 2b045d1 |
| Global np.random.seed(42) pollution | Use local default_rng instance | 2b045d1 |
| CodeQL only scans Python (not C#) | Added C# scanning (build-mode: none) | 787997d |
| Duplicated CI workaround code (3x) | Extracted to `.github/scripts/prepare-ci.sh` | 2a5c2bc |
| Legacy UI (UnityEngine.UI) vs TMPro | Migrated to TMPro | fc2c199 |
| `softprops/action-gh-release@v1` outdated (v2 exists) | Upgraded to v2 | 2a5c2bc |
| No CLI test coverage (main.py) | 5 integration tests (TestCLI class) | 52e16d7 |
| `export_river_path_json()` untested | Tested via TestCLI integration | 52e16d7 |
| `pytest-cov` not declared as dependency | Added to dev dependency group | e6f1e57 |

### Resolved

| Item | Severity | Resolution |
|------|----------|------------|
| ~~Dead code: `kartverket_dem.py`~~ | Low | ✅ Removed |
| ~~Dead code: `scripts/` directory~~ | Low | ✅ Removed |
| ~~Duplicate dev deps in pyproject.toml~~ | Low | ✅ Fixed |
| ~~`--size` and `--download` CLI args unused~~ | Low | ✅ Removed |
| ~~`camera.py` coordinate mismatch~~ | Medium | ✅ Fixed |
| ~~Python for-loop mesh generation~~ | Medium | ✅ Vectorized |
| ~~Frame-rate-dependent camera smoothing~~ | Low | ✅ SmoothDamp (c2fadd4) |
| ~~Deprecated Rigidbody APIs (velocity/angularDrag)~~ | Low | ✅ Fixed (4998aa8) |
| ~~Missing .meta files (RiverParticles, WeatherSystem, PhotoFilter)~~ | Medium | ✅ Fixed (eee176c) |
| ~~Orphaned KartverketDemImporter.cs.meta~~ | Medium | ✅ Removed (eee176c) |

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

## Next Steps — Remaining Tech Debt

### Priority 1: Quick fixes (< 15 min each) ✅ ALL DONE
- [x] Sprint in `Update()` not `FixedUpdate()` (physics jitter at low FPS) ✔️ (006cdcd)
- [x] Space key conflict (RiverCamera vs BoatController) ✔️ (006cdcd)
- [x] `terrain_mesh.py` `__main__` wrong data path ✔️ (e6f1e57)
- [x] Duplicate dev deps in pyproject.toml ✔️ (e6f1e57)
- [x] CI pipeline failure hidden by `|| echo` ✔️ (d2d472c)

### Priority 2: Medium effort (30 min — 2 hr)
- [x] Time.timeScale competition (multiple systems) ✔️ (42141f0)
- [x] SaveManager auto-save overwrites last user slot ✔️ (3272722)
- [x] `compute_flow_accumulation` O(n) Python loop → vectorize ✔️ (7c7ce9b) — Fixes #43
- [x] Add `pytest-cov` to dev deps ✔️ (e6f1e57)
- [x] Add CLI tests (main.py entry point) ✔️ (52e16d7) — Fixes #45

### Priority 3: Low priority (post v1.0.0)
- [x] CodeQL for C# (extend existing workflow) ✔️ (787997d) — Fixes #44
- [x] Legacy UI (UnityEngine.UI) → TMPro migration ✔️ (fc2c199)
- [x] `softprops/action-gh-release@v1` → v2 ✔️ (2a5c2bc)
- [x] Extract CI workaround into shared script ✔️ (2a5c2bc)

### Future features
- Weather effects (rain, fog particles)
- Multiplayer co-op
- VR support
- Additional rivers (Otra, Tovdalselva)

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

1. ~~**NVE ELVIS + HydAPI** — Replace gradient-descent river path with real river geometry + flow data~~ ✅ (1e215a8)
2. **Kartverket DTM 10** — Upgrade terrain from 30m to 10m resolution
3. ~~**NIBIO AR5** — Drive vegetation placement from real land-use data~~ ✅ (1e215a8)
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
