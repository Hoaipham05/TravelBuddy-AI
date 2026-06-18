"""
FastAPI router exposing TravelBuddy structured data from PostgreSQL.

These endpoints are intentionally data-first. AI can call them later, but the
frontend should be able to search/filter/compare without chat.
"""

from __future__ import annotations

import os
import sys
import json
import math
import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import uuid as uuidlib

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from pydantic import BaseModel, Field

from src.api.auth import get_current_user, UserPublic

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


def _execute(sql: str, params: dict | None = None) -> int:
    """Chạy INSERT/UPDATE/DELETE không cần RETURNING. Trả số dòng bị ảnh hưởng.
    (`with _connect()` của psycopg2 tự commit khi thoát block không lỗi.)"""
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or {})
                return cur.rowcount
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Travel database unavailable: {exc}") from exc


def _notify(user_id: str, actor: UserPublic | None, kind: str, message: str,
            review_id: str | None = None, comment_id: str | None = None,
            data: dict | None = None) -> None:
    """Tạo một thông báo cho `user_id`. Bỏ qua nếu tự tương tác với chính mình.
    Lỗi tạo thông báo không được làm hỏng hành động chính → nuốt lỗi."""
    if not user_id:
        return
    if actor and str(actor.id) == str(user_id):
        return
    try:
        _execute(
            """
            INSERT INTO notifications (user_id, actor_id, kind, review_id, comment_id, message, data)
            VALUES (%(uid)s, %(actor)s, %(kind)s, %(rid)s, %(cid)s, %(msg)s, %(data)s::jsonb)
            """,
            {
                "uid": user_id,
                "actor": str(actor.id) if actor else None,
                "kind": kind,
                "rid": review_id,
                "cid": comment_id,
                "msg": message,
                "data": json.dumps(data or {}),
            },
        )
    except Exception:  # noqa: BLE001
        pass


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


def _fetch_live_hotels(slug: str, checkin: str, checkout: str, adults: int) -> int:
    """Lấy giá khách sạn THẬT từ SerpApi (Google Hotels) cho điểm đến + ngày, lưu cache."""
    if not os.getenv("SERPAPI_API_KEY"):
        return 0
    if _TRAVEL_API_DIR not in sys.path:
        sys.path.insert(0, _TRAVEL_API_DIR)
    try:
        from collectors.serpapi_hotels import SerpApiHotelsCollector
        from db.connection import get_conn
    except Exception:
        return 0
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, slug FROM destinations WHERE slug = %s", (slug,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return 0
        dest = {"id": str(row[0]), "name": row[1], "slug": row[2]}
        col = SerpApiHotelsCollector()
        raw = col.search_hotels(dest, checkin, checkout, adults)
        if not raw:
            return 0
        saved = col.save_result_set(conn, dest, raw, checkin, checkout, adults)
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

    # Khi có ngày nhận/trả phòng mà chưa có giá còn hạn → lấy giá THẬT từ SerpApi (cache 24h)
    if checkin and checkout:
        fresh = _fetch_one(
            """
            SELECT 1 FROM hotel_rate_snapshots hrs
            JOIN hotels h ON h.id = hrs.hotel_id
            JOIN destinations d ON d.id = h.destination_id
            WHERE d.slug = %(destination)s AND hrs.checkin_date = %(checkin)s
              AND hrs.checkout_date = %(checkout)s AND hrs.adults = %(adults)s
              AND hrs.expires_at > NOW()
            LIMIT 1
            """,
            {"destination": destination, "checkin": checkin, "checkout": checkout, "adults": adults},
        )
        if not fresh:
            _fetch_live_hotels(destination, checkin.isoformat(), checkout.isoformat(), adults)

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


