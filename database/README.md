# Database

Thư mục này chứa schema và seed PostgreSQL của TravelBuddy AI.

## Cấu Trúc

```text
database/
├── travel_buddy_db/       # Schema canonical + seed, mount vào Postgres
└── README.md
```

> `travel_buddy_db/` được mount vào `/docker-entrypoint-initdb.d`. Postgres chạy
> tất cả file `.sql` trong đúng folder này theo thứ tự tên (01→02→03→04), trộn cả
> migration (`01_schema`, `02_community_social`) lẫn seed. Vì init-dir không đọc
> subfolder nên các file phải nằm chung; prefix số chính là thứ tự thực thi.

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

Backend data pipeline nằm tại:

```text
backend/src/api/travel_api/
```

Script wrapper chạy từ root project nằm tại:

```text
scripts/run_data_pipeline.py
```

## Lưu Ý

- `database/travel_buddy_db` đang được mount vào container PostgreSQL.
- Không đổi đường dẫn này nếu chưa cập nhật `docker-compose.yml`.
- Khi cần migration tool thật (Alembic/Flyway) ở phase sau thì tạo lại `migrations/` và chuyển mount tương ứng.
- Thiết kế chi tiết các bảng: [../docs/data/MO_TA_CO_SO_DU_LIEU.md](../docs/data/MO_TA_CO_SO_DU_LIEU.md).
