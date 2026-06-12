"""
db/connection.py
PostgreSQL helpers for the TravelBuddy canonical data schema.

Collectors should not create tables dynamically. Schema ownership belongs to
database/travel_buddy_db/01_schema.sql.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)


def get_conn():
    """Return a psycopg2 connection from environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "travel_buddy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", ""),
    )


def _json(value: Any) -> Json:
    if isinstance(value, str):
        try:
            return Json(json.loads(value))
        except json.JSONDecodeError:
            return Json(value)
    return Json(value if value is not None else {})


def _json_list(value: Any) -> Json:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return Json(parsed if isinstance(parsed, list) else [parsed])
        except json.JSONDecodeError:
            return Json([value])
    return Json(value if value is not None else [])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def expires_in(hours: int = 0, minutes: int = 0, days: int = 0) -> datetime:
    return utcnow() + timedelta(days=days, hours=hours, minutes=minutes)


# ---------------------------------------------------------------------------
# Destinations, hotels, POI
# ---------------------------------------------------------------------------

def upsert_destination(conn, row: dict) -> str:
    """Upsert a city/destination and return its UUID."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO destinations
            (name, slug, city, province, country_code, country_name, iata_city_code,
             description, lat, lng, timezone, tags, best_months, avg_rating,
             review_count, is_seeded, popularity_rank, source, updated_at)
        VALUES
            (%(name)s, %(slug)s, %(city)s, %(province)s, %(country_code)s,
             %(country_name)s, %(iata_city_code)s, %(description)s, %(lat)s,
             %(lng)s, %(timezone)s, %(tags)s, %(best_months)s, %(avg_rating)s,
             %(review_count)s, %(is_seeded)s, %(popularity_rank)s, %(source)s, NOW())
        ON CONFLICT (slug) DO UPDATE SET
            name = EXCLUDED.name,
            city = EXCLUDED.city,
            province = EXCLUDED.province,
            country_code = EXCLUDED.country_code,
            country_name = EXCLUDED.country_name,
            iata_city_code = EXCLUDED.iata_city_code,
            description = COALESCE(NULLIF(EXCLUDED.description, ''), destinations.description),
            lat = COALESCE(EXCLUDED.lat, destinations.lat),
            lng = COALESCE(EXCLUDED.lng, destinations.lng),
            timezone = EXCLUDED.timezone,
            tags = EXCLUDED.tags,
            best_months = EXCLUDED.best_months,
            avg_rating = EXCLUDED.avg_rating,
            review_count = EXCLUDED.review_count,
            source = EXCLUDED.source,
            updated_at = NOW()
        RETURNING id
        """,
        {
            "name": row.get("name", ""),
            "slug": row.get("slug", ""),
            "city": row.get("city", row.get("name", "")),
            "province": row.get("province"),
            "country_code": row.get("country_code", "VN"),
            "country_name": row.get("country_name", row.get("country", "Vietnam")),
            "iata_city_code": row.get("iata_city_code"),
            "description": row.get("description", ""),
            "lat": row.get("lat"),
            "lng": row.get("lng", row.get("lon")),
            "timezone": row.get("timezone", "Asia/Ho_Chi_Minh"),
            "tags": _json_list(row.get("tags", [])),
            "best_months": _json_list(row.get("best_months", [])),
            "avg_rating": row.get("avg_rating", 0),
            "review_count": row.get("review_count", 0),
            "is_seeded": row.get("is_seeded", False),
            "popularity_rank": row.get("popularity_rank"),
            "source": row.get("source", "api"),
        },
    )
    dest_id = str(cur.fetchone()[0])
    conn.commit()
    return dest_id


