from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession, RedisDep
from app.core.cache import cache_version, cached_json, store_json
from app.models.job_tracker import Application, ApplicationStatus, Company, Contact, Interview
from app.schemas.job_tracker import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    CompanyCreate,
    CompanyRead,
    CompanyUpdate,
    ContactCreate,
    ContactRead,
    ContactUpdate,
    InterviewCreate,
    InterviewRead,
    InterviewUpdate,
    JobStats,
)
from app.services import job_tracker as svc

router = APIRouter(prefix="/job-tracker", tags=["job-tracker"])


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


def _company_or_404(db: DbSession, user: CurrentUser, company_id: int) -> Company:
    company = svc.get_company(db, user.id, company_id)
    if company is None:
        raise _not_found("Company")
    return company


def _application_or_404(db: DbSession, user: CurrentUser, application_id: int) -> Application:
    application = svc.get_application(db, user.id, application_id)
    if application is None:
        raise _not_found("Application")
    return application


def _interview_or_404(db: DbSession, user: CurrentUser, interview_id: int) -> Interview:
    interview = svc.get_interview(db, user.id, interview_id)
    if interview is None:
        raise _not_found("Interview")
    return interview


def _contact_or_404(db: DbSession, user: CurrentUser, contact_id: int) -> Contact:
    contact = svc.get_contact(db, user.id, contact_id)
    if contact is None:
        raise _not_found("Contact")
    return contact


# --------------------------------------------------------------------------- #
# Companies
# --------------------------------------------------------------------------- #
@router.get("/companies", response_model=list[CompanyRead])
def list_companies(user: CurrentUser, db: DbSession) -> Sequence[Company]:
    return svc.list_companies(db, user.id)


@router.post(
    "/companies", response_model=CompanyRead, status_code=status.HTTP_201_CREATED
)
def create_company(data: CompanyCreate, user: CurrentUser, db: DbSession) -> Company:
    return svc.create_company(db, user.id, data)


@router.get("/companies/{company_id}", response_model=CompanyRead)
def read_company(company_id: int, user: CurrentUser, db: DbSession) -> Company:
    return _company_or_404(db, user, company_id)


@router.patch("/companies/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int, data: CompanyUpdate, user: CurrentUser, db: DbSession
) -> Company:
    return svc.update_company(db, _company_or_404(db, user, company_id), data)


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_company(db, _company_or_404(db, user, company_id))


# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
@router.get("/applications", response_model=list[ApplicationRead])
def list_applications(
    user: CurrentUser,
    db: DbSession,
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    sort: str = Query(default="-created_at"),
) -> Sequence[Application]:
    return svc.list_applications(db, user.id, status=status_filter, sort=sort)


@router.post(
    "/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED
)
def create_application(
    data: ApplicationCreate, user: CurrentUser, db: DbSession
) -> Application:
    try:
        return svc.create_application(db, user.id, data)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.get("/applications/{application_id}", response_model=ApplicationRead)
def read_application(application_id: int, user: CurrentUser, db: DbSession) -> Application:
    return _application_or_404(db, user, application_id)


@router.patch("/applications/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int, data: ApplicationUpdate, user: CurrentUser, db: DbSession
) -> Application:
    application = _application_or_404(db, user, application_id)
    try:
        return svc.update_application(db, user.id, application, data)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.delete(
    "/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_application(application_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_application(db, _application_or_404(db, user, application_id))


# --------------------------------------------------------------------------- #
# Interviews (nested under an application)
# --------------------------------------------------------------------------- #
@router.get(
    "/applications/{application_id}/interviews", response_model=list[InterviewRead]
)
def list_interviews(
    application_id: int, user: CurrentUser, db: DbSession
) -> Sequence[Interview]:
    _application_or_404(db, user, application_id)
    return svc.list_interviews(db, user.id, application_id)


@router.post(
    "/applications/{application_id}/interviews",
    response_model=InterviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_interview(
    application_id: int, data: InterviewCreate, user: CurrentUser, db: DbSession
) -> Interview:
    application = _application_or_404(db, user, application_id)
    return svc.create_interview(db, user.id, application, data)


@router.patch("/interviews/{interview_id}", response_model=InterviewRead)
def update_interview(
    interview_id: int, data: InterviewUpdate, user: CurrentUser, db: DbSession
) -> Interview:
    return svc.update_interview(db, _interview_or_404(db, user, interview_id), data)


@router.delete("/interviews/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(interview_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_interview(db, _interview_or_404(db, user, interview_id))


# --------------------------------------------------------------------------- #
# Contacts
# --------------------------------------------------------------------------- #
@router.get("/contacts", response_model=list[ContactRead])
def list_contacts(user: CurrentUser, db: DbSession) -> Sequence[Contact]:
    return svc.list_contacts(db, user.id)


@router.post(
    "/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED
)
def create_contact(data: ContactCreate, user: CurrentUser, db: DbSession) -> Contact:
    return svc.create_contact(db, user.id, data)


@router.get("/contacts/{contact_id}", response_model=ContactRead)
def read_contact(contact_id: int, user: CurrentUser, db: DbSession) -> Contact:
    return _contact_or_404(db, user, contact_id)


@router.patch("/contacts/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: int, data: ContactUpdate, user: CurrentUser, db: DbSession
) -> Contact:
    return svc.update_contact(db, _contact_or_404(db, user, contact_id), data)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_contact(db, _contact_or_404(db, user, contact_id))


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #
@router.get("/stats", response_model=JobStats)
def job_stats(
    user: CurrentUser, db: DbSession, client: RedisDep
) -> JobStats | dict[str, Any]:
    version = cache_version(client, "job-tracker", user.id)
    key = f"cache:job-tracker:{user.id}:v{version}:stats"
    hit = cached_json(client, key)
    if hit is not None:
        return cast("dict[str, Any]", hit)

    result = svc.compute_stats(db, user.id)
    store_json(client, key, result.model_dump(mode="json"), ttl_seconds=30)
    return result
