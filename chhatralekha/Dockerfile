# ChhatraLekha - APAAR ID Student Data Management & Verification Platform
#
# Two stages:
#   1. build the React frontend with Vite;
#   2. install the Python dependencies into a virtual environment.
# The runtime stage carries the API and the built frontend together, so the
# whole platform ships as one image.

# --------------------------------------------------------------- frontend
FROM node:22-alpine AS frontend

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


# --------------------------------------------------------------- backend
FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY chhatralekha/requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt


# --------------------------------------------------------------- runtime
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=dev \
    MONGODB_URL=mongodb://mongodb:27017 \
    MONGODB_DATABASE=edusync

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 chhatralekha

COPY --from=backend /opt/venv /opt/venv

WORKDIR /app
COPY --chown=chhatralekha:chhatralekha chhatralekha/app ./app
COPY --from=frontend --chown=chhatralekha:chhatralekha /build/dist /app/frontend/dist

USER chhatralekha
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
