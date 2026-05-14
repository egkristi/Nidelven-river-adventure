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

## Quick Start

```bash
# Clone repo
git clone https://github.com/egkristi/Nidelven-river-adventure.git

# Run Python MVP (downloads real 30m DEM automatically)
cd mvp && uv sync && uv run mvp --skip-render

# Run tests
cd mvp && uv run pytest tests/ -v

# Interactive 3D viewer (optional)
cd mvp && uv pip install -e '.[interactive]' && uv run mvp --interactive

# Or open Assets/ in Unity 6000 LTS
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