# ─────────────────────────────────────────────────────────────────────────────
#  Cộng đồng Traveler — feed bài chia sẻ (dùng bảng reviews, gắn theo điểm đến)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/community/posts")
def community_posts(
    destination: str | None = Query(default=None),
    sort: str = Query(default="recent"),
    limit: int = Query(default=40, ge=1, le=100),
):
    where = ["1=1"]
    params: dict[str, Any] = {"limit": limit}
    if destination:
        where.append("d.slug = %(destination)s")
        params["destination"] = destination
    order = "r.helpful_count DESC, r.created_at DESC" if sort == "helpful" else "r.created_at DESC"
    return {
        "items": _fetch_all(
            f"""
            SELECT r.id, r.rating, r.content, r.images, r.trip_data, r.helpful_count, r.created_at,
                   u.id AS author_id, u.full_name AS author_name, u.level AS author_level, u.avatar_url AS author_avatar,
                   d.slug AS destination_slug, d.name AS destination_name,
                   (SELECT COUNT(*) FROM community_comments cc WHERE cc.review_id = r.id) AS comment_count
            FROM reviews r
            JOIN users u ON u.id = r.user_id
            LEFT JOIN destinations d ON d.id = r.destination_id
            WHERE {' AND '.join(where)}
            ORDER BY {order}
            LIMIT %(limit)s
            """,
            params,
        )
    }


class CommunityPostIn(BaseModel):
    destination_slug: str = Field(..., min_length=1)
    content: str = Field(..., min_length=3, max_length=2000)
    rating: float = Field(default=5, ge=1, le=5)
    images: list[str] = Field(default_factory=list)
    trip_data: dict | None = None  # snapshot lịch trình đã tạo (bắt buộc gắn theo bài)


@router.post("/community/posts")
def create_community_post(body: CommunityPostIn, user: UserPublic = Depends(get_current_user)):
    if not body.trip_data:
        raise HTTPException(status_code=400, detail="Bài viết phải gắn với một lịch trình bạn đã tạo.")
    dest = _fetch_one("SELECT id, slug, name FROM destinations WHERE slug = %(s)s", {"s": body.destination_slug})
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    row = _fetch_one(
        """
        INSERT INTO reviews (user_id, destination_id, rating, content, images, trip_data)
        VALUES (%(uid)s, %(did)s, %(rating)s, %(content)s, %(images)s::jsonb, %(trip)s::jsonb)
        RETURNING id, rating, content, images, trip_data, helpful_count, created_at
        """,
        {
            "uid": str(user.id),
            "did": dest["id"],
            "rating": round(body.rating, 1),
            "content": body.content.strip(),
            "images": json.dumps(body.images),
            "trip": json.dumps(body.trip_data),
        },
    )
    row.update({
        "author_id": str(user.id),
        "author_name": user.full_name,
        "author_level": user.level,
        "author_avatar": user.avatar_url,
        "destination_slug": dest["slug"],
        "destination_name": dest["name"],
    })
    return row


def _post_snapshot(post: dict) -> dict:
    """Snapshot denormalize của một bài chia sẻ để hiển thị trong Wishlist."""
    imgs = post.get("images") or []
    return {
        "kind": "post",
        "author_name": post.get("author_name"),
        "destination_name": post.get("destination_name"),
        "destination_slug": post.get("destination_slug"),
        "excerpt": _excerpt(post.get("content")),
        "image_url": imgs[0] if imgs else None,
        "rating": post.get("rating"),
        "trip_data": post.get("trip_data"),
    }


