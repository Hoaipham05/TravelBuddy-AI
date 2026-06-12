# TravelBuddy AI - Báo Cáo Dữ Liệu

Ngày báo cáo: 11/06/2026  
Môi trường kiểm tra: PostgreSQL chạy bằng Docker, database `travel_buddy`  
Trạng thái: đã có dữ liệu nền cho backend/data layer, chưa xây frontend

## 1. Tóm Tắt Hiện Trạng

TravelBuddy AI đang đi theo kiến trúc hybrid:

- Dữ liệu tĩnh/nền được seed vào PostgreSQL: điểm đến, sân bay, hãng bay, tuyến bay phổ biến, metadata khách sạn, địa danh du lịch, packing templates, quốc gia fallback.
- Dữ liệu biến động được lấy từ API và lưu snapshot/cache có TTL: giá vé máy bay, giá phòng khách sạn, thời tiết, tỷ giá.
- Không seed giá vé/giá phòng mock vào production flow. Giá vé và giá phòng hiện có đến từ provider thật.
- Frontend chưa xây, nhưng backend API và database đã sẵn sàng để frontend đọc dữ liệu.

Tổng quan số bản ghi hiện tại:

| Bảng | Số bản ghi |
|---|---:|
| `destinations` | 10 |
| `airports` | 9 |
| `airlines` | 3 |
| `flight_routes` | 20 |
| `flight_price_snapshots` | 737 |
| `hotels` | 223 |
| `hotel_rate_snapshots` | 188 |
| `hotel_images` | 970 |
| `weather_cache` | 10 |
| `weather_daily_forecasts` | 100 |
| `pois` | 150 |
| `exchange_rate_cache` | 330 |
| `countries` | 10 |
| `packing_templates` | 4 |
| `packing_template_items` | 32 |
| `users` | 2 |
| `trips` | 1 |
| `reviews` | 1 |

## 2. Nguồn Dữ Liệu

| Nhóm dữ liệu | Nguồn hiện tại | Cách lấy | Trạng thái |
|---|---|---|---|
| Điểm đến | Manual curated seed | `02_seed_data.sql` | Đã có 10 điểm đến nội địa |
| Sân bay, hãng bay, route | Manual seed theo top route nội địa | `02_seed_data.sql` | Đã có 9 sân bay, 3 hãng, 20 route |
| Giá vé máy bay | SerpApi Google Flights | `pipeline.py --only flights` | Đã có 737 snapshot |
| Metadata khách sạn | Manual seed + SerpApi Google Hotels enrichment | `02_seed_data.sql` + `pipeline.py --only hotels` | Đã có 223 khách sạn |
| Giá phòng khách sạn | SerpApi Google Hotels | `pipeline.py --only hotels` | Đã có 188 rate snapshot |
| Ảnh khách sạn | SerpApi Google Hotels | Collector hotels lưu vào `hotel_images` | Đã có 970 ảnh |
| Thời tiết | Open-Meteo primary, MET Norway fallback | `pipeline.py --only weather` | Đã có 100 forecast rows qua `met-norway` |
| POI / địa danh | Manual curated seed | `03_seed_pois_curated.sql` | Đã có 150 POI |
| Tỷ giá | Frankfurter primary, exchange-rate fallback | `pipeline.py --only exchange_rate` | Đã có 330 rows |
| Metadata quốc gia | RestCountries/fallback seed | `02_seed_data.sql`, collector countries | Đã có 10 countries |
| Checklist hành lý | Rule/template seed | `02_seed_data.sql` | Đã có 4 templates, 32 items |
| Link đặt vé/đặt phòng | Provider link + fallback chính thức | `04_seed_booking_links.sql` + collectors | Đã có link cho flight/hotel hiện tại |

Tài liệu provider chính:

- SerpApi Google Flights: https://serpapi.com/google-flights-api
- SerpApi Google Hotels: https://serpapi.com/google-hotels-api
- Open-Meteo Forecast API: https://open-meteo.com/en/docs
- MET Norway Locationforecast API: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- Frankfurter API: https://www.frankfurter.app/docs
- RestCountries API: https://restcountries.com/
- OpenTripMap API, dùng để enrich POI sau này: https://dev.opentripmap.org/product

## 3. Mô Tả Chi Tiết Theo Nhóm Dữ Liệu

### 3.1 Điểm Đến

Bảng chính: `destinations`

Đã seed 10 điểm đến nội địa:

