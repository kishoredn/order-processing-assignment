"""Minimal order processing implementation for scaffold.

This module provides a single function `process_order` that validates
and computes a simple total for an order dictionary.
"""
from typing import Dict, Any


def process_order(order: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and process a single order.

    Expected order shape:
      {
        "id": str,
        "items": [{"sku": str, "qty": int, "unit_price": float}, ...]
      }

    Returns a new dict with the original order fields and added:
      - subtotal: sum(qty * unit_price)
      - total: subtotal (placeholder for future taxes/fees)

    Raises ValueError for invalid inputs.
    """
    if not isinstance(order, dict):
        raise ValueError("order must be a dict")

    order_id = order.get("id")
    if not order_id:
        raise ValueError("order missing 'id'")

    items = order.get("items")
    if not isinstance(items, list):
        raise ValueError("order 'items' must be a list")

    subtotal = 0.0
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"item at index {i} must be a dict")
        qty = item.get("qty")
        unit_price = item.get("unit_price")
        if not isinstance(qty, int) or qty < 0:
            raise ValueError(f"item at index {i} has invalid 'qty'")
        if not (isinstance(unit_price, (int, float)) and unit_price >= 0):
            raise ValueError(f"item at index {i} has invalid 'unit_price'")
        subtotal += qty * float(unit_price)

    result = dict(order)
    result["subtotal"] = round(subtotal, 2)
    result["total"] = result["subtotal"]
    return result
