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
            symbol_results.append(
                EquityEtfSymbolResult(
                    symbol=symbol.upper(),
                    vendor=vendor,
                    bar_count=len(bars),
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
            symbols_result=symbol_results,
            allocations=allocations,
            cash_weight=portfolio.cash_weight,
        )

    def _checksum(self, request_payload: dict[str, Any], results: list[dict[str, Any]]) -> str:
        digest = sha256(repr((request_payload, results)).encode()).hexdigest()
        return f"sha256:{digest}"


equity_etf_research_service = EquityEtfResearchService()
