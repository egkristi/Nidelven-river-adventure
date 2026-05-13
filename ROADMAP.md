# Nidelven River Adventure - Roadmap

Last updated: 2026-05-13

## Build Status

[![CI](https://github.com/egkristi/Nidelven-river-adventure/actions/workflows/ci.yml/badge.svg)](https://github.com/egkristi/Nidelven-river-adventure/actions)

## Current Status

**All MVP features complete.** Development now focused on polish and platform features.

---

## Task Priority Matrix

### Must Do (Required to run on PC)

| Task | Status | Notes |
|------|--------|-------|
| Unity Build for Windows | ⬜ | Create standalone Windows executable |
| Input System | ✅ | Keyboard/mouse controls implemented |
| Graphics Settings | ⬜ | Quality presets (Low/Medium/High) |
| Resolution Support | ⬜ | 1080p, 1440p, 4K |
| Exit to Desktop | ⬜ | Graceful shutdown |

### Should Do (Recommended for release)

| Task | Issue | Priority | Notes |
|------|-------|----------|-------|
| Steam Integration | #8 | High | Distribution, achievements, cloud saves |
| Settings Menu | - | High | Graphics, audio, controls |
| Tutorial | - | Medium | First-time player guidance |
| Performance Optimization | - | Medium | Target 60 FPS on min spec |

### Could Do (Nice to have)

| Task | Issue | Priority | Notes |
|------|-------|----------|-------|
| Wildlife System | #9 | Medium | Birds, fish, deer |
| Weather Effects | - | Low | Rain, fog, wind |
| VR Support | - | Low | Meta Quest, SteamVR |
| Multiplayer | - | Low | Co-op or racing |
| Additional Rivers | - | Low | Other Norwegian rivers |

---

## Requirements to Run on PC

### Minimum Specs

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11 64-bit or Linux |
| CPU | Intel i5-8400 / AMD Ryzen 5 2600 |
| RAM | 16 GB |
| GPU | GTX 1060 6GB / RX 580 |
| Storage | 2 GB SSD |
| DirectX | 11 or 12 |

### Recommended Specs

| Component | Requirement |
|-----------|-------------|
| CPU | Intel i7-10700 / AMD Ryzen 7 3700X |
| RAM | 32 GB |
| GPU | RTX 3060 / RX 6700 XT |
| Storage | 2 GB NVMe SSD |

### To Build and Run

1. **Unity 6000 LTS** installed
2. **Clone repository**:
   ```bash
   git clone https://github.com/egkristi/Nidelven-river-adventure.git
   ```
3. **Open in Unity**: File → Open Project → select folder
4. **Build**:
   - File → Build Settings
   - Select PC, Mac & Linux Standalone
   - Click Build

### To Run Pre-built

1. Download from Releases (when available)
2. Extract archive
3. Run `NidelvenRiverAdventure.exe`

---

## Completed Features ✅

| Phase | Feature | Issue |
|-------|---------|-------|
| MVP | Terrain Generation | - |
| MVP | River Flow | - |
| MVP | Boat Physics | #1 |
| MVP | Audio System | #2 |
| MVP | Save/Load | #3 |
| MVP | Kartverket DEM Import | #4 |
| Phase 1 | Vegetation System | #5 |
| Phase 1 | Day/Night Cycle | #6 |
| Phase 2 | Photo Mode | #7 |

---

## In Progress 🔄

| Feature | Issue | Status |
|---------|-------|--------|
| Steam Integration | #8 | Issue created, awaiting implementation |
| Wildlife System | #9 | Issue created, awaiting implementation |

---

## Known Blockers

| Blocker | Impact | Solution |
|---------|--------|----------|
| Unity license secrets | CI builds | Add UNITY_LICENSE to GitHub secrets (see CI_SETUP.md) |
| No releases | Distribution | Build manually or wait for CI |

---

## CI/CD Status

| Pipeline | Status | Notes |
|----------|--------|-------|
| Python MVP | ✅ Passing | ruff, black, tests |
| Unity Test | ⏸️ Waiting | Needs UNITY_LICENSE secret |
| Unity Build | ⏸️ Waiting | Needs UNITY_LICENSE secret |

---

## Next Actions

1. **Immediate**: Add Unity secrets to GitHub (see CI_SETUP.md)
2. **This Week**: Implement Steam integration (#8)
3. **Next Week**: Build settings menu and graphics options
4. **Following**: Wildlife system (#9)

---

## License & Data

- Code: MIT License
- Terrain data: © Kartverket / Norwegian Mapping Authority
- Imagery: © ESA (Sentinel-2)
- River data: OpenStreetMap contributors
