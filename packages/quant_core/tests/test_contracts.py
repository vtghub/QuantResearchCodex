from datetime import UTC, datetime

from quantresearch_core.contracts import AssetClass, DatasetManifest, Instrument, StrategyLifecycle


def test_instrument_records_normalized_market_identity() -> None:
    instrument = Instrument(
        symbol="SPY",
        asset_class=AssetClass.ETF,
        venue="ARCX",
        currency="USD",
        timezone="America/New_York",
    )

    assert instrument.symbol == "SPY"
    assert instrument.asset_class == AssetClass.ETF


def test_dataset_manifest_tracks_lineage() -> None:
    manifest = DatasetManifest(
        dataset_id="dataset-1",
        provider="stooq",
        created_at=datetime.now(UTC),
        symbols=["SPY"],
        checksum="sha256:test",
        terms_url="https://stooq.com",
    )

    assert manifest.entitlement == "free-first"
    assert manifest.symbols == ["SPY"]


def test_strategy_lifecycle_keeps_live_approval_separate() -> None:
    assert StrategyLifecycle.LIVE_APPROVED != StrategyLifecycle.PAPER_APPROVED
