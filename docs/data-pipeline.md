# Data Pipeline — Real-World to Unity

This document describes how real-world geographic data is ingested, processed, and converted into Unity-compatible assets.

## Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Sources   │───▶│   Download      │───▶│  Processing     │───▶│  Unity Assets   │
│  (Kartverket,   │    │  (Python/GDAL)  │    │  (GDAL/Python)  │    │  (Terrain,      │
│   Sentinel-2)   │    │                 │    │                 │    │   Textures)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Data Sources

### 1. Elevation (DEM) — Kartverket Høydedata

**Source:** https://hoydedata.no

| Dataset | Resolution | Coverage | Format |
|---------|------------|----------|--------|
| DTM (Digital Terrain Model) | 1m | Norway | GeoTIFF |
| DSM (Digital Surface Model) | 1m | Norway | GeoTIFF |

**Why:** Laser-scanned at 1-meter resolution — best available for Norway.

**Download method:**
- WCS service (Web Coverage Service)
- Area-of-interest: Bounding box around entire Nidelven watershed
- Alternative: Manual download via web interface

```bash
# Example: Download 10km x 10km area around Åmli
python scripts/download_dem.py \
  --source kartverket \
  --bbox 8.4,58.7,8.6,58.9 \
  --output data-sources/dem/
```

### 2. Aerial Imagery — Kartverket Norge i Bilder

**Source:** https://norgeibilder.no

| Dataset | Resolution | Coverage |
|---------|------------|----------|
| Orthophoto | 10-25cm | Most populated areas |

**Why:** Higher resolution than satellite for populated areas.

**Note:** May need to blend with satellite for forested/remote sections.

### 3. Satellite Imagery — Sentinel-2

**Source:** https://dataspace.copernicus.eu (ESA)

| Dataset | Bands | Resolution |
|---------|-------|------------|
| Sentinel-2 L2A | RGB + NIR | 10m |

**Why:** Complete coverage, free, regularly updated.

**Download method:**
- Copernicus Data Space Ecosystem API
- Filter by cloud cover < 10%
- Select most recent clear image

```bash
python scripts/download_sentinel.py \
  --bbox 8.2,58.3,8.9,58.9 \
  --start-date 2024-05-01 \
  --end-date 2024-09-30 \
  --max-cloud 10 \
  --output data-sources/imagery/
```

### 4. River Network — OpenStreetMap

**Source:** https://www.openstreetmap.org

| Feature | Tag |
|---------|-----|
| River centerline | `waterway=river` |
| River bank | `natural=water` + `water=river` |
| Rapids | `whitewater:section` |
| Bridge | `bridge=yes` |

**Download:**
```bash
# Overpass API query
python scripts/download_osm.py \
  --query 'way["waterway"="river"]["name"~"Nidelven"]'
  --output data-sources/osm/river.geojson
```

### 5. Additional Data

| Data | Source | Purpose |
|------|--------|---------|
| Water flow | NVE (hydro.no) | Realistic current speeds |
| Vegetation | AR5 (Kartverket) | Forest, farmland placement |
| Place names | SSR (Kartverket) | Village labels |

## Processing Pipeline

### Step 1: Merge & Crop DEM

```bash
# Merge multiple DEM tiles
gdalbuildvrt data-sources/dem/nidelven.vrt data-sources/dem/*.tif

# Crop to river corridor (2km buffer)
gdalwarp \
  -cutline data-sources/osm/river-buffer-2km.shp \
  -crop_to_cutline \
  -dstnodata -9999 \
  data-sources/dem/nidelven.vrt \
  data-sources/processed/dem-cropped.tif
```

### Step 2: Generate Normal Maps

```bash
gdaldem hillshade data-sources/processed/dem-cropped.tif \
  data-sources/processed/hillshade.tif -z 2

gdaldem slope data-sources/processed/dem-cropped.tif \
  data-sources/processed/slope.tif

gdaldem aspect data-sources/processed/dem-cropped.tif \
  data-sources/processed/aspect.tif
```

### Step 3: Convert to Unity Terrain

```python
# scripts/dem_to_unity.py
import numpy as np
from osgeo import gdal

# Read DEM
ds = gdal.Open('dem-cropped.tif')
band = ds.GetRasterBand(1)
data = band.ReadAsArray()

# Normalize to Unity terrain height (0-1000m = 0-1)
height_scale = 1000.0  # Max terrain height in meters
normalized = data / height_scale

# Split into terrain tiles (1024x1024 per tile)
# Save as Unity-readable raw files
```

### Step 4: Satellite → Unity Texture

```bash
# Reproject to same CRS as DEM
gdalwarp -t_srs EPSG:25833 \
  data-sources/imagery/sentinel.tif \
  data-sources/processed/imagery-reprojected.tif

# Resize to power-of-2 for Unity
gdal_translate -outsize 8192 8192 \
  data-sources/processed/imagery-reprojected.tif \
  Assets/StreamingAssets/Imagery/satelite-8k.tif
```

### Step 5: River Mesh Generation

```python
# scripts/generate_river_mesh.py
# From OSM centerline + DEM:
# 1. Sample elevation along river path
# 2. Create cross-section profiles
# 3. Extrude river bed mesh
# 4. Calculate flow direction vectors
```

## Unity Import Settings

### Terrain

| Setting | Value |
|---------|-------|
| Size | 2000m x 2000m (per tile) |
| Height | 1000m |
| Resolution | 1025 (heightmap) / 1024 (control) |
| Material | URP Terrain/Lit |

### Textures

| Texture | Format | Size | Compress |
|---------|--------|------|----------|
| Satellite | RGB(A) | 8K-16K | BC7 |
| Normal | RGB | 2K-4K | BC5 |
| Mask (splat) | R/G/B/A | 1K | BC4 |

## Data Updates

Real-world data changes:
- **DEM:** Rarely (landslide, new construction)
- **Imagery:** Seasonally (sentinel), every few years (aerial)
- **OSM:** Continuously

Recommendation: Pin to specific data versions. Update quarterly for OSM, annually for imagery.

## Storage & Versioning

Raw data is **gitignored** (too large). Store in:
- S3-compatible bucket, or
- Google Drive / Dropbox, or
- Self-hosted file server

Document exact versions in `data-sources/manifest.json`.

## Tools Required

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Orchestration |
| GDAL 3.6+ | Raster/vector processing |
| QGIS | Visual validation |
| Unity 6000+ | Final import |
