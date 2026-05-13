# Unity Scripts - Nidelven River Adventure

This folder contains all the C# scripts for the Unity implementation of Nidelven River Adventure.

## Folder Structure

```
Scripts/
├── Core/
│   └── GameManager.cs          # Central game coordinator
├── Environment/
│   ├── TerrainGenerator.cs     # DEM import and terrain generation
│   └── RiverController.cs      # River mesh and flow
├── Player/
│   └── RiverCamera.cs          # Camera following river
└── UI/                         # (Future) UI controllers
```

## Quick Start

### 1. Set Up the Scene

1. Create an empty GameObject named "World"
2. Add child GameObjects:
   - "Terrain" - Add TerrainGenerator component
   - "River" - Add RiverController component
   - "CameraRig" - Add RiverCamera component

### 2. Configure TerrainGenerator (on Terrain object)

- **useSyntheticFallback**: Enable for MVP (no DEM data needed)
- **terrainSize**: X=2000, Y=500, Z=2000 (meters)
- **resolution**: 513 (heightmap resolution)
- Add a terrain material (create URP Terrain/Lit material)

### 3. Configure RiverController (on River object)

- Drag Terrain GameObject into "Terrain Generator" field
- Set "Water Level Offset": -1 (meters below terrain)
- Add a water material (create URP shader for water)

### 4. Configure RiverCamera (on CameraRig)

- Drag River GameObject into "River" field
- Drag Terrain GameObject into "Terrain" field
- Camera component will be auto-added

### 5. Configure GameManager

1. Create empty GameObject named "GameManager"
2. Add GameManager component
3. Drag references to Terrain, River, and Camera objects

### 6. Press Play

The world will generate automatically and the camera will follow the river.

## Controls

| Key | Action |
|-----|--------|
| Space | Pause/Resume auto-follow |
| Left Click + Drag | Orbit camera around river |
| Scroll | Zoom in/out |
| Up Arrow | Speed up |
| Down Arrow | Slow down |
| R | Reset to start |
| Escape | Pause game |
| G | Regenerate world with new random seed |
| F1 | Show controls in console |

## Materials

### Terrain Material

Create a URP material with:
- Shader: Universal Render Pipeline/Terrain/Lit
- Add terrain textures for grass, rock, etc.

### Water Material

Create a new shader graph or use this simple setup:
- Base color: Light blue (0.2, 0.5, 0.8)
- Smoothness: 0.9
- Normal map: Add water normal map for waves
- Enable "Transparency" and set alpha to 0.8

## Importing Real DEM Data

1. Obtain DEM data from Kartverket (hoydedata.no)
2. Export as 16-bit RAW format
3. Place in Assets/StreamingAssets/
4. Update TerrainGenerator:
   - Set "Dem File Path" to the file
   - Disable "Use Synthetic Fallback"

## Troubleshooting

### Terrain is flat
- Check that TerrainGenerator resolution is set
- Verify useSyntheticFallback is enabled for MVP

### River not visible
- Check RiverController has water material assigned
- Verify terrain reference is set

### Camera not following
- Check RiverCamera has River reference assigned
- Verify GameManager is in scene

## Architecture

```
GameManager
    ├── TerrainGenerator (generates heightmap)
    ├── RiverController (creates mesh from terrain)
    └── RiverCamera (follows river path)
```

The terrain generates first, then the river samples terrain heights
to create its path, and finally the camera follows the river trajectory.

## Performance

- Terrain resolution 513: Good balance for MVP
- River path resolution 100: Sufficient for smooth following
- Target: 60 FPS on GTX 1060
