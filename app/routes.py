from fastapi import APIRouter, Request, status
from app.services import storage, processor

router = APIRouter()

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
async def reprocess_order(request: Request):
    """
    Accepts a corrected order JSON and sends it for processing.
    """
    order_data = await request.json()
    processor.process_order(order_data)
    return {"status": "accepted", "message": "Order sent for reprocessing."}
