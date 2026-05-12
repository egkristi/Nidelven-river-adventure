# Jira Issues: Nidelven River Adventure

**Epic:** Nidelven River Adventure - Unity Game
**GitHub:** https://github.com/egkristi/Nidelven-river-adventure
**Status:** Ready to create when Jira is available

---

## Epic: Nidelven River Adventure - Unity Game

**Type:** Epic  
**Summary:** Nidelven River Adventure - Unity Game  
**Description:**
A relaxing river exploration game set on the real Nidelven river in Agder, Norway. Built with Unity using real-world elevation data and satellite imagery.

Scope: Single-player relaxing exploration. Paddle, kayak, or canoe down the entire 67km stretch.

GitHub: https://github.com/egkristi/Nidelven-river-adventure

---

## Milestone 0: Research & Data Collection

**Type:** Story  
**Summary:** M0: Research & data collection  
**Description:**
Gather all real-world data needed for authentic terrain reconstruction.

**Tasks:**
- [ ] Download Kartverket DTM 1m for full Nidelven corridor (bbox: 8.2,58.3,8.9,58.9)
- [ ] Download Sentinel-2 imagery (cloud-free, summer season)
- [ ] Download OpenStreetMap river network (centerline, banks, rapids)
- [ ] Research water flow data from NVE (gauging stations)
- [ ] Document key waypoints: Røysland, Åmli, Nidelva, Arendal
- [ ] Validate data alignment (DEM vs imagery vs OSM)
- [ ] Create data-sources/manifest.json with version tracking

**Acceptance Criteria:**
- All raw data downloaded and verified
- Data alignment errors < 5m
- Manifest documents all sources with dates/licenses

---

## Milestone 1: Terrain Generation Pipeline

**Type:** Story  
**Summary:** M1: Terrain generation pipeline  
**Summary:** Build automated pipeline from real-world DEM to Unity Terrain.

**Tasks:**
- [ ] Create scripts/process_dem.py (merge, crop, normalize)
- [ ] Split 67km corridor into terrain tiles (2000m x 2000m, 1024 resolution)
- [ ] Generate normal maps from DEM (gdaldem hillshade/aspect/slope)
- [ ] Convert DEM to Unity Terrain heightmaps (.raw format)
- [ ] Implement terrain streaming/LOD system
- [ ] Create editor tool for terrain tile preview
- [ ] Test terrain at runtime (walk/fly through full 67km)

**Acceptance Criteria:**
- Full 67km terrain loaded seamlessly
- 60 FPS with terrain streaming
- Accurate elevation profile matches real Nidelven

---

## Milestone 2: Water System & River Flow

**Type:** Story  
**Summary:** M2: Water system & river flow  
**Description:** Create realistic river with flow based on actual elevation gradient.

**Tasks:**
- [ ] Generate river mesh from OSM centerline + DEM
- [ ] Implement Unity Water System with custom river shader
- [ ] Calculate flow direction vectors from DEM slope
- [ ] Add flow rate variation (calm stretches vs rapids)
- [ ] Create eddies behind rocks/sudden width changes
- [ ] Implement water audio (spatial, varies by current speed)
- [ ] Add foam/whitecaps in rapids

**Acceptance Criteria:**
- Water flows downhill correctly (validated against real gradient)
- Current speed varies from 0.5 m/s (calm) to 3+ m/s (rapids)
- Boat drifts with current when not paddling
- No visible seams between water and terrain

---

## Milestone 3: Player Controller (Kayak)

**Type:** Story  
**Summary:** M3: Player controller (kayak)  
**Description:** Physics-based kayak controller with paddle mechanics.

**Tasks:**
- [ ] Design kayak physics (buoyancy, drag, stability)
- [ ] Implement paddle mechanics (left/right strokes, momentum)
- [ ] Create input system (WASD + mouse look)
- [ ] Add camera controller (follow kayak, smooth damping)
- [ ] Implement sprint (Shift) with stamina system
- [ ] Create brake/reverse paddle (Space)
- [ ] Add vessel variants: kayak (fast), canoe (balanced), raft (stable)

**Acceptance Criteria:**
- Responsive controls with ~100ms input lag
- Realistic water interaction (paddling against current)
- Kayak capsizes in rapids if poorly controlled
- Vessel selection menu functional

---

