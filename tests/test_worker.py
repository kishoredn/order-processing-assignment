import json

from types import SimpleNamespace

from app.worker import run_worker_for_test


class FakeSQSClient:
    def __init__(self, messages):
        self._messages = messages
        self.deleted = []

    def get_queue_url(self, QueueName):
        return {"QueueUrl": "http://fake-queue"}

    def receive_message(self, QueueUrl, MaxNumberOfMessages, WaitTimeSeconds):
        if self._messages:
            m = self._messages.pop(0)
            return {"Messages": [m]}
        return {"Messages": []}

    def delete_message(self, QueueUrl, ReceiptHandle):
        self.deleted.append(ReceiptHandle)


def test_worker_processes_message(monkeypatch):
    messages = [{"ReceiptHandle": "r1", "Body": json.dumps({"user_id": "u1", "id": "o1", "order_value": 10.0})}]
    fake = FakeSQSClient(messages)

    def fake_boto_client(service_name, endpoint_url=None, region_name=None, aws_access_key_id=None, aws_secret_access_key=None):
        assert service_name == "sqs"
        return fake

    monkeypatch.setattr("app.worker.boto3.client", fake_boto_client)

    # monkeypatch processor to assert it's called
    called = {}

    def fake_process(order):
        called["order"] = order

    monkeypatch.setattr("app.worker.process_order", fake_process)

    # run worker for a small number of polls
    run_worker_for_test(max_polls=2)

    assert "order" in called
    assert fake.deleted == ["r1"]
