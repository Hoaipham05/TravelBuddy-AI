"""
database.py – Cơ sở dữ liệu nội bộ (mock) cho chuyến bay & khách sạn.

Thiết kế:
  • FLIGHTS_DB  : dict[(thành phố đi, thành phố đến)] → list[dict]
  • HOTELS_DB   : dict[thành phố] → list[dict]
  • CITY_ALIASES: chuẩn hóa tên thành phố (viết tắt, không dấu, tiếng Anh…)

Logic: search luôn kiểm tra cả chiều xuôi và chiều ngược của tuyến bay.
"""
from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════════
#  CITY NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

CITY_ALIASES: dict[str, str] = {
    # Hà Nội
    "hn": "Hà Nội", "hanoi": "Hà Nội", "ha noi": "Hà Nội",
    "hà nội": "Hà Nội", "hà noi": "Hà Nội", "noi bai": "Hà Nội",
    "nội bài": "Hà Nội",

    # Hồ Chí Minh
    "sg": "Hồ Chí Minh", "hcm": "Hồ Chí Minh", "tphcm": "Hồ Chí Minh",
    "saigon": "Hồ Chí Minh", "sài gòn": "Hồ Chí Minh",
    "ho chi minh": "Hồ Chí Minh", "ho chi minh city": "Hồ Chí Minh",
    "hồ chí minh": "Hồ Chí Minh", "tan son nhat": "Hồ Chí Minh",

    # Đà Nẵng
    "dn": "Đà Nẵng", "danang": "Đà Nẵng", "da nang": "Đà Nẵng",
    "đà nẵng": "Đà Nẵng", "da năng": "Đà Nẵng",

    # Phú Quốc
    "pq": "Phú Quốc", "phu quoc": "Phú Quốc", "phú quốc": "Phú Quốc",
    "phu quốc": "Phú Quốc",

    # Nha Trang
    "nt": "Nha Trang", "nhatrang": "Nha Trang", "nha trang": "Nha Trang",
    "cam ranh": "Nha Trang", "cảm ranh": "Nha Trang",

    # Đà Lạt
    "dl": "Đà Lạt", "dalat": "Đà Lạt", "da lat": "Đà Lạt",
    "đà lạt": "Đà Lạt", "lien khuong": "Đà Lạt",

    # Huế
    "hue": "Huế", "huế": "Huế", "phu bai": "Huế",

    # Hải Phòng
    "hp": "Hải Phòng", "hai phong": "Hải Phòng", "hải phòng": "Hải Phòng",
    "cat bi": "Hải Phòng",

    # Cần Thơ
    "ct": "Cần Thơ", "can tho": "Cần Thơ", "cần thơ": "Cần Thơ",

    # Hà Giang
    "ha giang": "Hà Giang", "hà giang": "Hà Giang", "hg": "Hà Giang",

    # Điện Biên
    "dien bien": "Điện Biên", "điện biên": "Điện Biên", "db": "Điện Biên",
    "dien bien phu": "Điện Biên", "điện biên phủ": "Điện Biên",
}


def normalize_city(name: str) -> str:
    """Chuẩn hóa tên thành phố về dạng chuẩn trong DB."""
    key = name.strip().lower()
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    # Partial match
    for alias, standard in CITY_ALIASES.items():
        if alias in key:
            return standard
    # Fallback: Title-case
    return name.strip().title()


def get_known_cities() -> list[str]:
    return sorted({v for v in CITY_ALIASES.values()})


# ─────────────────────────────────────────────────────────────────────────────
#  AIRPORT CITIES — thành phố có sân bay thương mại
# ─────────────────────────────────────────────────────────────────────────────
AIRPORT_CITIES: set[str] = {
    "Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Phú Quốc", "Nha Trang",
    "Đà Lạt", "Hải Phòng", "Huế", "Cần Thơ", "Buôn Ma Thuột",
    "Pleiku", "Quy Nhơn", "Vinh", "Thanh Hoá", "Chu Lai", "Điện Biên",
}


# ═══════════════════════════════════════════════════════════════════════════════
#  FLIGHTS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

