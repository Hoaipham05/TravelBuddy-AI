# TravelBuddy AI — Kiến trúc Hệ thống

> **Triết lý thiết kế:** Nền tảng là trung tâm — người dùng tự tìm kiếm, lọc, so sánh, đặt chỗ.
> AI chỉ là lớp hỗ trợ phía dưới, gợi ý khi người dùng bế tắc hoặc cần tóm tắt nhanh.

---

## Sơ đồ tổng quan

```
┌─────────────────────────────────────────────────────┐
│              Người dùng (Web)                       │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│     Nền tảng trung tâm — Tìm kiếm · Lọc · So sánh · Đặt chỗ    │
│    (Thay thế hỏi-đáp; người dùng tự thao tác, AI chỉ hỗ trợ)   │
└─────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
   ┌──────────┐    ┌──────────────┐    ┌────────────────┐
   │Trip Builder│  │ Giá thông minh│    │ Cộng đồng & UGC│
   └──────────┘    └──────────────┘    └────────────────┘
          │                │
          ▼                ▼
   ┌──────────────┐   ┌──────────────────┐
   │Hồ sơ thông minh│  │Quản lý chuyến đi │
   └──────────────┘   └──────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│          AI Du lịch — Trợ lý hỗ trợ (không phải trung tâm)     │
└─────────────────────────────────────────────────────┘
```

---

## 1. Nền tảng trung tâm

**Mục tiêu:** Thay thế hoàn toàn mô hình hỏi-đáp. Người dùng thao tác trực tiếp trên giao diện hệ thống thay vì chat với AI.

| Chức năng | Mô tả |
|-----------|-------|
| Tìm kiếm | Fulltext search điểm đến, khách sạn, chuyến bay theo nhiều tiêu chí |
| Lọc | Lọc theo giá, số sao, tiện ích, khoảng cách, đánh giá |
| So sánh | So sánh song song tối đa 3–4 lựa chọn (khách sạn / vé máy bay) |
| Đặt chỗ | Deep-link sang Booking.com, Agoda, VietJet, Vietnam Airlines |

**Nguồn dữ liệu:**
- DB nội bộ PostgreSQL (destinations, hotels, flights)
- Amadeus API (giá vé realtime)
- OpenTripMap API (điểm tham quan, POI)

---

## 2. Trip Builder

**Mục tiêu:** Công cụ lên lịch trình kéo-thả, không cần chat với AI.

| Chức năng | Mô tả |
|-----------|-------|
| Lên lịch trình kéo-thả | Kéo điểm đến / khách sạn / hoạt động vào timeline theo ngày |
| Chia sẻ & cộng tác | Mời bạn bè cùng chỉnh sửa lịch trình (role: owner / editor / viewer) |
| Tối ưu lộ trình AI | AI gợi ý sắp xếp thứ tự tham quan tối ưu theo địa lý & thời gian |
| Xuất PDF / iCal | Export lịch trình ra PDF in được hoặc file .ics thêm vào Google Calendar |

**Bảng DB liên quan:** `trips`, `trip_days`, `itinerary_items`, `trip_members`

---

## 3. Giá thông minh

**Mục tiêu:** Giúp người dùng chọn đúng thời điểm đặt vé / phòng với giá tốt nhất. Tích hợp thêm thông tin thời tiết để hỗ trợ quyết định.

| Chức năng | Mô tả | Nguồn dữ liệu |
|-----------|-------|---------------|
| Biểu đồ giá theo ngày | Line chart giá vé / phòng 30–90 ngày tới | `monthly_prices` (DB) + Amadeus API |
| Cảnh báo giá rẻ | Đặt ngưỡng giá → nhận thông báo khi giá xuống | Bảng `price_alerts` (DB) |
| Dự đoán xu hướng | Nhận xét "giá đang tăng / giảm / ổn định" dựa trên lịch sử | `exchange_rate_history` + Amadeus |
| So sánh nhiều tuyến | So sánh giá vé 2–3 tuyến bay cùng lúc | DB flights + Amadeus |
| **Thời tiết tích hợp** | Hiển thị dự báo 7 ngày tới cạnh biểu đồ giá — giúp chọn ngày đi phù hợp | **Open-Meteo API** (miễn phí, không cần key) |

