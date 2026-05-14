# Nidelven River Adventure 🛶

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

A relaxing river exploration game set on the real Nidelven river in Agder, Norway. Built with Unity using real-world elevation data from Copernicus GLO-30 DEM.

## Current Status

- ✅ Python MVP pipeline (terrain generation, river flow, real DEM)
- ✅ CI/CD (Python linting, tests, Unity test + build)
- ✅ Unity scripts (boat physics, camera, audio, etc.)
- ✅ Unity scene (MainScene with camera + lighting)
- ✅ Real DEM data (Copernicus GLO-30 30m resolution)

## Features

- ✅ **Terrain Generation**: Real DEM from Copernicus GLO-30 (30m resolution)
- ✅ **River Flow**: Realistic current based on elevation gradient
- ✅ **Interactive Renderer**: 3D terrain viewer with ModernGL (optional)
- ✅ **Boat Physics**: Buoyancy, paddling, capsize/recovery
- ✅ **Vegetation System**: GPU-instanced trees and rocks
- ✅ **Day/Night Cycle**: Dynamic lighting and atmosphere
- ✅ **Audio**: River ambience, birds, forest sounds
- ✅ **Photo Mode**: Freeze time, filters, screenshot capture
- ✅ **Save/Load**: JSON persistence with auto-save
- ✅ **Settings Menu**: Graphics, audio, controls
- ✅ **Tutorial System**: First-time player guidance
- ✅ **Steam Integration**: Achievements, cloud saves
- ✅ **Wildlife System**: Birds, deer with AI behavior
- ✅ **CI/CD**: GitHub Actions for CI, CodeQL, releases

## Running on PC

### Option 1: Download a Build (easiest)

1. Go to [Actions → CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml)
2. Click the latest successful run on `main`
3. Download the artifact **Build-StandaloneWindows64** (or **Build-StandaloneLinux64**)
4. Extract the zip and run `NidelvenRiverAdventure.exe`

> Builds are produced automatically on every push to `main`.

### Option 2: Unity Editor (development)

1. Install [Unity Hub](https://unity.com/download) and Unity **6000 LTS** (6000.4.x)
2. Clone the repo and open the root folder in Unity Hub → "Add project from disk"
3. Open `Assets/Scenes/MainScene.unity`
4. Press **Play** ▶️

### Option 3: Python MVP Terrain Viewer

```bash
# Clone repo
git clone https://github.com/egkristi/Nidelven-river-adventure.git
cd Nidelven-river-adventure/mvp

# Install and run (downloads real 30m DEM automatically)
uv sync && uv run mvp --skip-render

# Interactive 3D terrain viewer (requires OpenGL)
uv pip install -e '.[interactive]' && uv run mvp --interactive
```

### Running Tests

```bash
cd mvp && uv run pytest tests/ -v
```

## Project Structure

```
Assets/Scripts/    Unity C# scripts (boat, camera, terrain, audio, etc.)
mvp/               Python MVP pipeline
  src/mvp/         Source code (terrain mesh, river flow, renderer)
  tests/           Pytest test suite
  output/          Generated files (gitignored)
Packages/          Unity package manifest
.github/workflows/ CI/CD configuration
```

## Controls

| Key | Action |
|-----|--------|
| F12 | Photo Mode |
| WASD | Paddle boat |
| Shift | Sprint |
| Escape | Settings Menu |

## Documentation

- [ROADMAP.md](ROADMAP.md) - Development status & next steps
- [CI_SETUP.md](CI_SETUP.md) - CI/CD configuration
- [mvp/README.md](mvp/README.md) - Python MVP details

## Tech Stack

- Unity 6000 LTS with URP
- Python 3.11 + UV + pytest
- Copernicus GLO-30 DEM (30m, free, no auth)
- GitHub Actions CI/CD

## License

MIT - see [LICENSE](LICENSE)

Data: © Kartverket, © ESA (Sentinel-2), OpenStreetMap contributors
