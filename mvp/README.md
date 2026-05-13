# MVP Terrain Previewer
# Quick-start: python -m mvp.main

This directory contains a standalone Python MVP that:
- Downloads real DEM data from Kartverket
- Generates terrain mesh from elevation data
- Creates a river trajectory following actual topography
- Renders a 3D preview with camera following the river

## Quick Start

```bash
cd mvp
pip install -r requirements.txt
python -m mvp.main
```

## Files

| File | Purpose |
|------|---------|
| `dem_downloader.py` | Download DEM from Kartverket WCS |
| `terrain_mesh.py` | Generate terrain mesh from DEM |
| `river_flow.py` | Calculate river path from elevation gradient |
| `renderer.py` | OpenGL-based 3D renderer (moderngl) |
| `camera.py` | Camera controller following river trajectory |
| `main.py` | Entry point |

## Data Flow

```
Kartverket WCS → GeoTIFF → numpy array → terrain mesh (OBJ)
                                    ↓
                              river path (spline)
                                    ↓
                         OpenGL renderer + camera follow
```

## Notes

- The MVP uses a **simplified DEM** (10m resolution instead of 1m) for fast iteration
- Full 1m data will be used in the Unity version
- River path is generated from DEM gradient, not OSM (for independence)
