# QUY TRÌNH PHÁT TRIỂN DỰ ÁN TRAVELBUDDY AI
## Báo cáo Phương pháp luận & Các bước triển khai

> **Môn học:** Đồ án / Dự án Phần mềm
> **Nhóm thực hiện:** TravelBuddy Team
> **Phiên bản tài liệu:** 1.0

---

## MỤC LỤC

1. [Khởi động dự án (Project Initiation)](#1-khởi-động-dự-án)
2. [Phân tích yêu cầu (Requirements Analysis)](#2-phân-tích-yêu-cầu)
3. [Thiết kế hệ thống (System Design)](#3-thiết-kế-hệ-thống)
4. [Thiết kế cơ sở dữ liệu (Database Design)](#4-thiết-kế-cơ-sở-dữ-liệu)
5. [Thiết kế giao diện người dùng (UI/UX Design)](#5-thiết-kế-giao-diện-người-dùng)
6. [Xây dựng môi trường phát triển (Dev Environment Setup)](#6-xây-dựng-môi-trường-phát-triển)
7. [Phát triển Backend (Backend Development)](#7-phát-triển-backend)
8. [Phát triển Frontend (Frontend Development)](#8-phát-triển-frontend)
9. [Tích hợp API bên thứ ba (Third-party API Integration)](#9-tích-hợp-api-bên-thứ-ba)
10. [Tích hợp trí tuệ nhân tạo (AI Integration)](#10-tích-hợp-trí-tuệ-nhân-tạo)
11. [Kiểm thử (Testing)](#11-kiểm-thử)
12. [Triển khai (Deployment)](#12-triển-khai)
13. [Đánh giá & Cải tiến (Evaluation & Improvement)](#13-đánh-giá--cải-tiến)
14. [Tài liệu hóa (Documentation)](#14-tài-liệu-hóa)

---

## 1. KHỞI ĐỘNG DỰ ÁN

> **Mục tiêu:** Xác định rõ bài toán, phạm vi, tính khả thi và lập kế hoạch tổng thể trước khi viết bất kỳ dòng code nào.

### 1.1 Xác định bài toán (Problem Statement)

Đây là bước đầu tiên và quan trọng nhất — xác định **đúng vấn đề** cần giải quyết.

**Câu hỏi cần trả lời:**
- Người dùng đang gặp khó khăn gì trong việc lên kế hoạch du lịch?
- Các giải pháp hiện tại (Booking.com, Agoda, TripAdvisor) còn thiếu sót gì?
- TravelBuddy AI sẽ giải quyết vấn đề đó như thế nào?

**Bài toán của TravelBuddy:**

| Vấn đề hiện tại | Giải pháp TravelBuddy |
|-----------------|----------------------|
| Phải mở nhiều tab để so sánh giá vé, khách sạn | Nền tảng tập trung: tìm kiếm, so sánh, đặt chỗ tại 1 nơi |
| Không biết thời điểm nào nên đi để vừa rẻ vừa đẹp thời tiết | Biểu đồ Giá thông minh tích hợp dự báo thời tiết |
| Lên lịch trình thủ công tốn thời gian | Trip Builder kéo-thả tự động tối ưu lộ trình |
| Thông tin du lịch phân tán, khó tổng hợp | AI hỗ trợ tổng hợp thông tin khi cần |

### 1.2 Nghiên cứu thị trường & Đối thủ cạnh tranh

**Phân tích đối thủ (Competitive Analysis):**

| Tiêu chí | Booking.com | TripAdvisor | Google Travel | **TravelBuddy** |
|----------|------------|-------------|---------------|-----------------|
| Tìm kiếm khách sạn | ✅ | ✅ | ✅ | ✅ |
| Tìm kiếm vé máy bay | ❌ | ❌ | ✅ | ✅ |
| Trip Builder kéo-thả | ❌ | ❌ | ❌ | ✅ |
| Giá + thời tiết tích hợp | ❌ | ❌ | ❌ | ✅ |
| AI hỗ trợ | ❌ | ❌ | Hạn chế | ✅ |
| Cộng đồng UGC | ❌ | ✅ | ❌ | ✅ |
| Tối ưu cho người Việt | ❌ | ❌ | ❌ | ✅ |

**Phân tích người dùng mục tiêu (Target Users):**
- Người trẻ 18–35 tuổi, thích du lịch tự túc
- Gia đình lên kế hoạch đi chơi dịp lễ, hè
- Nhóm bạn đi du lịch cần chia sẻ và cộng tác lịch trình

### 1.3 Xác định phạm vi dự án (Project Scope)

**Trong phạm vi (In Scope):**
- Nền tảng tìm kiếm, lọc, so sánh: điểm đến, khách sạn, chuyến bay
- Biểu đồ giá thông minh tích hợp thời tiết
- Trip Builder lên lịch trình kéo-thả
- Hồ sơ người dùng và lịch sử chuyến đi
- AI hỗ trợ (không phải trung tâm)
- Cộng đồng: review, chia sẻ lịch trình

**Ngoài phạm vi (Out of Scope):**
- Hệ thống đặt vé / thanh toán trực tiếp (chỉ deep-link)
- App mobile native (iOS/Android) — chỉ responsive web
- Quản lý đối tác cung cấp dịch vụ (B2B)

### 1.4 Phân tích tính khả thi (Feasibility Study)

**Tính khả thi kỹ thuật:**
- Frontend: React/Vite — công nghệ phổ biến, nhóm có kinh nghiệm
- Backend: FastAPI (Python) — hiệu năng cao, dễ tích hợp AI
- Database: PostgreSQL — đủ mạnh cho dữ liệu du lịch, hỗ trợ fulltext search tiếng Việt
- AI: LangGraph + LiteLLM — modular, dễ thay đổi LLM provider
- Hạ tầng: Docker Compose → có thể triển khai trên VPS bất kỳ

**Tính khả thi kinh tế:**
- Chi phí phát triển: chủ yếu là thời gian nhóm (đồ án)
- Chi phí vận hành: VPS ~200k-500k VND/tháng
- API bên ngoài: Open-Meteo, RestCountries, Frankfurter — **hoàn toàn miễn phí**
- Amadeus sandbox — miễn phí 100 req/ngày
- Groq API — free tier đủ dùng cho demo

**Tính khả thi vận hành:**
- Giao diện trực quan, không yêu cầu đào tạo người dùng
- AI tự động xử lý ngôn ngữ tự nhiên tiếng Việt

### 1.5 Lập kế hoạch dự án (Project Planning)

**Phương pháp phát triển:** Agile Scrum với sprint 1–2 tuần

**Timeline tổng thể:**

```
Tuần 1–2  : Phân tích yêu cầu + Thiết kế hệ thống
Tuần 3–4  : Thiết kế DB + UI Wireframe
Tuần 5–6  : Setup môi trường + Khung Backend + API CRUD cơ bản
Tuần 7–8  : Frontend cốt lõi (Search, Destination detail)
Tuần 9–10 : Tích hợp API bên ngoài + Giá thông minh + Thời tiết
Tuần 11–12: Trip Builder + AI Widget
Tuần 13   : Kiểm thử tổng thể
Tuần 14   : Deploy + Viết báo cáo hoàn chỉnh
```

**Phân công nhóm (ví dụ nhóm 4 người):**

| Thành viên | Vai trò chính | Trách nhiệm |
|------------|--------------|-------------|
| Thành viên 1 | Team Lead / Backend | Kiến trúc hệ thống, FastAPI, DB |
| Thành viên 2 | Frontend Developer | React, UI components, responsive |
| Thành viên 3 | AI / Data Engineer | LangGraph agent, data collectors, API tích hợp |
| Thành viên 4 | Full-stack / DevOps | Docker, deploy, testing, tài liệu |

**Công cụ quản lý dự án:**
- **Trello / Jira:** Quản lý task theo sprint
- **GitHub:** Quản lý source code, pull request, code review
- **Figma:** Thiết kế UI/UX
- **Notion / Google Docs:** Tài liệu, meeting notes

---

## 2. PHÂN TÍCH YÊU CẦU

> **Mục tiêu:** Chuyển bài toán thực tế thành đặc tả kỹ thuật cụ thể, rõ ràng, có thể đo lường được.

### 2.1 Thu thập yêu cầu (Requirements Elicitation)

**Phương pháp thu thập:**
- **Phỏng vấn người dùng:** Hỏi 10–20 người trong độ tuổi mục tiêu về thói quen lên kế hoạch du lịch
- **Khảo sát online:** Google Form với 30–50 câu trả lời
- **Quan sát thực tế (User Journey Mapping):** Theo dõi người dùng sử dụng Booking.com, ghi nhận điểm đau (pain points)
- **Nghiên cứu đối thủ:** Dùng thử TripAdvisor, Google Travel, Traveloka để liệt kê tính năng

**Kết quả khảo sát (dữ liệu mẫu):**
- 78% người dùng phải mở ≥ 3 tab khi lên kế hoạch chuyến đi
- 65% không biết thời điểm nào trong tháng giá vé rẻ nhất
- 82% muốn có công cụ lên lịch trình trực quan thay vì ghi trên giấy
- 91% tin tưởng review từ người dùng thật hơn mô tả từ khách sạn

### 2.2 Yêu cầu chức năng (Functional Requirements)

#### FR-01: Tìm kiếm & Khám phá

| Mã | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-01.1 | Tìm kiếm điểm đến theo tên, tag, quốc gia | Cao |
| FR-01.2 | Tìm kiếm không dấu tiếng Việt (Hà Nội = ha noi = hanoi) | Cao |
| FR-01.3 | Tìm kiếm chuyến bay theo origin, destination, ngày đi | Cao |
| FR-01.4 | Tìm kiếm khách sạn theo thành phố, giá, số sao | Cao |
| FR-01.5 | Gợi ý autocomplete khi gõ tên điểm đến | Trung bình |
| FR-01.6 | Lọc kết quả theo nhiều tiêu chí đồng thời | Cao |
| FR-01.7 | Sắp xếp kết quả theo giá, rating, khoảng cách | Trung bình |

#### FR-02: Giá thông minh & Thời tiết

| Mã | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-02.1 | Hiển thị biểu đồ giá vé theo từng ngày trong tháng | Cao |
| FR-02.2 | Tích hợp dự báo thời tiết 7–16 ngày vào biểu đồ giá | Cao |
| FR-02.3 | Gợi ý "ngày tốt nhất" = giá thấp + thời tiết đẹp | Cao |
| FR-02.4 | Cảnh báo giá rẻ: đặt ngưỡng → nhận thông báo | Trung bình |
| FR-02.5 | So sánh giá vé trên 2–3 tuyến bay cùng lúc | Trung bình |
| FR-02.6 | Hiển thị tỷ giá quy đổi sang VND | Thấp |

#### FR-03: Trip Builder

| Mã | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-03.1 | Tạo lịch trình mới với tên, ngày bắt đầu/kết thúc | Cao |
| FR-03.2 | Kéo-thả địa điểm / khách sạn / hoạt động vào timeline | Cao |
| FR-03.3 | Kéo đổi thứ tự hoạt động trong cùng ngày | Cao |
| FR-03.4 | Tính tổng chi phí ước tính cho cả chuyến | Trung bình |
| FR-03.5 | Mời bạn bè cùng chỉnh sửa lịch trình | Trung bình |
| FR-03.6 | Xuất lịch trình ra PDF | Thấp |
| FR-03.7 | AI gợi ý sắp xếp lộ trình tối ưu | Thấp |

#### FR-04: Tài khoản & Hồ sơ

| Mã | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-04.1 | Đăng ký / Đăng nhập bằng email & mật khẩu | Cao |
| FR-04.2 | Lưu sở thích du lịch (ngân sách, loại hình, tiện nghi) | Trung bình |
| FR-04.3 | Xem lịch sử chuyến đi đã lên kế hoạch | Trung bình |
| FR-04.4 | Wishlist điểm đến muốn đến | Thấp |
| FR-04.5 | Tích điểm và huy hiệu gamification | Thấp |

#### FR-05: Cộng đồng & UGC

| Mã | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-05.1 | Viết review điểm đến / khách sạn kèm ảnh | Cao |
| FR-05.2 | Đánh giá sao (1–5) | Cao |
| FR-05.3 | Chia sẻ lịch trình public cho cộng đồng | Trung bình |
| FR-05.4 | Clone lịch trình của người khác | Thấp |

#### FR-06: AI Hỗ trợ

| Mã | Yêu cầu | Mức độ ưu tiên |
|----|---------|----------------|
| FR-06.1 | Chat AI floating widget trên mọi trang | Cao |
| FR-06.2 | AI gợi ý điểm đến khi người dùng bế tắc | Cao |
| FR-06.3 | AI tóm tắt so sánh 2–3 lựa chọn đang xem | Trung bình |
| FR-06.4 | AI trả lời câu hỏi về thời tiết, visa, văn hoá | Trung bình |
| FR-06.5 | AI nhận diện địa điểm từ ảnh upload | Thấp |

### 2.3 Yêu cầu phi chức năng (Non-Functional Requirements)

| Loại | Yêu cầu | Chỉ số đo lường |
|------|---------|-----------------|
| **Hiệu năng** | Trang chính load dưới 3 giây | Lighthouse Performance ≥ 80 |
| **Hiệu năng** | API response < 500ms (không kể AI) | Đo bằng Postman |
| **Khả năng mở rộng** | Hỗ trợ 100 người dùng đồng thời | Load test với k6 |
| **Bảo mật** | Bảo vệ API khỏi injection attacks | OWASP Top 10 checklist |
| **Bảo mật** | Dữ liệu người dùng mã hoá (password hash bcrypt) | Code review |
| **Khả dụng** | Uptime ≥ 99% trong giờ demo | Monitor với healthcheck |
| **Khả năng bảo trì** | Code coverage ≥ 60% | pytest-cov report |
| **Khả năng dùng** | Responsive: desktop, tablet, mobile | Chrome DevTools |
| **Khả năng dùng** | Hỗ trợ tìm kiếm không dấu tiếng Việt | Test case thủ công |
| **Tuân thủ** | Rate limit AI: 20 req/phút/user | Redis counter |

### 2.4 Xây dựng Use Case Diagram

**Các tác nhân (Actors):**
- **Khách (Guest):** Chưa đăng nhập — có thể tìm kiếm, xem thông tin
- **Người dùng đã đăng nhập (User):** Đầy đủ quyền
- **Admin:** Quản lý nội dung, duyệt review

**Use Case chính:**

```
[Khách]
  ├── UC-01: Tìm kiếm điểm đến
  ├── UC-02: Xem chi tiết điểm đến
  ├── UC-03: Xem giá vé + thời tiết
  └── UC-04: Đăng ký tài khoản

[Người dùng]
  ├── (Kế thừa tất cả UC của Khách)
  ├── UC-05: Tạo và quản lý Trip Builder
  ├── UC-06: Đặt cảnh báo giá
  ├── UC-07: Viết review
  ├── UC-08: Chia sẻ lịch trình
  ├── UC-09: Sử dụng AI chat
  └── UC-10: Quản lý hồ sơ cá nhân

[Admin]
  ├── UC-11: Quản lý dữ liệu điểm đến
  ├── UC-12: Duyệt / xóa review vi phạm
  └── UC-13: Xem thống kê hệ thống
```

### 2.5 Đặc tả User Stories

**Định dạng:** *"Là [vai trò], tôi muốn [hành động] để [mục tiêu]"*

**Ví dụ các User Stories quan trọng:**

> **US-01:** Là khách du lịch, tôi muốn xem biểu đồ giá vé kết hợp với thời tiết theo từng ngày trong tháng, để tôi chọn được ngày đi vừa rẻ vừa có thời tiết đẹp.

> **US-02:** Là người lên kế hoạch nhóm, tôi muốn kéo-thả các địa điểm vào lịch trình theo ngày, để dễ dàng sắp xếp và chia sẻ với bạn bè.

> **US-03:** Là người bận rộn, tôi muốn đặt cảnh báo giá cho tuyến HAN→PQC dưới 800k, để tôi không cần theo dõi giá mỗi ngày.

> **US-04:** Là người lần đầu đi nước ngoài, tôi muốn hỏi AI về thủ tục visa và thời tiết tháng 3 ở Nhật Bản, để tôi chuẩn bị đầy đủ mà không cần tìm kiếm thủ công.

---

## 3. THIẾT KẾ HỆ THỐNG

> **Mục tiêu:** Xây dựng bản thiết kế kỹ thuật chi tiết làm nền tảng cho toàn bộ quá trình phát triển.

### 3.1 Lựa chọn kiến trúc hệ thống

**Kiến trúc được chọn: Monolithic Modular (3-tier)**

```
┌─────────────────────────────────────────────┐
│  Presentation Layer (React SPA)              │
├─────────────────────────────────────────────┤
│  Business Logic Layer (FastAPI)              │
│  ├── API Routes                              │
│  ├── Service Layer                           │
│  ├── AI Agent (LangGraph)                   │
│  └── Background Jobs                        │
├─────────────────────────────────────────────┤
│  Data Layer                                  │
│  ├── PostgreSQL (persistent data)            │
│  ├── Redis (cache, session, queue)           │
│  └── External APIs (Amadeus, Open-Meteo...) │
└─────────────────────────────────────────────┘
```

**Lý do chọn Monolithic thay vì Microservices:**
- Quy mô nhóm nhỏ (3–5 người) → monolithic dễ quản lý hơn
- Đây là đồ án / MVP → ưu tiên tốc độ phát triển
- Có thể tách service sau khi hệ thống ổn định

### 3.2 Sơ đồ kiến trúc triển khai (Deployment Architecture)

```
Internet
    │
    ▼
[Nginx :8890]
    ├── / → Serve React build (static files)
    ├── /api/ → Proxy → FastAPI :8000
    └── /ws/ → Proxy → FastAPI WebSocket

[FastAPI :8000]
    ├── Xử lý HTTP requests
    ├── Publish jobs → Redis Streams
    └── SSE streaming cho AI responses

[Redis :6379]
    ├── Stream "travelbuddy:jobs" → Worker pool
    ├── Session storage (TTL 1h)
    ├── Result store (TTL 5m)
    └── Search cache (TTL 5m)

[Worker × 4]
    ├── Consume jobs từ Redis Stream
    ├── Chạy LangGraph Agent
    └── Lưu kết quả vào Result store

[PostgreSQL :5432]
    └── Persistent data: users, destinations, hotels, flights, trips...

[SearXNG :8080]
    └── Self-hosted search engine cho AI web search
```

### 3.3 Thiết kế API (API Design)

**Nguyên tắc thiết kế RESTful API:**
- Sử dụng HTTP verbs đúng nghĩa: GET (đọc), POST (tạo), PUT (sửa toàn bộ), PATCH (sửa một phần), DELETE (xóa)
- URL dùng danh từ số nhiều: `/destinations`, `/hotels`, `/flights`
- HTTP status codes chuẩn: 200, 201, 400, 401, 403, 404, 422, 429, 500
- Versioning: `/api/v1/...`
- Pagination: `?page=1&limit=20`
- Filtering: `?country=Vietnam&tags=biển,đảo`

**Danh sách endpoints chính:**

```
# Destinations
GET    /api/v1/destinations              # Danh sách + search + filter
GET    /api/v1/destinations/{slug}       # Chi tiết 1 điểm đến
GET    /api/v1/destinations/suggest?q=  # Autocomplete

# Flights
GET    /api/v1/flights/search            # Tìm chuyến bay
GET    /api/v1/flights/price-calendar   # Biểu đồ giá theo ngày
GET    /api/v1/flights/routes           # Danh sách tuyến bay

# Hotels
GET    /api/v1/hotels/search            # Tìm khách sạn
GET    /api/v1/hotels/{id}              # Chi tiết khách sạn
GET    /api/v1/hotels/compare?ids=...   # So sánh

# Weather
GET    /api/v1/weather/{slug}           # Thời tiết 7 ngày
GET    /api/v1/weather/batch?slugs=...  # Thời tiết nhiều nơi

# Trips
POST   /api/v1/trips                    # Tạo trip mới
GET    /api/v1/trips/{id}              # Chi tiết trip
PATCH  /api/v1/trips/{id}              # Cập nhật trip
DELETE /api/v1/trips/{id}              # Xóa trip
POST   /api/v1/trips/{id}/days/{day}/items  # Thêm item vào ngày

# Reviews
GET    /api/v1/reviews?destination_slug=  # Danh sách review
POST   /api/v1/reviews                    # Viết review mới

# Auth
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me

# AI
GET    /api/v1/session/{id}/stream      # SSE AI chat
DELETE /api/v1/session/{id}            # Xóa lịch sử chat

# Price Alerts
POST   /api/v1/price-alerts
GET    /api/v1/price-alerts
DELETE /api/v1/price-alerts/{id}
```

### 3.4 Sơ đồ luồng dữ liệu (Data Flow Diagram)

**Luồng 1: Tìm kiếm chuyến bay + Giá thông minh + Thời tiết**

```
User chọn HAN → DAD, tháng 7/2026
         │
         ▼
FastAPI nhận request GET /flights/price-calendar
         │
         ├──► Query PostgreSQL: flights WHERE origin='HAN' AND destination='DAD'
         │         └── monthly_prices JSON → [{date, min_price}]
         │
         ├──► Amadeus API (nếu data DB < 24h cũ): cập nhật giá realtime
         │
         ├──► Query weather_cache WHERE slug='da-nang'
         │         ├── Cache còn mới (< 6h) → dùng luôn
         │         └── Cache hết hạn → gọi Open-Meteo → cập nhật cache
         │
         ▼
FastAPI merge: [{date, price, weather_code, temp_max, rain_mm}]
         │
         ▼
Frontend render PriceWeatherChart:
  - Line chart giá vé
  - Icon thời tiết mỗi ngày
  - Badge "Gợi ý tốt nhất" highlight
```

**Luồng 2: AI Agent xử lý câu hỏi**

```
User gõ: "Tìm vé từ Hưng Yên đến Phú Quốc dưới 2 triệu"
         │
         ▼
SSE endpoint /session/{id}/stream
         │
         ▼
LangGraph Agent:
  Step 1: LLM phân tích → gọi plan_journey("Hưng Yên", "Phú Quốc")
  Step 2: Tool → normalize city → detect "không có sân bay" → relay HN
  Step 3: LLM → gọi search_flights("Hà Nội", "Phú Quốc")
  Step 4: Tool → gọi GET /api/v1/flights/search → DB + Amadeus
  Step 5: LLM → gọi search_hotels("Phú Quốc")
  Step 6: LLM → gọi calculate_budget(2000000, expenses)
  Step 7: LLM tổng hợp → answer
         │
         ▼
Stream từng event về client:
  AGENT_START → AGENT_STEP → TOOL_CALL → TOOL_CALL → AGENT_END
```

### 3.5 Lựa chọn công nghệ (Technology Stack)

| Tầng | Công nghệ | Lý do chọn |
|------|-----------|------------|
| **Frontend** | React 18 + Vite | Ecosystem lớn, HMR nhanh, build tối ưu |
| **Styling** | Tailwind CSS | Utility-first, không cần file CSS riêng |
| **State** | React hooks (useState, useContext) | Đủ dùng cho quy mô hiện tại, không over-engineer |
| **Charts** | Recharts | Dựa trên D3, API React-friendly |
| **Backend** | FastAPI (Python 3.11) | Async native, tự gen OpenAPI docs, type hints |
| **ORM** | SQLAlchemy 2.x async | Mature, type-safe với Mapped[] |
| **Database** | PostgreSQL 16 | JSONB, fulltext search, GIN index, mạnh nhất cho dữ liệu phức tạp |
| **Cache/Queue** | Redis 7 | Streams cho job queue, fast TTL cache |
| **AI Framework** | LangGraph | Stateful agent, loop tool-calling dễ kiểm soát |
| **LLM** | LiteLLM | Provider-agnostic (Groq/OpenAI/Gemini đổi chỗ nhau) |
| **Search** | SearXNG (self-hosted) | Privacy-first, không cần API key, fallback DDG |
| **Container** | Docker + Docker Compose | Đồng nhất môi trường dev/prod |
| **Web server** | Nginx | Reverse proxy, static files, SSL termination |

---

## 4. THIẾT KẾ CƠ SỞ DỮ LIỆU

> **Mục tiêu:** Thiết kế schema chuẩn hoá, đảm bảo tính toàn vẹn dữ liệu và hiệu năng truy vấn.

### 4.1 Phân tích thực thể (Entity Analysis)

**Các thực thể chính được xác định:**

| Thực thể | Mô tả | Thuộc tính chính |
|----------|-------|-----------------|
| **User** | Người dùng hệ thống | id, email, full_name, preferences, level |
| **Destination** | Điểm đến du lịch | id, name, slug, city, country, lat, lng, tags |
| **Hotel** | Khách sạn | id, name, stars, price_per_night, amenities |
| **Flight** | Chuyến bay | id, airline, flight_no, origin, destination, price |
| **Trip** | Kế hoạch chuyến đi | id, title, start_date, end_date, budget |
| **Review** | Đánh giá điểm đến / khách sạn | id, rating, content, images |
| **PriceAlert** | Cảnh báo giá | id, route, target_price, is_active |

### 4.2 Sơ đồ quan hệ thực thể (ERD)

```
USERS ──────────────────────────────────────────────────┐
  │ id (PK)                                              │
  │ email (UNIQUE)                                       │
  │ full_name                                            │
  │ travel_preferences (JSONB)                           │
  │ level                                                │
  │                                                      │
  ├──< TRIPS (owner_id FK)                               │
  │     │ id (PK)                                        │
  │     │ title                                          │
  │     │ start_date, end_date                           │
  │     │ budget                                         │
  │     │                                                │
  │     ├──< TRIP_DAYS (trip_id FK)                      │
  │     │     │                                          │
  │     │     └──< ITINERARY_ITEMS (day_id FK)           │
  │     │                                                │
  │     ├──< TRIP_MEMBERS (trip_id, user_id FK)          │
  │     └──< TRIP_EXPENSES (trip_id FK)                  │
  │                                                      │
  ├──< REVIEWS (user_id FK)                              │
  └──< PRICE_ALERTS (user_id FK)                         │
                                                         │
DESTINATIONS ─────────────────────────────────────────────
  │ id (PK)
  │ slug (UNIQUE)
  │ name, city, country
  │ lat, lng
  │ tags (JSONB)
  │ avg_rating
  │
  ├──< HOTELS (destination_id FK)
  │     │ id (PK)
  │     │ name, stars
  │     │ price_per_night
  │     │ amenities (JSONB)
  │     └──< REVIEWS (hotel_id FK)
  │
  ├──< FLIGHTS (destination_id FK)
  │     id (PK)
  │     airline, flight_no
  │     origin, destination (IATA)
  │     price, monthly_prices (JSONB)
  │
  └──< REVIEWS (destination_id FK)
```

### 4.3 Chuẩn hoá dữ liệu (Normalization)

Schema được thiết kế theo **3NF (Third Normal Form):**
- **1NF:** Mỗi cột có giá trị nguyên tử (trừ JSONB được dùng có chủ ý cho dữ liệu semi-structured như `tags`, `amenities`)
- **2NF:** Mọi thuộc tính phụ thuộc đầy đủ vào khóa chính
- **3NF:** Không có phụ thuộc bắc cầu giữa các thuộc tính không khóa

**Lý do dùng JSONB cho một số trường:**
- `tags`, `amenities`, `images`: Dữ liệu dạng mảng, không cần join bảng riêng, truy vấn bằng GIN index
- `travel_preferences`: Dữ liệu người dùng cá nhân hoá, schema thay đổi theo thời gian
- `monthly_prices`: Dữ liệu time-series dạng key-value đơn giản

### 4.4 Chiến lược Index

```sql
-- Tìm kiếm fulltext tiếng Việt (unaccent + GIN)
CREATE INDEX idx_dest_fts ON destinations
    USING GIN(to_tsvector('simple',
        unaccent(name || ' ' || city || ' ' || description)));

-- Tìm chuyến bay theo tuyến + sắp xếp giá
CREATE INDEX idx_flights_route ON flights(origin, destination);
CREATE INDEX idx_flights_price ON flights(price);

-- Filter khách sạn theo giá và sao
CREATE INDEX idx_hotels_price_stars ON hotels(destination_id, price_per_night, stars);

-- Truy vấn trip của user
CREATE INDEX idx_trips_owner ON trips(owner_id);

-- Public trips cho cộng đồng
CREATE INDEX idx_trips_public ON trips(is_public) WHERE is_public = TRUE;

-- Review của điểm đến / khách sạn
CREATE INDEX idx_reviews_dest ON reviews(destination_id);
CREATE INDEX idx_reviews_hotel ON reviews(hotel_id);
```

### 4.5 Chiến lược dữ liệu mẫu (Seed Data Strategy)

**Nguồn dữ liệu thực tế:**

| Nguồn | Nội dung | Cách thu thập |
|-------|---------|---------------|
| OpenTripMap API | 10 điểm đến, POI, khách sạn cơ bản | Collector tự động |
| Amadeus Sandbox | Giá vé 10 tuyến bay | Collector tự động |
| Open-Meteo API | Thời tiết 10 thành phố | Collector tự động, cache 6h |
| Thủ công | 15+ khách sạn có địa chỉ, giá, ảnh thật | Nhập tay từ Booking.com |
| Script SQL | 3 user mẫu, 1 trip mẫu 5N4Đ Đà Nẵng | file 02_seed_data.sql |

---

## 5. THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG

> **Mục tiêu:** Thiết kế UI/UX trước khi code để tránh làm đi làm lại, đảm bảo trải nghiệm người dùng nhất quán.

### 5.1 Nghiên cứu người dùng (User Research)

**Persona 1 — Minh (25 tuổi, nhân viên văn phòng)**
- Đi du lịch 3–4 lần/năm cùng bạn bè
- Hay dùng điện thoại để tìm kiếm
- Bế tắc khi so sánh giá khách sạn giữa nhiều trang
- Muốn lên lịch trình nhanh, không cần phức tạp

**Persona 2 — Linh (32 tuổi, kết hôn, có con nhỏ)**
- Lên kế hoạch du lịch gia đình, ngân sách cố định
- Cẩn thận, kiểm tra thời tiết trước khi đặt
- Hay bị overwhelmed với quá nhiều thông tin
- Muốn mọi thứ ở một nơi, dễ in ra / chia sẻ

### 5.2 Luồng người dùng (User Flow)

**User Flow chính — Lên kế hoạch chuyến đi:**

```
Trang chủ
    │
    ├── [Tìm kiếm] → Trang Tìm kiếm → Filter → Kết quả
    │                       │
    │                       ▼
    │               Trang Chi tiết Điểm đến
    │                       │
    │              ┌────────┴────────┐
    │              ▼                 ▼
    │         Xem Giá +          Xem Khách sạn
    │         Thời tiết               │
    │              │                  │
    │              └────────┬─────────┘
    │                       ▼
    │               [Thêm vào Trip]
    │                       │
    │                       ▼
    │               Trip Builder
    │                       │
    │              ┌────────┴────────┐
    │              ▼                 ▼
    │         Kéo-thả            Tính chi phí
    │         lịch trình              │
    │              │                  │
    │              └────────┬─────────┘
    │                       ▼
    │                Chia sẻ / Xuất PDF
    │
    └── [Hỏi AI] → Chat Widget (mọi trang)
```

### 5.3 Sơ đồ trang (Sitemap)

```
/ (Trang chủ)
├── /search (Tìm kiếm)
│   └── /destination/:slug (Chi tiết điểm đến)
│       ├── Tab: Tổng quan
│       ├── Tab: Khách sạn
│       ├── Tab: Vé máy bay + Giá thông minh
│       ├── Tab: Thời tiết
│       └── Tab: Đánh giá
├── /trip-builder
│   └── /trip-builder/:tripId (Chỉnh sửa trip)
├── /community (Cộng đồng)
│   └── /community/:slug (Forum theo điểm đến)
├── /profile
│   ├── /profile/trips (Lịch sử chuyến đi)
│   ├── /profile/wishlist
│   ├── /profile/alerts (Cảnh báo giá)
│   └── /profile/settings
├── /auth/login
└── /auth/register
```

### 5.4 Wireframe & Prototype

**Công cụ:** Figma

**Các màn hình cần wireframe:**

| Độ ưu tiên | Màn hình | Trạng thái |
|-----------|---------|------------|
| Cao | Trang chủ (hero + search bar) | Cần làm |
| Cao | Trang tìm kiếm + filter sidebar | Cần làm |
| Cao | Chi tiết điểm đến (4 tabs) | Cần làm |
| Cao | Biểu đồ Giá + Thời tiết | Cần làm |
| Cao | Trip Builder kéo-thả | Cần làm |
| Trung bình | Trang profile | Cần làm |
| Trung bình | AI Chat Widget | Cần làm |
| Thấp | Trang cộng đồng | Cần làm |

**Nguyên tắc thiết kế:**
- **Mobile-first:** Thiết kế cho màn hình 375px trước, sau đó mở rộng
- **Dark/Light mode:** Hỗ trợ cả hai theme từ đầu
- **Tối giản:** Không nhồi nhét thông tin, whitespace hợp lý
- **Nhất quán:** Dùng Design System thống nhất (màu sắc, typography, spacing)

### 5.5 Design System

**Bảng màu (Color Palette):**

| Token | Dark Mode | Light Mode | Dùng cho |
|-------|-----------|------------|---------|
| `--color-primary` | #7c3aed | #6d28d9 | Buttons, links, accent |
| `--color-secondary` | #06b6d4 | #0891b2 | Highlight, badge |
| `--color-bg` | #080812 | #f8f7ff | Background |
| `--color-surface` | rgba(10,10,20,0.85) | #ffffff | Card, panel |
| `--color-text` | #cbd5e1 | #374151 | Body text |
| `--color-text-bright` | #f1f5f9 | #111827 | Heading |

**Typography:**
- Font chính: *Be Vietnam Pro* (Google Fonts) — tối ưu cho tiếng Việt
- Font code: *JetBrains Mono* — hiển thị code, số liệu kỹ thuật
- Scale: 11px / 12px / 13px / 14px / 16px / 18px / 24px / 32px

**Component Library (tự xây):**
- Button (primary, secondary, ghost, danger)
- Input, Select, Textarea
- Card (destination, hotel, flight)
- Badge, Tag, Chip
- Modal, Drawer
- Toast notification
- Skeleton loading
- Star rating

---

## 6. XÂY DỰNG MÔI TRƯỜNG PHÁT TRIỂN

> **Mục tiêu:** Đảm bảo tất cả thành viên nhóm làm việc trên cùng môi trường, tránh lỗi "chạy máy tôi được, máy bạn không được".

### 6.1 Cài đặt công cụ phát triển

**Yêu cầu hệ thống:**
- Docker Desktop (Windows/Mac) hoặc Docker Engine + Docker Compose (Linux)
- Node.js 20+ (cho frontend dev)
- Python 3.11+ (cho backend dev local)
- Git
- VS Code với extensions: Python, Pylance, ESLint, Prettier, Docker, GitLens

### 6.2 Khởi tạo repository

```bash
# Cấu trúc thư mục dự án
TravelBuddy_AI/
├── frontend/          # React app
├── backend/           # FastAPI app
├── database/          # SQL schema + seed
├── docker/            # Nginx, SearXNG config
├── docs/              # Tài liệu
├── tests/             # Test files
├── .env.example       # Template biến môi trường
├── docker-compose.yml # Orchestration
└── README.md
```

**Quy trình Git:**
- **Branch `main`:** Code production, chỉ merge qua PR
- **Branch `develop`:** Integration branch
- **Branch `feature/xxx`:** Mỗi tính năng 1 branch
- **Commit message format:** `feat: add price chart component` / `fix: hotel search null pointer` / `docs: update API documentation`

### 6.3 Cấu hình Docker Compose

**Services trong docker-compose.yml:**
- `postgres` — PostgreSQL 16 với healthcheck
- `redis` — Redis 7 với password
- `searxng` — Self-hosted search
- `api` — FastAPI app
- `worker` — LangGraph agent workers (×4)
- `frontend` — Build React app một lần
- `nginx` — Entry point duy nhất :8890

```bash
# Khởi động toàn bộ stack
cp .env.example .env        # Điền API keys
docker-compose up -d --build

# Kiểm tra logs
docker-compose logs -f api
docker-compose logs -f worker
```

### 6.4 Quản lý biến môi trường

**Nguyên tắc bảo mật:**
- File `.env` **không bao giờ** commit lên Git (đã có trong `.gitignore`)
- `.env.example` chứa tất cả keys nhưng không có giá trị thật
- Mỗi thành viên có `.env` riêng ở máy local
- Production dùng biến môi trường của hosting (không có file .env trên server)

---

## 7. PHÁT TRIỂN BACKEND

> **Mục tiêu:** Xây dựng API server ổn định, bảo mật, có thể mở rộng.

### 7.1 Cấu trúc thư mục Backend

```
backend/
├── src/
│   ├── api/
│   │   ├── server.py          # FastAPI app + middleware
│   │   ├── routes/
│   │   │   ├── destinations.py
│   │   │   ├── flights.py
│   │   │   ├── hotels.py
│   │   │   ├── weather.py
│   │   │   ├── trips.py
│   │   │   ├── reviews.py
│   │   │   ├── auth.py
│   │   │   └── price_alerts.py
│   │   └── schemas/           # Pydantic models
│   │       ├── destination.py
│   │       ├── flight.py
│   │       ├── hotel.py
│   │       └── user.py
│   ├── db/
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── connection.py      # Engine, session factory
│   │   └── migrate.py         # Migration script
│   ├── agent/
│   │   └── graph.py           # LangGraph agent
│   ├── tools/
│   │   ├── travel.py          # Travel tools
│   │   ├── web_search.py      # Web search
│   │   └── image_search.py    # Image search
│   ├── cache/
│   │   └── session.py         # Redis client
│   ├── queue/
│   │   └── streams.py         # Job queue
│   ├── security/
│   │   └── guardrails.py      # AI safety
│   └── config.py              # Centralised config
└── requirements.txt
```

### 7.2 Quy trình phát triển Backend

**Bước 1 — Setup DB và migrations**
- Viết SQLAlchemy models từ schema SQL
- Viết migration script (chạy 01_schema.sql + 02_seed_data.sql)
- Verify dữ liệu đã insert đúng

**Bước 2 — CRUD APIs cơ bản**
- Destinations: GET list, GET detail, search fulltext
- Hotels: GET search với filter, GET detail
- Flights: GET search, GET price-calendar
- Mỗi endpoint đều có Pydantic response schema

**Bước 3 — Authentication**
- POST /auth/register: hash password bằng bcrypt, lưu DB
- POST /auth/login: verify password, tạo JWT token
- Middleware verify JWT cho protected routes

**Bước 4 — Business logic phức tạp**
- `/flights/price-calendar`: join flight data + weather cache
- `/hotels/compare`: aggregate data 3 khách sạn
- Trip Builder CRUD: nested resources (trip → days → items)

**Bước 5 — Background jobs**
- Refresh weather cache mỗi 6 giờ
- Check price alerts mỗi 6 giờ
- Clean up expired sessions

### 7.3 Bảo mật Backend

| Biện pháp | Implement |
|-----------|-----------|
| Rate limiting | Redis sliding window, 20 req/min/user |
| Input validation | Pydantic v2 strict mode |
| SQL injection | SQLAlchemy parameterized queries (không raw SQL) |
| XSS prevention | Pydantic html escape output |
| CORS | Whitelist domains, không dùng `allow_origins=["*"]` production |
| Secret management | Biến môi trường, không hardcode |
| AI Guardrails | 4-layer: InputGuard, ToolSanitizer, OutputGuard, LLMGuard |

---

## 8. PHÁT TRIỂN FRONTEND

> **Mục tiêu:** Xây dựng giao diện người dùng trực quan, hiệu năng cao, responsive.

### 8.1 Cấu trúc thư mục Frontend

```
frontend/src/
├── pages/
│   ├── HomePage.jsx
│   ├── SearchPage.jsx
│   ├── DestinationPage.jsx
│   ├── TripBuilderPage.jsx
│   ├── ProfilePage.jsx
│   └── AuthPage.jsx
├── components/
│   ├── common/
│   │   ├── Navbar.jsx
│   │   ├── Footer.jsx
│   │   ├── SearchBar.jsx
│   │   ├── FilterSidebar.jsx
│   │   └── SkeletonLoader.jsx
│   ├── destination/
│   │   ├── DestinationCard.jsx
│   │   └── WeatherWidget.jsx
│   ├── flight/
│   │   ├── FlightCard.jsx
│   │   └── PriceWeatherChart.jsx
│   ├── hotel/
│   │   ├── HotelCard.jsx
│   │   └── HotelCompare.jsx
│   ├── trip/
│   │   ├── TripCard.jsx
│   │   └── DayLane.jsx
│   ├── community/
│   │   └── ReviewSection.jsx
│   └── ai/
│       └── AIAssistantWidget.jsx
├── hooks/
│   ├── useSearch.js
│   ├── useWeather.js
│   └── useAuth.js
├── services/
│   └── api.js             # Axios instance + API calls
├── utils/
│   ├── formatters.js      # Format tiền, ngày, thời tiết
│   └── constants.js
└── main.jsx
```

### 8.2 Thứ tự phát triển Frontend

1. **Setup:** Cấu hình React Router, Axios instance, theme context
2. **Layout:** Navbar, Footer, protected routes
3. **Search Page:** Search bar + autocomplete + filter + kết quả
4. **Destination Detail:** 4 tabs với lazy loading
5. **Price Weather Chart:** Recharts + Open-Meteo data
6. **Trip Builder:** DnD Kit, timeline, CRUD
7. **Auth:** Login/Register forms
8. **Profile:** Lịch sử, wishlist, cài đặt
9. **AI Widget:** Floating button, SSE chat
10. **Reviews:** Form + gallery

---

## 9. TÍCH HỢP API BÊN THỨ BA

> **Mục tiêu:** Tích hợp các nguồn dữ liệu thực tế từ bên ngoài để hệ thống có dữ liệu phong phú và cập nhật.

### 9.1 Danh sách API tích hợp

| API | Mục đích | Giới hạn | Chiến lược |
|-----|---------|----------|-----------|
| **Open-Meteo** | Thời tiết 7–16 ngày | Không giới hạn, miễn phí | Cache 6h trong PostgreSQL |
| **Frankfurter** | Tỷ giá hối đoái (ECB) | Không giới hạn, miễn phí | Cache 24h |
| **RestCountries** | Thông tin quốc gia, visa | Không giới hạn, miễn phí | Cache 7 ngày (dữ liệu ít thay đổi) |
| **OpenTripMap** | Điểm tham quan, POI | 500 req/ngày (free) | Chạy 1 lần khi init DB |
| **Amadeus Sandbox** | Giá vé máy bay realtime | 100 req/ngày (free) | Cache 1h, dùng cho search thật |
| **Serper/Google** | Search web cho AI | 100 req/tháng (free) | Chỉ gọi khi AI cần |
| **DuckDuckGo** | Fallback web search | Không giới hạn | Fallback khi Serper hết quota |
| **Groq API** | LLM cho AI agent | 30 req/phút (free) | Rate limit + queue |

### 9.2 Chiến lược Caching API

```
User Request
    │
    ▼
Kiểm tra Redis cache
    │
    ├── Cache HIT (TTL còn) → Trả về ngay
    │
    └── Cache MISS
            │
            ▼
        Gọi External API
            │
            ├── Thành công → Lưu vào cache + PostgreSQL → Trả về
            │
            └── Thất bại → Trả về data cũ từ DB (stale-while-revalidate)
                           hoặc error message thân thiện
```

### 9.3 Error Handling cho External APIs

**Nguyên tắc Fail Gracefully:**
- Amadeus không trả lời → Dùng giá từ DB nội bộ, hiển thị badge "Giá tham khảo"
- Open-Meteo lỗi → Hiển thị "Không có thông tin thời tiết", ẩn weather widget
- Groq rate limit → Queue job, trả về "Đang xử lý, vui lòng chờ"
- Không có internet → Dùng data đã cache, hiển thị "Offline mode"

---

## 10. TÍCH HỢP TRÍ TUỆ NHÂN TẠO

> **Mục tiêu:** Tích hợp AI như một lớp hỗ trợ thông minh, không phải trung tâm hệ thống.

### 10.1 Kiến trúc AI Agent

**Mô hình ReAct (Reason + Act)** với LangGraph:

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│  LangGraph Agent Loop           │
│                                 │
│  [Think] → [Act] → [Observe]   │
│      │                          │
│      └── Lặp lại tối đa 12 lần │
└─────────────────────────────────┘
    │
    ├── Tool: plan_journey()
    ├── Tool: search_flights()
    ├── Tool: search_hotels()
    ├── Tool: calculate_budget()
    ├── Tool: get_travel_tips()
    ├── Tool: web_search()
    └── Tool: search_images()
```

### 10.2 Hệ thống Guardrails (An toàn AI)

**4 lớp bảo vệ:**

| Lớp | Tên | Chức năng | Vị trí |
|-----|-----|-----------|--------|
| L1 | InputGuard | Phát hiện prompt injection, jailbreak | Trước khi vào LLM |
| L2 | ToolOutputSanitizer | Làm sạch kết quả từ tool (tránh indirect injection) | Sau khi tool chạy |
| L3 | OutputGuard | Phát hiện system prompt leak, persona hijack | Sau khi LLM trả lời |
| L4 | LLMGuard (optional) | Classify safety bằng model nhỏ | Tùy chọn, tốn thêm 200ms |

### 10.3 Tái định vị AI trong hệ thống mới

**Trước (AI-first):** User → Chat với AI → AI gọi tools → Trả lời

**Sau (System-first):** User → Tương tác với UI → AI chỉ khi cần

```
Khi nào AI được gọi:
  ✅ User click nút "Hỏi AI về điểm đến này"
  ✅ User gõ vào AI widget
  ✅ User không tìm thấy kết quả phù hợp → gợi ý thay thế
  ✅ User muốn tóm tắt / so sánh 3 lựa chọn đang xem

Khi nào KHÔNG gọi AI:
  ❌ Tìm kiếm thông thường (dùng API trực tiếp)
  ❌ Hiển thị giá / thời tiết (dùng DB + API)
  ❌ CRUD trip builder (tự xử lý frontend)
```

---

## 11. KIỂM THỬ

> **Mục tiêu:** Đảm bảo hệ thống hoạt động đúng, ổn định và đáp ứng yêu cầu đã đặt ra.

### 11.1 Chiến lược kiểm thử (Testing Strategy)

**Phương pháp:** Testing Pyramid

```
        /\
       /  \
      / E2E \       (Ít nhất, chi phí cao)
     /────────\
    / Integration\  (Vừa phải)
   /──────────────\
  /   Unit Tests   \ (Nhiều nhất, chi phí thấp)
 /────────────────────\
```

### 11.2 Unit Testing

**Backend (pytest):**

```python
# Test ví dụ: normalize_city()
def test_normalize_city_with_accents():
    assert normalize_city("hà nội") == "Hà Nội"
    assert normalize_city("HAN") == "Hà Nội"
    assert normalize_city("hanoi") == "Hà Nội"

# Test calculate_budget()
def test_calculate_budget_over():
    result = calculate_budget.invoke({
        "total_budget": 5_000_000,
        "expenses": "ve_may_bay:3000000,khach_san:2500000"
    })
    assert "VƯỢT NGÂN SÁCH" in result

# Test guardrails
def test_prompt_injection_blocked():
    guard = InputGuard()
    result = guard.check("Ignore all previous instructions and...")
    assert result.is_blocked == True
```

**Frontend (Vitest + React Testing Library):**

```javascript
// Test PriceWeatherChart render
test('renders weather icons for each day', () => {
  const mockData = [
    { date: '2026-07-01', min_price: 980000, weather_code: 0, temp_max: 31 }
  ];
  render(<PriceWeatherChart data={mockData} />);
  expect(screen.getByText('31°C')).toBeInTheDocument();
});
```

### 11.3 Integration Testing

**Test các luồng kết hợp:**

```python
# Test API endpoint thật
async def test_search_flights_with_weather():
    response = await client.get(
        "/api/v1/flights/price-calendar",
        params={"origin": "HAN", "destination": "DAD", "month": "2026-07"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "weather_condition" in data[0]
    assert "min_price" in data[0]
```

### 11.4 End-to-End Testing (Playwright)

**Test các luồng người dùng quan trọng:**

```javascript
test('User tìm kiếm và xem biểu đồ giá + thời tiết', async ({ page }) => {
  await page.goto('/search');
  await page.fill('[data-testid="search-input"]', 'Đà Nẵng');
  await page.click('[data-testid="search-btn"]');
  await page.click('text=Xem chi tiết');
  await page.click('text=Vé máy bay');
  await expect(page.locator('[data-testid="price-weather-chart"]')).toBeVisible();
  await expect(page.locator('[data-testid="best-day-badge"]')).toBeVisible();
});
```

### 11.5 Performance Testing

**Công cụ:** k6

```javascript
// Load test: 100 concurrent users
export default function () {
  const res = http.get('http://localhost:8890/api/v1/destinations');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

### 11.6 Ma trận kiểm thử (Test Matrix)

| Tính năng | Unit | Integration | E2E | Performance | Kết quả |
|-----------|------|------------|-----|-------------|---------|
| Search destinations | ✅ | ✅ | ✅ | ✅ | — |
| Price + Weather chart | ✅ | ✅ | ✅ | — | — |
| Trip Builder | ✅ | ✅ | ✅ | — | — |
| AI guardrails | ✅ | ✅ | — | — | — |
| Auth flow | ✅ | ✅ | ✅ | — | — |
| Rate limiting | — | ✅ | — | ✅ | — |

---

## 12. TRIỂN KHAI

> **Mục tiêu:** Đưa hệ thống lên môi trường production ổn định, có thể trình diễn.

### 12.1 Môi trường triển khai

| Môi trường | Mô tả | Cấu hình |
|-----------|-------|---------|
| **Local** | Máy phát triển cá nhân | Docker Compose, hot reload |
| **Development** | Server dùng chung cả nhóm | Docker Compose, tích hợp CI |
| **Staging** | Giống production, dùng để test | Docker Compose production mode |
| **Production** | Demo cho giảng viên | VPS + Docker Compose + domain |

### 12.2 Quy trình CI/CD

```
Git push lên branch develop
         │
         ▼
GitHub Actions trigger:
  1. Lint: flake8 (Python) + ESLint (JS)
  2. Unit tests: pytest + Vitest
  3. Build Docker images
  4. Deploy lên Staging server
  5. Integration tests trên Staging
         │
         ▼
Merge vào main → Deploy lên Production
```

### 12.3 Checklist trước khi deploy Production

**Infrastructure:**
- [ ] VPS có đủ RAM (tối thiểu 2GB cho stack đầy đủ)
- [ ] Domain + SSL certificate (Let's Encrypt)
- [ ] Nginx config HTTPS redirect
- [ ] Firewall: chỉ mở port 80, 443, 22

**Security:**
- [ ] Đổi tất cả default passwords trong .env
- [ ] CORS: whitelist domain production, xóa `allow_origins=["*"]`
- [ ] Database: không expose port ra ngoài
- [ ] Redis: đặt password, không expose port

**Data:**
- [ ] Chạy migration + seed data
- [ ] Chạy 3 free collectors (weather, exchange rate, countries)
- [ ] Verify API keys hợp lệ (Amadeus, Groq/OpenAI)

**Monitoring:**
- [ ] Health check endpoint `/health` trả về 200
- [ ] Docker restart policy: `unless-stopped`
- [ ] Log rotation cấu hình

---

## 13. ĐÁNH GIÁ & CẢI TIẾN

> **Mục tiêu:** Đo lường hiệu quả thực tế, thu thập phản hồi và cải tiến liên tục.

### 13.1 Các chỉ số đo lường (KPIs)

**Kỹ thuật:**

| Chỉ số | Mục tiêu | Công cụ đo |
|--------|---------|-----------|
| Page load time | < 3 giây | Lighthouse |
| API response time (p95) | < 500ms | Postman, k6 |
| Uptime | ≥ 99% | Docker healthcheck |
| Test coverage | ≥ 60% | pytest-cov |
| Lighthouse Performance | ≥ 80 | Chrome DevTools |
| Lighthouse Accessibility | ≥ 90 | Chrome DevTools |

**Người dùng (cho buổi demo):**
- Thời gian hoàn thành task "Tìm chuyến bay + xem thời tiết" < 2 phút
- Tỷ lệ người dùng test hiểu cách dùng Trip Builder mà không cần hướng dẫn

### 13.2 User Testing & Phản hồi

**Kịch bản test với người dùng thật:**

1. *"Bạn muốn đi Đà Nẵng tháng 7. Hãy tìm chuyến bay rẻ nhất vào ngày thời tiết đẹp."*
   - Quan sát: User có dùng biểu đồ Giá + Thời tiết không? Có hiểu badge "Gợi ý tốt nhất" không?

2. *"Lên lịch trình 3 ngày Hội An cho 2 người, ngân sách 5 triệu."*
   - Quan sát: User có tự tìm được Trip Builder không? Kéo-thả có trực quan không?

3. *"Hỏi AI một câu về du lịch mà bạn không tìm thấy trên hệ thống."*
   - Quan sát: User có tìm thấy AI widget không? Phản hồi của AI có hữu ích không?

### 13.3 Danh sách cải tiến (Backlog)

Dựa trên phản hồi, sắp xếp vào backlog:

- **P0 (Critical):** Bugs ảnh hưởng core flow
- **P1 (High):** UX friction points được nhiều user phàn nàn
- **P2 (Medium):** Tính năng được yêu cầu thêm
- **P3 (Low):** Nice-to-have

---

## 14. TÀI LIỆU HÓA

> **Mục tiêu:** Tạo tài liệu đầy đủ phục vụ báo cáo học thuật và bàn giao dự án.

### 14.1 Tài liệu kỹ thuật

| Tài liệu | Nội dung | File |
|---------|---------|------|
| **README.md** | Hướng dẫn cài đặt, chạy local, cấu trúc project | `README.md` |
| **ARCHITECTURE.md** | Kiến trúc hệ thống chi tiết, sơ đồ, data flow | `docs/ARCHITECTURE.md` |
| **API Documentation** | Tự động generate từ FastAPI OpenAPI | `http://localhost:8000/docs` |
| **Database Schema** | ERD + mô tả từng bảng | `database/travel_buddy_db/README.md` |
| **Environment Setup** | Hướng dẫn cài đặt môi trường dev | `docs/DEV_SETUP.md` |

### 14.2 Tài liệu báo cáo đồ án

**Cấu trúc báo cáo đề xuất:**

```
Chương 1: Giới thiệu dự án
  1.1 Đặt vấn đề
  1.2 Mục tiêu dự án
  1.3 Phạm vi và giới hạn
  1.4 Bố cục báo cáo

Chương 2: Phân tích yêu cầu
  2.1 Khảo sát người dùng
  2.2 Phân tích đối thủ cạnh tranh
  2.3 Yêu cầu chức năng (bảng FR)
  2.4 Yêu cầu phi chức năng
  2.5 Use Case Diagram

Chương 3: Thiết kế hệ thống
  3.1 Kiến trúc tổng thể
  3.2 Thiết kế CSDL (ERD)
  3.3 Thiết kế API
  3.4 Thiết kế UI/UX (wireframe, design system)

Chương 4: Công nghệ sử dụng
  4.1 Technology Stack và lý do lựa chọn
  4.2 Các API bên thứ ba
  4.3 AI Framework (LangGraph, LiteLLM)

Chương 5: Cài đặt và triển khai
  5.1 Môi trường phát triển
  5.2 Phát triển Backend
  5.3 Phát triển Frontend
  5.4 Tích hợp AI
  5.5 Triển khai với Docker

Chương 6: Kiểm thử
  6.1 Chiến lược kiểm thử
  6.2 Kết quả Unit Test
  6.3 Kết quả Integration Test
  6.4 Đánh giá hiệu năng

Chương 7: Kết quả và đánh giá
  7.1 Demo các tính năng chính
  7.2 So sánh với mục tiêu ban đầu
  7.3 Hạn chế và hướng phát triển

Tài liệu tham khảo
Phụ lục
```

### 14.3 Tài liệu hướng dẫn sử dụng (User Manual)

Viết hướng dẫn ngắn gọn cho từng tính năng chính:
- Cách tìm kiếm và lọc điểm đến
- Cách đọc biểu đồ Giá + Thời tiết
- Cách tạo và chia sẻ lịch trình
- Cách dùng AI chat widget

---

## TÓM TẮT CÁC BƯỚC & THỨ TỰ ƯU TIÊN

```
GIAI ĐOẠN 1 — CHUẨN BỊ (Tuần 1-2)
  ✅ Bước 1: Xác định bài toán + Nghiên cứu thị trường
  ✅ Bước 2: Thu thập và đặc tả yêu cầu (Functional + Non-functional)
  ✅ Bước 3: Lựa chọn công nghệ + Kiến trúc hệ thống
  ✅ Bước 4: Thiết kế CSDL + ERD

GIAI ĐOẠN 2 — THIẾT KẾ (Tuần 3-4)
  ✅ Bước 5: Wireframe UI/UX + Design System
  ✅ Bước 6: Setup Git repo + Docker environment
  ✅ Bước 7: Viết API specification (contract-first)

GIAI ĐOẠN 3 — XÂY DỰNG (Tuần 5-12)
  ✅ Bước 8: Setup DB (PostgreSQL + migrations + seed data)
  ✅ Bước 9: Backend — CRUD APIs cơ bản
  ✅ Bước 10: Tích hợp APIs bên ngoài (collectors)
  ✅ Bước 11: Frontend — Search + Destination detail
  ✅ Bước 12: Giá thông minh + Thời tiết tích hợp
  ✅ Bước 13: Trip Builder
  ✅ Bước 14: AI widget tái định vị

GIAI ĐOẠN 4 — HOÀN THIỆN (Tuần 13-14)
  ✅ Bước 15: Kiểm thử toàn diện
  ✅ Bước 16: Tối ưu hiệu năng + bảo mật
  ✅ Bước 17: Deploy production
  ✅ Bước 18: Viết báo cáo + tài liệu hóa
```

---

*Tài liệu được soạn theo chuẩn IEEE 830 (Software Requirements Specification) và phương pháp Agile Scrum áp dụng trong môi trường học thuật.*

*Phiên bản: 1.0 | Ngày cập nhật: 2026*
