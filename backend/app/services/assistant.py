from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.core import tz
from app.core.config import get_settings
from app.models.user import User
from app.schemas.calendar import EventCreate
from app.schemas.finance import FinanceSummary
from app.schemas.learning import FlashcardCreate
from app.schemas.projects import TaskCreate
from app.services import calendar as calendar_svc
from app.services import finance as finance_svc
from app.services import learning as learning_svc
from app.services import projects as projects_svc

MAX_TOOL_ITERATIONS = 6
GAVE_UP = "I made several tool calls but couldn't wrap up — try asking something narrower."

SYSTEM_PROMPT = (
    "You are the assistant inside LifeOS, a personal management app. The user's "
    "data lives behind the tools you've been given: an agenda (tasks + calendar), "
    "a finance summary, projects, and flashcards. Prefer calling a tool over "
    "guessing. When the user asks you to add or schedule something, use the "
    "write tools and then confirm what you did in one or two sentences. Keep "
    "replies short and concrete. Today's date is {today}."
)

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_agenda",
        "description": (
            "Tasks due and calendar events over the next N days, plus how many "
            "flashcards are due."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"days": {"type": "integer", "minimum": 1, "maximum": 60}},
        },
    },
    {
        "name": "get_finance_summary",
        "description": (
            "Income, expenses, net, savings rate and per-category spend for a "
            "month (YYYY-MM, default: current)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"month": {"type": "string", "pattern": "^\\d{4}-\\d{2}$"}},
        },
    },
    {
        "name": "list_projects",
        "description": "The user's projects and how many tasks each has.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "create_task",
        "description": "Add a task to a project (matched by name) in its first column.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "title": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "due_on": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
            },
            "required": ["project", "title"],
        },
    },
    {
        "name": "create_event",
        "description": (
            "Add a calendar event. Times are ISO 8601 with a UTC offset, "
            "e.g. 2026-09-01T14:00:00Z."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start_at": {"type": "string"},
                "end_at": {"type": "string"},
            },
            "required": ["title", "start_at", "end_at"],
        },
    },
    {
        "name": "add_flashcard",
        "description": "Add a flashcard (front/back) to a course, matched by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "course": {"type": "string"},
                "front": {"type": "string"},
                "back": {"type": "string"},
            },
            "required": ["course", "front", "back"],
        },
    },
]


class AssistantNotConfigured(RuntimeError):
    """No Anthropic API key is set."""


@dataclass
class ChatResult:
    reply: str
    tool_calls: list[str] = field(default_factory=list)


def _client() -> Anthropic:
    key = get_settings().anthropic_api_key
    if not key:
        raise AssistantNotConfigured
    return Anthropic(api_key=key)


def ensure_configured() -> None:
    """Raise ``AssistantNotConfigured`` now, before a stream response has started."""
    _client()


def _base_params(tz_name: str = "UTC") -> dict[str, Any]:
    settings = get_settings()
    return {
        "model": settings.assistant_model,
        "max_tokens": 8192,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "medium"},
        "system": SYSTEM_PROMPT.format(today=tz.today(tz_name).isoformat()),
        "tools": TOOLS,
    }


def _user_tz(db: Session, user_id: int) -> str:
    user = db.get(User, user_id)
    return user.timezone if user else "UTC"


# --------------------------------------------------------------------------- #
# Tool implementations (all user-scoped, all returning a string for the model)
# --------------------------------------------------------------------------- #
def _find_project(db: Session, user_id: int, name: str) -> Any:
    wanted = name.strip().lower()
    for project in projects_svc.list_projects(db, user_id, include_archived=True):
        if project.name.lower() == wanted:
            return projects_svc.get_project(db, user_id, project.id)
    raise LookupError(f"no project named {name!r}")


def _find_course(db: Session, user_id: int, name: str) -> Any:
    wanted = name.strip().lower()
    for course in learning_svc.list_courses(db, user_id, include_archived=True):
        if course.title.lower() == wanted:
            return learning_svc.get_course(db, user_id, course.id)
    raise LookupError(f"no course named {name!r}")


def _tool_get_agenda(db: Session, user_id: int, args: dict[str, Any]) -> str:
    days = int(args.get("days", 7))
    now = datetime.now(UTC).replace(tzinfo=None)
    occurrences = calendar_svc.expand_occurrences(db, user_id, now, now + timedelta(days=days))
    events = [
        {"title": o.title, "start": o.start_at.isoformat()} for o in occurrences[:25]
    ]

    tasks: list[dict[str, Any]] = []
    horizon = date.today() + timedelta(days=days)
    for project in projects_svc.list_projects(db, user_id):
        board = projects_svc.get_board(db, user_id, project.id)
        if board is None:
            continue
        for column in board.columns:
            for task in column.tasks:
                if task.due_on is not None and task.due_on <= horizon:
                    tasks.append(
                        {
                            "project": project.name,
                            "title": task.title,
                            "due_on": task.due_on.isoformat(),
                        }
                    )

    cards_due = len(learning_svc.review_queue(db, user_id))
    return json.dumps({"events": events, "tasks_due": tasks, "flashcards_due": cards_due})


