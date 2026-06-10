"""
Phần mở rộng database.py — được import vào database.py.

Thêm:
  • AIRPORT_CITIES        : Tập các thành phố CÓ sân bay bay thương mại.
  • NEAREST_AIRPORT_CITY  : Thành phố không có sân bay → sân bay gần nhất + cách đi.
  • GROUND_TRANSPORT_DB   : Bus/tàu hoả giữa các cặp thành phố.
  • LONG_HAUL_ROUTES      : Tuyến đường bộ/tàu hoả xuyên Việt (HN → PQC).
"""
from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
#  AIRPORT CITIES (có sân bay thương mại)
# ─────────────────────────────────────────────────────────────────────────────
AIRPORT_CITIES: set[str] = {
    "Hà Nội",
    "Hồ Chí Minh",
    "Đà Nẵng",
    "Phú Quốc",
    "Nha Trang",
    "Đà Lạt",
    "Hải Phòng",
    "Huế",
    "Cần Thơ",
    "Buôn Ma Thuột",
    "Pleiku",
    "Quy Nhơn",
    "Vinh",
    "Thanh Hoá",
    "Chu Lai",   # sân bay Quảng Nam
}

# ─────────────────────────────────────────────────────────────────────────────
#  NEAREST AIRPORT — thành phố KHÔNG có sân bay → sân bay gần nhất
# ─────────────────────────────────────────────────────────────────────────────
# Mỗi entry: {
#   "airport_city": str,
#   "distance_km" : int,
#   "options"     : list[dict]  (các cách di chuyển)
# }
NEAREST_AIRPORT_CITY: dict[str, dict] = {
    "Hưng Yên": {
        "airport_city": "Hà Nội",
        "distance_km": 65,
        "options": [
            {
                "type": "bus_limousine",
                "operator": "Hoàng Long / Phương Trang",
                "departure_points": ["Hưng Yên → Cầu Giấy / Mỹ Đình (Hà Nội)"],
                "duration_min": 90,
                "price_vnd": 80_000,
                "note": "Limousine 9 chỗ, đặt trước tại bến xe Hưng Yên hoặc app",
            },
            {
                "type": "taxi_grab",
                "operator": "Grab / Be",
                "duration_min": 70,
                "price_vnd_range": (350_000, 450_000),
                "note": "Thuê xe từ Hưng Yên thẳng đến sân bay Nội Bài (~70km)",
            },
            {
                "type": "xe_khach",
                "operator": "Xe khách tuyến cố định",
                "departure_points": ["Bến xe Hưng Yên → Bến xe Nước Ngầm / Giáp Bát"],
                "duration_min": 100,
                "price_vnd": 50_000,
                "note": "Xuất bến mỗi 30 phút, sau đó đi tiếp xe buýt/taxi ra sân bay",
            },
        ],
    },
    "Hải Dương": {
        "airport_city": "Hà Nội",
        "distance_km": 57,
        "options": [
            {
                "type": "bus_limousine",
                "operator": "Hoàng Long",
                "duration_min": 75,
                "price_vnd": 70_000,
                "note": "Bến xe Hải Dương → Mỹ Đình",
            },
            {
                "type": "taxi_grab",
                "operator": "Grab",
                "duration_min": 65,
                "price_vnd_range": (300_000, 400_000),
            },
        ],
    },
    "Bắc Ninh": {
        "airport_city": "Hà Nội",
        "distance_km": 30,
        "options": [
            {
                "type": "xe_buyt",
                "operator": "Xe buýt tuyến 204",
                "duration_min": 60,
                "price_vnd": 9_000,
                "note": "Bắc Ninh → Hà Nội, sau đó đi tiếp xe buýt 86 ra Nội Bài",
            },
            {
                "type": "taxi_grab",
                "operator": "Grab",
                "duration_min": 40,
                "price_vnd_range": (180_000, 250_000),
            },
        ],
    },
    "Nam Định": {
        "airport_city": "Hà Nội",
        "distance_km": 90,
        "options": [
            {
                "type": "bus",
                "operator": "Xe khách Nam Định – Hà Nội",
                "duration_min": 120,
                "price_vnd": 90_000,
            },
            {
                "type": "tau_hoa",
                "operator": "Tàu hoả SE",
                "duration_min": 100,
                "price_vnd": 55_000,
                "note": "Ga Nam Định → Ga Hà Nội, tần suất 8 chuyến/ngày",
            },
        ],
    },
    "Ninh Bình": {
        "airport_city": "Hà Nội",
        "distance_km": 93,
        "options": [
            {
                "type": "tau_hoa",
                "operator": "Tàu hoả SE/TN",
                "duration_min": 80,
                "price_vnd": 65_000,
                "note": "Ga Ninh Bình → Ga Hà Nội",
            },
            {
                "type": "bus",
                "operator": "Hoàng Long",
                "duration_min": 110,
                "price_vnd": 80_000,
            },
        ],
    },
    "Vũng Tàu": {
        "airport_city": "Hồ Chí Minh",
        "distance_km": 125,
        "options": [
            {
                "type": "bus",
                "operator": "Phương Trang / Kumho",
                "duration_min": 150,
                "price_vnd": 100_000,
            },
            {
                "type": "phuong_tien_thuy",
                "operator": "Tàu cao tốc Greenlines",
                "duration_min": 75,
                "price_vnd": 250_000,
                "note": "Bến Bạch Đằng (Q1) → Vũng Tàu, nhiều chuyến/ngày",
            },
        ],
    },
    "Hà Giang": {
        # Backward-compatible default used by get_nearest_airport
        "airport_city": "Hà Nội",
        "distance_km": 300,
        "options": [
            {
                "type": "xe_khach",
                "operator": "Quang Nghị / Bằng Phấn",
                "duration_min": 390,
                "price_vnd": 260_000,
                "note": "Hà Giang → Mỹ Đình, sau đó đi Nội Bài",
            },
            {
                "type": "bus_limousine",
                "operator": "Limousine Hà Giang Express",
                "duration_min": 360,
                "price_vnd": 320_000,
            },
        ],
        # New: đa lựa chọn sân bay để tối ưu chi phí/thời gian/chặng
        "airport_options": [
            {
                "airport_city": "Hà Nội",
                "distance_km": 300,
                "options": [
                    {
                        "type": "xe_khach",
                        "operator": "Quang Nghị / Bằng Phấn",
                        "duration_min": 390,
                        "price_vnd": 260_000,
                        "note": "Hà Giang → Mỹ Đình, sau đó đi Nội Bài",
                    },
                    {
                        "type": "bus_limousine",
                        "operator": "Limousine Hà Giang Express",
                        "duration_min": 360,
                        "price_vnd": 320_000,
                    },
                ],
            },
            {
                "airport_city": "Điện Biên",
                "distance_km": 250,
                "options": [
                    {
                        "type": "xe_khach",
                        "operator": "Xe tuyến Hà Giang - Điện Biên",
                        "duration_min": 330,
                        "price_vnd": 230_000,
                        "note": "Tuyến liên tỉnh qua quốc lộ 279",
                    },
                    {
                        "type": "taxi_grab",
                        "operator": "Xe hợp đồng",
                        "duration_min": 280,
                        "price_vnd_range": (1_800_000, 2_400_000),
                    },
                ],
            },
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  GROUND TRANSPORT — giữa các thành phố lớn (bus / tàu hoả)
# ─────────────────────────────────────────────────────────────────────────────
GROUND_TRANSPORT_DB: dict[tuple[str, str], list[dict]] = {

    # ── Hà Nội ↔ Hồ Chí Minh (tàu hoả xuyên Việt) ──────────────────────────
    ("Hà Nội", "Hồ Chí Minh"): [
        {
            "type": "tau_hoa",
            "operator": "VNRailway – Tàu SE3/SE4",
            "duration_h": 30,
            "price_vnd_range": (700_000, 1_500_000),
            "note": "Ghế ngồi mềm → giường nằm điều hoà. Khởi hành 19:30, đến 5:30 hôm sau.",
        },
        {
            "type": "tau_hoa",
            "operator": "VNRailway – Tàu SE1/SE2",
            "duration_h": 32,
            "price_vnd_range": (550_000, 1_300_000),
            "note": "Tàu dừng nhiều ga hơn, phù hợp khám phá dọc đường.",
        },
        {
            "type": "bus_giuong_nam",
            "operator": "Phương Trang / Hoàng Long",
            "duration_h": 36,
            "price_vnd_range": (350_000, 500_000),
            "note": "Xe giường nằm 40 chỗ. Không khuyến khích — rất mệt.",
        },
    ],

    # ── Hà Nội ↔ Đà Nẵng ────────────────────────────────────────────────────
    ("Hà Nội", "Đà Nẵng"): [
        {
            "type": "tau_hoa",
            "operator": "VNRailway – SE7/SE8",
            "duration_h": 16,
            "price_vnd_range": (480_000, 1_100_000),
            "note": "Khởi hành 19:00 từ Hà Nội, đến Đà Nẵng 11:30 hôm sau.",
        },
        {
            "type": "bus_giuong_nam",
            "operator": "Hoàng Long / Kumho",
            "duration_h": 18,
            "price_vnd_range": (250_000, 380_000),
        },
    ],

    # ── Hồ Chí Minh ↔ Phú Quốc (đường thuỷ + bộ) ───────────────────────────
    ("Hồ Chí Minh", "Phú Quốc"): [
        {
            "type": "bus_ferry",
            "operator": "Phương Trang (xe + phà)",
            "duration_h": 7,
            "price_vnd_range": (350_000, 450_000),
            "route": "HCM → Rạch Giá (xe 5h) → Phú Quốc (phà 2h15m)",
            "note": "Phà SuperDong chạy từ Rạch Giá nhiều chuyến/ngày.",
        },
        {
            "type": "bus_ferry",
            "operator": "Tuyến Hà Tiên",
            "duration_h": 9,
            "price_vnd_range": (300_000, 420_000),
            "route": "HCM → Hà Tiên (xe 7h) → Phú Quốc (phà 1h)",
            "note": "Đẹp hơn nhưng lâu hơn tuyến Rạch Giá.",
        },
    ],

    # ── Hà Nội ↔ Phú Quốc (tàu hoả + phà — tuyến dài nhất) ─────────────────
    ("Hà Nội", "Phú Quốc"): [
        {
            "type": "tau_hoa_va_pha",
            "operator": "Tàu hoả + Phà kết hợp",
            "duration_h": 40,
            "price_vnd_range": (900_000, 2_000_000),
            "route": "HN → HCM (tàu 30h) → Rạch Giá (xe 5h) → Phú Quốc (phà 2h)",
            "note": "Tuyến này RẤT dài (~40h). Chỉ phù hợp nếu muốn trải nghiệm hành trình. "
                    "Khuyến nghị mạnh: đi máy bay (~2h15m, giá từ 1.1 triệu).",
        },
    ],

    # ── Đà Nẵng ↔ Hội An ────────────────────────────────────────────────────
    ("Đà Nẵng", "Hội An"): [
        {
            "type": "grab_xe_om",
            "operator": "Grab Car / xe ôm",
            "duration_min": 45,
            "price_vnd_range": (150_000, 250_000),
        },
        {
            "type": "xe_buyt",
            "operator": "Xe buýt tuyến 1",
            "duration_min": 60,
            "price_vnd": 20_000,
        },
    ],
}


def get_airport_candidates(city: str) -> list[dict]:
    """
    Trả về danh sách sân bay có thể dùng cho một thành phố không có sân bay.

    Mỗi phần tử gồm:
      - airport_city
      - distance_km
      - options (phương tiện chặng nối)
    """
    from src.database import normalize_city, AIRPORT_CITIES as _AC

    city_std = normalize_city(city)
    if city_std in _AC:
        return []

    relay = NEAREST_AIRPORT_CITY.get(city_std)
    if not relay:
        return []

    candidates = relay.get("airport_options")
    if candidates:
        out = []
        seen: set[str] = set()
        for c in sorted(candidates, key=lambda x: x.get("distance_km", 9999)):
            ac = c.get("airport_city")
            if not ac or ac in seen:
                continue
            seen.add(ac)
            out.append({
                "airport_city": ac,
                "distance_km": c.get("distance_km", relay.get("distance_km", 0)),
                "options": c.get("options", []),
            })
        return out

    return [{
        "airport_city": relay.get("airport_city", ""),
        "distance_km": relay.get("distance_km", 0),
        "options": relay.get("options", []),
    }]


def get_nearest_airport(city: str) -> dict | None:
    """
    Kiểm tra xem thành phố có sân bay không.
    Nếu không, trả về thông tin sân bay gần nhất và cách di chuyển.
    Nếu có sân bay, trả về None.
    """
    from src.database import normalize_city, AIRPORT_CITIES as _AC
    city_std = normalize_city(city)
    if city_std in _AC:
        return None  # Có sân bay rồi, không cần relay

    cands = get_airport_candidates(city_std)
    if cands:
        return cands[0]
    return None


def lookup_ground_transport(origin: str, destination: str) -> list[dict] | None:
    """
    Tra cứu phương tiện mặt đất / đường thuỷ giữa 2 thành phố.
    Tìm cả chiều xuôi lẫn ngược.
    """
    from src.database import normalize_city
    o = normalize_city(origin)
    d = normalize_city(destination)
    if (o, d) in GROUND_TRANSPORT_DB:
        return GROUND_TRANSPORT_DB[(o, d)]
    if (d, o) in GROUND_TRANSPORT_DB:
        return GROUND_TRANSPORT_DB[(d, o)]
    return None
