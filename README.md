# Nidelven River Adventure 🛶

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)
[![CodeQL](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/codeql.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/codeql.yml)

A relaxing river exploration game set on the **Nidelven river in Agder, Norway**. Paddle through a valley generated from real 30m satellite elevation data. Built with Unity 6000 LTS and a Python terrain pipeline.

> **Status:** Pre-alpha. Unity builds compile and run but use procedural terrain. Real DEM integration in progress — see [ROADMAP.md](ROADMAP.md) for the full audit and plan.

---

## Running on PC

### Download a Build (easiest)

1. Go to [Actions → CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml)
2. Click the latest successful run on `main`
3. Download **Build-StandaloneWindows64** (or **Build-StandaloneLinux64**)
4. Extract the zip and run `NidelvenRiverAdventure.exe`

> Builds are produced automatically on every push to `main` (Windows + Linux + macOS).

### From Source (Unity Editor)

```bash
git clone https://github.com/egkristi/Nidelven-river-adventure.git
```

1. Install [Unity Hub](https://unity.com/download) and Unity **6000.4.6f1** (LTS)
2. Open the cloned folder via Unity Hub → "Add project from disk"
3. Open `Assets/Scenes/MainScene.unity`
4. Press **Play** ▶️

### Python Terrain Pipeline

```bash
cd mvp
uv sync                          # install dependencies
uv run mvp                       # download real DEM + generate terrain + previews
uv run mvp --sample              # use synthetic terrain (no download)
uv run mvp --interactive         # 3D terrain viewer (requires OpenGL)
uv run pytest tests/ -v          # run test suite
```

The pipeline downloads Copernicus GLO-30 DEM tiles from AWS S3 on first run (~22 MB per tile, no auth required).

---

## Features

| Category | Details | Status |
|----------|---------|--------|
| **Terrain** | 30m DEM from Copernicus GLO-30 (Nidelven valley) | ✅ Python / ⚠️ Unity uses synthetic |
| **River** | Flow simulation via gradient descent + NVE ELVIS real geometry | ✅ Works on synthetic |
| **Boat Physics** | Buoyancy, paddling, capsize & recovery, stamina | ✅ Implemented |
| **Vegetation** | GPU-instanced trees and rocks by elevation/slope | ✅ Implemented |
| **Day/Night** | Dynamic sun cycle, ambient gradients, fog | ✅ Implemented |
| **Water Shader** | URP shader with waves, foam, fresnel, specular | ✅ Shader + flow animation |
| **Audio** | River ambience, birdsong, forest, paddle SFX | ✅ Implemented |
| **Wildlife** | Birds, deer with steering AI | ✅ Implemented |
| **Photo Mode** | Freeze time, brightness/contrast/saturation, capture | ✅ Implemented |
| **Save/Load** | JSON persistence with auto-save + distance tracking | ✅ Implemented |
| **Settings** | Resolution, quality, fullscreen, render scale, audio | ✅ Implemented |
| **Tutorial** | Step-based with key-wait and time-wait | ✅ Implemented |
| **Steam** | Achievements, stats, cloud saves (opt-in) | ✅ Guarded with `#if` |
| **CI/CD** | Python lint/test, Unity test/build, CodeQL | ✅ All green |

---

## Project Structure

```
Assets/
  Scenes/              MainScene.unity (camera + directional light)
  Scripts/
    Core/              GameManager, AudioManager, SaveManager, PhotoMode, SteamManager
    Environment/       DayNightCycle, TerrainGenerator, RiverController, Vegetation, Wildlife
    Player/            BoatController, RiverCamera
    UI/                SettingsMenu, TutorialSystem
  Shaders/             SimpleWater.shader (URP)
mvp/
  src/mvp/             Python pipeline
    dem_downloader.py  Copernicus GLO-30 tile download + merge
    terrain_mesh.py    DEM → OBJ mesh with normals (numpy vectorized)
    river_flow.py      Gradient descent river tracer + flow properties
    nve_river.py       NVE ELVIS WFS river geometry import
    renderer.py        Interactive ModernGL 3D viewer (optional)
    headless_renderer.py  Matplotlib preview images
  tests/               27 pytest tests (core modules: 46-69% coverage)
Packages/              Unity package manifest (URP, Input System, Cinemachine, TMPro)
.github/workflows/     ci.yml, codeql.yml
```

---

## Controls

| Key | Action |
|-----|--------|
| W / A / S / D | Paddle (forward / left / back / right) |
| Shift | Sprint (uses stamina) |
| F12 | Toggle Photo Mode |
| Escape | Settings / Pause |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Engine | Unity 6000.4.6f1 LTS, Universal Render Pipeline |
| Language | C# (Unity), Python 3.11 (terrain pipeline) |
| Elevation Data | Copernicus GLO-30 DEM — 30m resolution, free, AWS S3 |
| Package Manager | UV / hatchling (Python), Unity Package Manager |
| CI/CD | GitHub Actions — game-ci/unity-builder, CodeQL |
| Build Targets | Windows x64, Linux x64, macOS |

---

## CI/CD

All pipelines run on every push and PR to `main`:

| Workflow | What it does |
|----------|-------------|
| **Python MVP** | Ruff lint, Black format check, pytest (27 tests), full pipeline run |
| **Unity Test** | Compile + EditMode/PlayMode tests via game-ci Docker |
| **Unity Build** | Win64 + Linux64 + macOS artifacts (on `main` push only) |
| **CodeQL** | Static security analysis for Python |

---

## Development

```bash
# Python tests
cd mvp && uv run pytest tests/ -v

# Lint + format
cd mvp && uv run ruff check src/
cd mvp && uv run black src/

# Full pipeline with real DEM
cd mvp && uv run mvp --skip-render

# Interactive 3D viewer (requires moderngl)
cd mvp && uv pip install -e '.[interactive]' && uv run mvp --interactive
```

---

## Known Issues

See [ROADMAP.md](ROADMAP.md) for the full audit. Key items:

- Real DEM not yet streaming into Unity builds (procedural terrain used at runtime)
- PhotoMode pixel filter is CPU-bound (PF3 — use GPU post-processing)
- Particle effects (splash, foam, mist) not yet implemented

---

## Documentation

| Document | Content |
|----------|---------|
| [ROADMAP.md](ROADMAP.md) | Full project audit, bugs, phased roadmap, tech debt |
| [CI_SETUP.md](CI_SETUP.md) | CI/CD configuration and secrets setup |
| [mvp/README.md](mvp/README.md) | Python terrain pipeline details |

---

## License

MIT — see [LICENSE](LICENSE).

MIT - see [LICENSE](LICENSE)

Data: © Kartverket, © ESA (Sentinel-2), OpenStreetMap contributors