### Chi tiết tích hợp thời tiết trong Giá thông minh

```
Biểu đồ Giá + Thời tiết (theo ngày)
─────────────────────────────────────────────
Ngày     Giá vé (VND)    Thời tiết    Nhiệt độ
17/06    980.000          ☀️ Nắng      29°C
18/06    1.250.000        🌧️ Mưa       26°C
19/06    890.000          ⛅ Mây        28°C
20/06    760.000          ☀️ Nắng      31°C  ← Gợi ý tốt nhất
─────────────────────────────────────────────
AI gợi ý: "Ngày 20/06 vừa rẻ vừa nắng đẹp"
```

**API thời tiết sử dụng:**
- **Open-Meteo** (`https://api.open-meteo.com/v1/forecast`) — miễn phí, không cần API key, đã có collector tại `collectors/weather.py`
- Params: `daily=weathercode,temperature_2m_max,precipitation_sum`, `forecast_days=16`
- Cache vào bảng `weather_cache` (PostgreSQL), TTL refresh 6 giờ/lần

---

## 4. Cộng đồng & UGC

**Mục tiêu:** Nội dung do người dùng tạo ra, tăng độ tin cậy và engagement.

| Chức năng | Mô tả |
|-----------|-------|
| Review & ảnh từ người thật | Đánh giá sao + ảnh thực tế cho điểm đến và khách sạn |
| Chia sẻ lịch trình mẫu | Public trip templates — clone về dùng với 1 click |
| Forum theo điểm đến | Thread thảo luận gắn với từng destination slug |
| Gợi ý từ bạn bè | Xem bạn bè đã đi đâu, đang lên kế hoạch đi đâu |

**Bảng DB liên quan:** `reviews`, `trips` (is_public=true), `users`

---

## 5. Hồ sơ thông minh

**Mục tiêu:** Cá nhân hoá trải nghiệm dựa trên hành vi và sở thích của từng người dùng.

| Chức năng | Mô tả |
|-----------|-------|
| Lưu phong cách đi | Ngân sách ưa thích, số sao khách sạn, loại hình ăn uống, phương tiện |
| Lịch sử chuyến đi & wishlist | Các chuyến đã đi + danh sách điểm muốn đến |
| Gợi ý cá nhân hoá theo hành vi | Recommend dựa trên lịch sử tìm kiếm + booking |
| Tích điểm / huy hiệu du lịch | Gamification: đạt mốc số điểm đến, loại hình du lịch |

**Bảng DB liên quan:** `users` (travel_preferences JSONB), `trips`, `reviews`

---

## 6. Quản lý chuyến đi

**Mục tiêu:** Ví tài liệu du lịch kỹ thuật số, thay thế folder giấy tờ.

| Chức năng | Mô tả |
|-----------|-------|
| Ví tài liệu | Upload & lưu trữ: passport scan, visa, e-ticket, hotel voucher |
| Thông báo thay đổi real-time | Alert khi có thay đổi lịch bay, giá phòng, thời tiết xấu |
| Chia sẻ chi phí nhóm | Split bill cho chuyến đi tập thể, tính toán ai nợ ai |
| Nhật ký hành trình sau chuyến | Viết nhật ký + gắn ảnh sau khi trở về |

**Bảng DB liên quan:** `trips`, `trip_members`, `trip_expenses`, `itinerary_items`

---

## 7. AI Du lịch — Trợ lý hỗ trợ

**Vị trí trong hệ thống:** Lớp cuối cùng, chỉ kích hoạt khi người dùng cần.

> AI **không** là điểm vào chính. AI chỉ hỗ trợ khi người dùng bế tắc hoặc muốn xử lý ngôn ngữ tự nhiên.

