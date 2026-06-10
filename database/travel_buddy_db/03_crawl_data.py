"""
Travel Buddy — Web Crawler
Crawl data thực từ:
  1. Traveloka / Agoda     → giá khách sạn
  2. VietJet / Bamboo      → giá vé máy bay
  3. Tripadvisor VN        → review & rating điểm đến
  4. Foody.vn              → địa điểm ăn uống

Cài đặt:
    pip install requests beautifulsoup4 psycopg2-binary python-dotenv selenium

Cấu hình .env:
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=travel_buddy
    DB_USER=postgres
    DB_PASS=yourpassword
"""

import os, time, json, re, logging
from datetime import datetime
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ── Kết nối DB ────────────────────────────────────────────────
def get_db():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5432),
        dbname=os.getenv('DB_NAME', 'travel_buddy'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASS', '')
    )

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def fetch(url, timeout=15):
    """GET request với retry 3 lần."""
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            log.warning(f"Attempt {attempt+1}/3 failed for {url}: {e}")
            time.sleep(2 ** attempt)
    return None


# ══════════════════════════════════════════════════════════════
# CRAWLER 1: Giá vé máy bay từ trang VietJet
# ══════════════════════════════════════════════════════════════
class FlightCrawler:
    """
    Crawl giá vé từ API không chính thức của VietJet.
    URL pattern quan sát được từ Network tab browser.
    """

    VIETJET_SEARCH = "https://www.vietjetair.com/Sites/Web/vi-VN/Flight/Search"
    ROUTES = [
        ("HAN", "DAD"),  # Hà Nội → Đà Nẵng
        ("HAN", "SGN"),  # Hà Nội → TP.HCM
        ("HAN", "PQC"),  # Hà Nội → Phú Quốc
        ("SGN", "DAD"),  # TP.HCM → Đà Nẵng
        ("SGN", "PQC"),  # TP.HCM → Phú Quốc
        ("HAN", "BKK"),  # Hà Nội → Bangkok
    ]

    # Map IATA → destination slug trong DB
    IATA_TO_SLUG = {
        "DAD": "da-nang",
        "SGN": "ho-chi-minh",
        "PQC": "phu-quoc",
        "DLI": "da-lat",
        "CXR": "nha-trang",
        "VDO": "ha-long",
        "BKK": "bangkok",
        "NRT": "tokyo",
        "SIN": "singapore",
    }

    def crawl_route_prices(self, origin: str, dest: str, months: list[str]) -> list[dict]:
        """
        Crawl giá rẻ nhất mỗi tháng cho một tuyến.
        months: ["2026-06", "2026-07", ...]
        """
        results = []
        for month in months:
            year, mon = month.split("-")
            # Dùng ngày giữa tháng để tìm giá đại diện
            search_date = f"{year}-{mon}-15"
            url = (f"{self.VIETJET_SEARCH}"
                   f"?departureDate={search_date}"
                   f"&departureStation={origin}&arrivalStation={dest}"
                   f"&adult=1&children=0&infant=0&flightType=O")

            log.info(f"Crawl VietJet {origin}→{dest} tháng {month}")
            r = fetch(url)
            if not r:
                continue

            # Parse giá từ HTML (selector thực tế cần inspect browser)
            soup = BeautifulSoup(r.text, 'html.parser')
            price_elements = soup.select('.price-amount, .fare-price, [data-fare-price]')

            prices = []
            for el in price_elements:
                text = el.get_text(strip=True).replace('.', '').replace(',', '').replace('đ', '').replace('VND','').strip()
                try:
                    p = int(re.sub(r'\D', '', text))
                    if 300_000 < p < 15_000_000:  # sanity check
                        prices.append(p)
                except ValueError:
                    pass

            if prices:
                min_price = min(prices)
                results.append({
                    "month": month, "origin": origin, "dest": dest,
                    "min_price": min_price
                })
                log.info(f"  {origin}→{dest} {month}: {min_price:,}đ")

            time.sleep(1.5)  # tránh bị block

        return results

    def save_to_db(self, conn, flight_data: list[dict]):
        """Upsert flight data vào DB."""
        cur = conn.cursor()
        for f in flight_data:
            dest_slug = self.IATA_TO_SLUG.get(f["dest"])
            if not dest_slug:
                continue

            cur.execute("SELECT id FROM destinations WHERE slug = %s", (dest_slug,))
            row = cur.fetchone()
            if not row:
                continue
            dest_id = row[0]

            # Tạo monthly_prices JSON từ kết quả crawl
            cur.execute("""
                INSERT INTO flights
                    (destination_id, airline, flight_no, origin, destination, price, cabin_class, monthly_prices, source)
                VALUES (%s, %s, %s, %s, %s, %s, 'economy', %s, 'crawl')
                ON CONFLICT DO NOTHING
            """, (dest_id, 'VietJet Air', f'VJ-{f["origin"]}{f["dest"]}',
                  f["origin"], f["dest"], f["min_price"],
                  json.dumps({f["month"]: f["min_price"]})))
        conn.commit()
        log.info(f"Đã lưu {len(flight_data)} bản ghi flight.")

    def run(self):
        months = ["2026-06", "2026-07", "2026-08", "2026-09"]
        all_results = []
        for origin, dest in self.ROUTES:
            results = self.crawl_route_prices(origin, dest, months)
            all_results.extend(results)

        conn = get_db()
        self.save_to_db(conn, all_results)
        conn.close()
        return all_results


