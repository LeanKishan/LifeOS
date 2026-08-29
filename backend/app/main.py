from __future__ import annotations

import asyncio
import contextlib
import logging
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import jwt
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app import __version__
from app.api.routes import (
    analytics,
    auth,
    calendar,
    coach,
    finance,
    health,
    job_tracker,
    learning,
    projects,
    ws,
)
from app.core.cache import bump_cache_version
from app.core.config import get_settings
from app.core.observability import (
    HTTP_LATENCY,
    HTTP_REQUESTS,
    RequestIDMiddleware,
    configure_logging,
    get_request_id,
    init_sentry,
    render_metrics,
)
from app.core.ratelimit import over_limit_retry_after
from app.core.redis import get_redis
from app.core.security import decode_token
from app.realtime.fanout import run_fanout
from app.realtime.manager import manager, publish

settings = get_settings()
# Leave pytest's own log capture in place when running under it.
if "pytest" not in sys.modules:
    configure_logging(json_logs=settings.log_json, level=settings.log_level)
init_sentry(
    settings.sentry_dsn,
    environment=settings.environment,
    traces_sample_rate=settings.sentry_traces_sample_rate,
)
logger = logging.getLogger("lifeos")

# Path prefix -> live-update channel (matches the frontend's top-level query key).
LIVE_CHANNELS = {
    "/api/job-tracker": "job-tracker",
    "/api/projects": "projects",
    "/api/calendar": "calendar",
    "/api/finance": "finance",
    "/api/learning": "learning",
}
_MUTATING = {"POST", "PUT", "PATCH", "DELETE"}

# Static response headers applied to every response. The API only ever returns
# JSON, so the page-embedding / sniffing vectors can be shut off completely.
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
}
# Swagger UI / ReDoc need inline scripts+styles and a CDN; everything else gets
# a deny-all CSP. These paths don't exist in production (docs are disabled).
_DOCS_PATHS = {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}
_DOCS_CSP = (
    "default-src 'self'; img-src 'self' data:; worker-src 'self' blob:; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net"
)
_API_CSP = "default-src 'none'; frame-ancestors 'none'"
# When the API also serves the SPA, its HTML/asset responses need a real CSP:
# self scripts, inline styles (React style props), and the Google Fonts hosts.
_SPA_CSP = (
    "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
    "img-src 'self' data: blob:; font-src 'self' https://fonts.gstatic.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "script-src 'self'; connect-src 'self'"
)


def _route_label(request: Request) -> str:
    """Low-cardinality metrics label: the matched route *template*, not the URL."""
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else "__unmatched__"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    manager.loop = asyncio.get_running_loop()

    fanout_task: asyncio.Task[None] | None = None
    if settings.ws_fanout_enabled and not settings.redis_url.startswith("fakeredis"):
        fanout_task = asyncio.create_task(run_fanout(manager))

    try:
        yield
    finally:
        if fanout_task is not None:
            fanout_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await fanout_task


def create_app() -> FastAPI:
    docs_enabled = not settings.is_production
    app = FastAPI(
        title="LifeOS API",
        version=__version__,
        description="All-in-one personal management platform.",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        # Log the traceback server-side; never leak it to the client.
        logger.exception("Unhandled error: %s %s", request.method, request.url.path)
        return JSONResponse(
            {"detail": "Internal server error", "request_id": get_request_id()},
            status_code=500,
        )

    @app.middleware("http")
    async def on_mutation(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        if request.method not in _MUTATING or response.status_code >= 300:
            return response
        channel = next(
            (n for p, n in LIVE_CHANNELS.items() if request.url.path.startswith(p)),
            None,
        )
        auth_header = request.headers.get("authorization", "")
        if channel and auth_header.startswith("Bearer "):
            with contextlib.suppress(jwt.PyJWTError, KeyError, ValueError):
                user_id = int(decode_token(auth_header[7:], "access")["sub"])
                bump_cache_version(get_redis(), channel, user_id)
                publish(user_id, {"type": channel})
        return response

    @app.middleware("http")
    async def global_rate_limit(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # A coarse per-IP ceiling on writes, on top of the tight per-endpoint
        # limits on auth. Reads are untouched.
        if request.method in _MUTATING:
            client_host = request.client.host if request.client else "unknown"
            retry_after = over_limit_retry_after(
                f"global-mutations:{client_host}",
                settings.global_rate_limit_per_minute,
                60,
            )
            if retry_after:
                return JSONResponse(
                    {"detail": "Too many requests. Try again shortly."},
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={"Retry-After": str(retry_after)},
                )
        return await call_next(request)

    @app.middleware("http")
    async def limit_body_size(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        declared = request.headers.get("content-length")
        if declared is not None:
            with contextlib.suppress(ValueError):
                if int(declared) > settings.max_body_bytes:
                    return JSONResponse(
                        {"detail": "Request body too large"},
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    )
        return await call_next(request)

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        if request.url.path in _DOCS_PATHS:
            csp = _DOCS_CSP
        elif "text/html" in response.headers.get("content-type", ""):
            csp = _SPA_CSP
        else:
            csp = _API_CSP
        response.headers.setdefault("Content-Security-Policy", csp)
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response

    @app.middleware("http")
    async def observe_requests(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - started

        if request.url.path != "/metrics":
            label = _route_label(request)
            method = request.method
            HTTP_REQUESTS.labels(method, label, str(response.status_code)).inc()
            HTTP_LATENCY.labels(method, label).observe(elapsed)
            logger.info(
                "request",
                extra={
                    "method": method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round(elapsed * 1000, 1),
                    "client_ip": request.client.host if request.client else None,
                },
            )
        return response

    # CORS wraps the rest so short-circuited 413/429 responses keep CORS headers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    # Outermost: same context as the error handler, so a 500 can still name the
    # request; also echoes X-Request-ID on every non-error response.
    app.add_middleware(RequestIDMiddleware)

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(job_tracker.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(calendar.router, prefix="/api")
    app.include_router(finance.router, prefix="/api")
    app.include_router(learning.router, prefix="/api")
    app.include_router(coach.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    app.include_router(ws.router, prefix="/api")

    static_root = Path(settings.static_dir) if settings.static_dir else None
    serving_spa = static_root is not None and (static_root / "index.html").is_file()

    if not serving_spa:

        @app.get("/", tags=["meta"])
        def root() -> dict[str, str]:
            return {
                "name": "LifeOS API",
                "version": __version__,
                "docs": "/docs" if docs_enabled else "disabled",
            }

    if settings.metrics_enabled:

        @app.get("/metrics", include_in_schema=False)
        def metrics() -> Response:
            body, content_type = render_metrics()
            return PlainTextResponse(body, media_type=content_type)

    if serving_spa and static_root is not None:
        base = static_root.resolve()
        assets = base / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=assets), name="spa-assets")

        @app.get("/{spa_path:path}", include_in_schema=False)
        async def spa(spa_path: str) -> FileResponse:
            """Serve a real file if it exists, otherwise the SPA shell so the
            client router can take over. Registered last, so every `/api/*`
            route still wins."""
            candidate = (base / spa_path).resolve()
            if base in candidate.parents and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(base / "index.html")

    return app


app = create_app()
