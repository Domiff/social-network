from fastapi import APIRouter, WebSocket

from src.auth.repository import get_user_repo
from src.chat.service import ChatService
from src.core.database import new_session
from src.auth.jwt import get_jwt


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.websocket("/{chat_id}/ws")
async def chat(ws: WebSocket, chat_id: int, token: str):
    payload = get_jwt().get_payload(token)

    async with new_session() as session:
        ws.scope["user"] = await get_user_repo(session).get_by_id(int(payload["sub"]))

    service = ChatService(ws)
    await service.run(str(chat_id))
