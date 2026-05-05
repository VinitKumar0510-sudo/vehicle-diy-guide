import ssl
from urllib.parse import urlparse
import redis.asyncio as aioredis
from app.config import get_settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        parsed = urlparse(settings.redis_url)
        _redis = aioredis.Redis(
            host=parsed.hostname,
            port=parsed.port or 6380,
            password=parsed.password,
            username=parsed.username or None,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            decode_responses=True,
        )
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