def upsert_destination_image(conn, row: dict) -> str:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO destination_images
            (destination_id, url, thumbnail_url, provider, provider_ref, author_name,
             author_url, license, attribution, width, height, sort_order, is_primary)
        VALUES
            (%(destination_id)s, %(url)s, %(thumbnail_url)s, %(provider)s,
             %(provider_ref)s, %(author_name)s, %(author_url)s, %(license)s,
             %(attribution)s, %(width)s, %(height)s, %(sort_order)s, %(is_primary)s)
        RETURNING id
        """,
        {
            "destination_id": row["destination_id"],
            "url": row["url"],
            "thumbnail_url": row.get("thumbnail_url"),
            "provider": row.get("provider", "manual"),
            "provider_ref": row.get("provider_ref"),
            "author_name": row.get("author_name"),
            "author_url": row.get("author_url"),
            "license": row.get("license"),
            "attribution": row.get("attribution"),
            "width": row.get("width"),
            "height": row.get("height"),
            "sort_order": row.get("sort_order", 0),
            "is_primary": row.get("is_primary", False),
        },
    )
    image_id = str(cur.fetchone()[0])
    conn.commit()
    return image_id


def upsert_hotel(conn, row: dict) -> str:
    """Upsert hotel metadata. Rates live in hotel_rate_snapshots."""
    cur = conn.cursor()
    provider = row.get("provider", "manual")
    provider_property_id = row.get("provider_property_id")
    if provider and provider_property_id:
        cur.execute(
            """
            SELECT id
            FROM hotels
            WHERE provider = %s AND provider_property_id = %s
            LIMIT 1
            """,
            (provider, provider_property_id),
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                """
                UPDATE hotels
                SET name = %(name)s,
                    stars = %(stars)s,
                    property_type = %(property_type)s,
                    description = COALESCE(NULLIF(%(description)s, ''), description),
                    address = COALESCE(NULLIF(%(address)s, ''), address),
                    area = COALESCE(NULLIF(%(area)s, ''), area),
                    lat = COALESCE(%(lat)s, lat),
                    lng = COALESCE(%(lng)s, lng),
                    amenities = %(amenities)s,
                    avg_rating = %(avg_rating)s,
                    review_count = %(review_count)s,
                    deep_link_url = COALESCE(%(deep_link_url)s, deep_link_url),
                    source = %(source)s,
                    updated_at = NOW()
                WHERE id = %(id)s
                """,
                {
                    "id": existing[0],
                    "name": row.get("name", ""),
                    "stars": row.get("stars"),
                    "property_type": row.get("property_type", "hotel"),
                    "description": row.get("description", ""),
                    "address": row.get("address", ""),
                    "area": row.get("area"),
                    "lat": row.get("lat"),
                    "lng": row.get("lng", row.get("lon")),
                    "amenities": _json_list(row.get("amenities", [])),
                    "avg_rating": row.get("avg_rating", 0),
                    "review_count": row.get("review_count", 0),
                    "deep_link_url": row.get("deep_link_url"),
                    "source": row.get("source", "api"),
                },
            )
            conn.commit()
            return str(existing[0])

    cur.execute(
        """
        INSERT INTO hotels
            (destination_id, name, slug, stars, property_type, description, address,
             area, lat, lng, amenities, checkin_time, checkout_time, avg_rating,
             review_count, provider, provider_property_id, deep_link_url,
             is_seeded, source, updated_at)
        VALUES
            (%(destination_id)s, %(name)s, %(slug)s, %(stars)s, %(property_type)s,
             %(description)s, %(address)s, %(area)s, %(lat)s, %(lng)s, %(amenities)s,
             %(checkin_time)s, %(checkout_time)s, %(avg_rating)s, %(review_count)s,
             %(provider)s, %(provider_property_id)s, %(deep_link_url)s,
             %(is_seeded)s, %(source)s, NOW())
        ON CONFLICT (destination_id, slug) DO UPDATE SET
            name = EXCLUDED.name,
            stars = EXCLUDED.stars,
            property_type = EXCLUDED.property_type,
            description = COALESCE(NULLIF(EXCLUDED.description, ''), hotels.description),
            address = COALESCE(NULLIF(EXCLUDED.address, ''), hotels.address),
            area = COALESCE(NULLIF(EXCLUDED.area, ''), hotels.area),
            lat = COALESCE(EXCLUDED.lat, hotels.lat),
            lng = COALESCE(EXCLUDED.lng, hotels.lng),
            amenities = EXCLUDED.amenities,
            avg_rating = EXCLUDED.avg_rating,
            review_count = EXCLUDED.review_count,
            provider = EXCLUDED.provider,
            provider_property_id = EXCLUDED.provider_property_id,
            deep_link_url = COALESCE(EXCLUDED.deep_link_url, hotels.deep_link_url),
            source = EXCLUDED.source,
            updated_at = NOW()
        RETURNING id
        """,
        {
            "destination_id": row["destination_id"],
            "name": row.get("name", ""),
            "slug": row.get("slug", ""),
            "stars": row.get("stars"),
            "property_type": row.get("property_type", "hotel"),
            "description": row.get("description", ""),
            "address": row.get("address", ""),
            "area": row.get("area"),
            "lat": row.get("lat"),
            "lng": row.get("lng", row.get("lon")),
            "amenities": _json_list(row.get("amenities", [])),
            "checkin_time": row.get("checkin_time"),
            "checkout_time": row.get("checkout_time"),
            "avg_rating": row.get("avg_rating", 0),
            "review_count": row.get("review_count", 0),
            "provider": row.get("provider", "manual"),
            "provider_property_id": row.get("provider_property_id"),
            "deep_link_url": row.get("deep_link_url"),
            "is_seeded": row.get("is_seeded", False),
            "source": row.get("source", "api"),
        },
    )
    hotel_id = str(cur.fetchone()[0])
    conn.commit()
    return hotel_id


def upsert_hotel_image(conn, row: dict) -> str:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id
        FROM hotel_images
        WHERE hotel_id = %(hotel_id)s AND url = %(url)s
        LIMIT 1
        """,
        {"hotel_id": row["hotel_id"], "url": row["url"]},
    )
    existing = cur.fetchone()
    if existing:
        cur.execute(
            """
            UPDATE hotel_images
            SET thumbnail_url = %(thumbnail_url)s,
                provider = %(provider)s,
                provider_ref = %(provider_ref)s,
                license = %(license)s,
                attribution = %(attribution)s,
                sort_order = %(sort_order)s,
                is_primary = %(is_primary)s
            WHERE id = %(id)s
            """,
            {
                "id": existing[0],
                "thumbnail_url": row.get("thumbnail_url"),
                "provider": row.get("provider", "manual"),
                "provider_ref": row.get("provider_ref"),
                "license": row.get("license"),
                "attribution": row.get("attribution"),
                "sort_order": row.get("sort_order", 0),
                "is_primary": row.get("is_primary", False),
            },
        )
        conn.commit()
        return str(existing[0])

    cur.execute(
        """
        INSERT INTO hotel_images
            (hotel_id, url, thumbnail_url, provider, provider_ref, license,
             attribution, sort_order, is_primary)
        VALUES
            (%(hotel_id)s, %(url)s, %(thumbnail_url)s, %(provider)s,
             %(provider_ref)s, %(license)s, %(attribution)s,
             %(sort_order)s, %(is_primary)s)
        RETURNING id
        """,
        {
            "hotel_id": row["hotel_id"],
            "url": row["url"],
            "thumbnail_url": row.get("thumbnail_url"),
            "provider": row.get("provider", "manual"),
            "provider_ref": row.get("provider_ref"),
            "license": row.get("license"),
            "attribution": row.get("attribution"),
            "sort_order": row.get("sort_order", 0),
            "is_primary": row.get("is_primary", False),
        },
    )
    image_id = str(cur.fetchone()[0])
    conn.commit()
    return image_id


