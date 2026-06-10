"""
collectors/countries.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API:     RestCountries  (https://restcountries.com)
Data:    Thông tin quốc gia: tiền tệ, ngôn ngữ, múi giờ,
         flag, thị thực (visa) cho người Việt
Key:     KHÔNG CẦN — hoàn toàn miễn phí
Docs:    https://restcountries.com/#api-endpoints-v3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dùng để:
  - Hiển thị thông tin visa, tiền tệ trong Trip Builder
  - Cảnh báo "người Việt cần visa không?"
  - Thông tin múi giờ khi lên lịch trình
"""

import json, logging
from utils.helpers import safe_get

log = logging.getLogger(__name__)

BASE = "https://restcountries.com/v3.1"

# Quốc gia cần lấy thông tin (ISO 3166-1 alpha-2)
COUNTRIES = {
    "VN": {"name": "Vietnam",   "vn": "Việt Nam",   "visa_free": True},
    "TH": {"name": "Thailand",  "vn": "Thái Lan",   "visa_free": True},   # VN miễn thị thực 30 ngày
    "JP": {"name": "Japan",     "vn": "Nhật Bản",   "visa_free": False},  # cần visa
    "SG": {"name": "Singapore", "vn": "Singapore",  "visa_free": True},   # miễn thị thực 30 ngày
    "KR": {"name": "South Korea","vn":"Hàn Quốc",   "visa_free": False},
    "FR": {"name": "France",    "vn": "Pháp",       "visa_free": False},
    "US": {"name": "United States","vn":"Mỹ",       "visa_free": False},
}


class CountriesCollector:

    def fetch_country(self, code: str) -> dict | None:
        """
        GET /v3.1/alpha/{code}
        Trả về thông tin đầy đủ của 1 quốc gia.
        """
        r = safe_get(f"{BASE}/alpha/{code}")
        if not r:
            return None
        data = r.json()
        return data[0] if isinstance(data, list) and data else data

    def parse_country(self, raw: dict, code: str) -> dict:
        """Rút gọn thông tin cần thiết cho Travel Buddy."""
        meta = COUNTRIES.get(code, {})

        # Tiền tệ
        currencies = raw.get("currencies", {})
        currency_list = [
            {"code": k, "name": v.get("name",""), "symbol": v.get("symbol","")}
            for k, v in currencies.items()
        ]

        # Ngôn ngữ
        languages = list(raw.get("languages", {}).values())

        # Múi giờ
        timezones = raw.get("timezones", [])

        # Flag
        flags = raw.get("flags", {})

        return {
            "code":       code,
            "name_en":    raw.get("name", {}).get("common", ""),
            "name_vn":    meta.get("vn", ""),
            "capital":    raw.get("capital", [""])[0] if raw.get("capital") else "",
            "region":     raw.get("region", ""),
            "population": raw.get("population", 0),
            "area_km2":   raw.get("area", 0),
            "currencies": currency_list,
            "languages":  languages,
            "timezones":  timezones,
            "flag_url":   flags.get("png", ""),
            "flag_svg":   flags.get("svg", ""),
            "visa_free_for_vn": meta.get("visa_free", False),
            "calling_code": (raw.get("idd", {}).get("root","") +
                             (raw.get("idd",{}).get("suffixes",[""])[0] or "")),
            "source": "RestCountries API v3.1 (restcountries.com)",
        }

    def save_to_db(self, conn, country: dict):
        """Lưu vào bảng countries."""
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                code          CHAR(2) PRIMARY KEY,
                name_en       VARCHAR(100),
                name_vn       VARCHAR(100),
                capital       VARCHAR(100),
                region        VARCHAR(50),
                population    BIGINT,
                area_km2      NUMERIC(12,2),
                currencies    JSONB DEFAULT '[]',
                languages     JSONB DEFAULT '[]',
                timezones     JSONB DEFAULT '[]',
                flag_url      TEXT,
                flag_svg      TEXT,
                visa_free_for_vn BOOLEAN DEFAULT FALSE,
                calling_code  VARCHAR(10),
                updated_at    TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        cur.execute("""
            INSERT INTO countries
                (code, name_en, name_vn, capital, region, population,
                 area_km2, currencies, languages, timezones,
                 flag_url, flag_svg, visa_free_for_vn, calling_code)
            VALUES
                (%(code)s, %(name_en)s, %(name_vn)s, %(capital)s, %(region)s,
                 %(population)s, %(area_km2)s,
                 %(currencies)s::jsonb, %(languages)s::jsonb, %(timezones)s::jsonb,
                 %(flag_url)s, %(flag_svg)s, %(visa_free_for_vn)s, %(calling_code)s)
            ON CONFLICT (code) DO UPDATE SET
                name_vn          = EXCLUDED.name_vn,
                visa_free_for_vn = EXCLUDED.visa_free_for_vn,
                updated_at       = NOW()
        """, {**country,
              "currencies": json.dumps(country["currencies"], ensure_ascii=False),
              "languages":  json.dumps(country["languages"],  ensure_ascii=False),
              "timezones":  json.dumps(country["timezones"],  ensure_ascii=False),
        })
        conn.commit()
        log.info(f"  💾 Country: {country['name_en']} ({country['code']}) "
                 f"— visa_free={country['visa_free_for_vn']}, "
                 f"currency={[c['code'] for c in country['currencies']]}")

    def run(self, conn):
        log.info("🌍  RestCountries Collector bắt đầu")
        saved = 0
        for code in COUNTRIES:
            raw = self.fetch_country(code)
            if not raw:
                log.warning(f"  Không lấy được: {code}")
                continue
            parsed = self.parse_country(raw, code)
            self.save_to_db(conn, parsed)
            saved += 1

        log.info(f"✅ RestCountries: đã lưu {saved} quốc gia")
