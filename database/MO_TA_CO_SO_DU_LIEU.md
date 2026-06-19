# THIẾT KẾ CƠ SỞ DỮ LIỆU — TravelBuddy AI

> Hệ quản trị CSDL: **PostgreSQL 14+**. Khóa chính dùng `UUID` (sinh tự động). Các trường linh hoạt dùng kiểu `JSONB`. Dữ liệu giá vé / giá phòng / thời tiết là **snapshot có thời hạn** (`expires_at`) lấy từ API ngoài rồi cache lại.

## 1. Tổng quan các nhóm bảng

| Nhóm | Bảng | Vai trò |
|---|---|---|
| Người dùng | `users` | Tài khoản, hồ sơ, điểm thưởng |
| Điểm đến | `destinations`, `pois` | Thành phố/điểm du lịch và điểm tham quan |
| Chuyến bay | `airports`, `airlines`, `flight_routes`, `flight_price_snapshots` | Sân bay, hãng bay, tuyến bay và giá vé |
| Khách sạn | `hotels`, `hotel_rate_snapshots` | Khách sạn và giá phòng theo ngày |
| Thời tiết | `weather_cache`, `weather_daily_forecasts` | Cache dự báo và dự báo theo ngày |
| Chuyến đi | `trips`, `trip_days`, `itinerary_items`, `trip_members` | Kế hoạch chuyến đi, lịch trình, thành viên |
| Cộng đồng | `reviews`, `community_comments` | Bài đánh giá và bình luận |

---

## 2. Mô tả chi tiết các bảng cốt lõi

### 2.1. `users` — Người dùng
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh người dùng |
| full_name | VARCHAR(120) | NOT NULL | Họ tên |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email đăng nhập |
| password_hash | VARCHAR(255) | | Mật khẩu băm (Argon2) |
| google_sub | VARCHAR(255) | UNIQUE | ID đăng nhập Google OAuth |
| travel_preferences | JSONB | DEFAULT '{}' | Sở thích du lịch |
| total_points / level | INT / VARCHAR | | Điểm thưởng và cấp độ (Explorer...) |

### 2.2. `destinations` — Điểm đến
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh điểm đến |
| name / slug | VARCHAR | slug UNIQUE | Tên và đường dẫn |
| country_code | CHAR(2) | DEFAULT 'VN' | Mã quốc gia |
| lat / lng | NUMERIC(9,6) | | Tọa độ |
| tags / best_months | JSONB | | Thẻ phân loại, tháng đẹp nhất |
| avg_rating / review_count | NUMERIC / INT | | Điểm đánh giá trung bình |

### 2.3. `pois` — Điểm tham quan (Point of Interest)
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh POI |
| destination_id | UUID | FK → destinations | Thuộc điểm đến nào |
| name / category | VARCHAR | | Tên, loại (beach, historic, museum...) |
| lat / lng | NUMERIC(9,6) | | Tọa độ (để gom cụm lịch trình) |
| entrance_fee_amount | NUMERIC(14,2) | | Giá vé vào cửa |
| estimated_duration_min | INT | | Thời gian tham quan ước tính |

### 2.4. Nhóm chuyến bay
**`airports`**: `iata_code` (PK), name, city, country_code, lat/lng.
**`airlines`**: `iata_code` (PK), name, country_code, logo_url.
**`flight_routes`**: id (PK), `origin_iata` (FK), `destination_iata` (FK), `destination_id` (FK), `route_key` (UNIQUE) — định nghĩa một tuyến bay A→B.
**`flight_price_snapshots`**: id (PK), `route_id` (FK), `airline_iata` (FK), departure_date, price_amount, currency, `expires_at` — bản chụp giá vé tại một thời điểm.

### 2.5. Nhóm khách sạn
**`hotels`**: id (PK), `destination_id` (FK), name, stars, amenities (JSONB), avg_rating.
**`hotel_rate_snapshots`**: id (PK), `hotel_id` (FK), checkin_date, checkout_date, price_amount, `expires_at` — bản chụp giá phòng theo khoảng ngày.

### 2.6. Nhóm thời tiết
**`weather_cache`**: id (PK), `destination_id` (FK), cache_key (UNIQUE), forecast_days, `expires_at`, raw (JSONB) — cache phản hồi từ Open-Meteo.
**`weather_daily_forecasts`**: id (PK), `weather_cache_id` (FK), `destination_id` (FK), forecast_date, temp_max_c/temp_min_c, travel_score — dự báo từng ngày.

### 2.7. Nhóm chuyến đi (lập kế hoạch)
**`trips`**: id (PK), `owner_id` (FK → users), `destination_id` (FK), title, start/end_date, budget_amount, status, is_public, clone_count.
**`trip_days`**: id (PK), `trip_id` (FK), day_number, date — các ngày trong chuyến đi.
**`itinerary_items`**: id (PK), `day_id` (FK), item_type, `poi_id`/`hotel_id`/`flight_snapshot_id` (FK), start_time, cost_amount — từng hoạt động trong ngày.
**`trip_members`**: `trip_id` + `user_id` (PK kép, FK), role (owner/editor/viewer) — quan hệ **n-n** giữa người dùng và chuyến đi.

### 2.8. Nhóm cộng đồng
**`reviews`**: id (PK), `user_id` (FK), `destination_id`/`hotel_id`/`poi_id` (FK — chỉ 1 trong 3), rating (1-5), content, images (JSONB), helpful_count, trip_data (JSONB).
**`community_comments`**: id (PK), `review_id` (FK), `user_id` (FK), `parent_id` (FK tự tham chiếu — bình luận lồng nhau), content.

---

## 3. Các quan hệ chính (cardinality)

| Quan hệ | Loại |
|---|---|
| users — trips (owner_id) | 1 — n |
| users — trips (qua trip_members) | n — n |
| destinations — pois / hotels / flight_routes / weather_cache | 1 — n |
| trips — trip_days — itinerary_items | 1 — n — n |
| flight_routes — flight_price_snapshots | 1 — n |
| hotels — hotel_rate_snapshots | 1 — n |
| weather_cache — weather_daily_forecasts | 1 — n |
| reviews — community_comments | 1 — n |
| community_comments — community_comments (parent_id) | 1 — n (tự tham chiếu) |

---

## 4. Quyết định thiết kế đáng chú ý

1. **Tách `pois` khỏi `destinations`**: để Trip Builder gom cụm điểm tham quan theo tọa độ, và mỗi điểm đến có nhiều POI.
2. **Snapshot + `expires_at`**: giá vé/giá phòng/thời tiết thay đổi liên tục → lưu dạng bản chụp có thời hạn thay vì gắn cứng, vừa cache giảm gọi API vừa giữ lịch sử giá.
3. **Dùng `JSONB`** cho dữ liệu linh hoạt (tags, amenities, travel_preferences, trip_data) — không cần thêm bảng phụ.
4. **Ràng buộc CHECK đa hình** ở `reviews`: một review chỉ gắn đúng **một** đối tượng (điểm đến HOẶC khách sạn HOẶC POI).
5. **`UUID` làm khóa chính**: thuận lợi khi đồng bộ/phân tán, tránh lộ số lượng bản ghi.
