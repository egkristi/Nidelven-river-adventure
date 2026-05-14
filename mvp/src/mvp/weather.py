"""
Weather data integration for Nidelven River Adventure.

Data sources (all free, CC BY 4.0 / Norwegian Licence for Open Government Data):
- MET Norway Frost API: Historical observations + climate normals
- MET Norway Locationforecast 2.0: Current weather + 9-day forecast
- Closest station to Nidelven (Agder): Nelaug (SN37230) or Arendal (SN37400)

API docs:
- https://frost.met.no/
- https://api.met.no/weatherapi/locationforecast/2.0/documentation
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Nidelven river coordinates (Agder, Norway) - approximate center
NIDELVEN_LAT = 58.55
NIDELVEN_LON = 8.45

# MET Norway Frost API station near Nidelven
# Nelaug: SN37230 (inland), Arendal: SN37400 (coastal)
DEFAULT_STATION = "SN37230"

# Required by MET Norway Terms of Service
USER_AGENT = "NidelvenRiverAdventure/0.1 github.com/egkristi/Nidelven-river-adventure"

# Climate normals for Agder region (based on 1991-2020 normals)
# Monthly averages: temp (°C), precipitation (mm), wind (m/s), cloud cover (oktas 0-8)
CLIMATE_NORMALS = {
    1: {"temp": -2.0, "precip": 70, "wind": 2.5, "clouds": 6, "description": "Cold, overcast"},
    2: {"temp": -1.5, "precip": 55, "wind": 2.5, "clouds": 5, "description": "Cold, clearing"},
    3: {"temp": 1.5, "precip": 60, "wind": 2.8, "clouds": 5, "description": "Early spring"},
    4: {"temp": 6.0, "precip": 50, "wind": 2.5, "clouds": 5, "description": "Spring warming"},
    5: {"temp": 11.0, "precip": 65, "wind": 2.2, "clouds": 5, "description": "Late spring"},
    6: {"temp": 15.0, "precip": 70, "wind": 2.0, "clouds": 5, "description": "Early summer"},
    7: {"temp": 17.0, "precip": 80, "wind": 1.8, "clouds": 5, "description": "Midsummer"},
    8: {"temp": 16.0, "precip": 100, "wind": 1.9, "clouds": 5, "description": "Late summer"},
    9: {"temp": 12.0, "precip": 110, "wind": 2.3, "clouds": 5, "description": "Early autumn"},
    10: {"temp": 7.0, "precip": 120, "wind": 2.8, "clouds": 6, "description": "Autumn"},
    11: {"temp": 3.0, "precip": 100, "wind": 3.0, "clouds": 6, "description": "Late autumn"},
    12: {"temp": -0.5, "precip": 80, "wind": 2.8, "clouds": 6, "description": "Early winter"},
}


def get_seasonal_weather(month: int | None = None) -> dict:
    """
    Get typical weather for the season at Nidelven.

    Args:
        month: Month number (1-12). Defaults to current month.

    Returns:
        Dict with temperature, precipitation, wind, clouds, fog probability, etc.
    """
    if month is None:
        month = datetime.now().month

    normals = CLIMATE_NORMALS[month]

    # Derive game-relevant parameters from climate normals
    temp = normals["temp"]
    precip_mm = normals["precip"]

    # Rain probability based on monthly precipitation
    rain_probability = min(precip_mm / 150.0, 0.8)

    # Fog probability: higher in autumn/early morning, lower in summer
    fog_probability = 0.15 if month in (6, 7, 8) else 0.30 if month in (9, 10, 11) else 0.20

    # Mist over river: higher when warm air meets cold water (spring/autumn)
    river_mist_probability = 0.4 if month in (4, 5, 9, 10) else 0.15

    # Snow if cold enough
    snow_probability = 0.0
    if temp < 1.0:
        snow_probability = min(0.6, (1.0 - temp) * 0.15)

    # Daylight hours (approximate for 58.5°N)
    daylight_hours = {
        1: 6.5,
        2: 8.5,
        3: 11.0,
        4: 14.0,
        5: 16.5,
        6: 18.5,
        7: 18.0,
        8: 15.5,
        9: 12.5,
        10: 10.0,
        11: 7.5,
        12: 6.0,
    }

    sunrise_hour = 12.0 - daylight_hours[month] / 2.0
    sunset_hour = 12.0 + daylight_hours[month] / 2.0

    return {
        "source": "climate_normals_1991_2020",
        "month": month,
        "description": normals["description"],
        "temperature_celsius": temp,
        "wind_speed_ms": normals["wind"],
        "wind_direction_deg": 225,  # Prevailing SW winds in southern Norway
        "cloud_cover_oktas": normals["clouds"],
        "cloud_cover_fraction": normals["clouds"] / 8.0,
        "rain_probability": rain_probability,
        "snow_probability": snow_probability,
        "fog_probability": fog_probability,
        "river_mist_probability": river_mist_probability,
        "precipitation_mm_monthly": precip_mm,
        "sunrise_hour": round(sunrise_hour, 1),
        "sunset_hour": round(sunset_hour, 1),
        "daylight_hours": daylight_hours[month],
    }


def fetch_current_weather(
    lat: float = NIDELVEN_LAT,
    lon: float = NIDELVEN_LON,
) -> dict | None:
    """
    Fetch current weather from MET Norway Locationforecast 2.0.
    Free API, no key required, just User-Agent header.

    Returns:
        Dict with current conditions, or None on failure.
    """
    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    params = {"lat": lat, "lon": lon}
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Extract first timeseries entry (current/next hour)
        timeseries = data.get("properties", {}).get("timeseries", [])
        if not timeseries:
            logger.warning("No timeseries data in response")
            return None

        current = timeseries[0]
        details = current["data"]["instant"]["details"]

        # Next hour summary (rain, symbol)
        next_hour = current["data"].get("next_1_hours", {})
        symbol = next_hour.get("summary", {}).get("symbol_code", "unknown")
        precip_1h = next_hour.get("details", {}).get("precipitation_amount", 0)

        result = {
            "source": "met_locationforecast_2.0",
            "timestamp": current["time"],
            "temperature_celsius": details.get("air_temperature", 10),
            "wind_speed_ms": details.get("wind_speed", 2),
            "wind_direction_deg": details.get("wind_from_direction", 225),
            "cloud_cover_fraction": details.get("cloud_area_fraction", 50) / 100.0,
            "cloud_cover_oktas": round(details.get("cloud_area_fraction", 50) / 12.5),
            "humidity_percent": details.get("relative_humidity", 70),
            "pressure_hpa": details.get("air_pressure_at_sea_level", 1013),
            "precipitation_1h_mm": precip_1h,
            "symbol_code": symbol,
            "is_raining": precip_1h > 0.1,
            "fog_probability": 0.5 if details.get("relative_humidity", 0) > 95 else 0.1,
            "river_mist_probability": (
                0.4
                if details.get("relative_humidity", 0) > 85
                and details.get("air_temperature", 20) < 10
                else 0.1
            ),
        }

        # Derive sunrise/sunset from seasonal data
        month = datetime.fromisoformat(current["time"].replace("Z", "+00:00")).month
        seasonal = get_seasonal_weather(month)
        result["sunrise_hour"] = seasonal["sunrise_hour"]
        result["sunset_hour"] = seasonal["sunset_hour"]

        return result

    except requests.RequestException as e:
        logger.warning(f"Failed to fetch current weather: {e}")
        return None


def fetch_historical_weather(
    station_id: str = DEFAULT_STATION,
    date: str | None = None,
    client_id: str | None = None,
) -> dict | None:
    """
    Fetch historical weather from MET Norway Frost API.
    Requires a client_id (free registration at https://frost.met.no/).

    Args:
        station_id: MET Norway station ID (e.g., SN37230 for Nelaug)
        date: Date string YYYY-MM-DD. Defaults to yesterday.
        client_id: Frost API client ID. If None, returns synthetic data from normals.

    Returns:
        Dict with historical weather observations, or fallback to normals.
    """
    if date is None:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if client_id is None:
        # No API key — use climate normals as fallback
        month = int(date.split("-")[1])
        logger.info(f"No Frost API client_id, using climate normals for month {month}")
        seasonal = get_seasonal_weather(month)
        seasonal["source"] = "climate_normals_fallback"
        seasonal["date"] = date
        return seasonal

    url = "https://frost.met.no/observations/v0.jsonld"
    params = {
        "sources": station_id,
        "referencetime": date,
        "elements": "mean(air_temperature P1D),sum(precipitation_amount P1D),"
        "mean(wind_speed P1D),mean(cloud_area_fraction P1D)",
    }

    try:
        resp = requests.get(url, params=params, auth=(client_id, ""), timeout=10)
        resp.raise_for_status()
        data = resp.json()

        observations = {}
        for item in data.get("data", []):
            for obs in item.get("observations", []):
                element = obs.get("elementId", "")
                value = obs.get("value")
                if "air_temperature" in element:
                    observations["temperature_celsius"] = value
                elif "precipitation" in element:
                    observations["precipitation_mm"] = value
                elif "wind_speed" in element:
                    observations["wind_speed_ms"] = value
                elif "cloud_area_fraction" in element:
                    observations["cloud_cover_fraction"] = value / 100.0 if value else 0.5

        if not observations:
            logger.warning(f"No observations found for {station_id} on {date}")
            return None

        observations["source"] = "frost_api"
        observations["station_id"] = station_id
        observations["date"] = date
        return observations

    except requests.RequestException as e:
        logger.warning(f"Failed to fetch historical weather: {e}")
        return None


def build_weather_data(
    month: int | None = None,
    fetch_live: bool = True,
    frost_client_id: str | None = None,
) -> dict:
    """
    Build complete weather dataset for Unity consumption.

    Returns a dict with three layers:
    - seasonal: Typical conditions for the month
    - current: Live weather (if fetch_live=True and API reachable)
    - historical: Yesterday's observations (if Frost API key available)
    """
    seasonal = get_seasonal_weather(month)

    current = None
    if fetch_live:
        current = fetch_current_weather()

    historical = fetch_historical_weather(client_id=frost_client_id)

    # Determine which data to use as "active" weather in game
    # Priority: current > historical > seasonal
    active = current if current else (historical if historical else seasonal)

    return {
        "generated_at": datetime.now().isoformat(),
        "location": {"lat": NIDELVEN_LAT, "lon": NIDELVEN_LON, "name": "Nidelven, Agder"},
        "seasonal": seasonal,
        "current": current,
        "historical": historical,
        "active": active,
        "unity_params": _to_unity_params(active),
    }


def _to_unity_params(weather: dict) -> dict:
    """Convert weather data to Unity-friendly parameters."""
    temp = weather.get("temperature_celsius", 10)
    wind = weather.get("wind_speed_ms", 2)
    wind_dir = weather.get("wind_direction_deg", 225)
    clouds = weather.get("cloud_cover_fraction", 0.5)
    rain_prob = weather.get("rain_probability", 0)
    is_raining = weather.get("is_raining", rain_prob > 0.5)
    fog_prob = weather.get("fog_probability", 0.1)
    mist_prob = weather.get("river_mist_probability", 0.1)
    sunrise = weather.get("sunrise_hour", 6.0)
    sunset = weather.get("sunset_hour", 18.0)

    # Map to Unity shader/system parameters
    return {
        # DayNightCycle
        "sunrise_hour": sunrise,
        "sunset_hour": sunset,
        # Fog
        "fog_density": 0.005 + fog_prob * 0.03 + clouds * 0.01,
        "fog_color_r": 0.7 + (1 - clouds) * 0.2,
        "fog_color_g": 0.75 + (1 - clouds) * 0.15,
        "fog_color_b": 0.8 + (1 - clouds) * 0.1,
        # Rain
        "rain_intensity": 1.0 if is_raining else 0.0,
        "rain_particle_rate": 500 if is_raining else 0,
        # Wind (affects trees, water, particles)
        "wind_speed": wind,
        "wind_direction_x": -_sin_deg(wind_dir),
        "wind_direction_z": -_cos_deg(wind_dir),
        # Water
        "water_wave_height": 0.1 + wind * 0.05,
        "water_wave_speed": 1.0 + wind * 0.3,
        "river_mist_enabled": mist_prob > 0.25,
        "river_mist_density": mist_prob,
        # Sky
        "cloud_cover": clouds,
        "sun_intensity_multiplier": max(0.2, 1.0 - clouds * 0.7),
        "ambient_intensity_multiplier": 0.6 + clouds * 0.4,
        # Temperature effects
        "temperature_celsius": temp,
        "snow_on_ground": temp < 0,
        "breath_visible": temp < 5,
    }


def _sin_deg(deg: float) -> float:
    """Sin of angle in degrees."""
    import math

    return math.sin(math.radians(deg))


def _cos_deg(deg: float) -> float:
    """Cos of angle in degrees."""
    import math

    return math.cos(math.radians(deg))


def export_weather_json(output_path: Path, fetch_live: bool = True, month: int | None = None):
    """
    Export weather data as JSON for Unity to load from StreamingAssets.

    Args:
        output_path: Path to write weather_data.json
        fetch_live: Whether to attempt live API fetch
        month: Override month for seasonal data
    """
    data = build_weather_data(month=month, fetch_live=fetch_live)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Weather data exported: {output_path}")
    source = data["active"].get("source", "unknown")
    print(f"  Weather data: {output_path}")
    print(f"  Source: {source}")
    print(f"  Temperature: {data['active'].get('temperature_celsius', '?')}°C")
    print(f"  Wind: {data['active'].get('wind_speed_ms', '?')} m/s")
    print(f"  Clouds: {data['active'].get('cloud_cover_fraction', '?')}")


if __name__ == "__main__":
    import sys

    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output/weather_data.json")
    fetch_live = "--offline" not in sys.argv
    export_weather_json(output, fetch_live=fetch_live)
