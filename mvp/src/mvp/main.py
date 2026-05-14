#!/usr/bin/env python3
"""
Nidelven River Adventure - MVP Entry Point

This script runs the complete MVP pipeline:
1. Download/generate DEM data
2. Generate terrain mesh
3. Calculate river flow path
4. Render preview images
5. (Optional) Launch interactive 3D renderer

Usage:
    python -m mvp.main                     # Full pipeline with synthetic data
    python -m mvp.main --sample            # Force use of synthetic DEM
    python -m mvp.main --interactive       # Launch interactive renderer
    python -m mvp.main --output-dir ./out  # Custom output directory
"""

import argparse
import time
from pathlib import Path

from .dem_downloader import get_dem_path
from .headless_renderer import generate_preview_images
from .river_flow import create_river_from_dem
from .terrain_mesh import create_terrain_from_dem, export_unity_raw


def main():
    parser = argparse.ArgumentParser(description="Nidelven River Adventure MVP")
    parser.add_argument("--sample", action="store_true", help="Force use of synthetic DEM data")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive 3D renderer (requires display)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None, help="Output directory for generated files"
    )
    parser.add_argument("--skip-terrain", action="store_true", help="Skip terrain mesh generation")
    parser.add_argument("--skip-river", action="store_true", help="Skip river flow calculation")
    parser.add_argument("--skip-render", action="store_true", help="Skip image rendering")
    parser.add_argument(
        "--kartverket",
        action="store_true",
        help="Use Kartverket 1m LiDAR DEM (requires network, rasterio)",
    )

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir is None:
        # Use project-level output directory (mvp/output/)
        output_dir = Path(__file__).parent.parent.parent / "output"
    else:
        output_dir = args.output_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NIDELVEN RIVER ADVENTURE - MVP")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print()

    # Track timing
    start_time = time.time()

    # Step 1: Get DEM data
    print("STEP 1: DEM Data")
    print("-" * 40)

    data_dir = Path(__file__).parent.parent.parent / "data"

    if args.kartverket:
        # Try Kartverket 1m DTM (high-res LiDAR)
        from .kartverket_dem import get_kartverket_dem

        print("  Source: Kartverket DTM 1m (LiDAR)")
        dem_array = get_kartverket_dem(data_dir)
        if dem_array is not None:
            dem_path = data_dir / "kartverket_dtm1m.tif"
            print(f"  ✓ Using Kartverket 1m: {dem_array.shape[1]}x{dem_array.shape[0]}")
        else:
            print("  ✗ Kartverket unavailable, falling back to Copernicus 30m")
            prefer_real = not args.sample
            dem_path = get_dem_path(data_dir, prefer_real=prefer_real)
    else:
        prefer_real = not args.sample
        dem_path = get_dem_path(data_dir, prefer_real=prefer_real)
    print()

    # Step 2: Generate terrain mesh
    if not args.skip_terrain:
        print("STEP 2: Terrain Mesh Generation")
        print("-" * 40)

        terrain_mesh = create_terrain_from_dem(dem_path, output_dir, save_obj=True)

        # Also export Unity-ready RAW heightmap
        print("\n  Exporting Unity terrain...")
        export_unity_raw(dem_path, output_dir)
        print()
    else:
        print("STEP 2: Skipping terrain mesh generation")
        terrain_mesh = None
        print()

    # Step 3: Calculate river flow
    if not args.skip_river:
        print("STEP 3: River Flow Calculation")
        print("-" * 40)

        flow_data, metadata = create_river_from_dem(dem_path, output_dir)
        river_path = flow_data["path"]
        print()
    else:
        print("STEP 3: Skipping river flow calculation")
        flow_data = None
        river_path = None
        print()

    # Step 4: Generate preview images
    if not args.skip_render and terrain_mesh is not None:
        print("STEP 4: Generate Preview Images")
        print("-" * 40)

        # Load DEM for rendering
        from .terrain_mesh import load_dem

        dem_data, _ = load_dem(dem_path)

        generate_preview_images(
            dem_data, river_path=river_path, flow_data=flow_data, output_dir=output_dir
        )
        print()
    else:
        print("STEP 4: Skipping image rendering")
        print()

    # Step 5: Interactive renderer (optional)
    if args.interactive:
        print("STEP 5: Launching Interactive Renderer")
        print("-" * 40)

        try:
            from .renderer import run_renderer

            if terrain_mesh and flow_data:
                # Load DEM for river mesh generation
                from .terrain_mesh import load_dem

                dem_data, _ = load_dem(dem_path)

                # Generate river mesh for rendering
                from .river_flow import generate_river_mesh

                river_mesh = generate_river_mesh(flow_data, dem_data, terrain_mesh)

                run_renderer(
                    terrain_mesh=terrain_mesh, water_mesh=river_mesh, river_path=river_path
                )
            else:
                print("  Cannot launch interactive renderer: missing terrain or river data")
        except ImportError as e:
            print(f"  Cannot launch interactive renderer: {e}")
            print("  Install with: uv pip install -e '.[interactive]'")

    # Summary
    elapsed = time.time() - start_time
    print("=" * 60)
    print("MVP PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Time elapsed: {elapsed:.1f}s")
    print(f"Output directory: {output_dir}")
    print()
    print("Generated files:")

    output_files = list(output_dir.iterdir()) if output_dir.exists() else []
    if output_files:
        for f in sorted(output_files):
            size = f.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            print(f"  {f.name:40s} {size_str:>10s}")
    else:
        print("  (none)")

    print()
    print("Next steps:")
    print("  - View output images in the output directory")
    print("  - Run with --interactive for 3D preview")
    print("  - Copy terrain.raw + terrain_metadata.json to Assets/StreamingAssets/")
    print("  - Unity will auto-load real terrain on Play")
    print()


if __name__ == "__main__":
    main()
