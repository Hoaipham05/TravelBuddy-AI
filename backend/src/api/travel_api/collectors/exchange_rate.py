"""
collectors/exchange_rate.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API:     Frankfurter  (https://www.frankfurter.app)
Data:    Tỷ giá hối đoái realtime từ European Central Bank
Key:     KHÔNG CẦN — hoàn toàn miễn phí
Docs:    https://www.frankfurter.app/docs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dùng để:
  - Hiển thị "1 USD = X VND" trong Trip Builder
  - Tính tổng chi phí chuyến đi nước ngoài sang VND
  - Cảnh báo biến động tỷ giá khi book tour
"""

import json, logging
from datetime import datetime
from utils.helpers import safe_get, log_response

log = logging.getLogger(__name__)

BASE = "https://api.frankfurter.app"

# Các cặp tiền tệ cần theo dõi cho Travel Buddy
BASE_CURRENCY = "VND"
TARGET_CURRENCIES = ["USD", "EUR", "THB", "JPY", "SGD", "KRW", "GBP", "CNY"]


class ExchangeRateCollector:

    def fetch_latest(self) -> dict | None:
        """
        GET /latest?from=USD&to=VND,THB,JPY,...
        Frankfurter không hỗ trợ VND làm base currency trực tiếp,
        nên ta lấy từ USD và tính ngược.
        """
        r = safe_get(f"{BASE}/latest", params={
            "from": "USD",
            "to":   ",".join(TARGET_CURRENCIES + ["VND"]),
        })
        if not r:
            return None
        log_response("Frankfurter", r, ["date", "rates"])
        return r.json()

    def fetch_historical(self, days_back: int = 30) -> list[dict]:
        """
        GET /YYYY-MM-DD..YYYY-MM-DD?from=USD&to=VND
        Lấy lịch sử tỷ giá 30 ngày để vẽ biểu đồ xu hướng.
        """
        from datetime import date, timedelta
        end   = date.today().isoformat()
        start = (date.today() - timedelta(days=days_back)).isoformat()

        r = safe_get(f"{BASE}/{start}..{end}", params={
            "from": "USD",
            "to":   "VND,THB,JPY,SGD",
        })
        if not r:
            return []

        data  = r.json()
        rates = data.get("rates", {})  # {"2026-06-01": {"VND": 25430, ...}, ...}
        result = [{"date": d, **v} for d, v in sorted(rates.items())]
        log.info(f"[Frankfurter] Historical {start}..{end}: {len(result)} ngày")
        return result

    def parse_rates(self, raw: dict) -> dict:
        """
        Chuyển từ cơ sở USD → tính tỷ giá sang VND.
        raw["rates"]: {"VND": 25430, "THB": 33.8, "JPY": 150.2, ...}
        """
        rates_from_usd = raw.get("rates", {})
        vnd_per_usd    = rates_from_usd.get("VND", 25000)

        # Tính: 1 đơn vị ngoại tệ = ? VND
        vnd_rates = {}
        for currency, usd_rate in rates_from_usd.items():
            if currency == "VND":
                continue
            if usd_rate and usd_rate > 0:
                vnd_rates[currency] = round(vnd_per_usd / usd_rate, 2)

        return {
            "base":         "VND",
            "date":         raw.get("date", datetime.now().strftime("%Y-%m-%d")),
            "updated_at":   datetime.now().isoformat(),
            "source":       "Frankfurter API (frankfurter.app) — data từ European Central Bank",
            "usd_per_vnd":  round(1 / vnd_per_usd, 8),
            "vnd_per_usd":  vnd_per_usd,
            "rates":        vnd_rates,  # {"USD": 25430, "THB": 752, "JPY": 169, ...}
        }

    def save_to_db(self, conn, data: dict, history: list[dict] = None):
        """Lưu tỷ giá hiện tại và lịch sử vào DB."""
        cur = conn.cursor()

        # Bảng tỷ giá hiện tại
        cur.execute("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                base_currency  CHAR(3) NOT NULL,
                target_currency CHAR(3) NOT NULL,
                rate           NUMERIC(18, 4) NOT NULL,
                rate_date      DATE NOT NULL,
                source         TEXT,
                updated_at     TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (base_currency, target_currency, rate_date)
            )
        """)

        # Lưu từng cặp tiền tệ
        rate_date = data["date"]
        for currency, rate in data["rates"].items():
            cur.execute("""
                INSERT INTO exchange_rates
                    (base_currency, target_currency, rate, rate_date, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (base_currency, target_currency, rate_date)
                DO UPDATE SET rate = EXCLUDED.rate, updated_at = NOW()
            """, ("VND", currency, rate, rate_date, data["source"]))

        conn.commit()
        log.info(f"  💾 Exchange rates ({rate_date}): "
                 f"1 USD = {data['vnd_per_usd']:,.0f} VND, "
                 f"1 THB = {data['rates'].get('THB', 0):,.0f} VND, "
                 f"1 JPY = {data['rates'].get('JPY', 0):,.0f} VND")

        # Lưu lịch sử nếu có
        if history:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rate_history (
                    rate_date       DATE NOT NULL,
                    currency        CHAR(3) NOT NULL,
                    vnd_rate        NUMERIC(18,4),
                    PRIMARY KEY (rate_date, currency)
                )
            """)
            for row in history:
                vnd = row.get("VND", 0)
                for curr in ["THB", "JPY", "SGD"]:
                    val = row.get(curr)
                    if val and val > 0 and vnd > 0:
                        cur.execute("""
                            INSERT INTO exchange_rate_history (rate_date, currency, vnd_rate)
                            VALUES (%s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (row["date"], curr, round(vnd / val, 2)))
            conn.commit()
            log.info(f"  📈 Lịch sử tỷ giá: {len(history)} ngày")

    def run(self, conn):
        log.info("💱  Frankfurter (Exchange Rate) Collector bắt đầu")

        # Tỷ giá hiện tại
        raw = self.fetch_latest()
        if not raw:
            log.error("Không lấy được tỷ giá — bỏ qua")
            return

        parsed = self.parse_rates(raw)

        # Lịch sử 30 ngày
        history = self.fetch_historical(30)

        self.save_to_db(conn, parsed, history)
        log.info("✅ Frankfurter: tỷ giá đã cập nhật")