FLIGHTS_DB: dict[tuple[str, str], list[dict]] = {

    # ── Hà Nội ↔ Đà Nẵng ────────────────────────────────────────────────────
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20",
         "price": 1_450_000, "class": "economy", "duration": "1h20m"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20",
         "price": 2_800_000, "class": "business", "duration": "1h20m"},
        {"airline": "VietJet Air",       "departure": "08:30", "arrival": "09:50",
         "price": 890_000,   "class": "economy", "duration": "1h20m"},
        {"airline": "Bamboo Airways",    "departure": "11:00", "arrival": "12:20",
         "price": 1_200_000, "class": "economy", "duration": "1h20m"},
        {"airline": "VietJet Air",       "departure": "18:00", "arrival": "19:15",
         "price": 750_000,   "class": "economy", "duration": "1h15m"},
    ],

    # ── Hà Nội ↔ Phú Quốc ───────────────────────────────────────────────────
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15",
         "price": 2_100_000, "class": "economy", "duration": "2h15m"},
        {"airline": "VietJet Air",       "departure": "10:00", "arrival": "12:15",
         "price": 1_350_000, "class": "economy", "duration": "2h15m"},
        {"airline": "VietJet Air",       "departure": "16:00", "arrival": "18:15",
         "price": 1_100_000, "class": "economy", "duration": "2h15m"},
        {"airline": "Bamboo Airways",    "departure": "13:30", "arrival": "15:45",
         "price": 1_580_000, "class": "economy", "duration": "2h15m"},
    ],

    # ── Hà Nội ↔ Hồ Chí Minh ────────────────────────────────────────────────
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10",
         "price": 1_600_000, "class": "economy", "duration": "2h10m"},
        {"airline": "VietJet Air",       "departure": "07:30", "arrival": "09:40",
         "price": 950_000,   "class": "economy", "duration": "2h10m"},
        {"airline": "Bamboo Airways",    "departure": "12:00", "arrival": "14:10",
         "price": 1_300_000, "class": "economy", "duration": "2h10m"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10",
         "price": 3_200_000, "class": "business", "duration": "2h10m"},
        {"airline": "VietJet Air",       "departure": "20:30", "arrival": "22:40",
         "price": 820_000,   "class": "economy", "duration": "2h10m"},
    ],

    # ── Hồ Chí Minh ↔ Đà Nẵng ───────────────────────────────────────────────
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20",
         "price": 1_300_000, "class": "economy", "duration": "1h20m"},
        {"airline": "VietJet Air",       "departure": "13:00", "arrival": "14:20",
         "price": 780_000,   "class": "economy", "duration": "1h20m"},
        {"airline": "Bamboo Airways",    "departure": "16:00", "arrival": "17:20",
         "price": 1_050_000, "class": "economy", "duration": "1h20m"},
    ],

    # ── Hồ Chí Minh ↔ Phú Quốc ──────────────────────────────────────────────
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00",
         "price": 1_100_000, "class": "economy", "duration": "1h00m"},
        {"airline": "VietJet Air",       "departure": "15:00", "arrival": "16:00",
         "price": 650_000,   "class": "economy", "duration": "1h00m"},
        {"airline": "Bamboo Airways",    "departure": "11:00", "arrival": "12:00",
         "price": 880_000,   "class": "economy", "duration": "1h00m"},
    ],

    # ── Hà Nội ↔ Nha Trang ──────────────────────────────────────────────────
    ("Hà Nội", "Nha Trang"): [
        {"airline": "Vietnam Airlines", "departure": "06:30", "arrival": "08:30",
         "price": 1_750_000, "class": "economy", "duration": "2h00m"},
        {"airline": "VietJet Air",       "departure": "11:00", "arrival": "13:00",
         "price": 1_050_000, "class": "economy", "duration": "2h00m"},
        {"airline": "Bamboo Airways",    "departure": "14:30", "arrival": "16:30",
         "price": 1_280_000, "class": "economy", "duration": "2h00m"},
    ],

    # ── Hà Nội ↔ Đà Lạt ────────────────────────────────────────────────────
    ("Hà Nội", "Đà Lạt"): [
        {"airline": "Vietnam Airlines", "departure": "07:30", "arrival": "09:30",
         "price": 1_900_000, "class": "economy", "duration": "2h00m"},
        {"airline": "VietJet Air",       "departure": "13:00", "arrival": "15:00",
         "price": 1_150_000, "class": "economy", "duration": "2h00m"},
    ],

    # ── Hồ Chí Minh ↔ Nha Trang ────────────────────────────────────────────
    ("Hồ Chí Minh", "Nha Trang"): [
        {"airline": "Vietnam Airlines", "departure": "08:30", "arrival": "09:30",
         "price": 980_000,   "class": "economy", "duration": "1h00m"},
        {"airline": "VietJet Air",       "departure": "14:00", "arrival": "15:00",
         "price": 590_000,   "class": "economy", "duration": "1h00m"},
        {"airline": "Bamboo Airways",    "departure": "17:00", "arrival": "18:00",
         "price": 750_000,   "class": "economy", "duration": "1h00m"},
    ],

    # ── Hồ Chí Minh ↔ Đà Lạt ───────────────────────────────────────────────
    ("Hồ Chí Minh", "Đà Lạt"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:00",
         "price": 850_000,   "class": "economy", "duration": "1h00m"},
        {"airline": "VietJet Air",       "departure": "15:30", "arrival": "16:30",
         "price": 520_000,   "class": "economy", "duration": "1h00m"},
    ],

    # ── Đà Nẵng ↔ Phú Quốc ──────────────────────────────────────────────────
    ("Đà Nẵng", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "10:00", "arrival": "11:30",
         "price": 1_400_000, "class": "economy", "duration": "1h30m"},
        {"airline": "VietJet Air",       "departure": "16:00", "arrival": "17:30",
         "price": 980_000,   "class": "economy", "duration": "1h30m"},
    ],

    # ── Điện Biên ↔ Phú Quốc (mock cho tối ưu lộ trình từ vùng núi phía Bắc) ──
    ("Điện Biên", "Phú Quốc"): [
        {"airline": "VietJet Air",       "departure": "09:20", "arrival": "11:50",
         "price": 980_000,   "class": "economy", "duration": "2h30m"},
        {"airline": "Vietnam Airlines", "departure": "15:10", "arrival": "17:40",
         "price": 1_250_000, "class": "economy", "duration": "2h30m"},
    ],
}


