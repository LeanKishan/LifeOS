from __future__ import annotations

from datetime import date
from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TransactionKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


def _kind_column() -> SAEnum:
    return SAEnum(
        TransactionKind,
        native_enum=False,
        length=10,
        values_callable=lambda enum: [member.value for member in enum],
    )


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(30), default="checking")
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    starting_balance_cents: Mapped[int] = mapped_column(default=0)
    archived: Mapped[bool] = mapped_column(default=False)

    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class Category(TimestampMixin, Base):
    __tablename__ = "finance_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    kind: Mapped[TransactionKind] = mapped_column(_kind_column())
    color: Mapped[str] = mapped_column(String(20), default="#94a3b8")


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("finance_categories.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[TransactionKind] = mapped_column(_kind_column(), index=True)
    amount_cents: Mapped[int] = mapped_column()
    occurred_on: Mapped[date] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column(Text)

    account: Mapped[Account] = relationship(back_populates="transactions")


class Budget(TimestampMixin, Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "month", name="uq_budgets_scope"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("finance_categories.id", ondelete="CASCADE"), index=True
    )
    month: Mapped[str] = mapped_column(String(7))  # "YYYY-MM"
    limit_cents: Mapped[int] = mapped_column()


class Bill(TimestampMixin, Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    amount_cents: Mapped[int] = mapped_column()
    day_of_month: Mapped[int] = mapped_column(default=1)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("finance_categories.id", ondelete="SET NULL"), index=True
    )
    active: Mapped[bool] = mapped_column(default=True)
