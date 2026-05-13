# Nidelven River Adventure - Roadmap

Last updated: 2026-05-13

## Build Status

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Current Status: MVP Complete, Unity Scene Needed

---

## GitHub Actions Pipeline

| Pipeline | Status | Purpose |
|----------|--------|---------|
| CI (Python) | ✅ Passing | Lint (ruff/black), tests (pytest), MVP pipeline |
| CI (Unity Test) | ✅ Passing | Unity compile + test (requires UNITY_LICENSE secret) |
| CI (Unity Build) | ⏸️ Disabled | Needs committed Unity scene (#12) |
| CodeQL | ✅ Passing | Python security scanning |

---

## Completed Work

### Python MVP Pipeline
- ✅ DEM generation (synthetic Nidelven valley)
- ✅ Terrain mesh generation (OBJ export)
- ✅ River flow tracing (gradient descent)
- ✅ Preview image rendering (topdown, 3D, river profile)
- ✅ Test suite (7 tests, pytest)
- ✅ Proper `src/` layout with `uv` package manager

### Unity Scripts (Assets/Scripts/)
- ✅ BoatController (physics, paddling, capsize)
- ✅ RiverCamera (orbit, auto-follow)
- ✅ TerrainGenerator, VegetationGenerator
- ✅ DayNightCycle, WildlifeSpawner
- ✅ AudioManager, RiverController
- ✅ SaveManager, SettingsMenu, TutorialSystem
- ✅ PhotoMode, SteamManager, GameQuitter

### CI/CD
- ✅ Python linting + formatting checks
- ✅ Pytest test suite in CI
- ✅ Unity test runner (game-ci)
- ✅ CodeQL security scanning
- ✅ Proper permissions and CI workarounds

---

## Open Issues

| Issue | Title | Priority |
|-------|-------|----------|
| #12 | Add Unity scene to enable builds | High |
| #13 | Remove large terrain.obj from git history | Medium |
| #14 | Download real Kartverket DEM data | Medium |
| #15 | Add interactive 3D renderer | Low |

---

## Next Steps (v0.1.0)

### Phase 1: Playable Scene
- [ ] Create main Unity scene with terrain
- [ ] Import generated terrain mesh into Unity
- [ ] Set up boat + camera in scene
- [ ] Enable Unity build in CI
- [ ] First playable build

### Phase 2: Real Data
- [ ] Download real DEM from Kartverket hoydedata.no
- [ ] Implement proper river path from OSM/NVE data
- [ ] Texture terrain from Sentinel-2 satellite imagery

### Phase 3: Polish
- [ ] Water shader (river surface rendering)
- [ ] Particle effects (splash, foam)
- [ ] LOD system for terrain
- [ ] Performance optimization

---

## PC Requirements

### Minimum
- OS: Windows 10/11 64-bit
- CPU: Intel i5-8400 / AMD Ryzen 5 2600
- RAM: 16 GB
- GPU: GTX 1060 6GB / RX 580
- Storage: 2 GB SSD

### Build
```bash
git clone https://github.com/egkristi/Nidelven-river-adventure.git
cd Nidelven-river-adventure
# Open in Unity 6000 LTS
# File → Build Settings → Build
```

---

## Next Steps (Optional)

- Fix CI workflows (#11)
- Weather effects (rain, fog)
- Multiplayer co-op
- VR support
- Additional rivers

---

## License & Data

- Code: MIT License
- Terrain: © Kartverket
- Imagery: © ESA (Sentinel-2)
- River data: OpenStreetMap contributors
