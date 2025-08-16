import os
import sys
import time
import subprocess
import signal
import requests
import pytest


pytestmark = pytest.mark.skipunless(os.getenv("RUN_INTEGRATION") == "1", reason="E2E tests skipped by default")


def _start_worker():
	"""Start the worker as a subprocess and return the Popen object."""
	python = sys.executable
	cmd = [python, "-u", "app/worker.py"]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	return proc


def _populate_sqs(valid=5, invalid=2):
	python = sys.executable
	cmd = [python, "scripts/populate_sqs.py", "--valid", str(valid), "--invalid", str(invalid)]
	subprocess.check_call(cmd)


def test_e2e_flow():
	"""End-to-end test: start worker, publish messages, wait for processing, assert stats."""
	api_port = int(os.getenv("API_PORT", 8000))
	api_url = f"http://localhost:{api_port}"

	# Start worker
	worker = _start_worker()
	try:
		# Give worker a moment to start and establish queue
		time.sleep(2)

		# Publish test messages
		_populate_sqs(valid=5, invalid=2)

		# Poll the API until we see the expected number of processed orders
		timeout = 60
		deadline = time.time() + timeout
		total_orders = 0
		while time.time() < deadline:
			try:
				resp = requests.get(f"{api_url}/stats/global", timeout=3)
				resp.raise_for_status()
				data = resp.json()
				total_orders = int(data.get("total_orders", 0))
				if total_orders >= 5:
					break
			except Exception:
				# service not ready yet
				pass
			time.sleep(1)

		assert total_orders >= 5, f"expected >=5 processed orders, got {total_orders}"

	finally:
		# Teardown worker process
		if worker.poll() is None:
			try:
				worker.terminate()
				worker.wait(timeout=5)
			except Exception:
				worker.kill()
