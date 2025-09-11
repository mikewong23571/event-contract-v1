"""
Contract tests for GET /api/v1/backtests (list)
"""
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def seed_backtest(strategy: str = "ensemble_v1") -> str:
    resp = client.post(
        "/api/v1/backtests",
        json={
            "strategy_name": strategy,
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "symbol": "BTCUSDT",
        },
    )
    assert resp.status_code == 202
    return resp.json()["backtest_id"]


def test_list_backtests_basic():
    id1 = seed_backtest("s1")
    id2 = seed_backtest("s2")

    resp = client.get("/api/v1/backtests")
    assert resp.status_code == 200
    payload = resp.json()
    assert "results" in payload and isinstance(payload["results"], list)
    ids = {item["backtest_id"] for item in payload["results"]}
    assert id1 in ids and id2 in ids


def test_list_backtests_filter_and_limit():
    seed_backtest("alpha")
    seed_backtest("alpha")
    seed_backtest("beta")

    # Filter by strategy_name
    resp = client.get("/api/v1/backtests?strategy_name=alpha")
    assert resp.status_code == 200
    items = resp.json()["results"]
    assert all(itm["strategy_name"] == "alpha" for itm in items)

    # Limit
    resp2 = client.get("/api/v1/backtests?limit=1")
    assert resp2.status_code == 200
    assert len(resp2.json()["results"]) == 1

