"""
collectors/opentripmap.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API:     OpenTripMap  (https://dev.opentripmap.org)
Data:    Điểm tham quan, khách sạn, POI tại Việt Nam
Key:     Đăng ký miễn phí → 500 req/ngày
Docs:    https://dev.opentripmap.org/docs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Luồng:
  1. geoname()       → lấy lat/lng của thành phố
  2. radius_search() → lấy list POI xung quanh (xid)
  3. place_detail()  → lấy chi tiết từng POI
  4. parse + save   → lưu vào destinations / hotels
"""

import os, json, time, logging
from utils.helpers import safe_get, slugify
from db.connection import upsert_destination, upsert_hotel, get_dest_id

log = logging.getLogger(__name__)

BASE = "https://api.opentripmap.com/0.1/en/places"

# Danh sách thành phố cần lấy data
CITIES = [
    {"name": "Da Nang",   "slug": "da-nang",   "country": "VN", "vn_name": "Đà Nẵng"},
    {"name": "Hoi An",    "slug": "hoi-an",    "country": "VN", "vn_name": "Hội An"},
    {"name": "Ha Long",   "slug": "ha-long",   "country": "VN", "vn_name": "Hạ Long"},
    {"name": "Da Lat",    "slug": "da-lat",    "country": "VN", "vn_name": "Đà Lạt"},
    {"name": "Phu Quoc",  "slug": "phu-quoc",  "country": "VN", "vn_name": "Phú Quốc"},
    {"name": "Nha Trang", "slug": "nha-trang", "country": "VN", "vn_name": "Nha Trang"},
    {"name": "Sapa",      "slug": "sapa",      "country": "VN", "vn_name": "Sapa"},
    {"name": "Bangkok",   "slug": "bangkok",   "country": "TH", "vn_name": "Bangkok"},
    {"name": "Tokyo",     "slug": "tokyo",     "country": "JP", "vn_name": "Tokyo"},
    {"name": "Singapore", "slug": "singapore", "country": "SG", "vn_name": "Singapore"},
]

# Loại địa điểm muốn lấy (phân cấp OpenTripMap)
ATTRACTION_KINDS = "interesting_places,cultural,historic,natural,beaches,amusements"
HOTEL_KINDS      = "accomodations"   # lưu ý: OpenTripMap viết sai chính tả


