import time
import json
import logging
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize redis connection
try:
    import redis
    redis_client = redis.from_url(settings.redis_url, decode_responses=True) if settings.redis_url else None
except ImportError:
    redis_client = None

def check_rate_limit(key: str):
    """Stateless rate limiter using Redis."""
    if not redis_client:
        return

    try:
        now = int(time.time())
        minute = now // 60
        redis_key = f"rate_limit:{key}:{minute}"
        
        count = redis_client.incr(redis_key)
        if count == 1:
            redis_client.expire(redis_key, 60)
        
        if count > settings.rate_limit_per_minute:
            logger.warning(json.dumps({"event": "rate_limit_exceeded", "user": key}))
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                headers={"Retry-After": "60"},
            )
    except redis.RedisError as e:
        logger.error(json.dumps({"event": "redis_error_ratelimit", "error": str(e)}))
        # Allow pass if Redis fails to avoid breaking the app
        pass
