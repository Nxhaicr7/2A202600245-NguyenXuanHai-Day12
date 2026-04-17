import json
import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize redis connection
try:
    import redis
    redis_client = redis.from_url(settings.redis_url, decode_responses=True) if settings.redis_url else None
except ImportError:
    redis_client = None

def check_and_record_cost(input_tokens: int, output_tokens: int):
    """Stateless cost guard using Redis."""
    if not redis_client:
        return

    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        redis_key = f"daily_cost:{today}"
        
        current_cost = float(redis_client.get(redis_key) or 0)
        if current_cost >= settings.daily_budget_usd:
            logger.error(json.dumps({"event": "budget_exhausted", "cost": current_cost}))
            raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
        
        # Simple cost calc: $0.001 per 1k tokens
        new_cost = (input_tokens + output_tokens) * 0.000001
        redis_client.incrbyfloat(redis_key, new_cost)
        redis_client.expire(redis_key, 86400 * 2) # keep for 2 days
    except redis.RedisError as e:
        logger.error(json.dumps({"event": "redis_error_costguard", "error": str(e)}))
        pass
