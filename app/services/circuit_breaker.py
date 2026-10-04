# app/services/circuit_breaker.py
# We can build a simple, robust circuit breaker state manager using Redis. Redis will track whether our
# primary provider is currently "healthy" or "broken".

import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

CIRCUIT_KEY = "circuit:primary:status"
FAILURE_COUNT_KEY = "circuit:primary:failures"

async def is_circuit_open() -> bool:
    """Checks if the circuit breaker is OPEN (meaning primary is down)."""
    status = await redis_client.get(CIRCUIT_KEY)
    return status == "OPEN"

async def record_failure():
    """Records a failure. If failures reach 3, trip the circuit breaker for 60 seconds."""
    failures = await redis_client.incr(FAILURE_COUNT_KEY)
    if failures >= 3:
        print("🚨 CIRCUIT BREAKER TRIPPED! Switching to fallback provider for 60 seconds.")
        await redis_client.set(CIRCUIT_KEY, "OPEN", ex=60) # Trip for 60 seconds
        await redis_client.set(FAILURE_COUNT_KEY, 0)

async def record_success():
    """Resets failure counts on a successful request."""
    await redis_client.set(FAILURE_COUNT_KEY, 0)
    await redis_client.delete(CIRCUIT_KEY)