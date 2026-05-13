# Nidelven River Adventure 🛶

A relaxing river exploration game set on the real Nidelven river in Agder, Norway. Built with Unity using real-world elevation data and satellite imagery.

## Vision

Paddle, kayak, or canoe down the entire 67km stretch of Nidelven — from the forests of Røysland to the coastal waters of Arendal. Experience the real landscape: every bend, every rapid, every waterfall exists in the real world.

**Current scope:** Single-player relaxing exploration.  
**Future potential:** Time trials, multiplayer co-op, online racing, weather/survival mechanics.

## Quick Start

### For Players

Download the latest build from [Releases](https://github.com/egkristi/Nidelven-river-adventure/releases) (coming soon).

### For Developers

```bash
# Clone the repo
git clone https://github.com/egkristi/Nidelven-river-adventure.git
cd Nidelven-river-adventure

# Setup Python MVP (uses UV)
cd mvp
uv sync

# Run the MVP previewer
uv run mvp

# Or open in Unity
# File → Open Project → select this folder
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Engine | Unity 6000 (LTS) |
| Render Pipeline | URP (Universal Render Pipeline) |
| Terrain | Real-world DEM → Unity Terrain |
| Water | Custom URP shader with flow |
| Physics | Unity Physics (Buoyancy) |
| Data Pipeline | Python 3.11 + UV + GDAL |

## Project Structure

```
Nidelven-river-adventure/
├── Assets/                 # Unity project
│   ├── Scripts/
│   │   ├── Core/          # GameManager, AudioManager, SaveManager
│   │   ├── Environment/     # TerrainGenerator, RiverController, VegetationGenerator
│   │   ├── Player/          # BoatController, RiverCamera
│   │   └── UI/
│   ├── Shaders/           # Water shader
│   └── Scenes/
├── mvp/                    # Python terrain previewer
│   ├── dem_downloader.py
│   ├── terrain_mesh.py
│   ├── river_flow.py
│   └── renderer.py
├── docs/                   # Documentation
│   ├── data-pipeline.md
│   └── ROADMAP.md
└── design/
    └── gdd.md              # Game Design Document
```

## Controls

### Camera (Auto-Follow Mode)
| Key | Action |
|-----|--------|
| Space | Pause/Resume auto-follow |
| Left Click + Drag | Orbit camera |
| Scroll | Zoom in/out |
| Up/Down | Speed up/slow down |
| R | Reset to start |

### Boat (Player Mode)
| Key | Action |
|-----|--------|
| W / Up | Paddle forward |
| S / Down | Paddle backward |
| A / Left | Turn left (paddle right) |
| D / Right | Turn right (paddle left) |
| Shift | Sprint (uses stamina) |
| Space | Brake / Recover from capsize |

## Development

### Python MVP

The `mvp/` folder contains a standalone Python previewer for rapid iteration:

```bash
cd mvp
uv run python minimal.py      # Zero-dependency ASCII preview
uv run python -m mvp.main     # Full 3D preview
uv run python -m mvp.main --download  # Download real DEM
```

### Unity Setup

1. Create GameObjects: GameManager, Terrain, River, CameraRig, PlayerBoat
2. Add components:
   - Terrain → TerrainGenerator
   - River → RiverController
   - Terrain → VegetationGenerator (optional)
   - CameraRig → RiverCamera
   - PlayerBoat → BoatController + Rigidbody
   - (empty) → GameManager, AudioManager, SaveManager
3. Link references (see Scripts/README.md)
4. Press Play

### CI/CD

GitHub Actions runs:
- ✅ Python MVP linting (ruff, black)
- ✅ Minimal MVP execution test
- ⏸️ Unity tests (requires Unity license secrets)

**Latest Build Status:** [![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Features

### Implemented ✅

| Feature | Description | Issue |
|---------|-------------|-------|
| Terrain Generation | Synthetic valley or real DEM import | - |
| River Flow | Gradient-based path with realistic current | - |
| Camera System | Auto-follow with orbit controls | - |
| Boat Physics | Buoyancy, paddling, capsize/recovery | #1 |
| Soundscape | Layered river/forest ambience, birds | #2 |
| Save/Load | JSON persistence, auto-save, stats | #3 |
| Vegetation | GPU-instanced trees and rocks | #5 |

### In Progress 🔄

| Feature | Issue |
|---------|-------|
| Real DEM Import | #4 |
| Day/Night Cycle | #6 |

### Planned ⬜

| Feature | Priority | Issue |
|---------|----------|-------|
| Photo Mode | High | #7 |
| Wildlife (Ambient) | Medium | - |
| Weather Effects | Medium | - |
| Steam Integration | High | - |

## Data Sources

| Data | Source | Resolution |
|------|--------|------------|
| DEM | [Kartverket](https://hoydedata.no) | 1m/10m |
| Imagery | [Kartverket](https://norgeibilder.no) | 10-25cm |
| Satellite | Sentinel-2 (ESA) | 10m |
| River | OpenStreetMap | vector |

## Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed development status.

### Current: Phase 1 Content
- ✅ MVP Complete (terrain, river, boat, audio, save)
- 🔄 Vegetation System (#5)
- 🔄 Day/Night Cycle (#6)
- ⬜ Real DEM Import (#4)

## Contributing

1. Check [ROADMAP.md](ROADMAP.md) for open tasks
2. See [GitHub Issues](https://github.com/egkristi/Nidelven-river-adventure/issues)
3. Follow existing code style (UV + ruff + black)
4. Submit PR with clear description

## License

MIT — see [LICENSE](LICENSE)

## Acknowledgements

- Terrain data © Kartverket / Norwegian Mapping Authority
- Sentinel-2 imagery © European Space Agency
- OpenStreetMap contributors
