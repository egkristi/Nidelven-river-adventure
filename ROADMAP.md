# Nidelven River Adventure - Roadmap

Last updated: 2026-05-13

## Build Status

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Current Status: COMPLETE ✅

All planned features implemented.

---

## GitHub Actions Pipeline ✅ COMPLETE

| Pipeline | Status | Purpose |
|----------|--------|---------|
| CI (Python) | ✅ Passing | Linting, tests |
| CodeQL | ✅ Configured | Security scanning |
| Releases | ✅ Configured | Automated builds on tags |
| Unity CI | ⏸️ Waiting | Needs UNITY_LICENSE secret |

---

## Features Complete ✅

### Core Gameplay
- ✅ Terrain Generation (synthetic + Kartverket DEM) - #4
- ✅ River Flow with realistic current
- ✅ Boat Physics (buoyancy, paddling, capsize) - #1
- ✅ Camera System (auto-follow, orbit)

### Content
- ✅ Vegetation System (GPU-instanced trees/rocks) - #5
- ✅ Day/Night Cycle (dynamic lighting) - #6
- ✅ Wildlife System (birds, deer AI) - #9
- ✅ Audio (river ambience, forest, birds) - #2

### Systems
- ✅ Save/Load (JSON persistence) - #3
- ✅ Photo Mode (filters, capture) - #7
- ✅ Settings Menu (graphics, audio) - #10
- ✅ Tutorial System
- ✅ Game Quitter

### Platform
- ✅ Steam Manager (achievements, cloud saves) - #8
- ✅ Steam Achievements (8 defined)

### DevOps
- ✅ Python CI (ruff, black)
- ✅ CodeQL (C#, Python)
- ✅ Release automation

---

## All Issues Closed ✅

| Issue | Title | Status |
|-------|-------|--------|
| #1 | Boat Physics | ✅ |
| #2 | Soundscape | ✅ |
| #3 | Save/Load | ✅ |
| #4 | Kartverket DEM Import | ✅ |
| #5 | Vegetation System | ✅ |
| #6 | Day/Night Cycle | ✅ |
| #7 | Photo Mode | ✅ |
| #8 | Steam Integration | ✅ |
| #9 | Wildlife System | ✅ |
| #10 | Settings Menu | ✅ |

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
