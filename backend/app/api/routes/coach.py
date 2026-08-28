from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.assistant import ChatRequest, ChatResponse
from app.services.assistant import AssistantNotConfigured, run_chat

router = APIRouter(prefix="/coach", tags=["coach"])


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, user: CurrentUser, db: DbSession) -> ChatResponse:
    messages = [{"role": m.role, "content": m.content} for m in data.messages]
    try:
        result = run_chat(db, user.id, messages)
    except AssistantNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The assistant isn't configured on this server (no API key).",
        ) from exc
    return ChatResponse(reply=result.reply, tool_calls=result.tool_calls)
