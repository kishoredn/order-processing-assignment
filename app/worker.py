import json
import time
import boto3
import logging
from botocore.exceptions import ClientError

from app.config import settings
from app.services.processor import process_order

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_or_create_queue_url(sqs_client, queue_name):
    """
    Retrieves the URL of an SQS queue, creating it if it doesn't exist.
    """
    try:
        response = sqs_client.get_queue_url(QueueName=queue_name)
        logging.info(f"Queue '{queue_name}' found at URL: {response['QueueUrl']}")
        return response['QueueUrl']
    except ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            logging.warning(f"Queue '{queue_name}' not found. Creating it...")
            response = sqs_client.create_queue(QueueName=queue_name)
            logging.info(f"Queue '{queue_name}' created at URL: {response['QueueUrl']}")
            return response['QueueUrl']
        else:
            logging.error("Failed to get or create queue.", exc_info=True)
            raise

def run_worker():
    """
    Main worker function to poll SQS and process messages.
    """
    logging.info("Starting SQS worker...")
    sqs = boto3.client(
        "sqs",
        endpoint_url=settings.aws_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key
    )

    try:
        queue_url = get_or_create_queue_url(sqs, settings.sqs_queue_name)
    except ClientError:
        logging.error("Could not connect to SQS. Exiting.")
        return

    logging.info(f"Worker polling queue: {settings.sqs_queue_name}")
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                AttributeNames=['All']
            )

            messages = response.get("Messages", [])
            if not messages:
                # No messages, continue polling
                continue

            logging.info(f"Received {len(messages)} messages.")

            for msg in messages:
                receipt_handle = msg['ReceiptHandle']
                try:
                    body = json.loads(msg['Body'])
                    logging.info(f"Processing order_id: {body.get('order_id', 'N/A')}")
                    process_order(body)
                    # If processing is successful, delete the message
                    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                    logging.info(f"Successfully processed and deleted message for order_id: {body.get('order_id', 'N/A')}")
                except json.JSONDecodeError:
                    logging.error(f"Invalid JSON in message body. Message will be retried. Body: {msg['Body']}")
                    # Don't delete, let it become visible again for manual inspection/retry
                except Exception as e:
                    logging.error(f"Error processing message: {e}", exc_info=True)
                    # Let the message reappear for another attempt.
                    # The processor.py already logs invalid orders to Redis.
                    pass

        except ClientError as e:
            logging.error(f"SQS client error: {e}", exc_info=True)
            # Sleep before retrying to avoid overwhelming the service on connection issues
            time.sleep(5)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)
            time.sleep(5)


if __name__ == "__main__":
    run_worker()

def run_worker_for_test(max_polls: int):
    """
    Test helper to run the worker for a limited number of polls.
    """
    for _ in range(max_polls):
        run_worker()
