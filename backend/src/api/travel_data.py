"""
FastAPI router exposing TravelBuddy structured data from PostgreSQL.

These endpoints are intentionally data-first. AI can call them later, but the
frontend should be able to search/filter/compare without chat.
"""

from __future__ import annotations

import os
import sys
import math
import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/travel", tags=["travel-data"])


def _connect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "travel_buddy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", ""),
        cursor_factory=RealDictCursor,
        # Trả timestamptz theo giờ Việt Nam (+07:00) để giờ bay hiển thị đúng local,
        # thay vì UTC (gây lệch 7 tiếng so với web hãng/Google Flights).
        options="-c timezone=Asia/Ho_Chi_Minh",
    )


def _clean(value: Any) -> Any:
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _fetch_all(sql: str, params: dict | None = None) -> list[dict]:
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or {})
                return _clean(cur.fetchall())
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Travel database unavailable: {exc}") from exc


def _fetch_one(sql: str, params: dict | None = None) -> dict | None:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


@router.get("/destinations")
def list_destinations(
    q: str | None = Query(default=None),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    limit: int = Query(default=20, ge=1, le=100),
):
    where = ["1=1"]
    params: dict[str, Any] = {"limit": limit}
    if q:
        where.append(
            "to_tsvector('simple', unaccent(d.name || ' ' || COALESCE(d.city,'') || ' ' || COALESCE(d.description,''))) "
            "@@ plainto_tsquery('simple', unaccent(%(q)s))"
        )
        params["q"] = q
    if country:
        where.append("d.country_code = %(country)s")
        params["country"] = country.upper()

    return {
        "items": _fetch_all(
            f"""
            SELECT d.*,
                   img.url AS primary_image_url
            FROM destinations d
            LEFT JOIN LATERAL (
                SELECT url
                FROM destination_images
                WHERE destination_id = d.id
                ORDER BY is_primary DESC, sort_order ASC
                LIMIT 1
            ) img ON TRUE
            WHERE {' AND '.join(where)}
            ORDER BY COALESCE(d.popularity_rank, 999), d.avg_rating DESC, d.name
            LIMIT %(limit)s
            """,
            params,
        )
    }


@router.get("/destinations/{slug}")
def get_destination(slug: str):
    destination = _fetch_one(
        """
        SELECT d.*,
               COALESCE(
                   json_agg(DISTINCT jsonb_build_object(
                       'url', di.url,
                       'thumbnail_url', di.thumbnail_url,
                       'provider', di.provider,
                       'license', di.license,
                       'attribution', di.attribution,
                       'is_primary', di.is_primary
                   )) FILTER (WHERE di.id IS NOT NULL),
                   '[]'
               ) AS images
        FROM destinations d
        LEFT JOIN destination_images di ON di.destination_id = d.id
        WHERE d.slug = %(slug)s
        GROUP BY d.id
        """,
        {"slug": slug},
    )
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination


@router.get("/flights/price-calendar")
def flight_price_calendar(
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    date_from: date = Query(...),
    date_to: date = Query(...),
    cabin_class: str = Query(default="economy"),
):
    return {
        "items": _fetch_all(
            """
            SELECT DISTINCT ON (fps.departure_date, fps.airline_name)
                   fr.route_key,
                   fps.departure_date,
                   fps.airline_iata,
                   fps.airline_name,
                   fps.flight_number,
                   fps.cabin_class,
                   fps.depart_at,
                   fps.arrive_at,
                   fps.duration_minutes,
                   fps.stops,
                   fps.price_amount,
                   fps.currency,
                   COALESCE(NULLIF(fps.booking_url, ''), a.booking_base_url) AS booking_url,
                   a.booking_base_url AS airline_booking_base_url,
                   fps.source,
                   fps.fetched_at,
                   fps.expires_at
            FROM flight_routes fr
            JOIN flight_price_snapshots fps ON fps.route_id = fr.id
            LEFT JOIN airlines a ON a.iata_code = fps.airline_iata
            WHERE fr.origin_iata = %(origin)s
              AND fr.destination_iata = %(destination)s
              AND fps.departure_date BETWEEN %(date_from)s AND %(date_to)s
              AND fps.cabin_class = %(cabin_class)s
              AND fps.expires_at > NOW()
            ORDER BY fps.departure_date, fps.airline_name, fps.price_amount ASC
            """,
            {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "date_from": date_from,
                "date_to": date_to,
                "cabin_class": cabin_class,
            },
        )
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Airports & Airlines (master data dùng cho dropdown của FE)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/airports")
def list_airports(domestic_only: bool = Query(default=True)):
    where = "WHERE is_domestic_vn = TRUE" if domestic_only else ""
    return {
        "items": _fetch_all(
            f"""
            SELECT iata_code, name, city, country_code, lat, lng, timezone, is_domestic_vn
            FROM airports
            {where}
            ORDER BY is_domestic_vn DESC, city, iata_code
            """
        )
    }


@router.get("/airlines")
def list_airlines():
    return {
        "items": _fetch_all(
            """
            SELECT iata_code, name, country_code, booking_base_url, logo_url
            FROM airlines
            ORDER BY is_seed_target DESC, name
            """
        )
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Flight search — trả giá thật từ snapshots nếu có, nếu chưa có thì sinh
#  ước tính thực tế (đánh dấu source="estimated") để FE luôn có dữ liệu.
# ─────────────────────────────────────────────────────────────────────────────

_AIRLINE_PRICE_FACTOR = {"VN": 1.18, "VJ": 0.84, "QH": 1.0}
_CABIN_MULT = {"economy": 1.0, "premium_economy": 1.5, "business": 2.6, "first": 4.0}
_DEPART_SLOTS = [(6, 5), (8, 40), (11, 20), (14, 15), (17, 30), (20, 45)]


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    try:
        r = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lng2 - lng1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))
    except Exception:
        return 0.0


