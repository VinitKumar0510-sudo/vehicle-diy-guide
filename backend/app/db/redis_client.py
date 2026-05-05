import ssl
import redis.asyncio as aioredis
from app.config import get_settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        # Upstash uses rediss:// (SSL) — ssl_cert_reqs=None skips cert verification
        # which is required for Upstash's managed Redis
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            ssl_context=ssl_context,
        )
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
