# Copilot Instructions — Nidelven River Adventure

## Project Overview

A relaxing kayak/canoe exploration game on the **Nidelven river in Agder, Norway**. Uses real 30m DEM data (Copernicus GLO-30) with a Python terrain pipeline feeding into Unity 6000 LTS. Pre-alpha status.

**Repository:** `https://github.com/egkristi/Nidelven-river-adventure`
**Owner:** egkristi (Erling Kristiansen)

---

## Architecture

### Two-Layer System

```
Python Pipeline (mvp/)          →  Unity Game (Assets/)
─────────────────────────────      ────────────────────────────
DEM download (Copernicus S3)       TerrainGenerator.cs (loads RAW)
Terrain mesh generation            RiverController.cs (flow sim)
River flow tracing                 BoatController.cs (physics)
NVE ELVIS river import             Camera, Audio, UI, Wildlife
Export: terrain.raw + metadata     Shaders (URP), Vegetation
```

**Data flow:** Python exports `terrain.raw` + `terrain_metadata.json` → copied to `Assets/StreamingAssets/` → Unity `TerrainGenerator` auto-loads at runtime.

### Directory Structure

```
.github/workflows/     CI/CD (ci.yml, codeql.yml, release.yml)
Assets/Scripts/
  Core/                GameManager, AudioManager, SaveManager, PhotoMode, SteamManager, GameQuitter
  Environment/         TerrainGenerator, RiverController, DayNightCycle, VegetationGenerator, WildlifeSpawner
  Player/              BoatController, RiverCamera
  UI/                  SettingsMenu, TutorialSystem
Assets/Shaders/        SimpleWater.shader (URP)
mvp/
  src/mvp/             Python pipeline source
  tests/               pytest test suite
  pyproject.toml       UV/hatchling config
design/                Game Design Document
docs/                  Data pipeline docs, Jira issues
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Engine | Unity | 6000.4.6f1 LTS (local), 6000.4.5f1 (CI) |
| Render | Universal Render Pipeline (URP) | 17.0.3 |
| Language (Unity) | C# | .NET Standard 2.1 |
| Language (Pipeline) | Python | 3.11 |
| Package Manager | UV + hatchling | Latest |
| CI | GitHub Actions (game-ci/unity-builder v4) | — |
| DEM Source | Copernicus GLO-30 (AWS S3, no auth) | 30m |
| River Data | NVE ELVIS WFS | NLOD license |

---

## Development Rules

### Git Workflow
- **Branch:** `main` only (no develop branch yet)
- **Commit style:** Conventional Commits (`feat:`, `fix:`, `perf:`, `docs:`, `ci:`, `test:`, `chore:`, `refactor:`)
- **Push after every logical change** — CI validates on each push
- **zsh escape:** Never use `!` in commit messages (zsh history expansion). Use single quotes around messages containing `!`

### Python (mvp/)
- **Formatter:** Black (line-length 100)
- **Linter:** Ruff (rules: E, F, I, W, UP, B, C4, SIM; ignores: E501, N806, N802, N803)
- **Tests:** pytest (currently 23 tests in `tests/test_pipeline.py`)
- **Package manager:** UV (`uv sync`, `uv run`)
- **Source layout:** `mvp/src/mvp/` (hatchling src layout)
- **Run tests:** `cd mvp && uv run pytest tests/ -v`
- **Run lint:** `cd mvp && uv run ruff check src/ && uv run black --check src/`
- **Known quirk:** `trace_river_path()` has `boundary_margin=2` — tests must start river tracing at row ≥ 3 to avoid immediate exit

### Unity (C#)
- **Namespaces:** `Nidelven.Core`, `Nidelven.Environment`, `Nidelven.Player`, `Nidelven.UI`
- **Singleton pattern:** GameManager, AudioManager, SaveManager use `Instance` static property
- **csc.rsp:** Contains `-define:DISABLESTEAMWORKS` (Steamworks.NET not installed)
- **CI workaround:** CI strips URP from manifest.json and adds `-define:DISABLE_URP` to avoid ShaderGraph GUID errors in Docker
- **Build targets:** Windows x64, Linux x64 (CI); macOS (local dev)
- **Local build test:** `/Applications/Unity/Hub/Editor/6000.4.6f1/Unity.app/Contents/MacOS/Unity -batchmode -nographics -projectPath "$(pwd)" -buildTarget StandaloneOSX -buildOSXUniversalPlayer ./build/NidelvenRiverAdventure.app -logFile ./unity-build.log`

### CI/CD
- **Python MVP job:** Ruff lint → Black format → pytest → pipeline smoke test
- **Unity Test job:** game-ci/unity-test-runner (EditMode + PlayMode)
- **Unity Build job:** game-ci/unity-builder (Win64 + Linux64, `main` only)
- **CodeQL:** Python security analysis (weekly + on push)
- **Release:** Tag `v*` → builds + GitHub Release with zipped artifacts
- **Unity secrets required:** `UNITY_LICENSE`, `UNITY_EMAIL`, `UNITY_PASSWORD` (all jobs gracefully skip if missing)

---

## Key Technical Details

### Python Pipeline Modules

| Module | Purpose | Coverage |
|--------|---------|----------|
| `terrain_mesh.py` | DEM → mesh/normals (numpy vectorized) | 69% |
| `river_flow.py` | Gradient descent river tracing + flow | 46% |
| `nve_river.py` | NVE ELVIS WFS river geometry import | partial |
| `dem_downloader.py` | Copernicus GLO-30 tile download | 30% |
| `camera.py` | Interactive 3D viewer (OpenGL/glm) | 0% |
| `headless_renderer.py` | Matplotlib preview images | 0% |
| `renderer.py` | ModernGL interactive renderer | 0% |
| `main.py` | CLI orchestration | 0% |
| `minimal.py` | ASCII DEM + simple tracer | 19% |

### Unity Script Responsibilities

| Script | Role |
|--------|------|
| `GameManager` | Singleton, world generation orchestration, pause, input |
| `TerrainGenerator` | Loads RAW/GeoTIFF DEM or generates synthetic terrain |
| `RiverController` | River mesh generation, flow animation, trajectory API |
| `BoatController` | Rigidbody physics, buoyancy, paddle, capsize, vessel types |
| `RiverCamera` | Follow river trajectory or orbit |
| `AudioManager` | Layered soundscape, spatial audio, bird intervals |
| `DayNightCycle` | Sun rotation, sky/fog gradients, time compression |
| `VegetationGenerator` | GPU-instanced trees/rocks by elevation/slope |
| `WildlifeSpawner` | Birds, fish, deer with despawn distance |
| `PhotoMode` | Freeze time, free camera, screenshot capture |
| `SaveManager` | JSON save/load, auto-save, progress tracking |
| `SettingsMenu` | Resolution, quality, audio sliders |
| `TutorialSystem` | Step-based tutorial with key/time waits |
| `SteamManager` | Steam integration (guarded by `#if !DISABLESTEAMWORKS`) |