def _seed01(*parts) -> float:
    """Pseudo-ngẫu nhiên xác định (0..1) từ các tham số → cùng input cho cùng kết quả."""
    h = hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _get_airport(iata: str) -> dict | None:
    return _fetch_one(
        "SELECT iata_code, name, city, lat, lng FROM airports WHERE iata_code = %(c)s",
        {"c": iata.upper()},
    )


def _gen_offers(origin_ap: dict, dest_ap: dict, date_str: str, cabin: str, airlines: list[dict]) -> list[dict]:
    dist = _haversine_km(origin_ap.get("lat") or 0, origin_ap.get("lng") or 0,
                         dest_ap.get("lat") or 0, dest_ap.get("lng") or 0) or 600.0
    base_dur = int(dist / 750 * 60) + 35  # phút: bay + buffer mặt đất
    cabin_mult = _CABIN_MULT.get(cabin, 1.0)
    rk = f'{origin_ap["iata_code"]}-{dest_ap["iata_code"]}'
    offers: list[dict] = []
    for al in airlines:
        code = al["iata_code"].strip()
        factor = _AIRLINE_PRICE_FACTOR.get(code, 1.0)
        n_slots = 2 + (1 if _seed01(code, date_str, "n") > 0.45 else 0)  # 2–3 chuyến/hãng
        chosen = sorted(range(len(_DEPART_SLOTS)), key=lambda i: _seed01(code, date_str, "slot", i))[:n_slots]
        for si in chosen:
            hh, mm = _DEPART_SLOTS[si]
            r = _seed01(code, date_str, hh, mm)
            price = (480000 + dist * 1850) * factor * cabin_mult * (0.82 + 0.42 * r)
            price = int(round(price / 1000) * 1000)
            dur = base_dur + int(r * 25)
            depart = f"{date_str}T{hh:02d}:{mm:02d}:00+07:00"
            arr = (datetime.fromisoformat(depart) + timedelta(minutes=dur)).isoformat()
            offers.append({
                "route_key": rk,
                "departure_date": date_str,
                "airline_iata": code,
                "airline_name": al["name"],
                "flight_number": f"{code}{100 + int(r * 800)}",
                "cabin_class": cabin,
                "depart_at": depart,
                "arrive_at": arr,
                "duration_minutes": dur,
                "stops": 0,
                "price_amount": price,
                "currency": "VND",
                "booking_url": al.get("booking_base_url"),
                "airline_booking_base_url": al.get("booking_base_url"),
                "source": "estimated",
            })
    offers.sort(key=lambda o: o["price_amount"])
    return offers


def _gen_calendar(origin_ap, dest_ap, center: date, cabin, airlines, before=3, after=10) -> list[dict]:
    out = []
    for delta in range(-before, after + 1):
        d = center + timedelta(days=delta)
        day_offers = _gen_offers(origin_ap, dest_ap, d.isoformat(), cabin, airlines)
        if day_offers:
            out.append({"date": d.isoformat(), "min_price": min(o["price_amount"] for o in day_offers), "currency": "VND"})
    return out


