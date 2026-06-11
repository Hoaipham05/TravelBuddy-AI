# TravelBuddy AI — Danh sách việc cần làm

> Mỗi task có kèm prompt sẵn để paste vào AI assistant và hoàn thành ngay.
> Thứ tự từ trên xuống dưới = thứ tự ưu tiên thực hiện.

---

## PHASE 1 — Nền tảng Database

---

### Task 1.1 — Thêm PostgreSQL vào docker-compose.yml

**Mô tả:** Bổ sung service `postgres` vào `docker-compose.yml` hiện tại, đảm bảo các service `api` và `worker` chờ DB sẵn sàng trước khi khởi động. Thêm biến môi trường DB vào `.env.example`.

**Prompt:**

```
Dựa vào file docker-compose.yml hiện tại của project TravelBuddy (đã có các service: nginx, frontend, redis, searxng, api, worker), hãy:

1. Thêm service `postgres` dùng image postgres:16-alpine với:
   - Volume persistent: postgres_data
   - Healthcheck dùng pg_isready
   - Biến môi trường: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD đọc từ .env
   - Không expose port ra ngoài host (chỉ internal network travelbuddy)

2. Cập nhật service `api` và `worker` để depends_on postgres với condition: service_healthy

3. Thêm volume `postgres_data` vào phần volumes

4. Thêm các biến sau vào .env.example:
   DB_HOST=postgres
   DB_PORT=5432
   DB_NAME=travel_buddy
   DB_USER=travelbuddy
   DB_PASS=changeme_db_pass

Giữ nguyên toàn bộ cấu hình cũ, chỉ bổ sung thêm.
```

---

### Task 1.2 — Tạo SQLAlchemy models cho 11 bảng

**Mô tả:** Tạo file `backend/src/db/models.py` với SQLAlchemy ORM models tương ứng với schema trong `database/travel_buddy_db/01_schema.sql`. Tạo thêm `backend/src/db/connection.py` cho database session.

**Prompt:**

```
Dựa vào file SQL schema tại database/travel_buddy_db/01_schema.sql (có 11 bảng: users, destinations, hotels, flights, trips, trip_days, itinerary_items, reviews, price_alerts, trip_members, trip_expenses), hãy tạo 2 file:

1. backend/src/db/models.py:
   - Dùng SQLAlchemy 2.x với Mapped[] và mapped_column()
   - Tạo đầy đủ 11 model tương ứng với 11 bảng
   - JSONB columns dùng type JSON
   - UUID dùng uuid.UUID
   - Relationships đầy đủ (User.trips, Destination.hotels, Trip.days, v.v.)
   - Thêm __repr__ cho từng model

2. backend/src/db/connection.py:
   - Đọc DATABASE_URL từ biến môi trường (build từ DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS)
   - create_async_engine dùng asyncpg
   - AsyncSession factory
   - async get_db() dependency cho FastAPI
   - Hàm init_db() tạo tables nếu chưa có

Thêm asyncpg và sqlalchemy[asyncio] vào requirements.txt.
```

---

### Task 1.3 — Chạy và verify schema + seed data

**Mô tả:** Tạo script Python để auto-migrate (chạy 2 file SQL) khi container khởi động lần đầu. Verify dữ liệu đã insert đúng.

**Prompt:**

```
Tạo file backend/src/db/migrate.py với các chức năng:

1. Hàm run_sql_file(conn, filepath) — đọc và chạy file .sql qua psycopg2
2. Hàm migrate() — kiểm tra xem bảng destinations đã tồn tại chưa:
   - Nếu chưa: chạy 01_schema.sql rồi 02_seed_data.sql (đường dẫn relative từ project root)
   - Nếu rồi: log "DB already initialized, skipping"
3. Hàm verify() — in ra số bản ghi trong 6 bảng chính (destinations, hotels, flights, users, trips, reviews)
4. Thêm entry point if __name__ == "__main__": chạy migrate() + verify()

File SQL nằm tại: database/travel_buddy_db/01_schema.sql và 02_seed_data.sql
Dùng psycopg2-binary (đồng bộ, không cần async cho migration script).
In log rõ ràng mỗi bước: "Running schema...", "Running seed data...", "✅ Done".
```

---

## PHASE 2 — Data Pipeline

---

### Task 2.1 — Chạy 3 collectors miễn phí (Open-Meteo, Frankfurter, RestCountries)