def upsert_hotel_rate_snapshot(conn, row: dict) -> str:
    cur = conn.cursor()
    if row.get("provider_rate_id"):
        cur.execute(
            """
            SELECT id
            FROM hotel_rate_snapshots
            WHERE hotel_id = %(hotel_id)s
              AND checkin_date = %(checkin_date)s
              AND checkout_date = %(checkout_date)s
              AND adults = %(adults)s
              AND rooms = %(rooms)s
              AND provider = %(provider)s
              AND provider_rate_id = %(provider_rate_id)s
            ORDER BY fetched_at DESC
            LIMIT 1
            """,
            {
                "hotel_id": row["hotel_id"],
                "checkin_date": row["checkin_date"],
                "checkout_date": row["checkout_date"],
                "adults": row.get("adults", 2),
                "rooms": row.get("rooms", 1),
                "provider": row.get("provider", "booking"),
                "provider_rate_id": row.get("provider_rate_id"),
            },
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                """
                UPDATE hotel_rate_snapshots
                SET room_name = %(room_name)s,
                    refundable = %(refundable)s,
                    breakfast_included = %(breakfast_included)s,
                    price_amount = %(price_amount)s,
                    currency = %(currency)s,
                    taxes_and_fees = %(taxes_and_fees)s,
                    deep_link_url = %(deep_link_url)s,
                    fetched_at = NOW(),
                    expires_at = %(expires_at)s,
                    raw = %(raw)s
                WHERE id = %(id)s
                """,
                {
                    "id": existing[0],
                    "room_name": row.get("room_name"),
                    "refundable": row.get("refundable"),
                    "breakfast_included": row.get("breakfast_included"),
                    "price_amount": row.get("price_amount", 0),
                    "currency": row.get("currency", "VND"),
                    "taxes_and_fees": row.get("taxes_and_fees"),
                    "deep_link_url": row.get("deep_link_url"),
                    "expires_at": row.get("expires_at", expires_in(hours=24)),
                    "raw": _json(row.get("raw", {})),
                },
            )
            conn.commit()
            return str(existing[0])

    cur.execute(
        """
        INSERT INTO hotel_rate_snapshots
            (hotel_id, checkin_date, checkout_date, adults, rooms, room_name,
             refundable, breakfast_included, price_amount, currency, taxes_and_fees,
             provider, provider_rate_id, deep_link_url, fetched_at, expires_at, raw)
        VALUES
            (%(hotel_id)s, %(checkin_date)s, %(checkout_date)s, %(adults)s,
             %(rooms)s, %(room_name)s, %(refundable)s, %(breakfast_included)s,
             %(price_amount)s, %(currency)s, %(taxes_and_fees)s, %(provider)s,
             %(provider_rate_id)s, %(deep_link_url)s, NOW(), %(expires_at)s, %(raw)s)
        RETURNING id
        """,
        {
            "hotel_id": row["hotel_id"],
            "checkin_date": row["checkin_date"],
            "checkout_date": row["checkout_date"],
            "adults": row.get("adults", 2),
            "rooms": row.get("rooms", 1),
            "room_name": row.get("room_name"),
            "refundable": row.get("refundable"),
            "breakfast_included": row.get("breakfast_included"),
            "price_amount": row.get("price_amount", 0),
            "currency": row.get("currency", "VND"),
            "taxes_and_fees": row.get("taxes_and_fees"),
            "provider": row.get("provider", "booking"),
            "provider_rate_id": row.get("provider_rate_id"),
            "deep_link_url": row.get("deep_link_url"),
            "expires_at": row.get("expires_at", expires_in(hours=24)),
            "raw": _json(row.get("raw", {})),
        },
    )
    rate_id = str(cur.fetchone()[0])
    conn.commit()
    return rate_id