# Lấy giá THẬT từ SerpApi (Google Flights) cho đúng tuyến + ngày, lưu cache 24h.
# Tái dùng collector có sẵn; chỉ economy. Trả số snapshot đã lưu.
_TRAVEL_API_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "travel_api")


def _fetch_live_serpapi(origin: str, destination: str, date_str: str, cabin: str) -> int:
    if cabin != "economy" or not os.getenv("SERPAPI_API_KEY"):
        return 0
    if _TRAVEL_API_DIR not in sys.path:
        sys.path.insert(0, _TRAVEL_API_DIR)
    try:
        from collectors.serpapi_flights import SerpApiFlightsCollector
        from db.connection import get_conn
    except Exception:
        return 0
    conn = None
    try:
        conn = get_conn()
        saved = SerpApiFlightsCollector().collect_route(conn, origin, destination, date_str)
        conn.commit()
        return saved or 0
    except Exception:
        if conn:
            try: conn.rollback()
            except Exception: pass
        return 0
    finally:
        if conn:
            try: conn.close()
            except Exception: pass


@router.get("/flights/search")
def flight_search(
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    depart_date: date = Query(...),
    cabin_class: str = Query(default="economy"),
    adults: int = Query(default=1, ge=1, le=9),
):
    o, d = origin.upper(), destination.upper()
    if o == d:
        raise HTTPException(status_code=400, detail="Origin and destination must differ")
    origin_ap = _get_airport(o)
    dest_ap = _get_airport(d)
    if not origin_ap or not dest_ap:
        raise HTTPException(status_code=404, detail="Airport not found")

    airlines = _fetch_all(
        "SELECT iata_code, name, booking_base_url FROM airlines WHERE is_seed_target = TRUE ORDER BY name"
    ) or _fetch_all("SELECT iata_code, name, booking_base_url FROM airlines ORDER BY name")

    date_str = depart_date.isoformat()

    # 1) Ưu tiên giá thật (snapshots còn hạn) cho đúng ngày
    real = _fetch_all(
        """
        SELECT fr.route_key, fps.departure_date, fps.airline_iata, fps.airline_name,
               fps.flight_number, fps.cabin_class, fps.depart_at, fps.arrive_at,
               fps.duration_minutes, fps.stops, fps.price_amount, fps.currency,
               COALESCE(NULLIF(fps.booking_url, ''), a.booking_base_url) AS booking_url,
               a.booking_base_url AS airline_booking_base_url,
               fps.source
        FROM flight_routes fr
        JOIN flight_price_snapshots fps ON fps.route_id = fr.id
        LEFT JOIN airlines a ON a.iata_code = fps.airline_iata
        WHERE fr.origin_iata = %(o)s AND fr.destination_iata = %(d)s
          AND fps.departure_date = %(date)s AND fps.cabin_class = %(c)s
          AND fps.expires_at > NOW()
        ORDER BY fps.price_amount ASC
        """,
        {"o": o, "d": d, "date": depart_date, "c": cabin_class},
    )

    # 2) Chưa có cache cho đúng ngày → thử lấy giá THẬT từ SerpApi (economy), lưu cache 24h
    if not real and _fetch_live_serpapi(o, d, date_str, cabin_class):
        real = _fetch_all(
            """
            SELECT fr.route_key, fps.departure_date, fps.airline_iata, fps.airline_name,
                   fps.flight_number, fps.cabin_class, fps.depart_at, fps.arrive_at,
                   fps.duration_minutes, fps.stops, fps.price_amount, fps.currency,
                   COALESCE(NULLIF(fps.booking_url, ''), a.booking_base_url) AS booking_url,
                   a.booking_base_url AS airline_booking_base_url, fps.source
            FROM flight_routes fr
            JOIN flight_price_snapshots fps ON fps.route_id = fr.id
            LEFT JOIN airlines a ON a.iata_code = fps.airline_iata
            WHERE fr.origin_iata = %(o)s AND fr.destination_iata = %(d)s
              AND fps.departure_date = %(date)s AND fps.cabin_class = %(c)s
              AND fps.expires_at > NOW()
            ORDER BY fps.price_amount ASC
            """,
            {"o": o, "d": d, "date": depart_date, "c": cabin_class},
        )

    if real:
        estimated = False
        offers = real
    else:
        estimated = True
        offers = _gen_offers(origin_ap, dest_ap, date_str, cabin_class, airlines)

    # 3) Lịch giá: LUÔN dựng đủ 14 ngày (ước tính làm nền) để mọi tuyến nhất quán,
    #    rồi phủ giá THẬT lên những ngày đã có snapshot.
    calendar = _gen_calendar(origin_ap, dest_ap, depart_date, cabin_class, airlines)
    real_mins = _fetch_all(
        """
        SELECT fps.departure_date AS date, MIN(fps.price_amount) AS min_price
        FROM flight_routes fr
        JOIN flight_price_snapshots fps ON fps.route_id = fr.id
        WHERE fr.origin_iata = %(o)s AND fr.destination_iata = %(d)s
          AND fps.cabin_class = %(c)s AND fps.expires_at > NOW()
          AND fps.departure_date BETWEEN %(from)s AND %(to)s
        GROUP BY fps.departure_date
        """,
        {"o": o, "d": d, "c": cabin_class,
         "from": depart_date - timedelta(days=3), "to": depart_date + timedelta(days=10)},
    )
    rm = {str(r["date"]): r["min_price"] for r in real_mins}
    for c in calendar:
        if c["date"] in rm:
            c["min_price"] = rm[c["date"]]

    return {
        "origin": origin_ap,
        "destination": dest_ap,
        "depart_date": date_str,
        "cabin_class": cabin_class,
        "adults": adults,
        "currency": "VND",
        "estimated": estimated,
        "offers": offers,
        "price_calendar": calendar,
    }