# ══════════════════════════════════════════════════════════════
# CRAWLER 2: Khách sạn từ Agoda (public search API)
# ══════════════════════════════════════════════════════════════
class HotelCrawler:
    """
    Crawl danh sách khách sạn + giá từ Agoda qua URL search.
    """

    AGODA_SEARCH = "https://www.agoda.com/vi-vn/search"

    CITY_MAP = {
        "da-nang":   {"city_id": 1539, "name": "Da Nang"},
        "hoi-an":    {"city_id": 1527, "name": "Hoi An"},
        "da-lat":    {"city_id": 1534, "name": "Da Lat"},
        "ha-long":   {"city_id": 1542, "name": "Ha Long"},
        "phu-quoc":  {"city_id": 5593, "name": "Phu Quoc"},
        "nha-trang": {"city_id": 1543, "name": "Nha Trang"},
        "sapa":      {"city_id": 1589, "name": "Sapa"},
        "bangkok":   {"city_id": 852,  "name": "Bangkok"},
    }

    def crawl_city_hotels(self, slug: str, checkin="2026-06-17", checkout="2026-06-18") -> list[dict]:
        city_info = self.CITY_MAP.get(slug)
        if not city_info:
            return []

        url = (f"{self.AGODA_SEARCH}?"
               f"city={city_info['city_id']}"
               f"&checkIn={checkin}&checkOut={checkout}"
               f"&rooms=1&adults=2&children=0&locale=vi-vn&currency=VND")

        log.info(f"Crawl Agoda hotels: {slug}")
        r = fetch(url)
        if not r:
            return []

        soup = BeautifulSoup(r.text, 'html.parser')
        hotels = []

        # Selector dựa trên cấu trúc HTML Agoda (cần cập nhật nếu site thay đổi)
        for card in soup.select('[data-selenium="hotel-item"], .property-card, .hotel-list-item')[:15]:
            try:
                name_el    = card.select_one('[data-selenium="hotel-name"], .hotel-name, h3')
                price_el   = card.select_one('[data-selenium="display-price"], .price, .rate')
                stars_el   = card.select_one('.star-rating, [data-element-name="star-rating"]')
                rating_el  = card.select_one('[data-selenium="review-score"], .review-score')
                address_el = card.select_one('.hotel-address, [data-selenium="hotel-address"]')

                if not name_el:
                    continue

                name_text  = name_el.get_text(strip=True)
                price_text = price_el.get_text(strip=True) if price_el else "0"
                price_val  = int(re.sub(r'\D', '', price_text) or 0)
                stars_val  = int(stars_el.get('data-value', 0)) if stars_el else 3
                rating_val = float(re.sub(r'[^\d.]', '', rating_el.get_text()) or 0) if rating_el else 0.0
                addr_text  = address_el.get_text(strip=True) if address_el else ""

                if name_text and price_val > 0:
                    hotels.append({
                        "name": name_text, "price_per_night": price_val,
                        "stars": stars_val, "avg_rating": rating_val,
                        "address": addr_text, "destination_slug": slug
                    })
            except Exception as e:
                log.debug(f"Parse error: {e}")
                continue

        log.info(f"  Tìm thấy {len(hotels)} khách sạn cho {slug}")
        time.sleep(2)
        return hotels

    def save_to_db(self, conn, hotels: list[dict]):
        cur = conn.cursor()
        count = 0
        for h in hotels:
            cur.execute("SELECT id FROM destinations WHERE slug = %s", (h["destination_slug"],))
            row = cur.fetchone()
            if not row:
                continue
            cur.execute("""
                INSERT INTO hotels (destination_id, name, stars, price_per_night, address, avg_rating, amenities)
                VALUES (%s, %s, %s, %s, %s, %s, '["wifi"]')
                ON CONFLICT DO NOTHING
            """, (row[0], h["name"], h["stars"], h["price_per_night"], h["address"], h["avg_rating"]))
            count += 1
        conn.commit()
        log.info(f"Đã lưu {count} khách sạn từ crawl.")

    def run(self):
        all_hotels = []
        for slug in self.CITY_MAP:
            hotels = self.crawl_city_hotels(slug)
            all_hotels.extend(hotels)

        conn = get_db()
        self.save_to_db(conn, all_hotels)
        conn.close()
        return all_hotels


