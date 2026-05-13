# Nidelven River Adventure 🛶

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

A relaxing river exploration game set on the real Nidelven river in Agder, Norway. Built with Unity using real-world elevation data from Kartverket.

## Features

### Complete ✅
- Terrain Generation (synthetic + Kartverket DEM)
- River Flow with realistic current
- Boat Physics (buoyancy, paddling, capsize)
- Vegetation System (GPU-instanced trees/rocks)
- Day/Night Cycle with dynamic lighting
- Audio (river ambience, birds, forest)
- Photo Mode with filters
- Save/Load with JSON persistence

### In Development 🔄
- Steam Integration (#8)
- Wildlife System (#9)

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
| Space | Brake/Recover |

## Documentation

- [ROADMAP.md](ROADMAP.md) - Development status
- [CI_SETUP.md](CI_SETUP.md) - CI/CD configuration
- [Issues](https://github.com/egkristi/Nidelven-river-adventure/issues)

## Tech Stack

- Unity 6000 LTS with URP
- Python 3.11 + UV
- Kartverket DEM data

## License

MIT - see [LICENSE](LICENSE)

Data: © Kartverket, © ESA (Sentinel-2), OpenStreetMap contributors
