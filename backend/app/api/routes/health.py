from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.redis import get_redis

router = APIRouter(tags=["meta"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Liveness + a cheap database round-trip.

    Always 200 so a load balancer keeps the pod in rotation during a brief DB
    blip; the ``database`` field carries the real status.
    """
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # noqa: BLE001 - any failure means "not reachable right now"
        database = "unavailable"
    return {"status": "ok", "database": database}


@router.get("/health/ready")
def ready(response: Response, db: Session = Depends(get_db)) -> dict[str, object]:
    """Readiness: every backing service this process needs must answer.

    503 when something is down, so a deploy doesn't shift traffic onto a task
    that can't serve. Uptime monitors should watch this, not ``/health``.
    """
    checks: dict[str, str] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {type(exc).__name__}"
    try:
        get_redis().ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {type(exc).__name__}"

    ok = all(v == "ok" for v in checks.values())
    response.status_code = status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if ok else "degraded", "checks": checks}
