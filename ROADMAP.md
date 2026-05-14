# Nidelven River Adventure — Roadmap & Project Audit

Last updated: 2026-05-14 (post-fix)

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

---

## Executive Summary

The project has a **complete Unity codebase** (16 fully implemented scripts, URP shader, scene) and a **working Python terrain pipeline** (DEM download, mesh generation, river tracing, preview rendering). CI/CD is operational with automated Windows + Linux builds.

However, the two halves are **not connected** — the Python pipeline output is not automatically imported into Unity. The game will compile and build, but the player will only experience a synthetic terrain until the real DEM data integration is completed.

> ✅ **Phase 0 complete** — security issues fixed, Python lint clean, critical bugs resolved (see Resolved Issues below).

---

## Current Status

| Component | State | Confidence |
|-----------|-------|-----------|
| Python MVP pipeline | ✅ Functional | DEM download, mesh gen, river flow, lint clean |
| Unity scripts (16) | ✅ Compile & build | All logic implemented, 2 minor bugs remain |
| CI — Python | ✅ Passing | Lint (strict), format, tests, pipeline run |
| CI — Unity Test | ✅ Passing | Compiles in game-ci Docker (6000.4.6f1) |
| CI — Unity Build | ✅ Producing artifacts | Win64 + Linux64, 7-day retention |
| CodeQL | ✅ Passing | Python security scanning |
| Integration (Python→Unity) | ❌ Not connected | Manual file copy required |
| Playable experience | ⚠️ Partial | Synthetic terrain only; no real DEM in Unity |

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
| P4 | **Interactive renderer never loads data** — class attrs set but not read by `__init__` | Empty scene in 3D viewer |
| P5 | **River start logic inverted** — finds lowest (exit) point, not highest (source) | River traces wrong direction on real DEM |
| P6 | ~~Missing `import math`~~ | ✅ Fixed |

### Unity

| # | Bug | File | Impact |
|---|-----|------|--------|
| U1 | ~~RiverController `riverWidths` IndexOutOfRange~~ | ✅ Fixed — added initial width/speed for point 0 |
| U2 | ~~Shader property `_FlowOffset` not declared~~ | ✅ Fixed — added to shader Properties + CBUFFER |
| U3 | **SaveManager.lastPosition not initialized** — bogus distance on first frame | Stats show 1000s of meters immediately |
| U4 | **WildlifeSpawner compares progress (0–1) to distance (20f)** | Animals spawn anywhere regardless of river proximity |

---

## 🟡 Warnings — Should Fix

### Architecture

| # | Issue | Impact |
|---|-------|--------|
| A1 | Two unconnected terrain importers (`TerrainGenerator` + `KartverketDemImporter`) | Confusing; unclear which to use |
| A2 | `TerrainGenerator.LoadGeoTiff()` doesn't parse TIFF headers — reads raw bytes | Will produce garbage with real GeoTIFF files |
| A3 | Legacy Input API everywhere but New Input System package installed | Silent input failure if project settings misconfigured |
| A4 | Escape key handled by both `GameManager` and `SettingsMenu` | Race condition / double-toggle |
| A5 | Python `kartverket_dem.py` is dead code (WCS returns all-zero data) | Clutters codebase |
| A6 | `scripts/` directory appears orphaned (pre-MVP approach) | Should be removed or integrated |

### Performance

| # | Issue | Impact |
|---|-------|--------|
| PF1 | `terrain_mesh.py` vertex generation uses Python for-loops (262k iterations) | Extremely slow mesh generation |
| PF2 | `VegetationGenerator.RenderInstanced()` allocates arrays every frame | GC pressure, frame drops |
| PF3 | `PhotoMode.ApplyFilters()` iterates every pixel on CPU | Multi-second freeze on capture at 2x resolution |
| PF4 | `AudioManager` moves its own transform to player position | Breaks 3D audio spatialization for non-river sources |

### CI/CD

| # | Issue | Impact |
|---|-------|--------|
| C1 | Unity version mismatch: project is 6000.4.6f1, CI uses 6000.4.5f1 | Potential shader/serialization differences |
| C2 | Lint/format steps use `\|\| true` — never fail | No code quality gate |
| C3 | No uv/pip caching in Python job | ~30s wasted per run |
| C4 | No artifact retention configured (90-day default) | Storage cost for 500MB+ builds |
| C5 | Release workflow deadlocks when Unity secrets are missing | Release never triggers without secrets |

---

## 📊 Test Coverage

