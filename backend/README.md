# Backend

Backend của TravelBuddy AI gồm FastAPI server, LangGraph agent, data pipeline, tools và Redis workers.

## Cấu Trúc

```text
backend/
├── src/
│   ├── agent/          # LangGraph agent
│   ├── api/            # FastAPI server, travel data router, data collectors
│   ├── cache/          # Redis cache/session helpers
│   ├── queue/          # Redis Streams workers
│   ├── security/       # Guardrails
│   └── tools/          # Travel/search/image tools
├── tests/              # Backend tests
├── agent_cli.py        # CLI test agent local
├── Dockerfile
└── requirements.txt
```

## Chạy API Local

```bash
cd backend
pip install -r requirements.txt
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

## Chạy Data Pipeline Trong Docker

```bash
docker compose exec -T api sh -lc "cd /app/src/api/travel_api && python pipeline.py --summary"
```

## Ghi Chú

- Package backend vẫn tên là `src` để giữ import hiện tại như `src.api.server`.
- Data API chính cho TravelBuddy nằm ở `src/api/travel_data.py`.
- Data collectors nằm ở `src/api/travel_api/collectors`.
