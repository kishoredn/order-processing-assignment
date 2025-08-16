from app.services import storage
import math

def validate_order(order: dict) -> (bool, str | None):
    """
    Validates an order based on predefined rules.

    Args:
        order: A dictionary representing the order.

    Returns:
        A tuple containing a boolean indicating validity and a reason string if invalid.
    """
    # Rule 1: Check for required fields
    required_fields = ["user_id", "order_id", "order_value"]
    for field in required_fields:
        if field not in order:
            return False, f"Missing required field: {field}"

    # Rule 2: Check if order_value is a valid number
    order_value = order["order_value"]
    if not isinstance(order_value, (int, float)):
        return False, "order_value must be a number"

    # Rule 3: If 'items' are present, verify the total value
    if "items" in order and isinstance(order["items"], list):
        try:
            calculated_total = sum(
                item.get("quantity", 0) * item.get("price_per_unit", 0)
                for item in order["items"]
            )
            # Use a tolerance for floating-point comparisons
            if not math.isclose(calculated_total, order_value, rel_tol=1e-2):
                return False, f"Calculated total ({calculated_total}) does not match order_value ({order_value})"
        except (TypeError, KeyError):
            return False, "Invalid structure in 'items' list"

    return True, None


def process_order(order: dict):
    """
    Processes a single order.

    If the order is valid, its stats are updated in storage.
    If the order is invalid, it is logged.
    """
    is_valid, reason = validate_order(order)

    if is_valid:
        storage.update_user_stats(order["user_id"], order["order_value"])
        storage.update_global_stats(order["order_value"])
    else:
        storage.log_invalid_order(order, reason)
