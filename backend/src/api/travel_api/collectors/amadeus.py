"""
collectors/amadeus.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API:     Amadeus for Developers  (https://developers.amadeus.com)
Data:    Giá vé máy bay, lịch bay thực tế
Key:     Đăng ký miễn phí → sandbox không giới hạn
Docs:    https://developers.amadeus.com/self-service/category/flights
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Endpoints dùng:
  POST /v1/security/oauth2/token      → lấy access token
  GET  /v2/shopping/flight-offers     → tìm chuyến bay + giá
  GET  /v1/analytics/itinerary-price-metrics → xu hướng giá theo tháng
"""

import os, json, time, logging
from datetime import datetime, timedelta
from utils.helpers import safe_get, safe_post
from db.connection import upsert_flight, get_dest_id

log = logging.getLogger(__name__)

# Sandbox vs Production
URLS = {
    "test":       "https://test.api.amadeus.com",
    "production": "https://api.amadeus.com",
}

# IATA → destination slug trong DB
IATA_SLUG = {
    "DAD": "da-nang",
    "SGN": "ho-chi-minh",
    "PQC": "phu-quoc",
    "DLI": "da-lat",
    "CXR": "nha-trang",
    "VDO": "ha-long",
    "BKK": "bangkok",
    "NRT": "tokyo",
    "SIN": "singapore",
    "HAN": None,   # điểm xuất phát, không cần dest_id
}

# Tuyến bay cần lấy (origin, dest, ngày tìm kiếm)
ROUTES = [
    ("HAN", "DAD"),
    ("HAN", "SGN"),
    ("HAN", "PQC"),
    ("HAN", "DLI"),
    ("HAN", "CXR"),
    ("SGN", "DAD"),
    ("SGN", "PQC"),
    ("HAN", "BKK"),
    ("HAN", "NRT"),
    ("HAN", "SIN"),
]


