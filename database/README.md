# Database

Thư mục này chứa schema, seed và các placeholder liên quan đến dữ liệu PostgreSQL của TravelBuddy AI.

## Cấu Trúc

```text
database/
├── travel_buddy_db/       # Schema canonical và seed đang chạy trong Docker
├── migrations/            # Placeholder cho migration thật sau này
├── seeds/                 # Placeholder cho seed chia nhỏ sau này
└── README.md
```

## Thư Mục Đang Dùng Chính

Schema và seed hiện tại nằm tại:

```text
database/travel_buddy_db/
```

Các file chính:

- `01_schema.sql`: tạo toàn bộ bảng dữ liệu theo kiến trúc hybrid realtime/cache.
- `02_seed_data.sql`: seed dữ liệu tĩnh, không seed giá vé/giá phòng giả.
- `03_seed_pois_curated.sql`: bổ sung 150 POI curated cho 10 điểm đến nội địa.
- `04_seed_booking_links.sql`: chuẩn hóa/backfill link đặt vé, đặt phòng.
- `04_seed_booking_links.sql`: chuẩn hóa/backfill link đặt vé, đặt phòng.

Backend data pipeline nằm tại:

```text
backend/src/api/travel_api/
```

Script wrapper chạy từ root project nằm tại:

```text
scripts/run_data_pipeline.py
```

## Lưu Ý

- `database/travel_buddy_db` đang được mount vào container PostgreSQL tại `/travel_buddy_db`.
- Không đổi đường dẫn này nếu chưa cập nhật `docker-compose.yml`.
- `migrations/` và `seeds/` được giữ để chuyển sang migration tool sau này, ví dụ Alembic hoặc Flyway.