def lookup_flights(origin: str, destination: str) -> list[dict] | None:
    """
    Tra cứu FLIGHTS_DB với cả chiều xuôi và ngược.
    Trả về list các chuyến bay hoặc None nếu không tìm thấy.
    """
    o = normalize_city(origin)
    d = normalize_city(destination)
    # Chiều xuôi
    if (o, d) in FLIGHTS_DB:
        return FLIGHTS_DB[(o, d)]
    # Chiều ngược (nếu route là khứ hồi ta vẫn có dữ liệu)
    if (d, o) in FLIGHTS_DB:
        return FLIGHTS_DB[(d, o)]
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  HOTELS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

HOTELS_DB: dict[str, list[dict]] = {

    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury",    "stars": 5, "price_per_night": 1_800_000,
         "area": "Mỹ Khê",    "rating": 4.5, "amenities": ["pool", "gym", "spa", "beach"]},
        {"name": "Sala Danang Beach",     "stars": 4, "price_per_night": 1_200_000,
         "area": "Mỹ Khê",    "rating": 4.3, "amenities": ["pool", "gym", "breakfast"]},
        {"name": "Fivitel Danang",        "stars": 3, "price_per_night": 650_000,
         "area": "Sơn Trà",   "rating": 4.1, "amenities": ["breakfast", "wifi"]},
        {"name": "Memory Hostel",         "stars": 2, "price_per_night": 250_000,
         "area": "Hải Châu",  "rating": 4.6, "amenities": ["wifi", "locker"]},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350_000,
         "area": "An Thượng",  "rating": 4.7, "amenities": ["wifi", "kitchen", "breakfast"]},
    ],

    "Phú Quốc": [
        {"name": "Vinpearl Resort",       "stars": 5, "price_per_night": 3_500_000,
         "area": "Bãi Dài",    "rating": 4.4, "amenities": ["pool", "beach", "spa", "gym"]},
        {"name": "Sol by Meliá",          "stars": 4, "price_per_night": 1_500_000,
         "area": "Bãi Trường", "rating": 4.2, "amenities": ["pool", "beach", "gym"]},
        {"name": "Lahana Resort",         "stars": 3, "price_per_night": 800_000,
         "area": "Dương Đông", "rating": 4.0, "amenities": ["pool", "breakfast"]},
        {"name": "9Station Hostel",       "stars": 2, "price_per_night": 200_000,
         "area": "Dương Đông", "rating": 4.5, "amenities": ["wifi", "locker", "pool"]},
        {"name": "Coco Palm Resort",      "stars": 3, "price_per_night": 950_000,
         "area": "Bãi Trường", "rating": 4.2, "amenities": ["pool", "beach", "breakfast"]},
    ],

    "Hồ Chí Minh": [
        {"name": "Rex Hotel",             "stars": 5, "price_per_night": 2_800_000,
         "area": "Quận 1",    "rating": 4.3, "amenities": ["pool", "gym", "spa", "restaurant"]},
        {"name": "Liberty Central",       "stars": 4, "price_per_night": 1_400_000,
         "area": "Quận 1",    "rating": 4.1, "amenities": ["pool", "gym", "breakfast"]},
        {"name": "Cochin Zen Hotel",      "stars": 3, "price_per_night": 550_000,
         "area": "Quận 3",    "rating": 4.4, "amenities": ["breakfast", "wifi"]},
        {"name": "The Common Room",       "stars": 2, "price_per_night": 180_000,
         "area": "Quận 1",    "rating": 4.6, "amenities": ["wifi", "locker", "cafe"]},
        {"name": "Silverland Jolie Hotel","stars": 4, "price_per_night": 1_650_000,
         "area": "Quận 1",    "rating": 4.2, "amenities": ["pool", "breakfast", "gym"]},
    ],

    "Hà Nội": [
        {"name": "Sofitel Legend Metropole","stars": 5, "price_per_night": 5_500_000,
         "area": "Hoàn Kiếm", "rating": 4.8, "amenities": ["pool", "spa", "gym", "restaurant"]},
        {"name": "Mövenpick Hanoi",        "stars": 5, "price_per_night": 2_900_000,
         "area": "Ba Đình",   "rating": 4.5, "amenities": ["pool", "gym", "breakfast"]},
        {"name": "Hanoi La Siesta Hotel",  "stars": 4, "price_per_night": 1_350_000,
         "area": "Hoàn Kiếm", "rating": 4.6, "amenities": ["pool", "breakfast", "spa"]},
        {"name": "Viet Hostel",            "stars": 2, "price_per_night": 220_000,
         "area": "Hoàn Kiếm", "rating": 4.4, "amenities": ["wifi", "locker", "breakfast"]},
        {"name": "Golden Lotus Luxury",    "stars": 3, "price_per_night": 750_000,
         "area": "Hoàn Kiếm", "rating": 4.3, "amenities": ["breakfast", "wifi", "gym"]},
    ],

    "Nha Trang": [
        {"name": "Vinpearl Nha Trang Bay", "stars": 5, "price_per_night": 3_200_000,
         "area": "Hòn Tre",   "rating": 4.5, "amenities": ["beach", "pool", "spa", "gym"]},
        {"name": "Seahorse Resort",        "stars": 4, "price_per_night": 1_100_000,
         "area": "Trần Phú",  "rating": 4.2, "amenities": ["pool", "beach", "breakfast"]},
        {"name": "Gold Coast Hotel",       "stars": 3, "price_per_night": 680_000,
         "area": "Trần Phú",  "rating": 4.0, "amenities": ["breakfast", "wifi", "pool"]},
        {"name": "Lucky Hostel",           "stars": 2, "price_per_night": 190_000,
         "area": "Tháp Bà",   "rating": 4.3, "amenities": ["wifi", "locker"]},
    ],

    "Đà Lạt": [
        {"name": "Dalat Palace Heritage",  "stars": 5, "price_per_night": 2_500_000,
         "area": "Trung Tâm", "rating": 4.6, "amenities": ["spa", "restaurant", "garden"]},
        {"name": "TTC Hotel Premium",      "stars": 4, "price_per_night": 1_050_000,
         "area": "Hồ Xuân Hương", "rating": 4.3, "amenities": ["breakfast", "pool", "gym"]},
        {"name": "Dreams Hotel Dalat",     "stars": 3, "price_per_night": 550_000,
         "area": "Trung Tâm", "rating": 4.5, "amenities": ["breakfast", "wifi"]},
        {"name": "Peace Hostel",           "stars": 2, "price_per_night": 170_000,
         "area": "Chợ Đà Lạt","rating": 4.7, "amenities": ["wifi", "locker", "breakfast"]},
    ],
}


def lookup_hotels(city: str, max_price: int | None = None,
                  min_stars: int | None = None) -> list[dict] | None:
    """
    Tra cứu HOTELS_DB theo thành phố, có thể lọc theo giá và số sao.
    Trả về list đã sắp xếp theo rating giảm dần, hoặc None.
    """
    c = normalize_city(city)
    hotels = HOTELS_DB.get(c)
    if not hotels:
        return None
    result = list(hotels)
    if max_price is not None:
        result = [h for h in result if h["price_per_night"] <= max_price]
    if min_stars is not None:
        result = [h for h in result if h["stars"] >= min_stars]
    result.sort(key=lambda h: h["rating"], reverse=True)
    return result
