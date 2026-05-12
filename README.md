# Nidelven River Adventure 🛶

A relaxing river exploration game set on the real Nidelven river in Agder, Norway. Built with Unity using real-world elevation data and satellite imagery.

## Vision

Paddle, kayak, or canoe down the entire 67km stretch of Nidelven — from the forests of Røysland to the coastal waters of Arendal. Experience the real landscape: every bend, every rapid, every waterfall exists in the real world.

**Current scope:** Single-player relaxing exploration.
**Future potential:** Time trials, multiplayer co-op, online racing, weather/survival mechanics.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Engine | Unity 6000 (LTS) |
| Render Pipeline | URP (Universal Render Pipeline) |
| Terrain | Real-world DEM → Unity Terrain / Mesh |
| Imagery | Satellite + aerial orthophotos |
| Water | Unity Water System + custom river flow |
| Physics | Unity Physics (Buoyancy, fluid dynamics) |
| Data Pipeline | Python / GDAL / QGIS preprocessing |

## Data Sources

| Data Type | Source | Resolution |
|-----------|--------|------------|
| Elevation (DEM) | [Kartverket Høydedata](https://hoydedata.no) | 1m laser scanned |
| Aerial Imagery | [Kartverket Norge i Bilder](https://norgeibilder.no) | 10-25cm |
| Satellite | Sentinel-2 (ESA) | 10m |
| River centerline | OpenStreetMap | vector |
| Water flow data | NVE (Norges vassdrags- og energidirektorat) | gauging stations |
| Vegetation / land cover | AR5 (Kartverket) | vector |

See [`docs/data-pipeline.md`](docs/data-pipeline.md) for the full ingestion workflow.

## Project Structure

```
Nidelven-river-adventure/
├── Assets/
│   ├── Scripts/
│   │   ├── Core/           # Game loop, state management
│   │   ├── Environment/    # Terrain, water, weather, vegetation
│   │   ├── Player/         # Paddle mechanics, boat physics, camera
│   │   ├── UI/             # Menus, HUD, map
│   │   ├── Data/           # Save/load, telemetry
│   │   └── Networking/     # (future) multiplayer
│   ├── Materials/
│   ├── Prefabs/
│   ├── Scenes/
│   ├── Shaders/            # Custom water, terrain blending
│   ├── Audio/
│   ├── Resources/          # Runtime-loaded assets
│   ├── Editor/             # Custom editor tools
│   ├── Plugins/
│   └── StreamingAssets/    # DEM tiles, satellite imagery
├── docs/
│   ├── data-pipeline.md    # Real-world data ingestion
│   ├── technical-architecture.md
│   └── contributing.md
├── design/
│   └── gdd.md              # Game Design Document
├── scripts/                # Python / GDAL preprocessing scripts
├── data-sources/           # Raw downloaded data (gitignored)
├── .github/workflows/
└── ProjectSettings/
```

## Quick Start (for developers)

### Prerequisites

- Unity 6000 LTS (or latest 6.x)
- Python 3.10+ (data pipeline)
- GDAL 3.6+ (ogr2ogr, gdalwarp, gdaldem)
- QGIS (optional, for visual inspection)

### Data Setup

```bash
# 1. Clone the repo
git clone https://github.com/egkristi/Nidelven-river-adventure.git
cd Nidelven-river-adventure

# 2. Download and process real-world data
python scripts/download_data.py --river nidelven --output data-sources/
python scripts/process_dem.py --input data-sources/dem/ --output Assets/StreamingAssets/Terrain/
python scripts/process_imagery.py --input data-sources/imagery/ --output Assets/StreamingAssets/Imagery/

# 3. Open in Unity
# File → Open Project → select this folder
```

### Play

1. Open `Assets/Scenes/River.unity`
2. Press Play
3. Select your vessel (kayak, canoe, or raft)
4. Paddle downstream and enjoy the scenery

## Milestones

| Phase | Goal | Status |
|-------|------|--------|
| 0 | Research & data collection | 🔄 In Progress |
| 1 | Terrain generation pipeline | ⬜ |
| 2 | Water system & river flow | ⬜ |
| 3 | Player controller (kayak) | ⬜ |
| 4 | Vegetation & environment | ⬜ |
| 5 | Soundscape & atmosphere | ⬜ |
| 6 | UI, menus, save system | ⬜ |
| 7 | Polish & optimization | ⬜ |
| 8 | Steam release prep | ⬜ |

See [Issues](https://github.com/egkristi/Nidelven-river-adventure/issues) for detailed tasks.

## License

MIT — see [LICENSE](LICENSE)

## Acknowledgements

- Terrain data © Kartverket / Norwegian Mapping Authority
- Sentinel-2 imagery © European Space Agency
- OpenStreetMap contributors
