from datetime import UTC, datetime

from faker import Faker

from src.auth.schemas import CredentialsSchema, UserSchema
from src.chat.enums import ChatRole, ChatType
from src.chat.schemas import ChatIn, MemberIn, MessageIn

_faker = Faker()


def make_credentials():
    return CredentialsSchema(
        username=_faker.user_name(),
        password=_faker.password(),
        email=_faker.email(),
    ).to_dict()


def make_sub():
    return _faker.random_int(1, 100)


def make_user_schema():
    return UserSchema(
        username=_faker.user_name(),
        password=_faker.password(),
        email=_faker.email(),
        first_name=_faker.first_name(),
        last_name=_faker.last_name(),
        is_active=True,
        created_at=datetime.now(UTC),
    )


def make_chat():
    return ChatIn(name=_faker.word(), type=ChatType.GROUP).to_dict()


def make_message():
    return MessageIn(text=_faker.sentence()).to_dict()


def make_member(user_id: int = 1, role: ChatRole = ChatRole.MEMBER):
    return MemberIn(user_id=user_id, role=role).to_dict()
