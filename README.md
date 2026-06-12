# TravelBuddy AI

TravelBuddy AI là nền tảng du lịch thông minh theo hướng: người dùng tự thao tác, AI hỗ trợ khi cần. Dự án hiện có backend FastAPI/LangGraph, PostgreSQL data layer, Redis workers, Docker Compose, cấu trúc frontend React/Vite sẵn để phát triển tiếp.

## Trạng Thái Hiện Tại

- PostgreSQL thật đang được dùng qua Docker.
- Data layer đã có: điểm đến, tuyến bay, giá vé, khách sạn, giá phòng, thời tiết, POI, tỷ giá, quốc gia, packing templates.
- Backend đã có router `/travel/*` để frontend đọc dữ liệu.
- Frontend vẫn giữ cấu trúc React/Vite để làm tiếp, chưa phải trọng tâm ở giai đoạn data.
- Agent/backend tools vẫn được giữ để phát triển các tính năng AI sau.

## Cấu Trúc Thư Mục

```text
TravelBuddy_AI/
├── backend/                       # FastAPI, LangGraph agent, tools, workers, data pipeline
│   ├── src/
│   │   ├── agent/                 # LangGraph agent
│   │   ├── api/                   # FastAPI server, travel data router, data collectors
│   │   ├── cache/                 # Redis cache/session helpers
│   │   ├── queue/                 # Redis Streams worker logic
│   │   ├── security/              # Guardrails
│   │   └── tools/                 # Travel/search/image tools
│   ├── tests/                     # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                      # React/Vite app, giữ sẵn để xây UI
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── Dockerfile
│   └── package.json
│
├── database/                      # PostgreSQL schema, seed, data setup
│   ├── travel_buddy_db/           # Schema canonical và seed đang dùng
│   ├── migrations/                # Placeholder cho migration thật sau này
│   └── seeds/                     # Placeholder cho seed chia nhỏ sau này
│
├── docs/                          # Tài liệu dự án, chia theo nhóm
│   ├── api/
│   ├── architecture/
│   ├── data/
│   ├── development/
│   └── product/
│
├── docker/                        # Cấu hình hạ tầng container
│   ├── nginx/
│   └── searxng/
│
├── scripts/                       # Script tiện ích chạy từ root project
├── tests/                         # Test cấp hệ thống/e2e/integration
├── CI-CD/                         # Placeholder CI/CD và deployment
├── runtime/                       # Artifact local: logs, file sinh ra khi chạy
├── docker-compose.yml
├── .env.example
└── README.md
```

## Chạy Bằng Docker

```bash
cp .env.example .env
docker compose up -d --build
```

Kiểm tra service:

```bash
docker compose ps
```

## Database Và Seed

Schema/data chính nằm tại:

- [database/travel_buddy_db](./database/travel_buddy_db)

Reset database dev từ đầu:

```bash
docker compose up -d postgres
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/01_schema.sql
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/02_seed_data.sql
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/03_seed_pois_curated.sql
docker compose exec -T postgres psql -U postgres -d travel_buddy -f /travel_buddy_db/04_seed_booking_links.sql
```

Chạy data pipeline:

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --summary"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only flights"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only hotels"
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --only weather"
```

## Tài Liệu Nên Đọc

- Báo cáo dữ liệu: [docs/data/DATA_REPORT.md](./docs/data/DATA_REPORT.md)
- Kiến trúc hệ thống: [docs/architecture/ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md)
- API: [docs/api/API.md](./docs/api/API.md)
- Đặc tả tính năng: [docs/product/FEATURE_SPECIFICATION.md](./docs/product/FEATURE_SPECIFICATION.md)
- Quy trình phát triển: [docs/development/QUY_TRINH_PHAT_TRIEN.md](./docs/development/QUY_TRINH_PHAT_TRIEN.md)
- TODO kỹ thuật: [docs/development/TODO.md](./docs/development/TODO.md)

## Quy Ước

- Tài liệu và nội dung người dùng nhìn thấy dùng tiếng Việt có dấu.
- Không commit `.env` hoặc API key thật.
- Không seed giá vé/giá phòng mock cho production flow.
- Dữ liệu biến động phải có `source`, `fetched_at`, `expires_at`.
- Frontend, Agent, CI/CD placeholder được giữ lại để phát triển trong các phase sau.
