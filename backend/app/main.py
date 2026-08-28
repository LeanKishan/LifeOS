from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import auth, calendar, health, job_tracker, projects
from app.core.config import get_settings

settings = get_settings()


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

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(job_tracker.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(calendar.router, prefix="/api")

    @app.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        return {"name": "LifeOS API", "version": __version__, "docs": "/docs"}

    return app


app = create_app()
