
from fastapi import APIRouter, status, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List
from app.services import storage, processor
from typing import Literal

router = APIRouter()

@router.get("/stats/top-users")
def top_users(by: Literal["spend","orders"] = Query("spend", description="Leaderboard type: spend or orders"),
              n: int = Query(10, ge=1, le=100, description="Number of users to return (max 100)"),
              offset: int = Query(0, ge=0, description="Offset for pagination")):
    """
    Get top-N users by spend or order count.
    """
    try:
        users = storage.get_top_users(by, n, offset)
        return {"by": by, "n": n, "offset": offset, "users": users}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Pydantic models for order
class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price_per_unit: float

class Order(BaseModel):
    order_id: str
    user_id: str
    order_timestamp: str
    order_value: float
    items: List[OrderItem]
    shipping_address: str
    payment_method: str

@router.get("/users/{user_id}/stats")
def user_stats(user_id: str):
    """
    Retrieves the order statistics for a specific user.
    """
    stats = storage.get_user_stats(user_id)
    return {"user_id": user_id, **stats}

@router.get("/stats/global")
def global_stats():
    """
    Retrieves the global order and revenue statistics.
    """
    return storage.get_global_stats()

@router.get("/orders/invalid")
def invalid_orders(limit: int = 50):
    """
    Lists the most recent invalid orders, with a configurable limit.
    """
    return storage.list_invalid_orders(limit=limit)


@router.post("/orders/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_order(order: Order):
    """
    Accepts a corrected order JSON and sends it for processing.
    """
    processor.process_order(order.dict())
    return {"status": "accepted", "message": "Order sent for reprocessing."}