class AmadeusCollector:

    def __init__(self):
        self.api_key    = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET")
        self.env        = os.getenv("AMADEUS_ENV", "test")
        self.base_url   = URLS[self.env]
        self.token      = None
        self.token_expires_at = 0

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Thiếu AMADEUS_API_KEY / AMADEUS_API_SECRET trong .env\n"
                "Đăng ký miễn phí: https://developers.amadeus.com"
            )

    # ── 1. Authentication ───────────────────────────────────────
    def authenticate(self) -> bool:
        """
        POST /v1/security/oauth2/token
        Amadeus dùng OAuth2 client_credentials flow.
        Token có hiệu lực 30 phút, tự động refresh khi hết hạn.
        """
        if self.token and time.time() < self.token_expires_at - 60:
            return True  # token vẫn còn hiệu lực

        r = safe_post(
            f"{self.base_url}/v1/security/oauth2/token",
            data={
                "grant_type":    "client_credentials",
                "client_id":     self.api_key,
                "client_secret": self.api_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if not r:
            log.error("[Amadeus] Authentication thất bại")
            return False

        data = r.json()
        self.token = data["access_token"]
        self.token_expires_at = time.time() + data.get("expires_in", 1799)
        log.info(f"[Amadeus] ✅ Token lấy thành công (env={self.env})")
        return True

    def _auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    # ── 2. Tìm kiếm chuyến bay ──────────────────────────────────
    def search_flights(self, origin: str, dest: str,
                       depart_date: str, adults: int = 1,
                       max_results: int = 10) -> list[dict]:
        """
        GET /v2/shopping/flight-offers
        Trả về list offer: [{id, price, itineraries, validatingAirlineCodes, ...}]

        Params:
          originLocationCode:      IATA sân bay xuất phát
          destinationLocationCode: IATA sân bay đến
          departureDate:           YYYY-MM-DD
          adults:                  số người lớn
          currencyCode:            VND
          max:                     số kết quả tối đa
        """
        if not self.authenticate():
            return []

        r = safe_get(
            f"{self.base_url}/v2/shopping/flight-offers",
            params={
                "originLocationCode":      origin,
                "destinationLocationCode": dest,
                "departureDate":           depart_date,
                "adults":                  adults,
                "currencyCode":            "VND",
                "max":                     max_results,
                "nonStop":                 "false",
            },
            headers=self._auth_header(),
        )
        if not r:
            return []

        data = r.json()
        offers = data.get("data", [])
        log.info(f"[Amadeus] {origin}→{dest} {depart_date}: {len(offers)} chuyến bay")

        # Log raw JSON để làm minh chứng
        self._save_raw(f"flights_{origin}_{dest}_{depart_date}", data)
        return offers

    # ── 3. Xu hướng giá theo tháng ─────────────────────────────
    def price_metrics(self, origin: str, dest: str,
                      depart_date: str) -> dict | None:
        """
        GET /v1/analytics/itinerary-price-metrics
        Trả về: giá thấp nhất, trung bình, cao nhất cho tuyến bay
        trong khoảng thời gian nhất định.
        Dùng để xây dựng tính năng Price Intelligence.
        """
        if not self.authenticate():
            return None

        r = safe_get(
            f"{self.base_url}/v1/analytics/itinerary-price-metrics",
            params={
                "originIataCode":      origin,
                "destinationIataCode": dest,
                "departureDate":       depart_date,
                "currencyCode":        "VND",
            },
            headers=self._auth_header(),
        )
        if not r:
            return None

        data = r.json()
        self._save_raw(f"price_metrics_{origin}_{dest}", data)
        return data

    # ── 4. Parse offer → row cho DB ────────────────────────────
    def _parse_offer(self, offer: dict, dest_id: str) -> dict | None:
        """Chuyển Amadeus offer JSON → dict chuẩn cho bảng flights."""
        try:
            price_total = int(float(offer["price"]["total"]))
            itinerary   = offer["itineraries"][0]
            segments    = itinerary["segments"]
            first_seg   = segments[0]
            last_seg    = segments[-1]

            airline     = offer.get("validatingAirlineCodes", ["??"])[0]
            flight_no   = f"{first_seg['carrierCode']}{first_seg['number']}"
            origin      = first_seg["departure"]["iataCode"]
            destination = last_seg["arrival"]["iataCode"]
            depart_at   = first_seg["departure"]["at"]
            arrive_at   = last_seg["arrival"]["at"]

            # Số điểm dừng
            stops = len(segments) - 1
            cabin = offer["travelerPricings"][0]["fareDetailsBySegment"][0].get(
                "cabin", "ECONOMY"
            ).lower()

            return {
                "destination_id": dest_id,
                "airline":        airline,
                "flight_no":      flight_no,
                "origin":         origin,
                "destination":    destination,
                "price":          price_total,
                "cabin_class":    cabin,
                "depart_at":      depart_at,
                "arrive_at":      arrive_at,
                "monthly_prices": json.dumps({}),
                "source":         f"amadeus_{self.env}",
                # metadata thêm để báo cáo
                "_stops":         stops,
                "_duration":      itinerary.get("duration", ""),
                "_raw_price":     offer["price"],
            }
        except (KeyError, IndexError, ValueError) as e:
            log.debug(f"Parse offer thất bại: {e}")
            return None

    # ── 5. Lưu raw JSON làm minh chứng ─────────────────────────
    def _save_raw(self, name: str, data: dict):
        """
        Lưu raw response JSON vào thư mục evidence/.
        Đây là MINH CHỨNG để báo cáo: data lấy từ Amadeus API.
        """
        import os
        os.makedirs("evidence", exist_ok=True)
        path = f"evidence/{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "_meta": {
                    "source":    "Amadeus for Developers API",
                    "env":       self.env,
                    "endpoint":  f"{self.base_url}/v2/shopping/flight-offers",
                    "collected": datetime.now().isoformat(),
                    "docs":      "https://developers.amadeus.com/self-service/category/flights",
                },
                "data": data,
            }, f, ensure_ascii=False, indent=2)
        log.info(f"  📁 Raw JSON lưu tại: {path}")

    # ── 6. Pipeline chính ───────────────────────────────────────
    def run(self, conn):
        log.info("✈  Amadeus Collector bắt đầu")

        if not self.authenticate():
            log.error("Amadeus auth thất bại — bỏ qua collector này")
            return

        # Lấy data cho 3 ngày tiêu biểu (thứ 3 tuần tới = rẻ nhất)
        today = datetime.today()
        search_dates = [
            (today + timedelta(days=7)).strftime("%Y-%m-%d"),   # 1 tuần
            (today + timedelta(days=30)).strftime("%Y-%m-%d"),  # 1 tháng
            (today + timedelta(days=60)).strftime("%Y-%m-%d"),  # 2 tháng
        ]

        total_saved = 0
        for origin, dest in ROUTES:
            dest_slug = IATA_SLUG.get(dest)
            if not dest_slug:
                continue

            dest_id = get_dest_id(conn, dest_slug)
            if not dest_id:
                log.warning(f"Không tìm thấy destination slug={dest_slug} trong DB")
                continue

            # Lấy giá rẻ nhất qua các ngày
            monthly: dict = {}
            for date in search_dates:
                offers = self.search_flights(origin, dest, date, max_results=5)
                if not offers:
                    continue

                for offer in offers:
                    parsed = self._parse_offer(offer, dest_id)
                    if not parsed:
                        continue

                    # Gộp monthly_prices
                    month_key = date[:7]  # "2026-06"
                    if month_key not in monthly or parsed["price"] < monthly[month_key]:
                        monthly[month_key] = parsed["price"]

                    # Lưu chuyến bay vào DB
                    parsed["monthly_prices"] = json.dumps(monthly)
                    upsert_flight(conn, parsed)
                    total_saved += 1

                time.sleep(0.5)  # rate limit

            # Lấy price metrics để làm biểu đồ xu hướng
            self.price_metrics(origin, dest, search_dates[0])
            time.sleep(1)

        log.info(f"✅ Amadeus: đã lưu {total_saved} chuyến bay")
