# TravelBuddy AI - Database

Database này theo kiến trúc hybrid:

- Flight routes seed sẵn, giá vé thật được ghi vào `flight_price_snapshots` qua collector.
- Hotels có metadata seed, giá phòng thật được ghi vào `hotel_rate_snapshots` qua collector.
- Weather dùng Open-Meteo primary, MET Norway fallback, cache vào `weather_cache` / `weather_daily_forecasts`.
- POI lưu riêng trong `pois`, có tọa độ GPS để Trip Builder cluster và cho user tick vào note.
- Packing template là rule/template deterministic, không AI generate runtime.
- Exchange rate cache theo provider, TTL ngắn.
- Country metadata lưu trong `countries`, visa MVP trong `country_visa_rules`.

## Files

```text
01_schema.sql               # Canonical PostgreSQL schema
02_seed_data.sql            # Seed nền: destinations, airports, routes, hotels metadata, POI tối thiểu, packing
03_seed_pois_curated.sql    # Seed bổ sung 150 POI curated cho 10 điểm đến nội địa
04_seed_booking_links.sql   # Chuẩn hóa/backfill link đặt vé, đặt phòng
.env.example                # Biến môi trường cho DB và API keys
```

## Chạy Local Bằng Docker

PostgreSQL được mount folder này vào container tại `/travel_buddy_db`.

```bash
docker compose up -d postgres
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/01_schema.sql
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/02_seed_data.sql
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/03_seed_pois_curated.sql
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/04_seed_booking_links.sql
```

Lưu ý: `01_schema.sql` sẽ drop và tạo lại schema. Không chạy lại file này trên DB đang có flight/hotel snapshots nếu muốn giữ dữ liệu đã crawl.

## Dữ Liệu Seed Hiện Có

Sau `02_seed_data.sql` + `03_seed_pois_curated.sql`:

- 10 domestic destinations.
- 9 domestic airports.
- 3 airlines.
- 20 popular domestic flight routes.
- 30 hotel metadata seed, không có giá phòng mock.
- 150 curated POI, mỗi destination có 15 POI.
- Link đặt vé fallback cho 3 hãng bay chính.
- Link đặt phòng fallback/provider cho hotels.
- Country fallback, visa MVP, packing templates.

Giá vé và giá phòng không nằm trong seed static. Chúng được nạp bằng pipeline thật vào snapshot tables.

## Data Pipeline

Từ thư mục `backend/src/api/travel_api`:

```bash
python pipeline.py --summary
python pipeline.py --only flights
python pipeline.py --only hotels
python pipeline.py --only weather
python pipeline.py --only exchange_rate
python pipeline.py --only countries
python pipeline.py --only opentripmap
```

Trong Docker:

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only flights"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only hotels"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only weather"
```

## API Keys

```env
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

Không cần key:

- Open-Meteo forecast.
- MET Norway Locationforecast fallback.
- Frankfurter / exchange-rate fallback.

## Lưu Ý Quan Trọng

- Không seed giá vé/giá phòng mock vào production flow.
- POI curated là baseline cho MVP. Khi có `OPENTRIPMAP_KEY`, có thể refresh/enrich POI cho destination mới.
- Các giá trị GPS trong seed đủ để cluster và hiển thị bản đồ MVP, nhưng nên verify lại tọa độ trước khi dùng cho navigation chính xác.