| Slug | Tên |
|---|---|
| `da-nang` | Đà Nẵng |
| `ha-noi` | Hà Nội |
| `ho-chi-minh` | TP.HCM |
| `hoi-an` | Hội An |
| `phu-quoc` | Phú Quốc |
| `nha-trang` | Nha Trang |
| `da-lat` | Đà Lạt |
| `hue` | Huế |
| `ha-long` | Hạ Long |
| `sapa` | Sapa |

Mỗi destination có:

- Tên, slug, city/province, country.
- Mã IATA city nếu có.
- Mô tả, tọa độ lat/lng.
- Tags, best months, rating placeholder.
- `popularity_rank` để sắp xếp top destination.

Nguồn: curated manual seed trong `database/travel_buddy_db/02_seed_data.sql`.

### 3.2 Flight Routes Và Giá Vé Máy Bay

Bảng chính:

- `airports`
- `airlines`
- `flight_routes`
- `flight_price_snapshots`
- `flight_offer_cache`

Hiện có:

- 9 sân bay nội địa.
- 3 hãng bay seed target: Vietnam Airlines, VietJet Air, Bamboo Airways.
- 20 route phổ biến.
- 737 flight price snapshots.
- 15/20 route đang có giá vé còn hiệu lực.

Thông tin snapshot:

| Source | Rows | Từ ngày | Đến ngày | Giá thấp nhất | Giá cao nhất |
|---|---:|---|---|---:|---:|
| `serpapi_google_flights` | 737 | 2026-06-18 | 2026-07-11 | 776,720 VND | 5,604,000 VND |

Ví dụ route:

| Route | Snapshots | Giá thấp nhất |
|---|---:|---:|
| HAN -> SGN | 167 | 1,466,840 VND |
| SGN -> HAN | 113 | 1,358,840 VND |
| HAN -> DAD | 132 | 1,296,000 VND |
| DAD -> SGN | 74 | 1,242,200 VND |
| SGN -> PQC | 28 | 776,720 VND |

Cách lấy dữ liệu:

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only flights"
```

Biến môi trường cần có:

```env
FLIGHT_PRICE_PROVIDER=serpapi
SERPAPI_API_KEY=
SERPAPI_GOOGLE_DOMAIN=google.com
SERPAPI_GL=vn
SERPAPI_HL=vi
```

TTL:

- `flight_price_snapshots.expires_at`: 24 giờ.
- `flight_offer_cache.expires_at`: 15 phút.

Ghi chú:

- Amadeus đã được thiết kế sẵn nhưng hiện không dùng vì chưa tạo được account/key.
- SerpApi đang là provider thực tế đang chạy.
- Một số route chưa có snapshot do provider không trả kết quả tại thời điểm crawl.
- `booking_url` hiện đã được backfill cho 737/737 flight snapshots. Nếu provider không trả deep link cụ thể, hệ thống dùng link chính thức của hãng bay làm fallback.

### 3.3 Khách Sạn Và Giá Phòng

Bảng chính:

- `hotels`
- `hotel_images`
- `hotel_rate_snapshots`
- `hotel_offer_cache`

Hiện có:

- 223 khách sạn.
- 188 hotel rate snapshots.
- 970 ảnh khách sạn.
- Giá phòng lấy cho check-in 2026-07-11, checkout 2026-07-14.
- Mặc định adults = 2, rooms = 1.

Thông tin snapshot:

| Provider | Rows | Check-in | Checkout | Giá thấp nhất | Giá cao nhất |
|---|---:|---|---|---:|---:|
| `serpapi_google_hotels` | 188 | 2026-07-11 | 2026-07-14 | 955,800 VND | 74,641,280 VND |

Phân bổ theo destination:

| Destination | Hotels | Rate snapshots |
|---|---:|---:|
| Đà Nẵng | 23 | 20 |
| Hà Nội | 23 | 20 |
| TP.HCM | 23 | 20 |
| Hội An | 22 | 19 |
| Phú Quốc | 22 | 20 |
| Nha Trang | 22 | 20 |
| Đà Lạt | 21 | 17 |
| Huế | 21 | 19 |
| Hạ Long | 23 | 13 |
| Sapa | 23 | 20 |

Cách lấy dữ liệu:

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only hotels"
```

Biến môi trường cần có:

```env
HOTEL_PRICE_PROVIDER=serpapi
HOTEL_SEARCH_ADULTS=2
SERPAPI_API_KEY=
SERPAPI_GOOGLE_DOMAIN=google.com
SERPAPI_GL=vn
SERPAPI_HL=vi
```

TTL:

