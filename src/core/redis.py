from datetime import timedelta
from functools import lru_cache
from typing import Any, AsyncIterator, Awaitable, Callable

from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
)

from src.core.config import settings
from src.core.logging import get_logger


class BaseRedis:
    def __init__(self, redis) -> None:
        self.redis: Redis = redis
        self.logger = get_logger(self.__class__.__name__)

    async def _do(
        self, func: Callable[..., Awaitable[Any] | Any], *args, **kwargs
    ) -> Any:
        operation = getattr(func, "__name__", repr(func))
        try:
            return await func(*args, **kwargs)
        except (RedisConnectionError, RedisTimeoutError) as e:
            self.logger.error(
                "Redis connection error", operation=operation, error=str(e)
            )
            raise
        except Exception as e:
            self.logger.error(
                "Redis operation failed", operation=operation, error=str(e)
            )
            raise


class RedisCache(BaseRedis):
    async def set(
        self, key: str, value, expire: int | timedelta = settings.redis.EXPIRE
    ) -> None:
        await self._do(self.redis.set, key, value, ex=expire)
        self.logger.info("redis_set", redis_key=key)

    async def get(self, key: str) -> str | bytes | None:
        value = await self._do(self.redis.get, key)
        if value:
            self.logger.info("redis_get", redis_key=key)
            return value
        return None

    async def expire(self, key: str) -> None:
        await self._do(self.redis.expire, key, settings.redis.EXPIRE)
        self.logger.info("redis_expire", redis_key=key)

    async def delete(self, key: str) -> None:
        await self._do(self.redis.delete, key)
        self.logger.info("redis_delete", redis_key=key)


class RedisPubSub(BaseRedis):
    def __init__(self, redis):
        super().__init__(redis)
        self.pubsub: PubSub = self.redis.pubsub(ignore_subscribe_messages=True)

    async def subscribe(self, channel: str) -> None:
        await self._do(self.pubsub.subscribe, channel)
        self.logger.info("User subscribe to channel", channel=channel)

    async def unsubscribe(self, channel: str) -> None:
        await self._do(self.pubsub.unsubscribe, channel)
        self.logger.info("User unsubscribe to channel", channel=channel)

    async def publish(self, channel: str, payload: str) -> None:
        await self._do(self.redis.publish, channel, payload)
        self.logger.info("User publish to channel", channel=channel)

    async def listen(self) -> AsyncIterator[dict]:
        try:
            async for message in self.pubsub.listen():
                yield message
        except (RedisConnectionError, RedisTimeoutError) as e:
            self.logger.error(
                "Redis connection error", operation="listen", error=str(e)
            )
            raise
        except Exception as e:
            self.logger.error(
                "Redis operation failed", operation="listen", error=str(e)
            )
            raise


def key_builder(prefix: str, key: str) -> str:
    return f"{prefix}:{key}"


@lru_cache
def get_redis() -> Redis:
    return Redis.from_url(
        settings.redis.REDIS_URL,
        max_connections=settings.redis.CONNECTION_POOL_MAXSIZE,
        decode_responses=True,
    )


def get_cache() -> RedisCache:
    return RedisCache(get_redis())


def get_pubsub() -> RedisPubSub:
    return RedisPubSub(get_redis())
