"""
Minimal dependency-free terrain preview.
Can run without numpy/scipy/matplotlib.
Generates a simple ASCII preview and optional HTML output.
"""

import json
import math
import random
from pathlib import Path


def create_sample_dem_ascii(size: int = 64) -> list[list[float]]:
    """Create a simple synthetic DEM using pure Python."""
    dem = []
    random.seed(42)

    for y in range(size):
        row = []
        for x in range(size):
            # River valley (sine wave down center)
            river_x = size / 2 + (size / 8) * math.sin((y / size) * math.pi * 3)
            dist = abs(x - river_x)

            # Height: low at river, higher at edges
            base = 50
            river_depth = 30 * math.exp(-dist * 0.3)
            hills = (dist / size) ** 2 * 200
            noise = random.gauss(0, 2)

            # Waterfall feature
            if size * 0.55 < y < size * 0.65:
                hills += 20 * math.sin((y - size * 0.55) / (size * 0.1) * math.pi)

            height = base + river_depth + hills + noise
            row.append(max(0, height))
        dem.append(row)

    return dem


def trace_river_path(dem: list[list[float]]) -> list[tuple[int, int]]:
    """Trace a simple river path through the DEM."""
    size = len(dem)
    path = []

    # Start from top, center-ish
    x = size // 2

    for y in range(size):
        # Find lowest point in neighborhood
        best_x = x
        best_height = dem[y][x]

        for dx in range(-2, 3):
            nx = x + dx
            if 0 <= nx < size and dem[y][nx] < best_height:
                best_height = dem[y][nx]
                best_x = nx

        x = best_x
        path.append((x, y))

    return path


