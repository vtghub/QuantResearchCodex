import asyncio
from uuid import UUID

import pytest
from quantresearch_adapters.brokers import AlpacaBrokerAdapter, BrokerAdapterDisabledError
from quantresearch_adapters.market_data import StooqProvider
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