- `hotel_rate_snapshots.expires_at`: 24 giờ.
- `hotel_offer_cache.expires_at`: 30 phút.

Ghi chú:

- Booking Demand API đã để sẵn trong code nhưng chưa dùng vì cần token/approval.
- SerpApi Google Hotels đang là provider đang chạy.
- Hotel metadata seed ban đầu có 30 khách sạn; sau khi crawl SerpApi đã enrich thành 223 khách sạn.
- Một số query Google Hotels có thể trả về property gần khu vực lân cận; khi làm production nên thêm city bounds/radius để lọc chặt hơn.
- `deep_link_url` hiện đã có cho 223/223 hotels và 188/188 hotel rate snapshots.

### 3.4 Link Đặt Vé Và Đặt Phòng

Booking link cũng được xem là data vì backend/frontend cần dùng nó để đưa user sang bên bán vé/phòng.

Bảng/cột đang dùng:

- Vé máy bay: `flight_price_snapshots.booking_url`.
- Hãng bay fallback: `airlines.booking_base_url`.
- Khách sạn metadata fallback: `hotels.deep_link_url`.
- Giá phòng cụ thể: `hotel_rate_snapshots.deep_link_url`.

Hiện trạng:

| Nhóm link | Số lượng có link | Tổng số |
|---|---:|---:|
| Airlines có `booking_base_url` | 3 | 3 |
| Flight snapshots có `booking_url` | 737 | 737 |
| Hotels có `deep_link_url` | 223 | 223 |
| Hotel rate snapshots có `deep_link_url` | 188 | 188 |

Link fallback hãng bay:

| Hãng | Link |
|---|---|
| Vietnam Airlines | `https://www.vietnamairlines.com/vn/vi/home` |
| VietJet Air | `https://www.vietjetair.com/vi` |
| Bamboo Airways | `https://www.bambooairways.com/vn/vi` |

Cách bổ sung/backfill dữ liệu link:

```bash
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/04_seed_booking_links.sql
```

Luồng dùng ở FE sau này:

1. Với vé máy bay, frontend đọc `booking_url` từ endpoint `GET /travel/flights/price-calendar`.
2. Nếu `booking_url` là deep link do provider trả về thì user đi thẳng tới offer tương ứng.
3. Nếu `booking_url` là fallback của hãng bay thì user được đưa tới trang chính thức của hãng để tự hoàn tất tìm kiếm/đặt vé.
4. Với khách sạn, frontend ưu tiên `booking_url` từ rate snapshot, sau đó fallback về `hotels.deep_link_url`.

Lưu ý quan trọng:

- Không tự chế deep link có query tuyến/ngày nếu chưa chắc provider hỗ trợ.
- Fallback link chỉ đảm bảo user có nơi để đặt, không đảm bảo đã prefill ngày/tuyến/phòng.

### 3.5 Thời Tiết

Bảng chính:

- `weather_cache`
- `weather_daily_forecasts`

Hiện có:

- 10 weather cache rows.
- 100 daily forecast rows.
- Mỗi destination có 10 ngày forecast.
- Date range: 2026-06-11 đến 2026-06-20.
- Source hiện tại: `met-norway`.

Phân bổ:

| Destination | Source | Forecast days |
|---|---|---:|
| Đà Nẵng | `met-norway` | 10 |
| Hà Nội | `met-norway` | 10 |
| TP.HCM | `met-norway` | 10 |
| Hội An | `met-norway` | 10 |
| Phú Quốc | `met-norway` | 10 |
| Nha Trang | `met-norway` | 10 |
| Đà Lạt | `met-norway` | 10 |
| Huế | `met-norway` | 10 |
| Hạ Long | `met-norway` | 10 |
| Sapa | `met-norway` | 10 |

