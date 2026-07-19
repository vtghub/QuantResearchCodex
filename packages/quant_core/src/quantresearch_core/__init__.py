"""Core contracts for QuantResearchCodex."""

from quantresearch_core.backtesting import (
    BacktestInput,
    BacktestResult,
    moving_average_signals,
    returns_from_prices,
    run_vector_backtest,
)
from quantresearch_core.contracts import (
    ApprovalMode,
    BacktestEngine,
    Broker,
    BrokerMode,
    DataProvider,
    RiskPolicy,
    Strategy,
    StrategyLifecycle,
)
from quantresearch_core.portfolio import (
    PortfolioConstructionResult,
    PortfolioHolding,
    annualized_volatility,
    construct_long_only_momentum_portfolio,
)

__all__ = [
    "ApprovalMode",
    "BacktestInput",
    "BacktestEngine",
    "BacktestResult",
    "Broker",
    "BrokerMode",
    "DataProvider",
    "PortfolioConstructionResult",
    "PortfolioHolding",
    "RiskPolicy",
    "Strategy",
    "StrategyLifecycle",
    "annualized_volatility",
    "construct_long_only_momentum_portfolio",
    "moving_average_signals",
    "returns_from_prices",
    "run_vector_backtest",
]
