import os
import time
import pytest

import subprocess
import requests

pytestmark = pytest.mark.skipunless(os.getenv("RUN_INTEGRATION") == "1", reason="E2E tests skipped by default")


def test_e2e_flow():
    """Minimal end-to-end test that requires Localstack (SQS) and Redis running.

    This test is skipped by default. Set RUN_INTEGRATION=1 to enable.
    """
    # quick smoke: assume localstack provides SQS on AWS_ENDPOINT_URL
    # and the API is running on API_PORT
    api_port = int(os.getenv("API_PORT", 8000))
    api_url = f"http://localhost:{api_port}"

    # This test will be a very small smoke: check global stats endpoint exists
    resp = requests.get(f"{api_url}/stats/global", timeout=5)
    assert resp.status_code == 200
