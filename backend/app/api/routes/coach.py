from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession
from app.schemas.assistant import ChatRequest, ChatResponse
from app.services import assistant
from app.services.assistant import AssistantNotConfigured, run_chat

router = APIRouter(prefix="/coach", tags=["coach"])


def _messages(data: ChatRequest) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in data.messages]


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, user: CurrentUser, db: DbSession) -> ChatResponse:
    try:
        result = run_chat(db, user.id, _messages(data))
    except AssistantNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The assistant isn't configured on this server (no API key).",
        ) from exc
    return ChatResponse(reply=result.reply, tool_calls=result.tool_calls)


@router.post("/chat/stream")
def chat_stream(data: ChatRequest, user: CurrentUser, db: DbSession) -> StreamingResponse:
    """Server-sent events: `{"type": "delta"|"tool"|"done"|"error", ...}` per line."""
    try:
        assistant.ensure_configured()  # 503 before the stream body starts
    except AssistantNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The assistant isn't configured on this server (no API key).",
        ) from exc

    messages = _messages(data)

    def sse() -> Iterator[str]:
        try:
            for event in assistant.run_chat_stream(db, user.id, messages):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:  # noqa: BLE001 - surface a clean end to the client
            yield f'data: {json.dumps({"type": "error"})}\n\n'

    return StreamingResponse(
        sse(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
