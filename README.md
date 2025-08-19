# Order Processing (local)

Lightweight local e-commerce order pipeline example.

What this repo contains
- FastAPI endpoints to expose user/global stats, leaderboards, and invalid orders.
- A worker that consumes order messages from SQS (Localstack) and processes them.
- Redis-only storage primitives for aggregates, leaderboards, and invalid message channel.
- Small unit tests and helper scripts to replay invalids / populate SQS.

Status (what's implemented)
- Config loader (`app/config.py`) with sensible defaults and `.env` support.
- Redis storage primitives (`app/services/storage.py`).
- Validation & processing logic (`app/services/processor.py`).
- FastAPI app and routes (`app/main.py`, `app/routes.py`) including POST `/orders/reprocess`.
- SQS worker (`app/worker.py`) and helper replay script (`scripts/replay_invalids.py`).
- Unit tests for processor and worker (mocked storage/boto3). Leaderboard logic with Redis ZSETs.

Prerequisites
- Python 3.11+
- Redis (for full integration)
- Localstack (optional, for local SQS)
- Recommended: create and activate a venv before installing dependencies

Environment variables (.env)
- AWS_ENDPOINT_URL=http://localhost:4566
- AWS_REGION=us-east-1
- AWS_ACCESS_KEY_ID=test
- AWS_SECRET_ACCESS_KEY=test
- SQS_QUEUE_NAME=orders
- REDIS_HOST=localhost
- REDIS_PORT=6379
- API_PORT=8000


Install dependencies

Windows (PowerShell):

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r .\requirements.txt
```

Notes for Windows
- `requirements.txt` uses `uvicorn` (without `[standard]`) to avoid native build failures for `httptools`.
- If you need `uvicorn[standard]` extras (faster server), install Visual C++ Build Tools first.

Run the API

```powershell
python -m uvicorn app.main:app --reload --port 8000
python .\app\main.py
```


Endpoints
- GET /users/{user_id}/stats -> { user_id, order_count, total_spend }
- GET /stats/global -> { total_orders, total_revenue }
- GET /orders/invalid?limit=50 -> list of recent invalid entries
- POST /orders/reprocess -> accept corrected order JSON and attempt to reprocess it
- GET /stats/top-users?by=spend&n=10&offset=0 -> Top-N users by spend (default n=10, max=100)
- GET /stats/top-users?by=orders&n=10&offset=0 -> Top-N users by order count (default n=10, max=100)
Leaderboard

- Leaderboards are implemented using Redis ZSETs:
	- `leaderboard:spend` ranks users by total spend
	- `leaderboard:orders` ranks users by order count
- Endpoints allow querying top-N users by spend or orders, with pagination support (offset).
- Leaderboards update automatically as new orders are processed.

Run the worker (consumes SQS)

```powershell
python .\app\worker.py
```

Populate SQS (example)
- A `scripts/populate_sqs.py` helper may exist; run it to create sample valid/invalid orders and send to SQS (requires Localstack).

Replay invalid orders

```powershell
python .\scripts\replay_invalids.py 10
```

Testing

- Unit tests (mocked) can run without Redis:

```powershell
python -m pytest tests/test_processor.py -q
python -m pytest tests/test_worker.py -q
```

- Storage tests require `redis` and a running Redis instance. To skip storage tests set:

```powershell
$env:SKIP_REDIS_TESTS = '1'
python -m pytest -q
```

Troubleshooting
- Import errors on startup usually mean dependencies are missing — run the pip install step above.
- On Windows, avoid `uvicorn[standard]` unless you have build tools installed; using plain `uvicorn` is simpler.

Docker / docker-compose
- This repo includes a `docker-compose.yml` in the plan; you can run Redis and Localstack together and run the app/worker in containers. Adjust compose file as needed.



