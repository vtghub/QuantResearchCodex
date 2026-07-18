from fastapi.testclient import TestClient
from quantresearch_api.main import create_app

client = TestClient(create_app())


def test_health_reports_live_trading_disabled_by_default() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["live_trading_enabled"] is False


def test_tenant_context_uses_headers() -> None:
    tenant_id = "00000000-0000-0000-0000-000000000001"
    workspace_id = "00000000-0000-0000-0000-000000000002"

    response = client.get(
        "/api/v1/identity/me",
        headers={
            "x-tenant-id": tenant_id,
            "x-workspace-id": workspace_id,
            "x-role": "researcher",
        },
    )

    assert response.status_code == 200
    assert response.json()["tenant_id"] == tenant_id
    assert response.json()["workspace_id"] == workspace_id
    assert response.json()["role"] == "researcher"


def test_strategy_list_is_lifecycle_scaffolded() -> None:
    response = client.get("/api/v1/strategies")

    assert response.status_code == 200
    assert response.json()[0]["lifecycle"] == "draft"
    assert response.json()[0]["live_enabled"] is False
