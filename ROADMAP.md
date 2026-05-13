# Roadmap: Nidelven River Adventure

This document tracks development progress and planned features.

Last updated: 2026-05-13

## Build Status

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Current Status: Phase 1 Content Complete ✅

| Phase | Status | Description |
|-------|--------|-------------|
| MVP | ✅ Complete | Core gameplay loop |
| Phase 1 | ✅ Complete | Content (vegetation, day/night) |
| Phase 2 | 🔄 In Progress | Polish (photo mode, DEM, Steam) |

## Completed Milestones

### MVP: Core Gameplay ✅
All MVP features implemented and tested.

| Feature | Status | Issue |
|---------|--------|-------|
| Terrain Generation | ✅ | - |
| River Flow | ✅ | - |
| Camera Following | ✅ | - |
| Boat Physics | ✅ | #1 |
| Soundscape | ✅ | #2 |
| Save/Load System | ✅ | #3 |
| CI/CD Pipeline | ✅ | - |

### Phase 1: Content ✅
| Feature | Status | Issue |
|---------|--------|-------|
| Vegetation System | ✅ Complete | #5 |
| Day/Night Cycle | ✅ Complete | #6 |

## In Progress

### Phase 2: Polish 🔄

| Feature | Priority | Status | Issue |
|---------|----------|--------|-------|
| Real DEM Import | High | 🔄 In Progress | #4 |
| Photo Mode | High | ⬜ Open | #7 |

## Open Issues

| # | Title | Phase | Labels |
|---|-------|-------|--------|
| 4 | Import real DEM data from Kartverket | Phase 2 | `mvp`, `data` |
| 7 | Photo Mode with Share | Phase 2 | `phase-2`, `feature` |

## Closed Issues ✅

| # | Title | Closed |
|---|-------|--------|
| 1 | Boat Physics | ✅ |
| 2 | Soundscape | ✅ |
| 3 | Save/Load | ✅ |
| 5 | Vegetation System | ✅ |
| 6 | Day/Night Cycle | ✅ |

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

- feat: DayNightCycle with dynamic lighting (closes #6)
- feat: VegetationGenerator with GPU instancing (closes #5)
- docs: Updated README and ROADMAP
- CI: Fixed Python workflow
- feat: BoatController, AudioManager, SaveManager