### Water Shader (SimpleWater.shader)
- URP `UniversalForward` pass only (no DepthOnly — known gap)
- Properties: `_BaseColor`, `_FoamColor`, `_WaveHeight`, `_WaveSpeed`, `_FlowOffset`, `_Smoothness`
- Transparent blend, ZWrite Off
- Missing: depth-based effects (needs DepthOnly pass)

---

## Known Issues & Tech Debt

### Open GitHub Issues
- **#20** Phase 2: Data Quality — real river path + 1m DEM
- **#21** Phase 3: Water shader DepthOnly + vegetation instancing (PF2)
- **#22** Phase 3: Audio spatialization (PF4) + LOD system

### Performance Issues (Still Open)
- **PF2:** `VegetationGenerator.RenderInstanced()` allocates arrays every frame → GC pressure
- **PF3:** `PhotoMode.ApplyFilters()` iterates every pixel on CPU
- **PF4:** `AudioManager` moves its own transform to player (breaks 3D spatialization)

### CI Gaps
- **C1:** Unity version mismatch: local 6000.4.6f1 vs CI 6000.4.5f1
- Release workflow needs the same URP-removal workaround as CI (currently missing)

---

## Norwegian Geodata Sources (Free)

| Source | Data | API |
|--------|------|-----|
| Kartverket DTM 1m | LiDAR elevation | WCS `wcs.geonorge.no` |
| Norge i bilder | Aerial photos 10-25cm | WMTS `opencache.statkart.no` |
| NVE ELVIS | River centerlines | WFS `gis3.nve.no/map/services/Elvenett/MapServer/WFSServer` |
| NIBIO AR5 | Land cover | WFS `wfs.nibio.no` |
| Sentinel-2 | 10m satellite | AWS S3 `sentinel-cogs` |

All are CC BY 4.0 or NLOD licensed.

---

## Workflow Conventions

1. **Before making changes:** Run tests locally (`cd mvp && uv run pytest tests/ -v`)
2. **After changes:** Run lint + tests, then commit + push
3. **Issue tracking:** Create GitHub issues for new bugs/features; reference in commits
4. **Docs:** Update ROADMAP.md and README.md as work progresses
5. **Coverage:** Run `uv run pytest tests/ --cov=mvp --cov-report=term-missing` to check (pytest-cov installed in venv)

---

## File Conventions

- Unity `.meta` files MUST be committed (asset references)
- `*.tif`, `*.dem`, `*.hgt` are gitignored (large DEM files)
- `Library/`, `Temp/`, `Logs/`, `UserSettings/` are gitignored
- `mvp/output/` and `mvp/data/` are gitignored (generated)
- `.vscode/` is tracked (shared editor settings)

---

## Quick Commands

```bash
# Python
cd mvp && uv run pytest tests/ -v                    # Run tests
cd mvp && uv run ruff check src/                     # Lint
cd mvp && uv run black src/                          # Format
cd mvp && uv run mvp --sample --skip-render          # Pipeline smoke test

# Unity (local)
# Tests:
/Applications/Unity/Hub/Editor/6000.4.6f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -nographics -projectPath "$(pwd)" \
  -runTests -testPlatform EditMode \
  -testResults ./test-results-editmode.xml -logFile ./unity-test-editmode.log

# Build (macOS):
/Applications/Unity/Hub/Editor/6000.4.6f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -nographics -projectPath "$(pwd)" \
  -buildTarget StandaloneOSX \
  -buildOSXUniversalPlayer ./build/NidelvenRiverAdventure.app \
  -logFile ./unity-build.log

# Git
git add -A && git commit -m 'type: description' && git push

# GitHub CLI
GH_PAGER=cat gh run list --limit 5
GH_PAGER=cat gh issue list --state open
```
