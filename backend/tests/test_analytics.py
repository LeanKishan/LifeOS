from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

OVERVIEW = "/api/analytics/overview"
AuthHeaderFactory = Callable[..., dict[str, str]]


def board(client: TestClient, headers: dict[str, str], name: str = "Work") -> dict:
    return client.post("/api/projects", json={"name": name}, headers=headers).json()


def add_task(
    client: TestClient, headers: dict[str, str], project: dict, title: str, priority: str = "medium"
) -> int:
    resp = client.post(
        f"/api/projects/{project['id']}/tasks",
        json={"column_id": project["columns"][0]["id"], "title": title, "priority": priority},
        headers=headers,
    )
    return int(resp.json()["id"])


def finish_task(client: TestClient, headers: dict[str, str], task_id: int) -> None:
    resp = client.patch(
        f"/api/projects/tasks/{task_id}", json={"done": True}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["done"] is True
    assert resp.json()["completed_at"] is not None


def spend(
    client: TestClient,
    headers: dict[str, str],
    account_id: int,
    cents: int,
    on: str,
    kind: str = "expense",
) -> None:
    resp = client.post(
        "/api/finance/transactions",
        json={"account_id": account_id, "kind": kind, "amount_cents": cents, "occurred_on": on},
        headers=headers,
    )
    assert resp.status_code == 201


# --------------------------------------------------------------------------- #
def test_requires_auth(client: TestClient) -> None:
    assert client.get(OVERVIEW).status_code == 401


def test_productivity_completion_and_cycle(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    project = board(client, auth_headers)
    ids = [add_task(client, auth_headers, project, f"T{i}", "high") for i in range(4)]
    finish_task(client, auth_headers, ids[0])
    finish_task(client, auth_headers, ids[1])

    data = client.get(OVERVIEW, headers=auth_headers).json()
    prod = data["productivity"]
    assert prod["tasks_total"] == 4
    assert prod["tasks_done"] == 2
    assert prod["completion_rate"] == 0.5
    assert prod["by_priority"]["high"] == 2  # the two still open
    assert prod["avg_cycle_days"] is not None
    assert sum(w["count"] for w in prod["done_by_week"]) == 2


def test_overdue_counts_open_past_due_tasks(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    project = board(client, auth_headers)
    task_id = client.post(
        f"/api/projects/{project['id']}/tasks",
        json={
            "column_id": project["columns"][0]["id"],
            "title": "late",
            "due_on": "2020-01-01",
        },
        headers=auth_headers,
    ).json()["id"]

    assert client.get(OVERVIEW, headers=auth_headers).json()["productivity"]["overdue"] == 1

    finish_task(client, auth_headers, task_id)
    assert client.get(OVERVIEW, headers=auth_headers).json()["productivity"]["overdue"] == 0


def test_finance_monthly_trend(client: TestClient, auth_headers: dict[str, str]) -> None:
    account_id = client.post(
        "/api/finance/accounts",
        json={"name": "Checking", "starting_balance_cents": 0},
        headers=auth_headers,
    ).json()["id"]
    spend(client, auth_headers, account_id, 300_000, "2026-06-15", kind="income")
    spend(client, auth_headers, account_id, 100_000, "2026-06-20")
    spend(client, auth_headers, account_id, 50_000, "2026-07-05")

    data = client.get(
        f"{OVERVIEW}?from=2026-05-01&to=2026-08-01", headers=auth_headers
    ).json()
    by_month = {m["month"]: m for m in data["finance"]["by_month"]}
    assert by_month["2026-06"]["net_cents"] == 200_000
    assert by_month["2026-07"]["net_cents"] == -50_000


def test_learning_maturity_buckets(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    course = client.post(
        "/api/learning/courses", json={"title": "Go"}, headers=auth_headers
    ).json()
    cards = [
        client.post(
            f"/api/learning/courses/{course['id']}/flashcards",
            json={"front": f"q{i}", "back": f"a{i}"},
            headers=auth_headers,
        ).json()
        for i in range(3)
    ]
    # one review bumps a card off "new"
    client.post(
        f"/api/learning/flashcards/{cards[0]['id']}/review",
        json={"quality": 5},
        headers=auth_headers,
    )

    maturity = client.get(OVERVIEW, headers=auth_headers).json()["learning"]["maturity"]
    assert maturity["new"] == 2
    assert maturity["learning"] == 1
    assert maturity["mature"] == 0


def test_job_funnel(client: TestClient, auth_headers: dict[str, str]) -> None:
    for status_value in ["applied", "applied", "offer"]:
        client.post(
            "/api/job-tracker/applications",
            json={"company_name": "X", "role": "SWE", "status": status_value},
            headers=auth_headers,
        )
    job = client.get(OVERVIEW, headers=auth_headers).json()["job_search"]
    assert job["funnel"]["applied"] == 2
    assert job["funnel"]["offer"] == 1
    assert sum(w["count"] for w in job["applications_by_week"]) == 3


def test_range_validation(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.get(
        f"{OVERVIEW}?from=2026-06-01&to=2026-05-01", headers=auth_headers
    ).status_code == 422
    assert client.get(
        f"{OVERVIEW}?from=2020-01-01&to=2026-01-01", headers=auth_headers
    ).status_code == 422


def test_overview_is_user_scoped(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    project = board(client, alice)
    add_task(client, alice, project, "secret")

    assert client.get(OVERVIEW, headers=bob).json()["productivity"]["tasks_total"] == 0


def test_range_end_follows_the_users_timezone(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    from app.core import tz

    default_end = client.get(OVERVIEW, headers=auth_headers).json()["range"]["date_to"]
    assert default_end == tz.today("UTC").isoformat()

    client.patch(
        "/api/auth/me", json={"timezone": "Pacific/Kiritimati"}, headers=auth_headers
    )  # UTC+14
    shifted_end = client.get(OVERVIEW, headers=auth_headers).json()["range"]["date_to"]
    assert shifted_end == tz.today("Pacific/Kiritimati").isoformat()


def test_exports(client: TestClient, auth_headers: dict[str, str]) -> None:
    project = board(client, auth_headers)
    finish_task(client, auth_headers, add_task(client, auth_headers, project, "done one"))

    csv_resp = client.get("/api/analytics/export.csv", headers=auth_headers)
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"].startswith("text/csv")
    assert csv_resp.text.splitlines()[0] == "section,metric,value"

    pdf_resp = client.get("/api/analytics/export.pdf", headers=auth_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.content.startswith(b"%PDF")
