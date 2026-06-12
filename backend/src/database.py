"""
database.py
Structured travel-data lookup layer for agent tools.

No mock flight/hotel prices live here. The tools read PostgreSQL snapshots
when available; if the database has no fresh data, they return None so the
agent can fall back to official/realtime search paths instead of inventing
prices.
"""

from __future__ import annotations

import os

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:  # pragma: no cover - optional dependency in lightweight demos
    psycopg2 = None
    RealDictCursor = None


CITY_ALIASES: dict[str, str] = {
    "hn": "Hà Nội",
    "hanoi": "Hà Nội",
    "ha noi": "Hà Nội",
    "hà nội": "Hà Nội",
    "noi bai": "Hà Nội",
    "nội bài": "Hà Nội",

    "sg": "Hồ Chí Minh",
    "hcm": "Hồ Chí Minh",
    "tphcm": "Hồ Chí Minh",
    "saigon": "Hồ Chí Minh",
    "sài gòn": "Hồ Chí Minh",
    "ho chi minh": "Hồ Chí Minh",
    "ho chi minh city": "Hồ Chí Minh",
    "hồ chí minh": "Hồ Chí Minh",
    "tan son nhat": "Hồ Chí Minh",

    "dn": "Đà Nẵng",
    "danang": "Đà Nẵng",
    "da nang": "Đà Nẵng",
    "đà nẵng": "Đà Nẵng",

    "pq": "Phú Quốc",
    "phu quoc": "Phú Quốc",
    "phú quốc": "Phú Quốc",

    "nt": "Nha Trang",
    "nhatrang": "Nha Trang",
    "nha trang": "Nha Trang",
    "cam ranh": "Nha Trang",

    "dl": "Đà Lạt",
    "dalat": "Đà Lạt",
    "da lat": "Đà Lạt",
    "đà lạt": "Đà Lạt",
    "lien khuong": "Đà Lạt",

    "hue": "Huế",
    "huế": "Huế",
    "phu bai": "Huế",

    "hp": "Hải Phòng",
    "hai phong": "Hải Phòng",
    "hải phòng": "Hải Phòng",
    "cat bi": "Hải Phòng",

    "ha long": "Hạ Long",
    "hạ long": "Hạ Long",
    "van don": "Hạ Long",

    "sapa": "Sapa",
    "sa pa": "Sapa",
    "lào cai": "Sapa",
    "lao cai": "Sapa",

    "ct": "Cần Thơ",
    "can tho": "Cần Thơ",
    "cần thơ": "Cần Thơ",

    "ha giang": "Hà Giang",
    "hà giang": "Hà Giang",
    "hg": "Hà Giang",

    "dien bien": "Điện Biên",
    "điện biên": "Điện Biên",
    "dien bien phu": "Điện Biên",
    "điện biên phủ": "Điện Biên",
}


def normalize_city(name: str) -> str:
    key = (name or "").strip().lower()
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    for alias, standard in CITY_ALIASES.items():
        if alias in key:
            return standard
    return (name or "").strip().title()


def get_known_cities() -> list[str]:
    return sorted({*CITY_ALIASES.values(), *CITY_IATA.keys()})


AIRPORT_CITIES: set[str] = {
    "Hà Nội",
    "Hồ Chí Minh",
    "Đà Nẵng",
    "Phú Quốc",
    "Nha Trang",
    "Đà Lạt",
    "Hải Phòng",
    "Huế",
    "Hạ Long",
    "Cần Thơ",
    "Buôn Ma Thuột",
    "Pleiku",
    "Quy Nhơn",
    "Vinh",
    "Thanh Hoá",
    "Chu Lai",
    "Điện Biên",
}

CITY_IATA: dict[str, str] = {
    "Hà Nội": "HAN",
    "Hồ Chí Minh": "SGN",
    "Đà Nẵng": "DAD",
    "Phú Quốc": "PQC",
    "Nha Trang": "CXR",
    "Đà Lạt": "DLI",
    "Huế": "HUI",
    "Hạ Long": "VDO",
    "Hải Phòng": "HPH",
}


