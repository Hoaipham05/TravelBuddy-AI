"""
SerpApi Google Hotels collector.

This is the MVP-friendly hotel-rate provider when Booking/Agoda partner access
is not ready. It stores Google Hotels results into the canonical hotels,
hotel_images, hotel_rate_snapshots and hotel_offer_cache tables.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, datetime, timedelta
from typing import Any

from db.connection import (
    expires_in,
    get_seeded_destinations,
    upsert_hotel,
    upsert_hotel_image,
    upsert_hotel_offer_cache,
    upsert_hotel_rate_snapshot,
)
from utils.helpers import safe_get, slugify

log = logging.getLogger(__name__)

BASE_URL = "https://serpapi.com/search"


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stars(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        extracted = "".join(ch for ch in value if ch.isdigit() or ch == ".")
        return _number(extracted)
    return None


class SerpApiHotelsCollector:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.google_domain = os.getenv("SERPAPI_GOOGLE_DOMAIN", "google.com")
        self.gl = os.getenv("SERPAPI_GL", "vn")
        self.hl = os.getenv("SERPAPI_HL", "vi")
        if not self.api_key:
            raise ValueError("Missing SERPAPI_API_KEY")

    def search_hotels(self, destination: dict, checkin: str, checkout: str, adults: int = 2) -> dict | None:
        params = {
            "engine": "google_hotels",
            "api_key": self.api_key,
            "google_domain": self.google_domain,
            "q": f"{destination['name']} hotels",
            "check_in_date": checkin,
            "check_out_date": checkout,
            "adults": adults,
            "currency": "VND",
            "gl": self.gl,
            "hl": self.hl,
        }
        r = safe_get(BASE_URL, params=params, timeout=45, retries=3, delay=2)
        if not r:
            return None
        data = r.json()
        props = self._properties(data)
        log.info("SerpApi hotels %s %s-%s: %s properties", destination["slug"], checkin, checkout, len(props))
        self._save_raw(f"serpapi_hotels_{destination['slug']}_{checkin}_{checkout}", data)
        return data

    def _properties(self, raw: dict | None) -> list[dict]:
        if not raw:
            return []
        props = raw.get("properties")
        if isinstance(props, list):
            return [item for item in props if isinstance(item, dict)]
        return []

    def parse_hotel(self, item: dict, destination_id: str) -> dict | None:
        name = item.get("name")
        if not name:
            return None
        gps = item.get("gps_coordinates") if isinstance(item.get("gps_coordinates"), dict) else {}
        hotel_class = item.get("extracted_hotel_class", item.get("hotel_class"))
        return {
            "destination_id": destination_id,
            "name": name,
            "slug": slugify(name),
            "stars": _stars(hotel_class),
            "property_type": "hotel",
            "description": item.get("description"),
            "address": item.get("address"),
            "lat": gps.get("latitude"),
            "lng": gps.get("longitude"),
            "amenities": item.get("amenities") or [],
            "avg_rating": item.get("overall_rating") or 0,
            "review_count": item.get("reviews") or 0,
            "provider": "serpapi_google_hotels",
            "provider_property_id": item.get("property_token"),
            "deep_link_url": item.get("link") or item.get("serpapi_property_details_link"),
            "source": "serpapi_google_hotels",
        }

    def save_images(self, conn, hotel_id: str, item: dict) -> None:
        images = item.get("images") if isinstance(item.get("images"), list) else []
        thumbnail = item.get("thumbnail")
        if thumbnail:
            images = [{"thumbnail": thumbnail, "original_image": thumbnail}, *images]
        seen = set()
        for idx, image in enumerate(images[:5]):
            url = image.get("original_image") or image.get("thumbnail")
            if not url or url in seen:
                continue
            seen.add(url)
            upsert_hotel_image(
                conn,
                {
                    "hotel_id": hotel_id,
                    "url": url,
                    "thumbnail_url": image.get("thumbnail"),
                    "provider": "serpapi_google_hotels",
                    "provider_ref": item.get("property_token"),
                    "license": "Google Hotels result",
                    "attribution": "Image URL returned by SerpApi Google Hotels",
                    "sort_order": idx,
                    "is_primary": idx == 0,
                },
            )

    def save_rates(self, conn, hotel_id: str, item: dict, checkin: str, checkout: str, adults: int) -> bool:
        # Lưu GIÁ MỖI ĐÊM (đúng cách Google Hotels hiển thị, đã gồm thuế/phí),
        # fallback extracted_price rồi tổng kỳ nghỉ nếu thiếu.
        rate_per_night = item.get("rate_per_night") if isinstance(item.get("rate_per_night"), dict) else {}
        total_rate = item.get("total_rate") if isinstance(item.get("total_rate"), dict) else {}
        amount = _number(
            rate_per_night.get("extracted_lowest")
            or item.get("extracted_price")
            or total_rate.get("extracted_lowest")
        )
        if amount is None:
            return False

        upsert_hotel_rate_snapshot(
            conn,
            {
                "hotel_id": hotel_id,
                "checkin_date": checkin,
                "checkout_date": checkout,
                "adults": adults,
                "rooms": 1,
                "room_name": "Google Hotels lowest available rate",
                "price_amount": amount,
                "currency": "VND",
                "provider": "serpapi_google_hotels",
                "provider_rate_id": item.get("property_token"),
                "deep_link_url": item.get("link") or item.get("serpapi_property_details_link"),
                "expires_at": expires_in(hours=24),
                "raw": item,
            },
        )
        return True

    def save_result_set(self, conn, destination: dict, raw: dict, checkin: str, checkout: str, adults: int) -> int:
        saved_rates = 0
        for item in self._properties(raw):
            hotel_row = self.parse_hotel(item, destination["id"])
            if not hotel_row:
                continue
            hotel_id = upsert_hotel(conn, hotel_row)
            self.save_images(conn, hotel_id, item)
            if self.save_rates(conn, hotel_id, item, checkin, checkout, adults):
                saved_rates += 1
        return saved_rates

    def _save_raw(self, name: str, data: dict):
        os.makedirs("evidence", exist_ok=True)
        path = os.path.join("evidence", f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "_meta": {
                        "source": "SerpApi Google Hotels",
                        "endpoint": BASE_URL,
                        "collected": datetime.now().isoformat(),
                    },
                    "data": data,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def run(self, conn):
        log.info("SerpApi Google Hotels collector started")
        destinations = get_seeded_destinations(conn)
        checkin = (date.today() + timedelta(days=30)).isoformat()
        checkout = (date.today() + timedelta(days=33)).isoformat()
        adults = int(os.getenv("HOTEL_SEARCH_ADULTS", "2"))
        total = 0

        for destination in destinations:
            raw = self.search_hotels(destination, checkin, checkout, adults=adults)
            if not raw:
                continue
            cache_key = f"serpapi_hotels:{destination['slug']}:{checkin}:{checkout}:{adults}:1"
            upsert_hotel_offer_cache(
                conn,
                cache_key,
                destination["id"],
                {
                    "q": f"{destination['name']} hotels",
                    "checkin": checkin,
                    "checkout": checkout,
                    "adults": adults,
                    "rooms": 1,
                    "currency": "VND",
                },
                raw,
                provider="serpapi_google_hotels",
                ttl_minutes=30,
            )
            saved = self.save_result_set(conn, destination, raw, checkin, checkout, adults)
            total += saved
            log.info("SerpApi hotel rates %s: %s rows", destination["slug"], saved)
            time.sleep(1.0)

        log.info("SerpApi Google Hotels collector finished: %s rate snapshots", total)
