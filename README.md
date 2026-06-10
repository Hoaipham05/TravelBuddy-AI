# TravelBuddy AI

TravelBuddy AI is an AI travel assistant built with a React/Vite frontend, a FastAPI/LangGraph backend, Redis Streams workers, SearXNG search, and Nginx as the production entry point.

## Project Structure

```text
TravelBuddy_AI/
├── frontend/                  # React Vite user interface
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   │   └── TravelBuddyApp.jsx
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
│
├── backend/                   # FastAPI backend, agent, tools, queue workers
│   ├── src/
│   │   ├── agent/             # LangGraph agent and LLM factory
│   │   ├── api/               # FastAPI routes/endpoints
│   │   ├── cache/             # Redis session/result/cache helpers
│   │   ├── queue/             # Redis Streams producer/consumer
│   │   ├── security/          # Guardrails
│   │   ├── tools/             # Travel, web search, image search tools
│   │   ├── config.py
│   │   ├── database.py        # Mock travel data
│   │   └── database_additions.py
│   ├── agent_cli.py           # Local CLI chat without API/queue
│   ├── Dockerfile
│   ├── requirements.txt
│   └── system_prompt.txt
│
├── docker/
│   ├── nginx/nginx.conf
│   └── searxng/settings.yml
│
├── database/                  # DB docs/migrations placeholder
│   ├── migrations/
│   ├── seeds/
│   └── README.md
│
├── docs/
│   ├── API.md
│   └── Architecture.md
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── CI-CD/
│   ├── github-actions/
│   └── deployment/
│
├── .env.example
├── docker-compose.yml
└── README.md
```

## Run With Docker Compose

```bash
cp .env.example .env
docker-compose up -d --build
```

Open the app at `http://localhost:8890`.

## Local Development

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

CLI agent test:

```bash
cd backend
python agent_cli.py
```

## Notes

- Root `.env` is still used by `docker-compose.yml`.
- The backend package is intentionally still named `src` inside `backend/` so existing imports such as `src.api.server` keep working.
- Real database migrations can be added under `database/migrations`; current demo data lives in `backend/src/database.py`.