def upsert_hotel_offer_cache(
    conn,
    cache_key: str,
    destination_id: str | None,
    request: dict,
    response: dict,
    provider: str = "booking",
    ttl_minutes: int = 30,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO hotel_offer_cache
            (cache_key, destination_id, request, response, provider, fetched_at, expires_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), %s)
        ON CONFLICT (cache_key) DO UPDATE SET
            destination_id = EXCLUDED.destination_id,
            request = EXCLUDED.request,
            response = EXCLUDED.response,
            provider = EXCLUDED.provider,
            fetched_at = NOW(),
            expires_at = EXCLUDED.expires_at
        """,
        (cache_key, destination_id, Json(request), Json(response), provider, expires_in(minutes=ttl_minutes)),
    )
    conn.commit()


def upsert_poi(conn, row: dict) -> str:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO pois
            (destination_id, name, slug, category, kinds, description, lat, lng,
             address, estimated_duration_min, entrance_fee_amount, currency,
             avg_rating, source, source_ref, wikidata_id, wikipedia_url,
             is_seeded, fetched_at, raw)
        VALUES
            (%(destination_id)s, %(name)s, %(slug)s, %(category)s, %(kinds)s,
             %(description)s, %(lat)s, %(lng)s, %(address)s,
             %(estimated_duration_min)s, %(entrance_fee_amount)s, %(currency)s,
             %(avg_rating)s, %(source)s, %(source_ref)s, %(wikidata_id)s,
             %(wikipedia_url)s, %(is_seeded)s, NOW(), %(raw)s)
        ON CONFLICT (destination_id, slug) DO UPDATE SET
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            kinds = EXCLUDED.kinds,
            description = COALESCE(NULLIF(EXCLUDED.description, ''), pois.description),
            lat = COALESCE(EXCLUDED.lat, pois.lat),
            lng = COALESCE(EXCLUDED.lng, pois.lng),
            address = COALESCE(NULLIF(EXCLUDED.address, ''), pois.address),
            avg_rating = EXCLUDED.avg_rating,
            source = EXCLUDED.source,
            source_ref = EXCLUDED.source_ref,
            wikidata_id = EXCLUDED.wikidata_id,
            wikipedia_url = EXCLUDED.wikipedia_url,
            raw = EXCLUDED.raw,
            updated_at = NOW()
        RETURNING id
        """,
        {
            "destination_id": row.get("destination_id"),
            "name": row.get("name", ""),
            "slug": row.get("slug", ""),
            "category": row.get("category"),
            "kinds": _json_list(row.get("kinds", [])),
            "description": row.get("description", ""),
            "lat": row.get("lat"),
            "lng": row.get("lng", row.get("lon")),
            "address": row.get("address"),
            "estimated_duration_min": row.get("estimated_duration_min"),
            "entrance_fee_amount": row.get("entrance_fee_amount"),
            "currency": row.get("currency", "VND"),
            "avg_rating": row.get("avg_rating", 0),
            "source": row.get("source", "opentripmap"),
            "source_ref": row.get("source_ref"),
            "wikidata_id": row.get("wikidata_id"),
            "wikipedia_url": row.get("wikipedia_url"),
            "is_seeded": row.get("is_seeded", False),
            "raw": _json(row.get("raw", {})),
        },
    )
    poi_id = str(cur.fetchone()[0])
    conn.commit()
    return poi_id


