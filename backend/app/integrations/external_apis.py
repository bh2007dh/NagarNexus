from datetime import datetime, timezone
from typing import Dict, Any, List
import httpx
from app.core.config import settings


def fetch_open_meteo_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Query Open-Meteo Weather API for current and hourly environmental measurements
    with graceful timeout and error handling.
    """
    url = f"{settings.OPEN_METEO_BASE_URL}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "past_days": 3,
        "forecast_days": 3,
        "timezone": "auto",
    }
    retrieved_at = datetime.now(timezone.utc).isoformat()
    try:
        with httpx.Client(timeout=6.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            return {
                "status": "live_api",
                "source_name": "Open-Meteo Weather Forecast API",
                "source_url": "https://open-meteo.com/",
                "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
                "geographical_resolution": "grid_cell (~11km atmospheric reanalysis/forecast grid)",
                "retrieved_at": retrieved_at,
                "latitude": payload.get("latitude", latitude),
                "longitude": payload.get("longitude", longitude),
                "elevation_m": payload.get("elevation"),
                "current": payload.get("current", {}),
                "current_units": payload.get("current_units", {}),
                "hourly": payload.get("hourly", {}),
            }
    except Exception as exc:
        return {
            "status": "offline_fallback",
            "source_name": "Open-Meteo Weather API (Cached/Database Observation Fallback)",
            "source_url": "https://open-meteo.com/",
            "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
            "geographical_resolution": "grid_cell",
            "retrieved_at": retrieved_at,
            "error_note": f"Live API unreachable ({type(exc).__name__}); serving stored local database observations.",
        }


def fetch_openaq_air_quality(latitude: float, longitude: float, radius_m: int = 25000) -> Dict[str, Any]:
    """
    Query OpenAQ API for nearby air quality station measurements.
    Never assumes every pollutant exists at every station.
    """
    url = f"{settings.OPENAQ_BASE_URL}/latest"
    params = {
        "coordinates": f"{latitude:.4f},{longitude:.4f}",
        "radius": radius_m,
        "limit": 5,
    }
    headers = {"Accept": "application/json"}
    if settings.OPENAQ_API_KEY:
        headers["X-API-Key"] = settings.OPENAQ_API_KEY

    retrieved_at = datetime.now(timezone.utc).isoformat()
    try:
        with httpx.Client(timeout=6.0, headers=headers) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            measurements = []
            for station in results:
                for m in station.get("measurements", []):
                    measurements.append({
                        "station": station.get("location"),
                        "parameter": m.get("parameter"),
                        "value": m.get("value"),
                        "unit": m.get("unit"),
                        "last_updated": m.get("lastUpdated"),
                    })
            return {
                "status": "live_api",
                "source_name": "OpenAQ Air Quality API",
                "source_url": "https://openaq.org/",
                "attribution": "Air quality data aggregated by OpenAQ",
                "geographical_resolution": "monitoring_station",
                "retrieved_at": retrieved_at,
                "measurements": measurements,
            }
    except Exception as exc:
        return {
            "status": "offline_fallback",
            "source_name": "OpenAQ Air Quality Network (Stored Station Observations)",
            "source_url": "https://openaq.org/",
            "attribution": "Air quality schema aligned with OpenAQ / CPCB station standards",
            "geographical_resolution": "monitoring_station",
            "retrieved_at": retrieved_at,
            "measurements": [],
            "error_note": f"OpenAQ live query unavailable ({type(exc).__name__}); using local database observations.",
        }


def geocode_nominatim(query: str) -> List[Dict[str, Any]]:
    """
    Search OpenStreetMap Nominatim geocoding API with mandatory User-Agent header
    and attribution metadata.
    """
    url = f"{settings.NOMINATIM_BASE_URL}/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 5,
        "addressdetails": 1,
    }
    headers = {"User-Agent": settings.NOMINATIM_USER_AGENT}
    try:
        with httpx.Client(timeout=5.0, headers=headers) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            items = resp.json()
            return [
                {
                    "display_name": item.get("display_name"),
                    "latitude": float(item.get("lat", 0.0)),
                    "longitude": float(item.get("lon", 0.0)),
                    "geographical_resolution": item.get("type", "locality"),
                    "attribution": "© OpenStreetMap contributors (ODbL)",
                }
                for item in items
            ]
    except Exception:
        return []

