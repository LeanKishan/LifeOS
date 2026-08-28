from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

EVENTS = "/api/calendar/events"
OCCURRENCES = "/api/calendar/occurrences"

AuthHeaderFactory = Callable[..., dict[str, str]]


def make_event(
    client: TestClient, headers: dict[str, str], **overrides: object
) -> dict:
    payload: dict[str, object] = {
        "title": "Standup",
        "start_at": "2026-09-01T09:00:00Z",
        "end_at": "2026-09-01T09:30:00Z",
    }
    payload.update(overrides)
    resp = client.post(EVENTS, json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def occ(client: TestClient, headers: dict[str, str], frm: str, to: str) -> list[dict]:
    resp = client.get(f"{OCCURRENCES}?from={frm}&to={to}", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def test_requires_auth(client: TestClient) -> None:
    assert client.get(EVENTS).status_code == 401


def test_end_before_start_is_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.post(
        EVENTS,
        json={
            "title": "bad",
            "start_at": "2026-09-01T10:00:00Z",
            "end_at": "2026-09-01T09:00:00Z",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_bad_recurrence_rule_is_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.post(
        EVENTS,
        json={
            "title": "bad rule",
            "start_at": "2026-09-01T09:00:00Z",
            "end_at": "2026-09-01T09:30:00Z",
            "recurrence": "FREQ=NONSENSE;BYDAY=ZZ",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_cross_link_to_foreign_project_is_422(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    project = client.post("/api/projects", json={"name": "Alice"}, headers=alice).json()

    resp = client.post(
        EVENTS,
        json={
            "title": "review",
            "start_at": "2026-09-01T09:00:00Z",
            "end_at": "2026-09-01T10:00:00Z",
            "project_id": project["id"],
        },
        headers=bob,
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Occurrence expansion — single events
# --------------------------------------------------------------------------- #
def test_single_event_in_and_out_of_range(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    make_event(client, auth_headers)

    inside = occ(client, auth_headers, "2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z")
    assert len(inside) == 1
    assert inside[0]["is_recurring"] is False

    outside = occ(client, auth_headers, "2026-10-01T00:00:00Z", "2026-10-02T00:00:00Z")
    assert outside == []


def test_partial_overlap_is_included(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    make_event(
        client,
        auth_headers,
        start_at="2026-09-01T23:00:00Z",
        end_at="2026-09-02T01:00:00Z",
    )
    # window ends inside the event
    hits = occ(client, auth_headers, "2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z")
    assert len(hits) == 1


# --------------------------------------------------------------------------- #
# Occurrence expansion — recurring
# --------------------------------------------------------------------------- #
def test_weekly_recurrence_count(client: TestClient, auth_headers: dict[str, str]) -> None:
    make_event(client, auth_headers, recurrence="FREQ=WEEKLY;COUNT=4")
    hits = occ(client, auth_headers, "2026-09-01T00:00:00Z", "2026-10-15T00:00:00Z")
    assert len(hits) == 4
    starts = [h["start_at"][:10] for h in hits]
    assert starts == ["2026-09-01", "2026-09-08", "2026-09-15", "2026-09-22"]
    assert all(h["is_recurring"] for h in hits)


def test_recurrence_respects_until(client: TestClient, auth_headers: dict[str, str]) -> None:
    make_event(
        client, auth_headers, recurrence="FREQ=DAILY;UNTIL=20260905T090000Z"
    )
    hits = occ(client, auth_headers, "2026-09-01T00:00:00Z", "2026-09-30T00:00:00Z")
    assert [h["start_at"][:10] for h in hits] == [
        "2026-09-01",
        "2026-09-02",
        "2026-09-03",
        "2026-09-04",
        "2026-09-05",
    ]


def test_range_clips_recurrence_to_the_window(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    make_event(client, auth_headers, recurrence="FREQ=DAILY")
    hits = occ(client, auth_headers, "2026-09-10T00:00:00Z", "2026-09-13T00:00:00Z")
    assert [h["start_at"][:10] for h in hits] == ["2026-09-10", "2026-09-11", "2026-09-12"]


def test_occurrence_keeps_the_event_duration(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    make_event(
        client,
        auth_headers,
        start_at="2026-09-01T09:00:00Z",
        end_at="2026-09-01T10:30:00Z",
        recurrence="FREQ=WEEKLY;COUNT=2",
    )
    hits = occ(client, auth_headers, "2026-09-01T00:00:00Z", "2026-09-30T00:00:00Z")
    for hit in hits:
        assert hit["start_at"][11:16] == "09:00"
        assert hit["end_at"][11:16] == "10:30"


def test_occurrences_sorted_across_events(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    make_event(
        client, auth_headers, title="B",
        start_at="2026-09-01T15:00:00Z", end_at="2026-09-01T16:00:00Z",
    )
    make_event(
        client, auth_headers, title="A",
        start_at="2026-09-01T09:00:00Z", end_at="2026-09-01T10:00:00Z",
    )
    hits = occ(client, auth_headers, "2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z")
    assert [h["title"] for h in hits] == ["A", "B"]


def test_range_too_large_is_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    resp = client.get(
        f"{OCCURRENCES}?from=2026-01-01T00:00:00Z&to=2028-01-01T00:00:00Z",
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_occurrences_are_user_scoped(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    make_event(client, alice)
    assert occ(client, bob, "2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z") == []


# --------------------------------------------------------------------------- #
# Reminders
# --------------------------------------------------------------------------- #
def test_reminders_attach_and_detach(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    event = make_event(client, auth_headers)
    created = client.post(
        f"{EVENTS}/{event['id']}/reminders",
        json={"minutes_before": 15},
        headers=auth_headers,
    )
    assert created.status_code == 201
    reminder_id = created.json()["id"]

    detail = client.get(f"{EVENTS}/{event['id']}", headers=auth_headers).json()
    assert detail["reminders"][0]["minutes_before"] == 15

    assert (
        client.delete(f"/api/calendar/reminders/{reminder_id}", headers=auth_headers).status_code
        == 204
    )


def test_update_event_revalidates_times(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    event = make_event(client, auth_headers)
    resp = client.patch(
        f"{EVENTS}/{event['id']}",
        json={"end_at": "2026-08-01T00:00:00Z"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
