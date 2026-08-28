from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_token
from app.realtime.manager import manager
from app.services import users as user_service

router = APIRouter()


def _user_id_from_token(token: str) -> int | None:
    try:
        payload = decode_token(token, "access")
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.isdigit():
        return None
    return int(sub)


@router.websocket("/ws")
async def live_updates(
    websocket: WebSocket,
    token: str = Query(default=""),
    db: Session = Depends(get_db),
) -> None:
    """Push channel. The client authenticates with its access token in the query
    string (browsers can't set headers on a WebSocket) and then only receives.
    """
    user_id = _user_id_from_token(token)
    if user_id is None or user_service.get_by_id(db, user_id) is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user_id, websocket)
    await websocket.send_json({"type": "connected"})
    try:
        while True:
            await websocket.receive_text()  # client isn't expected to send; keeps it open
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
