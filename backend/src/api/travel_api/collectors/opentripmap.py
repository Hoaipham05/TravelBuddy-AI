"""
collectors/opentripmap.py
OpenTripMap POI collector.

Strategy:
  - destinations table stores city-level destinations only.
  - pois table stores attractions/places with GPS for Trip Builder clustering.
  - hotel metadata may be supplemented from accomodations, but rates are not
    generated here.
"""

from __future__ import annotations

import json
import logging
import os
import time

from utils.helpers import safe_get, slugify
from db.connection import get_dest_id, upsert_destination, upsert_hotel, upsert_poi, upsert_poi_image

log = logging.getLogger(__name__)

BASE = "https://api.opentripmap.com/0.1"

CITIES = [
    {"name": "Da Nang", "slug": "da-nang", "country": "VN", "vn_name": "Đà Nẵng"},
    {"name": "Hanoi", "slug": "ha-noi", "country": "VN", "vn_name": "Hà Nội"},
    {"name": "Ho Chi Minh City", "slug": "ho-chi-minh", "country": "VN", "vn_name": "TP.HCM"},
    {"name": "Hoi An", "slug": "hoi-an", "country": "VN", "vn_name": "Hội An"},
    {"name": "Phu Quoc", "slug": "phu-quoc", "country": "VN", "vn_name": "Phú Quốc"},
    {"name": "Nha Trang", "slug": "nha-trang", "country": "VN", "vn_name": "Nha Trang"},
    {"name": "Da Lat", "slug": "da-lat", "country": "VN", "vn_name": "Đà Lạt"},
    {"name": "Hue", "slug": "hue", "country": "VN", "vn_name": "Huế"},
    {"name": "Ha Long", "slug": "ha-long", "country": "VN", "vn_name": "Hạ Long"},
    {"name": "Sa Pa", "slug": "sapa", "country": "VN", "vn_name": "Sapa"},
]

ATTRACTION_KINDS = "interesting_places,cultural,historic,natural,beaches,amusements,foods"
HOTEL_KINDS = "accomodations"  # OpenTripMap spelling


