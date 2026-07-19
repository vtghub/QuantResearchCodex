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

__all__ = [
    "ApprovalMode",
    "BacktestInput",
    "BacktestEngine",
    "BacktestResult",
    "Broker",
    "BrokerMode",
    "DataProvider",
    "RiskPolicy",
    "Strategy",
    "StrategyLifecycle",
    "moving_average_signals",
    "returns_from_prices",
    "run_vector_backtest",
]