**Mô tả:** 3 collectors này không cần API key, chạy được ngay. Cần fix import path và đảm bảo kết nối được DB trong Docker.

**Prompt:**

```
Trong project TravelBuddy, các file collector nằm tại backend/src/api/travel_api/collectors/ (weather.py, exchange_rate.py, countries.py). Hiện tại các file này dùng relative import (from utils.helpers import ...) không chạy được từ ngoài thư mục.

Hãy:
1. Fix tất cả import trong 3 file weather.py, exchange_rate.py, countries.py thành absolute import (from src.api.travel_api.utils.helpers import ...)
2. Fix import trong db/connection.py tương tự
3. Tạo script backend/scripts/run_free_collectors.py:
   - Kết nối PostgreSQL dùng biến môi trường DB_*
   - Chạy tuần tự: ExchangeRateCollector, CountriesCollector, WeatherCollector
   - In progress rõ ràng, catch exception từng collector riêng (1 lỗi không dừng cái khác)
   - In tổng kết cuối: bao nhiêu bản ghi đã insert/update

4. Thêm command vào docker-compose.yml để chạy script này 1 lần sau khi migrate xong (dùng service type: one-shot hoặc entrypoint script)
```

---

### Task 2.2 — Tích hợp Open-Meteo vào bảng weather_cache

**Mô tả:** Đảm bảo dữ liệu thời tiết được lưu vào `weather_cache` và có endpoint API để frontend lấy, phục vụ tính năng Giá thông minh.

**Prompt:**

```
Trong TravelBuddy, collector weather.py đã có sẵn tại backend/src/api/travel_api/collectors/weather.py. Hãy:

1. Verify bảng weather_cache đã được tạo đúng (destination_slug TEXT PRIMARY KEY, data JSONB, updated_at TIMESTAMPTZ)

2. Tạo FastAPI router tại backend/src/api/routes/weather.py với endpoints:
   GET /weather/{destination_slug}
   - Trả về data từ bảng weather_cache
   - Nếu data cũ hơn 6 giờ: gọi lại Open-Meteo API, cập nhật cache, rồi trả về
   - Response schema: { slug, current: {temp_c, condition, is_day}, forecast_7days: [{date, condition, temp_max_c, temp_min_c, rain_mm}] }
   
   GET /weather/batch?slugs=da-nang,hoi-an,phu-quoc
   - Lấy thời tiết nhiều điểm đến cùng lúc (dùng cho trang tổng quan)

3. Thêm router này vào backend/src/api/server.py

4. Viết hàm refresh_weather_if_stale(slug, db_conn) để dùng chung cho cả API endpoint và background job

Dùng httpx async cho các API call bên trong FastAPI endpoints.
```

---

### Task 2.3 — Cấu hình Amadeus sandbox và chạy collector vé máy bay

**Mô tả:** Sau khi đăng ký Amadeus sandbox (miễn phí), chạy collector để lấy giá vé thật vào DB.

**Prompt:**

```
File backend/src/api/travel_api/collectors/amadeus.py đã có sẵn logic gọi Amadeus API. Hãy:

1. Fix import path thành absolute imports
2. Thêm retry logic: nếu HTTP 429 (rate limit) thì sleep 1 giây rồi retry tối đa 3 lần
3. Tạo script backend/scripts/run_amadeus_collector.py:
   - Đọc AMADEUS_API_KEY và AMADEUS_API_SECRET từ biến môi trường
   - Nếu thiếu key: in hướng dẫn đăng ký tại https://developers.amadeus.com và exit(0) (không báo lỗi)
   - Chạy collector cho 10 tuyến bay đã định nghĩa trong ROUTES
   - Lưu raw JSON vào evidence/ kèm timestamp
   - In tổng kết: bao nhiêu chuyến bay đã lưu, tuyến nào thành công/thất bại

4. Thêm AMADEUS_API_KEY= và AMADEUS_API_SECRET= (trống) vào .env.example kèm comment hướng dẫn
```

---

## PHASE 3 — FastAPI CRUD Endpoints

---

### Task 3.1 — Destinations API (thay mock data)

**Mô tả:** Tạo router `/destinations` query từ PostgreSQL thay vì mock dict. Đây là endpoint quan trọng nhất vì mọi tính năng khác phụ thuộc vào.

**Prompt:**

