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

`airports` — Sân bay
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| iata_code | CHAR(3) | PK | Mã sân bay IATA |
| name / city | VARCHAR | | Tên sân bay, thành phố |
| country_code | CHAR(2) | NOT NULL | Mã quốc gia |
| lat / lng | NUMERIC(9,6) | | Tọa độ |

`airlines` — Hãng bay
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| iata_code | CHAR(2) | PK | Mã hãng bay IATA |
| name | VARCHAR | | Tên hãng |
| country_code | CHAR(2) | | Mã quốc gia |
| logo_url | TEXT | | Logo hãng |

`flight_routes` — Tuyến bay
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh tuyến bay |
| origin_iata | CHAR(3) | FK → airports | Sân bay đi |
| destination_iata | CHAR(3) | FK → airports | Sân bay đến |
| destination_id | UUID | FK → destinations | Điểm đến gắn với tuyến |
| route_key | VARCHAR(7) | UNIQUE | Khóa định danh tuyến A→B |

`flight_price_snapshots` — Bản chụp giá vé
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh bản chụp giá |
| route_id | UUID | FK → flight_routes | Thuộc tuyến nào |
| airline_iata | CHAR(2) | FK → airlines | Hãng bay |
| departure_date | DATE | NOT NULL | Ngày bay |
| price_amount / currency | NUMERIC(14,2) / CHAR(3) | | Giá vé và tiền tệ |
| expires_at | TIMESTAMPTZ | NOT NULL | Thời điểm hết hạn cache |

### 2.5. Nhóm khách sạn

`hotels` — Khách sạn
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh khách sạn |
| destination_id | UUID | FK → destinations | Thuộc điểm đến nào |
| name | VARCHAR | | Tên khách sạn |
| stars | NUMERIC(2,1) | CHECK 0–5 | Hạng sao |
| amenities | JSONB | DEFAULT '[]' | Tiện ích |
| avg_rating | NUMERIC | | Điểm đánh giá trung bình |

`hotel_rate_snapshots` — Bản chụp giá phòng
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh bản chụp giá |
| hotel_id | UUID | FK → hotels | Thuộc khách sạn nào |
| checkin_date / checkout_date | DATE | checkout > checkin | Khoảng ngày ở |
| price_amount / currency | NUMERIC(14,2) / CHAR(3) | | Giá phòng và tiền tệ |
| expires_at | TIMESTAMPTZ | NOT NULL | Thời điểm hết hạn cache |

### 2.6. Nhóm thời tiết

`weather_cache` — Cache dự báo
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh bản cache |
| destination_id | UUID | FK → destinations | Thuộc điểm đến nào |
| cache_key | VARCHAR(220) | UNIQUE | Khóa cache |
| forecast_days | SMALLINT | DEFAULT 16 | Số ngày dự báo |
| raw | JSONB | | Phản hồi gốc từ Open-Meteo |
| expires_at | TIMESTAMPTZ | NOT NULL | Thời điểm hết hạn cache |

`weather_daily_forecasts` — Dự báo theo ngày
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh bản ghi |
| weather_cache_id | UUID | FK → weather_cache | Thuộc bản cache nào |
| destination_id | UUID | FK → destinations | Thuộc điểm đến nào |
| forecast_date | DATE | NOT NULL | Ngày dự báo |
| temp_max_c / temp_min_c | NUMERIC(5,2) | | Nhiệt độ cao/thấp nhất |
| travel_score | SMALLINT | CHECK 0–100 | Điểm phù hợp du lịch |

### 2.7. Nhóm chuyến đi (lập kế hoạch)

`trips` — Chuyến đi
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh chuyến đi |
| owner_id | UUID | FK → users | Người tạo chuyến |
| destination_id | UUID | FK → destinations | Điểm đến |
| title | VARCHAR | | Tên chuyến đi |
| start_date / end_date | DATE | | Ngày bắt đầu/kết thúc |
| budget_amount / currency | NUMERIC / CHAR(3) | | Ngân sách |
| status / is_public / clone_count | VARCHAR / BOOLEAN / INT | | Trạng thái, công khai, số lần được clone |

`trip_days` — Ngày trong chuyến
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh ngày |
| trip_id | UUID | FK → trips | Thuộc chuyến nào |
| day_number | SMALLINT | UNIQUE theo trip | Ngày thứ mấy |
| date | DATE | | Ngày cụ thể |

`itinerary_items` — Hoạt động trong ngày
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh hoạt động |
| day_id | UUID | FK → trip_days | Thuộc ngày nào |
| item_type | VARCHAR(40) | NOT NULL | Loại hoạt động |
| poi_id / hotel_id / flight_snapshot_id | UUID | FK | Đối tượng gắn kèm |
| start_time | TIME | | Giờ bắt đầu |
| cost_amount / currency | NUMERIC(14,2) / CHAR(3) | | Chi phí |

`trip_members` — Thành viên chuyến đi
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| trip_id + user_id | UUID | PK kép, FK | Quan hệ **n-n** người dùng ↔ chuyến đi |
| role | VARCHAR | | Vai trò (owner / editor / viewer) |

### 2.8. Nhóm cộng đồng

`reviews` — Bài đánh giá
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh bài đánh giá |
| user_id | UUID | FK → users | Người viết |
| destination_id / hotel_id / poi_id | UUID | FK (chỉ 1 trong 3) | Đối tượng được đánh giá |
| rating | INT | CHECK 1–5 | Điểm đánh giá |
| content | TEXT | | Nội dung |
| images / trip_data | JSONB | | Ảnh đính kèm, dữ liệu chuyến đi |
| helpful_count | INT | DEFAULT 0 | Số lượt thấy hữu ích |

`community_comments` — Bình luận
| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| id | UUID | PK | Định danh bình luận |
| review_id | UUID | FK → reviews | Thuộc bài đánh giá nào |
| user_id | UUID | FK → users | Người bình luận |
| parent_id | UUID | FK tự tham chiếu | Bình luận cha (lồng nhau) |
| content | TEXT | | Nội dung |

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