Cách lấy dữ liệu:

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only weather"
```

Logic provider:

1. Gọi Open-Meteo trước.
2. Nếu Open-Meteo lỗi SSL, timeout, 502 hoặc rate limit thì fallback sang MET Norway.
3. Lưu raw response vào `weather_cache`.
4. Parse thành forecast từng ngày trong `weather_daily_forecasts`.

TTL:

- `weather_cache.expires_at`: 6 giờ.

Ghi chú:

- Open-Meteo trên môi trường hiện tại đang lỗi kết nối.
- MET Norway fallback không cần API key, nhưng cần User-Agent rõ ràng.
- `precipitation_probability_max` có thể `null` khi dùng MET Norway vì endpoint compact không trả xác suất mưa giống Open-Meteo.
- `travel_score` được tính deterministic từ mưa, gió, nhiệt độ.

### 3.6 POI / Địa Danh Du Lịch

Bảng chính:

- `pois`
- `poi_images`

Hiện có:

- 150 POI.
- 10 destinations.
- Mỗi destination có 15 POI curated.
- `poi_images` hiện chưa có ảnh.

Phân bổ:

| Destination | POI |
|---|---:|
| Đà Nẵng | 15 |
| Hà Nội | 15 |
| TP.HCM | 15 |
| Hội An | 15 |
| Phú Quốc | 15 |
| Nha Trang | 15 |
| Đà Lạt | 15 |
| Huế | 15 |
| Hạ Long | 15 |
| Sapa | 15 |

Ví dụ Đà Nẵng:

- Cầu Rồng
- Bà Nà Hills
- Bãi biển Mỹ Khê
- Ngũ Hành Sơn
- Bán đảo Sơn Trà
- Chùa Linh Ứng Sơn Trà
- Chợ Hàn
- Cầu Tình Yêu
- Bảo tàng Điêu khắc Chăm
- Asia Park Đà Nẵng
- Đèo Hải Vân
- Đỉnh Bàn Cờ
- Bãi biển Non Nước
- Công viên APEC
- Chợ đêm Helio

Cách lấy/tạo dữ liệu:

```bash
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/03_seed_pois_curated.sql
```

Nguồn:

- Manual curated seed cho MVP.
- OpenTripMap đã để sẵn trong collector để enrich destination mới khi có `OPENTRIPMAP_KEY`.
- Không dùng AI generate POI facts.

Ghi chú:

- GPS đủ để hiển thị map/cluster MVP.
- Trước khi dùng cho navigation chính xác nên verify lại tọa độ.
- Ảnh POI và Wikidata/Wikipedia reference chưa enrich.

### 3.7 Tỷ Giá

Bảng chính:

- `exchange_rate_cache`
- `exchange_rate_history`

Hiện có:

- 330 rows trong `exchange_rate_cache`.

Cách lấy dữ liệu:

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only exchange_rate"
```

Provider:

- Frankfurter primary.
- Fallback exchange-rate provider khi cần VND và Frankfurter không trả đủ.

TTL:

- `exchange_rate_cache.expires_at`: 1 giờ.

### 3.8 Quốc Gia Và Visa MVP

Bảng chính:

- `countries`
- `country_visa_rules`

Hiện có:

- 10 countries.
- Country metadata seed/fallback cho các thị trường cơ bản.
- Visa rule MVP cho passport Việt Nam.

Cách lấy/tạo dữ liệu:

```bash
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/02_seed_data.sql
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only countries"
```

Ghi chú:

- Visa là dữ liệu high-stakes và thay đổi theo thời gian.
- Production cần gắn nguồn lãnh sự chính thức và lịch verify riêng.
- RestCountries không cung cấp visa rule; visa hiện là MVP fallback.

### 3.9 Packing Templates

Bảng chính:

- `packing_templates`
- `packing_template_items`
- `user_packing_lists`
- `user_packing_items`

Hiện có:

- 4 templates.
- 32 template items.
- 5 nhóm item: clothing, accessories, health, documents, electronics.

Nguồn:

- Rule/template deterministic trong `02_seed_data.sql`.
- Không generate bằng AI runtime.

Mục đích:

- Gợi ý checklist hành lý theo trip type, season, days, activities.
- User có thể tick/bỏ tick và thêm item riêng sau này.

## 4. API Backend Đang Đọc Dữ Liệu

Router chính: `backend/src/api/travel_data.py`

Endpoint hiện có:

| Endpoint | Mục đích |
|---|---|
| `GET /travel/destinations` | Danh sách destinations |
| `GET /travel/destinations/{slug}` | Chi tiết 1 destination |
| `GET /travel/flights/price-calendar` | Giá vé theo route và ngày |
| `GET /travel/weather/forecast` | Forecast theo destination |
| `GET /travel/price-calendar/best-days` | Kết hợp giá vé và weather score |
| `GET /travel/hotels` | Hotel metadata + rate mới nhất/exact date |
| `GET /travel/pois` | POI theo destination/category |
| `GET /travel/packing/templates` | Packing templates theo điều kiện |
| `GET /travel/exchange-rates` | Tỷ giá cache |
| `GET /travel/countries/{code}` | Metadata country |

Ví dụ test:

```bash
docker compose exec -T api python -c "import requests; print(requests.get('http://localhost:8000/travel/pois', params={'destination':'da-nang','limit':20}).json())"
docker compose exec -T api python -c "import requests; print(requests.get('http://localhost:8000/travel/weather/forecast', params={'destination':'da-nang','days':5}).json())"
```

