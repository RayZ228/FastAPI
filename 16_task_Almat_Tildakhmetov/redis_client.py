import aioredis
import asyncio
from config import settings
REDIS_URL = settings.REDIS_URL

redis = None

async def get_redis():
    global redis
    if redis is None:
        redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis

# monkey-patch aioredis for delete_pattern (helper)
async def delete_pattern(redis, pattern):
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)
aioredis.Redis.delete_pattern = delete_pattern
