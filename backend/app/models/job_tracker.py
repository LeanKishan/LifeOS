from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ApplicationStatus(StrEnum):
    WISHLIST = "wishlist"
    APPLIED = "applied"
    ASSESSMENT = "assessment"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# The company got back to you (beyond an auto-ack).
RESPONDED_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {
        ApplicationStatus.ASSESSMENT,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.OFFER,
        ApplicationStatus.ACCEPTED,
        ApplicationStatus.REJECTED,
    }
)

# No longer in play.
CLOSED_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
)


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    website: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    applications: Mapped[list[Application]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class Application(TimestampMixin, Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )

    role: Mapped[str] = mapped_column(String(200))
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(
            ApplicationStatus,
            native_enum=False,
            length=20,
            # Persist the lowercase values ("applied"), not the member names.
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=ApplicationStatus.APPLIED,
        index=True,
    )
    source: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(200))
    job_url: Mapped[str | None] = mapped_column(String(1000))
    salary_min: Mapped[int | None] = mapped_column()
    salary_max: Mapped[int | None] = mapped_column()
    salary_currency: Mapped[str] = mapped_column(String(3), default="USD")
    applied_on: Mapped[date | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)

    company: Mapped[Company] = relationship(back_populates="applications")
    interviews: Mapped[list[Interview]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="Interview.scheduled_at",
    )


class Interview(TimestampMixin, Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(50))
    scheduled_at: Mapped[datetime | None] = mapped_column()
    outcome: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="interviews")


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
