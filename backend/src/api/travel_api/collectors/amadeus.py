"""
collectors/amadeus.py
Amadeus Flight Offers Search collector.

Strategy:
  - Top popular routes are stored in flight_routes.
  - Each API result is stored as a flight_price_snapshots row with TTL 24h
    for seeded route refresh.
  - Realtime endpoint code can reuse search_flights + flight_offer_cache TTL 15m.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta

from utils.helpers import safe_get, safe_post
from db.connection import (
    expires_in,
    get_or_create_flight_route,
    upsert_flight_offer_cache,
    upsert_flight_price_snapshot,
)

log = logging.getLogger(__name__)

URLS = {
    "test": "https://test.api.amadeus.com",
    "production": "https://api.amadeus.com",
}

AIRLINE_NAMES = {
    "VN": "Vietnam Airlines",
    "VJ": "VietJet Air",
    "QH": "Bamboo Airways",
}

IATA_SLUG = {
    "HAN": "ha-noi",
    "SGN": "ho-chi-minh",
    "DAD": "da-nang",
    "PQC": "phu-quoc",
    "CXR": "nha-trang",
    "DLI": "da-lat",
    "HUI": "hue",
    "VDO": "ha-long",
}

POPULAR_ROUTES = [
    ("HAN", "SGN", 1),
    ("SGN", "HAN", 2),
    ("HAN", "DAD", 3),
    ("DAD", "HAN", 4),
    ("SGN", "DAD", 5),
    ("DAD", "SGN", 6),
    ("HAN", "PQC", 7),
    ("PQC", "HAN", 8),
    ("SGN", "PQC", 9),
    ("PQC", "SGN", 10),
    ("HAN", "CXR", 11),
    ("CXR", "HAN", 12),
    ("SGN", "CXR", 13),
    ("CXR", "SGN", 14),
    ("HAN", "DLI", 15),
    ("DLI", "HAN", 16),
    ("SGN", "DLI", 17),
    ("DLI", "SGN", 18),
    ("HAN", "HUI", 19),
    ("SGN", "HUI", 20),
]


def parse_iso_duration_minutes(value: str | None) -> int | None:
    if not value:
        return None
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", value)
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    return hours * 60 + minutes


class AmadeusCollector:
    def __init__(self):
        self.api_key = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET")
        self.env = os.getenv("AMADEUS_ENV", "test")
        self.base_url = URLS.get(self.env, URLS["test"])
        self.token = None
        self.token_expires_at = 0

        if not self.api_key or not self.api_secret:
            raise ValueError("Missing AMADEUS_API_KEY / AMADEUS_API_SECRET")

    def authenticate(self) -> bool:
        if self.token and time.time() < self.token_expires_at - 60:
            return True

        r = safe_post(
            f"{self.base_url}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if not r:
            return False

        data = r.json()
        self.token = data["access_token"]
        self.token_expires_at = time.time() + data.get("expires_in", 1799)
        log.info("Amadeus authenticated (env=%s)", self.env)
        return True

    def _auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        adults: int = 1,
        max_results: int = 20,
    ) -> dict | None:
        if not self.authenticate():
            return None

        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": depart_date,
            "adults": adults,
            "currencyCode": "VND",
            "max": max_results,
            "nonStop": "false",
        }
        r = safe_get(
            f"{self.base_url}/v2/shopping/flight-offers",
            params=params,
            headers=self._auth_header(),
        )
        if not r:
            return None

        data = r.json()
        offers = data.get("data", [])
        log.info("Amadeus %s-%s %s: %s offers", origin, destination, depart_date, len(offers))
        self._save_raw(f"flights_{origin}_{destination}_{depart_date}", data)
        return data

    def parse_offer(self, offer: dict, route_id: str) -> dict | None:
        try:
            itinerary = offer["itineraries"][0]
            segments = itinerary["segments"]
            first = segments[0]
            last = segments[-1]

            airline_iata = (offer.get("validatingAirlineCodes") or [first.get("carrierCode") or ""])[0]
            flight_number = f"{first.get('carrierCode', '')}{first.get('number', '')}"
            departure_at = first["departure"]["at"]

            cabin = "economy"
            traveler_pricing = offer.get("travelerPricings") or []
            if traveler_pricing:
                fare_details = traveler_pricing[0].get("fareDetailsBySegment") or []
                if fare_details:
                    cabin = (fare_details[0].get("cabin") or "economy").lower()

            return {
                "route_id": route_id,
                "airline_iata": airline_iata if airline_iata in AIRLINE_NAMES else airline_iata or None,
                "airline_name": AIRLINE_NAMES.get(airline_iata, airline_iata or "Unknown Airline"),
                "flight_number": flight_number,
                "cabin_class": cabin,
                "departure_date": departure_at[:10],
                "depart_at": departure_at,
                "arrive_at": last["arrival"]["at"],
                "duration_minutes": parse_iso_duration_minutes(itinerary.get("duration")),
                "stops": max(0, len(segments) - 1),
                "price_amount": int(float(offer["price"]["total"])),
                "currency": offer.get("price", {}).get("currency", "VND"),
                "source": f"amadeus_{self.env}",
                "source_ref": offer.get("id"),
                "expires_at": expires_in(hours=24),
                "raw": offer,
            }
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            log.debug("Amadeus offer parse failed: %s", exc)
            return None

    def _save_raw(self, name: str, data: dict):
        os.makedirs("evidence", exist_ok=True)
        path = os.path.join("evidence", f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "_meta": {
                        "source": "Amadeus Flight Offers Search",
                        "env": self.env,
                        "endpoint": f"{self.base_url}/v2/shopping/flight-offers",
                        "collected": datetime.now().isoformat(),
                    },
                    "data": data,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def collect_route(self, conn, origin: str, destination: str, depart_date: str, rank: int | None = None) -> int:
        destination_slug = IATA_SLUG.get(destination)
        route_id = get_or_create_flight_route(
            conn,
            origin,
            destination,
            destination_slug=destination_slug,
            is_popular_seed=rank is not None,
            popularity_rank=rank,
        )

        raw = self.search_flights(origin, destination, depart_date, max_results=20)
        if not raw:
            return 0

        cache_key = f"{origin}:{destination}:{depart_date}:1:economy"
        upsert_flight_offer_cache(conn, cache_key, route_id, {
            "origin": origin,
            "destination": destination,
            "departureDate": depart_date,
            "adults": 1,
            "currencyCode": "VND",
        }, raw, ttl_minutes=15)

        saved = 0
        for offer in raw.get("data", []):
            parsed = self.parse_offer(offer, route_id)
            if not parsed:
                continue
            upsert_flight_price_snapshot(conn, parsed)
            saved += 1
        return saved

    def run(self, conn):
        log.info("Amadeus collector started")
        if not self.authenticate():
            log.error("Amadeus auth failed")
            return

        today = date.today()
        search_dates = [
            (today + timedelta(days=7)).isoformat(),
            (today + timedelta(days=14)).isoformat(),
            (today + timedelta(days=30)).isoformat(),
        ]

        total = 0
        for origin, destination, rank in POPULAR_ROUTES:
            for depart_date in search_dates:
                total += self.collect_route(conn, origin, destination, depart_date, rank=rank)
                time.sleep(0.4)

        log.info("Amadeus collector finished: %s snapshots", total)