| Chức năng | Trigger | Mô tả |
|-----------|---------|-------|
| Gợi ý khi bế tắc | Người dùng không tìm thấy kết quả phù hợp | AI hỏi lại + gợi ý điểm đến thay thế |
| Tóm tắt & so sánh nhanh | Người dùng click "Hỏi AI về lựa chọn này" | Tóm tắt ưu/nhược của 2–3 lựa chọn đang xem |
| Trả lời câu hỏi điểm đến | Widget chat trong trang chi tiết điểm đến | Hỏi về thời tiết, văn hoá, ăn uống, visa |
| Tìm vé / khách sạn theo yêu cầu | Người dùng chat yêu cầu phức tạp | Agent gọi tool tìm DB + web, trả kết quả có cấu trúc |

**Stack:** LangGraph agent + LiteLLM + Redis Streams (giữ nguyên từ kiến trúc cũ)

---

## Kiến trúc kỹ thuật tổng thể

```
Browser / Mobile App
        │
        ▼
   Nginx :8890
   ├── /          → React SPA (Vite build)
   ├── /api/      → FastAPI
   └── /ws/       → WebSocket

FastAPI
   ├── /destinations/**   → CRUD + Search (PostgreSQL)
   ├── /flights/**        → Query DB + Amadeus realtime
   ├── /hotels/**         → Query DB + Agoda fallback
   ├── /weather/**        → weather_cache (Open-Meteo refresh 6h)
   ├── /trips/**          → Trip Builder CRUD
   ├── /community/**      → Reviews, UGC
   ├── /profile/**        → User profile, wishlist
   ├── /chat              → AI agent (async via Redis Stream)
   └── /session/*/stream  → SSE reasoning trace

PostgreSQL (11 bảng)
   users · destinations · hotels · flights
   trips · trip_days · itinerary_items · trip_members
   reviews · price_alerts · trip_expenses
   + weather_cache · exchange_rates · countries

Redis
   ├── Session history (TTL 1h)
   ├── Job queue (Streams)
   ├── Result store (TTL 5m)
   └── Search cache (TTL 5m)

External APIs
   ├── Amadeus        → Giá vé realtime
   ├── Open-Meteo     → Thời tiết (miễn phí)
   ├── OpenTripMap    → POI, điểm tham quan
   ├── Frankfurter    → Tỷ giá (miễn phí)
   ├── RestCountries  → Thông tin quốc gia (miễn phí)
   └── Serper/DDG     → Web search fallback cho AI
```

---

## Data Flow: Giá thông minh + Thời tiết

```
User chọn tuyến HAN → DAD, tháng 7/2026
        │
        ├─► Query DB flights (monthly_prices JSON)
        │         │
        │         ▼
        │   Amadeus API (realtime prices cho 30 ngày tới)
        │
        ├─► Query weather_cache WHERE destination_slug = 'da-nang'
        │         │
        │         ├── Cache còn hạn (< 6h) → dùng luôn
        │         └── Cache hết hạn → gọi Open-Meteo API → cập nhật cache
        │
        ▼
   Frontend render:
   - Line chart: Trục X = ngày, Trục Y = giá vé
   - Icon thời tiết gắn trên mỗi cột ngày
   - Badge "Gợi ý tốt nhất" = ngày giá thấp + thời tiết đẹp
```

---

## Phân tầng phát triển

| Phase | Nội dung | Ưu tiên |
|-------|----------|---------|
| **Phase 1** | PostgreSQL + Schema + Seed data | 🔴 Ngay |
| **Phase 2** | Data pipeline (collectors chạy được) | 🔴 Ngay |
| **Phase 3** | FastAPI CRUD endpoints thay mock data | 🟠 Cao |
| **Phase 4** | Nền tảng trung tâm (Search/Filter UI) | 🟠 Cao |
| **Phase 5** | Giá thông minh + Thời tiết tích hợp | 🟡 Trung bình |
| **Phase 6** | Trip Builder UI | 🟡 Trung bình |
| **Phase 7** | Cộng đồng & UGC | 🟢 Sau |
| **Phase 8** | Hồ sơ thông minh + Gamification | 🟢 Sau |
| **Phase 9** | AI tái định vị (hỗ trợ, không trung tâm) | 🟢 Sau |
