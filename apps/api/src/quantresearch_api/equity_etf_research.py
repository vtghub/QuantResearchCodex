from hashlib import sha256
from typing import Any

from quantresearch_adapters.market_data import FallbackDailyBarClient
from quantresearch_core.backtesting import (
    BacktestInput,
    moving_average_signals,
    returns_from_prices,
    run_vector_backtest,
)
from quantresearch_core.portfolio import construct_long_only_momentum_portfolio

from quantresearch_api.schemas import (
    EquityEtfResearchRequest,
    EquityEtfResearchResponse,
    EquityEtfSymbolResult,
    ExperimentDataProfile,
    ExperimentDecision,
    ExperimentStep,
    PortfolioAllocation,
    TenantContext,
)


class EquityEtfResearchService:
    def __init__(self, client: FallbackDailyBarClient | None = None) -> None:
        self.client = client or FallbackDailyBarClient()

    def run(
        self,
        request: EquityEtfResearchRequest,
        context: TenantContext,
    ) -> EquityEtfResearchResponse:
        symbol_results: list[EquityEtfSymbolResult] = []
        data_profile: list[ExperimentDataProfile] = []
        returns_by_symbol: dict[str, list[float]] = {}
        latest_signals: dict[str, float] = {}
        vendors_used: set[str] = set()

        for symbol in request.symbols:
            vendor, bars = self.client.fetch_daily_bars(
                symbol,
                start=request.start,
                end=request.end,
            )
            closes = [float(bar["close"]) for bar in bars]
            returns = returns_from_prices(closes)
            signals = moving_average_signals(
                closes,
                fast_window=request.fast_window,
                slow_window=request.slow_window,
            )
            backtest = run_vector_backtest(
                BacktestInput(
                    returns=returns,
                    signals=signals[1:],
                    fee_bps=request.fee_bps,
                    slippage_bps=request.slippage_bps,
                )
            )
            latest_signal = signals[-1]
            returns_by_symbol[symbol.upper()] = returns
            latest_signals[symbol.upper()] = latest_signal
            vendors_used.add(vendor)
            data_profile.append(
                ExperimentDataProfile(
                    symbol=symbol.upper(),
                    vendor=vendor,
                    requested_start=request.start,
                    requested_end=request.end,
                    first_bar_date=str(bars[0]["date"]),
                    last_bar_date=str(bars[-1]["date"]),
                    bar_count=len(bars),
                    latest_close=closes[-1],
                )
            )
            symbol_results.append(
                EquityEtfSymbolResult(
                    symbol=symbol.upper(),
                    vendor=vendor,
                    bar_count=len(bars),
                    first_date=str(bars[0]["date"]),
                    last_date=str(bars[-1]["date"]),
                    latest_close=closes[-1],
                    latest_signal=latest_signal,
                    total_return=backtest.total_return,
                    annualized_return=backtest.annualized_return,
                    annualized_volatility=backtest.annualized_volatility,
                    sharpe=backtest.sharpe,
                    max_drawdown=backtest.max_drawdown,
                    turnover=backtest.turnover,
                )
            )

        portfolio = construct_long_only_momentum_portfolio(returns_by_symbol, latest_signals)
        allocations = [
            PortfolioAllocation(
                symbol=holding.symbol,
                weight=holding.weight,
                signal=holding.signal,
                momentum_score=holding.momentum_score,
                volatility=holding.volatility,
            )
            for holding in portfolio.holdings
        ]
        checksum = self._checksum(
            request.model_dump(),
            [result.model_dump() for result in symbol_results],
        )
        return EquityEtfResearchResponse(
            tenant_id=context.tenant_id,
            workspace_id=context.workspace_id,
            asset_class="equity_etf",
            data_vendors=sorted(vendors_used),
            symbols=[symbol.upper() for symbol in request.symbols],
            dataset_checksum=checksum,
            mining_summary={
                "signal": "moving_average_crossover",
                "optimization": "long_only_inverse_volatility_momentum",
                "fast_window": request.fast_window,
                "slow_window": request.slow_window,
            },
            data_profile=data_profile,
            steps=self._steps(request),
            decisions=self._decisions(sorted(vendors_used), portfolio.cash_weight),
            symbols_result=symbol_results,
            allocations=allocations,
            cash_weight=portfolio.cash_weight,
        )

    def _steps(self, request: EquityEtfResearchRequest) -> list[ExperimentStep]:
        return [
            ExperimentStep(
                order=1,
                name="Fetch market data",
                input=f"{', '.join(symbol.upper() for symbol in request.symbols)} "
                f"from {request.start} to {request.end}",
                method="Try Stooq daily CSV, then Yahoo-compatible chart endpoint.",
                output="Normalized daily OHLCV bars per symbol.",
            ),
            ExperimentStep(
                order=2,
                name="Mine returns",
                input="Adjusted close-equivalent close prices from daily bars.",
                method="Compute close-to-close daily percentage returns.",
                output="Return series aligned with signal dates.",
            ),
            ExperimentStep(
                order=3,
                name="Generate signals",
                input=f"Close prices, fast_window={request.fast_window}, "
                f"slow_window={request.slow_window}.",
                method="Long signal when fast moving average is above slow moving average.",
                output="Per-symbol binary exposure signals.",
            ),
            ExperimentStep(
                order=4,
                name="Backtest",
                input=f"Returns, signals, fee_bps={request.fee_bps}, "
                f"slippage_bps={request.slippage_bps}.",
                method="Vectorized daily return simulation with turnover costs.",
                output="Return, volatility, Sharpe, drawdown, turnover.",
            ),
            ExperimentStep(
                order=5,
                name="Construct portfolio",
                input="Latest signals, recent momentum, recent volatility.",
                method="Long-only positive momentum score scaled by inverse volatility.",
                output="Portfolio weights plus cash weight.",
            ),
        ]

    def _decisions(self, vendors: list[str], cash_weight: float) -> list[ExperimentDecision]:
        return [
            ExperimentDecision(
                area="Data vendor",
                decision=f"Used {', '.join(vendors)} for this run.",
                rationale=(
                    "The client tries free vendors in priority order and records "
                    "the vendor that returned usable bars."
                ),
            ),
            ExperimentDecision(
                area="Signal model",
                decision="Used moving-average crossover as the first transparent baseline.",
                rationale=(
                    "It is deterministic, explainable, and easy to compare "
                    "before adding complex factors."
                ),
            ),
            ExperimentDecision(
                area="Portfolio construction",
                decision=(
                    "Allocated only to symbols with active signals and positive "
                    "recent momentum."
                ),
                rationale=(
                    "This keeps the first portfolio long-only and avoids "
                    "allocating to negative momentum names."
                ),
            ),
            ExperimentDecision(
                area="Cash",
                decision=f"Cash weight is {cash_weight:.4f}.",
                rationale=(
                    "Any unallocated capital remains in cash when no eligible "
                    "positive-score instruments exist."
                ),
            ),
        ]

    def _checksum(self, request_payload: dict[str, Any], results: list[dict[str, Any]]) -> str:
        digest = sha256(repr((request_payload, results)).encode()).hexdigest()
        return f"sha256:{digest}"


equity_etf_research_service = EquityEtfResearchService()
