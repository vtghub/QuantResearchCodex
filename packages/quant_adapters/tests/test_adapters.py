import asyncio
from uuid import UUID

import pytest
from quantresearch_adapters.brokers import AlpacaBrokerAdapter, BrokerAdapterDisabledError
from quantresearch_adapters.market_data import (
    FallbackDailyBarClient,
    StooqProvider,
    parse_stooq_daily_csv,
)
from quantresearch_core.contracts import (
    AssetClass,
    BrokerMode,
    Instrument,
    OrderIntent,
)


def test_market_data_provider_records_provenance() -> None:
    provider = StooqProvider(symbols=["SPY"])

    instruments = asyncio.run(provider.discover())
    manifest = asyncio.run(provider.ingest(["SPY"]))

    assert instruments[0].asset_class == AssetClass.EQUITY
    assert manifest.provider == "stooq"
    assert manifest.checksum.startswith("sha256:")


def test_stooq_daily_csv_parser_normalizes_bars() -> None:
    rows = parse_stooq_daily_csv(
        "SPY",
        "Date,Open,High,Low,Close,Volume\n2024-01-02,100,101,99,100.5,1000\n",
    )

    assert rows == [
        {
            "symbol": "SPY",
            "date": "2024-01-02",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000,
        }
    ]


def test_fallback_daily_bar_client_uses_yahoo_when_stooq_is_empty() -> None:
    def fetcher(url: str) -> str:
        if "stooq.com" in url:
            return "Date,Open,High,Low,Close,Volume\n"
        return (
            '{"chart":{"result":[{"timestamp":[1704153600],'
            '"indicators":{"quote":[{"open":[100],"high":[101],"low":[99],'
            '"close":[100.5],"volume":[1000]}]}}]}}'
        )

    vendor, rows = FallbackDailyBarClient(fetcher=fetcher).fetch_daily_bars(
        "SPY",
        start="20240101",
        end="20240103",
    )

    assert vendor == "yahoo-finance-compatible"
    assert rows[0]["close"] == 100.5


def test_live_broker_rejects_without_enablement() -> None:
    broker = AlpacaBrokerAdapter(mode=BrokerMode.LIVE, live_trading_enabled=False)
    order = OrderIntent(
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        workspace_id=UUID("00000000-0000-0000-0000-000000000002"),
        strategy_id=UUID("00000000-0000-0000-0000-000000000003"),
        instrument=Instrument(
            symbol="SPY",
            asset_class=AssetClass.ETF,
            venue="ARCX",
            currency="USD",
            timezone="America/New_York",
        ),
        side="buy",
        quantity=1,
        order_type="market",
        client_order_id="test-order",
        mode=BrokerMode.LIVE,
    )

    with pytest.raises(BrokerAdapterDisabledError):
        asyncio.run(broker.submit_order(order))
