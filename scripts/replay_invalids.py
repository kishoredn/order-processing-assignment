import argparse
import json
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.services import storage, processor
from app.config import settings
from app.logging import configure_logging, get_logger

# Ensure centralized logging is configured when running the script
configure_logging()
logger = get_logger(__name__)

def replay_invalid_orders(limit: int):
    """
    Pops a specified number of invalid orders from the Redis list
    and attempts to reprocess them.
    """
    logger.info("Attempting to replay up to %s invalid orders...", limit)
    
    # In a real application, you might want a more robust way to access the Redis client
    # without relying on the internal implementation of the storage service.
    client = storage.get_redis_client()
    
    reprocessed_count = 0
    for _ in range(limit):
        # RPOP pops and returns the last element of the list
        order_json = client.rpop(storage.INVALID_ORDERS_KEY)
        
        if order_json is None:
            logger.info("No more invalid orders to replay.")
            break
            
        try:
            log_entry = json.loads(order_json)
            order_data = log_entry.get("order", {})
            
            if not order_data:
                logger.warning("Skipping empty order entry: %s", log_entry)
                continue
            logger.info("Replaying order_id: %s", order_data.get('order_id', 'N/A'))
            processor.process_order(order_data)
            reprocessed_count += 1
            
        except json.JSONDecodeError:
            logger.error("Could not decode JSON for order: %s", order_json)
        except Exception as e:
            logger.exception("An error occurred while replaying order: %s", e)
            # Optionally, push it back to the invalid queue or a separate dead-letter queue
            # client.lpush(storage.INVALID_ORDERS_KEY, order_json)

    logger.info("Replay finished. Processed %s orders.", reprocessed_count)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay invalid orders from the Redis queue.")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="The maximum number of invalid orders to replay."
    )
    args = parser.parse_args()
    
    replay_invalid_orders(args.limit)