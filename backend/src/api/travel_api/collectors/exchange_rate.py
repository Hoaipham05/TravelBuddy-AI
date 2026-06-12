"""
collectors/exchange_rate.py
Frankfurter v2 exchange-rate collector.

Strategy:
  - Fetch USD-based rates including VND, then derive VND -> target and
    target -> VND rates for UI conversion.
  - Cache TTL: 1 hour.
  - Persist latest rows to exchange_rate_cache and same rows to history.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from utils.helpers import safe_get, log_response
from db.connection import expires_in, upsert_exchange_rate

log = logging.getLogger(__name__)

BASE = "https://api.frankfurter.dev/v2"
FALLBACK_BASE = "https://open.er-api.com/v6/latest/USD"
TARGET_CURRENCIES = ["VND", "USD", "EUR", "THB", "JPY", "SGD", "KRW", "GBP", "CNY", "AUD"]


class ExchangeRateCollector:
    def fetch_latest(self) -> dict | None:
        r = safe_get(
            f"{BASE}/rates",
            params={"base": "USD", "quotes": ",".join(TARGET_CURRENCIES)},
        )
        if not r:
            return None
        log_response("Frankfurter", r, ["date", "rates", "data"])
        return r.json()

    def fetch_latest_fallback(self) -> dict | None:
        r = safe_get(FALLBACK_BASE)
        if not r:
            return None
        log_response("ExchangeRate-API Open Access", r, ["result", "base_code", "rates"])
        return r.json()

    def fetch_history(self, days_back: int = 30) -> dict | None:
        end = date.today()
        start = end - timedelta(days=days_back)
        r = safe_get(
            f"{BASE}/rates",
            params={
                "from": start.isoformat(),
                "to": end.isoformat(),
                "base": "USD",
                "quotes": "VND,THB,JPY,SGD,EUR",
            },
        )
        if not r:
            return None
        return r.json()

    def _extract_rates_payload(self, raw: dict | list) -> tuple[str, dict[str, float]]:
        """
        Frankfurter has had multiple public shapes. Support:
          - {"date": "...", "rates": {...}}
          - {"data": {"date": "...", "rates": {...}}}
          - {"data": [{"date": "...", "rates": {...}}, ...]}
        """
        data: Any = raw.get("data", raw) if isinstance(raw, dict) else raw
        if isinstance(data, list):
            data = data[-1] if data else {}
        if isinstance(data, dict) and "rates" in data:
            fallback_date = raw.get("date") if isinstance(raw, dict) else None
            return data.get("date", fallback_date or datetime.utcnow().date().isoformat()), data.get("rates", {})
        if isinstance(raw, dict):
            if raw.get("result") == "success" and isinstance(raw.get("rates"), dict):
                updated = raw.get("time_last_update_utc", "")
                rate_date = datetime.utcnow().date().isoformat()
                if updated:
                    try:
                        rate_date = datetime.strptime(updated, "%a, %d %b %Y %H:%M:%S %z").date().isoformat()
                    except ValueError:
                        pass
                return rate_date, raw["rates"]
            return raw.get("date", datetime.utcnow().date().isoformat()), raw.get("rates", {})
        return datetime.utcnow().date().isoformat(), {}

    def _extract_history_rows(self, raw: dict | list) -> list[tuple[str, dict[str, float]]]:
        data: Any = raw.get("data", raw) if isinstance(raw, dict) else raw
        if isinstance(data, list):
            return [(item.get("date"), item.get("rates", {})) for item in data if item.get("date")]
        if isinstance(raw, dict) and isinstance(raw.get("rates"), dict):
            rates = raw["rates"]
            # Legacy time-series shape: {"rates": {"2026-01-01": {...}}}
            if rates and all(isinstance(v, dict) for v in rates.values()):
                return [(d, v) for d, v in sorted(rates.items())]
        return []

    def _rows_from_usd_rates(self, rate_date: str, rates_from_usd: dict[str, float], raw: dict) -> list[dict]:
        vnd_per_usd = rates_from_usd.get("VND")
        if not vnd_per_usd:
            log.warning("Frankfurter response has no VND quote; cannot derive VND rates")
            return []
        source = "exchange-rate-api-open" if isinstance(raw, dict) and raw.get("result") == "success" else "frankfurter"

        rows = [
            {
                "base_currency": "USD",
                "target_currency": "VND",
                "rate": vnd_per_usd,
                "rate_date": rate_date,
                "source": source,
                "expires_at": expires_in(hours=1),
                "raw": raw,
            },
            {
                "base_currency": "VND",
                "target_currency": "USD",
                "rate": round(1 / vnd_per_usd, 10),
                "rate_date": rate_date,
                "source": source,
                "expires_at": expires_in(hours=1),
                "raw": raw,
            },
        ]

        for currency, usd_to_currency in rates_from_usd.items():
            if currency in {"USD", "VND"} or not usd_to_currency:
                continue
            rows.append(
                {
                    "base_currency": currency,
                    "target_currency": "VND",
                    "rate": round(vnd_per_usd / usd_to_currency, 6),
                    "rate_date": rate_date,
                    "source": source,
                    "expires_at": expires_in(hours=1),
                    "raw": raw,
                }
            )
            rows.append(
                {
                    "base_currency": "VND",
                    "target_currency": currency,
                    "rate": round(usd_to_currency / vnd_per_usd, 10),
                    "rate_date": rate_date,
                    "source": source,
                    "expires_at": expires_in(hours=1),
                    "raw": raw,
                }
            )
        return rows

    def run(self, conn):
        log.info("Frankfurter collector started")

        raw = self.fetch_latest()
        if not raw:
            log.error("Frankfurter latest fetch failed")
            return

        rate_date, rates = self._extract_rates_payload(raw)
        if not rates.get("VND"):
            log.warning("Frankfurter response has no VND quote; falling back to ExchangeRate-API Open Access")
            raw = self.fetch_latest_fallback()
            if not raw:
                log.error("ExchangeRate fallback fetch failed")
                return
            rate_date, rates = self._extract_rates_payload(raw)

        rows = self._rows_from_usd_rates(rate_date, rates, raw)
        for row in rows:
            upsert_exchange_rate(conn, row)

        history_raw = self.fetch_history(30) if not (isinstance(raw, dict) and raw.get("result") == "success") else None
        history_count = 0
        if history_raw:
            for hist_date, hist_rates in self._extract_history_rows(history_raw):
                hist_rows = self._rows_from_usd_rates(hist_date, hist_rates, history_raw)
                for row in hist_rows:
                    # History rows do not need short cache semantics, but cache table
                    # keeps the latest per date; expires_at is harmless for history.
                    upsert_exchange_rate(conn, row)
                    history_count += 1

        log.info("Frankfurter collector finished: %s latest rows, %s history rows", len(rows), history_count)
