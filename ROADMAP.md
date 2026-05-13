# Roadmap: Nidelven River Adventure

This document tracks development progress and planned features.

Last updated: 2026-05-13

## Current Status: ✅ MVP COMPLETE

All MVP features have been implemented:

| Feature | Status | Issue |
|---------|--------|-------|
| Terrain Generation | ✅ Complete | - |
| River Flow | ✅ Complete | - |
| Camera Following | ✅ Complete | - |
| Boat Physics | ✅ Complete | #1 |
| Soundscape | ✅ Complete | #2 |
| Save/Load System | ✅ Complete | #3 |
| CI/CD Pipeline | ✅ Complete | - |

## Completed Milestones

### MVP-1: Core Infrastructure ✅
- [x] Project structure with Unity + Python MVP
- [x] DEM downloader (Kartverket WCS)
- [x] Terrain mesh generator
- [x] UV package manager setup
- [x] GitHub Actions CI (Python MVP)

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

### MVP-5: Boat Physics ✅
- [x] BoatController.cs with buoyancy
- [x] Paddle mechanics (WASD)
- [x] River current drift
- [x] Capsize/recovery system
- [x] Three vessel types (kayak/canoe/raft)
- [x] Stamina system

### MVP-6: Soundscape ✅
- [x] AudioManager.cs
- [x] Layered river ambience (calm/rapids)
- [x] Forest ambience
- [x] Bird sounds (random intervals)
- [x] Paddle sound hooks

### MVP-7: Save/Load ✅
- [x] SaveManager.cs
- [x] JSON serialization
- [x] Auto-save every 60s
- [x] Multiple save slots
- [x] Progress persistence

## In Progress

### Phase 1: Content 🔄

| Feature | Priority | Status | Issue |
|---------|----------|--------|-------|
| Real DEM Import | High | 🔄 In Progress | #4 |
| Vegetation System | High | ⬜ Open | - |
| Wildlife (Ambient) | Medium | ⬜ Open | - |
| Day/Night Cycle | Medium | ⬜ Open | - |

## Upcoming Milestones

### Phase 2: Polish
| Feature | Priority | Status |
|---------|----------|--------|
| Weather Effects | Medium | ⬜ |
| Photo Mode | High | ⬜ |
| VR Support | Low | ⬜ |
| Multiplayer | Low | ⬜ |
| Steam Integration | High | ⬜ |

## CI/CD Status

| Pipeline | Status | Notes |
|----------|--------|-------|
| Python MVP | ✅ Passing | ruff, black, tests |
| Unity Test | ⏸️ Skipped | Needs UNITY_LICENSE secret |
| Unity Build | ⏸️ Skipped | Needs UNITY_LICENSE secret |

## Definition of Done

For each milestone:
1. Code complete and tested
2. Documentation updated
3. CI passes
4. GitHub issue closed with summary
5. Demo video/screenshots (if applicable)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow.

## Recent Commits

- CI: Fixed Python workflow (pip instead of uv)
- feat: Implemented SaveManager with JSON serialization
- feat: Implemented AudioManager with layered soundscape
- feat: Implemented BoatController with physics
- docs: Updated README.md with UV instructions
- docs: Created ROADMAP.md with milestone tracking
