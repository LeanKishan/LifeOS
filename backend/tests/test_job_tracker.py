from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

APPS = "/api/job-tracker/applications"
COMPANIES = "/api/job-tracker/companies"
CONTACTS = "/api/job-tracker/contacts"
STATS = "/api/job-tracker/stats"

AuthHeaderFactory = Callable[..., dict[str, str]]


def make_application(
    client: TestClient, headers: dict[str, str], **overrides: object
) -> dict[str, object]:
    payload: dict[str, object] = {"company_name": "Globex", "role": "SWE"}
    payload.update(overrides)
    resp = client.post(APPS, json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


# --------------------------------------------------------------------------- #
# Auth boundary
# --------------------------------------------------------------------------- #
def test_endpoints_require_auth(client: TestClient) -> None:
    assert client.get(APPS).status_code == 401
    assert client.get(STATS).status_code == 401


# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
def test_create_application_auto_creates_company(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    body = make_application(client, auth_headers, company_name="Initech", role="Backend Engineer")
    assert body["company"]["name"] == "Initech"
    assert body["status"] == "applied"
    assert body["interviews"] == []

    companies = client.get(COMPANIES, headers=auth_headers).json()
    assert [c["name"] for c in companies] == ["Initech"]


def test_create_application_reuses_company_by_name_case_insensitive(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    make_application(client, auth_headers, company_name="Acme")
    make_application(client, auth_headers, company_name="acme")
    assert len(client.get(COMPANIES, headers=auth_headers).json()) == 1


def test_create_application_requires_a_company_reference(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    resp = client.post(APPS, json={"role": "SWE"}, headers=auth_headers)
    assert resp.status_code == 422


def test_create_application_with_unknown_company_id_is_422(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    resp = client.post(APPS, json={"company_id": 999, "role": "SWE"}, headers=auth_headers)
    assert resp.status_code == 422


def test_list_is_scoped_to_the_owner(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    make_application(client, alice, company_name="AliceCorp")

    assert len(client.get(APPS, headers=alice).json()) == 1
    assert client.get(APPS, headers=bob).json() == []


def test_cannot_read_another_users_application(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    app_id = make_application(client, alice)["id"]

    assert client.get(f"{APPS}/{app_id}", headers=bob).status_code == 404
    assert client.patch(f"{APPS}/{app_id}", json={"role": "x"}, headers=bob).status_code == 404
    assert client.delete(f"{APPS}/{app_id}", headers=bob).status_code == 404


def test_patch_application_is_partial(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    body = make_application(client, auth_headers, role="SWE", source="LinkedIn")
    resp = client.patch(
        f"{APPS}/{body['id']}", json={"status": "interviewing"}, headers=auth_headers
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["status"] == "interviewing"
    assert updated["source"] == "LinkedIn"
    assert updated["role"] == "SWE"


def test_filter_by_status(client: TestClient, auth_headers: dict[str, str]) -> None:
    make_application(client, auth_headers, company_name="A", status="applied")
    make_application(client, auth_headers, company_name="B", status="offer")

    offers = client.get(f"{APPS}?status=offer", headers=auth_headers).json()
    assert [a["company"]["name"] for a in offers] == ["B"]


def test_delete_application_cascades_interviews(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    app_id = make_application(client, auth_headers)["id"]
    client.post(
        f"{APPS}/{app_id}/interviews", json={"kind": "phone"}, headers=auth_headers
    )
    assert client.delete(f"{APPS}/{app_id}", headers=auth_headers).status_code == 204
    assert client.get(f"{APPS}/{app_id}/interviews", headers=auth_headers).status_code == 404


# --------------------------------------------------------------------------- #
# Interviews
# --------------------------------------------------------------------------- #
def test_add_and_list_interviews(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    app_id = make_application(client, auth_headers)["id"]
    created = client.post(
        f"{APPS}/{app_id}/interviews",
        json={"kind": "technical", "outcome": "passed"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    assert created.json()["application_id"] == app_id

    listed = client.get(f"{APPS}/{app_id}/interviews", headers=auth_headers).json()
    assert [i["kind"] for i in listed] == ["technical"]


def test_cannot_add_interview_to_another_users_application(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    app_id = make_application(client, alice)["id"]

    resp = client.post(
        f"{APPS}/{app_id}/interviews", json={"kind": "phone"}, headers=bob
    )
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# Contacts
# --------------------------------------------------------------------------- #
def test_contact_crud(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        CONTACTS, json={"name": "Dana Scully", "role": "Recruiter"}, headers=auth_headers
    )
    assert created.status_code == 201
    contact_id = created.json()["id"]

    patched = client.patch(
        f"{CONTACTS}/{contact_id}", json={"email": "dana@fbi.gov"}, headers=auth_headers
    )
    assert patched.json()["email"] == "dana@fbi.gov"
    assert patched.json()["role"] == "Recruiter"

    assert client.delete(f"{CONTACTS}/{contact_id}", headers=auth_headers).status_code == 204
    assert client.get(f"{CONTACTS}/{contact_id}", headers=auth_headers).status_code == 404


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #
def test_stats_empty(client: TestClient, auth_headers: dict[str, str]) -> None:
    stats = client.get(STATS, headers=auth_headers).json()
    assert stats["total"] == 0
    assert stats["response_rate"] == 0.0
    assert stats["by_status"]["applied"] == 0


def test_stats_aggregates_by_status(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for status_value in ["applied", "applied", "interviewing", "offer", "rejected", "wishlist"]:
        make_application(client, auth_headers, company_name="C", status=status_value)

    stats = client.get(STATS, headers=auth_headers).json()
    assert stats["total"] == 6
    assert stats["by_status"]["applied"] == 2
    assert stats["active"] == 5  # 6 total - 1 rejected (only closed one here)
    assert stats["responded"] == 3  # interviewing + offer + rejected
    assert stats["offers"] == 1
    # submitted = 6 - 1 wishlist = 5; responded 3 / 5 = 0.6
    assert stats["response_rate"] == 0.6
