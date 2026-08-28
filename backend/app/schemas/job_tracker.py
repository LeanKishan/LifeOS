from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.job_tracker import ApplicationStatus


class _FromORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Company
# --------------------------------------------------------------------------- #
class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class CompanyRead(_FromORM, CompanyBase):
    id: int
    created_at: datetime


# --------------------------------------------------------------------------- #
# Interview
# --------------------------------------------------------------------------- #
class InterviewBase(BaseModel):
    kind: str = Field(min_length=1, max_length=50)
    scheduled_at: datetime | None = None
    outcome: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    kind: str | None = Field(default=None, min_length=1, max_length=50)
    scheduled_at: datetime | None = None
    outcome: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class InterviewRead(_FromORM, InterviewBase):
    id: int
    application_id: int
    created_at: datetime


# --------------------------------------------------------------------------- #
# Application
# --------------------------------------------------------------------------- #
class ApplicationBase(BaseModel):
    role: str = Field(min_length=1, max_length=200)
    status: ApplicationStatus = ApplicationStatus.APPLIED
    source: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=200)
    job_url: str | None = Field(default=None, max_length=1000)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: str = Field(default="USD", min_length=3, max_length=3)
    applied_on: date | None = None
    notes: str | None = None


class ApplicationCreate(ApplicationBase):
    company_id: int | None = None
    company_name: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _require_company_ref(self) -> ApplicationCreate:
        has_name = bool(self.company_name and self.company_name.strip())
        if self.company_id is None and not has_name:
            raise ValueError("Provide either company_id or company_name")
        return self


class ApplicationUpdate(BaseModel):
    company_id: int | None = None
    role: str | None = Field(default=None, min_length=1, max_length=200)
    status: ApplicationStatus | None = None
    source: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=200)
    job_url: str | None = Field(default=None, max_length=1000)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: str | None = Field(default=None, min_length=3, max_length=3)
    applied_on: date | None = None
    notes: str | None = None


class ApplicationRead(_FromORM, ApplicationBase):
    id: int
    company: CompanyRead
    interviews: list[InterviewRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Contact
# --------------------------------------------------------------------------- #
class ContactBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = None
    company_id: int | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = None
    company_id: int | None = None


class ContactRead(_FromORM, ContactBase):
    id: int
    created_at: datetime


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #
class JobStats(BaseModel):
    total: int
    by_status: dict[str, int]
    active: int
    responded: int
    response_rate: float
    offers: int
    offer_rate: float
