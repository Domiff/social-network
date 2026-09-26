import asyncio

from fastapi.websockets import WebSocketDisconnect, WebSocketState, WebSocket

from src.core.database import new_session
from src.core.redis import get_pubsub, RedisPubSub, get_cache, RedisCache, key_builder
from src.core.logging import get_logger
from src.chat.schemas import MemberIn, MessageIn
from src.chat.repositories import ChatMemberRepository, MessageRepository


class ChatService:
    CHAT_PREFIX = "chat"
    MEMBER_PREFIX = "member"

    def __init__(self, ws: WebSocket):
        self.ws: WebSocket = ws
        self.pubsub: RedisPubSub = get_pubsub()
        self.cache: RedisCache = get_cache()
        self.logger = get_logger("chat_service")

    async def connect(self):
        await self.ws.accept()

    async def disconnect(self):
        if self.ws.client_state is WebSocketState.CONNECTED:
            await self.ws.close()

    async def join(self, chat_id: int) -> None:
        user_id = self.ws.user.id
        async with new_session() as session:
            repo = ChatMemberRepository(session)
            member = await repo.detail(chat_id=chat_id, user_id=user_id)
            if member is None:
                member = await repo.create(
                    data=MemberIn(user_id=user_id, chat_id=chat_id)
                )
        await self.cache.set(
            key_builder(self.MEMBER_PREFIX, member.id),
            member.id,
        )
        await self.pubsub.subscribe(self._channel_builder(chat_id))

    async def leave(self, chat_id: int) -> None:
        user_id = self.ws.user.id
        async with new_session() as session:
            member = await ChatMemberRepository(session).detail(chat_id=chat_id, user_id=user_id)
            await ChatMemberRepository(session).delete(
                user_id=user_id,
                chat_id=chat_id,
            )
        if member is not None:
            await self.cache.delete(
                key_builder(self.MEMBER_PREFIX, member.id),
            )
        await self.pubsub.unsubscribe(self._channel_builder(chat_id))

    async def send(self, chat_id: int, text: str) -> None:
        user_id = self.ws.user.id
        async with new_session() as session:
            member = await ChatMemberRepository(session).detail(chat_id=chat_id, user_id=user_id)
            if member is None:
                self.logger.warning(
                    "Message dropped: user is not a chat member",
                    chat_id=chat_id,
                    user_id=user_id,
                )
                return
            message = MessageIn(
                text=text,
                chat_id=chat_id,
                sender_id=member.id,
            )
            await MessageRepository(session).create(data=message)
        await self.pubsub.publish(self._channel_builder(chat_id), text)

    async def run(self, chat_id: int) -> None:
        await self.connect()
        await self.join(chat_id)

        chat_task = asyncio.create_task(self._from_redis())
        try:
            while True:
                msg = await self.ws.receive_text()
                await self.send(chat_id=chat_id, text=msg)
        except WebSocketDisconnect:
            pass
        finally:
            chat_task.cancel()
            await self.leave(chat_id=chat_id)
            await self.pubsub.close()
            await self.disconnect()

    def _channel_builder(self, chat_id: int) -> str:
        return key_builder(self.CHAT_PREFIX, chat_id)

    async def _from_redis(self) -> None:
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                await self.ws.send_text(message["data"])
