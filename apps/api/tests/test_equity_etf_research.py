from fastapi.testclient import TestClient
from quantresearch_api.equity_etf_research import EquityEtfResearchService
from quantresearch_api.main import create_app

client = TestClient(create_app())


class FakeDailyBarClient:
    def fetch_daily_bars(self, symbol: str, *, start: str, end: str):
        del start, end
        base = 100 if symbol.upper() == "SPY" else 80
        rows = [
            {
                "symbol": symbol.upper(),
                "date": f"2024-01-{day:02d}",
                "open": base + day - 1,
                "high": base + day,
                "low": base + day - 2,
                "close": base + day,
                "volume": 1000 + day,
            }
            for day in range(1, 80)
        ]
        return "stooq", rows


def test_equity_etf_research_service_runs_end_to_end() -> None:
    from quantresearch_api.schemas import EquityEtfResearchRequest, TenantContext

    response = EquityEtfResearchService(FakeDailyBarClient()).run(
        EquityEtfResearchRequest(
            symbols=["SPY", "QQQ"],
            start="20240101",
            end="20240430",
            fast_window=5,
            slow_window=20,
        ),
        TenantContext(),
    )

    assert response.asset_class == "equity_etf"
    assert response.data_vendors == ["stooq"]
    assert response.dataset_checksum.startswith("sha256:")
    assert response.data_profile[0].first_bar_date == "2024-01-01"
    assert response.raw_bars[0].symbol == "SPY"
    assert response.raw_bars[0].open == 100
    assert response.steps[0].name == "Fetch market data"
    assert response.decisions[0].area == "Data vendor"
    assert len(response.symbols_result) == 2
    assert round(sum(allocation.weight for allocation in response.allocations), 6) == 1.0


def test_equity_etf_research_endpoint_is_role_gated(monkeypatch) -> None:
    from quantresearch_api import api

    monkeypatch.setattr(api.equity_etf_research_service, "client", FakeDailyBarClient())

    viewer = client.post(
        "/api/v1/research/use-cases/equity-etf/live-run",
        json={"symbols": ["SPY"], "start": "20240101", "end": "20240430"},
        headers={"x-role": "viewer"},
    )
    researcher = client.post(
        "/api/v1/research/use-cases/equity-etf/live-run",
        json={"symbols": ["SPY"], "start": "20240101", "end": "20240430"},
        headers={"x-role": "researcher"},
    )

    assert viewer.status_code == 403
    assert researcher.status_code == 200
    assert researcher.json()["symbols"] == ["SPY"]
    assert researcher.json()["steps"][2]["name"] == "Generate signals"
