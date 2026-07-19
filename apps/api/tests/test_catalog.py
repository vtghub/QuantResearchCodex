from fastapi.testclient import TestClient
from quantresearch_api.main import create_app

client = TestClient(create_app())


def _headers(role: str, tenant_suffix: str) -> dict[str, str]:
    return {
        "x-role": role,
        "x-tenant-id": f"00000000-0000-0000-0000-000000000{tenant_suffix}",
        "x-workspace-id": "00000000-0000-0000-0000-000000000002",
    }


def _dataset_payload(symbol: str = "SPY") -> dict[str, object]:
    return {
        "provider": "stooq",
        "symbols": [symbol],
        "asset_class": "etf",
        "storage_uri": f"memory://datasets/{symbol.lower()}",
        "storage_format": "parquet",
        "checksum": f"sha256:{symbol.lower()}",
        "row_count": 252,
        "entitlement": "free-first",
        "transform_version": "raw-v1",
    }


def test_researcher_can_create_and_list_dataset_manifest() -> None:
    headers = _headers("researcher", "201")

    created = client.post("/api/v1/data/manifests", json=_dataset_payload(), headers=headers)
    listed = client.get("/api/v1/data/manifests", headers=headers)
    catalog = client.get("/api/v1/data/catalog", headers=headers)

    assert created.status_code == 201
    assert created.json()["provider"] == "stooq"
    assert created.json()["storage_format"] == "parquet"
    assert listed.status_code == 200
    assert any(item["id"] == created.json()["id"] for item in listed.json())
    assert any(item["status"] == "manifested" for item in catalog.json())


def test_dataset_manifests_are_tenant_scoped() -> None:
    created = client.post(
        "/api/v1/data/manifests",
        json=_dataset_payload("QQQ"),
        headers=_headers("researcher", "202"),
    )
    other_tenant = client.get(
        "/api/v1/data/manifests",
        headers=_headers("researcher", "203"),
    )

    assert created.status_code == 201
    assert other_tenant.status_code == 200
    assert all(item["id"] != created.json()["id"] for item in other_tenant.json())


def test_viewer_cannot_create_dataset_manifest() -> None:
    response = client.post(
        "/api/v1/data/manifests",
        json=_dataset_payload("IWM"),
        headers=_headers("viewer", "204"),
    )

    assert response.status_code == 403


def test_researcher_can_create_artifact_version() -> None:
    headers = _headers("researcher", "205")

    created = client.post(
        "/api/v1/artifacts",
        json={
            "artifact_type": "backtest",
            "name": "Momentum Baseline",
            "version": "1.0.0",
            "source_run_id": "run-001",
            "storage_uri": "memory://artifacts/momentum-baseline",
            "checksum": "sha256:momentum-baseline",
            "metrics": {"sharpe": 1.2, "max_drawdown": -0.08},
        },
        headers=headers,
    )
    listed = client.get("/api/v1/artifacts", headers=headers)

    assert created.status_code == 201
    assert created.json()["artifact_type"] == "backtest"
    assert created.json()["version"] == "1.0.0"
    assert any(item["id"] == created.json()["id"] for item in listed.json())
