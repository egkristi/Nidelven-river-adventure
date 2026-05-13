# Roadmap: Nidelven River Adventure

This document tracks development progress and planned features.

Last updated: 2026-05-13

## Build Status

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Current Status: Phase 1 Content

| Phase | Status | Description |
|-------|--------|-------------|
| MVP | ✅ Complete | Core gameplay loop |
| Phase 1 | 🔄 In Progress | Content (vegetation, day/night, DEM) |
| Phase 2 | ⬜ Planned | Polish (photo mode, Steam) |

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

## In Progress

### Phase 1: Content 🔄

| Feature | Priority | Status | Issue |
|---------|----------|--------|-------|
| Vegetation System | High | ✅ Implemented | #5 |
| Day/Night Cycle | High | ⬜ Open | #6 |
| Real DEM Import | High | ⬜ Open | #4 |

## Open Issues

| # | Title | Phase | Labels |
|---|-------|-------|--------|
| 4 | Import real DEM data from Kartverket | Phase 1 | `mvp`, `data` |
| 5 | Vegetation System | Phase 1 | `phase-1`, `graphics` |
| 6 | Day/Night Cycle | Phase 1 | `phase-1`, `lighting` |
| 7 | Photo Mode | Phase 2 | `phase-2`, `feature` |

## Upcoming Milestones

### Phase 2: Polish
| Feature | Priority | Status | Issue |
|---------|----------|--------|-------|
| Photo Mode | High | ⬜ Open | #7 |
| Wildlife (Ambient) | Medium | ⬜ | - |
| Weather Effects | Medium | ⬜ | - |
| Steam Integration | High | ⬜ | - |

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

- feat: VegetationGenerator with GPU instancing
- docs: Updated README and ROADMAP - MVP Complete
- CI: Fixed Python workflow (pip instead of uv)
- feat: BoatController, AudioManager, SaveManager
