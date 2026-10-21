# EduSynC - APAAR ID Student Data Management & Verification Platform
#
# Build stage: install the dependencies into a virtual environment.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install "sqlalchemy[asyncio]" greenlet \
    && /opt/venv/bin/pip install -r requirements.txt


# Runtime stage: a slim image with only the application and the venv.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=dev \
    DATABASE_URL=sqlite+aiosqlite:////data/edusync.db

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 edusync \
    && mkdir -p /data \
    && chown edusync:edusync /data

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=edusync:edusync app ./app
COPY --chown=edusync:edusync alembic.ini ./
COPY --chown=edusync:edusync alembic ./alembic

USER edusync
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