class OpenTripMapCollector:

    def __init__(self):
        self.key = os.getenv("OPENTRIPMAP_KEY")
        if not self.key:
            raise ValueError(
                "Thiếu OPENTRIPMAP_KEY trong .env\n"
                "Đăng ký miễn phí: https://dev.opentripmap.org/product"
            )

    def _p(self, extra: dict = None) -> dict:
        """Thêm apikey vào params."""
        params = {"apikey": self.key}
        if extra:
            params.update(extra)
        return params

    # ── 1. Lấy tọa độ thành phố ────────────────────────────────
    def geoname(self, city_name: str, country: str) -> dict | None:
        """
        GET /geoname?name=Da+Nang&country=VN
        Trả về: {name, country, lat, lon, population, ...}
        """
        r = safe_get(f"{BASE}/geoname",
                     params=self._p({"name": city_name, "country": country}))
        if not r:
            return None
        data = r.json()
        log.info(f"[OpenTripMap] geoname {city_name}: lat={data.get('lat')}, lon={data.get('lon')}")
        return data

    # ── 2. Tìm POI theo bán kính ────────────────────────────────
    def radius_search(self, lat: float, lon: float, kinds: str,
                      radius: int = 15000, limit: int = 50) -> list[dict]:
        """
        GET /radius?lat=...&lon=...&radius=15000&kinds=interesting_places
        Trả về list: [{xid, name, dist, kinds, point: {lat, lon}}, ...]
        """
        r = safe_get(f"{BASE}/radius", params=self._p({
            "lat": lat, "lon": lon,
            "radius": radius,
            "kinds": kinds,
            "limit": limit,
            "format": "json",
        }))
        if not r:
            return []
        results = r.json()
        log.info(f"[OpenTripMap] radius({lat},{lon}) → {len(results)} POIs")
        return results if isinstance(results, list) else []

    # ── 3. Chi tiết từng POI ────────────────────────────────────
    def place_detail(self, xid: str) -> dict | None:
        """
        GET /xid/{xid}
        Trả về thông tin chi tiết: name, address, wikipedia_extracts,
        image, rate (rating), kinds, point
        """
        r = safe_get(f"{BASE}/xid/{xid}", params=self._p())
        if not r:
            return None
        data = r.json()
        time.sleep(0.3)  # tránh rate limit 500 req/ngày
        return data

    # ── 4. Parse POI → row cho DB ───────────────────────────────
    def _parse_attraction(self, detail: dict, city_info: dict, dest_id: str) -> dict | None:
        """Chuyển raw JSON → dict chuẩn cho bảng destinations."""
        name = detail.get("name", "").strip()
        if not name or len(name) < 3:
            return None

        point   = detail.get("point", {})
        address = detail.get("address", {})
        wiki    = detail.get("wikipedia_extracts", {})
        kinds   = detail.get("kinds", "")

        # Ánh xạ kinds → tags
        tag_map = {
            "beaches":      "biển",
            "historic":     "lịch sử",
            "cultural":     "văn hóa",
            "natural":      "thiên nhiên",
            "museums":      "bảo tàng",
            "amusements":   "giải trí",
            "architecture": "kiến trúc",
            "religion":     "tâm linh",
        }
        tags = [v for k, v in tag_map.items() if k in kinds]

        return {
            "name":         name,
            "slug":         slugify(name) + f"-{city_info['slug']}",
            "city":         city_info["vn_name"],
            "country":      city_info.get("country_name", "Vietnam"),
            "description":  wiki.get("text", "")[:800],
            "lat":          point.get("lat"),
            "lng":          point.get("lon"),
            "images":       json.dumps([detail["image"]] if detail.get("image") else []),
            "tags":         json.dumps(tags),
            "best_months":  json.dumps([]),
            "avg_rating":   min(5.0, float(detail.get("rate", 0)) / 2),  # rate 0-10 → 0-5
            "review_count": detail.get("wikidata", 0),
        }

    def _parse_hotel(self, detail: dict, dest_id: str) -> dict | None:
        """Chuyển raw JSON → dict chuẩn cho bảng hotels."""
        name = detail.get("name", "").strip()
        if not name or len(name) < 3:
            return None

        point   = detail.get("point", {})
        address = detail.get("address", {})
        props   = detail.get("properties", {})

        # Đoán số sao từ tags/name
        stars = 3
        name_lower = name.lower()
        if any(w in name_lower for w in ["5 star","five star","luxury","palace","grand"]):
            stars = 5
        elif any(w in name_lower for w in ["4 star","resort","boutique"]):
            stars = 4
        elif any(w in name_lower for w in ["hostel","backpacker","budget"]):
            stars = 2

        return {
            "destination_id":  dest_id,
            "name":            name,
            "stars":           stars,
            "price_per_night": 0,          # OpenTripMap không có giá → Amadeus bổ sung
            "address":         ", ".join(filter(None, [
                                    address.get("road",""),
                                    address.get("suburb",""),
                                    address.get("city",""),
                                ])),
            "lat":             point.get("lat"),
            "lng":             point.get("lon"),
            "amenities":       json.dumps(["wifi"]),
            "images":          json.dumps([detail["image"]] if detail.get("image") else []),
            "avg_rating":      0,
        }

    # ── 5. Chạy toàn bộ pipeline cho 1 thành phố ──────────────
    def collect_city(self, conn, city: dict):
        log.info(f"\n{'='*50}")
        log.info(f"[OpenTripMap] Bắt đầu thu thập: {city['vn_name']}")

        # 1. Tọa độ
        geo = self.geoname(city["name"], city["country"])
        if not geo or not geo.get("lat"):
            log.error(f"Không lấy được tọa độ {city['name']}")
            return
        lat, lon = float(geo["lat"]), float(geo["lon"])
        city["country_name"] = geo.get("country", "Vietnam")

        # 2. Upsert destination chính
        dest_row = {
            "name":         city["vn_name"],
            "slug":         city["slug"],
            "city":         city["vn_name"],
            "country":      city["country_name"],
            "description":  "",
            "lat":          lat,
            "lng":          lon,
            "images":       "[]",
            "tags":         "[]",
            "best_months":  "[]",
            "avg_rating":   0,
            "review_count": 0,
        }
        dest_id = upsert_destination(conn, dest_row)
        log.info(f"  → Destination ID: {dest_id}")

        # 3. Lấy danh sách điểm tham quan
        log.info(f"  → Tìm điểm tham quan (r=15km)...")
        attractions = self.radius_search(lat, lon, ATTRACTION_KINDS, radius=15000, limit=30)
        saved_attr = 0
        for poi in attractions[:20]:   # giới hạn 20 để tiết kiệm quota
            xid = poi.get("xid")
            if not xid:
                continue
            detail = self.place_detail(xid)
            if not detail:
                continue
            parsed = self._parse_attraction(detail, city, dest_id)
            if parsed:
                try:
                    upsert_destination(conn, parsed)
                    saved_attr += 1
                except Exception as e:
                    log.debug(f"Skip attraction {xid}: {e}")
        log.info(f"  → Đã lưu {saved_attr} điểm tham quan")

        # 4. Lấy danh sách khách sạn
        log.info(f"  → Tìm khách sạn (r=10km)...")
        hotels_raw = self.radius_search(lat, lon, HOTEL_KINDS, radius=10000, limit=20)
        saved_hotels = 0
        for poi in hotels_raw[:15]:
            xid = poi.get("xid")
            if not xid:
                continue
            detail = self.place_detail(xid)
            if not detail:
                continue
            parsed = self._parse_hotel(detail, dest_id)
            if parsed:
                try:
                    upsert_hotel(conn, parsed)
                    saved_hotels += 1
                except Exception as e:
                    log.debug(f"Skip hotel {xid}: {e}")
        log.info(f"  → Đã lưu {saved_hotels} khách sạn")

        time.sleep(1)  # nghỉ giữa các thành phố

    def run(self, conn):
        log.info("🗺  OpenTripMap Collector bắt đầu")
        for city in CITIES:
            self.collect_city(conn, city)
        log.info("✅ OpenTripMap Collector hoàn thành")