@router.post("/community/posts/{post_id}/helpful")
def community_post_helpful(post_id: str, user: UserPublic = Depends(get_current_user)):
    """Bấm 'Hữu ích' = tăng lượt + lưu bài vào Wishlist (idempotent theo user)."""
    post = _fetch_one(
        """
        SELECT r.id, r.user_id, r.content, r.images, r.trip_data, r.rating,
               d.slug AS destination_slug, d.name AS destination_name,
               au.full_name AS author_name
        FROM reviews r
        JOIN users au ON au.id = r.user_id
        LEFT JOIN destinations d ON d.id = r.destination_id
        WHERE r.id = %(id)s
        """,
        {"id": post_id},
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Lưu (idempotent) — chỉ tăng lượt + thông báo khi đây là lần đầu user này thấy hữu ích.
    inserted = _fetch_one(
        """
        INSERT INTO saved_items (user_id, kind, review_id, snapshot, dedup_key)
        VALUES (%(uid)s, 'post', %(rid)s, %(snap)s::jsonb, %(dedup)s)
        ON CONFLICT (user_id, dedup_key) DO NOTHING
        RETURNING id
        """,
        {"uid": str(user.id), "rid": post_id,
         "snap": json.dumps(_post_snapshot(post)), "dedup": f"post:{post_id}"},
    )
    if inserted:
        row = _fetch_one(
            "UPDATE reviews SET helpful_count = helpful_count + 1 WHERE id = %(id)s RETURNING helpful_count",
            {"id": post_id},
        )
        _notify(str(post["user_id"]), user, "helpful",
                f"{user.full_name} thấy bài chia sẻ của bạn hữu ích", review_id=post_id)
    else:
        row = _fetch_one("SELECT helpful_count FROM reviews WHERE id = %(id)s", {"id": post_id})
    return {"helpful_count": row["helpful_count"], "saved": True}


@router.delete("/community/posts/{post_id}/helpful")
def remove_community_post_helpful(post_id: str, user: UserPublic = Depends(get_current_user)):
    """Bỏ 'Hữu ích' = giảm lượt + gỡ bài khỏi Wishlist (chỉ khi user này từng lưu)."""
    removed = _execute(
        "DELETE FROM saved_items WHERE user_id = %(uid)s AND dedup_key = %(dedup)s",
        {"uid": str(user.id), "dedup": f"post:{post_id}"},
    )
    if removed:
        row = _fetch_one(
            "UPDATE reviews SET helpful_count = GREATEST(helpful_count - 1, 0) WHERE id = %(id)s RETURNING helpful_count",
            {"id": post_id},
        )
    else:
        row = _fetch_one("SELECT helpful_count FROM reviews WHERE id = %(id)s", {"id": post_id})
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"helpful_count": row["helpful_count"], "saved": False}


@router.get("/community/featured-destinations")
def community_featured_destinations(limit: int = Query(default=5, ge=1, le=12)):
    """Điểm đến nổi bật cho HomePage — tổng hợp từ cộng đồng:
    nhiều review tích cực (avg rating >= 4) + nhiều lượt hữu ích."""
    return {
        "items": _fetch_all(
            """
            SELECT d.slug, d.name, d.city,
                   COUNT(r.id) AS review_count,
                   ROUND(AVG(r.rating)::numeric, 1) AS avg_rating,
                   COALESCE(SUM(r.helpful_count), 0) AS total_helpful,
                   img.url AS image_url
            FROM destinations d
            JOIN reviews r ON r.destination_id = d.id
            LEFT JOIN LATERAL (
                SELECT url FROM destination_images
                WHERE destination_id = d.id ORDER BY is_primary DESC, sort_order ASC LIMIT 1
            ) img ON TRUE
            GROUP BY d.id, img.url
            HAVING AVG(r.rating) >= 4
            ORDER BY COALESCE(SUM(r.helpful_count), 0) DESC, COUNT(r.id) DESC, AVG(r.rating) DESC
            LIMIT %(limit)s
            """,
            {"limit": limit},
        )
    }


# ─── Bình luận cho bài cộng đồng ─────────────────────────────────────────────

@router.get("/community/posts/{post_id}/comments")
def list_comments(post_id: str):
    return {
        "items": _fetch_all(
            """
            SELECT c.id, c.content, c.images, c.created_at, c.parent_id,
                   u.id AS author_id, u.full_name AS author_name, u.avatar_url AS author_avatar
            FROM community_comments c
            JOIN users u ON u.id = c.user_id
            WHERE c.review_id = %(pid)s
            ORDER BY COALESCE(c.parent_id::text, c.id::text), c.created_at ASC
            """,
            {"pid": post_id},
        )
    }


