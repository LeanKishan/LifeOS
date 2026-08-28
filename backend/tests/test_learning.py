from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.models.learning import Flashcard
from app.services import learning as svc

LEARN = "/api/learning"
AuthHeaderFactory = Callable[..., dict[str, str]]
TODAY = date(2026, 1, 1)


def new_card(**overrides: object) -> Flashcard:
    card = Flashcard(front="q", back="a", ease_factor=2.5, interval_days=0, repetitions=0)
    for key, value in overrides.items():
        setattr(card, key, value)
    return card


# --------------------------------------------------------------------------- #
# SM-2 algorithm (pure unit tests)
# --------------------------------------------------------------------------- #
def test_first_good_review_sets_interval_one() -> None:
    card = new_card()
    svc.apply_sm2(card, quality=5, today=TODAY)
    assert card.repetitions == 1
    assert card.interval_days == 1
    assert card.due_on == TODAY + timedelta(days=1)
    assert card.ease_factor > 2.5


def test_second_and_third_good_reviews_step_the_interval() -> None:
    card = new_card()
    svc.apply_sm2(card, quality=4, today=TODAY)  # -> interval 1, reps 1
    svc.apply_sm2(card, quality=4, today=TODAY)  # -> interval 6, reps 2
    assert card.interval_days == 6
    assert card.repetitions == 2

    ease_before = card.ease_factor
    svc.apply_sm2(card, quality=4, today=TODAY)  # -> interval round(6 * ease)
    assert card.repetitions == 3
    assert card.interval_days == round(6 * card.ease_factor)
    assert card.ease_factor == pytest.approx(ease_before, abs=0.001)  # quality 4 keeps ease


def test_failing_review_resets_repetitions_and_lowers_ease() -> None:
    card = new_card(repetitions=5, interval_days=40, ease_factor=2.6)
    svc.apply_sm2(card, quality=1, today=TODAY)
    assert card.repetitions == 0
    assert card.interval_days == 1
    assert card.due_on == TODAY + timedelta(days=1)
    assert card.ease_factor < 2.6


def test_ease_factor_never_drops_below_floor() -> None:
    card = new_card(ease_factor=1.35)
    for _ in range(5):
        svc.apply_sm2(card, quality=0, today=TODAY)
    assert card.ease_factor == svc.MIN_EASE


def test_invalid_quality_raises() -> None:
    with pytest.raises(ValueError, match="quality"):
        svc.apply_sm2(new_card(), quality=7, today=TODAY)


# --------------------------------------------------------------------------- #
# HTTP: review queue + endpoint
# --------------------------------------------------------------------------- #
def _course(client: TestClient, headers: dict[str, str], title: str = "Spanish") -> dict:
    resp = client.post(f"{LEARN}/courses", json={"title": title}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _card(client: TestClient, headers: dict[str, str], course_id: int) -> dict:
    resp = client.post(
        f"{LEARN}/courses/{course_id}/flashcards",
        json={"front": "hola", "back": "hello"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_new_cards_are_due_today_and_appear_in_the_queue(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    course = _course(client, auth_headers)
    _card(client, auth_headers, course["id"])
    queue = client.get(f"{LEARN}/review", headers=auth_headers).json()
    assert len(queue) == 1


def test_reviewing_a_card_pushes_it_out_of_the_queue(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    course = _course(client, auth_headers)
    card = _card(client, auth_headers, course["id"])

    reviewed = client.post(
        f"{LEARN}/flashcards/{card['id']}/review", json={"quality": 5}, headers=auth_headers
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["repetitions"] == 1

    assert client.get(f"{LEARN}/review", headers=auth_headers).json() == []


def test_review_rejects_bad_quality(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    course = _course(client, auth_headers)
    card = _card(client, auth_headers, course["id"])
    resp = client.post(
        f"{LEARN}/flashcards/{card['id']}/review", json={"quality": 9}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_review_queue_is_user_scoped(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    course = _course(client, alice)
    _card(client, alice, course["id"])
    assert client.get(f"{LEARN}/review", headers=bob).json() == []


# --------------------------------------------------------------------------- #
# HTTP: course progress
# --------------------------------------------------------------------------- #
def test_course_progress_tracks_completed_lessons(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    course = _course(client, auth_headers)
    lessons = [
        client.post(
            f"{LEARN}/courses/{course['id']}/lessons",
            json={"title": f"Lesson {i}"},
            headers=auth_headers,
        ).json()
        for i in range(4)
    ]

    detail = client.get(f"{LEARN}/courses/{course['id']}", headers=auth_headers).json()
    assert detail["lesson_count"] == 4
    assert detail["progress"] == 0.0

    for lesson in lessons[:2]:
        client.patch(
            f"{LEARN}/lessons/{lesson['id']}",
            json={"completed": True},
            headers=auth_headers,
        )

    detail = client.get(f"{LEARN}/courses/{course['id']}", headers=auth_headers).json()
    assert detail["lessons_completed"] == 2
    assert detail["progress"] == 0.5


def test_completing_a_lesson_stamps_a_date_then_clears_it(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    course = _course(client, auth_headers)
    lesson = client.post(
        f"{LEARN}/courses/{course['id']}/lessons",
        json={"title": "Intro"},
        headers=auth_headers,
    ).json()

    done = client.patch(
        f"{LEARN}/lessons/{lesson['id']}", json={"completed": True}, headers=auth_headers
    ).json()
    assert done["completed_on"] is not None

    undone = client.patch(
        f"{LEARN}/lessons/{lesson['id']}", json={"completed": False}, headers=auth_headers
    ).json()
    assert undone["completed_on"] is None


def test_course_reports_due_flashcard_count(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    course = _course(client, auth_headers)
    _card(client, auth_headers, course["id"])
    _card(client, auth_headers, course["id"])
    detail = client.get(f"{LEARN}/courses/{course['id']}", headers=auth_headers).json()
    assert detail["flashcards_due"] == 2


def test_lessons_reorder(client: TestClient, auth_headers: dict[str, str]) -> None:
    course = _course(client, auth_headers)
    made = [
        client.post(
            f"{LEARN}/courses/{course['id']}/lessons",
            json={"title": t},
            headers=auth_headers,
        ).json()
        for t in ["A", "B", "C"]
    ]
    client.post(
        f"{LEARN}/lessons/{made[2]['id']}/move", json={"position": 0}, headers=auth_headers
    )
    detail = client.get(f"{LEARN}/courses/{course['id']}", headers=auth_headers).json()
    assert [lesson["title"] for lesson in detail["lessons"]] == ["C", "A", "B"]


# --------------------------------------------------------------------------- #
# Ownership & cascade
# --------------------------------------------------------------------------- #
def test_other_user_cannot_touch_course(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    course = _course(client, alice)
    assert client.get(f"{LEARN}/courses/{course['id']}", headers=bob).status_code == 404


def test_delete_course_cascades(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    course = _course(client, auth_headers)
    _card(client, auth_headers, course["id"])
    lesson = client.post(
        f"{LEARN}/courses/{course['id']}/lessons", json={"title": "x"}, headers=auth_headers
    ).json()

    assert client.delete(f"{LEARN}/courses/{course['id']}", headers=auth_headers).status_code == 204

    gone_cards = client.get(f"{LEARN}/courses/{course['id']}/flashcards", headers=auth_headers)
    gone_lesson = client.patch(f"{LEARN}/lessons/{lesson['id']}", json={}, headers=auth_headers)
    assert gone_cards.status_code == 404
    assert gone_lesson.status_code == 404
    assert client.get(f"{LEARN}/review", headers=auth_headers).json() == []
