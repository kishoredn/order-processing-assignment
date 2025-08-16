from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_global_stats_default(monkeypatch):
    # monkeypatch storage.get_global_stats to return zeros
    monkeypatch.setattr("app.services.storage.get_global_stats", lambda: {"total_orders": 0, "total_revenue": 0.0})
    r = client.get("/stats/global")
    assert r.status_code == 200
    assert r.json() == {"total_orders": 0, "total_revenue": 0.0}
