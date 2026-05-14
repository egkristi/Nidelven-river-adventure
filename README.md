# Nidelven River Adventure 🛶

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)
[![CodeQL](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/codeql.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/codeql.yml)

A relaxing river exploration game set on the **Nidelven river in Agder, Norway**. Paddle through a photorealistic valley generated from real 30m satellite elevation data. Built with Unity 6000 LTS and a Python terrain pipeline.

---

## Running on PC

### Download a Build (easiest)

1. Go to [Actions → CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml)
2. Click the latest successful run on `main`
3. Download **Build-StandaloneWindows64** (or **Build-StandaloneLinux64**)
4. Extract the zip and run `NidelvenRiverAdventure.exe`

> Builds are produced automatically on every push to `main` (Windows + Linux).

### From Source (Unity Editor)

```bash
git clone https://github.com/egkristi/Nidelven-river-adventure.git
```

1. Install [Unity Hub](https://unity.com/download) and Unity **6000.4.x LTS**
2. Open the cloned folder via Unity Hub → "Add project from disk"
3. Open `Assets/Scenes/MainScene.unity`
4. Press **Play** ▶️

### Python MVP (terrain viewer only)

```bash
cd mvp
uv sync
uv run mvp                      # generates terrain + preview images
uv run mvp --interactive        # 3D terrain viewer (requires OpenGL)
```

The MVP downloads real Copernicus GLO-30 DEM data automatically on first run. Use `--sample` to skip the download and use synthetic terrain instead.

---

## Features

| Category | Details |
|----------|---------|
| **Terrain** | Real 30m DEM (Copernicus GLO-30) covering the Nidelven valley |
| **River** | Flow simulation based on elevation gradient descent |
| **Boat Physics** | Buoyancy, paddling, capsize & recovery |
| **Vegetation** | GPU-instanced trees and rocks |
| **Day/Night** | Dynamic sun cycle, atmospheric lighting |
| **Audio** | River ambience, birdsong, forest sounds |
| **Wildlife** | Birds, deer with steering-behavior AI |
| **Photo Mode** | Freeze time, color filters, screenshot capture |
| **Save/Load** | JSON persistence with auto-save |
| **Settings** | Graphics quality, audio levels, control remapping |
| **Tutorial** | Contextual first-time player guidance |
| **Steam** | Achievements, cloud saves (opt-in via `DISABLESTEAMWORKS`) |

---

## Project Structure

```
Assets/
  Scenes/            Unity scenes (MainScene.unity)
  Scripts/
    Core/            GameManager, AudioManager, SaveManager, PhotoMode, Steam
    Environment/     DayNightCycle, TerrainGenerator, Vegetation, Wildlife, River
    Player/          BoatController, RiverCamera
    UI/              SettingsMenu, TutorialSystem
  Shaders/           SimpleWater.shader
mvp/
  src/mvp/           Python pipeline (DEM download, terrain mesh, river flow, renderer)
  tests/             Pytest suite (7 tests)
Packages/            Unity package manifest
.github/workflows/   CI (Python + Unity) and CodeQL
```

---

## Controls

| Key | Action |
|-----|--------|
| W / A / S / D | Paddle (forward / left / back / right) |
| Shift | Sprint |
| F12 | Photo Mode |
| Escape | Settings / Pause |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Engine | Unity 6000 LTS, Universal Render Pipeline |
| Language | C# (Unity), Python 3.11 (MVP pipeline) |
| Elevation Data | Copernicus GLO-30 DEM — 30m resolution, free, no auth |
| Package Manager | UV (Python), Unity Package Manager |
| CI/CD | GitHub Actions (lint, test, build, CodeQL) |
| Build Targets | Windows x64, Linux x64 |

---

## CI/CD

All pipelines run on every push and PR to `main`:

| Workflow | What it does |
|----------|-------------|
| **Python MVP** | Ruff lint, Black format check, pytest, full pipeline run |
| **Unity Test** | Compile + EditMode/PlayMode tests (game-ci) |
| **Unity Build** | Produces Windows + Linux builds (artifacts on `main` only) |
| **CodeQL** | Static security analysis for Python |

---

## Development

```bash
# Run tests
cd mvp && uv run pytest tests/ -v

# Lint
cd mvp && uv run ruff check src/

# Format
cd mvp && uv run black src/
```

See [ROADMAP.md](ROADMAP.md) for planned features and progress, [CI_SETUP.md](CI_SETUP.md) for CI configuration details, and [mvp/README.md](mvp/README.md) for the Python pipeline documentation.

---

## License

MIT — see [LICENSE](LICENSE).

MIT - see [LICENSE](LICENSE)

Data: © Kartverket, © ESA (Sentinel-2), OpenStreetMap contributors