| Module | Covered | Not Covered |
|--------|---------|-------------|
| `minimal.py` | `create_sample_dem_ascii` | `trace_river_path`, `render_ascii`, `render_html` |
| `terrain_mesh.py` | `generate_mesh`, `calculate_normals` | `load_dem`, `save_mesh_obj`, `create_terrain_from_dem` |
| `river_flow.py` | `find_start_point`, `trace_river_path` | `smooth_path`, `calculate_flow_properties`, `generate_river_mesh` |
| `dem_downloader.py` | `create_sample_dem` | `download_dem_copernicus`, `get_dem_path` |
| `headless_renderer.py` | ❌ | All |
| `renderer.py` | ❌ | All |
| `camera.py` | ❌ | All |
| `main.py` | ❌ | All |

**Estimated coverage: ~20-25%.** No integration tests. No edge-case tests.

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
- [ ] Fix `TerrainGenerator.LoadGeoTiff()` to parse real TIFF (or use RAW format)
- [ ] Build pipeline: Python DEM → Unity StreamingAssets (automated copy or build step)
- [ ] Wire up boat + camera with real terrain in scene
- [ ] Fix remaining Unity bugs (U3, U4)
- [ ] Fix Input System configuration (set to "Both")
- [ ] First playable build with real terrain

### Phase 2: Data Quality (v0.2.0)

- [x] Download real DEM (Copernicus GLO-30, 30m)
- [x] Fix NaN handling in terrain_mesh.py
- [ ] Fix river tracer for real DEM (use flow accumulation / D8 algorithm)
- [ ] Implement proper river path from OSM or NVE data
- [ ] Texture terrain from Sentinel-2 satellite imagery or Norway aerial photos
- [ ] Add DEM integrity verification (checksum)
- [ ] Vectorize terrain mesh generation (eliminate Python for-loops)

### Phase 3: Polish (v0.3.0)

- [x] Fix water shader flow animation (_FlowOffset)
- [ ] Add `DepthOnly` pass to water shader
- [ ] Fix vegetation GPU instancing (pre-allocate batches)
- [ ] Fix AudioManager 3D spatialization (child objects for sources)
- [ ] Remove debug OnGUI overlays (or gate behind `#if UNITY_EDITOR`)
- [ ] Add proper water depth/transparency
- [ ] Particle effects (splash, foam, mist)
- [ ] LOD system for terrain + vegetation

### Phase 4: CI/CD Hardening

- [x] Remove `|| true` from lint/format CI steps
- [x] Add uv caching to Python job
- [x] Configure artifact retention (7 days CI)
- [ ] Fix release workflow deadlock (needs: with proper `if:`)
- [ ] Pin Unity version in release.yml
- [ ] Add integration test (full pipeline end-to-end)
- [ ] Increase test coverage to >60%

### Phase 5: Game Experience (v1.0.0)

- [ ] Complete tutorial flow with real terrain
- [ ] Balance boat physics + stamina
- [ ] Sound design pass (real recordings or quality samples)
- [ ] Multiple save slots with preview screenshots
- [ ] Steam achievements for river milestones
- [ ] Settings menu with URP quality presets
- [ ] Localization (Norwegian / English)
- [ ] Performance profiling + optimization pass

---

## Technical Debt Register

| Item | Severity | Effort | Notes |
|------|----------|--------|-------|
| Dead code: `kartverket_dem.py` | Low | 5 min | WCS confirmed non-functional; remove |
| Dead code: `scripts/` directory | Low | 5 min | Superseded by `mvp/` |
| ~~Duplicate dev deps in pyproject.toml~~ | ~~Low~~ | — | ✅ Fixed (ruff+black added to dependency-groups) |
| `--size` and `--download` CLI args unused | Low | 10 min | Remove or implement |
| `camera.py` coordinate mismatch | Medium | 30 min | Row/col → X/Z mapping inconsistent with terrain_mesh |
| Python for-loop mesh generation | Medium | 1-2 hr | Rewrite with numpy vectorization |
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
└────────────────────────┬────────────────────────────┘
                         │ ← NOT YET CONNECTED
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

The critical integration gap is getting the Python pipeline's real DEM output into Unity's `TerrainGenerator`. Options:
1. Export RAW 16-bit heightmap from Python → Unity `StreamingAssets/` → `TerrainData.SetHeights()`
2. Use Unity's `Terrain` API to import GeoTIFF directly (requires GDAL or custom parser)
3. Export OBJ mesh from Python → Unity mesh import (loses Terrain features like splatmaps)
- [ ] Performance optimization

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

## License & Data

- Code: MIT License
- Terrain: © Kartverket
- Imagery: © ESA (Sentinel-2)
- River data: OpenStreetMap contributors
