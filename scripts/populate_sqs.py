import argparse
import json
import random
from datetime import datetime
import uuid
import boto3
from botocore.exceptions import ClientError
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.logutil import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

def get_sqs_client():
    """Initializes and returns a boto3 SQS client."""
    return boto3.client(
        "sqs",
        endpoint_url=settings.aws_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key
    )

def get_or_create_queue_url(sqs_client, queue_name):
    """Gets the queue URL, creating the queue if it doesn't exist."""
    try:
        return sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
    except ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            logger.info("Queue '%s' not found, creating it...", queue_name)
            return sqs_client.create_queue(QueueName=queue_name)["QueueUrl"]
        else:
            raise

def generate_valid_order():
    """Generates a random, valid order with extra fields."""
    user_id = f"user_{random.randint(1, 100)}"
    order_id = str(uuid.uuid4())
    items = []
    order_value = 0
    for _ in range(random.randint(1, 5)):
        quantity = random.randint(1, 3)
        price_per_unit = round(random.uniform(10.0, 200.0), 2)
        item_total = quantity * price_per_unit
        items.append({
            "product_id": f"P{random.randint(1, 99):03d}",
            "quantity": quantity,
            "price_per_unit": price_per_unit
        })
        order_value += item_total

    # Add extra fields
    order = {
        "user_id": user_id,
        "order_id": order_id,
        "order_value": round(order_value, 2),
        "order_timestamp": datetime.utcnow().isoformat() + "Z",
        "items": items,
        "shipping_address": f"{random.randint(100,999)} Main St, Springfield",
        "payment_method": random.choice(["CreditCard", "PayPal", "BankTransfer"])
    }
    return order

def generate_invalid_order():
    """Generates a random, invalid order with extra fields."""
    order_type = random.choice(['missing_field', 'mismatch_value', 'bad_items'])
    order = generate_valid_order()

    if order_type == 'missing_field':
        if 'order_value' in order:
            del order['order_value']
    elif order_type == 'mismatch_value':
        order['order_value'] += 10.5
    elif order_type == 'bad_items':
        # Mess up the price of one item
        if order['items']:
            order['items'][0]['price_per_unit'] = "not_a_number"
    return order

def populate_queue(queue_url, num_valid, num_invalid):
    """Populates the SQS queue with a mix of valid and invalid orders."""
    sqs = get_sqs_client()
    messages = []
    
    logger.info("Generating %s valid orders...", num_valid)
    for _ in range(num_valid):
        messages.append(generate_valid_order())
        
    logger.info("Generating %s invalid orders...", num_invalid)
    for _ in range(num_invalid):
        messages.append(generate_invalid_order())
        
    random.shuffle(messages)
    
    logger.info("Sending %s messages to the queue: %s", len(messages), queue_url)
    
    sent_count = 0
    for msg in messages:
        try:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(msg)
            )
            sent_count += 1
        except ClientError as e:
            logger.error("Error sending message: %s", e)
            
    logger.info("Successfully sent %s messages.", sent_count)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate the SQS queue with sample order data.")
    parser.add_argument("--valid", type=int, default=50, help="Number of valid orders to generate.")
    parser.add_argument("--invalid", type=int, default=10, help="Number of invalid orders to generate.")
    args = parser.parse_args()

    try:
        client = get_sqs_client()
        q_url = get_or_create_queue_url(client, settings.sqs_queue_name)
        populate_queue(q_url, args.valid, args.invalid)
    except ClientError as e:
        logger.error("A client error occurred: %s", e)
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)