def _db_enabled() -> bool:
    return os.getenv("TRAVELBUDDY_DATA_MODE", "auto").strip().lower() in {"auto", "postgres", "db"}


def _db_conn():
    if not psycopg2 or not _db_enabled():
        return None
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            dbname=os.getenv("DB_NAME", "travel_buddy"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", ""),
            cursor_factory=RealDictCursor,
            connect_timeout=2,
        )
    except Exception:
        return None


def _time_label(value) -> str:
    if not value:
        return "?"
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")
    text = str(value)
    return text[11:16] if len(text) >= 16 else text


def _duration_label(minutes) -> str:
    minutes = int(minutes or 0)
    if not minutes:
        return "?"
    h, m = divmod(minutes, 60)
    return f"{h}h{m:02d}m" if m else f"{h}h"


def lookup_flights(origin: str, destination: str) -> list[dict] | None:
    """Return fresh flight snapshots from PostgreSQL, or None if unavailable."""
    origin_city = normalize_city(origin)
    destination_city = normalize_city(destination)
    origin_iata = CITY_IATA.get(origin_city)
    destination_iata = CITY_IATA.get(destination_city)
    if not origin_iata or not destination_iata:
        return None

    conn = _db_conn()
    if not conn:
        return None

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fps.airline_name,
                           fps.flight_number,
                           fps.depart_at,
                           fps.arrive_at,
                           fps.duration_minutes,
                           fps.price_amount,
                           fps.cabin_class
                    FROM flight_routes fr
                    JOIN flight_price_snapshots fps ON fps.route_id = fr.id
                    WHERE fr.origin_iata = %s
                      AND fr.destination_iata = %s
                      AND fps.expires_at > NOW()
                    ORDER BY fps.departure_date ASC, fps.price_amount ASC
                    LIMIT 12
                    """,
                    (origin_iata, destination_iata),
                )
                rows = cur.fetchall()
    except Exception:
        return None
    finally:
        conn.close()

    if not rows:
        return None

    return [
        {
            "airline": row["airline_name"],
            "flight_no": row.get("flight_number"),
            "departure": _time_label(row.get("depart_at")),
            "arrival": _time_label(row.get("arrive_at")),
            "duration": _duration_label(row.get("duration_minutes")),
            "price": int(row["price_amount"]),
            "class": row.get("cabin_class") or "economy",
            "source": "postgres_snapshot",
        }
        for row in rows
    ]


def lookup_hotels(
    city: str,
    max_price: int | None = None,
    min_stars: int | None = None,
) -> list[dict] | None:
    """Return hotels with fresh rate snapshots from PostgreSQL, or None."""
    city_std = normalize_city(city)
    conn = _db_conn()
    if not conn:
        return None

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT h.name,
                           h.stars,
                           h.area,
                           h.avg_rating,
                           h.amenities,
                           rate.price_amount
                    FROM destinations d
                    JOIN hotels h ON h.destination_id = d.id
                    JOIN LATERAL (
                        SELECT price_amount
                        FROM hotel_rate_snapshots
                        WHERE hotel_id = h.id
                          AND expires_at > NOW()
                        ORDER BY checkin_date ASC, price_amount ASC
                        LIMIT 1
                    ) rate ON TRUE
                    WHERE d.name = %(city)s
                      AND (%(min_stars)s IS NULL OR h.stars >= %(min_stars)s)
                      AND (%(max_price)s IS NULL OR rate.price_amount <= %(max_price)s)
                    ORDER BY rate.price_amount ASC, h.avg_rating DESC
                    LIMIT 10
                    """,
                    {
                        "city": city_std,
                        "min_stars": min_stars,
                        "max_price": max_price,
                    },
                )
                rows = cur.fetchall()
    except Exception:
        return None
    finally:
        conn.close()

    if not rows:
        return None

    return [
        {
            "name": row["name"],
            "stars": int(row.get("stars") or 0),
            "price_per_night": int(row["price_amount"]),
            "area": row.get("area") or "",
            "rating": float(row.get("avg_rating") or 0),
            "amenities": row.get("amenities") or [],
            "source": "postgres_snapshot",
        }
        for row in rows
    ]
