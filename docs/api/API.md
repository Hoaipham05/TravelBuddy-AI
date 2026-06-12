# API

Main FastAPI app: `backend/src/api/server.py`.

Key endpoints:

- `GET /health`
- `POST /auth/login`
- `GET /auth/me`
- `POST /chat`
- `GET /chat/{job_id}`
- `GET /session/{session_id}/stream`
- `DELETE /session/{session_id}`
- `POST /vision/identify`

Structured travel data endpoints:

- `GET /travel/destinations`
- `GET /travel/destinations/{slug}`
- `GET /travel/flights/price-calendar`
- `GET /travel/weather/forecast`
- `GET /travel/price-calendar/best-days`
- `GET /travel/hotels`
- `GET /travel/pois`
- `GET /travel/packing/templates`
- `GET /travel/exchange-rates`
- `GET /travel/countries/{code}`

When running through Docker Compose, Nginx exposes the API under `/api/*` at `http://localhost:8890`.
