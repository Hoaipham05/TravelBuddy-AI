"""
FastAPI router exposing TravelBuddy structured data from PostgreSQL.

These endpoints are intentionally data-first. AI can call them later, but the
frontend should be able to search/filter/compare without chat.
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

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
