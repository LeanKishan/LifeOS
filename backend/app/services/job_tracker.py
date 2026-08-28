from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.job_tracker import (
    CLOSED_STATUSES,
    RESPONDED_STATUSES,
    Application,
    ApplicationStatus,
    Company,
    Contact,
    Interview,
)
from app.schemas.job_tracker import (
    ApplicationCreate,
    ApplicationUpdate,
    CompanyCreate,
    CompanyUpdate,
    ContactCreate,
    ContactUpdate,
    InterviewCreate,
    InterviewUpdate,
    JobStats,
)

_SORTABLE = {
    "created_at": Application.created_at,
    "updated_at": Application.updated_at,
    "role": Application.role,
    "status": Application.status,
    "applied_on": Application.applied_on,
}


def _apply_changes(obj: object, changes: dict[str, object]) -> None:
    for field, value in changes.items():
        setattr(obj, field, value)


# --------------------------------------------------------------------------- #
# Companies
# --------------------------------------------------------------------------- #
def list_companies(db: Session, user_id: int) -> Sequence[Company]:
    return db.scalars(
        select(Company).where(Company.user_id == user_id).order_by(Company.name)
    ).all()


def get_company(db: Session, user_id: int, company_id: int) -> Company | None:
    return db.scalars(
        select(Company).where(Company.id == company_id, Company.user_id == user_id)
    ).first()


def create_company(db: Session, user_id: int, data: CompanyCreate) -> Company:
    company = Company(user_id=user_id, **data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def update_company(db: Session, company: Company, data: CompanyUpdate) -> Company:
    _apply_changes(company, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(company)
    return company


def delete_company(db: Session, company: Company) -> None:
    db.delete(company)
    db.commit()


def _resolve_company(
    db: Session, user_id: int, company_id: int | None, company_name: str | None
) -> Company:
    if company_id is not None:
        company = get_company(db, user_id, company_id)
        if company is None:
            raise LookupError("company_id does not belong to you")
        return company

    name = (company_name or "").strip()
    existing = db.scalars(
        select(Company).where(
            Company.user_id == user_id, func.lower(Company.name) == name.lower()
        )
    ).first()
    if existing is not None:
        return existing

    company = Company(user_id=user_id, name=name)
    db.add(company)
    db.flush()
    return company


# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
def _application_query(user_id: int) -> Select[tuple[Application]]:
    return (
        select(Application)
        .where(Application.user_id == user_id)
        .options(
            selectinload(Application.company),
            selectinload(Application.interviews),
        )
    )


def list_applications(
    db: Session,
    user_id: int,
    *,
    status: ApplicationStatus | None = None,
    sort: str = "-created_at",
) -> Sequence[Application]:
    stmt = _application_query(user_id)
    if status is not None:
        stmt = stmt.where(Application.status == status)

    descending = sort.startswith("-")
    column = _SORTABLE.get(sort.lstrip("-"), Application.created_at)
    stmt = stmt.order_by(column.desc() if descending else column.asc())
    return db.scalars(stmt).all()


def get_application(db: Session, user_id: int, application_id: int) -> Application | None:
    return db.scalars(
        _application_query(user_id).where(Application.id == application_id)
    ).first()


def create_application(db: Session, user_id: int, data: ApplicationCreate) -> Application:
    company = _resolve_company(db, user_id, data.company_id, data.company_name)
    payload = data.model_dump(exclude={"company_id", "company_name"})
    application = Application(user_id=user_id, company=company, **payload)
    db.add(application)
    db.commit()
    return _reload_application(db, user_id, application.id)


def update_application(
    db: Session, user_id: int, application: Application, data: ApplicationUpdate
) -> Application:
    changes = data.model_dump(exclude_unset=True)
    if "company_id" in changes:
        new_company = get_company(db, user_id, int(changes.pop("company_id")))
        if new_company is None:
            raise LookupError("company_id does not belong to you")
        application.company = new_company
    _apply_changes(application, changes)
    db.commit()
    return _reload_application(db, user_id, application.id)


def delete_application(db: Session, application: Application) -> None:
    db.delete(application)
    db.commit()


def _reload_application(db: Session, user_id: int, application_id: int) -> Application:
    application = get_application(db, user_id, application_id)
    if application is None:  # pragma: no cover - just committed it
        raise RuntimeError("application vanished after commit")
    return application


# --------------------------------------------------------------------------- #
# Interviews
# --------------------------------------------------------------------------- #
def list_interviews(db: Session, user_id: int, application_id: int) -> Sequence[Interview]:
    return db.scalars(
        select(Interview)
        .where(Interview.user_id == user_id, Interview.application_id == application_id)
        .order_by(Interview.scheduled_at.is_(None), Interview.scheduled_at)
    ).all()


def get_interview(db: Session, user_id: int, interview_id: int) -> Interview | None:
    return db.scalars(
        select(Interview).where(
            Interview.id == interview_id, Interview.user_id == user_id
        )
    ).first()


def create_interview(
    db: Session, user_id: int, application: Application, data: InterviewCreate
) -> Interview:
    interview = Interview(
        user_id=user_id, application_id=application.id, **data.model_dump()
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


def update_interview(db: Session, interview: Interview, data: InterviewUpdate) -> Interview:
    _apply_changes(interview, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(interview)
    return interview


def delete_interview(db: Session, interview: Interview) -> None:
    db.delete(interview)
    db.commit()


# --------------------------------------------------------------------------- #
# Contacts
# --------------------------------------------------------------------------- #
def list_contacts(db: Session, user_id: int) -> Sequence[Contact]:
    return db.scalars(
        select(Contact).where(Contact.user_id == user_id).order_by(Contact.name)
    ).all()


def get_contact(db: Session, user_id: int, contact_id: int) -> Contact | None:
    return db.scalars(
        select(Contact).where(Contact.id == contact_id, Contact.user_id == user_id)
    ).first()


def create_contact(db: Session, user_id: int, data: ContactCreate) -> Contact:
    contact = Contact(user_id=user_id, **data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(db: Session, contact: Contact, data: ContactUpdate) -> Contact:
    _apply_changes(contact, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, contact: Contact) -> None:
    db.delete(contact)
    db.commit()


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #
def compute_stats(db: Session, user_id: int) -> JobStats:
    rows = db.execute(
        select(Application.status, func.count())
        .where(Application.user_id == user_id)
        .group_by(Application.status)
    ).all()

    by_status: dict[str, int] = {status.value: 0 for status in ApplicationStatus}
    for raw_status, count in rows:
        by_status[ApplicationStatus(raw_status).value] = int(count)

    total = sum(by_status.values())
    submitted = total - by_status[ApplicationStatus.WISHLIST.value]
    responded = sum(by_status[s.value] for s in RESPONDED_STATUSES)
    offers = (
        by_status[ApplicationStatus.OFFER.value]
        + by_status[ApplicationStatus.ACCEPTED.value]
    )
    active = total - sum(by_status[s.value] for s in CLOSED_STATUSES)

    return JobStats(
        total=total,
        by_status=by_status,
        active=active,
        responded=responded,
        response_rate=round(responded / submitted, 3) if submitted else 0.0,
        offers=offers,
        offer_rate=round(offers / submitted, 3) if submitted else 0.0,
    )
