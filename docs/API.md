# API

Main FastAPI app: `backend/src/api/server.py`.

Key endpoints:

- `GET /health`
- `POST /chat`
- `GET /chat/{job_id}`
- `GET /session/{session_id}/stream`
- `DELETE /session/{session_id}`
- `POST /vision/identify`

When running through Docker Compose, Nginx exposes the API under `/api/*` at `http://localhost:8890`.
