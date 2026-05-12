# Game Design Document: Nidelven River Adventure

## Elevator Pitch

A meditative river journey down the real Nidelven in southern Norway. Paddle a kayak, canoe, or raft through 67km of photorealistic terrain — every bend, rapid, and waterfall exists in the real world.

## Core Pillars

1. **Authenticity** — Real terrain, real river, real places
2. **Presence** — Feel the water, hear the forest, slow down
3. **Exploration** — Discover hidden coves, wildlife, viewpoints
4. **Accessibility** — No fail states, no pressure, pure flow

## Target Experience

**Mood:** Calm, contemplative, occasionally exhilarating (rapids)
**Pacing:** Self-directed, no time limits
**Session length:** 15 min — 3 hours (save/resume anywhere)
**Audio:** Binaural river sounds, ambient forest, distant birds

## Setting

### The River: Nidelven (Agder, Norway)

| Attribute | Detail |
|-----------|--------|
| Length | ~67 km |
| Source | Røysland (inland forests) |
| Mouth | Arendal (coastal town) |
| Terrain | Forested valleys, farmland, small towns, coastal delta |
| Notable features | Waterfalls, rapids, calm stretches, bridges |

### Key Locations (Waypoints)

| km | Location | Character |
|----|----------|-----------|
| 0 | Røysland | Narrow forest stream, clear water |
| 15 | Åmli | Small town, historic bridge |
| 30 | Nidelva | Wider river, farmland |
| 45 | Arendal approach | Estuary feel, tidal effects |
| 67 | Arendal harbor | Coastal finish, sunset views |

## Gameplay Mechanics

### Vessels

| Vessel | Speed | Stability | Best For |
|--------|-------|-----------|----------|
| Kayak | Fast | Low | Experienced, rapids |
| Canoe | Medium | Medium | Balanced exploration |
| Raft | Slow | High | Relaxing, wildlife watching |

### Controls (PC)

| Input | Action |
|-------|--------|
| W/S | Paddle forward/back |
| A/D | Turn |
| Space | Brake (reverse paddle) |
| Shift | Sprint (limited stamina) |
| Mouse | Camera look |
| Tab | Toggle map |
| Esc | Pause menu |

### River Physics

- **Flow:** Realistic current based on actual elevation gradient
- **Eddies:** Calm spots behind rocks for rest
- **Rapids:** Skill-based navigation (no instant fail)
- **Wind:** Affects open stretches

### Progression

No traditional "unlock" system. Progression is:
- **Discovery:** Find all waypoints, hidden coves
- **Knowledge:** Learn the river (where to rest, best routes)
- **Mastery:** Complete speed runs, perfect runs

Optional challenges (post-launch):
- Time trials (leaderboards)
- Photo mode achievements
- Wildlife spotting checklist

## Environment

### Terrain

- **Base:** Kartverket 1m DEM
- **Coverage:** Full 67km with 2km corridor
- **Detail:** LOD system, streaming chunks

### Vegetation

| Zone | Dominant Species |
|------|------------------|
| Upper river | Spruce, pine, birch |
| Farmland | Deciduous, hedgerows |
| Estuary | Reeds, coastal grasses |

Placement driven by:
- AR5 land cover data (real)
- Procedural fill where data sparse

### Wildlife (Ambient)

- Birds: Osprey, heron, ducks, eagles
- Fish: Salmon (jumping in rapids), trout
- Mammals: Deer (riverbanks), beaver, otter

### Water

- Unity Water System + custom river shader
- Flow direction from DEM gradient
- Whitecaps in rapids
- Reflections (SSR + planar)

### Weather/Time

- **Day cycle:** Compressed (1 real hour = full day)
- **Seasons:** Toggleable (spring green, autumn colors)
- **Weather:** Clear, overcast, light rain (no storms)

## Audio Design

### Layered Soundscape

| Layer | Content |
|-------|---------|
| Base | River ambience (varies by current speed) |
| Spatial | Birds, insects, wind in trees |
| Event | Splash, paddle strokes, wildlife calls |
| Music | Minimal, ambient generative (optional toggle) |

### Implementation

- Wwise or Unity Audio
- Binaural spatialization (headphones recommended)
- Dynamic mixing based on camera position

## UI/UX

### Main Menu

- Continue Journey
- New Journey (vessel select, starting point)
- Journey Log (stats, achievements, photos)
- Settings
- Exit

### In-Game HUD (Minimal)

- Compass (optional toggle)
- Distance to next waypoint
- Current speed
- Photo mode button

### Map

- Schematic river view
- Discovered waypoints marked
- Current position
- Optional: Full terrain view (satellite)

## Technical Requirements

### Minimum Spec (PC)

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11, Linux |
| CPU | Intel i5-8400 / AMD Ryzen 5 2600 |
| RAM | 16 GB |
| GPU | GTX 1060 6GB / RX 580 |
| Storage | 10 GB SSD |
| DirectX | 11 or 12 |

### Recommended

| Component | Requirement |
|-----------|-------------|
| CPU | Intel i7-10700 / AMD Ryzen 7 3700X |
| RAM | 32 GB |
| GPU | RTX 3060 / RX 6700 XT |
| Storage | 10 GB NVMe SSD |

## Post-Launch (Future)

| Feature | Priority |
|---------|----------|
| Photo mode | High |
| VR support | Medium |
| Multiplayer (co-op) | Medium |
| Multiplayer (racing) | Low |
| Additional rivers | Low |
| Mod support | Low |

## Success Metrics

- **User reviews:** >80% positive
- **Session duration:** Median >30 min
- **Completion rate:** >30% reach Arendal
- **Return rate:** >40% play again within 30 days

## Inspiration

- *Firewatch* (environmental storytelling)
- *ABZÛ* (underwater meditation)
- *Euro Truck Simulator* (real places, relaxing)
- *The Long Dark* (survival atmosphere, not mechanics)
