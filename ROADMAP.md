# Nidelven River Adventure - Roadmap

Last updated: 2026-05-13

## Build Status

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Current Status: RELEASED ✅ v0.0.1

**[Download Release](https://github.com/egkristi/Nidelven-river-adventure/releases/tag/v0.0.1)**

---

## GitHub Actions Pipeline

| Pipeline | Status | Purpose |
|----------|--------|---------|
| CI (Python) | ✅ Passing | Linting, tests |
| CodeQL | 🔄 Fixed | Python security scanning only |
| Releases | 🔄 Fixed | Source + builds (if secrets configured) |
| Unity CI | ⏸️ Optional | Needs UNITY_LICENSE secret |

**Recent Fixes (Issue #11):**
- CodeQL: Removed C# analysis (requires Unity), Python only
- Release: Conditional Unity builds, always creates source archive

---

## v0.0.1 Release - Complete ✅

### All 10 Issues Resolved

| Issue | Feature | Status |
|-------|---------|--------|
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

### Open Issues

| Issue | Title | Status |
|-------|-------|--------|
| #11 | Fix GitHub Actions workflows | 🔄 In Progress |

### Features Complete

#### Core Gameplay
- ✅ Terrain Generation (synthetic + Kartverket DEM) - #4
- ✅ River Flow with realistic current
- ✅ Boat Physics (buoyancy, paddling, capsize) - #1
- ✅ Camera System (auto-follow, orbit)

#### Content
- ✅ Vegetation System (GPU-instanced trees/rocks) - #5
- ✅ Day/Night Cycle (dynamic lighting) - #6
- ✅ Wildlife System (birds, deer AI) - #9
- ✅ Audio (river ambience, forest, birds) - #2

#### Systems
- ✅ Save/Load (JSON persistence) - #3
- ✅ Photo Mode (filters, capture) - #7
- ✅ Settings Menu (graphics, audio) - #10
- ✅ Tutorial System
- ✅ Game Quitter

#### Platform
- ✅ Steam Manager (achievements, cloud saves) - #8
- ✅ Steam Achievements (8 defined)

#### DevOps
- ✅ Python CI (ruff, black)
- ✅ CodeQL configured (Python only)
- ✅ Release automation (tag-based, conditional Unity)

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
