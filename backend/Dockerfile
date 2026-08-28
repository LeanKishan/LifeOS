# syntax=docker/dockerfile:1

# ── base: interpreter + uv, shared by every stage ───────────────────────────
FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# ── deps: runtime-only dependency layer, cached until the lockfile changes ───
FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ── dev: full toolchain + live reload; compose bind-mounts the source over it ─
FROM base AS dev
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── prod: slim runtime, no build tools, non-root, gunicorn ──────────────────
FROM base AS prod
# The image *is* production: the M12 config guard then refuses to boot without a
# real DATABASE_URL / REDIS_URL / JWT_SECRET.
ENV ENVIRONMENT=production \
    CELERY_EAGER=false \
    WEB_CONCURRENCY=2 \
    FORWARDED_ALLOW_IPS="*"
COPY --from=deps /app/.venv /app/.venv
COPY . .
RUN useradd --system --uid 1001 --home-dir /app appuser \
 && chmod +x /app/docker/entrypoint.sh \
 && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
# entrypoint dispatches: serve (default) | migrate | worker | beat
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["serve"]
