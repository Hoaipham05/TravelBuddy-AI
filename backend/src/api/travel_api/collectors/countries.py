"""
collectors/countries.py
Country metadata collector.

Important:
  REST Countries v3.1/v4 legacy endpoints are no longer reliable. The current
  v5 API requires a free API key. If RESTCOUNTRIES_API_KEY is missing, this
  collector seeds a small manual fallback set so the app still works in MVP.

Visa notes are stored separately as deterministic/manual rules. RestCountries
is not a visa authority.
"""

from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any

from utils.helpers import safe_get
from db.connection import upsert_country, upsert_visa_rule

log = logging.getLogger(__name__)

BASE = "https://api.restcountries.com/countries/v5"

COUNTRY_META = {
    "VN": {"name_vn": "Việt Nam", "visa_required": False, "visa_type": "domestic", "max_stay_days": None},
    "TH": {"name_vn": "Thái Lan", "visa_required": False, "visa_type": "visa_free", "max_stay_days": 30},
    "JP": {"name_vn": "Nhật Bản", "visa_required": True, "visa_type": "sticker_or_evisa", "max_stay_days": None},
    "SG": {"name_vn": "Singapore", "visa_required": False, "visa_type": "visa_free", "max_stay_days": 30},
    "KR": {"name_vn": "Hàn Quốc", "visa_required": True, "visa_type": "sticker_or_evisa", "max_stay_days": None},
    "CN": {"name_vn": "Trung Quốc", "visa_required": True, "visa_type": "sticker", "max_stay_days": None},
    "FR": {"name_vn": "Pháp", "visa_required": True, "visa_type": "schengen", "max_stay_days": None},
    "US": {"name_vn": "Mỹ", "visa_required": True, "visa_type": "sticker", "max_stay_days": None},
    "AU": {"name_vn": "Úc", "visa_required": True, "visa_type": "visitor", "max_stay_days": None},
    "GB": {"name_vn": "Vương quốc Anh", "visa_required": True, "visa_type": "visitor_visa", "max_stay_days": None},
}

FALLBACK_COUNTRIES = {
    "VN": {
        "alpha3": "VNM", "name_en": "Vietnam", "capital": "Hanoi", "region": "Asia",
        "subregion": "South-Eastern Asia", "currencies": [{"code": "VND", "name": "Vietnamese đồng", "symbol": "₫"}],
        "languages": ["Vietnamese"], "timezones": ["UTC+07:00"], "calling_code": "+84",
    },
    "TH": {
        "alpha3": "THA", "name_en": "Thailand", "capital": "Bangkok", "region": "Asia",
        "subregion": "South-Eastern Asia", "currencies": [{"code": "THB", "name": "Thai baht", "symbol": "฿"}],
        "languages": ["Thai"], "timezones": ["UTC+07:00"], "calling_code": "+66",
    },
    "JP": {
        "alpha3": "JPN", "name_en": "Japan", "capital": "Tokyo", "region": "Asia",
        "subregion": "Eastern Asia", "currencies": [{"code": "JPY", "name": "Japanese yen", "symbol": "¥"}],
        "languages": ["Japanese"], "timezones": ["UTC+09:00"], "calling_code": "+81",
    },
    "SG": {
        "alpha3": "SGP", "name_en": "Singapore", "capital": "Singapore", "region": "Asia",
        "subregion": "South-Eastern Asia", "currencies": [{"code": "SGD", "name": "Singapore dollar", "symbol": "$"}],
        "languages": ["English", "Malay", "Tamil", "Chinese"], "timezones": ["UTC+08:00"], "calling_code": "+65",
    },
    "KR": {
        "alpha3": "KOR", "name_en": "South Korea", "capital": "Seoul", "region": "Asia",
        "subregion": "Eastern Asia", "currencies": [{"code": "KRW", "name": "South Korean won", "symbol": "₩"}],
        "languages": ["Korean"], "timezones": ["UTC+09:00"], "calling_code": "+82",
    },
    "CN": {
        "alpha3": "CHN", "name_en": "China", "capital": "Beijing", "region": "Asia",
        "subregion": "Eastern Asia", "currencies": [{"code": "CNY", "name": "Chinese yuan", "symbol": "¥"}],
        "languages": ["Chinese"], "timezones": ["UTC+08:00"], "calling_code": "+86",
    },
    "FR": {
        "alpha3": "FRA", "name_en": "France", "capital": "Paris", "region": "Europe",
        "subregion": "Western Europe", "currencies": [{"code": "EUR", "name": "Euro", "symbol": "€"}],
        "languages": ["French"], "timezones": ["UTC+01:00"], "calling_code": "+33",
    },
    "US": {
        "alpha3": "USA", "name_en": "United States", "capital": "Washington, D.C.", "region": "Americas",
        "subregion": "North America", "currencies": [{"code": "USD", "name": "United States dollar", "symbol": "$"}],
        "languages": ["English"], "timezones": ["UTC-05:00"], "calling_code": "+1",
    },
    "AU": {
        "alpha3": "AUS", "name_en": "Australia", "capital": "Canberra", "region": "Oceania",
        "subregion": "Australia and New Zealand", "currencies": [{"code": "AUD", "name": "Australian dollar", "symbol": "$"}],
        "languages": ["English"], "timezones": ["UTC+10:00"], "calling_code": "+61",
    },
    "GB": {
        "alpha3": "GBR", "name_en": "United Kingdom", "capital": "London", "region": "Europe",
        "subregion": "Northern Europe", "currencies": [{"code": "GBP", "name": "British pound", "symbol": "£"}],
        "languages": ["English"], "timezones": ["UTC+00:00"], "calling_code": "+44",
    },
}


