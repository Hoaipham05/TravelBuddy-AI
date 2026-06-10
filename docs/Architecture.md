# Architecture

TravelBuddy AI is organized as a small monorepo:

- `frontend/`: React/Vite chat UI.
- `backend/`: FastAPI API, LangGraph agent, Redis queue workers, tools, and guardrails.
- `docker/`: runtime infrastructure configuration.
- `database/`: future database migrations and seed data.
- `tests/`: shared test layout.

Production flow:

```text
Browser -> Nginx :8890 -> React static files
Browser -> Nginx /api -> FastAPI
FastAPI -> Redis Streams -> Worker
Worker -> LangGraph Agent -> Tools/Search/LLM
Worker -> Redis Result Store -> FastAPI/SSE response
```
