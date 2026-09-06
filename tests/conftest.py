import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.auth.depends import get_current_user
from src.auth.repository import get_user_repo
from src.auth.service import AuthService, get_auth_service
from src.chat.repositories import (
    get_chat_member_repository,
    get_chat_repository,
    get_message_repository,
)
from src.core.database import Base, get_session
from src.core.setup import create_app
from tests.factories import make_user_schema

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    url=TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="session")
async def async_engine():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(async_engine):
    async_session = async_sessionmaker(
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        bind=async_engine,
        class_=AsyncSession,
    )

    async with async_session() as session:
        yield session

    async with async_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
def user_repo(session):
    return get_user_repo(session)


@pytest.fixture
def chat_repo(session):
    return get_chat_repository(session)


@pytest.fixture
def message_repo(session):
    return get_message_repository(session)


@pytest.fixture
def member_repo(session):
    return get_chat_member_repository(session)


@pytest.fixture
def auth_service(session):
    return AuthService(session)


@pytest.fixture
async def client(session, auth_service):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    yield AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver")


@pytest.fixture
async def authorized_client(session, auth_service):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_current_user] = make_user_schema
    yield AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver")
