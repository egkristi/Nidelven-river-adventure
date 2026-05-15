"""
NVE HydAPI client for water discharge and level data.

Fetches real-time and historical hydrological observations from NVE's
HydAPI REST service. Provides accurate river flow speed and water level
for Nidelva stations in Agder.

API: https://hydapi.nve.no/
License: NLOD (free for any use with attribution)
Documentation: https://hydapi.nve.no/UserDocumentation/

Key parameters:
- 1001: Discharge (m³/s) — water flow volume
- 1000: Water stage (m) — water level above reference
- 1003: Water temperature (°C)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# NVE HydAPI base URL
HYDAPI_BASE_URL = "https://hydapi.nve.no/api/v1"

# Required user agent for NVE API Terms of Service
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Nidelva stations in Agder
# These are gauging stations on or near Nidelva
NIDELVA_STATIONS = {
    "Rygenefoss": "2.145.0",  # Main station on Nidelva
    "Flaksvann": "2.32.0",  # Upstream lake
    "Bøylefoss": "2.11.0",  # Upstream Nidelva
}

# Default station for river flow data
DEFAULT_STATION_ID = "2.145.0"  # Rygenefoss

# HydAPI parameter IDs
PARAM_DISCHARGE = 1001  # m³/s
PARAM_WATER_STAGE = 1000  # m (water level)
PARAM_WATER_TEMP = 1003  # °C

# Typical flow characteristics for Nidelva (based on historical data)
# Used as fallback when API is unavailable
NIDELVA_FLOW_NORMALS = {
    1: {"discharge_m3s": 25.0, "stage_m": 1.2, "temp_c": 1.0},
    2: {"discharge_m3s": 20.0, "stage_m": 1.0, "temp_c": 0.5},
    3: {"discharge_m3s": 30.0, "stage_m": 1.3, "temp_c": 2.0},
    4: {"discharge_m3s": 80.0, "stage_m": 2.5, "temp_c": 5.0},  # Spring flood
    5: {"discharge_m3s": 100.0, "stage_m": 3.0, "temp_c": 8.0},  # Peak snowmelt
    6: {"discharge_m3s": 60.0, "stage_m": 2.0, "temp_c": 13.0},
    7: {"discharge_m3s": 35.0, "stage_m": 1.5, "temp_c": 17.0},
    8: {"discharge_m3s": 30.0, "stage_m": 1.3, "temp_c": 16.0},
    9: {"discharge_m3s": 45.0, "stage_m": 1.8, "temp_c": 12.0},  # Autumn rain
    10: {"discharge_m3s": 60.0, "stage_m": 2.2, "temp_c": 8.0},  # Autumn flood
    11: {"discharge_m3s": 50.0, "stage_m": 1.9, "temp_c": 4.0},
    12: {"discharge_m3s": 35.0, "stage_m": 1.4, "temp_c": 2.0},
}


def get_seasonal_flow(month: int | None = None) -> dict:
    """
    Get typical flow for the season at Nidelva (offline fallback).

    Args:
        month: Month number (1-12). Defaults to current month.

    Returns:
        Dict with discharge_m3s, stage_m, temp_c, flow_speed_ms, river_width_m
    """
    if month is None:
        month = datetime.now().month

    month = max(1, min(12, month))
    normals = NIDELVA_FLOW_NORMALS[month]

    # Estimate flow speed from discharge using Manning's equation approximation
    # For Nidelva: typical cross-section ~40m wide, 1.5m avg depth
    # v = Q / A, where A = width * depth
    discharge = normals["discharge_m3s"]
    avg_depth = normals["stage_m"] * 0.7  # stage is from datum, avg depth ~70% of stage
    river_width = 30.0 + discharge * 0.15  # Width increases with flow
    cross_section = river_width * max(avg_depth, 0.3)
    flow_speed = discharge / cross_section if cross_section > 0 else 0.5

    return {
        "discharge_m3s": discharge,
        "stage_m": normals["stage_m"],
        "temp_c": normals["temp_c"],
        "flow_speed_ms": round(flow_speed, 2),
        "river_width_m": round(river_width, 1),
        "month": month,
        "source": "climate_normals",
    }


def fetch_observations(
    station_id: str = DEFAULT_STATION_ID,
    parameter: int = PARAM_DISCHARGE,
    reference_time: str | None = None,
    api_key: str | None = None,
    timeout: int = 15,
) -> list[dict[str, Any]]:
    """
    Fetch observations from NVE HydAPI.

    Args:
        station_id: NVE station ID (e.g. "2.145.0" for Rygenefoss)
        parameter: Parameter ID (1001=discharge, 1000=stage, 1003=temp)
        reference_time: Time range string (e.g. "P1D/now" for last 24h)
                       If None, defaults to last 7 days.
        api_key: NVE HydAPI key (optional, rate-limited without)
        timeout: Request timeout in seconds

    Returns:
        List of observation dicts with 'time' and 'value' keys

    Raises:
        requests.RequestException: On network errors
    """
    if reference_time is None:
        # Default: last 7 days to now
        reference_time = "P7D/now"

    url = f"{HYDAPI_BASE_URL}/Observations"
    params = {
        "StationId": station_id,
        "Parameter": str(parameter),
        "ReferenceTime": reference_time,
        "ResolutionTime": "PT1H",  # Hourly resolution
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    if api_key:
        headers["X-API-Key"] = api_key

    logger.info(f"Fetching HydAPI: station={station_id}, param={parameter}")

    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()

    data = response.json()

    # Parse response — HydAPI returns nested structure
    observations = []
    if "data" in data:
        for series in data["data"]:
            if "observations" in series:
                for obs in series["observations"]:
                    observations.append(
                        {
                            "time": obs.get("time", ""),
                            "value": obs.get("value"),
                            "quality": obs.get("quality", 0),
                        }
                    )

    logger.info(f"  Received {len(observations)} observations")
    return observations


def fetch_current_flow(
    station_id: str = DEFAULT_STATION_ID,
    api_key: str | None = None,
    timeout: int = 15,
) -> dict:
    """
    Fetch current river flow (discharge + stage) from NVE HydAPI.

    Args:
        station_id: NVE station ID
        api_key: Optional HydAPI key
        timeout: Request timeout

    Returns:
        Dict with discharge_m3s, stage_m, flow_speed_ms, river_width_m,
        timestamp, source
    """
    try:
        # Fetch last 24 hours of discharge
        discharge_obs = fetch_observations(
            station_id=station_id,
            parameter=PARAM_DISCHARGE,
            reference_time="P1D/now",
            api_key=api_key,
            timeout=timeout,
        )

        # Fetch last 24 hours of water stage
        stage_obs = fetch_observations(
            station_id=station_id,
            parameter=PARAM_WATER_STAGE,
            reference_time="P1D/now",
            api_key=api_key,
            timeout=timeout,
        )

        # Use most recent valid observation
        discharge = _latest_value(discharge_obs)
        stage = _latest_value(stage_obs)

        if discharge is None:
            logger.warning("No discharge data, using seasonal fallback")
            return get_seasonal_flow()

        # Calculate derived values
        if stage is None:
            stage = discharge * 0.03 + 0.5  # Rough estimate from discharge

        avg_depth = stage * 0.7
        river_width = 30.0 + discharge * 0.15
        cross_section = river_width * max(avg_depth, 0.3)
        flow_speed = discharge / cross_section if cross_section > 0 else 0.5

        timestamp = _latest_time(discharge_obs)

        return {
            "discharge_m3s": round(discharge, 1),
            "stage_m": round(stage, 2),
            "flow_speed_ms": round(flow_speed, 2),
            "river_width_m": round(river_width, 1),
            "timestamp": timestamp,
            "station_id": station_id,
            "source": "nve_hydapi",
        }

    except (requests.RequestException, KeyError, ValueError) as e:
        logger.warning(f"HydAPI request failed: {e}, using seasonal fallback")
        return get_seasonal_flow()


def fetch_flow_statistics(
    station_id: str = DEFAULT_STATION_ID,
    api_key: str | None = None,
    timeout: int = 15,
) -> dict:
    """
    Fetch flow statistics (mean, min, max) for a station.

    Returns long-term statistics useful for normalizing river physics.
    """
    try:
        # Fetch last 30 days for statistical range
        observations = fetch_observations(
            station_id=station_id,
            parameter=PARAM_DISCHARGE,
            reference_time="P30D/now",
            api_key=api_key,
            timeout=timeout,
        )

        values = [obs["value"] for obs in observations if obs["value"] is not None]
        if not values:
            return _default_statistics()

        return {
            "mean_discharge_m3s": round(sum(values) / len(values), 1),
            "min_discharge_m3s": round(min(values), 1),
            "max_discharge_m3s": round(max(values), 1),
            "observation_count": len(values),
            "station_id": station_id,
            "source": "nve_hydapi",
        }

    except (requests.RequestException, KeyError, ValueError) as e:
        logger.warning(f"HydAPI statistics failed: {e}")
        return _default_statistics()


def build_river_physics_params(flow_data: dict) -> dict:
    """
    Convert hydrological data to Unity river physics parameters.

    Args:
        flow_data: Dict from fetch_current_flow() or get_seasonal_flow()

    Returns:
        Dict with Unity-ready parameters for RiverController
    """
    discharge = flow_data.get("discharge_m3s", 40.0)
    flow_speed = flow_data.get("flow_speed_ms", 1.0)
    river_width = flow_data.get("river_width_m", 35.0)
    stage = flow_data.get("stage_m", 1.5)
    temp = flow_data.get("temp_c", 10.0)

    # Normalize flow speed for game (0.3-3.0 m/s range)
    game_flow_speed = max(0.3, min(3.0, flow_speed))

    # Turbulence increases with discharge
    turbulence = min(1.0, discharge / 150.0)

    # Current strength for boat physics (0-1 normalized)
    current_strength = min(1.0, flow_speed / 2.5)

    # Water clarity decreases with high flow (sediment)
    # Clear at low flow, murky at flood stage
    clarity = max(0.2, 1.0 - (discharge / 200.0))

    return {
        "flow_speed": round(game_flow_speed, 2),
        "river_width": round(river_width, 1),
        "water_depth": round(stage * 0.7, 2),
        "turbulence": round(turbulence, 2),
        "current_strength": round(current_strength, 2),
        "water_clarity": round(clarity, 2),
        "water_temperature": round(temp, 1),
        "discharge_m3s": round(discharge, 1),
        "source": flow_data.get("source", "unknown"),
    }


def export_flow_json(
    output_path: Path,
    fetch_live: bool = True,
    api_key: str | None = None,
    month: int | None = None,
) -> Path:
    """
    Export river flow data as JSON for Unity consumption.

    Args:
        output_path: Directory to write flow_data.json
        fetch_live: If True, try live API first; fallback to seasonal
        api_key: Optional NVE HydAPI key
        month: Month override for seasonal data

    Returns:
        Path to the exported JSON file
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    if fetch_live:
        flow_data = fetch_current_flow(api_key=api_key)
    else:
        flow_data = get_seasonal_flow(month=month)

    physics_params = build_river_physics_params(flow_data)

    result = {
        "flow_data": flow_data,
        "physics_params": physics_params,
        "stations": NIDELVA_STATIONS,
        "generated_at": datetime.now().isoformat(),
    }

    output_file = output_path / "flow_data.json"
    output_file.write_text(json.dumps(result, indent=2, default=str))

    logger.info(f"Flow data exported: {output_file}")
    print(f"  Flow data exported: {output_file}")
    print(f"  Discharge: {flow_data.get('discharge_m3s', '?')} m³/s")
    print(f"  Flow speed: {flow_data.get('flow_speed_ms', '?')} m/s")
    print(f"  Source: {flow_data.get('source', 'unknown')}")

    return output_file


def _latest_value(observations: list[dict]) -> float | None:
    """Get the most recent valid value from observations."""
    for obs in reversed(observations):
        if obs.get("value") is not None:
            return float(obs["value"])
    return None


def _latest_time(observations: list[dict]) -> str | None:
    """Get the timestamp of the most recent observation."""
    for obs in reversed(observations):
        if obs.get("time"):
            return obs["time"]
    return None


def _default_statistics() -> dict:
    """Return default statistics based on historical Nidelva data."""
    return {
        "mean_discharge_m3s": 45.0,
        "min_discharge_m3s": 8.0,
        "max_discharge_m3s": 250.0,
        "observation_count": 0,
        "station_id": DEFAULT_STATION_ID,
        "source": "historical_estimate",
    }