## 5. Cách Khởi Tạo Lại Database Từ Đầu

Cần chú ý: lệnh `01_schema.sql` sẽ drop schema hiện tại. Chỉ chạy khi muốn reset DB dev.

```bash
docker compose up -d postgres

docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/01_schema.sql
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/02_seed_data.sql
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/03_seed_pois_curated.sql
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/04_seed_booking_links.sql
```

Sau đó nạp dữ liệu API:

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only flights"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only hotels"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only weather"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only exchange_rate"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only countries"
```

Kiểm tra summary:

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --summary"
```

## 6. Biến Môi Trường Cần Có

Không commit API key thật vào repo.

```env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=travel_buddy
DB_USER=postgres
DB_PASS=

SERPAPI_API_KEY=
SERPAPI_GOOGLE_DOMAIN=google.com
SERPAPI_GL=vn
SERPAPI_HL=vi

FLIGHT_PRICE_PROVIDER=serpapi
HOTEL_PRICE_PROVIDER=serpapi
HOTEL_SEARCH_ADULTS=2

AMADEUS_API_KEY=
AMADEUS_API_SECRET=
AMADEUS_ENV=test

OPENTRIPMAP_KEY=
OPENTRIPMAP_LANG=vi
```

## 7. Cron/Refresh Đề Xuất

| Job | Lệnh | Tần suất | Lý do |
|---|---|---|---|
| Flight prices | `pipeline.py --only flights` | 24 giờ | Giá vé thay đổi nhanh, snapshot TTL 24 giờ |
| Hotel prices | `pipeline.py --only hotels` | 24 giờ | Giá phòng thay đổi theo ngày, TTL 24 giờ |
| Weather | `pipeline.py --only weather` | 6 giờ | Weather cache TTL 6 giờ |
| Exchange rates | `pipeline.py --only exchange_rate` | 1 giờ | Tỷ giá cache TTL 1 giờ |
| Countries | `pipeline.py --only countries` | 7-30 ngày | Metadata quốc gia ít thay đổi |
| OpenTripMap POI enrich | `pipeline.py --only opentripmap` | Theo nhu cầu / weekly | Chỉ cần khi thêm destination mới hoặc enrich POI |

## 8. Những Phần Còn Thiếu Hoặc Nên Làm Tiếp

1. POI images chưa có.
   - `poi_images`: 0 rows.
   - Nên enrich bằng Wikimedia Commons hoặc OpenTripMap images khi có key.

2. Destination images chưa có.
   - `destination_images`: 0 rows.
   - Nên seed Wikimedia Commons URL để tránh rate limit Unsplash.

3. Wikidata/Wikipedia reference cho POI chưa có.
   - `wikidata_id`, `wikipedia_url` đang null cho POI curated.
   - Nên enrich để tăng độ tin cậy và attribution.

4. Open-Meteo đang lỗi kết nối từ môi trường hiện tại.
   - Đã có MET Norway fallback nên weather không còn bị trống.
   - Nếu muốn dùng Open-Meteo primary ổn định, cần kiểm tra DNS, proxy, firewall, VPN hoặc network của máy.

5. Flight route coverage chưa đủ 20/20.
   - 15/20 route có giá còn hiệu lực.
   - Các route chưa có giá nên được retry theo ngày khác hoặc provider khác.

6. Hotel provider cần tighten location filter.
   - Google Hotels có thể trả về property lân cận.
   - Nên thêm city bounds/radius hoặc lọc theo khoảng cách tới destination center.

7. Visa rules mới ở mức MVP.
   - Production cần dùng nguồn lãnh sự/chính phủ và có lịch verify riêng.

## 9. Kết Luận

Phần data backend hiện đã đủ để bắt đầu xây frontend MVP:

- Có destination, hotel, flight, weather, POI, packing, exchange rate, country data.
- Giá vé và giá phòng là snapshot lấy từ provider, không phải mock.
- Weather đã có fallback provider nên không phụ thuộc duy nhất vào Open-Meteo.
- POI đã đủ cho flow user chọn điểm đến và tick địa danh vào note/trip builder.

Cần ưu tiên tiếp theo:

1. Xây FE đọc các endpoint `/travel/*`.
2. Bổ sung ảnh destination/POI.
3. Thêm scheduler cron thật cho pipeline.
4. Thêm UI/logic cho user tick POI vào trip note/itinerary.
