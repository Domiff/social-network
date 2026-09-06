from fastcrud import FastCRUD, JoinConfig
from fastcrud.types import GetMultiResponseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.chat.models import Chat, ChatMember, Message
from src.chat.schemas import (
    ChatIn,
    ChatOut,
    MemberIn,
    MemberOut,
    MessageIn,
    MessageOut,
)
from src.core.database import BaseRepository, SessionDep


class ChatRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.chat_crud = FastCRUD(Chat)

    async def create(self, data: ChatIn) -> ChatOut:
        return await self.chat_crud.create(
            db=self.session,
            object=data,
            schema_to_select=ChatOut,
            return_as_model=True,
        )

    async def list(self) -> GetMultiResponseModel[ChatOut]:
        return await self.chat_crud.get_multi(
            db=self.session,
            sort_columns="id",
            sort_orders="desc",
            schema_to_select=ChatOut,
            return_as_model=True,
        )

    async def exists(self, chat_id: int) -> bool:
        return await self.chat_crud.exists(db=self.session, id=chat_id)

    async def detail(self, chat_id: int) -> ChatOut | None:
        return await self.chat_crud.get_joined(
            db=self.session,
            id=chat_id,
            schema_to_select=ChatOut,
            return_as_model=True,
            nest_joins=True,
            joins_config=[
                JoinConfig(
                    model=Message,
                    join_on=Message.chat_id == Chat.id,
                    join_prefix="messages_",
                    schema_to_select=MessageOut,
                    relationship_type="one-to-many",
                    sort_columns=["created_at", "id"],
                    sort_orders=["desc", "desc"],
                    nested_limit=50,
                ),
            ],
        )

    async def update(self, chat_id: int, data: ChatIn) -> ChatOut | None:
        return await self.chat_crud.update(
            db=self.session,
            object=data,
            schema_to_select=ChatOut,
            return_as_model=True,
            id=chat_id,
        )

    async def delete(self, chat_id: int) -> None:
        return await self.chat_crud.db_delete(
            db=self.session,
            id=chat_id,
        )


class MessageRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.message_crud = FastCRUD(Message)

    async def create(self, chat_id: int, data: MessageIn) -> MessageOut:
        return await self.message_crud.create(
            db=self.session,
            object=data.model_copy(update={"chat_id": chat_id}),
            schema_to_select=MessageOut,
            return_as_model=True,
        )

    async def list(self, chat_id: int) -> GetMultiResponseModel[MessageOut]:
        return await self.message_crud.get_multi(
            db=self.session,
            chat_id=chat_id,
            sort_columns="id",
            sort_orders="desc",
            schema_to_select=MessageOut,
            return_as_model=True,
        )

    async def detail(self, message_id: int) -> MessageOut | None:
        return await self.message_crud.get(
            db=self.session,
            id=message_id,
            schema_to_select=MessageOut,
            return_as_model=True,
        )

    async def exists(self, message_id: int) -> bool:
        return await self.message_crud.exists(db=self.session, id=message_id)

    async def update(self, message_id: int, data: MessageIn) -> MessageOut | None:
        return await self.message_crud.update(
            db=self.session,
            object=data,
            schema_to_select=MessageOut,
            return_as_model=True,
            id=message_id,
        )

    async def delete(self, message_id: int) -> None:
        return await self.message_crud.db_delete(
            db=self.session,
            id=message_id,
        )


class ChatMemberRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.chat_member_crud = FastCRUD(ChatMember)

    async def create(self, chat_id: int, data: MemberIn) -> MemberOut:
        return await self.chat_member_crud.create(
            db=self.session,
            object=data.model_copy(update={"chat_id": chat_id}),
            schema_to_select=MemberOut,
            return_as_model=True,
        )

    async def list(self, chat_id: int) -> GetMultiResponseModel[MemberOut]:
        return await self.chat_member_crud.get_multi(
            db=self.session,
            chat_id=chat_id,
            sort_columns="id",
            sort_orders="asc",
            schema_to_select=MemberOut,
            return_as_model=True,
        )

    async def detail(self, chat_id: int, user_id: int) -> MemberOut | None:
        return await self.chat_member_crud.get(
            db=self.session,
            chat_id=chat_id,
            user_id=user_id,
            schema_to_select=MemberOut,
            return_as_model=True,
        )

    async def exists(self, chat_id: int, user_id: int) -> bool:
        return await self.chat_member_crud.exists(
            db=self.session,
            chat_id=chat_id,
            user_id=user_id,
        )

    async def update(
        self, chat_id: int, user_id: int, data: MemberIn
    ) -> MemberOut | None:
        return await self.chat_member_crud.update(
            db=self.session,
            object=data,
            schema_to_select=MemberOut,
            return_as_model=True,
            chat_id=chat_id,
            user_id=user_id,
        )

    async def delete(self, chat_id: int, user_id: int) -> None:
        return await self.chat_member_crud.db_delete(
            db=self.session,
            chat_id=chat_id,
            user_id=user_id,
        )


def get_chat_repository(session: SessionDep) -> ChatRepository:
    return ChatRepository(session)


def get_message_repository(session: SessionDep) -> MessageRepository:
    return MessageRepository(session)


def get_chat_member_repository(session: SessionDep) -> ChatMemberRepository:
    return ChatMemberRepository(session)
