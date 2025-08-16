import redis
import json
from datetime import datetime
from app.config import settings

# --- Redis Client ---
# Use a connection pool for efficient connection management.
redis_pool = redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    decode_responses=True
)

def get_redis_client():
    """Returns a Redis client from the connection pool."""
    return redis.Redis(connection_pool=redis_pool)

# --- Constants for Redis Keys ---
USER_STATS_PREFIX = "user:"
GLOBAL_STATS_KEY = "global:stats"
INVALID_ORDERS_KEY = "invalid_orders"

# --- Storage Functions ---

def update_user_stats(user_id: str, order_value: float):
    """
    Updates the order count and total spend for a specific user.
    Uses Redis Hashes with HINCRBY and HINCRBYFLOAT.
    """
    client = get_redis_client()
    key = f"{USER_STATS_PREFIX}{user_id}"
    # Use a pipeline for atomic execution of the two commands.
    with client.pipeline() as pipe:
        pipe.hincrby(key, "order_count", 1)
        pipe.hincrbyfloat(key, "total_spend", order_value)
        pipe.execute()

def update_global_stats(order_value: float):
    """
    Updates the total number of orders and total revenue globally.
    Uses Redis Hashes with HINCRBY and HINCRBYFLOAT.
    """
    client = get_redis_client()
    with client.pipeline() as pipe:
        pipe.hincrby(GLOBAL_STATS_KEY, "total_orders", 1)
        pipe.hincrbyfloat(GLOBAL_STATS_KEY, "total_revenue", order_value)
        pipe.execute()

def get_user_stats(user_id: str) -> dict:
    """
    Retrieves the statistics for a given user.
    Returns a dictionary with zero values if the user does not exist.
    """
    client = get_redis_client()
    stats = client.hgetall(f"{USER_STATS_PREFIX}{user_id}")
    return {
        "order_count": int(stats.get("order_count", 0)),
        "total_spend": float(stats.get("total_spend", 0.0))
    }

def get_global_stats() -> dict:
    """
    Retrieves the global order and revenue statistics.
    Returns a dictionary with zero values if no stats are available.
    """
    client = get_redis_client()
    stats = client.hgetall(GLOBAL_STATS_KEY)
    return {
        "total_orders": int(stats.get("total_orders", 0)),
        "total_revenue": float(stats.get("total_revenue", 0.0))
    }

def log_invalid_order(order_data: dict, reason: str):
    """
    Logs an invalid order by pushing it to a Redis List as a JSON string.
    """
    client = get_redis_client()
    log_entry = {
        "order": order_data,
        "reason": reason,
        "ts": datetime.utcnow().isoformat(),
    }
    client.lpush(INVALID_ORDERS_KEY, json.dumps(log_entry))

def list_invalid_orders(limit: int = 50) -> list:
    """
    Retrieves a list of the most recent invalid orders.
    """
    client = get_redis_client()
    invalid_orders_json = client.lrange(INVALID_ORDERS_KEY, 0, limit - 1)
    return [json.loads(order) for order in invalid_orders_json]