@router.get("/weather/forecast")
def weather_forecast(destination: str, days: int = Query(default=16, ge=1, le=16)):
    return {
        "items": _fetch_all(
            """
            SELECT wdf.forecast_date,
                   wdf.weather_code,
                   wdf.temp_max_c,
                   wdf.temp_min_c,
                   wdf.precipitation_sum_mm,
                   wdf.precipitation_probability_max,
                   wdf.wind_speed_max_kmh,
                   wdf.travel_score,
                   wc.fetched_at,
                   wc.expires_at
            FROM destinations d
            JOIN weather_daily_forecasts wdf ON wdf.destination_id = d.id
            JOIN weather_cache wc ON wc.id = wdf.weather_cache_id
            WHERE d.slug = %(destination)s
              AND wc.expires_at > NOW()
            ORDER BY wdf.forecast_date
            LIMIT %(days)s
            """,
            {"destination": destination, "days": days},
        )
    }


@router.get("/weather/by-airport")
def weather_by_airport(iata: str = Query(..., min_length=3, max_length=3),
                       days: int = Query(default=10, ge=1, le=16),
                       date_from: date | None = Query(default=None),
                       date_to: date | None = Query(default=None)):
    """
    Thời tiết tại thành phố của sân bay đến (dùng cho trang vé máy bay).
    Map mã sân bay → destination (qua iata_city_code), ưu tiên cache trong DB,
    nếu chưa có thì lấy trực tiếp từ Open-Meteo (miễn phí, không cần key).
    """
    dest = _fetch_one(
        """
        SELECT slug, name, city, lat, lng
        FROM destinations
        WHERE iata_city_code = %(iata)s
        ORDER BY COALESCE(popularity_rank, 999)
        LIMIT 1
        """,
        {"iata": iata.upper()},
    )
    if not dest:
        return {"destination": None, "items": [], "source": None}

    cached = _fetch_all(
        """
        SELECT wdf.forecast_date, wdf.weather_code, wdf.temp_max_c, wdf.temp_min_c,
               wdf.precipitation_sum_mm, wdf.precipitation_probability_max,
               wdf.wind_speed_max_kmh, wdf.travel_score
        FROM destinations d
        JOIN weather_daily_forecasts wdf ON wdf.destination_id = d.id
        JOIN weather_cache wc ON wc.id = wdf.weather_cache_id
        WHERE d.slug = %(slug)s AND wc.expires_at > NOW()
        ORDER BY wdf.forecast_date
        LIMIT %(days)s
        """,
        {"slug": dest["slug"], "days": days},
    )
    if cached:
        return {"destination": dest, "items": cached, "source": "cache"}

    # fallback: Open-Meteo trực tiếp
    try:
        params = {
            "latitude": dest["lat"], "longitude": dest["lng"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                     "precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
            "timezone": "auto",
        }
        # Nếu có khoảng ngày (khớp lịch giá) → dùng start/end; Open-Meteo dự báo tới ~16 ngày tới.
        if date_from and date_to:
            params["start_date"] = date_from.isoformat()
            params["end_date"] = date_to.isoformat()
        else:
            params["forecast_days"] = days
        r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=8)
        r.raise_for_status()
        dd = r.json().get("daily", {})
        times = dd.get("time", [])
        items = [{
            "forecast_date": times[i],
            "weather_code": (dd.get("weather_code") or [None])[i],
            "temp_max_c": (dd.get("temperature_2m_max") or [None])[i],
            "temp_min_c": (dd.get("temperature_2m_min") or [None])[i],
            "precipitation_sum_mm": (dd.get("precipitation_sum") or [None])[i],
            "precipitation_probability_max": (dd.get("precipitation_probability_max") or [None])[i],
            "wind_speed_max_kmh": (dd.get("wind_speed_10m_max") or [None])[i],
        } for i in range(len(times))]
        return {"destination": dest, "items": items, "source": "open-meteo-live"}
    except Exception:
        return {"destination": dest, "items": [], "source": None}