```
Tạo FastAPI router tại backend/src/api/routes/destinations.py để thay thế mock data trong backend/src/database.py.

Endpoints cần có:
1. GET /destinations
   - Params: country (filter), tags (filter, comma-separated), page, limit (mặc định 20)
   - Trả về: list destinations với avg_rating, review_count, best_months, tags
   - Có full-text search qua param q= (dùng PostgreSQL GIN index đã có)

2. GET /destinations/{slug}
   - Trả về destination chi tiết + danh sách hotels (top 5 theo rating) + điểm tham quan (top 10)
   - Include weather hiện tại từ weather_cache (nullable nếu chưa có)

3. GET /destinations/search/suggest?q=da
   - Autocomplete: trả về tối đa 5 kết quả matching tên/slug/city
   - Dùng cho search box trên navbar

Dùng SQLAlchemy async session (get_db dependency).
Response dùng Pydantic v2 schemas, tạo file backend/src/api/schemas/destination.py riêng.
Thêm router vào server.py với prefix /destinations.
```

---

### Task 3.2 — Flights API với giá realtime

**Mô tả:** Endpoint tìm kiếm chuyến bay kết hợp DB nội bộ + Amadeus realtime fallback.

**Prompt:**

```
Tạo FastAPI router tại backend/src/api/routes/flights.py:

1. GET /flights/search
   - Params bắt buộc: origin (IATA hoặc tên thành phố), destination, travel_date (YYYY-MM-DD)
   - Params tùy chọn: cabin_class (economy/business), adults (default 1)
   - Logic:
     a. Chuẩn hoá origin/destination qua hàm normalize_city() từ database.py
     b. Query DB flights WHERE origin=? AND destination=? ORDER BY price ASC
     c. Nếu DB có kết quả: trả về kèm flag "source": "db"
     d. Nếu DB không có: gọi Amadeus sandbox API (nếu có key), trả về kèm flag "source": "amadeus_live"
     e. Nếu cả 2 đều không có: trả về 404 với message gợi ý tuyến gần nhất
   
2. GET /flights/price-calendar?origin=HAN&destination=DAD&month=2026-07
   - Trả về mảng [{date, min_price, weather_condition, weather_temp}] cho cả tháng
   - Join với weather_cache để ghép thông tin thời tiết vào từng ngày
   - Dùng cho tính năng Giá thông minh + biểu đồ

3. GET /flights/routes
   - Trả về danh sách tất cả tuyến bay có trong DB (dùng cho dropdown search)

Tạo Pydantic schemas tại backend/src/api/schemas/flight.py.
```

---

### Task 3.3 — Hotels API

**Mô tả:** Endpoint tìm kiếm khách sạn từ DB thay mock dict, với filter nâng cao.

**Prompt:**

```
Tạo FastAPI router tại backend/src/api/routes/hotels.py:

1. GET /hotels/search
   - Params: city (hoặc destination_slug), checkin, checkout, adults, max_price, min_stars, amenities (comma-separated)
   - Query PostgreSQL bảng hotels JOIN destinations
   - Tính số đêm từ checkin/checkout → tính total_price
   - Sort options: price_asc, price_desc, rating_desc, stars_desc
   - Trả về danh sách có pagination

2. GET /hotels/{hotel_id}
   - Chi tiết 1 khách sạn: thông tin đầy đủ + reviews (top 10) + location map data (lat/lng)

3. GET /hotels/compare?ids=uuid1,uuid2,uuid3
   - So sánh tối đa 3 khách sạn side-by-side
   - Trả về object {hotels: [...], comparison: {price_winner, rating_winner, amenities_matrix}}

Tạo Pydantic schemas tại backend/src/api/schemas/hotel.py.
Thêm index trên hotels(destination_id, price_per_night, stars) nếu chưa có.
```

---

## PHASE 4 — Nền tảng trung tâm (Frontend)

---

### Task 4.1 — Trang tìm kiếm chính

**Mô tả:** Trang `/search` là điểm vào chính của người dùng, thay thế chat box. Có search bar, filter sidebar, kết quả dạng card.

**Prompt:**

