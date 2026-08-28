from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Path, Query, Response, UploadFile, status

from app.api.deps import CurrentUser, DbSession, RedisDep
from app.core.cache import cache_version, cached_json, store_json
from app.models.finance import Account, Bill, Budget, Category, Transaction, TransactionKind
from app.schemas.finance import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
    BillCreate,
    BillRead,
    BillUpdate,
    BudgetRead,
    BudgetSet,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    FinanceSummary,
    ImportResult,
    ReportRequest,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from app.services import finance as svc
from app.services.reports import load_report
from app.worker.tasks import generate_finance_report

router = APIRouter(prefix="/finance", tags=["finance"])


def _404(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


def _422(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)


def _account_or_404(db: DbSession, user: CurrentUser, account_id: int) -> Account:
    account = svc.get_account(db, user.id, account_id)
    if account is None:
        raise _404("Account")
    return account


def _category_or_404(db: DbSession, user: CurrentUser, category_id: int) -> Category:
    category = svc.get_category(db, user.id, category_id)
    if category is None:
        raise _404("Category")
    return category


def _transaction_or_404(db: DbSession, user: CurrentUser, transaction_id: int) -> Transaction:
    transaction = svc.get_transaction(db, user.id, transaction_id)
    if transaction is None:
        raise _404("Transaction")
    return transaction


def _budget_or_404(db: DbSession, user: CurrentUser, budget_id: int) -> Budget:
    budget = svc.get_budget(db, user.id, budget_id)
    if budget is None:
        raise _404("Budget")
    return budget


def _bill_or_404(db: DbSession, user: CurrentUser, bill_id: int) -> Bill:
    bill = svc.get_bill(db, user.id, bill_id)
    if bill is None:
        raise _404("Bill")
    return bill


# --------------------------------------------------------------------------- #
# Accounts
# --------------------------------------------------------------------------- #
@router.get("/accounts", response_model=list[AccountRead])
def list_accounts(
    user: CurrentUser, db: DbSession, archived: bool = Query(default=False)
) -> list[AccountRead]:
    return svc.list_accounts(db, user.id, include_archived=archived)


@router.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(data: AccountCreate, user: CurrentUser, db: DbSession) -> AccountRead:
    account = svc.create_account(db, user.id, data)
    return svc.account_read(db, user.id, account)


@router.patch("/accounts/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int, data: AccountUpdate, user: CurrentUser, db: DbSession
) -> AccountRead:
    account = svc.update_account(db, _account_or_404(db, user, account_id), data)
    return svc.account_read(db, user.id, account)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_account(db, _account_or_404(db, user, account_id))


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #
@router.get("/categories", response_model=list[CategoryRead])
def list_categories(user: CurrentUser, db: DbSession) -> Sequence[Category]:
    return svc.list_categories(db, user.id)


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, user: CurrentUser, db: DbSession) -> Category:
    return svc.create_category(db, user.id, data)


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int, data: CategoryUpdate, user: CurrentUser, db: DbSession
) -> Category:
    return svc.update_category(db, _category_or_404(db, user, category_id), data)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_category(db, _category_or_404(db, user, category_id))