@router.get("/price-calendar/best-days")
def best_days(
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    date_from: date = Query(...),
    date_to: date = Query(...),
):
    return {
        "items": _fetch_all(
            """
            WITH cheapest AS (
                SELECT fr.id AS route_id,
                       fr.destination_id,
                       fps.departure_date,
                       MIN(fps.price_amount) AS min_price
                FROM flight_routes fr
                JOIN flight_price_snapshots fps ON fps.route_id = fr.id
                WHERE fr.origin_iata = %(origin)s
                  AND fr.destination_iata = %(destination)s
                  AND fps.departure_date BETWEEN %(date_from)s AND %(date_to)s
                  AND fps.expires_at > NOW()
                GROUP BY fr.id, fr.destination_id, fps.departure_date
            ),
            price_stats AS (
                SELECT MIN(min_price) AS min_p, MAX(min_price) AS max_p FROM cheapest
            )
            SELECT c.departure_date,
                   c.min_price,
                   wdf.weather_code,
                   wdf.temp_max_c,
                   wdf.temp_min_c,
                   wdf.precipitation_sum_mm,
                   wdf.travel_score,
                   ROUND(
                       (
                           CASE
                               WHEN ps.max_p = ps.min_p THEN 100
                               ELSE 100 - ((c.min_price - ps.min_p) / NULLIF(ps.max_p - ps.min_p, 0) * 100)
                           END
                       ) * 0.6 + COALESCE(wdf.travel_score, 50) * 0.4
                   ) AS best_day_score
            FROM cheapest c
            CROSS JOIN price_stats ps
            LEFT JOIN weather_daily_forecasts wdf
                ON wdf.destination_id = c.destination_id
               AND wdf.forecast_date = c.departure_date
            ORDER BY best_day_score DESC NULLS LAST, c.min_price ASC
            """,
            {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "date_from": date_from,
                "date_to": date_to,
            },
        )
    }


@router.get("/hotels")
def list_hotels(
    destination: str,
    checkin: date | None = Query(default=None),
    checkout: date | None = Query(default=None),
    adults: int = Query(default=2, ge=1, le=8),
    min_stars: float | None = Query(default=None, ge=0, le=5),
    limit: int = Query(default=30, ge=1, le=100),
):
    where = ["d.slug = %(destination)s"]
    params: dict[str, Any] = {
        "destination": destination,
        "checkin": checkin,
        "checkout": checkout,
        "adults": adults,
        "limit": limit,
    }
    if min_stars is not None:
        where.append("h.stars >= %(min_stars)s")
        params["min_stars"] = min_stars

    rate_join = ""
    if checkin and checkout:
        rate_join = """
            LEFT JOIN LATERAL (
                SELECT checkin_date, checkout_date, price_amount, currency, deep_link_url, fetched_at, expires_at
                FROM hotel_rate_snapshots
                WHERE hotel_id = h.id
                  AND checkin_date = %(checkin)s
                  AND checkout_date = %(checkout)s
                  AND adults = %(adults)s
                  AND expires_at > NOW()
                ORDER BY price_amount ASC
                LIMIT 1
            ) rate ON TRUE
        """
    else:
        rate_join = """
            LEFT JOIN LATERAL (
                SELECT checkin_date, checkout_date, price_amount, currency, deep_link_url, fetched_at, expires_at
                FROM hotel_rate_snapshots
                WHERE hotel_id = h.id
                  AND adults = %(adults)s
                  AND expires_at > NOW()
                ORDER BY fetched_at DESC, price_amount ASC
                LIMIT 1
            ) rate ON TRUE
        """

    return {
        "items": _fetch_all(
            f"""
            SELECT h.*,
                   img.url AS primary_image_url,
                   rate.checkin_date AS rate_checkin_date,
                   rate.checkout_date AS rate_checkout_date,
                   rate.price_amount,
                   rate.currency AS rate_currency,
                   COALESCE(rate.deep_link_url, h.deep_link_url) AS booking_url,
                   rate.fetched_at AS rate_fetched_at,
                   rate.expires_at AS rate_expires_at
            FROM hotels h
            JOIN destinations d ON d.id = h.destination_id
            LEFT JOIN LATERAL (
                SELECT url FROM hotel_images
                WHERE hotel_id = h.id
                ORDER BY is_primary DESC, sort_order ASC
                LIMIT 1
            ) img ON TRUE
            {rate_join}
            WHERE {' AND '.join(where)}
            ORDER BY rate.price_amount ASC NULLS LAST, h.avg_rating DESC, h.name
            LIMIT %(limit)s
            """,
            params,
        )
    }


