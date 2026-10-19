# syntax=docker/dockerfile:1.7
# DOCUPRO production image: FastAPI conversion service + prebuilt web client.
# Build:  docker build -t docupro:1.0.0 .
# Run:    docker run --rm -p 8000:8000 --env-file .env docupro:1.0.0

# ---------- stage 1: build the web client ----------
FROM node:22-alpine AS web
WORKDIR /build

# Install dependencies from the lockfile only, so the layer is cached.
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY apps/web/ ./
# Empty by default: the browser talks to the same origin that serves the app.
ARG VITE_API_BASE=""
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

# ---------- stage 2: runtime ----------
FROM python:3.11-slim AS runtime

# INSTALL_OFFICE=1 adds LibreOffice, which is required for PPTX -> PDF and used
# as the high-fidelity path for DOCX -> PDF. Set it to 0 for a small image.
ARG INSTALL_OFFICE=1
ARG TESSERACT_LANGS="eng fra spa deu por ara"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DOCUPRO_DATA_DIR=/data \
    DOCUPRO_WEB_DIR=/app/web \
    DOCUPRO_LOG_LEVEL=INFO \
    PORT=8000

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        ca-certificates curl \
        tesseract-ocr \
        fonts-dejavu-core fonts-noto-core fontconfig; \
    for lang in ${TESSERACT_LANGS}; do \
        apt-get install -y --no-install-recommends "tesseract-ocr-${lang}" || true; \
    done; \
    if [ "${INSTALL_OFFICE}" = "1" ]; then \
        apt-get install -y --no-install-recommends \
            libreoffice-writer libreoffice-calc libreoffice-impress; \
    fi; \
    rm -rf /var/lib/apt/lists/*; \
    fc-cache -f >/dev/null

WORKDIR /app
COPY services/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/api/docupro_api ./docupro_api
COPY services/api/pytest.ini ./pytest.ini
COPY --from=web /build/dist ./web

# Unprivileged runtime user; /data holds the per-job working directories.
RUN groupadd --gid 10001 docupro \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin docupro \
    && mkdir -p /data \
    && chown -R docupro:docupro /data /app
USER docupro

EXPOSE 8000
VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/api/health" || exit 1

# One process: the job registry lives in memory, so scaling out requires a
# shared store. Concurrency is provided by the in-process worker pool
# (DOCUPRO_MAX_CONCURRENCY) and can be scaled with CPU/memory limits.
CMD ["sh", "-c", "exec uvicorn docupro_api.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --proxy-headers --forwarded-allow-ips='*' --no-server-header"]
