"""
collectors/weather.py
Realtime weather collector.

Strategy:
  - No weather seed data.
  - Fetch Open-Meteo first; fall back to MET Norway if Open-Meteo is unavailable.
  - Store raw response in weather_cache (TTL 6h) and per-day rows in
    weather_daily_forecasts for Price Calendar joins.
"""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.helpers import safe_get, log_response
from db.connection import get_seeded_destinations, save_weather_forecast

log = logging.getLogger(__name__)

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
MET_NORWAY_BASE = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
MET_NORWAY_HEADERS = {
    "User-Agent": "TravelBuddyAI/1.0 contact:dev@travelbuddy.local",
}


def met_symbol_to_weather_code(symbol_code: str | None) -> int | None:
    """Map MET Norway symbol names to approximate WMO weather codes."""
    if not symbol_code:
        return None
    symbol = symbol_code.lower()
    if "thunder" in symbol:
        return 95
    if "snow" in symbol or "sleet" in symbol:
        return 71
    if "heavyrain" in symbol:
        return 65
    if "rainshowers" in symbol:
        return 80
    if "lightrain" in symbol:
        return 61
    if "rain" in symbol:
        return 63
    if "fog" in symbol:
        return 45
    if "cloudy" in symbol:
        if "partly" in symbol:
            return 2
        return 3
    if "fair" in symbol:
        return 1
    if "clearsky" in symbol:
        return 0
    return None


def travel_score(row: dict) -> int:
    """Simple deterministic score for 'ngay tot nhat' recommendation."""
    score = 100

    rain_mm = row.get("precipitation_sum_mm") or 0
    rain_prob = row.get("precipitation_probability_max") or 0
    wind = row.get("wind_speed_max_kmh") or 0
    tmax = row.get("temp_max_c")
    tmin = row.get("temp_min_c")

    if rain_mm >= 20:
        score -= 45
    elif rain_mm >= 10:
        score -= 30
    elif rain_mm >= 3:
        score -= 15

    if rain_prob >= 80:
        score -= 20
    elif rain_prob >= 60:
        score -= 12
    elif rain_prob >= 40:
        score -= 6

    if wind >= 45:
        score -= 20
    elif wind >= 30:
        score -= 10

    if tmax is not None and tmax >= 36:
        score -= 12
    if tmin is not None and tmin <= 10:
        score -= 10

    return max(0, min(100, score))