def upsert_poi_image(conn, row: dict) -> str:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO poi_images
            (poi_id, url, thumbnail_url, provider, provider_ref, license, attribution, sort_order)
        VALUES
            (%(poi_id)s, %(url)s, %(thumbnail_url)s, %(provider)s, %(provider_ref)s,
             %(license)s, %(attribution)s, %(sort_order)s)
        RETURNING id
        """,
        {
            "poi_id": row["poi_id"],
            "url": row["url"],
            "thumbnail_url": row.get("thumbnail_url"),
            "provider": row.get("provider", "manual"),
            "provider_ref": row.get("provider_ref"),
            "license": row.get("license"),
            "attribution": row.get("attribution"),
            "sort_order": row.get("sort_order", 0),
        },
    )
    image_id = str(cur.fetchone()[0])
    conn.commit()
    return image_id


def get_dest_id(conn, slug: str) -> str | None:
    cur = conn.cursor()
    cur.execute("SELECT id FROM destinations WHERE slug = %s", (slug,))
    row = cur.fetchone()
    return str(row[0]) if row else None


def get_seeded_destinations(conn) -> list[dict]:
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT id, name, slug, lat, lng, timezone, country_code
        FROM destinations
        WHERE lat IS NOT NULL AND lng IS NOT NULL
        ORDER BY COALESCE(popularity_rank, 999), name
        """
    )
    return [dict(r) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# Flights
# ---------------------------------------------------------------------------

def get_or_create_flight_route(
    conn,
    origin_iata: str,
    destination_iata: str,
    destination_slug: str | None = None,
    is_popular_seed: bool = False,
    popularity_rank: int | None = None,
) -> str:
    destination_id = get_dest_id(conn, destination_slug) if destination_slug else None
    route_key = f"{origin_iata}-{destination_iata}"
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO flight_routes
            (origin_iata, destination_iata, route_key, destination_id,
             is_domestic, is_popular_seed, popularity_rank)
        VALUES (%s, %s, %s, %s, TRUE, %s, %s)
        ON CONFLICT (origin_iata, destination_iata) DO UPDATE SET
            destination_id = COALESCE(EXCLUDED.destination_id, flight_routes.destination_id),
            is_popular_seed = flight_routes.is_popular_seed OR EXCLUDED.is_popular_seed,
            popularity_rank = COALESCE(flight_routes.popularity_rank, EXCLUDED.popularity_rank)
        RETURNING id
        """,
        (origin_iata, destination_iata, route_key, destination_id, is_popular_seed, popularity_rank),
    )
    route_id = str(cur.fetchone()[0])
    conn.commit()
    return route_id


def get_route_id(conn, origin_iata: str, destination_iata: str) -> str | None:
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM flight_routes WHERE origin_iata = %s AND destination_iata = %s",
        (origin_iata, destination_iata),
    )
    row = cur.fetchone()
    return str(row[0]) if row else None


def upsert_flight_price_snapshot(conn, row: dict) -> str:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO flight_price_snapshots
            (route_id, airline_iata, airline_name, flight_number, cabin_class,
             departure_date, depart_at, arrive_at, duration_minutes, stops,
             price_amount, currency, seats_left, booking_url, source, source_ref,
             fetched_at, expires_at, raw)
        VALUES
            (%(route_id)s, %(airline_iata)s, %(airline_name)s, %(flight_number)s,
             %(cabin_class)s, %(departure_date)s, %(depart_at)s, %(arrive_at)s,
             %(duration_minutes)s, %(stops)s, %(price_amount)s, %(currency)s,
             %(seats_left)s, %(booking_url)s, %(source)s, %(source_ref)s,
             NOW(), %(expires_at)s, %(raw)s)
        RETURNING id
        """,
        {
            "route_id": row["route_id"],
            "airline_iata": row.get("airline_iata"),
            "airline_name": row.get("airline_name", row.get("airline", "")),
            "flight_number": row.get("flight_number", row.get("flight_no")),
            "cabin_class": row.get("cabin_class", "economy"),
            "departure_date": row.get("departure_date"),
            "depart_at": row.get("depart_at"),
            "arrive_at": row.get("arrive_at"),
            "duration_minutes": row.get("duration_minutes"),
            "stops": row.get("stops", 0),
            "price_amount": row.get("price_amount", row.get("price", 0)),
            "currency": row.get("currency", "VND"),
            "seats_left": row.get("seats_left"),
            "booking_url": row.get("booking_url"),
            "source": row.get("source", "api"),
            "source_ref": row.get("source_ref"),
            "expires_at": row.get("expires_at", expires_in(hours=24)),
            "raw": _json(row.get("raw", {})),
        },
    )
    snapshot_id = str(cur.fetchone()[0])
    conn.commit()
    return snapshot_id