@router.get("/pois")
def list_pois(
    destination: str,
    category: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    where = ["d.slug = %(destination)s"]
    params: dict[str, Any] = {"destination": destination, "limit": limit}
    if category:
        where.append("p.category = %(category)s")
        params["category"] = category

    return {
        "items": _fetch_all(
            f"""
            SELECT p.*,
                   img.url AS primary_image_url
            FROM pois p
            JOIN destinations d ON d.id = p.destination_id
            LEFT JOIN LATERAL (
                SELECT url FROM poi_images
                WHERE poi_id = p.id
                ORDER BY sort_order ASC
                LIMIT 1
            ) img ON TRUE
            WHERE {' AND '.join(where)}
            ORDER BY p.avg_rating DESC, p.name
            LIMIT %(limit)s
            """,
            params,
        )
    }


@router.get("/packing/templates")
def packing_templates(
    trip_type: str,
    season: str,
    days: int = Query(..., ge=1, le=60),
):
    return {
        "items": _fetch_all(
            """
            SELECT pt.*,
                   COALESCE(
                       json_agg(jsonb_build_object(
                           'id', pti.id,
                           'category', pti.category,
                           'item_name', pti.item_name,
                           'quantity_rule', pti.quantity_rule,
                           'note', pti.note,
                           'is_default_checked', pti.is_default_checked,
                           'sort_order', pti.sort_order
                       ) ORDER BY pti.category, pti.sort_order)
                       FILTER (WHERE pti.id IS NOT NULL),
                       '[]'
                   ) AS items
            FROM packing_templates pt
            LEFT JOIN packing_template_items pti ON pti.template_id = pt.id
            WHERE pt.is_active = TRUE
              AND pt.trip_type IN (%(trip_type)s, 'general')
              AND pt.season = %(season)s
              AND pt.day_min <= %(days)s
              AND (pt.day_max IS NULL OR pt.day_max >= %(days)s)
            GROUP BY pt.id
            ORDER BY pt.priority ASC
            """,
            {"trip_type": trip_type, "season": season, "days": days},
        )
    }


@router.get("/exchange-rates")
def exchange_rates(
    base: str = Query(default="VND", min_length=3, max_length=3),
    quotes: str = Query(default="USD,THB,JPY,SGD,EUR"),
):
    quote_list = [q.strip().upper() for q in quotes.split(",") if q.strip()]
    return {
        "items": _fetch_all(
            """
            SELECT base_currency, target_currency, rate, rate_date, source, fetched_at, expires_at
            FROM exchange_rate_cache
            WHERE base_currency = %(base)s
              AND target_currency = ANY(%(quotes)s)
              AND expires_at > NOW()
            ORDER BY target_currency
            """,
            {"base": base.upper(), "quotes": quote_list},
        )
    }


@router.get("/countries/{code}")
def country_detail(code: str):
    row = _fetch_one(
        """
        SELECT c.*,
               vr.visa_required,
               vr.visa_type,
               vr.max_stay_days,
               vr.note AS visa_note,
               vr.verified_at AS visa_verified_at
        FROM countries c
        LEFT JOIN country_visa_rules vr
            ON vr.destination_country_code = c.code
           AND vr.passport_country_code = 'VN'
        WHERE c.code = %(code)s
        """,
        {"code": code.upper()},
    )
    if not row:
        raise HTTPException(status_code=404, detail="Country not found")
    return row
