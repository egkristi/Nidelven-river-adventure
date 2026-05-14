# Nidelven River Adventure - Roadmap

Last updated: 2026-05-13

## Build Status

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Current Status: All Issues Resolved, CI Green

---

## GitHub Actions Pipeline

| Pipeline | Status | Purpose |
|----------|--------|---------|
| CI (Python) | ✅ Passing | Lint (ruff/black), tests (pytest), MVP pipeline |
| CI (Unity Test) | ✅ Passing | Unity compile + test (requires UNITY_LICENSE secret) |
| CI (Unity Build) | ✅ Enabled | Builds Win64 + Linux64 (on main push) |
| CodeQL | ✅ Passing | Python security scanning |

---

## Completed Work

### Python MVP Pipeline
- ✅ DEM download (Copernicus GLO-30, 30m resolution, Nidelven area)
- ✅ Terrain mesh generation (OBJ export, 1680x2160 px)
- ✅ River flow tracing (gradient descent)
- ✅ Preview image rendering (topdown, 3D, river profile)
- ✅ Interactive 3D renderer (ModernGL, optional deps)
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
- ✅ Unity build (Windows + Linux)
- ✅ CodeQL security scanning
- ✅ Proper permissions and CI workarounds
- ✅ Large files removed from git history

---

## Resolved Issues

| Issue | Title | Resolution |
|-------|-------|------------|
| #12 | Add Unity scene to enable builds | Added MainScene.unity, enabled CI build |
| #13 | Remove large terrain.obj from git history | Removed via git-filter-repo |
| #14 | Download real DEM data | Copernicus GLO-30 from AWS S3 |
| #15 | Add interactive 3D renderer | Wired up ModernGL renderer as optional dep |

---

## Next Steps (v0.1.0)

### Phase 1: Playable Scene
- [x] Create main Unity scene with terrain
- [ ] Import generated terrain mesh into Unity
- [ ] Set up boat + camera in scene
- [x] Enable Unity build in CI
- [ ] First playable build

### Phase 2: Real Data
- [x] Download real DEM (Copernicus GLO-30, 30m)
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
