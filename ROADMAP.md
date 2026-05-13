# Nidelven River Adventure - Roadmap

Last updated: 2026-05-13

## Build Status

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Current Status

**PC Release Ready - Core Systems Complete**

---

## GitHub Actions Pipeline Tasks

### CI/CD Infrastructure (Priority: High)

| Task | Status | Notes |
|------|--------|-------|
| 1. Set up GitHub Actions pipeline for CI | ✅ | Python MVP linting and tests |
| 2. Set up GitHub Actions pipeline for CodeQL | ⬜ | Security scanning |
| 3. Set up GitHub Actions pipeline for releases | ⬜ | Automated builds on tags |
| 4. Set up GitHub Actions pipeline as required | ⬜ | Unity builds, dependency checks |

#### Required Pipelines:

| Pipeline | Purpose | Trigger |
|----------|---------|---------|
| `ci.yml` | Python linting/tests | Push/PR |
| `codeql.yml` | Security analysis | Push to main, weekly |
| `release.yml` | Build and publish | Tag push (v*) |
| `unity.yml` | Unity builds | Push/PR (if secrets configured) |
| `dependabot.yml` | Dependency updates | Daily checks |

---

## Task Priority Matrix

### Must Do (Required for PC Release) ✅ COMPLETE

| Task | Status | Notes |
|------|--------|-------|
| Input System | ✅ | Keyboard/mouse controls |
| Graphics Settings | ✅ | Resolution, quality, fullscreen, render scale |
| Resolution Support | ✅ | All resolutions supported |
| Exit to Desktop | ✅ | GameQuitter with auto-save |
| Settings Menu | ✅ | Graphics, audio, controls panels |
| Tutorial System | ✅ | Step-by-step player guidance |

### Should Do (For Full Release)

| Task | Issue | Status | Notes |
|------|-------|--------|-------|
| Steam Integration | #8 | 🔄 In Progress | Achievements, cloud saves implemented |
| Performance Optimization | - | ⬜ | Target 60 FPS on min spec |
| Main Menu | - | ⬜ | Title screen, new/continue game |
| Loading Screen | - | ⬜ | Progress indicator |

### Could Do (Post-Release)

| Task | Issue | Status | Notes |
|------|-------|--------|-------|
| Wildlife System | #9 | ⬜ | Birds, fish, deer |
| Weather Effects | - | ⬜ | Rain, fog, wind |
| VR Support | - | ⬜ | Meta Quest, SteamVR |
| Multiplayer | - | ⬜ | Co-op or racing |
| Additional Rivers | - | ⬜ | Other Norwegian rivers |

---

## What You Need to Run on PC

### Minimum Specs

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11 64-bit |
| CPU | Intel i5-8400 / AMD Ryzen 5 2600 |
| RAM | 16 GB |
| GPU | GTX 1060 6GB / RX 580 |
| Storage | 2 GB SSD |
| DirectX | 11 or 12 |

### Build Instructions

```bash
# 1. Clone repository
git clone https://github.com/egkristi/Nidelven-river-adventure.git

# 2. Open in Unity 6000 LTS
# File → Open Project → select folder

# 3. Build for Windows
# File → Build Settings → PC Standalone → Build
```

---

## Completed Features ✅

### Core Gameplay
- ✅ Terrain Generation (synthetic + Kartverket DEM)
- ✅ River Flow with realistic current
- ✅ Boat Physics (buoyancy, paddling, capsize/recovery)
- ✅ Camera System (auto-follow, orbit)

### Content
- ✅ Vegetation System (GPU-instanced trees/rocks)
- ✅ Day/Night Cycle (dynamic lighting)
- ✅ Audio (river ambience, birds, forest)

### Systems
- ✅ Save/Load (JSON persistence)
- ✅ Photo Mode (freeze time, filters, screenshots)
- ✅ Settings Menu (graphics, audio, controls)
- ✅ Tutorial System (player guidance)
- ✅ Game Quitter (graceful exit)

### Platform
- ✅ Steam Manager (achievements, stats, cloud saves)
- ✅ Steam Achievements (8 defined)

---

## Open Issues

| Issue | Title | Status |
|-------|-------|--------|
| #8 | Steam Integration | 🔄 Steam Manager implemented, needs App ID |
| #9 | Wildlife System | ⬜ Not started |

---

## CI/CD Status

| Pipeline | Status |
|----------|--------|
| Python MVP | ✅ Passing |
| CodeQL | ⬜ Not configured |
| Releases | ⬜ Not configured |
| Unity Test | ⏸️ Needs UNITY_LICENSE secret |
| Unity Build | ⏸️ Needs UNITY_LICENSE secret |

---

## Next Actions

1. **Set up CodeQL workflow** for security scanning
2. **Set up release workflow** for automated builds
3. **Add Steam App ID** to SteamManager.cs
4. **Build Windows executable** for testing

---

## License & Data

- Code: MIT License
- Terrain: © Kartverket
- Imagery: © ESA (Sentinel-2)
- River data: OpenStreetMap contributors
