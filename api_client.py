"""
API Client
──────────
Integrates external REST APIs:
  - OpenWeatherMap (live weather)
  - Open-Meteo (free fallback weather, no key needed)
  - REST Countries (country data)
  - MockAPI (internal demo endpoint)
  - NewsAPI (top headlines — optional)
"""

import os
import json
import httpx
from typing import Optional
from datetime import datetime


class APIClient:
    """
    Unified API gateway for DocuBot external data sources.

    Supports:
    • Weather data (Open-Meteo, no API key needed)
    • Country information (REST Countries)
    • Currency exchange rates (exchangerate-api)
    • Placeholder internal API calls
    """

    def __init__(self):
        self.weather_key = os.getenv("OPENWEATHER_API_KEY")
        self.news_key = os.getenv("NEWS_API_KEY")
        self.timeout = 8.0

    # ──────────────────────────────────────────────────────────────────────────
    # Weather
    # ──────────────────────────────────────────────────────────────────────────

    def get_weather(self, city: str) -> dict:
        """
        Get current weather for a city.
        Uses OpenWeatherMap if key is set, otherwise Open-Meteo (free).
        """
        if self.weather_key:
            return self._owm_weather(city)
        return self._open_meteo_weather(city)

    def _owm_weather(self, city: str) -> dict:
        url = "https://api.openweathermap.org/data/2.5/weather"
        try:
            r = httpx.get(
                url,
                params={"q": city, "appid": self.weather_key, "units": "metric"},
                timeout=self.timeout,
            )
            r.raise_for_status()
            d = r.json()
            return {
                "city": d["name"],
                "country": d["sys"]["country"],
                "temp_c": d["main"]["temp"],
                "feels_like": d["main"]["feels_like"],
                "humidity": d["main"]["humidity"],
                "condition": d["weather"][0]["description"],
                "wind_kph": round(d["wind"]["speed"] * 3.6, 1),
                "source": "OpenWeatherMap",
            }
        except Exception as e:
            return {"error": str(e)}

    def _open_meteo_weather(self, city: str) -> dict:
        """Free tier weather using Open-Meteo + geocoding."""
        try:
            # Step 1: Geocode
            geo_r = httpx.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"},
                timeout=self.timeout,
            )
            geo_r.raise_for_status()
            geo = geo_r.json()
            if not geo.get("results"):
                return {"error": f"City '{city}' not found"}

            loc = geo["results"][0]
            lat, lon = loc["latitude"], loc["longitude"]

            # Step 2: Weather
            wx_r = httpx.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                    "wind_speed_unit": "kmh",
                },
                timeout=self.timeout,
            )
            wx_r.raise_for_status()
            wx = wx_r.json()["current"]

            return {
                "city": loc["name"],
                "country": loc.get("country", ""),
                "temp_c": wx["temperature_2m"],
                "humidity": wx["relative_humidity_2m"],
                "wind_kph": wx["wind_speed_10m"],
                "condition": self._wmo_code_to_text(wx["weather_code"]),
                "source": "Open-Meteo (free)",
            }
        except Exception as e:
            return {"error": str(e)}

    def _wmo_code_to_text(self, code: int) -> str:
        codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 61: "Slight rain",
            63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow", 80: "Rain showers",
            95: "Thunderstorm", 99: "Thunderstorm with hail",
        }
        return codes.get(code, f"Code {code}")

    # ──────────────────────────────────────────────────────────────────────────
    # Country Info
    # ──────────────────────────────────────────────────────────────────────────

    def get_country_info(self, country_name: str) -> dict:
        """Fetch country details from REST Countries API (no key needed)."""
        try:
            r = httpx.get(
                f"https://restcountries.com/v3.1/name/{country_name}",
                params={"fields": "name,capital,population,currencies,languages,region,flag"},
                timeout=self.timeout,
            )
            r.raise_for_status()
            c = r.json()[0]
            currencies = list(c.get("currencies", {}).keys())
            languages = list(c.get("languages", {}).values())
            return {
                "name": c["name"]["common"],
                "official_name": c["name"]["official"],
                "capital": c.get("capital", ["Unknown"])[0],
                "population": c.get("population", 0),
                "region": c.get("region", ""),
                "currencies": currencies,
                "languages": languages,
                "flag": c.get("flag", ""),
                "source": "REST Countries API",
            }
        except Exception as e:
            return {"error": str(e)}

    # ──────────────────────────────────────────────────────────────────────────
    # Exchange Rates
    # ──────────────────────────────────────────────────────────────────────────

    def get_exchange_rate(self, base: str = "USD", target: str = "EUR") -> dict:
        """Get live exchange rates (no key needed)."""
        try:
            r = httpx.get(
                f"https://open.er-api.com/v6/latest/{base.upper()}",
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            rate = data["rates"].get(target.upper())
            return {
                "base": base.upper(),
                "target": target.upper(),
                "rate": rate,
                "updated": data.get("time_last_update_utc", ""),
                "source": "ExchangeRate-API",
            }
        except Exception as e:
            return {"error": str(e)}

    # ──────────────────────────────────────────────────────────────────────────
    # Top-Level Method for Agent
    # ──────────────────────────────────────────────────────────────────────────

    def dispatch(self, api_type: str, params: dict) -> str:
        """
        Single entry point for the LangChain agent.
        api_type: 'weather' | 'country' | 'exchange'
        """
        if api_type == "weather":
            result = self.get_weather(params.get("city", "London"))
        elif api_type == "country":
            result = self.get_country_info(params.get("country", "India"))
        elif api_type == "exchange":
            result = self.get_exchange_rate(
                params.get("base", "USD"), params.get("target", "EUR")
            )
        else:
            result = {"error": f"Unknown API type: {api_type}"}

        return json.dumps(result, indent=2)

    def get_capabilities_description(self) -> str:
        return (
            "Available external APIs: "
            "(1) Weather: current weather for any city "
            "(2) Country Info: details about any country "
            "(3) Exchange Rates: live currency conversion between any pair"
        )
