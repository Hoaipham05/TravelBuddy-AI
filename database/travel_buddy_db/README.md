# Travel Buddy — Hướng dẫn cài đặt Database

## Cấu trúc file

```
travel_buddy_db/
├── 01_schema.sql      # Tạo 11 bảng + indexes
├── 02_seed_data.sql   # Insert data thực (10 điểm đến, 15+ khách sạn, 8 chuyến bay)
├── 03_crawl_data.py   # Script crawl data thực từ web
├── .env.example       # Mẫu file cấu hình
└── README.md
```

---

## Bước 1 — Cài PostgreSQL và tạo database

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Tạo database
psql -U postgres
CREATE DATABASE travel_buddy;
\q
```

---

## Bước 2 — Chạy schema và seed data

```bash
# Tạo bảng
psql -U postgres -d travel_buddy -f 01_schema.sql

# Insert data mẫu thực tế
psql -U postgres -d travel_buddy -f 02_seed_data.sql
```

Sau bước này sẽ có sẵn:
- 10 điểm đến (Đà Nẵng, Hội An, Hạ Long, Đà Lạt, Phú Quốc, Sapa, Nha Trang, Bangkok, Tokyo, Singapore)
- 12 khách sạn thực tế với giá cụ thể
- 8 chuyến bay với giá tham khảo theo tháng
- 3 user mẫu + 1 chuyến đi mẫu 5N4Đ Đà Nẵng

---

## Bước 3 — Crawl data thực từ web (tùy chọn)

```bash
# Cài thư viện
pip install requests beautifulsoup4 psycopg2-binary python-dotenv

# Tạo file .env
cp .env.example .env
# Điền thông tin DB vào .env

# Chạy crawler
python 03_crawl_data.py
```

### Lấy Amadeus API key (miễn phí, khuyên dùng)

1. Đăng ký tại https://developers.amadeus.com
2. Tạo app mới → chọn "Self-Service APIs"
3. Copy `API Key` và `API Secret` vào `.env`
4. Môi trường test: 100 request/ngày, không cần thẻ

```env
AMADEUS_API_KEY=your_key_here
AMADEUS_API_SECRET=your_secret_here
```

---

## Bước 4 — Kết nối với FastAPI

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# main.py — ví dụ API tìm kiếm điểm đến
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db

app = FastAPI()

@app.get("/destinations/search")
def search_destinations(q: str, db: Session = Depends(get_db)):
    results = db.execute("""
        SELECT id, name, city, avg_rating, tags
        FROM destinations
        WHERE to_tsvector('simple', unaccent(name || ' ' || city))
              @@ plainto_tsquery('simple', unaccent(:q))
        ORDER BY avg_rating DESC
        LIMIT 10
    """, {"q": q}).fetchall()
    return [dict(r) for r in results]

@app.get("/flights/cheap")
def get_cheap_flights(origin: str, dest: str, db: Session = Depends(get_db)):
    results = db.execute("""
        SELECT airline, flight_no, price, depart_at, monthly_prices
        FROM flights
        WHERE origin = :origin AND destination = :dest
        ORDER BY price ASC
        LIMIT 5
    """, {"origin": origin, "dest": dest}).fetchall()
    return [dict(r) for r in results]
```

---

## Câu trả lời cho giáo viên

Khi giáo viên hỏi "data lấy từ đâu?", trả lời:

> Hệ thống dùng 3 nguồn dữ liệu kết hợp:
> 1. **Database tĩnh (PostgreSQL)**: Dữ liệu điểm đến, khách sạn, chuyến bay được thu thập thủ công và qua script crawl từ các trang du lịch thực tế (Agoda, VietJet) rồi lưu vào PostgreSQL.
> 2. **Amadeus API**: Tích hợp API chính thức (miễn phí) của Amadeus để lấy giá vé máy bay realtime.
> 3. **AI Search**: Trợ lý AI dùng web search để bổ sung thông tin mới nhất khi cần.
