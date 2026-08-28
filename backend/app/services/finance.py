from __future__ import annotations

import csv
import io
import re
from collections.abc import Sequence
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.finance import (
    Account,
    Bill,
    Budget,
    Category,
    Transaction,
    TransactionKind,
)
from app.schemas.finance import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
    BillCreate,
    BillUpdate,
    BudgetSet,
    CategoryCreate,
    CategorySpend,
    CategoryUpdate,
    FinanceSummary,
    ImportResult,
    ImportRowError,
    TransactionCreate,
    TransactionUpdate,
)


def _apply(obj: object, changes: dict[str, object]) -> None:
    for field, value in changes.items():
        setattr(obj, field, value)


def month_bounds(month: str) -> tuple[date, date]:
    match = re.fullmatch(r"(\d{4})-(\d{2})", month)
    if match is None:
        raise LookupError("month must be YYYY-MM")
    year, mon = int(match.group(1)), int(match.group(2))
    if not 1 <= mon <= 12:
        raise LookupError("month out of range")
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start, end


# --------------------------------------------------------------------------- #
# Accounts
# --------------------------------------------------------------------------- #
def _account_deltas(db: Session, user_id: int) -> dict[int, int]:
    rows = db.execute(
        select(
            Transaction.account_id,
            Transaction.kind,
            func.sum(Transaction.amount_cents),
        )
        .where(Transaction.user_id == user_id)
        .group_by(Transaction.account_id, Transaction.kind)
    ).all()
    deltas: dict[int, int] = {}
    for account_id, kind, total in rows:
        sign = 1 if TransactionKind(kind) is TransactionKind.INCOME else -1
        deltas[account_id] = deltas.get(account_id, 0) + sign * int(total or 0)
    return deltas


def _to_account_read(account: Account, balance_cents: int) -> AccountRead:
    return AccountRead(
        id=account.id,
        name=account.name,
        kind=account.kind,
        currency=account.currency,
        starting_balance_cents=account.starting_balance_cents,
        balance_cents=balance_cents,
        archived=account.archived,
        created_at=account.created_at,
    )


def list_accounts(
    db: Session, user_id: int, *, include_archived: bool = False
) -> list[AccountRead]:
    stmt = select(Account).where(Account.user_id == user_id)
    if not include_archived:
        stmt = stmt.where(Account.archived.is_(False))
    accounts = db.scalars(stmt.order_by(Account.name)).all()
    deltas = _account_deltas(db, user_id)
    return [
        _to_account_read(a, a.starting_balance_cents + deltas.get(a.id, 0))
        for a in accounts
    ]


def get_account(db: Session, user_id: int, account_id: int) -> Account | None:
    return db.scalars(
        select(Account).where(Account.id == account_id, Account.user_id == user_id)
    ).first()


def account_read(db: Session, user_id: int, account: Account) -> AccountRead:
    delta = _account_deltas(db, user_id).get(account.id, 0)
    return _to_account_read(account, account.starting_balance_cents + delta)


