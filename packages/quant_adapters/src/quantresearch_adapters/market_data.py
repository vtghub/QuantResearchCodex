import csv
import json
from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
from io import StringIO
from typing import ClassVar
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from quantresearch_core.contracts import AssetClass, DatasetManifest, Instrument


class OnlineDataUnavailableError(RuntimeError):
    """Raised when an online data vendor cannot return usable daily bars."""


DailyBar = dict[str, str | int | float]


def _stooq_symbol(symbol: str) -> str:
    normalized = symbol.lower()
    if "." in normalized:
        return normalized
    return f"{normalized}.us"


def _yyyymmdd_to_epoch(value: str) -> int:
    return int(datetime.strptime(value, "%Y%m%d").replace(tzinfo=UTC).timestamp())


def parse_stooq_daily_csv(symbol: str, payload: str) -> list[DailyBar]:
    rows: list[DailyBar] = []
    for row in csv.DictReader(StringIO(payload)):
        if not row.get("Date") or row.get("Close") in {None, ""}:
            continue
        rows.append(
            {
                "symbol": symbol.upper(),
                "date": row["Date"],
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(float(row.get("Volume") or 0)),
            }
        )
    if not rows:
        raise OnlineDataUnavailableError(f"No Stooq daily bars returned for {symbol}.")
    return rows


def parse_yahoo_chart_json(symbol: str, payload: str) -> list[DailyBar]:
    document = json.loads(payload)
    result = (document.get("chart", {}).get("result") or [None])[0]
    if not result:
        raise OnlineDataUnavailableError(f"No Yahoo-compatible daily bars returned for {symbol}.")

    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    rows: list[DailyBar] = []
    for index, timestamp in enumerate(timestamps):
        close = quote.get("close", [None])[index]
        if close is None:
            continue
        rows.append(
            {
                "symbol": symbol.upper(),
                "date": datetime.fromtimestamp(timestamp, UTC).date().isoformat(),
                "open": float(quote.get("open", [close])[index] or close),
                "high": float(quote.get("high", [close])[index] or close),
                "low": float(quote.get("low", [close])[index] or close),
                "close": float(close),
                "volume": int(quote.get("volume", [0])[index] or 0),
            }
        )
    if not rows:
        raise OnlineDataUnavailableError(f"No Yahoo-compatible daily bars returned for {symbol}.")
    return rows


class FallbackDailyBarClient:
    stooq_base_url = "https://stooq.com/q/d/l/"
    yahoo_base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"

    def __init__(self, fetcher: Callable[[str], str] | None = None) -> None:
        self._fetcher = fetcher or self._fetch_url

    def fetch_daily_bars(
        self,
        symbol: str,
        *,
        start: str,
        end: str,
    ) -> tuple[str, list[DailyBar]]:
        errors: list[str] = []
        for vendor, url, parser in self._vendor_attempts(symbol, start=start, end=end):
            try:
                return vendor, parser(symbol, self._fetcher(url))
            except (
                OnlineDataUnavailableError,
                URLError,
                TimeoutError,
                json.JSONDecodeError,
            ) as exc:
                errors.append(f"{vendor}: {exc}")
        raise OnlineDataUnavailableError("; ".join(errors))

    def _vendor_attempts(self, symbol: str, *, start: str, end: str):
        stooq_query = urlencode({"s": _stooq_symbol(symbol), "d1": start, "d2": end, "i": "d"})
        yahoo_query = urlencode(
            {
                "period1": _yyyymmdd_to_epoch(start),
                "period2": _yyyymmdd_to_epoch(end),
                "interval": "1d",
            }
        )
        return [
            ("stooq", f"{self.stooq_base_url}?{stooq_query}", parse_stooq_daily_csv),
            (
                "yahoo-finance-compatible",
                f"{self.yahoo_base_url}{symbol.upper()}?{yahoo_query}",
                parse_yahoo_chart_json,
            ),
        ]

    def _fetch_url(self, url: str) -> str:
        request = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 QuantResearchCodex/0.1"},
        )
        with urlopen(request, timeout=15) as response:
            return response.read().decode("utf-8")


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
