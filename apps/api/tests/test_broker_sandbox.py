from uuid import UUID

from fastapi.testclient import TestClient
from quantresearch_api.main import create_app

client = TestClient(create_app())


def _paper_order(client_order_id: str = "paper-order-0001") -> dict[str, object]:
    return {
        "strategy_id": str(UUID("00000000-0000-0000-0000-000000000003")),
        "symbol": "SPY",
        "asset_class": "etf",
        "venue": "ARCX",
        "currency": "USD",
        "timezone": "America/New_York",
        "side": "buy",
        "quantity": 10,
        "order_type": "market",
        "estimated_price": 500,
        "client_order_id": client_order_id,
        "mode": "paper",
    }


def test_trader_can_submit_paper_order() -> None:
    response = client.post(
        "/api/v1/brokers/alpaca/paper/orders",
        json=_paper_order(),
        headers={"x-role": "trader"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["broker"] == "alpaca"
    assert body["status"] == "accepted-paper"
    assert body["estimated_notional"] == 5000
    assert "mode-paper" in body["gates"]
    assert "live-disabled" in body["gates"]


def test_duplicate_paper_order_replays_existing_result() -> None:
    order = _paper_order("paper-order-0002")

    first = client.post(
        "/api/v1/brokers/interactive-brokers/paper/orders",
        json=order,
        headers={"x-role": "trader"},
    )
    second = client.post(
        "/api/v1/brokers/interactive-brokers/paper/orders",
        json=order,
        headers={"x-role": "trader"},
    )

    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["status"] == first.json()["status"]
    assert "idempotency-replay" in second.json()["gates"]


def test_viewer_cannot_submit_paper_order() -> None:
    response = client.post(
        "/api/v1/brokers/alpaca/paper/orders",
        json=_paper_order("paper-order-0003"),
        headers={"x-role": "viewer"},
    )

    assert response.status_code == 403


def test_live_mode_is_blocked_by_sandbox_gate() -> None:
    order = _paper_order("paper-order-0004")
    order["mode"] = "live"

    response = client.post(
        "/api/v1/brokers/alpaca/paper/orders",
        json=order,
        headers={"x-role": "trader"},
    )

    assert response.status_code == 403
    assert "Live orders are blocked" in response.json()["detail"]


def test_unknown_broker_is_rejected() -> None:
    response = client.post(
        "/api/v1/brokers/unknown/paper/orders",
        json=_paper_order("paper-order-0005"),
        headers={"x-role": "trader"},
    )

    assert response.status_code == 404


def test_paper_order_notional_limit_is_enforced() -> None:
    order = _paper_order("paper-order-0006")
    order["quantity"] = 1_000_000

    response = client.post(
        "/api/v1/brokers/alpaca/paper/orders",
        json=order,
        headers={"x-role": "trader"},
    )

    assert response.status_code == 422
    assert "notional exceeds" in response.json()["detail"]
