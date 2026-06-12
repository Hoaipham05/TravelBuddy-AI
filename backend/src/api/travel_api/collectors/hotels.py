"""
collectors/hotels.py
Booking.com Demand API collector for hotel metadata and rates.

This collector is optional. It requires partner credentials:
  BOOKING_API_TOKEN
  BOOKING_AFFILIATE_ID

Agoda partner endpoints are not publicly stable, so Agoda remains a deep-link
provider until partner documentation is available.
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Any

from utils.helpers import safe_post, slugify
from db.connection import (
    expires_in,
    get_seeded_destinations,
    upsert_hotel,
    upsert_hotel_offer_cache,
    upsert_hotel_rate_snapshot,
)

log = logging.getLogger(__name__)

BASE_URLS = {
    "production": "https://demandapi.booking.com/3.2",
    "sandbox": "https://demandapi-sandbox.booking.com/3.2",
}


class BookingDemandHotelCollector:
    def __init__(self):
        self.token = os.getenv("BOOKING_API_TOKEN")
        self.affiliate_id = os.getenv("BOOKING_AFFILIATE_ID")
        self.env = os.getenv("BOOKING_ENV", "sandbox")
        self.base_url = BASE_URLS.get(self.env, BASE_URLS["sandbox"])
        if not self.token or not self.affiliate_id:
            raise ValueError("Missing BOOKING_API_TOKEN / BOOKING_AFFILIATE_ID")

    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Affiliate-Id": self.affiliate_id,
            "Content-Type": "application/json",
        }

    def post(self, path: str, payload: dict) -> dict | None:
        r = safe_post(f"{self.base_url}{path}", json_body=payload, headers=self.headers(), timeout=30)
        if not r:
            return None
        return r.json()

    def _objects(self, raw: dict | list | None) -> list[dict]:
        if not raw:
            return []
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, dict)]
        data: Any = raw.get("data", raw)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            for key in ("objects", "results", "accommodations", "products"):
                value = data.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]
        for key in ("results", "accommodations", "products"):
            value = raw.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        return []

    def find_city_id(self, destination: dict) -> int | str | None:
        payload = {"query": destination["name"], "language": "vi-vn"}
        raw = self.post("/common/locations/cities", payload)
        for item in self._objects(raw):
            city_id = item.get("id") or item.get("city") or item.get("dest_id")
            if city_id:
                return city_id
        return None

    def search_accommodations(self, city_id: int | str, checkin: str, checkout: str) -> dict | None:
        payload = {
            "booker": {"country": "vn", "platform": "desktop"},
            "checkin": checkin,
            "checkout": checkout,
            "guests": {"number_of_adults": 2, "number_of_rooms": 1},
            "location": {"city": city_id},
            "currency": "VND",
            "extras": ["products", "extra_charges"],
        }
        return self.post("/accommodations/search", payload)

    def details(self, accommodation_ids: list[Any]) -> dict | None:
        if not accommodation_ids:
            return None
        payload = {
            "accommodations": accommodation_ids[:50],
            "extras": ["description", "facilities", "photos"],
            "languages": ["vi-vn", "en-gb"],
        }
        return self.post("/accommodations/details", payload)

    def parse_hotel(self, item: dict, destination_id: str) -> dict | None:
        hotel_id = item.get("id") or item.get("accommodation") or item.get("hotel_id")
        name = item.get("name") or item.get("accommodation_name") or item.get("property_name")
        if not name:
            return None

        location = item.get("location", {}) if isinstance(item.get("location"), dict) else {}
        coordinates = item.get("coordinates", {}) if isinstance(item.get("coordinates"), dict) else {}
        review = item.get("review_score", item.get("rating", {}))

        if isinstance(review, dict):
            avg_rating = review.get("score") or review.get("value") or 0
            review_count = review.get("count") or 0
        else:
            avg_rating = review or 0
            review_count = 0

        stars = item.get("stars") or item.get("star_rating")
        if isinstance(stars, dict):
            stars = stars.get("value")

        return {
            "destination_id": destination_id,
            "name": name,
            "slug": slugify(name),
            "stars": stars,
            "property_type": item.get("property_type", "hotel"),
            "description": item.get("description", ""),
            "address": item.get("address") or location.get("address"),
            "lat": item.get("latitude") or location.get("latitude") or coordinates.get("latitude"),
            "lng": item.get("longitude") or location.get("longitude") or coordinates.get("longitude"),
            "amenities": item.get("facilities") or item.get("amenities") or [],
            "avg_rating": avg_rating,
            "review_count": review_count,
            "provider": "booking",
            "provider_property_id": str(hotel_id) if hotel_id else None,
            "deep_link_url": item.get("url") or item.get("deep_link_url"),
            "source": "booking_demand",
        }

    def parse_price(self, item: dict) -> tuple[float | None, str]:
        price = item.get("price") or item.get("price_display") or item.get("gross_amount")
        currency = item.get("currency") or "VND"

        if isinstance(price, dict):
            currency = price.get("currency") or currency
            for key in ("gross_amount", "amount", "total", "book"):
                value = price.get(key)
                if isinstance(value, dict):
                    currency = value.get("currency") or currency
                    value = value.get("value") or value.get("amount")
                if value is not None:
                    try:
                        return float(value), currency
                    except (TypeError, ValueError):
                        pass
        if price is not None:
            try:
                return float(price), currency
            except (TypeError, ValueError):
                return None, currency
        return None, currency

    def save_result_set(self, conn, destination: dict, raw: dict, checkin: str, checkout: str) -> int:
        destination_id = destination["id"]
        saved = 0
        for item in self._objects(raw):
            hotel_row = self.parse_hotel(item, destination_id)
            if not hotel_row:
                continue
            hotel_id = upsert_hotel(conn, hotel_row)
            amount, currency = self.parse_price(item)
            if amount is not None:
                upsert_hotel_rate_snapshot(
                    conn,
                    {
                        "hotel_id": hotel_id,
                        "checkin_date": checkin,
                        "checkout_date": checkout,
                        "adults": 2,
                        "rooms": 1,
                        "room_name": item.get("room_name"),
                        "refundable": item.get("refundable"),
                        "breakfast_included": item.get("breakfast_included"),
                        "price_amount": amount,
                        "currency": currency,
                        "provider": "booking",
                        "provider_rate_id": str(item.get("product_id") or item.get("id") or ""),
                        "deep_link_url": item.get("url") or item.get("deep_link_url"),
                        "expires_at": expires_in(hours=24),
                        "raw": item,
                    },
                )
            saved += 1
        return saved

    def run(self, conn):
        log.info("Booking Demand hotel collector started")
        destinations = get_seeded_destinations(conn)
        checkin = (date.today() + timedelta(days=30)).isoformat()
        checkout = (date.today() + timedelta(days=33)).isoformat()
        total = 0

        for destination in destinations:
            city_id = self.find_city_id(destination)
            if not city_id:
                log.warning("Booking city id not found: %s", destination["slug"])
                continue

            raw = self.search_accommodations(city_id, checkin, checkout)
            if not raw:
                continue

            cache_key = f"booking:{destination['slug']}:{checkin}:{checkout}:2:1"
            upsert_hotel_offer_cache(
                conn,
                cache_key,
                destination["id"],
                {"city_id": city_id, "checkin": checkin, "checkout": checkout, "adults": 2, "rooms": 1},
                raw,
                provider="booking",
                ttl_minutes=30,
            )
            saved = self.save_result_set(conn, destination, raw, checkin, checkout)
            total += saved
            log.info("Booking hotels %s: %s rows", destination["slug"], saved)

        log.info("Booking Demand hotel collector finished: %s rows", total)
