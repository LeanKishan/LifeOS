from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.analytics import AnalyticsOverview
from app.services import analytics as svc

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def read_overview(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
) -> AnalyticsOverview:
    try:
        return svc.overview(db, user.id, date_from, date_to)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/export.csv")
def export_csv(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
) -> Response:
    try:
        data = svc.overview(db, user.id, date_from, date_to)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return Response(
        content=svc.to_csv(data),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="lifeos-analytics.csv"'},
    )


@router.get("/export.pdf")
def export_pdf(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
) -> Response:
    try:
        data = svc.overview(db, user.id, date_from, date_to)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return Response(
        content=svc.to_pdf(data),
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="lifeos-analytics.pdf"'},
    )
