import os
import pytest

from app.services import storage


pytestmark = pytest.mark.skipunless(os.getenv("RUN_INTEGRATION") == "1", reason="Integration tests skipped by default")


def test_storage_integration_update_get():
    """Integration test for storage that requires a running Redis instance.

    This test is skipped by default. Set RUN_INTEGRATION=1 to enable.
    """
    # Use a unique user id to avoid clashing with other tests
    user_id = f"it-{os.getpid()}"
    # Clean state
    r = storage.get_redis()
    r.delete(f"user:{user_id}")

    storage.update_user_stats(user_id, 12.34)
    storage.update_global_stats(12.34)

    u = storage.get_user_stats(user_id)
    g = storage.get_global_stats()

    assert u["order_count"] >= 1
    assert u["total_spend"] >= 12.34
    assert g["total_revenue"] >= 12.34
