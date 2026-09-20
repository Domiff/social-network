from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR: Path = Path(__file__).parent.parent.parent


class AppSettings(BaseSettings):
    IS_DEBUG: bool = Field(default=True)
    IS_DOCKERIZED: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class DBSettings(AppSettings):
    SQLITE_URL: str = "sqlite+aiosqlite:///db.sqlite3"

    POSTGRES_DB: str = "POSTGRES_DB"
    POSTGRES_USER: str = "POSTGRES_USER"
    POSTGRES_PASSWORD: str = "POSTGRES_PASSWORD"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    def get_pg_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def model_post_init(self, __context) -> None:
        object.__setattr__(
            self,
            "DB_URL",
            self.get_pg_url() if self.IS_DOCKERIZED else self.SQLITE_URL,
        )


class CORSSettings(AppSettings):
    ALLOW_CREDENTIALS: bool
    ALLOW_ORIGINS: list[str]
    ALLOW_METHODS: list[str]


class AuthSettings(AppSettings):
    PRIVATE_KEY_PATH: Path = BASE_DIR / "keys" / "jwt-private.pem"
    PUBLIC_KEY_PATH: Path = BASE_DIR / "keys" / "jwt-public.pem"
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30


class HTTPSettings(AppSettings):
    TIMEOUT: float = 30.0
    CONNECT: float = 5.0
    MAX_CONNECTIONS: int = 100
    MAX_KEEPALIVE_CONNECTIONS: int = 20
    KEEPALIVE_EXPIRY: float = 30.0

    def model_post_init(self, __context) -> None:
        object.__setattr__(self, "VERIFY_SSL", False if self.IS_DEBUG else True)


class S3Settings(AppSettings):
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION: str
    S3_BUCKET: str


class AdminSettings(AppSettings):
    ADMIN_SECRET_KEY: str


class RedisSettings(AppSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CONNECTION_POOL_MAXSIZE: int = 10
    EXPIRE: int = 60 * 60

    def model_post_init(self, __context) -> None:
        object.__setattr__(
            self, "REDIS_HOST", "redis" if self.IS_DOCKERIZED else "localhost"
        )
        object.__setattr__(
            self,
            "REDIS_URL",
            f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}",
        )


class Settings(AppSettings):
    app: AppSettings = AppSettings()
    db: DBSettings = DBSettings()
    cors: CORSSettings = CORSSettings()
    auth: AuthSettings = AuthSettings()
    http: HTTPSettings = HTTPSettings()
    s3: S3Settings = S3Settings()
    admin: AdminSettings = AdminSettings()
    redis: RedisSettings = RedisSettings()


settings = Settings()
