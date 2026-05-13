# Roadmap: Nidelven River Adventure

This document tracks development progress and planned features.

Last updated: 2026-05-13

## Current Status: MVP Phase

The MVP focuses on:
1. ✅ Terrain generation (synthetic + real DEM support)
2. ✅ River flow visualization
3. ✅ Camera following river trajectory
4. 🔄 Boat physics (Issue #1)
5. ⬜ Soundscape (Issue #2)
6. ⬜ Save/load system (Issue #3)

## Completed Features

### MVP-1: Core Infrastructure ✅
- [x] Project structure with Unity + Python MVP
- [x] DEM downloader (Kartverket WCS)
- [x] Terrain mesh generator
- [x] UV package manager setup

### MVP-2: River System ✅
- [x] Gradient-following river path
- [x] Flow properties (velocity, width)
- [x] Spline smoothing
- [x] River mesh generation

### MVP-3: Camera & Rendering ✅
- [x] River-following camera
- [x] Manual orbit controls
- [x] Headless renderer (matplotlib)
- [x] OpenGL renderer (moderngl)

### MVP-4: Unity Scripts ✅
- [x] TerrainGenerator.cs (DEM import)
- [x] RiverController.cs
- [x] RiverCamera.cs
- [x] GameManager.cs
- [x] SimpleWater.shader

## In Progress

### MVP-5: Boat Physics 🔄
Issue: #1
- [ ] Boat prefab with buoyancy
- [ ] Paddle mechanics
- [ ] River current drift
- [ ] Collision with terrain

## Upcoming Milestones

### MVP-6: Soundscape
Issue: #2
- River ambience (speed-based)
- Forest ambience
- Bird sounds
- Paddle/water interaction

### MVP-7: Save/Load
Issue: #3
- JSON save format
- Progress persistence
- Settings save

### MVP-8: Real DEM Import
Issue: #4
- Kartverket DTM download
- GeoTIFF importer
- Coordinate conversion

## Post-MVP Features

| Feature | Priority | Status |
|---------|----------|--------|
| Vegetation system | High | ⬜ |
| Wildlife (ambient) | Medium | ⬜ |
| Day/night cycle | Medium | ⬜ |
| Weather effects | Medium | ⬜ |
| Photo mode | High | ⬜ |
| VR support | Low | ⬜ |
| Multiplayer | Low | ⬜ |
| Steam integration | High | ⬜ |

## Definition of Done

For each milestone:
1. Code complete and tested
2. Documentation updated
3. CI passes
4. GitHub issue closed with summary
5. Demo video/screenshots (if applicable)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow.
