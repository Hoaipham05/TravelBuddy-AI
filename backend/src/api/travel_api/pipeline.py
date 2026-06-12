"""
TravelBuddy data pipeline.

Usage:
  python pipeline.py
  python pipeline.py --only weather
  python pipeline.py --only exchange_rate
  python pipeline.py --only countries
  python pipeline.py --only hotels
  python pipeline.py --only serpapi_hotels
  python pipeline.py --only booking_hotels
  python pipeline.py --only opentripmap
  python pipeline.py --only flights
  python pipeline.py --only serpapi
  python pipeline.py --only amadeus
  python pipeline.py --summary
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PIPELINE_LOG_PATH = os.getenv("TRAVELBUDDY_PIPELINE_LOG", "pipeline.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PIPELINE_LOG_PATH, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def run_pipeline(only: str | None = None):
    from db.connection import get_conn, summary

    only = only.lower() if only else None

    log.info("=" * 55)
    log.info("TravelBuddy data pipeline")
    log.info("=" * 55)

    conn = get_conn()

    if not only or only == "exchange_rate":
        log.info("\n[1/6] Exchange rates (Frankfurter)")
        try:
            from collectors.exchange_rate import ExchangeRateCollector

            ExchangeRateCollector().run(conn)
        except Exception as exc:
            log.error("ExchangeRate error: %s", exc)

    if not only or only == "countries":
        log.info("\n[2/6] Countries (RestCountries or fallback seed)")
        try:
            from collectors.countries import CountriesCollector

            CountriesCollector().run(conn)
        except Exception as exc:
            log.error("Countries error: %s", exc)

    if not only or only == "weather":
        log.info("\n[3/6] Thời tiết (Open-Meteo primary, MET Norway fallback, TTL 6h)")
        try:
            from collectors.weather import WeatherCollector

            WeatherCollector().run(conn)
        except Exception as exc:
            log.error("Weather error: %s", exc)

    if not only or only == "opentripmap":
        log.info("\n[4/6] POI (OpenTripMap)")
        try:
            from collectors.opentripmap import OpenTripMapCollector

            OpenTripMapCollector().run(conn)
        except ValueError as exc:
            log.warning("  Skip OpenTripMap: %s", exc)
        except Exception as exc:
            log.error("OpenTripMap error: %s", exc)

    if not only or only in {"hotels", "serpapi_hotels", "booking_hotels"}:
        provider = (
            "serpapi"
            if only == "serpapi_hotels"
            else "booking"
            if only == "booking_hotels"
            else os.getenv("HOTEL_PRICE_PROVIDER", "serpapi")
        ).lower()
        log.info("\n[5/6] Hotels (%s)", provider)
        try:
            if provider == "serpapi":
                from collectors.serpapi_hotels import SerpApiHotelsCollector

                SerpApiHotelsCollector().run(conn)
            elif provider == "booking":
                from collectors.hotels import BookingDemandHotelCollector

                BookingDemandHotelCollector().run(conn)
            else:
                log.warning("  Unknown HOTEL_PRICE_PROVIDER=%s; skipping hotels", provider)
        except ValueError as exc:
            log.warning("  Skip hotels: %s", exc)
        except Exception as exc:
            log.error("Hotels error: %s", exc)

    if not only or only in {"flights", "serpapi", "amadeus"}:
        provider = (
            only
            if only in {"serpapi", "amadeus"}
            else os.getenv("FLIGHT_PRICE_PROVIDER", "serpapi")
        ).lower()
        log.info("\n[6/6] Flight prices (%s)", provider)
        try:
            if provider == "serpapi":
                from collectors.serpapi_flights import SerpApiFlightsCollector

                SerpApiFlightsCollector().run(conn)
            elif provider == "amadeus":
                from collectors.amadeus import AmadeusCollector

                AmadeusCollector().run(conn)
            else:
                log.warning("  Unknown FLIGHT_PRICE_PROVIDER=%s; skipping flight prices", provider)
        except ValueError as exc:
            log.warning("  Skip flight prices: %s", exc)
        except Exception as exc:
            log.error("Flight prices error: %s", exc)

    summary(conn)
    conn.close()

    log.info("\nPipeline finished")
    log.info("Evidence JSON: evidence/")
    log.info("Detailed log: %s", PIPELINE_LOG_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TravelBuddy data pipeline")
    parser.add_argument("--only", help="Run one collector")
    parser.add_argument("--summary", action="store_true", help="Show DB summary only")
    args = parser.parse_args()

    if args.summary:
        from db.connection import get_conn, summary

        conn = get_conn()
        summary(conn)
        conn.close()
    else:
        run_pipeline(only=args.only)