class CommentIn(BaseModel):
    content: str = Field(default="", max_length=1000)
    parent_id: str | None = None
    images: list[str] = Field(default_factory=list)


@router.post("/community/posts/{post_id}/comments")
def add_comment(post_id: str, body: CommentIn, user: UserPublic = Depends(get_current_user)):
    content = body.content.strip()
    if not content and not body.images:
        raise HTTPException(status_code=400, detail="Bình luận cần nội dung hoặc ảnh.")
    post = _fetch_one("SELECT id, user_id FROM reviews WHERE id = %(id)s", {"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    parent = None
    if body.parent_id:
        parent = _fetch_one(
            "SELECT id, user_id FROM community_comments WHERE id = %(id)s AND review_id = %(pid)s",
            {"id": body.parent_id, "pid": post_id},
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    row = _fetch_one(
        """
        INSERT INTO community_comments (review_id, user_id, content, images, parent_id)
        VALUES (%(pid)s, %(uid)s, %(c)s, %(imgs)s::jsonb, %(parent_id)s)
        RETURNING id, content, images, created_at, parent_id
        """,
        {"pid": post_id, "uid": str(user.id), "c": content,
         "imgs": json.dumps(body.images[:8]),
         "parent_id": body.parent_id if body.parent_id else None},
    )
    row.update({"author_id": str(user.id), "author_name": user.full_name, "author_avatar": user.avatar_url})

    # Thông báo: trả lời → báo chủ bình luận cha; bình luận gốc → báo tác giả bài.
    if parent:
        _notify(str(parent["user_id"]), user, "reply",
                f"{user.full_name} đã trả lời bình luận của bạn",
                review_id=post_id, comment_id=str(row["id"]))
    _notify(str(post["user_id"]), user, "comment",
            f"{user.full_name} đã bình luận về bài chia sẻ của bạn",
            review_id=post_id, comment_id=str(row["id"]))
    return row


# ─────────────────────────────────────────────────────────────────────────────
#  Upload ảnh (cộng đồng) — lưu file vào volume, phục vụ tĩnh qua /uploads
# ─────────────────────────────────────────────────────────────────────────────

_UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.getcwd(), "uploads"))
_ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif",
}
_MAX_UPLOAD_BYTES = 6 * 1024 * 1024  # 6MB (FE đã nén client-side trước khi gửi)


@router.post("/uploads/image")
async def upload_image(file: UploadFile = File(...), user: UserPublic = Depends(get_current_user)):
    ext = _ALLOWED_IMAGE_TYPES.get((file.content_type or "").lower())
    if not ext:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận ảnh JPEG/PNG/WebP/GIF.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File rỗng.")
    if len(data) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Ảnh quá lớn (tối đa 6MB).")

    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    fname = f"{uuidlib.uuid4().hex}{ext}"
    try:
        with open(os.path.join(_UPLOAD_DIR, fname), "wb") as fh:
            fh.write(data)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Không lưu được ảnh.") from exc

    # URL đi qua proxy: FE dùng /api/uploads/<file>; backend phục vụ tại /uploads/<file>.
    return {"url": f"/api/uploads/{fname}"}


# ─────────────────────────────────────────────────────────────────────────────
#  Lưu "hữu ích" từ cộng đồng → đổ vào Wishlist
# ─────────────────────────────────────────────────────────────────────────────

def _excerpt(text: str | None, n: int = 220) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[:n].rstrip() + "…"


class SaveItemIn(BaseModel):
    kind: str = Field(..., pattern="^(post|comment|photo)$")
    review_id: str
    comment_id: str | None = None
    image_url: str | None = None
    note: str | None = Field(default=None, max_length=500)


