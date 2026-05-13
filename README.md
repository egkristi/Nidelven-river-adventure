# Nidelven River Adventure 🛶

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

A relaxing river exploration game set on the real Nidelven river in Agder, Norway. Built with Unity using real-world elevation data and satellite imagery.

## Features

- ✅ **Terrain Generation**: Synthetic or real DEM from Kartverket
- ✅ **River Flow**: Realistic current based on elevation gradient
- ✅ **Boat Physics**: Buoyancy, paddling, capsize/recovery
- ✅ **Vegetation**: GPU-instanced trees and rocks
- ✅ **Day/Night Cycle**: Dynamic lighting and atmosphere
- ✅ **Soundscape**: Layered river, forest, and bird sounds
- ✅ **Photo Mode**: Freeze time, filters, screenshot capture
- ✅ **Save/Load**: JSON persistence with auto-save

## Quick Start

### For Players

Download from [Releases](https://github.com/egkristi/Nidelven-river-adventure/releases) (coming soon).

### For Developers

```bash
git clone https://github.com/egkristi/Nidelven-river-adventure.git
cd Nidelven-river-adventure

# Python MVP
cd mvp && uv sync && uv run mvp

# Or open in Unity
```

## Documentation

- [ROADMAP.md](ROADMAP.md) - Development progress
- [CI_SETUP.md](CI_SETUP.md) - CI/CD configuration
- [docs/data-pipeline.md](docs/data-pipeline.md) - DEM import workflow

## Controls

| Mode | Key | Action |
|------|-----|--------|
| General | F12 | Photo Mode |
| Camera | Space | Pause/Resume |
| Camera | Scroll | Zoom |
| Boat | WASD | Paddle/Steer |
| Boat | Shift | Sprint |
| Photo | Space | Capture |

## Tech Stack

- Unity 6000 LTS with URP
- Python 3.11 + UV for data pipeline
- Kartverket DEM data (Norway)

## License

MIT - see [LICENSE](LICENSE)

## Acknowledgements

- Terrain data © Kartverket
- Imagery © ESA (Sentinel-2)
- OpenStreetMap contributors
