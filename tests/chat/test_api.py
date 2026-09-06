import pytest

from src.chat.enums import ChatRole
from src.chat.schemas import MessageIn
from tests.factories import make_chat, make_member, make_message


async def create_chat(client):
    response = await client.post("/chat", json=make_chat())
    return response.json()


@pytest.mark.parametrize(
    "data",
    [
        make_chat(),
        make_chat(),
        make_chat(),
    ],
)
async def test_create_chat(authorized_client, data):
    response = await authorized_client.post("/chat", json=data)

    assert response.status_code == 201
    assert response.json()["name"] == data["name"]


async def test_create_chat_unauthorized(client):
    response = await client.post("/chat", json=make_chat())

    assert response.status_code == 401


async def test_list_chats(authorized_client):
    await create_chat(authorized_client)

    response = await authorized_client.get("/chat")

    assert response.status_code == 200
    assert response.json()["total_count"] == 1


async def test_detail_chat(authorized_client):
    chat = await create_chat(authorized_client)

    response = await authorized_client.get(f"/chat/{chat['id']}")

    assert response.status_code == 200
    assert response.json()["messages"] == []


async def test_detail_chat_not_found(authorized_client):
    response = await authorized_client.get("/chat/999")

    assert response.status_code == 404


async def test_update_chat(authorized_client):
    chat = await create_chat(authorized_client)

    response = await authorized_client.patch(
        f"/chat/{chat['id']}", json={"name": "New name"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New name"


async def test_update_chat_not_found(authorized_client):
    response = await authorized_client.patch("/chat/999", json={"name": "New name"})

    assert response.status_code == 404


async def test_delete_chat(authorized_client):
    chat = await create_chat(authorized_client)

    response = await authorized_client.delete(f"/chat/{chat['id']}")

    assert response.status_code == 204
    assert (await authorized_client.get(f"/chat/{chat['id']}")).status_code == 404


async def test_delete_chat_not_found(authorized_client):
    response = await authorized_client.delete("/chat/999")

    assert response.status_code == 404


async def test_list_messages(authorized_client, message_repo):
    chat = await create_chat(authorized_client)
    await message_repo.create(chat_id=chat["id"], data=MessageIn(**make_message()))

    response = await authorized_client.get(f"/chat/{chat['id']}/messages")

    assert response.status_code == 200
    assert response.json()["total_count"] == 1


@pytest.mark.parametrize(
    "data",
    [
        make_member(user_id=1),
        make_member(user_id=2, role=ChatRole.ADMIN),
        make_member(user_id=3, role=ChatRole.OWNER),
    ],
)
async def test_add_member(authorized_client, data):
    chat = await create_chat(authorized_client)

    response = await authorized_client.post(f"/chat/{chat['id']}/members", json=data)

    assert response.status_code == 201
    assert response.json()["user_id"] == data["user_id"]


async def test_add_member_twice(authorized_client):
    chat = await create_chat(authorized_client)
    await authorized_client.post(f"/chat/{chat['id']}/members", json=make_member(user_id=1))

    response = await authorized_client.post(
        f"/chat/{chat['id']}/members", json=make_member(user_id=1)
    )

    assert response.status_code == 409


async def test_add_member_with_unknown_role(authorized_client):
    chat = await create_chat(authorized_client)

    response = await authorized_client.post(
        f"/chat/{chat['id']}/members", json={"user_id": 1, "role": "king"}
    )

    assert response.status_code == 422


async def test_list_members(authorized_client):
    chat = await create_chat(authorized_client)
    await authorized_client.post(f"/chat/{chat['id']}/members", json=make_member(user_id=1))
    await authorized_client.post(f"/chat/{chat['id']}/members", json=make_member(user_id=2))

    response = await authorized_client.get(f"/chat/{chat['id']}/members")

    assert response.status_code == 200
    assert response.json()["total_count"] == 2


async def test_detail_member(authorized_client):
    chat = await create_chat(authorized_client)
    await authorized_client.post(f"/chat/{chat['id']}/members", json=make_member(user_id=7))

    response = await authorized_client.get(f"/chat/{chat['id']}/members/7")

    assert response.status_code == 200
    assert response.json()["user_id"] == 7


async def test_detail_member_not_found(authorized_client):
    chat = await create_chat(authorized_client)

    response = await authorized_client.get(f"/chat/{chat['id']}/members/999")

    assert response.status_code == 404


async def test_update_member(authorized_client):
    chat = await create_chat(authorized_client)
    await authorized_client.post(f"/chat/{chat['id']}/members", json=make_member(user_id=7))

    response = await authorized_client.patch(
        f"/chat/{chat['id']}/members/7", json={"role": ChatRole.ADMIN}
    )

    assert response.status_code == 200
    assert response.json()["role"].lower() == ChatRole.ADMIN


async def test_update_member_not_found(authorized_client):
    chat = await create_chat(authorized_client)

    response = await authorized_client.patch(
        f"/chat/{chat['id']}/members/999", json={"role": ChatRole.ADMIN}
    )

    assert response.status_code == 404


async def test_delete_member(authorized_client):
    chat = await create_chat(authorized_client)
    await authorized_client.post(f"/chat/{chat['id']}/members", json=make_member(user_id=7))

    response = await authorized_client.delete(f"/chat/{chat['id']}/members/7")

    assert response.status_code == 204
    assert (
        await authorized_client.get(f"/chat/{chat['id']}/members/7")
    ).status_code == 404