```
Tạo React component tại frontend/src/pages/SearchPage.jsx cho trang tìm kiếm chính của TravelBuddy.

Giao diện gồm:
1. Search bar nổi bật ở trên: input điểm đến với autocomplete gọi GET /destinations/search/suggest
2. Filter sidebar bên trái (collapsible trên mobile):
   - Loại hình: biển / núi / thành phố / văn hoá (checkbox)
   - Ngân sách: slider range (triệu VND)
   - Thời gian đi: month picker
   - Quốc gia: Vietnam / Thailand / Japan / Singapore
3. Kết quả dạng card grid (2 cột desktop, 1 cột mobile):
   Mỗi card: ảnh, tên, rating sao, tags, giá vé rẻ nhất từ Hà Nội, nút "Xem chi tiết"
4. Sort bar: Phổ biến / Giá thấp / Rating cao
5. Pagination hoặc infinite scroll

Dùng React hooks (useState, useEffect, useCallback).
Gọi API GET /destinations với các params tương ứng filter.
Dùng Tailwind classes (dự án đã có).
Không dùng thư viện UI nào ngoài những gì đã có trong package.json.
Style nhất quán với TravelBuddyApp.jsx hiện tại (dark/light theme toggle).
```

---

### Task 4.2 — Trang chi tiết điểm đến

**Mô tả:** Trang `/destination/:slug` hiển thị đầy đủ thông tin, thời tiết, danh sách khách sạn, gợi ý tham quan.

**Prompt:**

```
Tạo React component tại frontend/src/pages/DestinationPage.jsx:

Layout:
1. Hero section: ảnh đẹp full-width + tên điểm đến + breadcrumb
2. Tab bar: Tổng quan | Khách sạn | Vé máy bay | Thời tiết | Đánh giá

Tab Tổng quan:
- Mô tả điểm đến
- Widget thời tiết 7 ngày (gọi GET /weather/{slug}): hiện icon thời tiết + nhiệt độ từng ngày
- Tháng đẹp nhất để đi (từ best_months DB)
- Tags / loại hình du lịch

Tab Khách sạn:
- List top 5 khách sạn từ GET /hotels/search?destination_slug=...
- Mỗi item: tên, sao, giá/đêm, rating, amenities icons, nút "Đặt ngay" (deep-link)

Tab Vé máy bay:
- Form chọn ngày đi + số người
- Gọi GET /flights/search khi submit
- Hiện danh sách chuyến bay: hãng, giờ, giá, nút "Đặt vé"

Tab Thời tiết:
- Bảng 7 ngày chi tiết: ngày, icon, nhiệt độ max/min, lượng mưa, gió

Tab Đánh giá:
- List reviews từ DB (GET /destinations/{slug} đã bao gồm)
- Form viết review (nếu đã đăng nhập)

Dùng React Router (thêm vào App nếu chưa có).
Data fetching dùng useEffect + async/await, hiện skeleton loading.
```

---

## PHASE 5 — Giá thông minh + Thời tiết

---

### Task 5.1 — Component biểu đồ Giá + Thời tiết kết hợp

**Mô tả:** Chart line hiển thị giá vé theo ngày, mỗi cột ngày gắn icon thời tiết. Là tính năng đặc trưng nhất của hệ thống.

**Prompt:**

```
Tạo React component tại frontend/src/components/PriceWeatherChart.jsx:

Dữ liệu đầu vào (props):
- origin: string (VD: "HAN")
- destination: string (VD: "DAD")
- month: string "YYYY-MM"

Gọi API: GET /flights/price-calendar?origin=HAN&destination=DAD&month=2026-07
Response: [{date, min_price, weather_condition, weather_temp_max, rain_mm}]

Giao diện:
1. Line chart dùng thư viện recharts (đã có trong package.json):
   - Trục X: ngày trong tháng
   - Trục Y: giá vé (VND, format triệu)
   - Tooltip khi hover: giá + thời tiết chi tiết

2. Dưới trục X: hàng icon thời tiết nhỏ tương ứng từng ngày
   - ☀️ weathercode 0-2, ⛅ 3, 🌧️ 61-65, ⛈️ 95-99

3. Badge highlight tự động: ngày có giá thấp nhất + thời tiết đẹp nhất (không mưa, ít gió)
   → viền xanh + label "Gợi ý tốt nhất"

4. Summary bar phía dưới: "Giá rẻ nhất tháng: X VND ngày DD/MM | Thời tiết đẹp nhất: DD/MM"

5. Month navigator: nút < > để chuyển tháng (load lại data)

Hỗ trợ dark/light theme (dùng CSS variables giống TravelBuddyApp.jsx).
```

---

### Task 5.2 — Hệ thống cảnh báo giá (Price Alert)

**Mô tả:** Người dùng đặt ngưỡng giá → hệ thống kiểm tra định kỳ → gửi thông báo khi giá xuống dưới ngưỡng.

**Prompt:**

