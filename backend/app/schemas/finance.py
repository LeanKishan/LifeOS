from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.finance import TransactionKind


class _FromORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Accounts
# --------------------------------------------------------------------------- #
class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: str = Field(default="checking", max_length=30)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    starting_balance_cents: int = 0


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    kind: str | None = Field(default=None, max_length=30)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    starting_balance_cents: int | None = None
    archived: bool | None = None


class AccountRead(BaseModel):
    id: int
    name: str
    kind: str
    currency: str
    starting_balance_cents: int
    balance_cents: int
    archived: bool
    created_at: datetime


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #
class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    kind: TransactionKind
    color: str = Field(default="#94a3b8", max_length=20)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=20)


class CategoryRead(_FromORM):
    id: int
    name: str
    kind: TransactionKind
    color: str


# --------------------------------------------------------------------------- #
# Transactions
# --------------------------------------------------------------------------- #
class TransactionCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    kind: TransactionKind
    amount_cents: int = Field(gt=0)
    occurred_on: date
    description: str | None = None


class TransactionUpdate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    kind: TransactionKind | None = None
    amount_cents: int | None = Field(default=None, gt=0)
    occurred_on: date | None = None
    description: str | None = None


class TransactionRead(_FromORM):
    id: int
    account_id: int
    category_id: int | None
    kind: TransactionKind
    amount_cents: int
    occurred_on: date
    description: str | None
    created_at: datetime


class ImportRowError(BaseModel):
    row: int
    message: str


class ImportResult(BaseModel):
    imported: int
    errors: list[ImportRowError] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Budgets
# --------------------------------------------------------------------------- #
class BudgetSet(BaseModel):
    category_id: int
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    limit_cents: int = Field(ge=0)


class BudgetRead(_FromORM):
    id: int
    category_id: int
    month: str
    limit_cents: int


# --------------------------------------------------------------------------- #
# Bills
# --------------------------------------------------------------------------- #
class BillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount_cents: int = Field(gt=0)
    day_of_month: int = Field(default=1, ge=1, le=31)
    category_id: int | None = None
    active: bool = True


class BillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    amount_cents: int | None = Field(default=None, gt=0)
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    category_id: int | None = None
    active: bool | None = None


class BillRead(_FromORM):
    id: int
    name: str
    amount_cents: int
    day_of_month: int
    category_id: int | None
    active: bool


# --------------------------------------------------------------------------- #
# Monthly summary
# --------------------------------------------------------------------------- #
class CategorySpend(BaseModel):
    category_id: int
    name: str
    color: str
    spent_cents: int
    budget_cents: int | None
    over: bool


class FinanceSummary(BaseModel):
    month: str
    income_cents: int
    expense_cents: int
    net_cents: int
    savings_rate: float
    uncategorized_cents: int
    upcoming_bills_cents: int
    by_category: list[CategorySpend] = Field(default_factory=list)
