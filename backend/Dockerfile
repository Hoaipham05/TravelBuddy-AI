FROM python:3.11-slim

WORKDIR /app

# System deps (readability-lxml cần lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: API server (override trong docker-compose)
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