def _tool_get_finance_summary(db: Session, user_id: int, args: dict[str, Any]) -> str:
    month = args.get("month") or datetime.now(UTC).strftime("%Y-%m")
    summary: FinanceSummary = finance_svc.summarize(db, user_id, month)
    return summary.model_dump_json()


def _tool_list_projects(db: Session, user_id: int, _args: dict[str, Any]) -> str:
    rows = [
        {"name": p.name, "tasks": p.task_count, "archived": p.archived}
        for p in projects_svc.list_projects(db, user_id, include_archived=True)
    ]
    return json.dumps(rows)


def _tool_create_task(db: Session, user_id: int, args: dict[str, Any]) -> str:
    project = _find_project(db, user_id, args["project"])
    board = projects_svc.get_board(db, user_id, project.id)
    if board is None or not board.columns:
        raise LookupError("that project has no columns")
    payload = TaskCreate(
        column_id=board.columns[0].id,
        title=args["title"],
        priority=args.get("priority", "medium"),
        due_on=date.fromisoformat(args["due_on"]) if args.get("due_on") else None,
    )
    task = projects_svc.create_task(db, user_id, board.columns[0], payload)
    return json.dumps({"created_task_id": task.id, "in_project": project.name})


def _tool_create_event(db: Session, user_id: int, args: dict[str, Any]) -> str:
    payload = EventCreate(
        title=args["title"],
        start_at=datetime.fromisoformat(args["start_at"].replace("Z", "+00:00")),
        end_at=datetime.fromisoformat(args["end_at"].replace("Z", "+00:00")),
    )
    event = calendar_svc.create_event(db, user_id, payload)
    return json.dumps({"created_event_id": event.id})


def _tool_add_flashcard(db: Session, user_id: int, args: dict[str, Any]) -> str:
    course = _find_course(db, user_id, args["course"])
    card = learning_svc.create_flashcard(
        db,
        user_id,
        course,
        FlashcardCreate(front=args["front"], back=args["back"]),
        date.today(),
    )
    return json.dumps({"created_flashcard_id": card.id, "in_course": course.title})


_DISPATCH = {
    "get_agenda": _tool_get_agenda,
    "get_finance_summary": _tool_get_finance_summary,
    "list_projects": _tool_list_projects,
    "create_task": _tool_create_task,
    "create_event": _tool_create_event,
    "add_flashcard": _tool_add_flashcard,
}


def execute_tool(db: Session, user_id: int, name: str, args: dict[str, Any]) -> str:
    handler = _DISPATCH.get(name)
    if handler is None:
        return f"error: unknown tool {name!r}"
    try:
        return handler(db, user_id, args)
    except (LookupError, ValueError, KeyError) as exc:
        return f"error: {exc}"


# --------------------------------------------------------------------------- #
# The agentic loop
# --------------------------------------------------------------------------- #
def run_chat(db: Session, user_id: int, messages: list[dict[str, Any]]) -> ChatResult:
    client = _client()
    conversation: list[dict[str, Any]] = list(messages)
    tool_calls: list[str] = []
    params = _base_params(_user_tz(db, user_id))

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(**{**params, "messages": conversation})
        conversation.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            reply = "".join(
                block.text for block in response.content if block.type == "text"
            )
            return ChatResult(reply=reply.strip(), tool_calls=tool_calls)

        results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_calls.append(block.name)
            output = execute_tool(
                db, user_id, block.name, cast("dict[str, Any]", block.input)
            )
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": output.startswith("error:"),
                }
            )
        conversation.append({"role": "user", "content": results})

    return ChatResult(reply=GAVE_UP, tool_calls=tool_calls)


def run_chat_stream(
    db: Session, user_id: int, messages: list[dict[str, Any]]
) -> Iterator[dict[str, Any]]:
    """Same agentic loop as ``run_chat``, but yields events as they happen:

    ``{"type": "delta", "text": ...}``   assistant text, token by token
    ``{"type": "tool", "name": ...}``    a tool is about to run
    ``{"type": "done", "tool_calls": [...]}``
    """
    client = _client()
    conversation: list[dict[str, Any]] = list(messages)
    tool_calls: list[str] = []
    params = _base_params(_user_tz(db, user_id))

    for _ in range(MAX_TOOL_ITERATIONS):
        with client.messages.stream(**{**params, "messages": conversation}) as stream:
            for text in stream.text_stream:
                yield {"type": "delta", "text": text}
            final = stream.get_final_message()

        conversation.append({"role": "assistant", "content": final.content})

        if final.stop_reason != "tool_use":
            yield {"type": "done", "tool_calls": tool_calls}
            return

        results: list[dict[str, Any]] = []
        for block in final.content:
            if block.type != "tool_use":
                continue
            tool_calls.append(block.name)
            yield {"type": "tool", "name": block.name}
            output = execute_tool(
                db, user_id, block.name, cast("dict[str, Any]", block.input)
            )
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": output.startswith("error:"),
                }
            )
        conversation.append({"role": "user", "content": results})

    yield {"type": "delta", "text": GAVE_UP}
    yield {"type": "done", "tool_calls": tool_calls}