class WeatherCollector:
    """Fetch weather forecast and persist canonical weather cache rows."""

    def fetch_open_meteo(self, lat: float, lng: float, timezone: str = "Asia/Ho_Chi_Minh") -> dict | None:
        r = safe_get(
            OPEN_METEO_BASE,
            params={
                "latitude": lat,
                "longitude": lng,
                "daily": ",".join(
                    [
                        "weather_code",
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "precipitation_sum",
                        "precipitation_probability_max",
                        "wind_speed_10m_max",
                    ]
                ),
                "current": "temperature_2m,weather_code,wind_speed_10m,is_day",
                "timezone": timezone,
                "forecast_days": 16,
            },
            timeout=8,
            retries=1,
        )
        if not r:
            return None
        log_response("Open-Meteo", r, ["current", "daily"])
        return r.json()

    def fetch_met_norway(self, lat: float, lng: float) -> dict | None:
        r = safe_get(
            MET_NORWAY_BASE,
            params={
                "lat": round(lat, 6),
                "lon": round(lng, 6),
            },
            headers=MET_NORWAY_HEADERS,
            timeout=15,
            retries=2,
        )
        if not r:
            return None
        raw = r.json()
        meta = raw.get("properties", {}).get("meta", {})
        timeseries_count = len(raw.get("properties", {}).get("timeseries", []))
        log.info(
            "[MET Norway] %s timeseries points, updated_at=%s",
            timeseries_count,
            meta.get("updated_at"),
        )
        return raw

    def fetch_forecast(self, lat: float, lng: float, timezone: str = "Asia/Ho_Chi_Minh") -> tuple[str, dict] | None:
        raw = self.fetch_open_meteo(lat, lng, timezone)
        if raw:
            return "open-meteo", raw

        log.warning("Open-Meteo unavailable; trying MET Norway fallback")
        raw = self.fetch_met_norway(lat, lng)
        if raw:
            return "met-norway", raw
        return None

    def parse_open_meteo_daily_rows(self, raw: dict) -> list[dict]:
        daily = raw.get("daily", {})
        dates = daily.get("time", [])
        codes = daily.get("weather_code", daily.get("weathercode", []))
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        precip_prob = daily.get("precipitation_probability_max", [])
        wind = daily.get("wind_speed_10m_max", daily.get("windspeed_10m_max", []))

        rows: list[dict] = []
        for i, day in enumerate(dates):
            row = {
                "date": day,
                "weather_code": codes[i] if i < len(codes) else None,
                "temp_max_c": temp_max[i] if i < len(temp_max) else None,
                "temp_min_c": temp_min[i] if i < len(temp_min) else None,
                "precipitation_sum_mm": precip[i] if i < len(precip) else None,
                "precipitation_probability_max": precip_prob[i] if i < len(precip_prob) else None,
                "wind_speed_max_kmh": wind[i] if i < len(wind) else None,
            }
            row["travel_score"] = travel_score(row)
            rows.append(row)
        return rows

    def parse_met_norway_daily_rows(self, raw: dict, timezone: str = "Asia/Ho_Chi_Minh") -> list[dict]:
        tz = ZoneInfo(timezone)
        days: dict[str, dict] = {}

        for item in raw.get("properties", {}).get("timeseries", []):
            time_value = item.get("time")
            if not time_value:
                continue

            dt = datetime.fromisoformat(time_value.replace("Z", "+00:00")).astimezone(tz)
            day = dt.date().isoformat()
            data = item.get("data", {})
            instant = data.get("instant", {}).get("details", {})
            temp = instant.get("air_temperature")
            wind_ms = instant.get("wind_speed")
            next_1h = data.get("next_1_hours", {})
            next_6h = data.get("next_6_hours", {})
            next_12h = data.get("next_12_hours", {})

            bucket = days.setdefault(
                day,
                {
                    "date": day,
                    "weather_code": None,
                    "temp_max_c": None,
                    "temp_min_c": None,
                    "precipitation_sum_mm": 0.0,
                    "precipitation_probability_max": None,
                    "wind_speed_max_kmh": None,
                },
            )

            if temp is not None:
                bucket["temp_max_c"] = temp if bucket["temp_max_c"] is None else max(bucket["temp_max_c"], temp)
                bucket["temp_min_c"] = temp if bucket["temp_min_c"] is None else min(bucket["temp_min_c"], temp)
            if wind_ms is not None:
                wind_kmh = round(float(wind_ms) * 3.6, 2)
                current_wind = bucket["wind_speed_max_kmh"]
                bucket["wind_speed_max_kmh"] = wind_kmh if current_wind is None else max(current_wind, wind_kmh)

            precip_details = next_1h.get("details") or {}
            if "precipitation_amount" in precip_details:
                bucket["precipitation_sum_mm"] += float(precip_details.get("precipitation_amount") or 0)

            summary = next_1h.get("summary") or next_6h.get("summary") or next_12h.get("summary") or {}
            code = met_symbol_to_weather_code(summary.get("symbol_code"))
            if bucket["weather_code"] is None and code is not None:
                bucket["weather_code"] = code

        rows = list(days.values())[:16]
        for row in rows:
            row["precipitation_sum_mm"] = round(row["precipitation_sum_mm"], 2)
            row["travel_score"] = travel_score(row)
        return rows

    def parse_daily_rows(self, source: str, raw: dict, timezone: str = "Asia/Ho_Chi_Minh") -> list[dict]:
        if source == "met-norway":
            return self.parse_met_norway_daily_rows(raw, timezone)
        return self.parse_open_meteo_daily_rows(raw)

    def run(self, conn):
        log.info("Weather collector started")
        destinations = get_seeded_destinations(conn)
        saved = 0

        for dest in destinations:
            result = self.fetch_forecast(
                float(dest["lat"]),
                float(dest["lng"]),
                dest.get("timezone") or "Asia/Ho_Chi_Minh",
            )
            if not result:
                log.warning("Weather skipped: %s", dest["slug"])
                continue

            source, raw = result
            rows = self.parse_daily_rows(source, raw, dest.get("timezone") or "Asia/Ho_Chi_Minh")
            save_weather_forecast(conn, dest, raw, rows, ttl_hours=6, source=source)
            saved += 1
            current = raw.get("current", {})
            if source == "met-norway":
                timeseries = raw.get("properties", {}).get("timeseries", [])
                details = safe_get_nested(timeseries, 0, "data", "instant", "details") or {}
                current = {
                    "temperature_2m": details.get("air_temperature"),
                    "weather_code": rows[0].get("weather_code") if rows else None,
                }
            log.info(
                "Weather saved: %s via %s (%s C, code=%s, %s days)",
                dest["slug"],
                source,
                current.get("temperature_2m"),
                current.get("weather_code"),
                len(rows),
            )

        log.info("Weather collector finished: %s destinations", saved)


def safe_get_nested(value, *keys):
    for key in keys:
        if isinstance(key, int):
            if not isinstance(value, list) or len(value) <= key:
                return None
            value = value[key]
            continue
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value
