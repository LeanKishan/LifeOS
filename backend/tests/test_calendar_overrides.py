from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import AuthHeaderFactory
from tests.test_calendar import EVENTS, make_event, occ

WEEKLY = {
    "title": "Standup",
    "start_at": "2026-09-07T09:00:00Z",  # a Monday
    "end_at": "2026-09-07T09:30:00Z",
    "recurrence": "FREQ=WEEKLY;COUNT=4",
}
WINDOW = ("2026-09-01T00:00:00Z", "2026-10-05T00:00:00Z")


def _override(client: TestClient, headers: dict, event_id: int, body: dict) -> dict:
    resp = client.put(f"{EVENTS}/{event_id}/overrides", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_cancel_one_instance_removes_only_that_occurrence(
    client: TestClient, auth_headers: dict
) -> None:
    event = make_event(client, auth_headers, **WEEKLY)
    assert len(occ(client, auth_headers, *WINDOW)) == 4

    _override(
        client,
        auth_headers,
        event["id"],
        {"occurrence_start": "2026-09-14T09:00:00Z", "canceled": True},
    )

    starts = [o["start_at"] for o in occ(client, auth_headers, *WINDOW)]
    assert len(starts) == 3
    assert "2026-09-14T09:00:00+00:00" not in starts


def test_move_one_instance_changes_time_and_flags_it(
    client: TestClient, auth_headers: dict
) -> None:
    event = make_event(client, auth_headers, **WEEKLY)
    _override(
        client,
        auth_headers,
        event["id"],
        {
            "occurrence_start": "2026-09-21T09:00:00Z",
            "start_at": "2026-09-21T15:00:00Z",
            "end_at": "2026-09-21T16:00:00Z",
            "title": "Standup (moved)",
        },
    )

    moved = next(
        o
        for o in occ(client, auth_headers, *WINDOW)
        if o["occurrence_start"] == "2026-09-21T09:00:00+00:00"
    )
    assert moved["start_at"] == "2026-09-21T15:00:00+00:00"
    assert moved["end_at"] == "2026-09-21T16:00:00+00:00"
    assert moved["title"] == "Standup (moved)"
    assert moved["overridden"] is True


def test_override_is_idempotent_per_instance(client: TestClient, auth_headers: dict) -> None:
    event = make_event(client, auth_headers, **WEEKLY)
    body = {"occurrence_start": "2026-09-14T09:00:00Z", "title": "v1"}
    first = _override(client, auth_headers, event["id"], body)
    second = _override(client, auth_headers, event["id"], {**body, "title": "v2"})

    assert first["id"] == second["id"]
    assert second["title"] == "v2"
    listed = client.get(f"{EVENTS}/{event['id']}/overrides", headers=auth_headers).json()
    assert len(listed) == 1


def test_override_start_outside_window_is_pulled_in(
    client: TestClient, auth_headers: dict
) -> None:
    event = make_event(client, auth_headers, **WEEKLY)
    # 2026-09-28 instance normally sits in-window; move it to November (out of window)
    _override(
        client,
        auth_headers,
        event["id"],
        {
            "occurrence_start": "2026-09-28T09:00:00Z",
            "start_at": "2026-11-02T09:00:00Z",
            "end_at": "2026-11-02T09:30:00Z",
        },
    )
    sept = occ(client, auth_headers, "2026-09-01T00:00:00Z", "2026-10-05T00:00:00Z")
    assert all(o["occurrence_start"] != "2026-09-28T09:00:00+00:00" for o in sept)

    nov = occ(client, auth_headers, "2026-11-01T00:00:00Z", "2026-11-08T00:00:00Z")
    assert any(o["start_at"] == "2026-11-02T09:00:00+00:00" for o in nov)


def test_override_must_reference_a_real_instance(
    client: TestClient, auth_headers: dict
) -> None:
    event = make_event(client, auth_headers, **WEEKLY)
    resp = client.put(
        f"{EVENTS}/{event['id']}/overrides",
        json={"occurrence_start": "2026-09-08T09:00:00Z"},  # a Tuesday, not on the rule
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_deleting_an_override_reverts_the_instance(
    client: TestClient, auth_headers: dict
) -> None:
    event = make_event(client, auth_headers, **WEEKLY)
    created = _override(
        client,
        auth_headers,
        event["id"],
        {"occurrence_start": "2026-09-14T09:00:00Z", "canceled": True},
    )
    assert len(occ(client, auth_headers, *WINDOW)) == 3

    assert (
        client.delete(
            f"/api/calendar/overrides/{created['id']}", headers=auth_headers
        ).status_code
        == 204
    )
    assert len(occ(client, auth_headers, *WINDOW)) == 4


def test_overrides_are_user_scoped(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    event = make_event(client, alice, **WEEKLY)

    resp = client.put(
        f"{EVENTS}/{event['id']}/overrides",
        json={"occurrence_start": "2026-09-14T09:00:00Z", "canceled": True},
        headers=bob,
    )
    assert resp.status_code == 404