def _dig(obj: dict, *keys: str, default=None):
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


class CountriesCollector:
    def __init__(self):
        self.api_key = os.getenv("RESTCOUNTRIES_API_KEY", "")

    def fetch_country(self, code: str) -> dict | None:
        if not self.api_key:
            return None

        r = safe_get(
            f"{BASE}/code",
            params={"q": code},
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        if not r:
            return None
        return r.json()

    def _first_object(self, raw: dict) -> dict:
        data = raw.get("data", raw)
        if isinstance(data, dict):
            objects = data.get("objects")
            if isinstance(objects, list) and objects:
                return objects[0]
        if isinstance(raw, list) and raw:
            return raw[0]
        return data if isinstance(data, dict) else {}

    def parse_country(self, code: str, raw: dict) -> dict:
        obj = self._first_object(raw)
        meta = COUNTRY_META.get(code, {})

        names = obj.get("names", obj.get("name", {}))
        codes = obj.get("codes", {})
        currencies_obj = obj.get("currencies", {})
        languages_obj = obj.get("languages", {})
        flag = obj.get("flag", obj.get("flags", {}))

        currencies = []
        if isinstance(currencies_obj, dict):
            for curr_code, value in currencies_obj.items():
                if isinstance(value, dict):
                    currencies.append({
                        "code": curr_code,
                        "name": value.get("name", ""),
                        "symbol": value.get("symbol", ""),
                    })
                else:
                    currencies.append({"code": curr_code, "name": str(value), "symbol": ""})

        languages = list(languages_obj.values()) if isinstance(languages_obj, dict) else languages_obj or []

        calling_code = ""
        idd = obj.get("idd", {})
        if isinstance(idd, dict):
            suffixes = idd.get("suffixes") or [""]
            calling_code = f"{idd.get('root', '')}{suffixes[0] or ''}"

        return {
            "code": code,
            "alpha3": codes.get("alpha_3") or codes.get("cca3") or obj.get("cca3"),
            "name_en": _dig(names, "common") or obj.get("names.common") or obj.get("name_en") or code,
            "name_vn": meta.get("name_vn"),
            "capital": (obj.get("capital") or [""])[0] if isinstance(obj.get("capital"), list) else obj.get("capital"),
            "region": obj.get("region"),
            "subregion": obj.get("subregion"),
            "population": obj.get("population"),
            "area_km2": obj.get("area") or obj.get("area_km2"),
            "currencies": currencies,
            "languages": languages,
            "timezones": obj.get("timezones", []),
            "flag_url": flag.get("png") if isinstance(flag, dict) else None,
            "flag_svg": flag.get("svg") if isinstance(flag, dict) else None,
            "calling_code": calling_code,
            "source": "restcountries_v5",
            "raw": raw,
        }

    def fallback_country(self, code: str) -> dict:
        base = FALLBACK_COUNTRIES[code]
        meta = COUNTRY_META.get(code, {})
        return {
            "code": code,
            "name_vn": meta.get("name_vn"),
            "source": "manual_seed_fallback",
            "raw": {},
            **base,
        }

    def save_visa_rule(self, conn, code: str):
        meta = COUNTRY_META[code]
        upsert_visa_rule(
            conn,
            {
                "passport_country_code": "VN",
                "destination_country_code": code,
                "visa_required": meta["visa_required"],
                "visa_type": meta["visa_type"],
                "max_stay_days": meta["max_stay_days"],
                "note": (
                    "Quy tắc visa được seed thủ công cho MVP. "
                    "Production cần xác minh lại từ nguồn lãnh sự/chính phủ chính thức."
                ),
                "verified_at": date.today(),
            },
        )

    def run(self, conn):
        log.info("Countries collector started")
        if not self.api_key:
            log.warning("RESTCOUNTRIES_API_KEY missing; using manual fallback country metadata")

        saved = 0
        for code in COUNTRY_META:
            country = None
            if self.api_key:
                raw = self.fetch_country(code)
                if raw:
                    country = self.parse_country(code, raw)
            if country is None:
                country = self.fallback_country(code)

            upsert_country(conn, country)
            self.save_visa_rule(conn, code)
            saved += 1

        log.info("Countries collector finished: %s countries", saved)