def upsert_flight_offer_cache(
    conn,
    cache_key: str,
    route_id: str | None,
    request: dict,
    response: dict,
    ttl_minutes: int = 15,
    source: str = "amadeus",
):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO flight_offer_cache
            (cache_key, route_id, request, response, source, fetched_at, expires_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), %s)
        ON CONFLICT (cache_key) DO UPDATE SET
            route_id = EXCLUDED.route_id,
            request = EXCLUDED.request,
            response = EXCLUDED.response,
            source = EXCLUDED.source,
            fetched_at = NOW(),
            expires_at = EXCLUDED.expires_at
        """,
        (cache_key, route_id, Json(request), Json(response), source, expires_in(minutes=ttl_minutes)),
    )
    conn.commit()


# Backward-compatible wrapper for old callers. Prefer upsert_flight_price_snapshot.
def upsert_flight(conn, row: dict) -> str:
    route_id = row.get("route_id") or get_or_create_flight_route(
        conn,
        row.get("origin"),
        row.get("destination"),
    )
    return upsert_flight_price_snapshot(
        conn,
        {
            **row,
            "route_id": route_id,
            "airline_name": row.get("airline", row.get("airline_name", "")),
            "flight_number": row.get("flight_no", row.get("flight_number")),
            "departure_date": str(row.get("depart_at", ""))[:10] or row.get("departure_date"),
            "price_amount": row.get("price", row.get("price_amount", 0)),
            "expires_at": row.get("expires_at", expires_in(hours=24)),
        },
    )


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

def save_weather_forecast(
    conn,
    destination: dict,
    raw: dict,
    daily_rows: list[dict],
    ttl_hours: int = 6,
    source: str = "open-meteo",
) -> str:
    cache_key = f"{destination['slug']}:{destination['lat']}:{destination['lng']}:16:{destination.get('timezone', 'Asia/Ho_Chi_Minh')}"
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO weather_cache
            (destination_id, cache_key, lat, lng, timezone, forecast_days,
             source, fetched_at, expires_at, raw)
        VALUES (%s, %s, %s, %s, %s, 16, %s, NOW(), %s, %s)
        ON CONFLICT (cache_key) DO UPDATE SET
            destination_id = EXCLUDED.destination_id,
            lat = EXCLUDED.lat,
            lng = EXCLUDED.lng,
            timezone = EXCLUDED.timezone,
            forecast_days = EXCLUDED.forecast_days,
            source = EXCLUDED.source,
            fetched_at = NOW(),
            expires_at = EXCLUDED.expires_at,
            raw = EXCLUDED.raw
        RETURNING id
        """,
        (
            destination["id"],
            cache_key,
            destination["lat"],
            destination["lng"],
            destination.get("timezone", "Asia/Ho_Chi_Minh"),
            source,
            expires_in(hours=ttl_hours),
            Json(raw),
        ),
    )
    cache_id = str(cur.fetchone()[0])

    cur.execute("DELETE FROM weather_daily_forecasts WHERE weather_cache_id = %s", (cache_id,))
    for row in daily_rows:
        cur.execute(
            """
            INSERT INTO weather_daily_forecasts
                (weather_cache_id, destination_id, forecast_date, weather_code,
                 temp_max_c, temp_min_c, precipitation_sum_mm,
                 precipitation_probability_max, wind_speed_max_kmh, travel_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                cache_id,
                destination["id"],
                row.get("date"),
                row.get("weather_code"),
                row.get("temp_max_c"),
                row.get("temp_min_c"),
                row.get("precipitation_sum_mm"),
                row.get("precipitation_probability_max"),
                row.get("wind_speed_max_kmh"),
                row.get("travel_score"),
            ),
        )
    conn.commit()
    return cache_id


# ---------------------------------------------------------------------------
# Exchange rates, countries
# ---------------------------------------------------------------------------

def upsert_exchange_rate(conn, row: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO exchange_rate_cache
            (base_currency, target_currency, rate, rate_date, source, fetched_at, expires_at, raw)
        VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
        ON CONFLICT (base_currency, target_currency, rate_date) DO UPDATE SET
            rate = EXCLUDED.rate,
            source = EXCLUDED.source,
            fetched_at = NOW(),
            expires_at = EXCLUDED.expires_at,
            raw = EXCLUDED.raw
        """,
        (
            row["base_currency"],
            row["target_currency"],
            row["rate"],
            row["rate_date"],
            row.get("source", "frankfurter"),
            row.get("expires_at", expires_in(hours=1)),
            _json(row.get("raw", {})),
        ),
    )
    cur.execute(
        """
        INSERT INTO exchange_rate_history
            (rate_date, base_currency, target_currency, rate, source)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (rate_date, base_currency, target_currency) DO UPDATE SET
            rate = EXCLUDED.rate,
            source = EXCLUDED.source
        """,
        (
            row["rate_date"],
            row["base_currency"],
            row["target_currency"],
            row["rate"],
            row.get("source", "frankfurter"),
        ),
    )
    conn.commit()


