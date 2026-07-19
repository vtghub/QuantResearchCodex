from uuid import UUID

from fastapi.testclient import TestClient
from quantresearch_api.main import create_app

client = TestClient(create_app())


def _headers(role: str, tenant_suffix: str) -> dict[str, str]:
    return {
        "x-role": role,
        "x-tenant-id": f"00000000-0000-0000-0000-000000000{tenant_suffix}",
        "x-workspace-id": "00000000-0000-0000-0000-000000000002",
    }


def _paper_order(client_order_id: str) -> dict[str, object]:
    return {
        "strategy_id": str(UUID("00000000-0000-0000-0000-000000000003")),
        "symbol": "SPY",
        "asset_class": "etf",
        "venue": "ARCX",
        "currency": "USD",
        "timezone": "America/New_York",
        "side": "buy",
        "quantity": 1,
        "order_type": "market",
        "estimated_price": 500,
        "client_order_id": client_order_id,
        "mode": "paper",
    }


def test_risk_policies_are_tenant_scoped() -> None:
    response = client.get("/api/v1/risk/policies", headers=_headers("viewer", "101"))

    assert response.status_code == 200
    body = response.json()
    assert {policy["name"] for policy in body} == {
        "execution-kill-switch",
        "paper-notional-limit",
        "two-person-live-approval",
    }
    assert body[0]["tenant_id"] == "00000000-0000-0000-0000-000000000101"


def test_kill_switch_blocks_broker_orders() -> None:
    headers = _headers("trader", "102")

    enabled = client.post(
        "/api/v1/risk/kill-switch",
        json={"enabled": True, "reason": "testing execution halt"},
        headers=headers,
    )
    blocked = client.post(
        "/api/v1/brokers/alpaca/paper/orders",
        json=_paper_order("risk-order-0001"),
        headers=headers,
    )
    disabled = client.post(
        "/api/v1/risk/kill-switch",
        json={"enabled": False, "reason": "testing execution clear"},
        headers=headers,
    )

    assert enabled.status_code == 200
    assert enabled.json()["enabled"] is True
    assert blocked.status_code == 423
    assert "kill switch" in blocked.json()["detail"]
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False


def test_viewer_cannot_mutate_kill_switch() -> None:
    response = client.post(
        "/api/v1/risk/kill-switch",
        json={"enabled": True, "reason": "viewer should not mutate"},
        headers=_headers("viewer", "103"),
    )

    assert response.status_code == 403


def test_two_person_approval_flow() -> None:
    requested = client.post(
        "/api/v1/risk/approvals",
        json={
            "target_kind": "strategy",
            "target_id": "00000000-0000-0000-0000-000000000003",
            "reason": "approve paper to live promotion",
        },
        headers=_headers("trader", "104"),
    )

    assert requested.status_code == 201
    approval_id = requested.json()["id"]

    approved = client.post(
        f"/api/v1/risk/approvals/{approval_id}/approve",
        headers=_headers("platform_admin", "104"),
    )

    assert approved.status_code == 200
    assert approved.json()["record"]["status"] == "approved"
    assert approved.json()["record"]["approved_by"] == ["platform_admin"]
    assert "two-person-approval-satisfied" in approved.json()["gates"]


def test_requester_cannot_self_approve() -> None:
    headers = _headers("platform_admin", "105")
    requested = client.post(
        "/api/v1/risk/approvals",
        json={
            "target_kind": "strategy",
            "target_id": "00000000-0000-0000-0000-000000000003",
            "reason": "self approval should fail",
        },
        headers=headers,
    )

    assert requested.status_code == 201

    approved = client.post(
        f"/api/v1/risk/approvals/{requested.json()['id']}/approve",
        headers=headers,
    )

    assert approved.status_code == 409
