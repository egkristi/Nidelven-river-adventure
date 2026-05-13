# Nidelven River Adventure 🛶

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

A relaxing river exploration game set on the real Nidelven river in Agder, Norway. Built with Unity using real-world elevation data from Kartverket.

## Current Status

- ✅ Python MVP pipeline (terrain generation, river flow, preview images)
- ✅ CI/CD (Python linting, tests, Unity test runner)
- ✅ Unity scripts (boat physics, camera, audio, etc.)
- ⏸️ Unity build (disabled until scenes are committed)

## Features

- ✅ **Terrain Generation**: Synthetic or real DEM from Kartverket
- ✅ **River Flow**: Realistic current based on elevation gradient
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

# Run Python MVP
cd mvp && uv sync && uv run mvp

# Run tests
cd mvp && uv run pytest tests/ -v

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
- Kartverket DEM data
- GitHub Actions CI/CD

## License

MIT - see [LICENSE](LICENSE)

Data: © Kartverket, © ESA (Sentinel-2), OpenStreetMap contributors