def upsert_country(conn, country: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO countries
            (code, alpha3, name_en, name_vn, capital, region, subregion,
             population, area_km2, currencies, languages, timezones,
             flag_url, flag_svg, calling_code, source, fetched_at, raw)
        VALUES
            (%(code)s, %(alpha3)s, %(name_en)s, %(name_vn)s, %(capital)s,
             %(region)s, %(subregion)s, %(population)s, %(area_km2)s,
             %(currencies)s, %(languages)s, %(timezones)s,
             %(flag_url)s, %(flag_svg)s, %(calling_code)s,
             %(source)s, NOW(), %(raw)s)
        ON CONFLICT (code) DO UPDATE SET
            alpha3 = EXCLUDED.alpha3,
            name_en = EXCLUDED.name_en,
            name_vn = COALESCE(EXCLUDED.name_vn, countries.name_vn),
            capital = EXCLUDED.capital,
            region = EXCLUDED.region,
            subregion = EXCLUDED.subregion,
            population = EXCLUDED.population,
            area_km2 = EXCLUDED.area_km2,
            currencies = EXCLUDED.currencies,
            languages = EXCLUDED.languages,
            timezones = EXCLUDED.timezones,
            flag_url = EXCLUDED.flag_url,
            flag_svg = EXCLUDED.flag_svg,
            calling_code = EXCLUDED.calling_code,
            source = EXCLUDED.source,
            fetched_at = NOW(),
            updated_at = NOW(),
            raw = EXCLUDED.raw
        """,
        {
            "code": country["code"],
            "alpha3": country.get("alpha3"),
            "name_en": country.get("name_en", ""),
            "name_vn": country.get("name_vn"),
            "capital": country.get("capital"),
            "region": country.get("region"),
            "subregion": country.get("subregion"),
            "population": country.get("population"),
            "area_km2": country.get("area_km2"),
            "currencies": _json_list(country.get("currencies", [])),
            "languages": _json_list(country.get("languages", [])),
            "timezones": _json_list(country.get("timezones", [])),
            "flag_url": country.get("flag_url"),
            "flag_svg": country.get("flag_svg"),
            "calling_code": country.get("calling_code"),
            "source": country.get("source", "restcountries"),
            "raw": _json(country.get("raw", {})),
        },
    )
    conn.commit()


def upsert_visa_rule(conn, rule: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO country_visa_rules
            (passport_country_code, destination_country_code, visa_required,
             visa_type, max_stay_days, note, source_url, verified_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (passport_country_code, destination_country_code) DO UPDATE SET
            visa_required = EXCLUDED.visa_required,
            visa_type = EXCLUDED.visa_type,
            max_stay_days = EXCLUDED.max_stay_days,
            note = EXCLUDED.note,
            source_url = EXCLUDED.source_url,
            verified_at = EXCLUDED.verified_at,
            updated_at = NOW()
        """,
        (
            rule.get("passport_country_code", "VN"),
            rule["destination_country_code"],
            rule["visa_required"],
            rule.get("visa_type"),
            rule.get("max_stay_days"),
            rule.get("note"),
            rule.get("source_url"),
            rule.get("verified_at"),
        ),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------

def log_refresh_job(conn, job: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO data_refresh_jobs
            (job_name, provider, entity_type, status, started_at, finished_at,
             records_fetched, records_upserted, error_message, metadata)
        VALUES
            (%(job_name)s, %(provider)s, %(entity_type)s, %(status)s,
             %(started_at)s, %(finished_at)s, %(records_fetched)s,
             %(records_upserted)s, %(error_message)s, %(metadata)s)
        """,
        {
            "job_name": job.get("job_name", "unknown"),
            "provider": job.get("provider"),
            "entity_type": job.get("entity_type", "unknown"),
            "status": job.get("status", "success"),
            "started_at": job.get("started_at", utcnow()),
            "finished_at": job.get("finished_at", utcnow()),
            "records_fetched": job.get("records_fetched", 0),
            "records_upserted": job.get("records_upserted", 0),
            "error_message": job.get("error_message"),
            "metadata": _json(job.get("metadata", {})),
        },
    )
    conn.commit()


def summary(conn):
    """Print row counts for the canonical tables."""
    cur = conn.cursor()
    tables = [
        "destinations",
        "airports",
        "airlines",
        "flight_routes",
        "flight_price_snapshots",
        "hotels",
        "hotel_rate_snapshots",
        "weather_cache",
        "weather_daily_forecasts",
        "pois",
        "exchange_rate_cache",
        "countries",
        "packing_templates",
        "packing_template_items",
        "users",
        "trips",
        "reviews",
    ]
    print("\nTong ban ghi trong DB:")
    print("-" * 44)
    for tbl in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            print(f"  {tbl:<28} {cur.fetchone()[0]:>8} rows")
        except Exception as exc:
            print(f"  {tbl:<28} ERROR: {exc}")
            conn.rollback()
    print("-" * 44)
