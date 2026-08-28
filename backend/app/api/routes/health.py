from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

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
