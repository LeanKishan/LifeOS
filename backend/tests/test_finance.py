from __future__ import annotations

import io
from collections.abc import Callable

from fastapi.testclient import TestClient

FIN = "/api/finance"
AuthHeaderFactory = Callable[..., dict[str, str]]


def make_account(client: TestClient, headers: dict[str, str], **kw: object) -> dict:
    body: dict[str, object] = {"name": "Checking", "starting_balance_cents": 100_000}
    body.update(kw)
    resp = client.post(f"{FIN}/accounts", json=body, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def make_category(
    client: TestClient, headers: dict[str, str], name: str, kind: str = "expense"
) -> dict:
    resp = client.post(
        f"{FIN}/categories", json={"name": name, "kind": kind}, headers=headers
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def add_txn(
    client: TestClient,
    headers: dict[str, str],
    account_id: int,
    *,
    kind: str,
    cents: int,
    on: str,
    category_id: int | None = None,
) -> dict:
    resp = client.post(
        f"{FIN}/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "kind": kind,
            "amount_cents": cents,
            "occurred_on": on,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# --------------------------------------------------------------------------- #
# Basics
# --------------------------------------------------------------------------- #
def test_requires_auth(client: TestClient) -> None:
    assert client.get(f"{FIN}/summary?month=2026-08").status_code == 401


def test_amount_must_be_positive(client: TestClient, auth_headers: dict[str, str]) -> None:
    account = make_account(client, auth_headers)
    resp = client.post(
        f"{FIN}/transactions",
        json={
            "account_id": account["id"],
            "kind": "expense",
            "amount_cents": 0,
            "occurred_on": "2026-08-10",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_foreign_account_is_422(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    account = make_account(client, alice)
    resp = client.post(
        f"{FIN}/transactions",
        json={
            "account_id": account["id"],
            "kind": "expense",
            "amount_cents": 500,
            "occurred_on": "2026-08-10",
        },
        headers=bob,
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Account balance
# --------------------------------------------------------------------------- #
def test_account_balance_reflects_transactions(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    account = make_account(client, auth_headers, starting_balance_cents=100_000)
    add_txn(client, auth_headers, account["id"], kind="income", cents=50_000, on="2026-08-01")
    add_txn(client, auth_headers, account["id"], kind="expense", cents=20_000, on="2026-08-02")

    listed = client.get(f"{FIN}/accounts", headers=auth_headers).json()
    assert listed[0]["balance_cents"] == 130_000


# --------------------------------------------------------------------------- #
# Filters
# --------------------------------------------------------------------------- #
def test_transaction_filters(client: TestClient, auth_headers: dict[str, str]) -> None:
    account = make_account(client, auth_headers)
    add_txn(client, auth_headers, account["id"], kind="income", cents=1000, on="2026-08-01")
    add_txn(client, auth_headers, account["id"], kind="expense", cents=2000, on="2026-08-15")
    add_txn(client, auth_headers, account["id"], kind="expense", cents=3000, on="2026-09-01")

    only_expense = client.get(
        f"{FIN}/transactions?kind=expense", headers=auth_headers
    ).json()
    assert {t["amount_cents"] for t in only_expense} == {2000, 3000}

    august = client.get(
        f"{FIN}/transactions?from=2026-08-01&to=2026-08-31", headers=auth_headers
    ).json()
    assert {t["amount_cents"] for t in august} == {1000, 2000}


# --------------------------------------------------------------------------- #
# Summary aggregation
# --------------------------------------------------------------------------- #
def test_summary_math(client: TestClient, auth_headers: dict[str, str]) -> None:
    account = make_account(client, auth_headers)
    add_txn(client, auth_headers, account["id"], kind="income", cents=400_000, on="2026-08-05")
    add_txn(client, auth_headers, account["id"], kind="expense", cents=100_000, on="2026-08-10")
    add_txn(client, auth_headers, account["id"], kind="expense", cents=180_000, on="2026-08-20")

    summary = client.get(f"{FIN}/summary?month=2026-08", headers=auth_headers).json()
    assert summary["income_cents"] == 400_000
    assert summary["expense_cents"] == 280_000
    assert summary["net_cents"] == 120_000
    assert summary["savings_rate"] == 0.3


def test_summary_month_boundary(client: TestClient, auth_headers: dict[str, str]) -> None:
    account = make_account(client, auth_headers)
    add_txn(client, auth_headers, account["id"], kind="expense", cents=100, on="2026-07-31")
    add_txn(client, auth_headers, account["id"], kind="expense", cents=200, on="2026-08-01")
    add_txn(client, auth_headers, account["id"], kind="expense", cents=400, on="2026-08-31")
    add_txn(client, auth_headers, account["id"], kind="expense", cents=800, on="2026-09-01")

    summary = client.get(f"{FIN}/summary?month=2026-08", headers=auth_headers).json()
    assert summary["expense_cents"] == 600


def test_summary_budget_vs_actual(client: TestClient, auth_headers: dict[str, str]) -> None:
    account = make_account(client, auth_headers)
    groceries = make_category(client, auth_headers, "Groceries")
    add_txn(
        client, auth_headers, account["id"],
        kind="expense", cents=62_000, on="2026-08-12", category_id=groceries["id"],
    )
    client.post(
        f"{FIN}/budgets",
        json={"category_id": groceries["id"], "month": "2026-08", "limit_cents": 60_000},
        headers=auth_headers,
    )

    summary = client.get(f"{FIN}/summary?month=2026-08", headers=auth_headers).json()
    row = next(c for c in summary["by_category"] if c["category_id"] == groceries["id"])
    assert row["spent_cents"] == 62_000
    assert row["budget_cents"] == 60_000
    assert row["over"] is True


def test_summary_bad_month_is_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get(f"{FIN}/summary?month=2026-13", headers=auth_headers).status_code == 422


# --------------------------------------------------------------------------- #
# Budget upsert
# --------------------------------------------------------------------------- #
def test_budget_post_is_upsert(client: TestClient, auth_headers: dict[str, str]) -> None:
    category = make_category(client, auth_headers, "Rent")
    body = {"category_id": category["id"], "month": "2026-08", "limit_cents": 150_000}
    first = client.post(f"{FIN}/budgets", json=body, headers=auth_headers).json()
    body["limit_cents"] = 160_000
    second = client.post(f"{FIN}/budgets", json=body, headers=auth_headers).json()

    assert first["id"] == second["id"]
    assert second["limit_cents"] == 160_000
    listed = client.get(f"{FIN}/budgets?month=2026-08", headers=auth_headers).json()
    assert len(listed) == 1


# --------------------------------------------------------------------------- #
# CSV import
# --------------------------------------------------------------------------- #
def test_csv_import(client: TestClient, auth_headers: dict[str, str]) -> None:
    make_account(client, auth_headers, name="Everyday")
    csv_text = (
        "occurred_on,description,amount,kind,category,account\n"
        "2026-08-03,Coffee,4.50,expense,Cafe,Everyday\n"
        "2026-08-04,Paycheck,2500.00,income,Salary,Everyday\n"
        "2026-08-05,Bad row,notanumber,expense,,Everyday\n"
        "2026-08-06,Ghost,10.00,expense,,Nonexistent\n"
    )
    resp = client.post(
        f"{FIN}/transactions/import",
        files={"file": ("tx.csv", io.BytesIO(csv_text.encode()), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["imported"] == 2
    assert {e["row"] for e in body["errors"]} == {4, 5}

    txns = client.get(f"{FIN}/transactions", headers=auth_headers).json()
    assert {t["amount_cents"] for t in txns} == {450, 250_000}


def test_csv_import_missing_columns_is_422(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    resp = client.post(
        f"{FIN}/transactions/import",
        files={"file": ("tx.csv", io.BytesIO(b"foo,bar\n1,2\n"), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Ownership & cascade
# --------------------------------------------------------------------------- #
def test_delete_account_removes_its_transactions(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    account = make_account(client, auth_headers)
    txn = add_txn(client, auth_headers, account["id"], kind="expense", cents=500, on="2026-08-10")

    assert client.delete(f"{FIN}/accounts/{account['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"{FIN}/transactions/{txn['id']}", headers=auth_headers).status_code == 404


def test_delete_category_nulls_transactions(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    account = make_account(client, auth_headers)
    category = make_category(client, auth_headers, "Toys")
    txn = add_txn(
        client, auth_headers, account["id"],
        kind="expense", cents=500, on="2026-08-10", category_id=category["id"],
    )

    deleted = client.delete(f"{FIN}/categories/{category['id']}", headers=auth_headers)
    assert deleted.status_code == 204
    fetched = client.get(f"{FIN}/transactions/{txn['id']}", headers=auth_headers).json()
    assert fetched["category_id"] is None