def create_account(db: Session, user_id: int, data: AccountCreate) -> Account:
    account = Account(user_id=user_id, **data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_account(db: Session, account: Account, data: AccountUpdate) -> Account:
    _apply(account, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, account: Account) -> None:
    db.delete(account)
    db.commit()


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #
def list_categories(db: Session, user_id: int) -> Sequence[Category]:
    return db.scalars(
        select(Category).where(Category.user_id == user_id).order_by(Category.name)
    ).all()


def get_category(db: Session, user_id: int, category_id: int) -> Category | None:
    return db.scalars(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    ).first()


def create_category(db: Session, user_id: int, data: CategoryCreate) -> Category:
    category = Category(user_id=user_id, **data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category: Category, data: CategoryUpdate) -> Category:
    _apply(category, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> None:
    db.delete(category)
    db.commit()


# --------------------------------------------------------------------------- #
# Transactions
# --------------------------------------------------------------------------- #
def _transaction_filter(
    user_id: int,
    *,
    account_id: int | None,
    category_id: int | None,
    kind: TransactionKind | None,
    date_from: date | None,
    date_to: date | None,
) -> Select[tuple[Transaction]]:
    stmt = select(Transaction).where(Transaction.user_id == user_id)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    if category_id is not None:
        stmt = stmt.where(Transaction.category_id == category_id)
    if kind is not None:
        stmt = stmt.where(Transaction.kind == kind)
    if date_from is not None:
        stmt = stmt.where(Transaction.occurred_on >= date_from)
    if date_to is not None:
        stmt = stmt.where(Transaction.occurred_on <= date_to)
    return stmt


def list_transactions(
    db: Session,
    user_id: int,
    *,
    account_id: int | None = None,
    category_id: int | None = None,
    kind: TransactionKind | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Transaction]:
    stmt = _transaction_filter(
        user_id,
        account_id=account_id,
        category_id=category_id,
        kind=kind,
        date_from=date_from,
        date_to=date_to,
    )
    stmt = stmt.order_by(Transaction.occurred_on.desc(), Transaction.id.desc())
    return db.scalars(stmt.limit(limit).offset(offset)).all()


def get_transaction(db: Session, user_id: int, transaction_id: int) -> Transaction | None:
    return db.scalars(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == user_id
        )
    ).first()


def _validate_transaction_links(
    db: Session, user_id: int, account_id: int | None, category_id: int | None
) -> None:
    if account_id is not None and get_account(db, user_id, account_id) is None:
        raise LookupError("account_id does not belong to you")
    if category_id is not None and get_category(db, user_id, category_id) is None:
        raise LookupError("category_id does not belong to you")


def create_transaction(
    db: Session, user_id: int, data: TransactionCreate
) -> Transaction:
    _validate_transaction_links(db, user_id, data.account_id, data.category_id)
    transaction = Transaction(user_id=user_id, **data.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def update_transaction(
    db: Session, user_id: int, transaction: Transaction, data: TransactionUpdate
) -> Transaction:
    changes = data.model_dump(exclude_unset=True)
    _validate_transaction_links(
        db, user_id, changes.get("account_id"), changes.get("category_id")
    )
    _apply(transaction, changes)
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, transaction: Transaction) -> None:
    db.delete(transaction)
    db.commit()


# --------------------------------------------------------------------------- #
# CSV import
# --------------------------------------------------------------------------- #
_REQUIRED_COLUMNS = {"occurred_on", "kind", "amount", "account"}


def import_transactions(db: Session, user_id: int, csv_text: str) -> ImportResult:
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None or not _REQUIRED_COLUMNS.issubset(reader.fieldnames):
        missing = sorted(_REQUIRED_COLUMNS.difference(reader.fieldnames or []))
        raise LookupError(f"CSV is missing columns: {missing}")

    accounts = {
        a.name.lower(): a
        for a in db.scalars(select(Account).where(Account.user_id == user_id))
    }
    categories = {
        (c.name.lower(), c.kind): c
        for c in db.scalars(select(Category).where(Category.user_id == user_id))
    }

    imported = 0
    errors: list[ImportRowError] = []

    for line_number, row in enumerate(reader, start=2):
        try:
            occurred = date.fromisoformat((row["occurred_on"] or "").strip())
            kind = TransactionKind((row["kind"] or "").strip().lower())
            try:
                amount = Decimal((row["amount"] or "").strip())
            except InvalidOperation:
                raise ValueError(f"invalid amount: {row['amount']!r}") from None
            if amount <= 0:
                raise ValueError("amount must be positive")
            cents = int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))

            account = accounts.get((row["account"] or "").strip().lower())
            if account is None:
                raise ValueError(f"unknown account: {row['account']!r}")

            category = None
            category_name = (row.get("category") or "").strip()
            if category_name:
                key = (category_name.lower(), kind)
                category = categories.get(key)
                if category is None:
                    category = Category(
                        user_id=user_id, name=category_name, kind=kind, color="#94a3b8"
                    )
                    db.add(category)
                    db.flush()
                    categories[key] = category

            db.add(
                Transaction(
                    user_id=user_id,
                    account_id=account.id,
                    category_id=category.id if category else None,
                    kind=kind,
                    amount_cents=cents,
                    occurred_on=occurred,
                    description=(row.get("description") or "").strip() or None,
                )
            )
            imported += 1
        except (KeyError, ValueError, InvalidOperation) as exc:
            errors.append(ImportRowError(row=line_number, message=str(exc)))

    if imported:
        db.commit()
    else:
        db.rollback()
    return ImportResult(imported=imported, errors=errors)


