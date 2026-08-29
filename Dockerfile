# syntax=docker/dockerfile:1
# One self-contained image: the FastAPI backend also serves the built React SPA.
# Used for the single-service Render / Fly / "one URL" deployment. The split
# frontend + backend images live in frontend/Dockerfile and backend/Dockerfile.

# ── build the SPA ───────────────────────────────────────────────────────────
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# No VITE_API_URL: the app calls a same-origin /api, which this image serves.
RUN npm run build

# ── python base ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

FROM base AS deps
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ── runtime ────────────────────────────────────────────────────────────────
FROM base AS runtime
ENV ENVIRONMENT=production \
    CELERY_EAGER=false \
    WEB_CONCURRENCY=1 \
    FORWARDED_ALLOW_IPS="*" \
    LOG_JSON=true \
    STATIC_DIR=/app/static
COPY --from=deps /app/.venv /app/.venv
COPY backend/ ./
COPY --from=web /web/dist /app/static
RUN useradd --system --uid 1001 --home-dir /app appuser \
 && chmod +x /app/docker/entrypoint.sh \
 && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["web"]