## Milestone 4: Vegetation & Environment

**Type:** Story  
**Summary:** M4: Vegetation & environment  
**Description:** Populate terrain with trees, rocks, and landmarks based on real data.

**Tasks:**
- [ ] Parse AR5 vegetation data (forest, farmland, wetland)
- [ ] Create tree prefabs: spruce, pine, birch, oak
- [ ] Implement GPU-instanced tree rendering
- [ ] Place trees based on AR5 + slope/elevation rules
- [ ] Add rocks/boulders along riverbanks
- [ ] Place bridges from OSM data
- [ ] Add landmark labels (villages, viewpoints)

**Acceptance Criteria:**
- Vegetation matches real land cover types
- 60 FPS with full vegetation
- Recognizable real locations (e.g., Åmli bridge)
- No floating trees, proper terrain alignment

---

## Milestone 5: Soundscape & Atmosphere

**Type:** Story  
**Summary:** M5: Soundscape & atmosphere  
**Description:** Layered audio design for immersion.

**Tasks:**
- [ ] Record/source river ambience (varies by current)
- [ ] Add bird sounds (osprey, heron, eagles)
- [ ] Create forest ambience (wind in trees, insects)
- [ ] Implement spatial audio (binaural for headphones)
- [ ] Add paddle/water interaction sounds
- [ ] Create optional ambient music (generative/minimal)
- [ ] Implement audio mixing based on camera location

**Acceptance Criteria:**
- Audio feels realistic and immersive
- No jarring transitions between biomes
- Music toggleable (default: off)
- Spatial audio works with stereo headphones

---

## Milestone 6: UI, Menus & Save System

**Type:** Story  
**Summary:** M6: UI, menus & save system  
**Description:** Complete game flow from menu to end credits.

**Tasks:**
- [ ] Create main menu (Continue, New Journey, Journey Log, Settings, Exit)
- [ ] Design minimal HUD (compass, distance, speed)
- [ ] Implement pause menu (Resume, Settings, Save & Quit)
- [ ] Create save system (position, vessel, time of day)
- [ ] Build Journey Log (stats, achievements, photos)
- [ ] Add map overlay (river schematic, discovered waypoints)
- [ ] Implement settings (graphics, audio, controls)

**Acceptance Criteria:**
- Save/load works at any point
- Journey persists across sessions
- UI navigable with keyboard/mouse
- Map shows accurate position

---

## Milestone 7: Polish & Optimization

**Type:** Story  
**Summary:** M7: Polish & optimization  
**Description:** Performance pass and bug fixes.

**Tasks:**
- [ ] Profile and optimize terrain streaming
- [ ] Optimize water rendering (GPU cost)
- [ ] Reduce vegetation overdraw
- [ ] Implement texture streaming for satellite imagery
- [ ] Fix physics glitches (boat getting stuck)
- [ ] Add loading screen with tips
- [ ] Create tutorial overlay (first launch)

**Acceptance Criteria:**
- 60 FPS on GTX 1060 (min spec)
- 30 FPS on integrated graphics (optional)
- No major memory leaks
- Load time < 30 seconds to gameplay

---

## Milestone 8: Steam Release Prep

**Type:** Story  
**Summary:** M8: Steam release prep  
**Description:** Final packaging and distribution setup.

**Tasks:**
- [ ] Create Steam store page assets (trailer, screenshots)
- [ ] Build Windows x64 release
- [ ] Build Linux x64 release
- [ ] Set up Steam Cloud saves
- [ ] Configure Steam achievements
- [ ] Write store description and tags
- [ ] Prepare press kit

**Acceptance Criteria:**
- Builds run on clean Windows/Linux installs
- Steam integration functional
- Store page approved by Steam
- Ready for "Coming Soon" announcement

---

## Technical Debt / Future

**Type:** Task  
**Summary:** Tech: Multiplayer architecture research  
**Description:** Research networking approach for future co-op/racing modes.

**Type:** Task  
**Summary:** Tech: VR controller support  
**Description:** Evaluate VR adaptation feasibility (Meta Quest, SteamVR).

**Type:** Task  
**Summary:** Tech: Additional rivers  
**Description:** Document pipeline for adapting to other Norwegian rivers.

---

*Created: 2026-05-12*
*When Jira is available, create Epic first, then link all Stories to it.*
