# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=120 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PROGRESS_BAR=off \
    PIP_RETRIES=10

# System deps for readability-lxml/lxml.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel \
    && pip install --prefer-binary --retries 10 --timeout 120 -r requirements.txt

COPY . .

# Default: API server; docker-compose overrides this for workers.
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
