"""
Headless renderer for MVP.
Generates images without requiring a display.
Uses matplotlib for terrain visualization.
"""

from pathlib import Path

import numpy as np


def render_terrain_topdown(
    dem_data: np.ndarray,
    river_path: np.ndarray | None = None,
    output_path: Path | None = None,
    title: str = "Nidelven River - Terrain",
) -> np.ndarray:
    """
    Render a top-down view of terrain with river overlay.

    Returns:
        RGB image array
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import LightSource
    except ImportError:
        print("matplotlib not available for rendering")
        return np.zeros((512, 512, 3), dtype=np.uint8)

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    # Create hillshade for 3D effect
    ls = LightSource(azdeg=315, altdeg=45)

    # Hillshade
    rgb = ls.shade(dem_data, plt.cm.terrain, vert_exag=0.1, blend_mode="overlay")

    ax.imshow(rgb, origin="lower", extent=[0, dem_data.shape[1], 0, dem_data.shape[0]])

    # Overlay river path
    if river_path is not None:
        if river_path.shape[1] >= 2:
            ax.plot(river_path[:, 1], river_path[:, 0], "b-", linewidth=2, alpha=0.8, label="River")
            ax.plot(river_path[:, 1], river_path[:, 0], "c-", linewidth=1, alpha=0.5)

        # Mark start and end
        ax.plot(river_path[0, 1], river_path[0, 0], "g^", markersize=10, label="Start")
        ax.plot(river_path[-1, 1], river_path[-1, 0], "rv", markersize=10, label="End")

    # Add elevation contours
    contours = ax.contour(dem_data, levels=10, colors="black", alpha=0.3, linewidths=0.5)
    ax.clabel(contours, inline=True, fontsize=6, fmt="%1.0fm")

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("X (pixels)")
    ax.set_ylabel("Y (pixels)")
    ax.legend(loc="upper right")
    ax.set_aspect("equal")

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"  ✓ Saved: {output_path}")

    # Convert to numpy array
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()

    plt.close(fig)

    return img


def render_river_profile(flow_data: dict, output_path: Path | None = None):
    """
    Render river elevation profile and flow properties.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available for rendering")
        return

    elevations = flow_data["elevations"]
    velocities = flow_data["velocities"]
    widths = flow_data["widths"]

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # Elevation profile
    axes[0].plot(elevations, "g-", linewidth=1.5)
    axes[0].set_ylabel("Elevation (m)")
    axes[0].set_title("River Elevation Profile", fontweight="bold")
    axes[0].grid(True, alpha=0.3)

    # Velocity
    axes[1].plot(velocities, "b-", linewidth=1.5)
    axes[1].set_ylabel("Velocity (m/s)")
    axes[1].set_title("Flow Velocity", fontweight="bold")
    axes[1].grid(True, alpha=0.3)

    # Width
    axes[2].plot(widths, "r-", linewidth=1.5)
    axes[2].set_ylabel("Width (m)")
    axes[2].set_xlabel("Distance along river")
    axes[2].set_title("River Width", fontweight="bold")
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"  ✓ Saved: {output_path}")

    plt.close(fig)


def render_3d_perspective(
    dem_data: np.ndarray,
    river_path: np.ndarray | None = None,
    output_path: Path | None = None,
    angle: float = 45.0,
    title: str = "Nidelven River - 3D View",
):
    """
    Render a 3D perspective view using matplotlib.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib 3D not available")
        return

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection="3d")

    # Create meshgrid
    x = np.arange(dem_data.shape[1])
    y = np.arange(dem_data.shape[0])
    X, Y = np.meshgrid(x, y)

    # Plot surface (downsample for performance)
    step = max(1, int(max(dem_data.shape) / 200))
    ax.plot_surface(
        X[::step, ::step],
        Y[::step, ::step],
        dem_data[::step, ::step],
        cmap="terrain",
        alpha=0.8,
        linewidth=0,
        antialiased=True,
    )

    # Plot river path
    if river_path is not None and river_path.shape[1] >= 2:
        # Sample elevations along path
        path_elevations = []
        for row, col in river_path[:, :2]:
            r = int(np.clip(round(row), 0, dem_data.shape[0] - 1))
            c = int(np.clip(round(col), 0, dem_data.shape[1] - 1))
            path_elevations.append(dem_data[r, c])

        ax.plot(
            river_path[:, 1],
            river_path[:, 0],
            path_elevations,
            "b-",
            linewidth=3,
            alpha=0.9,
            label="River",
        )

        # Start/end markers
        ax.plot(
            [river_path[0, 1]],
            [river_path[0, 0]],
            [path_elevations[0]],
            "g^",
            markersize=10,
            label="Start",
        )
        ax.plot(
            [river_path[-1, 1]],
            [river_path[-1, 0]],
            [path_elevations[-1]],
            "rv",
            markersize=10,
            label="End",
        )

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Elevation (m)")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.view_init(elev=30, azim=angle)
    ax.legend()

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"  ✓ Saved: {output_path}")

    plt.close(fig)


def generate_preview_images(
    dem_data: np.ndarray,
    river_path: np.ndarray | None = None,
    flow_data: dict | None = None,
    output_dir: Path = None,
):
    """
    Generate all preview images.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "output"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating preview images...")

    # Top-down terrain view
    render_terrain_topdown(
        dem_data,
        river_path,
        output_path=output_dir / "terrain_topdown.png",
        title="Nidelven River - Terrain Overview",
    )

    # 3D perspective
    render_3d_perspective(
        dem_data,
        river_path,
        output_path=output_dir / "terrain_3d.png",
        angle=45.0,
        title="Nidelven River - 3D Perspective",
    )

    # River profile
    if flow_data:
        render_river_profile(flow_data, output_path=output_dir / "river_profile.png")

    print(f"\n  All images saved to: {output_dir}")


if __name__ == "__main__":
    print("Headless Renderer for Nidelven River Adventure MVP")
    print("This module is imported by main.py")