# --------------------------------------------------------------------------- #
# Budgets
# --------------------------------------------------------------------------- #
def list_budgets(db: Session, user_id: int, month: str) -> Sequence[Budget]:
    return db.scalars(
        select(Budget).where(Budget.user_id == user_id, Budget.month == month)
    ).all()


def get_budget(db: Session, user_id: int, budget_id: int) -> Budget | None:
    return db.scalars(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    ).first()


def set_budget(db: Session, user_id: int, data: BudgetSet) -> Budget:
    if get_category(db, user_id, data.category_id) is None:
        raise LookupError("category_id does not belong to you")
    existing = db.scalars(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == data.category_id,
            Budget.month == data.month,
        )
    ).first()
    if existing is not None:
        existing.limit_cents = data.limit_cents
        db.commit()
        db.refresh(existing)
        return existing

    budget = Budget(user_id=user_id, **data.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, budget: Budget) -> None:
    db.delete(budget)
    db.commit()


# --------------------------------------------------------------------------- #
# Bills
# --------------------------------------------------------------------------- #
def list_bills(db: Session, user_id: int) -> Sequence[Bill]:
    return db.scalars(
        select(Bill).where(Bill.user_id == user_id).order_by(Bill.day_of_month)
    ).all()


def get_bill(db: Session, user_id: int, bill_id: int) -> Bill | None:
    return db.scalars(
        select(Bill).where(Bill.id == bill_id, Bill.user_id == user_id)
    ).first()


def create_bill(db: Session, user_id: int, data: BillCreate) -> Bill:
    bill = Bill(user_id=user_id, **data.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def update_bill(db: Session, bill: Bill, data: BillUpdate) -> Bill:
    _apply(bill, data.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(bill)
    return bill


def delete_bill(db: Session, bill: Bill) -> None:
    db.delete(bill)
    db.commit()


# --------------------------------------------------------------------------- #
# Monthly summary
# --------------------------------------------------------------------------- #
def summarize(db: Session, user_id: int, month: str) -> FinanceSummary:
    start, end = month_bounds(month)
    window = (Transaction.occurred_on >= start, Transaction.occurred_on < end)

    kind_rows = db.execute(
        select(Transaction.kind, func.sum(Transaction.amount_cents))
        .where(Transaction.user_id == user_id, *window)
        .group_by(Transaction.kind)
    ).all()
    totals = {kind: 0 for kind in TransactionKind}
    for kind, total in kind_rows:
        totals[TransactionKind(kind)] = int(total or 0)
    income = totals[TransactionKind.INCOME]
    expense = totals[TransactionKind.EXPENSE]
    net = income - expense
    savings_rate = round(net / income, 4) if income > 0 else 0.0

    spend_rows = db.execute(
        select(Transaction.category_id, func.sum(Transaction.amount_cents))
        .where(
            Transaction.user_id == user_id,
            Transaction.kind == TransactionKind.EXPENSE,
            *window,
        )
        .group_by(Transaction.category_id)
    ).all()
    spent: dict[int | None, int] = {
        category_id: int(total or 0) for category_id, total in spend_rows
    }
    uncategorized = spent.pop(None, 0)

    budgets = {b.category_id: b.limit_cents for b in list_budgets(db, user_id, month)}
    categories = db.scalars(
        select(Category).where(
            Category.user_id == user_id, Category.kind == TransactionKind.EXPENSE
        )
    ).all()

    by_category: list[CategorySpend] = []
    for category in categories:
        spent_cents = spent.get(category.id, 0)
        budget_cents = budgets.get(category.id)
        by_category.append(
            CategorySpend(
                category_id=category.id,
                name=category.name,
                color=category.color,
                spent_cents=spent_cents,
                budget_cents=budget_cents,
                over=budget_cents is not None and spent_cents > budget_cents,
            )
        )
    by_category.sort(key=lambda entry: entry.spent_cents, reverse=True)

    bills_total = int(
        db.scalar(
            select(func.coalesce(func.sum(Bill.amount_cents), 0)).where(
                Bill.user_id == user_id, Bill.active.is_(True)
            )
        )
        or 0
    )

    return FinanceSummary(
        month=month,
        income_cents=income,
        expense_cents=expense,
        net_cents=net,
        savings_rate=savings_rate,
        uncategorized_cents=uncategorized,
        upcoming_bills_cents=bills_total,
        by_category=by_category,
    )
