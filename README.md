# Nidelven River Adventure 🛶

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

A relaxing river exploration game set on the real Nidelven river in Agder, Norway. Built with Unity using real-world elevation data from Kartverket.

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

# Or open Assets/ in Unity 6000 LTS
```

## Controls

| Key | Action |
|-----|--------|
| F12 | Photo Mode |
| WASD | Paddle boat |
| Shift | Sprint |
| Escape | Settings Menu |

## Documentation

- [ROADMAP.md](ROADMAP.md) - Development status
- [CI_SETUP.md](CI_SETUP.md) - CI/CD configuration

## Tech Stack

- Unity 6000 LTS with URP
- Python 3.11 + UV
- Kartverket DEM data
- GitHub Actions CI/CD

## License

MIT - see [LICENSE](LICENSE)

Data: © Kartverket, © ESA (Sentinel-2), OpenStreetMap contributors
