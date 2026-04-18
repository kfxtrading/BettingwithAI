FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --upgrade pip && pip install -e ".[api]"

COPY scripts/ ./scripts/
COPY models/ ./models/
COPY data/ ./data_seed/

RUN mkdir -p /app/data/raw \
             /app/data/sofascore \
             /app/data/snapshots \
             /app/data/predictions \
             /app/data/processed \
             /app/data/monitoring

EXPOSE 8000

CMD ["sh", "-c", "uvicorn football_betting.api.app:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
