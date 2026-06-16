# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_RETRIES=5

# gcc + libxml2/libxslt: required by readability-lxml
# curl: used by HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel \
    && pip install --prefer-binary -r requirements.txt

COPY . .

HEALTHCHECK --interval=15s --timeout=5s --start-period=25s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

# Default: API server (docker-compose overrides CMD for worker replicas)
CMD ["uvicorn", "src.api.server:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]
