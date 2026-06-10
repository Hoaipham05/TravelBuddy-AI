# Travel Buddy — API Data Pipeline

## Cấu trúc project

```
travel_api/
├── pipeline.py              # Điểm vào chính, chạy tất cả collectors
├── .env.example             # Mẫu cấu hình API keys
├── collectors/
│   ├── opentripmap.py       # Điểm tham quan + khách sạn (OpenTripMap)
│   ├── amadeus.py           # Vé máy bay realtime (Amadeus)
│   ├── weather.py           # Thời tiết 7 ngày (Open-Meteo)
│   ├── countries.py         # Thông tin quốc gia (RestCountries)
│   └── exchange_rate.py     # Tỷ giá tiền tệ (Frankfurter)
├── db/
│   └── connection.py        # Kết nối PostgreSQL, helper upsert
├── utils/
│   └── helpers.py           # safe_get, slugify, log_response
└── evidence/                # Raw JSON responses (minh chứng cho báo cáo)
```

---

## Cài đặt

```bash
pip install requests psycopg2-binary python-dotenv
cp .env.example .env
# Điền DB credentials + API keys vào .env
```

---

## Đăng ký API Keys

### 1. OpenTripMap (điểm tham quan)
- URL: https://dev.opentripmap.org/product
- Thời gian: ~2 phút
- Free tier: 500 request/ngày
- Điền vào `.env`: `OPENTRIPMAP_KEY=...`

### 2. Amadeus (vé máy bay)
- URL: https://developers.amadeus.com → Self-Service → Create App
- Thời gian: ~5 phút, cần tài khoản
- Sandbox: unlimited requests, data gần thực
- Điền vào `.env`: `AMADEUS_API_KEY=...` và `AMADEUS_API_SECRET=...`

### 3. Open-Meteo, RestCountries, Frankfurter
- **Không cần đăng ký** — gọi trực tiếp

---

## Chạy pipeline

```bash
cd travel_api

# Chạy 3 API không cần key ngay (để test)
python pipeline.py --only weather
python pipeline.py --only exchange_rate
python pipeline.py --only countries

# Sau khi có key
python pipeline.py --only opentripmap
python pipeline.py --only amadeus

# Chạy tất cả
python pipeline.py

# Xem tóm tắt DB
python pipeline.py --summary
```

---

## Nguồn dữ liệu — Bảng trích dẫn cho Báo cáo

| STT | API | Nhà cung cấp | Loại data | License | URL |
|-----|-----|-------------|-----------|---------|-----|
| 1 | OpenTripMap API | OpenTripMap.com | Điểm tham quan, POI, khách sạn | CC BY-SA | https://dev.opentripmap.org |
| 2 | Amadeus Flight Offers | Amadeus for Developers | Giá vé máy bay, lịch bay | Commercial (free sandbox) | https://developers.amadeus.com |
| 3 | Open-Meteo API | Open-Meteo.com | Thời tiết realtime, dự báo 7 ngày | CC BY 4.0 | https://open-meteo.com |
| 4 | REST Countries API v3.1 | restcountries.com | Thông tin quốc gia, tiền tệ, visa | Mozilla Public License 2.0 | https://restcountries.com |
| 5 | Frankfurter API | Frankfurter.app | Tỷ giá hối đoái (nguồn ECB) | MIT | https://frankfurter.app |

> **Ghi chú cho báo cáo:** Toàn bộ response JSON raw được lưu trong thư mục `evidence/` mỗi lần chạy pipeline. File JSON có timestamp và metadata nguồn API — dùng làm minh chứng đính kèm báo cáo.

---

## Minh chứng data cho giáo viên

Sau khi chạy pipeline, thư mục `evidence/` sẽ có các file như:

```
evidence/
├── flights_HAN_DAD_2026-06-17.json   ← Response thực từ Amadeus
├── flights_HAN_BKK_2026-06-20.json
├── price_metrics_HAN_DAD.json
└── ...
```

Mỗi file có cấu trúc:
```json
{
  "_meta": {
    "source": "Amadeus for Developers API",
    "env": "test",
    "endpoint": "https://test.api.amadeus.com/v2/shopping/flight-offers",
    "collected": "2026-06-09T14:30:00",
    "docs": "https://developers.amadeus.com/self-service/category/flights"
  },
  "data": { ... raw response ... }
}
```

---

## Luồng hoạt động trong hệ thống

```
Người dùng tìm chuyến đi
        │
        ▼
Backend FastAPI nhận request
        │
        ├── destinations, hotels  ← DB (từ OpenTripMap, đã lưu)
        ├── weather               ← DB (từ Open-Meteo, cập nhật hàng ngày)
        ├── exchange_rates        ← DB (từ Frankfurter, cập nhật hàng ngày)
        ├── country info          ← DB (từ RestCountries, ổn định)
        └── flights               ← Gọi Amadeus API realtime (cache 15 phút)
                │
                ▼
        Trả về response tổng hợp cho frontend
```
