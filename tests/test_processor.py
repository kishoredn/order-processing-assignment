import pytest

from app.services import processor


def test_validate_order_missing_fields():
    valid, reason = processor.validate_order({})
    assert not valid
    assert reason == "Missing required field: user_id"


def test_validate_order_value_type():
    valid, reason = processor.validate_order({"user_id": "u1", "order_id": "o1", "order_value": "bad"})
    assert not valid
    assert reason == "order_value must be a number"


def test_validate_order_items_mismatch():
    order = {"user_id": "u1", "order_id": "o2", "order_value": 10.0, "items": [{"sku": "x", "quantity": 1, "price_per_unit": 5.0}]}
    valid, reason = processor.validate_order(order)
    assert not valid
    assert reason == "Calculated total (5.0) does not match order_value (10.0)"


def test_process_order_valid(monkeypatch):
    calls = {"user": 0, "global": 0}

    def fake_update_user_stats(user_id, order_value):
        calls["user"] += 1

    def fake_update_global_stats(order_value):
        calls["global"] += 1

    monkeypatch.setattr("app.services.storage.update_user_stats", fake_update_user_stats)
    monkeypatch.setattr("app.services.storage.update_global_stats", fake_update_global_stats)
    monkeypatch.setattr("app.services.storage.log_invalid_order", lambda o, r: (_ for _ in ()).throw(AssertionError("should not log invalid")))

    order = {"user_id": "u1", "order_id": "o3", "order_value": 15.0, "items": [{"sku": "a", "quantity": 3, "price_per_unit": 5.0}]}
    processor.process_order(order)

    assert calls["user"] == 1
    assert calls["global"] == 1


def test_process_order_invalid_logs(monkeypatch):
    logged = {}

    def fake_log(order, reason):
        logged["order"] = order
        logged["reason"] = reason

    monkeypatch.setattr("app.services.storage.log_invalid_order", fake_log)

    order = {"user_id": "u1", "order_id": "o4", "order_value": 10.0, "items": [{"sku": "a", "quantity": 1, "price_per_unit": 2.0}]}
    processor.process_order(order)

    assert logged["reason"] == "Calculated total (2.0) does not match order_value (10.0)"
    assert logged["order"]["order_id"] == "o4"
