# UV Setup for Nidelven MVP

This project uses [uv](https://docs.astral.sh/uv/) for Python package management.

## Quick Start

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates virtual environment)
uv sync

# Run the MVP
uv run python -m mvp.main

# Or use the script entry point
uv run nidelven
```

## Available Commands

```bash
# Run with sample data
uv run python -m mvp.main --sample

# Try to download real DEM
uv run python -m mvp.main --download

# Run the minimal version (no deps)
uv run python -m mvp.minimal

# Format code
uv run black mvp/

# Lint code
uv run ruff check mvp/

# Type check
uv run mypy mvp/
```

## Dependencies

Managed in `pyproject.toml`:

- **numpy**: Array operations
- **rasterio**: GeoTIFF DEM reading
- **scipy**: Interpolation and mesh processing
- **matplotlib**: 2D/3D visualization
- **pillow**: Image export
- **moderngl**: OpenGL rendering (optional)
- **PyGLM**: GLM math library for Python
- **requests**: HTTP for DEM downloads

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Build package
uv build
```
