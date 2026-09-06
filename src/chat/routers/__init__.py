from fastapi import APIRouter

from src.chat.routers.chats import router as chats_router
from src.chat.routers.members import router as members_router
from src.chat.routers.pages import router as pages_router

router = APIRouter()
router.include_router(chats_router)
router.include_router(members_router)
router.include_router(pages_router)
