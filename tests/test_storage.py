import pytest
import redis
import json
import time

# Add project root to the Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import storage
from app.config import settings

# --- Test Fixture for Redis Client ---

@pytest.fixture(scope="module")
def redis_client():
    """
    Provides a Redis client for the test module.
    It flushes the test database before tests run.
    """
    # Use a separate test database number if possible, e.g., db=1
    client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=1, # Use a different DB for testing
        decode_responses=True
    )
    client.flushdb()
    yield client
    client.flushdb()

# --- Monkeypatch Redis Client in Storage Service ---

@pytest.fixture(autouse=True)
def patch_redis_client(monkeypatch, redis_client):
    """
    Monkeypatches the get_redis_client function in the storage service
    to return our test client. This runs for every test function.
    """
    def get_test_redis_client():
        return redis_client
    
    monkeypatch.setattr(storage, 'get_redis_client', get_test_redis_client)

# --- Test Cases ---

def test_update_and_get_user_stats(redis_client):
    """Test updating and retrieving statistics for a single user."""
    user_id = "test_user_1"
    
    # First update
    storage.update_user_stats(user_id, 100.50)
    stats = storage.get_user_stats(user_id)
    assert stats["order_count"] == 1
    assert stats["total_spend"] == 100.50
    
    # Second update
    storage.update_user_stats(user_id, 50.25)
    stats = storage.get_user_stats(user_id)
    assert stats["order_count"] == 2
    assert stats["total_spend"] == 150.75

def test_get_user_stats_non_existent():
    """Test retrieving stats for a user that does not exist."""
    stats = storage.get_user_stats("non_existent_user")
    assert stats["order_count"] == 0
    assert stats["total_spend"] == 0.0

def test_update_and_get_global_stats(redis_client):
    """Test updating and retrieving global statistics."""
    # First update
    storage.update_global_stats(250.75)
    stats = storage.get_global_stats()
    assert stats["total_orders"] == 1
    assert stats["total_revenue"] == 250.75
    
    # Second update
    storage.update_global_stats(100.00)
    stats = storage.get_global_stats()
    assert stats["total_orders"] == 2
    assert stats["total_revenue"] == 350.75

def test_get_global_stats_non_existent(redis_client):
    """Test retrieving global stats when none have been set."""
    # Clear any global stats from previous tests
    redis_client.delete(storage.GLOBAL_STATS_KEY)
    
    stats = storage.get_global_stats()
    assert stats["total_orders"] == 0
    assert stats["total_revenue"] == 0.0

def test_log_and_list_invalid_orders(redis_client):
    """Test logging an invalid order and retrieving the list."""
    order_data_1 = {"order_id": "invalid_1", "details": "missing_field"}
    reason_1 = "User ID is missing"
    
    order_data_2 = {"order_id": "invalid_2", "details": "bad_value"}
    reason_2 = "Order value mismatch"
    
    # Log two invalid orders
    storage.log_invalid_order(order_data_1, reason_1)
    # Wait a tiny bit to ensure timestamp is different
    time.sleep(0.01)
    storage.log_invalid_order(order_data_2, reason_2)
    
    # Retrieve the list of invalid orders
    invalid_list = storage.list_invalid_orders(limit=10)
    
    # Assertions
    assert len(invalid_list) == 2
    
    # Redis LPUSH prepends, so the last one in is the first one out
    assert invalid_list[0]["order"] == order_data_2
    assert invalid_list[0]["reason"] == reason_2
    assert "ts" in invalid_list[0]
    
    assert invalid_list[1]["order"] == order_data_1
    assert invalid_list[1]["reason"] == reason_1
    assert "ts" in invalid_list[1]

def test_list_invalid_orders_limit():
    """Test that the limit parameter is respected."""
    for i in range(5):
        storage.log_invalid_order({"order_id": f"lim_{i}"}, "limit test")
        
    invalid_list = storage.list_invalid_orders(limit=3)
    assert len(invalid_list) == 3
    # Check that it returns the most recent ones
    assert invalid_list[0]["order"]["order_id"] == "lim_4"
    assert invalid_list[1]["order"]["order_id"] == "lim_3"
    assert invalid_list[2]["order"]["order_id"] == "lim_2"