# ══════════════════════════════════════════════════════════════
# CRAWLER 3: Reviews & rating từ Tripadvisor
# ══════════════════════════════════════════════════════════════
class ReviewCrawler:
    """
    Crawl review từ Tripadvisor VN.
    CHÚ Ý: Chỉ dùng cho mục đích học thuật/nghiên cứu.
    Tripadvisor có terms of service nghiêm về crawling.
    Thay bằng Tripadvisor Content API cho production.
    """

    TRIPADVISOR_SEARCH = "https://www.tripadvisor.com.vn/Search?q={query}&searchSessionId=0"

    DESTINATION_QUERIES = {
        "da-nang":  "Đà Nẵng Vietnam attractions",
        "hoi-an":   "Hội An Vietnam attractions",
        "da-lat":   "Đà Lạt Vietnam attractions",
        "ha-long":  "Hạ Long Vietnam",
        "phu-quoc": "Phú Quốc Vietnam beach",
    }

    def crawl_destination_info(self, slug: str) -> dict | None:
        query = self.DESTINATION_QUERIES.get(slug, "")
        if not query:
            return None

        url = self.TRIPADVISOR_SEARCH.format(query=requests.utils.quote(query))
        log.info(f"Crawl Tripadvisor: {slug}")
        r = fetch(url)
        if not r:
            return None

        soup = BeautifulSoup(r.text, 'html.parser')

        # Lấy rating tổng
        rating_el = soup.select_one('.rating .value-title, [class*="ratingBubble"], .overallRating')
        rating = 0.0
        if rating_el:
            try:
                rating = float(re.sub(r'[^\d.]', '', rating_el.get_text()) or 0)
            except:
                pass

        # Lấy description
        desc_el = soup.select_one('.overview-section p, .destination-overview, [class*="description"]')
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        time.sleep(2)
        return {"slug": slug, "avg_rating": rating, "description": description}

    def update_db(self, conn, info: dict):
        cur = conn.cursor()
        if info.get("avg_rating", 0) > 0:
            cur.execute("""
                UPDATE destinations
                SET avg_rating = %s
                WHERE slug = %s
            """, (info["avg_rating"], info["slug"]))
            conn.commit()

    def run(self):
        conn = get_db()
        for slug in self.DESTINATION_QUERIES:
            info = self.crawl_destination_info(slug)
            if info:
                self.update_db(conn, info)
        conn.close()