```
Implement tính năng Price Alert cho TravelBuddy:

Backend:
1. Router backend/src/api/routes/price_alerts.py:
   POST /price-alerts — tạo alert mới (route, target_price, notify_via: email/inapp)
   GET /price-alerts — lấy danh sách alert của user hiện tại
   DELETE /price-alerts/{id} — xóa alert
   
2. Background job backend/src/jobs/check_price_alerts.py:
   - Chạy mỗi 6 giờ (dùng APScheduler hoặc simple loop trong worker)
   - Query tất cả active price_alerts
   - Với mỗi alert: gọi GET /flights/search để lấy giá hiện tại
   - Nếu giá hiện tại <= target_price: 
     + Cập nhật triggered_at trong DB
     + Tạo thông báo in-app (lưu vào bảng notifications mới)
     + Set is_active = false

Frontend:
3. Component frontend/src/components/PriceAlertButton.jsx:
   - Button "🔔 Theo dõi giá" trên trang kết quả chuyến bay
   - Click mở modal: nhập giá mục tiêu + email
   - Gọi POST /price-alerts
   - Sau khi tạo: hiện badge "Đang theo dõi giá X VND"
```

---

## PHASE 6 — Trip Builder

---

### Task 6.1 — Trip Builder UI kéo-thả

**Mô tả:** Trang lên lịch trình chính với timeline kéo-thả theo ngày. Tính năng cốt lõi của Trip Builder.

**Prompt:**

```
Tạo React component tại frontend/src/pages/TripBuilderPage.jsx:

Layout 2 cột:
- Cột trái (1/3): Panel tìm kiếm + kéo items
  + Search bar tìm điểm đến / khách sạn
  + Kết quả hiện dạng card nhỏ, có handle kéo
  + Tab: Điểm đến | Khách sạn | Vé bay | Hoạt động

- Cột phải (2/3): Timeline lịch trình
  + Header: Tên chuyến đi (editable inline) + Ngày bắt đầu/kết thúc
  + Mỗi ngày là 1 lane: "Ngày 1 - Thứ 2, 14/07"
  + Trong mỗi lane: list các item đã kéo vào, có thể kéo đổi thứ tự
  + Cuối mỗi lane: nút "+ Thêm hoạt động"
  + Footer: Tổng chi phí ước tính

Drag & Drop:
- Dùng @dnd-kit/core (thêm vào package.json)
- Kéo từ panel trái thả vào bất kỳ ngày nào
- Kéo đổi thứ tự item trong cùng 1 ngày
- Kéo item sang ngày khác

API calls:
- GET /destinations?q=... cho search
- POST /trips — tạo trip mới
- POST /trips/{id}/days/{day_id}/items — thêm item
- PUT /trips/{id}/days/{day_id}/items/{item_id} — cập nhật (sort_order)
- DELETE /trips/{id}/days/{day_id}/items/{item_id}

Thêm router /trip-builder vào App.jsx.
```

---

## PHASE 7 — Tái định vị AI

---

### Task 7.1 — AI chuyển thành widget hỗ trợ

**Mô tả:** Thay vì là trang chính, AI chat thu nhỏ thành floating button ở góc màn hình. Chỉ hiển thị khi người dùng click.

**Prompt:**

```
Refactor TravelBuddyApp.jsx thành floating AI assistant widget:

1. Tạo component frontend/src/components/AIAssistantWidget.jsx:
   - Floating button 🤖 ở góc phải dưới màn hình (position: fixed)
   - Click → expand thành chat panel (400x600px, slide up animation)
   - Click nút X → collapse lại
   - Badge số tin nhắn chưa đọc khi thu nhỏ

2. Context-aware: widget nhận prop currentContext
   - Khi ở trang DestinationPage: pre-fill "Hỏi về [tên điểm đến]..."
   - Khi ở trang SearchPage: pre-fill "Không tìm thấy điểm đến phù hợp? Hỏi AI..."
   - Khi ở TripBuilderPage: pre-fill "Tối ưu lộ trình của tôi..."

3. Quick action buttons (phía trên input box):
   - "🗺️ Gợi ý lịch trình" 
   - "💰 Tính ngân sách"
   - "🌤️ Thời tiết ổn không?"
   - Click vào → tự động fill câu hỏi tương ứng + gửi

4. AI response renderer: giữ nguyên markdown renderer từ TravelBuddyApp.jsx

5. Thêm AIAssistantWidget vào App.jsx (layout level, hiển thị mọi trang)

Giữ nguyên toàn bộ logic chat/SSE từ TravelBuddyApp.jsx, chỉ thay đổi UI container.
```

