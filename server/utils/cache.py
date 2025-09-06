from redis.asyncio import Redis
import os

async def get_redis() -> Redis:
    return Redis(
        host = os.getenv("REDIS_HOST", "localhost"),
        port = int(os.getenv("REDIS_PORT", 6379)),
        decode_responses = True,
        max_connections = 100
    )