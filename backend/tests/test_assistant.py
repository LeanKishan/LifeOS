from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.services import assistant


def text_reply(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)], stop_reason="end_turn"
    )


def tool_call(name: str, tool_input: dict[str, Any], call_id: str = "t1") -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", name=name, input=tool_input, id=call_id)],
        stop_reason="tool_use",
    )


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    state: dict[str, Any] = {"script": [], "calls": []}

    class FakeMessages:
        def create(self, **kwargs: Any) -> SimpleNamespace:
            snapshot = {**kwargs, "messages": list(kwargs.get("messages", []))}
            state["calls"].append(snapshot)
            return state["script"].pop(0)  # type: ignore[no-any-return]

    class FakeClient:
        def __init__(self, api_key: str | None = None) -> None:
            self.messages = FakeMessages()

    monkeypatch.setattr(assistant, "Anthropic", FakeClient)
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "test-key")
    return state


def _user_id(client: TestClient, db_session: Session) -> int:
    client.post(
        "/api/auth/register", json={"email": "owner@example.com", "password": "password123"}
    )
    return int(
        db_session.scalars(select(User).where(User.email == "owner@example.com")).one().id
    )


# --------------------------------------------------------------------------- #
# The loop
# --------------------------------------------------------------------------- #
def test_plain_reply_passes_through(
    client: TestClient, db_session: Session, fake_llm: dict[str, Any]
) -> None:
    fake_llm["script"] = [text_reply("Hello from LifeOS.")]
    user_id = _user_id(client, db_session)

    result = assistant.run_chat(db_session, user_id, [{"role": "user", "content": "hi"}])
    assert result.reply == "Hello from LifeOS."
    assert result.tool_calls == []


def test_loop_runs_a_tool_then_answers(
    client: TestClient, db_session: Session, auth_headers: dict[str, str], fake_llm: dict[str, Any]
) -> None:
    board = client.post("/api/projects", json={"name": "Demo"}, headers=auth_headers).json()
    client.post(
        f"/api/projects/{board['id']}/tasks",
        json={"column_id": board["columns"][0]["id"], "title": "Ship it"},
        headers=auth_headers,
    )
    user_id = db_session.scalars(
        select(User).where(User.email == "owner@example.com")
    ).one().id

    fake_llm["script"] = [
        tool_call("list_projects", {}),
        text_reply("You have one project, Demo, with 1 task."),
    ]

    result = assistant.run_chat(
        db_session, int(user_id), [{"role": "user", "content": "what projects do I have?"}]
    )
    assert result.tool_calls == ["list_projects"]
    assert result.reply == "You have one project, Demo, with 1 task."

    # the tool result the model saw on the 2nd call
    second_call_messages = fake_llm["calls"][1]["messages"]
    tool_result_text = second_call_messages[-1]["content"][0]["content"]
    assert "Demo" in tool_result_text


def test_loop_gives_up_after_max_iterations(
    client: TestClient, db_session: Session, fake_llm: dict[str, Any]
) -> None:
    fake_llm["script"] = [
        tool_call("list_projects", {}) for _ in range(assistant.MAX_TOOL_ITERATIONS)
    ]
    user_id = _user_id(client, db_session)

    result = assistant.run_chat(db_session, user_id, [{"role": "user", "content": "loop"}])
    assert len(result.tool_calls) == assistant.MAX_TOOL_ITERATIONS
    assert "narrower" in result.reply


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #
def test_create_task_tool_creates_the_task(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    client.post("/api/projects", json={"name": "Roadmap"}, headers=auth_headers)
    user_id = db_session.scalars(
        select(User).where(User.email == "owner@example.com")
    ).one().id

    out = assistant.execute_tool(
        db_session, int(user_id), "create_task", {"project": "roadmap", "title": "M10"}
    )
    assert "created_task_id" in json.loads(out)

    board = client.get(
        "/api/projects/"
        f"{client.get('/api/projects', headers=auth_headers).json()[0]['id']}",
        headers=auth_headers,
    ).json()
    titles = [t["title"] for c in board["columns"] for t in c["tasks"]]
    assert "M10" in titles


def test_tool_errors_come_back_as_strings(db_session: Session) -> None:
    out = assistant.execute_tool(db_session, 999, "create_task", {"project": "ghost", "title": "x"})
    assert out.startswith("error:")
    assert "ghost" in out


# --------------------------------------------------------------------------- #
# Endpoint
# --------------------------------------------------------------------------- #
def test_chat_endpoint_returns_reply(
    client: TestClient, auth_headers: dict[str, str], fake_llm: dict[str, Any]
) -> None:
    fake_llm["script"] = [text_reply("Sure thing.")]
    resp = client.post(
        "/api/coach/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["reply"] == "Sure thing."


def test_chat_endpoint_503_when_unconfigured(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/api/coach/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
        headers=auth_headers,
    )
    assert resp.status_code == 503
