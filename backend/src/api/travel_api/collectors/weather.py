"""
collectors/weather.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API:     Open-Meteo  (https://open-meteo.com)
Data:    Thời tiết hiện tại + 7 ngày tới tại các điểm đến
Key:     KHÔNG CẦN — hoàn toàn miễn phí
Docs:    https://open-meteo.com/en/docs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dùng để:
  - Hiển thị thời tiết trong Trip Builder
  - Cảnh báo "nên đi tháng nào" cho Price Intelligence
  - Dữ liệu thực tế 100% realtime
"""

import json, logging
from datetime import datetime
from utils.helpers import safe_get, log_response
from db.connection import get_dest_id

log = logging.getLogger(__name__)

BASE = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Trời quang", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Sương mù", 48: "Icy fog",
    51: "Mưa phùn nhẹ", 53: "Mưa phùn", 55: "Mưa phùn nặng",
    61: "Mưa nhẹ", 63: "Mưa vừa", 65: "Mưa to",
    71: "Tuyết nhẹ", 73: "Tuyết vừa", 75: "Tuyết to",
    80: "Mưa rào nhẹ", 81: "Mưa rào", 82: "Mưa rào nặng",
    95: "Giông bão", 99: "Giông có mưa đá",
}

# Điểm đến có tọa độ (lấy từ destinations sau khi OpenTripMap đã insert)
CITY_COORDS = {
    "da-nang":   (16.0544, 108.2022),
    "hoi-an":    (15.8801, 108.3380),
    "ha-long":   (20.9101, 107.1839),
    "da-lat":    (11.9404, 108.4583),
    "phu-quoc":  (10.2897, 103.9840),
    "nha-trang": (12.2388, 109.1967),
    "sapa":      (22.3364, 103.8438),
    "bangkok":   (13.7563, 100.5018),
    "tokyo":     (35.6762, 139.6503),
    "singapore": (1.3521,  103.8198),
}


class WeatherCollector:
    """
    Gọi Open-Meteo API lấy thời tiết 7 ngày tới.
    Lưu vào bảng riêng hoặc update trường weather_cache trong destinations.
    """

    def fetch_forecast(self, lat: float, lng: float) -> dict | None:
        """
        GET https://api.open-meteo.com/v1/forecast
        Params:
          latitude, longitude: tọa độ
          daily: weathercode, temperature_2m_max/min, precipitation_sum, windspeed_10m_max
          timezone: Asia/Bangkok (UTC+7 cho VN)
          forecast_days: 7
        """
        r = safe_get(BASE, params={
            "latitude":            lat,
            "longitude":           lng,
            "daily":               "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "current_weather":     "true",
            "timezone":            "Asia/Bangkok",
            "forecast_days":       7,
        })
        if not r:
            return None
        log_response("Open-Meteo", r, ["current_weather", "daily"])
        return r.json()

    def parse_forecast(self, raw: dict, slug: str) -> dict:
        """
        Chuyển raw JSON → dict gọn gàng để lưu/hiển thị.
        """
        current = raw.get("current_weather", {})
        daily   = raw.get("daily", {})

        # Dự báo 7 ngày
        days = []
        dates       = daily.get("time", [])
        codes       = daily.get("weathercode", [])
        temp_max    = daily.get("temperature_2m_max", [])
        temp_min    = daily.get("temperature_2m_min", [])
        precip      = daily.get("precipitation_sum", [])
        wind        = daily.get("windspeed_10m_max", [])

        for i in range(len(dates)):
            days.append({
                "date":        dates[i],
                "condition":   WMO_CODES.get(codes[i] if i < len(codes) else 0, "N/A"),
                "temp_max_c":  temp_max[i] if i < len(temp_max) else None,
                "temp_min_c":  temp_min[i] if i < len(temp_min) else None,
                "rain_mm":     precip[i]   if i < len(precip)   else None,
                "wind_kmh":    wind[i]     if i < len(wind)      else None,
            })

        return {
            "slug":       slug,
            "updated_at": datetime.now().isoformat(),
            "source":     "Open-Meteo API (open-meteo.com)",
            "current": {
                "temp_c":      current.get("temperature"),
                "windspeed":   current.get("windspeed"),
                "condition":   WMO_CODES.get(current.get("weathercode", 0), "N/A"),
                "is_day":      bool(current.get("is_day", 1)),
            },
            "forecast_7days": days,
        }

    def save_to_db(self, conn, weather: dict):
        """
        Lưu vào bảng weather_cache (tạo thêm nếu chưa có)
        hoặc update JSONB field trong destinations.
        """
        cur = conn.cursor()

        # Tạo bảng nếu chưa có
        cur.execute("""
            CREATE TABLE IF NOT EXISTS weather_cache (
                destination_slug VARCHAR(120) PRIMARY KEY,
                data             JSONB NOT NULL,
                updated_at       TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        cur.execute("""
            INSERT INTO weather_cache (destination_slug, data, updated_at)
            VALUES (%s, %s::jsonb, NOW())
            ON CONFLICT (destination_slug) DO UPDATE
            SET data = EXCLUDED.data, updated_at = NOW()
        """, (weather["slug"], json.dumps(weather, ensure_ascii=False)))

        conn.commit()
        log.info(f"  💾 Weather saved: {weather['slug']} "
                 f"({weather['current']['temp_c']}°C, {weather['current']['condition']})")

    def run(self, conn):
        log.info("🌤  Open-Meteo Collector bắt đầu")
        saved = 0
        for slug, (lat, lng) in CITY_COORDS.items():
            raw = self.fetch_forecast(lat, lng)
            if not raw:
                log.warning(f"  Không lấy được thời tiết: {slug}")
                continue
            parsed = self.parse_forecast(raw, slug)
            self.save_to_db(conn, parsed)
            saved += 1

        log.info(f"✅ Open-Meteo: đã lưu thời tiết {saved} thành phố")
