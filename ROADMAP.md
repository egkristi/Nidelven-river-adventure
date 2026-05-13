# Roadmap: Nidelven River Adventure

Last updated: 2026-05-13

## Build Status

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Current Status: Phase 2 Features Complete ✅

| Phase | Status | Description |
|-------|--------|-------------|
| MVP | ✅ Complete | Core gameplay |
| Phase 1 | ✅ Complete | Content (vegetation, day/night) |
| Phase 2 | ✅ Complete | Polish (photo mode) |
| Phase 3 | 🔄 In Progress | Data Integration (DEM import) |

## Completed Features

### MVP ✅
- Terrain Generation
- River Flow
- Camera Following
- Boat Physics (#1)
- Soundscape (#2)
- Save/Load (#3)

### Phase 1 ✅
- Vegetation System (#5)
- Day/Night Cycle (#6)

### Phase 2 ✅
- Photo Mode (#7)

## Open Issues

| # | Title | Phase |
|---|-------|-------|
| 4 | Import real DEM data from Kartverket | Phase 3 |

## CI/CD

| Pipeline | Status |
|----------|--------|
| Python MVP | ✅ Passing |
| Unity Test | ⏸️ Needs license secret |
| Unity Build | ⏸️ Needs license secret |

## Recent Commits

- feat: PhotoMode with filters and capture
- feat: DayNightCycle with dynamic lighting
- feat: VegetationGenerator with GPU instancing
- feat: BoatController, AudioManager, SaveManager
- docs: Updated README and ROADMAP
- CI: Fixed Python workflow
