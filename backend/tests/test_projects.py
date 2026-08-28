from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

PROJECTS = "/api/projects"

AuthHeaderFactory = Callable[..., dict[str, str]]


def new_project(client: TestClient, headers: dict[str, str], name: str = "Portfolio") -> dict:
    resp = client.post(PROJECTS, json={"name": name}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def column_ids(board: dict) -> list[int]:
    return [column["id"] for column in board["columns"]]


def add_task(
    client: TestClient, headers: dict[str, str], project_id: int, column_id: int, title: str
) -> dict:
    resp = client.post(
        f"{PROJECTS}/{project_id}/tasks",
        json={"column_id": column_id, "title": title},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def board_of(client: TestClient, headers: dict[str, str], project_id: int) -> dict:
    resp = client.get(f"{PROJECTS}/{project_id}", headers=headers)
    assert resp.status_code == 200
    return resp.json()


def titles_in_column(board: dict, column_id: int) -> list[str]:
    column = next(c for c in board["columns"] if c["id"] == column_id)
    return [task["title"] for task in column["tasks"]]


# --------------------------------------------------------------------------- #
# Projects & default columns
# --------------------------------------------------------------------------- #
def test_requires_auth(client: TestClient) -> None:
    assert client.get(PROJECTS).status_code == 401


def test_new_project_gets_three_ordered_columns(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board = new_project(client, auth_headers)
    assert [column["name"] for column in board["columns"]] == ["To Do", "In Progress", "Done"]
    assert [column["position"] for column in board["columns"]] == [0, 1, 2]


def test_list_excludes_archived_by_default(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board = new_project(client, auth_headers, name="Old")
    client.patch(f"{PROJECTS}/{board['id']}", json={"archived": True}, headers=auth_headers)

    assert client.get(PROJECTS, headers=auth_headers).json() == []
    assert len(client.get(f"{PROJECTS}?archived=true", headers=auth_headers).json()) == 1


def test_project_list_reports_task_count(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board = new_project(client, auth_headers)
    add_task(client, auth_headers, board["id"], column_ids(board)[0], "A")
    add_task(client, auth_headers, board["id"], column_ids(board)[0], "B")

    listed = client.get(PROJECTS, headers=auth_headers).json()
    assert listed[0]["task_count"] == 2


# --------------------------------------------------------------------------- #
# Task ordering
# --------------------------------------------------------------------------- #
def test_new_tasks_append_with_dense_positions(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board = new_project(client, auth_headers)
    todo = column_ids(board)[0]
    for title in ["A", "B", "C"]:
        add_task(client, auth_headers, board["id"], todo, title)

    board = board_of(client, auth_headers, board["id"])
    tasks = next(c for c in board["columns"] if c["id"] == todo)["tasks"]
    assert [(t["title"], t["position"]) for t in tasks] == [("A", 0), ("B", 1), ("C", 2)]


def test_move_task_within_column_reorders(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board = new_project(client, auth_headers)
    todo = column_ids(board)[0]
    tasks = [add_task(client, auth_headers, board["id"], todo, t) for t in ["A", "B", "C"]]

    # move C (index 2) to the front
    resp = client.post(
        f"{PROJECTS}/tasks/{tasks[2]['id']}/move",
        json={"column_id": todo, "position": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    board = board_of(client, auth_headers, board["id"])
    assert titles_in_column(board, todo) == ["C", "A", "B"]


def test_move_task_across_columns_renumbers_both(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board = new_project(client, auth_headers)
    todo, doing = column_ids(board)[0], column_ids(board)[1]
    a = add_task(client, auth_headers, board["id"], todo, "A")
    b = add_task(client, auth_headers, board["id"], todo, "B")
    add_task(client, auth_headers, board["id"], doing, "X")

    client.post(
        f"{PROJECTS}/tasks/{a['id']}/move",
        json={"column_id": doing, "position": 0},
        headers=auth_headers,
    )

    board = board_of(client, auth_headers, board["id"])
    assert titles_in_column(board, todo) == ["B"]
    assert titles_in_column(board, doing) == ["A", "X"]
    remaining = next(c for c in board["columns"] if c["id"] == todo)["tasks"]
    assert remaining[0]["position"] == 0
    assert b["id"] == remaining[0]["id"]


def test_move_position_past_the_end_clamps(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board = new_project(client, auth_headers)
    todo = column_ids(board)[0]
    tasks = [add_task(client, auth_headers, board["id"], todo, t) for t in ["A", "B", "C"]]

    client.post(
        f"{PROJECTS}/tasks/{tasks[0]['id']}/move",
        json={"column_id": todo, "position": 99},
        headers=auth_headers,
    )
    board = board_of(client, auth_headers, board["id"])
    assert titles_in_column(board, todo) == ["B", "C", "A"]


def test_delete_task_closes_the_position_gap(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board = new_project(client, auth_headers)
    todo = column_ids(board)[0]
    tasks = [add_task(client, auth_headers, board["id"], todo, t) for t in ["A", "B", "C"]]

    client.delete(f"{PROJECTS}/tasks/{tasks[1]['id']}", headers=auth_headers)
    board = board_of(client, auth_headers, board["id"])
    remaining = next(c for c in board["columns"] if c["id"] == todo)["tasks"]
    assert [(t["title"], t["position"]) for t in remaining] == [("A", 0), ("C", 1)]


def test_move_task_to_column_in_another_project_is_422(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board_a = new_project(client, auth_headers, name="A")
    board_b = new_project(client, auth_headers, name="B")
    task = add_task(client, auth_headers, board_a["id"], column_ids(board_a)[0], "T")

    resp = client.post(
        f"{PROJECTS}/tasks/{task['id']}/move",
        json={"column_id": column_ids(board_b)[0], "position": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Columns
# --------------------------------------------------------------------------- #
def test_move_column_reorders(client: TestClient, auth_headers: dict[str, str]) -> None:
    board = new_project(client, auth_headers)
    done = column_ids(board)[2]
    client.post(
        f"{PROJECTS}/columns/{done}/move", json={"position": 0}, headers=auth_headers
    )
    board = board_of(client, auth_headers, board["id"])
    assert [c["name"] for c in board["columns"]] == ["Done", "To Do", "In Progress"]


# --------------------------------------------------------------------------- #
# Subtasks, labels, comments
# --------------------------------------------------------------------------- #
def test_subtask_toggle_updates_card_counts(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board = new_project(client, auth_headers)
    task = add_task(client, auth_headers, board["id"], column_ids(board)[0], "T")

    s1 = client.post(
        f"{PROJECTS}/tasks/{task['id']}/subtasks", json={"title": "step 1"}, headers=auth_headers
    ).json()
    client.post(
        f"{PROJECTS}/tasks/{task['id']}/subtasks", json={"title": "step 2"}, headers=auth_headers
    )
    client.patch(
        f"{PROJECTS}/subtasks/{s1['id']}", json={"done": True}, headers=auth_headers
    )

    detail = client.get(f"{PROJECTS}/tasks/{task['id']}", headers=auth_headers).json()
    assert detail["subtask_total"] == 2
    assert detail["subtask_done"] == 1


def test_set_task_labels_replaces_and_rejects_foreign_labels(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board_a = new_project(client, auth_headers, name="A")
    board_b = new_project(client, auth_headers, name="B")
    task = add_task(client, auth_headers, board_a["id"], column_ids(board_a)[0], "T")

    label_a = client.post(
        f"{PROJECTS}/{board_a['id']}/labels", json={"name": "bug"}, headers=auth_headers
    ).json()
    label_b = client.post(
        f"{PROJECTS}/{board_b['id']}/labels", json={"name": "chore"}, headers=auth_headers
    ).json()

    ok = client.put(
        f"{PROJECTS}/tasks/{task['id']}/labels",
        json={"label_ids": [label_a["id"]]},
        headers=auth_headers,
    )
    assert ok.status_code == 200
    assert [label["name"] for label in ok.json()["labels"]] == ["bug"]

    bad = client.put(
        f"{PROJECTS}/tasks/{task['id']}/labels",
        json={"label_ids": [label_b["id"]]},
        headers=auth_headers,
    )
    assert bad.status_code == 422


def test_comments_add_and_count(client: TestClient, auth_headers: dict[str, str]) -> None:
    board = new_project(client, auth_headers)
    task = add_task(client, auth_headers, board["id"], column_ids(board)[0], "T")
    client.post(
        f"{PROJECTS}/tasks/{task['id']}/comments", json={"body": "first"}, headers=auth_headers
    )
    detail = client.get(f"{PROJECTS}/tasks/{task['id']}", headers=auth_headers).json()
    assert detail["comment_count"] == 1
    assert detail["comments"][0]["body"] == "first"


# --------------------------------------------------------------------------- #
# Ownership & cascade
# --------------------------------------------------------------------------- #
def test_other_user_cannot_touch_project_or_task(
    client: TestClient, make_auth_headers: AuthHeaderFactory
) -> None:
    alice = make_auth_headers("alice@example.com")
    bob = make_auth_headers("bob@example.com")
    board = new_project(client, alice)
    task = add_task(client, alice, board["id"], column_ids(board)[0], "secret")

    assert client.get(f"{PROJECTS}/{board['id']}", headers=bob).status_code == 404
    assert client.get(f"{PROJECTS}/tasks/{task['id']}", headers=bob).status_code == 404
    assert (
        client.post(
            f"{PROJECTS}/tasks/{task['id']}/move",
            json={"column_id": column_ids(board)[1], "position": 0},
            headers=bob,
        ).status_code
        == 404
    )


def test_delete_project_cascades(client: TestClient, auth_headers: dict[str, str]) -> None:
    board = new_project(client, auth_headers)
    task = add_task(client, auth_headers, board["id"], column_ids(board)[0], "T")

    assert client.delete(f"{PROJECTS}/{board['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"{PROJECTS}/{board['id']}", headers=auth_headers).status_code == 404
    assert client.get(f"{PROJECTS}/tasks/{task['id']}", headers=auth_headers).status_code == 404