class OpenTripMapCollector:
    def __init__(self):
        self.key = os.getenv("OPENTRIPMAP_KEY")
        self.lang = os.getenv("OPENTRIPMAP_LANG", "vi")
        if not self.key:
            raise ValueError("Missing OPENTRIPMAP_KEY. Register at https://dev.opentripmap.org/product")

    @property
    def places_base(self) -> str:
        return f"{BASE}/{self.lang}/places"

    def _params(self, extra: dict | None = None) -> dict:
        params = {"apikey": self.key}
        if extra:
            params.update(extra)
        return params

    def geoname(self, city_name: str, country: str) -> dict | None:
        r = safe_get(
            f"{self.places_base}/geoname",
            params=self._params({"name": city_name, "country": country}),
        )
        if not r:
            return None
        return r.json()

    def radius_search(self, lat: float, lon: float, kinds: str, radius: int, limit: int) -> list[dict]:
        r = safe_get(
            f"{self.places_base}/radius",
            params=self._params(
                {
                    "lat": lat,
                    "lon": lon,
                    "radius": radius,
                    "kinds": kinds,
                    "limit": limit,
                    "format": "json",
                    "rate": 2,
                }
            ),
        )
        if not r:
            return []
        data = r.json()
        return data if isinstance(data, list) else []

    def place_detail(self, xid: str) -> dict | None:
        r = safe_get(f"{self.places_base}/xid/{xid}", params=self._params())
        if not r:
            return None
        time.sleep(0.25)
        return r.json()

    def category_from_kinds(self, kinds: str) -> str:
        mapping = [
            ("beaches", "beach"),
            ("foods", "food"),
            ("historic", "historic"),
            ("cultural", "culture"),
            ("natural", "nature"),
            ("amusements", "amusement"),
            ("religion", "religion"),
            ("museums", "museum"),
        ]
        for needle, category in mapping:
            if needle in kinds:
                return category
        return "attraction"

    def parse_address(self, detail: dict) -> str:
        address = detail.get("address", {})
        if not isinstance(address, dict):
            return ""
        parts = [
            address.get("road"),
            address.get("suburb"),
            address.get("city"),
            address.get("state"),
            address.get("country"),
        ]
        return ", ".join(p for p in parts if p)

    def parse_poi(self, detail: dict, destination_id: str, city_slug: str) -> dict | None:
        name = (detail.get("name") or "").strip()
        if len(name) < 3:
            return None

        point = detail.get("point", {})
        kinds_str = detail.get("kinds", "")
        wiki = detail.get("wikipedia_extracts") or {}
        description = wiki.get("text") or detail.get("info", {}).get("descr", "")

        return {
            "destination_id": destination_id,
            "name": name,
            "slug": f"{slugify(name)}-{city_slug}",
            "category": self.category_from_kinds(kinds_str),
            "kinds": [k for k in kinds_str.split(",") if k],
            "description": description[:1200],
            "lat": point.get("lat"),
            "lng": point.get("lon"),
            "address": self.parse_address(detail),
            "estimated_duration_min": 90,
            "avg_rating": min(5.0, float(detail.get("rate", 0) or 0) / 2),
            "source": "opentripmap",
            "source_ref": detail.get("xid"),
            "wikidata_id": detail.get("wikidata"),
            "wikipedia_url": detail.get("wikipedia"),
            "raw": detail,
        }

    def parse_hotel(self, detail: dict, destination_id: str) -> dict | None:
        name = (detail.get("name") or "").strip()
        if len(name) < 3:
            return None

        point = detail.get("point", {})
        name_lower = name.lower()
        stars = 3
        if any(word in name_lower for word in ["palace", "luxury", "grand", "resort"]):
            stars = 4
        if "5 star" in name_lower:
            stars = 5
        if any(word in name_lower for word in ["hostel", "homestay"]):
            stars = 2

        return {
            "destination_id": destination_id,
            "name": name,
            "slug": slugify(name),
            "stars": stars,
            "property_type": "hotel",
            "description": (detail.get("wikipedia_extracts") or {}).get("text", "")[:1000],
            "address": self.parse_address(detail),
            "lat": point.get("lat"),
            "lng": point.get("lon"),
            "amenities": ["wifi"],
            "provider": "opentripmap",
            "provider_property_id": detail.get("xid"),
            "source": "opentripmap",
        }

    def ensure_destination(self, conn, city: dict, geo: dict) -> str:
        existing = get_dest_id(conn, city["slug"])
        if existing:
            return existing

        return upsert_destination(
            conn,
            {
                "name": city["vn_name"],
                "slug": city["slug"],
                "city": city["vn_name"],
                "country_code": city["country"],
                "country_name": "Vietnam" if city["country"] == "VN" else geo.get("country", ""),
                "lat": geo.get("lat"),
                "lng": geo.get("lon"),
                "tags": [],
                "best_months": [],
                "is_seeded": False,
                "source": "opentripmap",
            },
        )

    def collect_city(self, conn, city: dict):
        log.info("OpenTripMap city: %s", city["vn_name"])
        geo = self.geoname(city["name"], city["country"])
        if not geo or not geo.get("lat") or not geo.get("lon"):
            log.warning("OpenTripMap geoname failed: %s", city["name"])
            return {"pois": 0, "hotels": 0}

        lat = float(geo["lat"])
        lon = float(geo["lon"])
        destination_id = self.ensure_destination(conn, city, geo)

        pois_raw = self.radius_search(lat, lon, ATTRACTION_KINDS, radius=15000, limit=35)
        saved_pois = 0
        for item in pois_raw[:25]:
            xid = item.get("xid")
            if not xid:
                continue
            detail = self.place_detail(xid)
            if not detail:
                continue
            parsed = self.parse_poi(detail, destination_id, city["slug"])
            if not parsed:
                continue
            poi_id = upsert_poi(conn, parsed)
            if detail.get("image"):
                upsert_poi_image(
                    conn,
                    {
                        "poi_id": poi_id,
                        "url": detail["image"],
                        "provider": "opentripmap",
                        "provider_ref": xid,
                    },
                )
            saved_pois += 1

        hotels_raw = self.radius_search(lat, lon, HOTEL_KINDS, radius=10000, limit=12)
        saved_hotels = 0
        for item in hotels_raw[:8]:
            xid = item.get("xid")
            if not xid:
                continue
            detail = self.place_detail(xid)
            if not detail:
                continue
            parsed_hotel = self.parse_hotel(detail, destination_id)
            if not parsed_hotel:
                continue
            upsert_hotel(conn, parsed_hotel)
            saved_hotels += 1

        log.info("OpenTripMap %s: %s POIs, %s hotels", city["slug"], saved_pois, saved_hotels)
        time.sleep(0.8)
        return {"pois": saved_pois, "hotels": saved_hotels}

    def run(self, conn):
        log.info("OpenTripMap collector started")
        total_pois = 0
        total_hotels = 0
        for city in CITIES:
            result = self.collect_city(conn, city)
            total_pois += result["pois"]
            total_hotels += result["hotels"]
        log.info("OpenTripMap collector finished: %s POIs, %s hotels", total_pois, total_hotels)
