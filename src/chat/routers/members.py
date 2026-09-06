from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastcrud.types import GetMultiResponseModel
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.auth.depends import get_current_user
from src.chat.repositories import ChatMemberRepository, get_chat_member_repository
from src.chat.schemas import MemberIn, MemberOut
from src.core.exceptions import AlreadyExists, DoesNotExists

router = APIRouter(
    prefix="/chat/{chat_id}/members",
    tags=["Chat"],
    dependencies=[Depends(get_current_user)],
)

ChatMemberRepositoryDep = Annotated[
    ChatMemberRepository, Depends(get_chat_member_repository)
]


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_member(
    chat_id: int,
    data: MemberIn,
    repo: ChatMemberRepositoryDep,
) -> MemberOut:
    try:
        return await repo.create(chat_id=chat_id, data=data)
    except IntegrityError as e:
        raise AlreadyExists("Member already exists") from e


@router.get("")
async def list_members(
    chat_id: int,
    repo: ChatMemberRepositoryDep,
) -> GetMultiResponseModel[MemberOut]:
    return await repo.list(chat_id=chat_id)


@router.get("/{user_id}")
async def detail_member(
    chat_id: int,
    user_id: int,
    repo: ChatMemberRepositoryDep,
) -> MemberOut:
    member = await repo.detail(chat_id=chat_id, user_id=user_id)
    if member is None:
        raise DoesNotExists("Member does not exist")
    return member


@router.patch("/{user_id}")
async def update_member(
    chat_id: int,
    user_id: int,
    data: MemberIn,
    repo: ChatMemberRepositoryDep,
) -> MemberOut | None:
    try:
        return await repo.update(chat_id=chat_id, user_id=user_id, data=data)
    except NoResultFound as e:
        raise DoesNotExists("Member does not exist") from e


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    chat_id: int,
    user_id: int,
    repo: ChatMemberRepositoryDep,
) -> None:
    if not await repo.exists(chat_id=chat_id, user_id=user_id):
        raise DoesNotExists("Member does not exist")
    await repo.delete(chat_id=chat_id, user_id=user_id)
