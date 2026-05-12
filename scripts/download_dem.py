#!/usr/bin/env python3
"""
Download DEM data from Kartverket Høydedata.

Usage:
    python download_dem.py --bbox 8.4,58.7,8.6,58.9 --output ./dem/
    python download_dem.py --river nidelven --output ./dem/
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Tuple

import requests
from osgeo import ogr

# Kartverket WCS endpoint
KARTVERKET_WCS = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm1"

# Approximate bounding box for full Nidelven river
RIVER_BBOX = {
    "nidelven": (8.2, 58.3, 8.9, 58.9)  # min_lon, min_lat, max_lon, max_lat
}


def parse_bbox(bbox_str: str) -> Tuple[float, float, float, float]:
    """Parse bbox string 'min_lon,min_lat,max_lon,max_lat'."""
    parts = bbox_str.split(",")
    if len(parts) != 4:
        raise ValueError("bbox must be in format: min_lon,min_lat,max_lon,max_lat")
    return tuple(float(x.strip()) for x in parts)


def get_coverage_from_kartverket(bbox: Tuple[float, float, float, float]) -> dict:
    """Query Kartverket WCS for available data in bbox."""
    # WCS GetCapabilities to discover layers
    # WCS DescribeCoverage to get details
    # WCS GetCoverage to download
    
    # For now, this is a placeholder that returns metadata
    # Full implementation would parse WCS XML responses
    
    print(f"Querying Kartverket for bbox: {bbox}")
    print(f"CRS: EPSG:4326 (WGS84)")
    print(f"Note: Full implementation requires parsing WCS XML")
    
    return {
        "source": "Kartverket Høydedata",
        "bbox": bbox,
        "resolution": "1m",
        "format": "GeoTIFF",
        "url": f"https://hoydedata.no/OnlineTileDownload/Download.ashx?..."
    }


def download_manual_instructions(bbox: Tuple[float, float, float, float], output_dir: Path):
    """Print instructions for manual download."""
    print("\n" + "="*60)
    print("MANUAL DOWNLOAD REQUIRED")
    print("="*60)
    print(f"\nBounding box: {bbox}")
    print(f"\nOption 1: Kartverket Høydedata (web interface)")
    print(f"  URL: https://hoydedata.no")
    print(f"  Steps:")
    print(f"    1. Navigate to 'Download data'")
    print(f"    2. Draw rectangle covering: lon {bbox[0]} to {bbox[2]}, lat {bbox[1]} to {bbox[3]}")
    print(f"    3. Select 'DTM 1m' (Digital Terrain Model)")
    print(f"    4. Download as GeoTIFF")
    print(f"    5. Save to: {output_dir}")
    print(f"\nOption 2: Direct API (requires API key)")
    print(f"  Contact: geodatainfo@kartverket.no")
    print(f"\nOutput directory: {output_dir}")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Download DEM data for Nidelven")
    parser.add_argument("--bbox", type=str, help="Bounding box: min_lon,min_lat,max_lon,max_lat")
    parser.add_argument("--river", type=str, choices=["nidelven"], default="nidelven",
                        help="Predefined river area")
    parser.add_argument("--output", type=Path, default=Path("../data-sources/dem"),
                        help="Output directory")
    parser.add_argument("--check-only", action="store_true",
                        help="Only check availability, don't download")
    
    args = parser.parse_args()
    
    # Determine bbox
    if args.bbox:
        bbox = parse_bbox(args.bbox)
    else:
        bbox = RIVER_BBOX.get(args.river)
        if not bbox:
            print(f"Unknown river: {args.river}")
            sys.exit(1)
    
    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Check/download
    info = get_coverage_from_kartverket(bbox)
    
    if args.check_only:
        print(json.dumps(info, indent=2))
        return
    
    # For now, provide manual instructions
    # TODO: Implement full WCS client
    download_manual_instructions(bbox, args.output)
    
    # Save metadata
    metadata_file = args.output / "download_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump({
            "bbox": bbox,
            "river": args.river,
            "requested_at": "2024-01-01T00:00:00Z",  # TODO: actual timestamp
            "source": "Kartverket Høydedata",
            "status": "manual_download_required"
        }, f, indent=2)
    
    print(f"Metadata saved to: {metadata_file}")


if __name__ == "__main__":
    main()
