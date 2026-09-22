from src.chat.enums import ChatRole
from src.core.schemas import BaseSchema, DateTimeSchema


class MessageIn(BaseSchema):
    text: str | None = None
    chat_id: int | None = None
    sender_id: int


class MessageOut(BaseSchema, DateTimeSchema):
    id: int
    text: str
    chat_id: int
    sender_id: int


class ChatIn(BaseSchema):
    type: str | None = None
    name: str | None = None


class ChatOut(BaseSchema, DateTimeSchema):
    id: int
    type: str
    name: str | None = None
    messages: list[MessageOut] = []


class MemberIn(BaseSchema):
    user_id: int | None = None
    chat_id: int | None = None
    role: ChatRole | None = None


class MemberOut(BaseSchema, DateTimeSchema):
    id: int
    chat_id: int
    user_id: int
    role: str
