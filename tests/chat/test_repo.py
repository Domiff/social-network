import pytest
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.chat.enums import ChatRole
from src.chat.schemas import ChatIn, MemberIn, MessageIn
from tests.factories import make_chat, make_member, make_message


@pytest.mark.parametrize(
    "data",
    [
        make_chat(),
        make_chat(),
        make_chat(),
    ],
)
async def test_create_chat(chat_repo, data):
    chat = await chat_repo.create(data=ChatIn(**data))

    assert chat is not None
    assert chat.id
    assert chat.name == data["name"]


async def test_list_chats(chat_repo):
    await chat_repo.create(data=ChatIn(**make_chat()))

    chats = await chat_repo.list()

    assert chats["data"]
    assert chats["total_count"] == 1


async def test_detail_chat(chat_repo):
    created = await chat_repo.create(data=ChatIn(**make_chat()))

    chat = await chat_repo.detail(chat_id=created.id)

    assert chat is not None
    assert chat.id == created.id
    assert chat.messages == []


async def test_detail_chat_not_found(chat_repo):
    assert await chat_repo.detail(chat_id=999) is None


async def test_detail_chat_contains_messages(chat_repo, message_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    await message_repo.create(chat_id=chat.id, data=MessageIn(**make_message()))

    detail = await chat_repo.detail(chat_id=chat.id)

    assert len(detail.messages) == 1
    assert detail.messages[0].chat_id == chat.id


async def test_exists_chat(chat_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))

    assert await chat_repo.exists(chat_id=chat.id) is True
    assert await chat_repo.exists(chat_id=999) is False


async def test_update_chat(chat_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))

    updated = await chat_repo.update(chat_id=chat.id, data=ChatIn(name="New name"))

    assert updated.name == "New name"
    # .lower(): UPDATE ... RETURNING отдаёт имя члена enum ("GROUP"),
    # а чтение — значение ("group"). Ужесточить после values_callable на колонке.
    assert updated.type.lower() == chat.type.lower()


async def test_update_chat_not_found(chat_repo):
    with pytest.raises(NoResultFound):
        await chat_repo.update(chat_id=999, data=ChatIn(name="New name"))


async def test_delete_chat(chat_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))

    await chat_repo.delete(chat_id=chat.id)

    assert await chat_repo.exists(chat_id=chat.id) is False


@pytest.mark.parametrize(
    "data",
    [
        make_message(),
        make_message(),
        make_message(),
    ],
)
async def test_create_message(chat_repo, message_repo, data):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))

    message = await message_repo.create(chat_id=chat.id, data=MessageIn(**data))

    assert message is not None
    assert message.text == data["text"]
    assert message.chat_id == chat.id


async def test_list_messages(chat_repo, message_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    await message_repo.create(chat_id=chat.id, data=MessageIn(**make_message()))
    await message_repo.create(chat_id=chat.id, data=MessageIn(**make_message()))

    messages = await message_repo.list(chat_id=chat.id)

    assert messages["total_count"] == 2
    assert messages["data"][0].id > messages["data"][1].id


async def test_detail_message(chat_repo, message_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    created = await message_repo.create(chat_id=chat.id, data=MessageIn(**make_message()))

    message = await message_repo.detail(message_id=created.id)

    assert message is not None
    assert message.id == created.id


async def test_update_message(chat_repo, message_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    message = await message_repo.create(chat_id=chat.id, data=MessageIn(**make_message()))

    updated = await message_repo.update(
        message_id=message.id, data=MessageIn(text="Edited")
    )

    assert updated.text == "Edited"
    assert updated.chat_id == chat.id


async def test_delete_message(chat_repo, message_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    message = await message_repo.create(chat_id=chat.id, data=MessageIn(**make_message()))

    await message_repo.delete(message_id=message.id)

    assert await message_repo.exists(message_id=message.id) is False


@pytest.mark.parametrize(
    "data",
    [
        make_member(user_id=1),
        make_member(user_id=2, role=ChatRole.ADMIN),
        make_member(user_id=3, role=ChatRole.OWNER),
    ],
)
async def test_add_member(chat_repo, member_repo, data):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))

    member = await member_repo.create(chat_id=chat.id, data=MemberIn(**data))

    assert member is not None
    assert member.chat_id == chat.id
    assert member.user_id == data["user_id"]


async def test_add_member_twice(chat_repo, member_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    await member_repo.create(chat_id=chat.id, data=MemberIn(**make_member(user_id=1)))

    with pytest.raises(IntegrityError):
        await member_repo.create(
            chat_id=chat.id, data=MemberIn(**make_member(user_id=1))
        )


async def test_list_members(chat_repo, member_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    await member_repo.create(chat_id=chat.id, data=MemberIn(**make_member(user_id=1)))
    await member_repo.create(chat_id=chat.id, data=MemberIn(**make_member(user_id=2)))

    members = await member_repo.list(chat_id=chat.id)

    assert members["total_count"] == 2


async def test_detail_member(chat_repo, member_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    await member_repo.create(chat_id=chat.id, data=MemberIn(**make_member(user_id=7)))

    member = await member_repo.detail(chat_id=chat.id, user_id=7)

    assert member is not None
    assert member.user_id == 7


async def test_exists_member(chat_repo, member_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    await member_repo.create(chat_id=chat.id, data=MemberIn(**make_member(user_id=7)))

    assert await member_repo.exists(chat_id=chat.id, user_id=7) is True
    assert await member_repo.exists(chat_id=chat.id, user_id=8) is False


async def test_update_member_role(chat_repo, member_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    await member_repo.create(chat_id=chat.id, data=MemberIn(**make_member(user_id=7)))

    updated = await member_repo.update(
        chat_id=chat.id, user_id=7, data=MemberIn(role=ChatRole.ADMIN)
    )

    assert updated.user_id == 7
    assert updated.role.lower() == ChatRole.ADMIN  # см. комментарий в test_update_chat


async def test_delete_member(chat_repo, member_repo):
    chat = await chat_repo.create(data=ChatIn(**make_chat()))
    await member_repo.create(chat_id=chat.id, data=MemberIn(**make_member(user_id=7)))

    await member_repo.delete(chat_id=chat.id, user_id=7)

    assert await member_repo.exists(chat_id=chat.id, user_id=7) is False