# --------------------------------------------------------------------------- #
# Transactions
# --------------------------------------------------------------------------- #
@router.get("/transactions", response_model=list[TransactionRead])
def list_transactions(
    user: CurrentUser,
    db: DbSession,
    account_id: int | None = Query(default=None),
    category_id: int | None = Query(default=None),
    kind: TransactionKind | None = Query(default=None),
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Sequence[Transaction]:
    return svc.list_transactions(
        db,
        user.id,
        account_id=account_id,
        category_id=category_id,
        kind=kind,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED
)
def create_transaction(
    data: TransactionCreate, user: CurrentUser, db: DbSession
) -> Transaction:
    try:
        return svc.create_transaction(db, user.id, data)
    except LookupError as exc:
        raise _422(str(exc)) from exc


@router.get("/transactions/{transaction_id}", response_model=TransactionRead)
def read_transaction(transaction_id: int, user: CurrentUser, db: DbSession) -> Transaction:
    return _transaction_or_404(db, user, transaction_id)


@router.patch("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int, data: TransactionUpdate, user: CurrentUser, db: DbSession
) -> Transaction:
    transaction = _transaction_or_404(db, user, transaction_id)
    try:
        return svc.update_transaction(db, user.id, transaction, data)
    except LookupError as exc:
        raise _422(str(exc)) from exc


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_transaction(db, _transaction_or_404(db, user, transaction_id))


@router.post("/transactions/import", response_model=ImportResult)
def import_transactions(
    file: UploadFile, user: CurrentUser, db: DbSession
) -> ImportResult:
    raw = file.file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise _422("file must be UTF-8 encoded CSV") from exc
    try:
        return svc.import_transactions(db, user.id, text)
    except LookupError as exc:
        raise _422(str(exc)) from exc


# --------------------------------------------------------------------------- #
# Budgets
# --------------------------------------------------------------------------- #
@router.get("/budgets", response_model=list[BudgetRead])
def list_budgets(
    user: CurrentUser, db: DbSession, month: str = Query(pattern=r"^\d{4}-\d{2}$")
) -> Sequence[Budget]:
    return svc.list_budgets(db, user.id, month)


@router.post("/budgets", response_model=BudgetRead)
def set_budget(data: BudgetSet, user: CurrentUser, db: DbSession) -> Budget:
    try:
        return svc.set_budget(db, user.id, data)
    except LookupError as exc:
        raise _422(str(exc)) from exc


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_budget(db, _budget_or_404(db, user, budget_id))


# --------------------------------------------------------------------------- #
# Bills
# --------------------------------------------------------------------------- #
@router.get("/bills", response_model=list[BillRead])
def list_bills(user: CurrentUser, db: DbSession) -> Sequence[Bill]:
    return svc.list_bills(db, user.id)


@router.post("/bills", response_model=BillRead, status_code=status.HTTP_201_CREATED)
def create_bill(data: BillCreate, user: CurrentUser, db: DbSession) -> Bill:
    return svc.create_bill(db, user.id, data)


@router.patch("/bills/{bill_id}", response_model=BillRead)
def update_bill(
    bill_id: int, data: BillUpdate, user: CurrentUser, db: DbSession
) -> Bill:
    return svc.update_bill(db, _bill_or_404(db, user, bill_id), data)


@router.delete("/bills/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(bill_id: int, user: CurrentUser, db: DbSession) -> None:
    svc.delete_bill(db, _bill_or_404(db, user, bill_id))


# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #
@router.get("/summary", response_model=FinanceSummary)
def summary(
    user: CurrentUser,
    db: DbSession,
    client: RedisDep,
    month: str = Query(pattern=r"^\d{4}-\d{2}$"),
) -> FinanceSummary | dict[str, Any]:
    version = cache_version(client, "finance", user.id)
    key = f"cache:finance:{user.id}:v{version}:{month}"
    hit = cached_json(client, key)
    if hit is not None:
        return cast("dict[str, Any]", hit)

    try:
        result = svc.summarize(db, user.id, month)
    except LookupError as exc:
        raise _422(str(exc)) from exc

    store_json(client, key, result.model_dump(mode="json"), ttl_seconds=30)
    return result


# --------------------------------------------------------------------------- #
# Monthly PDF report (rendered by a Celery task)
# --------------------------------------------------------------------------- #
@router.post("/reports", status_code=status.HTTP_202_ACCEPTED)
def request_report(data: ReportRequest, user: CurrentUser) -> dict[str, str]:
    generate_finance_report.delay(user.id, data.month)
    return {"status": "queued", "month": data.month}


@router.get("/reports/{month}")
def download_report(
    user: CurrentUser,
    client: RedisDep,
    month: str = Path(pattern=r"^\d{4}-\d{2}$"),
) -> Response:
    pdf = load_report(client, user.id, month)
    if pdf is None:
        raise _404("Report")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="finance-{month}.pdf"'},
    )
