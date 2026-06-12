"""
SerpApi Google Flights collector.

Use this provider when Amadeus Self-Service signup is blocked. Results are
stored in the same flight_price_snapshots table as Amadeus snapshots, so the
frontend/API layer does not need provider-specific logic.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, datetime, timedelta

from collectors.amadeus import AIRLINE_NAMES, IATA_SLUG, POPULAR_ROUTES
from db.connection import (
    expires_in,
    get_or_create_flight_route,
    upsert_flight_offer_cache,
    upsert_flight_price_snapshot,
)
from utils.helpers import safe_get

log = logging.getLogger(__name__)

BASE_URL = "https://serpapi.com/search"

AIRLINE_CODES = {
    "Vietnam Airlines": "VN",
    "VietJet Air": "VJ",
    "Vietjet Air": "VJ",
    "VietJet": "VJ",
    "Vietjet": "VJ",
    "Bamboo Airways": "QH",
}

AIRLINE_BOOKING_URLS = {
    "VN": "https://www.vietnamairlines.com/vn/vi/home",
    "VJ": "https://www.vietjetair.com/vi",
    "QH": "https://www.bambooairways.com/vn/vi",
}


def _parse_local_datetime(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.isoformat() + "+07:00"
        except ValueError:
            continue
    return value


def _normalize_flight_number(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace(" ", "").upper()


def _fallback_booking_url(airline_iata: str | None) -> str | None:
    if not airline_iata:
        return None
    return AIRLINE_BOOKING_URLS.get(airline_iata)


class SerpApiFlightsCollector:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.google_domain = os.getenv("SERPAPI_GOOGLE_DOMAIN", "google.com")
        self.gl = os.getenv("SERPAPI_GL", "vn")
        self.hl = os.getenv("SERPAPI_HL", "vi")

        if not self.api_key:
            raise ValueError("Missing SERPAPI_API_KEY")

    def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        adults: int = 1,
    ) -> dict | None:
        params = {
            "engine": "google_flights",
            "api_key": self.api_key,
            "google_domain": self.google_domain,
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": depart_date,
            "type": "2",
            "currency": "VND",
            "hl": self.hl,
            "gl": self.gl,
            "adults": adults,
            "travel_class": "1",
            "include_airlines": "VN,VJ,QH",
        }
        r = safe_get(BASE_URL, params=params, timeout=40, retries=3, delay=2)
        if not r:
            return None

        data = r.json()
        best_count = len(data.get("best_flights") or [])
        other_count = len(data.get("other_flights") or [])
        log.info(
            "SerpApi %s-%s %s: %s best, %s other",
            origin,
            destination,
            depart_date,
            best_count,
            other_count,
        )
        self._save_raw(f"serpapi_flights_{origin}_{destination}_{depart_date}", data)
        return data

    def parse_offer(self, offer: dict, route_id: str, fallback_date: str) -> dict | None:
        try:
            segments = offer.get("flights") or []
            if not segments:
                return None

            first = segments[0]
            last = segments[-1]
            airline_name = first.get("airline") or offer.get("airline") or "Unknown Airline"
            airline_iata = AIRLINE_CODES.get(airline_name)
            flight_number = _normalize_flight_number(first.get("flight_number"))
            departure_at = _parse_local_datetime((first.get("departure_airport") or {}).get("time"))
            arrive_at = _parse_local_datetime((last.get("arrival_airport") or {}).get("time"))

            price = offer.get("price")
            if price is None:
                return None

            return {
                "route_id": route_id,
                "airline_iata": airline_iata,
                "airline_name": AIRLINE_NAMES.get(airline_iata, airline_name),
                "flight_number": flight_number,
                "cabin_class": (first.get("travel_class") or "economy").lower(),
                "departure_date": (departure_at or fallback_date)[:10],
                "depart_at": departure_at,
                "arrive_at": arrive_at,
                "duration_minutes": offer.get("total_duration") or first.get("duration"),
                "stops": max(0, len(segments) - 1),
                "price_amount": int(float(price)),
                "currency": "VND",
                "booking_url": offer.get("booking_url") or _fallback_booking_url(airline_iata),
                "source": "serpapi_google_flights",
                "source_ref": offer.get("booking_token") or flight_number,
                "expires_at": expires_in(hours=24),
                "raw": offer,
            }
        except (TypeError, ValueError) as exc:
            log.debug("SerpApi offer parse failed: %s", exc)
            return None

    def _save_raw(self, name: str, data: dict):
        os.makedirs("evidence", exist_ok=True)
        path = os.path.join("evidence", f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "_meta": {
                        "source": "SerpApi Google Flights",
                        "endpoint": BASE_URL,
                        "collected": datetime.now().isoformat(),
                    },
                    "data": data,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def collect_route(self, conn, origin: str, destination: str, depart_date: str, rank: int | None = None) -> int:
        route_id = get_or_create_flight_route(
            conn,
            origin,
            destination,
            destination_slug=IATA_SLUG.get(destination),
            is_popular_seed=rank is not None,
            popularity_rank=rank,
        )

        raw = self.search_flights(origin, destination, depart_date)
        if not raw:
            return 0

        cache_key = f"serpapi:{origin}:{destination}:{depart_date}:1:economy"
        upsert_flight_offer_cache(
            conn,
            cache_key,
            route_id,
            {
                "origin": origin,
                "destination": destination,
                "departureDate": depart_date,
                "adults": 1,
                "currencyCode": "VND",
            },
            raw,
            ttl_minutes=15,
            source="serpapi_google_flights",
        )

        saved = 0
        offers = (raw.get("best_flights") or []) + (raw.get("other_flights") or [])
        for offer in offers:
            parsed = self.parse_offer(offer, route_id, depart_date)
            if not parsed:
                continue
            upsert_flight_price_snapshot(conn, parsed)
            saved += 1
        return saved

    def run(self, conn):
        log.info("SerpApi Google Flights collector started")
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
                time.sleep(0.8)

        log.info("SerpApi Google Flights collector finished: %s snapshots", total)