---

### Task 7.2 — Cập nhật AI tools dùng API thật thay mock data

**Mô tả:** Các tools `search_flights`, `search_hotels` trong `travel.py` hiện dùng dict mock. Cập nhật để gọi các API endpoint đã tạo ở Phase 3.

**Prompt:**

```
Cập nhật file backend/src/tools/travel.py để thay mock data bằng gọi API thật:

1. Tạo helper backend/src/tools/api_client.py:
   - BASE_URL = os.getenv("INTERNAL_API_URL", "http://api:8000")  
   - async get_destinations(q, country, tags, limit) → gọi GET /destinations
   - async search_flights_api(origin, dest, date) → gọi GET /flights/search
   - async search_hotels_api(city, max_price, min_stars) → gọi GET /hotels/search
   - async get_weather(slug) → gọi GET /weather/{slug}
   - Dùng httpx.AsyncClient với timeout=10s, retry 2 lần

2. Cập nhật tool search_flights trong travel.py:
   - Thay lookup_flights() bằng gọi api_client.search_flights_api()
   - Fallback về mock data nếu API không trả về kết quả

3. Cập nhật tool search_hotels:
   - Thay lookup_hotels() bằng api_client.search_hotels_api()

4. Thêm tool mới get_destination_weather(destination_slug):
   - Gọi api_client.get_weather()
   - Trả về thời tiết 7 ngày dạng text để AI dùng trong câu trả lời

5. Cập nhật ALL_TOOLS trong travel.py để include tool mới

Đảm bảo không break các test hiện có. Nếu INTERNAL_API_URL không set, log warning và fallback về mock data.
```

---

## PHASE 8 — Cộng đồng & UGC

---

### Task 8.1 — Reviews system

**Mô tả:** Cho phép người dùng viết review điểm đến và khách sạn, hiển thị trên trang chi tiết.

**Prompt:**

```
Implement reviews system cho TravelBuddy:

Backend - backend/src/api/routes/reviews.py:
1. GET /reviews?destination_slug=da-nang&page=1&limit=10
   - Trả về reviews kèm thông tin user (full_name, avatar, level)
   - Sort theo created_at DESC
   - Include aggregate: avg_rating, total_reviews, rating_distribution {5:10, 4:5, ...}

2. POST /reviews
   - Body: {destination_id | hotel_id, rating, content, images: [base64]}
   - Validation: content min 50 chars, rating 1-5
   - Sau khi insert: UPDATE destinations SET avg_rating = ..., review_count = ...
   - Return review vừa tạo

3. POST /reviews/{id}/helpful
   - Tăng helpful_count += 1

Frontend - component frontend/src/components/ReviewSection.jsx:
- Hiển thị aggregate rating (sao tổng + bar chart phân bố)
- List reviews: avatar, tên, level badge, ngày, rating sao, content, ảnh gallery
- Form viết review: star rating click, textarea, upload ảnh (tối đa 5)
- Nút "Hữu ích 👍" với số đếm

Thêm basic auth middleware (đơn giản: X-User-ID header) để protect POST endpoints.
```

---

## Checklist tổng thể

```
Phase 1 — Database
[ ] Task 1.1 — PostgreSQL trong docker-compose
[ ] Task 1.2 — SQLAlchemy models
[ ] Task 1.3 — Migration + verify script

Phase 2 — Data Pipeline  
[ ] Task 2.1 — 3 collectors miễn phí
[ ] Task 2.2 — Weather API endpoint
[ ] Task 2.3 — Amadeus collector

Phase 3 — API Endpoints
[ ] Task 3.1 — Destinations API
[ ] Task 3.2 — Flights API + price calendar
[ ] Task 3.3 — Hotels API

Phase 4 — Frontend cốt lõi
[ ] Task 4.1 — Search page
[ ] Task 4.2 — Destination detail page

Phase 5 — Giá thông minh
[ ] Task 5.1 — Price + Weather chart
[ ] Task 5.2 — Price alerts

Phase 6 — Trip Builder
[ ] Task 6.1 — Drag & drop UI

Phase 7 — AI tái định vị
[ ] Task 7.1 — Floating widget
[ ] Task 7.2 — Tools dùng API thật

Phase 8 — Cộng đồng
[ ] Task 8.1 — Reviews system
```
