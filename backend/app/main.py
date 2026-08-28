from __future__ import annotations

import contextlib

import jwt
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app import __version__
from app.api.routes import (
    auth,
    calendar,
    finance,
    health,
    job_tracker,
    learning,
    projects,
    ws,
)
from app.core.config import get_settings
from app.core.security import decode_token
from app.realtime.manager import publish

settings = get_settings()

# Path prefix -> live-update channel (matches the frontend's top-level query key).
LIVE_CHANNELS = {
    "/api/job-tracker": "job-tracker",
    "/api/projects": "projects",
    "/api/calendar": "calendar",
    "/api/finance": "finance",
    "/api/learning": "learning",
}
_MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


def create_app() -> FastAPI:
    app = FastAPI(
        title="LifeOS API",
        version=__version__,
        description="All-in-one personal management platform.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def emit_live_updates(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        if request.method not in _MUTATING or response.status_code >= 300:
            return response
        channel = next(
            (name for prefix, name in LIVE_CHANNELS.items() if request.url.path.startswith(prefix)),
            None,
        )
        auth_header = request.headers.get("authorization", "")
        if channel and auth_header.startswith("Bearer "):
            with contextlib.suppress(jwt.PyJWTError, KeyError, ValueError):
                payload = decode_token(auth_header[7:], "access")
                publish(int(payload["sub"]), {"type": channel})
        return response

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(job_tracker.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(calendar.router, prefix="/api")
    app.include_router(finance.router, prefix="/api")
    app.include_router(learning.router, prefix="/api")
    app.include_router(ws.router, prefix="/api")

    @app.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        return {"name": "LifeOS API", "version": __version__, "docs": "/docs"}

    return app


app = create_app()
