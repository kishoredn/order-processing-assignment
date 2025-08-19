import pytest
from unittest.mock import Mock, patch

# Add project root to the Python path to allow importing from 'app'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.processor import validate_order, process_order

# --- Test Cases for validate_order ---

def test_validate_order_valid():
    """Test a standard, valid order."""
    order = {
        "user_id": "user123",
        "order_id": "order456",
        "order_value": 50.00,
        "items": [
            {"item_id": "a", "quantity": 2, "price_per_unit": 25.00}
        ]
    }
    is_valid, reason = validate_order(order)
    assert is_valid
    assert reason is None

def test_validate_order_missing_required_field():
    """Test an order missing a required field like 'user_id'."""
    order = {
        "order_id": "order456",
        "order_value": 50.00
    }
    is_valid, reason = validate_order(order)
    assert not is_valid
    assert "Missing required field: user_id" in reason

def test_validate_order_invalid_order_value_type():
    """Test an order where 'order_value' is not a number."""
    order = {
        "user_id": "user123",
        "order_id": "order456",
        "order_value": "fifty-dollars"
    }
    is_valid, reason = validate_order(order)
    assert not is_valid
    assert "order_value must be a number" in reason

def test_validate_order_items_sum_mismatch():
    """Test an order where the sum of items does not match 'order_value'."""
    order = {
        "user_id": "user123",
        "order_id": "order456",
        "order_value": 55.00, # Mismatch
        "items": [
            {"item_id": "a", "quantity": 2, "price_per_unit": 25.00} # Sum is 50.00
        ]
    }
    is_valid, reason = validate_order(order)
    assert not is_valid
    assert "does not match order_value" in reason

def test_validate_order_items_sum_match_with_tolerance():
    """Test floating point comparison with a small tolerance."""
    order = {
        "user_id": "user123",
        "order_id": "order456",
        "order_value": 33.33,
        "items": [
            {"item_id": "a", "quantity": 1, "price_per_unit": 33.331}
        ]
    }
    is_valid, reason = validate_order(order)
    assert is_valid
    assert reason is None

def test_validate_order_invalid_item_structure():
    """Test an order with malformed items."""
    order = {
        "user_id": "user123",
        "order_id": "order456",
        "order_value": 50.00,
        "items": [
            {"item_id": "a", "qty": 2, "price": 25.00} # Wrong keys
        ]
    }
    is_valid, reason = validate_order(order)
    assert not is_valid
    assert "Calculated total (0) does not match order_value (50.0)" in reason

def test_validate_order_no_items_is_valid():
    """An order without an 'items' list is still considered valid if required fields are present."""
    order = {
        "user_id": "user123",
        "order_id": "order456",
        "order_value": 150.00
    }
    is_valid, reason = validate_order(order)
    assert is_valid
    assert reason is None

# --- Test Cases for process_order ---

@patch('app.services.processor.storage')
def test_process_order_valid_path(mock_storage):
    """Test that a valid order calls the correct storage functions."""
    valid_order = {
        "user_id": "user123",
        "order_id": "order456",
        "order_value": 75.50
    }
    
    process_order(valid_order)
    
    # Assert that storage functions for valid orders were called
    mock_storage.update_user_stats.assert_called_once_with("user123", 75.50)
    mock_storage.update_global_stats.assert_called_once_with(75.50)
    
    # Assert that the invalid order logger was NOT called
    mock_storage.log_invalid_order.assert_not_called()

@patch('app.services.processor.storage')
def test_process_order_invalid_path(mock_storage):
    """Test that an invalid order calls the invalid logging function."""
    invalid_order = {
        "order_id": "order789",
        "order_value": 100.00
        # Missing user_id
    }
    
    process_order(invalid_order)
    
    # Assert that the invalid order logger was called
    mock_storage.log_invalid_order.assert_called_once()
    # Grab the arguments it was called with
    args, kwargs = mock_storage.log_invalid_order.call_args
    assert args[0] == invalid_order
    assert "Missing required field: user_id" in args[1]
    
    # Assert that storage functions for valid orders were NOT called
    mock_storage.update_user_stats.assert_not_called()
    mock_storage.update_global_stats.assert_not_called()