def render_ascii(dem: list[list[float]], path: list[tuple[int, int]], width: int = 80) -> str:
    """Render terrain as ASCII art."""
    size = len(dem)

    # Downsample to fit width
    step = max(1, size // width)

    # Height range
    flat_dem = [h for row in dem for h in row]
    h_min = min(flat_dem)
    h_max = max(flat_dem)
    h_range = h_max - h_min if h_max > h_min else 1

    # ASCII characters from low to high
    chars = " .,-~:;=!*#$@"

    # Create path set for fast lookup
    path_set = set(path)

    lines = []
    lines.append("NIDELVEN RIVER - TERRAIN PREVIEW (ASCII)")
    lines.append("=" * width)
    lines.append(f"Elevation range: {h_min:.0f}m - {h_max:.0f}m")
    lines.append("")

    for y in range(0, size, step):
        line = ""
        for x in range(0, size, step):
            if (x, y) in path_set:
                line += "~"  # River
            else:
                h = dem[y][x]
                idx = int((h - h_min) / h_range * (len(chars) - 1))
                idx = max(0, min(len(chars) - 1, idx))
                line += chars[idx]
        lines.append(line)

    lines.append("")
    lines.append("Legend: ~ = River,  . = Low,  @ = High")
    lines.append(f"Path length: {len(path)} points")

    return "\n".join(lines)


def render_html(dem: list[list[float]], path: list[tuple[int, int]], output_path: Path):
    """Render terrain as a simple HTML visualization."""
    size = len(dem)

    # Height range
    flat_dem = [h for row in dem for h in row]
    h_min = min(flat_dem)
    h_max = max(flat_dem)
    h_range = h_max - h_min if h_max > h_min else 1

    path_set = set(path)

    # Generate color for each pixel
    pixels = []
    for y in range(size):
        row = []
        for x in range(size):
            if (x, y) in path_set:
                # River: blue
                row.append((30, 100, 200))
            else:
                h = dem[y][x]
                t = (h - h_min) / h_range

                # Terrain gradient: green to brown to gray
                if t < 0.3:
                    # Green (low)
                    r = int(50 + t / 0.3 * 50)
                    g = int(100 + t / 0.3 * 100)
                    b = int(30 + t / 0.3 * 20)
                elif t < 0.7:
                    # Brown (mid)
                    t2 = (t - 0.3) / 0.4
                    r = int(100 + t2 * 100)
                    g = int(200 - t2 * 100)
                    b = int(50 - t2 * 30)
                else:
                    # Gray (high)
                    t3 = (t - 0.7) / 0.3
                    v = int(150 + t3 * 105)
                    r = g = b = v

                row.append((r, g, b))
        pixels.append(row)

    # Generate HTML
    pixel_size = max(2, 512 // size)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Nidelven River - Terrain Preview</title>
    <style>
        body {{ font-family: sans-serif; background: #222; color: #fff; text-align: center; }}
        h1 {{ margin: 20px; }}
        #terrain {{ display: inline-block; border: 2px solid #444; }}
        .pixel {{ width: {pixel_size}px; height: {pixel_size}px; display: inline-block; }}
        .row {{ line-height: 0; }}
        #legend {{ margin: 20px; font-size: 14px; }}
        .legend-item {{ display: inline-block; margin: 0 15px; }}
        .color-box {{ width: 20px; height: 20px; display: inline-block; vertical-align: middle; margin-right: 5px; }}
    </style>
</head>
<body>
    <h1>🛶 Nidelven River Adventure - MVP Preview</h1>
    <div id="terrain">
"""

    for y in range(size):
        html += '        <div class="row">\n'
        for x in range(size):
            r, g, b = pixels[y][x]
            html += f'            <div class="pixel" style="background:rgb({r},{g},{b})"></div>\n'
        html += "        </div>\n"

    html += """    </div>
    <div id="legend">
        <div class="legend-item"><div class="color-box" style="background:rgb(30,100,200)"></div> River</div>
        <div class="legend-item"><div class="color-box" style="background:rgb(50,150,40)"></div> Low terrain</div>
        <div class="legend-item"><div class="color-box" style="background:rgb(150,100,20)"></div> Mid terrain</div>
        <div class="legend-item"><div class="color-box" style="background:rgb(200,200,200)"></div> High terrain</div>
    </div>
    <p style="font-size: 12px; color: #888;">
        Synthetic terrain for MVP preview. Real DEM data will replace this in production.
    </p>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    print(f"  ✓ HTML preview saved: {output_path}")


def run_minimal_mvp(output_dir: Path = None):
    """Run the minimal MVP pipeline without any external dependencies."""
    if output_dir is None:
        output_dir = Path(__file__).parent / "output"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NIDELVEN RIVER - MINIMAL MVP (No dependencies)")
    print("=" * 60)
    print()

    # Generate DEM
    print("Generating synthetic DEM...")
    dem = create_sample_dem_ascii(size=64)
    print(f"  DEM size: {len(dem)}x{len(dem[0])}")

    # Trace river
    print("Tracing river path...")
    path = trace_river_path(dem)
    print(f"  Path length: {len(path)} points")

    # ASCII preview
    print("\n" + "-" * 60)
    print(render_ascii(dem, path, width=60))
    print("-" * 60)

    # HTML preview
    print("\nGenerating HTML preview...")
    html_path = output_dir / "preview_minimal.html"
    render_html(dem, path, html_path)

    # Save metadata
    metadata = {
        "type": "minimal_mvp",
        "dem_size": len(dem),
        "path_length": len(path),
        "elevation_range": {
            "min": min(h for row in dem for h in row),
            "max": max(h for row in dem for h in row),
        },
        "files_generated": [str(html_path.name)],
    }

    meta_path = output_dir / "mvp_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  ✓ Metadata saved: {meta_path}")

    print("\n" + "=" * 60)
    print("MINIMAL MVP COMPLETE")
    print("=" * 60)
    print("\nOpen this file in a browser to see the visual preview:")
    print(f"  file://{html_path.absolute()}")
    print("\nFor full features, install: pip install numpy scipy matplotlib pillow")


if __name__ == "__main__":
    run_minimal_mvp()