# ══════════════════════════════════════════════════════════════
# CRAWLER 4: Amadeus API (API chính thức – khuyên dùng)
# ══════════════════════════════════════════════════════════════
class AmadeusFlightCrawler:
    """
    Dùng Amadeus Test API (miễn phí) để lấy giá vé thực tế.
    Đăng ký tại: https://developers.amadeus.com
    - Test environment: 100 req/ngày, dữ liệu gần thực
    - Không cần thẻ tín dụng
    """

    AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
    SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

    def __init__(self):
        self.api_key    = os.getenv("AMADEUS_API_KEY", "")
        self.api_secret = os.getenv("AMADEUS_API_SECRET", "")
        self.token      = None

    def authenticate(self) -> bool:
        if not self.api_key:
            log.warning("AMADEUS_API_KEY chưa cấu hình trong .env")
            return False

        r = requests.post(self.AUTH_URL, data={
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret,
        })
        if r.status_code == 200:
            self.token = r.json()["access_token"]
            log.info("Amadeus authentication OK")
            return True
        log.error(f"Amadeus auth failed: {r.text}")
        return False

    def search_flights(self, origin: str, dest: str, date: str, adults=1) -> list[dict]:
        if not self.token:
            return []

        r = requests.get(self.SEARCH_URL, headers={
            "Authorization": f"Bearer {self.token}"
        }, params={
            "originLocationCode": origin,
            "destinationLocationCode": dest,
            "departureDate": date,
            "adults": adults,
            "max": 10,
            "currencyCode": "VND",
        })

        if r.status_code != 200:
            log.error(f"Amadeus search failed: {r.status_code} {r.text[:200]}")
            return []

        flights = []
        for offer in r.json().get("data", []):
            try:
                price = int(float(offer["price"]["total"]))
                seg   = offer["itineraries"][0]["segments"][0]
                flights.append({
                    "airline":     seg["carrierCode"],
                    "flight_no":   seg["carrierCode"] + seg["number"],
                    "origin":      seg["departure"]["iataCode"],
                    "destination": seg["arrival"]["iataCode"],
                    "price":       price,
                    "depart_at":   seg["departure"]["at"],
                    "arrive_at":   seg["arrival"]["at"],
                })
            except (KeyError, ValueError) as e:
                log.debug(f"Parse flight offer: {e}")

        log.info(f"Amadeus {origin}→{dest} {date}: {len(flights)} chuyến, rẻ nhất {min((f['price'] for f in flights), default=0):,}đ")
        return flights

    def save_to_db(self, conn, flights: list[dict], dest_slug: str):
        cur = conn.cursor()
        cur.execute("SELECT id FROM destinations WHERE slug = %s", (dest_slug,))
        row = cur.fetchone()
        if not row:
            return
        dest_id = row[0]

        for f in flights:
            cur.execute("""
                INSERT INTO flights
                    (destination_id, airline, flight_no, origin, destination,
                     price, cabin_class, depart_at, arrive_at, source)
                VALUES (%s, %s, %s, %s, %s, %s, 'economy', %s, %s, 'amadeus')
                ON CONFLICT DO NOTHING
            """, (dest_id, f["airline"], f["flight_no"], f["origin"],
                  f["destination"], f["price"], f["depart_at"], f["arrive_at"]))
        conn.commit()
        log.info(f"Lưu {len(flights)} flights từ Amadeus cho {dest_slug}")

    def run(self):
        if not self.authenticate():
            log.warning("Bỏ qua Amadeus crawler (chưa cấu hình API key)")
            return

        ROUTES = [
            ("HAN", "DAD", "da-nang",  "2026-06-17"),
            ("HAN", "SGN", "ho-chi-minh", "2026-06-17"),
            ("HAN", "BKK", "bangkok",  "2026-06-20"),
        ]
        conn = get_db()
        for origin, dest, slug, date in ROUTES:
            flights = self.search_flights(origin, dest, date)
            self.save_to_db(conn, flights, slug)
            time.sleep(1)
        conn.close()


# ══════════════════════════════════════════════════════════════
# MAIN — chạy tất cả crawlers
# ══════════════════════════════════════════════════════════════
def main():
    log.info("=" * 55)
    log.info("Travel Buddy Data Crawler bắt đầu")
    log.info("=" * 55)

    # 1. Amadeus API (ưu tiên — data chính xác nhất)
    log.info("\n[1/4] Amadeus API flights...")
    AmadeusFlightCrawler().run()

    # 2. Crawl giá VietJet (fallback nếu không có Amadeus key)
    log.info("\n[2/4] VietJet price crawler...")
    FlightCrawler().run()

    # 3. Crawl khách sạn Agoda
    log.info("\n[3/4] Agoda hotel crawler...")
    HotelCrawler().run()

    # 4. Cập nhật rating từ Tripadvisor
    log.info("\n[4/4] Tripadvisor review crawler...")
    ReviewCrawler().run()

    log.info("\nHoàn thành! Kiểm tra DB:")
    conn = get_db()
    cur = conn.cursor()
    for tbl in ['destinations','hotels','flights','users','trips','reviews']:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(f"  {tbl}: {cur.fetchone()[0]} bản ghi")
    conn.close()


if __name__ == "__main__":
    main()
