# TravelBuddy AI - Data Pipeline

Pipeline này ghi vào schema canonical tại `database/travel_buddy_db/01_schema.sql`.

## Collectors

| Collector | Lệnh | Ghi vào bảng | Key |
|---|---|---|---|
| Weather | `python pipeline.py --only weather` | `weather_cache`, `weather_daily_forecasts` | Không cần key |
| Exchange rate | `python pipeline.py --only exchange_rate` | `exchange_rate_cache`, `exchange_rate_history` | Không cần key |
| Countries | `python pipeline.py --only countries` | `countries`, `country_visa_rules` | Optional `RESTCOUNTRIES_API_KEY` |
| POI | `python pipeline.py --only opentripmap` | `pois`, `poi_images`, bổ sung `hotels` metadata | `OPENTRIPMAP_KEY` |
| Hotels | `python pipeline.py --only hotels` | `hotels`, `hotel_images`, `hotel_rate_snapshots`, `hotel_offer_cache` | `SERPAPI_API_KEY` hoặc Booking partner credentials |
| Flights | `python pipeline.py --only flights` | `flight_price_snapshots`, `flight_offer_cache` | `SERPAPI_API_KEY` hoặc Amadeus credentials |

## Chạy Trong Docker

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --summary"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only flights"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only hotels"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only weather"
```

## Chạy Local

```bash
cd backend/src/api/travel_api
cp .env.example .env
python pipeline.py --summary
python pipeline.py --only weather
```

## Nguyên Tắc Dữ Liệu

- Không seed giá vé/giá phòng mock.
- Giá vé/phòng luôn là snapshot có `source`, `fetched_at`, `expires_at`.
- Weather cache TTL 6 giờ.
- Exchange rate cache TTL 1 giờ.
- Flight snapshot TTL 24 giờ, realtime offer cache TTL 15 phút.
- Hotel snapshot TTL 24 giờ, realtime offer cache TTL 30 phút.
- POI tách khỏi `destinations` để Trip Builder cluster theo GPS.
- Booking link là data: flight dùng `booking_url`, hotel dùng `deep_link_url`; nếu provider không trả deep link cụ thể thì dùng fallback chính thức.

## Evidence

Raw response từ provider được lưu trong thư mục `evidence/` khi collector chạy để làm minh chứng nguồn dữ liệu. Thư mục này là artifact runtime và không nên commit nếu chứa dữ liệu lớn hoặc nhạy cảm.

Log pipeline mặc định ghi vào `pipeline.log` trong working directory. Có thể đổi bằng biến `TRAVELBUDDY_PIPELINE_LOG`.
