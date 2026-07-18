from datetime import UTC, datetime
from hashlib import sha256
from typing import ClassVar

from quantresearch_core.contracts import AssetClass, DatasetManifest, Instrument


class StaticProvider:
    name: ClassVar[str]
    terms_url: ClassVar[str | None] = None
    asset_class: ClassVar[AssetClass]
    venue: ClassVar[str]

    def __init__(self, symbols: list[str] | None = None) -> None:
        self.symbols = symbols or []

    async def discover(self) -> list[Instrument]:
        return [
            Instrument(
                symbol=symbol,
                asset_class=self.asset_class,
                venue=self.venue,
                currency="USD",
                timezone="UTC",
            )
            for symbol in self.symbols
        ]

    async def ingest(self, symbols: list[str]) -> DatasetManifest:
        digest = sha256(f"{self.name}:{','.join(symbols)}".encode()).hexdigest()
        return DatasetManifest(
            dataset_id=f"{self.name}:{digest[:12]}",
            provider=self.name,
            created_at=datetime.now(UTC),
            symbols=symbols,
            checksum=f"sha256:{digest}",
            terms_url=self.terms_url,
            transform_version="normalized-v0",
        )


class FredProvider(StaticProvider):
    name = "fred"
    terms_url = "https://fred.stlouisfed.org/docs/api/terms_of_use.html"
    asset_class = AssetClass.FX
    venue = "FRED"


class StooqProvider(StaticProvider):
    name = "stooq"
    terms_url = "https://stooq.com"
    asset_class = AssetClass.EQUITY
    venue = "STOOQ"


class YahooFinanceCompatibleProvider(StaticProvider):
    name = "yahoo-finance-compatible"
    terms_url = "https://finance.yahoo.com"
    asset_class = AssetClass.EQUITY
    venue = "YAHOO"


class CoinGeckoProvider(StaticProvider):
    name = "coingecko"
    terms_url = "https://www.coingecko.com/en/api_terms"
    asset_class = AssetClass.CRYPTO
    venue = "COINGECKO"


class EcbFxProvider(StaticProvider):
    name = "ecb-fx"
    terms_url = "https://www.ecb.europa.eu/services/disclaimer/html/index.en.html"
    asset_class = AssetClass.FX
    venue = "ECB"