@router.post("/community/saved")
def save_item(body: SaveItemIn, user: UserPublic = Depends(get_current_user)):
    post = _fetch_one(
        """
        SELECT r.id, r.user_id, r.content, r.images, r.trip_data, r.rating,
               d.slug AS destination_slug, d.name AS destination_name,
               au.full_name AS author_name
        FROM reviews r
        JOIN users au ON au.id = r.user_id
        LEFT JOIN destinations d ON d.id = r.destination_id
        WHERE r.id = %(id)s
        """,
        {"id": body.review_id},
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = None
    if body.kind == "comment":
        if not body.comment_id:
            raise HTTPException(status_code=400, detail="Thiếu comment_id.")
        comment = _fetch_one(
            """
            SELECT c.id, c.user_id, c.content, c.images, u.full_name AS author_name
            FROM community_comments c JOIN users u ON u.id = c.user_id
            WHERE c.id = %(id)s AND c.review_id = %(pid)s
            """,
            {"id": body.comment_id, "pid": body.review_id},
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

    # dedup_key: mỗi (bài) / (bình luận) / (ảnh cụ thể) chỉ lưu 1 lần
    if body.kind == "post":
        dedup = f"post:{body.review_id}"
    elif body.kind == "comment":
        dedup = f"comment:{body.comment_id}"
    else:
        if not body.image_url:
            raise HTTPException(status_code=400, detail="Thiếu image_url.")
        dedup = f"photo:{body.review_id}:{body.image_url}"

    # snapshot denormalize để Wishlist render độc lập
    src = comment if body.kind == "comment" else post
    snapshot = {
        "kind": body.kind,
        "author_name": src.get("author_name") or post.get("author_name"),
        "destination_name": post.get("destination_name"),
        "destination_slug": post.get("destination_slug"),
        "excerpt": _excerpt(src.get("content")),
        "image_url": body.image_url,
        "rating": post.get("rating"),
    }
    if body.kind == "post":
        snapshot["trip_data"] = post.get("trip_data")
        imgs = post.get("images") or []
        if not body.image_url and imgs:
            snapshot["image_url"] = imgs[0]

    row = _fetch_one(
        """
        INSERT INTO saved_items (user_id, kind, review_id, comment_id, image_url, note, snapshot, dedup_key)
        VALUES (%(uid)s, %(kind)s, %(rid)s, %(cid)s, %(img)s, %(note)s, %(snap)s::jsonb, %(dedup)s)
        ON CONFLICT (user_id, dedup_key) DO UPDATE SET note = COALESCE(EXCLUDED.note, saved_items.note)
        RETURNING id, kind, review_id, comment_id, image_url, note, snapshot, created_at
        """,
        {"uid": str(user.id), "kind": body.kind, "rid": body.review_id,
         "cid": body.comment_id, "img": body.image_url, "note": body.note,
         "snap": json.dumps(snapshot), "dedup": dedup},
    )

    # Báo cho tác giả nội dung được lưu. Với bài chia sẻ, "lưu" = "thấy hữu ích".
    target_author = comment["user_id"] if comment else post["user_id"]
    if body.kind == "post":
        msg = f"{user.full_name} thấy bài chia sẻ của bạn hữu ích"
    else:
        label = {"comment": "bình luận", "photo": "tấm ảnh"}[body.kind]
        msg = f"{user.full_name} đã lưu {label} của bạn vào wishlist"
    _notify(str(target_author), user, "save", msg,
            review_id=body.review_id, comment_id=body.comment_id)
    return row


@router.get("/community/saved")
def list_saved(user: UserPublic = Depends(get_current_user)):
    return {
        "items": _fetch_all(
            """
            SELECT id, kind, review_id, comment_id, image_url, note, snapshot, created_at
            FROM saved_items WHERE user_id = %(uid)s
            ORDER BY created_at DESC
            """,
            {"uid": str(user.id)},
        )
    }


@router.delete("/community/saved/{item_id}")
def delete_saved(item_id: str, user: UserPublic = Depends(get_current_user)):
    n = _execute(
        "DELETE FROM saved_items WHERE id = %(id)s AND user_id = %(uid)s",
        {"id": item_id, "uid": str(user.id)},
    )
    if not n:
        raise HTTPException(status_code=404, detail="Saved item not found")
    return {"deleted": True}


# ─────────────────────────────────────────────────────────────────────────────
#  Thông báo
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/notifications")
def list_notifications(
    user: UserPublic = Depends(get_current_user),
    limit: int = Query(default=30, ge=1, le=100),
):
    items = _fetch_all(
        """
        SELECT n.id, n.kind, n.message, n.review_id, n.comment_id, n.data, n.is_read, n.created_at,
               a.full_name AS actor_name, a.avatar_url AS actor_avatar
        FROM notifications n
        LEFT JOIN users a ON a.id = n.actor_id
        WHERE n.user_id = %(uid)s
        ORDER BY n.created_at DESC
        LIMIT %(limit)s
        """,
        {"uid": str(user.id), "limit": limit},
    )
    unread = _fetch_one(
        "SELECT COUNT(*) AS c FROM notifications WHERE user_id = %(uid)s AND is_read = FALSE",
        {"uid": str(user.id)},
    )
    return {"items": items, "unread": int(unread["c"]) if unread else 0}


# ─────────────────────────────────────────────────────────────────────────────
#  Hồ sơ người dùng — cập nhật của tôi + xem công khai (sở thích du lịch)
# ─────────────────────────────────────────────────────────────────────────────

class ProfileUpdateIn(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, max_length=120)
    birthday: str | None = Field(default=None, max_length=20)
    interests: list[str] | None = None


@router.put("/profile")
def update_profile(body: ProfileUpdateIn, user: UserPublic = Depends(get_current_user)):
    """Lưu hồ sơ của tôi. Thông tin cá nhân + sở thích cất trong users.travel_preferences."""
    prefs: dict[str, Any] = {}
    for key in ("bio", "phone", "location", "birthday", "interests"):
        val = getattr(body, key)
        if val is not None:
            prefs[key] = val
    row = _fetch_one(
        """
        UPDATE users
           SET full_name = COALESCE(%(name)s, full_name),
               travel_preferences = travel_preferences || %(prefs)s::jsonb,
               updated_at = NOW()
         WHERE id = %(id)s
     RETURNING id, full_name, email, avatar_url, travel_preferences, total_points, level
        """,
        {"name": body.full_name.strip() if body.full_name else None,
         "prefs": json.dumps(prefs), "id": str(user.id)},
    )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


@router.get("/users/{user_id}")
def public_user_profile(user_id: str):
    """Hồ sơ công khai — để người khác xem sở thích du lịch của một thành viên."""
    try:
        uuidlib.UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail="User not found")
    row = _fetch_one(
        """
        SELECT u.id, u.full_name, u.avatar_url, u.level, u.travel_preferences, u.created_at,
               (SELECT COUNT(*) FROM reviews r WHERE r.user_id = u.id) AS post_count
        FROM users u WHERE u.id = %(id)s
        """,
        {"id": user_id},
    )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


class MarkReadIn(BaseModel):
    ids: list[str] | None = None  # None = đánh dấu đã đọc tất cả


@router.post("/notifications/read")
def mark_notifications_read(body: MarkReadIn, user: UserPublic = Depends(get_current_user)):
    if body.ids:
        _execute(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = %(uid)s AND id = ANY(%(ids)s::uuid[])",
            {"uid": str(user.id), "ids": body.ids},
        )
    else:
        _execute(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = %(uid)s AND is_read = FALSE",
            {"uid": str(user.id)},
        )
    return {"ok": True}
