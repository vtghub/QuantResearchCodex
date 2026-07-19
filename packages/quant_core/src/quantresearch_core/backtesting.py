from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class BacktestInput:
    returns: list[float]
    signals: list[float]
    fee_bps: float = 1.0
    slippage_bps: float = 1.0


@dataclass(frozen=True)
class BacktestResult:
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe: float
    max_drawdown: float
    turnover: float
    equity_curve: list[float]


def run_vector_backtest(input_data: BacktestInput) -> BacktestResult:
    if len(input_data.returns) != len(input_data.signals):
        raise ValueError("returns and signals must have the same length")
    if not input_data.returns:
        raise ValueError("backtest requires at least one return")

    prior_signal = 0.0
    equity = 1.0
    equity_curve: list[float] = []
    strategy_returns: list[float] = []
    turnover = 0.0
    cost_rate = (input_data.fee_bps + input_data.slippage_bps) / 10_000

    for market_return, signal in zip(input_data.returns, input_data.signals, strict=True):
        clipped_signal = max(min(signal, 1.0), -1.0)
        trade_size = abs(clipped_signal - prior_signal)
        turnover += trade_size
        net_return = prior_signal * market_return - trade_size * cost_rate
        equity *= 1 + net_return
        equity_curve.append(equity)
        strategy_returns.append(net_return)
        prior_signal = clipped_signal

    total_return = equity - 1
    mean_return = sum(strategy_returns) / len(strategy_returns)
    variance = sum((value - mean_return) ** 2 for value in strategy_returns) / len(strategy_returns)
    daily_volatility = sqrt(variance)
    annualized_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1
    annualized_volatility = daily_volatility * sqrt(252)
    sharpe = annualized_return / annualized_volatility if annualized_volatility else 0.0

    peak = 1.0
    max_drawdown = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        drawdown = value / peak - 1
        max_drawdown = min(max_drawdown, drawdown)

    return BacktestResult(
        total_return=total_return,
        annualized_return=annualized_return,
        annualized_volatility=annualized_volatility,
        sharpe=sharpe,
        max_drawdown=max_drawdown,
        turnover=turnover,
        equity_curve=equity_curve,
    )


def moving_average_signals(prices: list[float], fast_window: int, slow_window: int) -> list[float]:
    if fast_window <= 0 or slow_window <= 0:
        raise ValueError("windows must be positive")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be smaller than slow_window")
    if len(prices) < slow_window:
        raise ValueError("not enough prices for slow_window")

    signals: list[float] = []
    for index in range(len(prices)):
        if index + 1 < slow_window:
            signals.append(0.0)
            continue
        fast_average = sum(prices[index + 1 - fast_window : index + 1]) / fast_window
        slow_average = sum(prices[index + 1 - slow_window : index + 1]) / slow_window
        signals.append(1.0 if fast_average > slow_average else 0.0)
    return signals


def returns_from_prices(prices: list[float]) -> list[float]:
    if len(prices) < 2:
        raise ValueError("at least two prices are required")
    return [(current / prior) - 1 for prior, current in zip(prices, prices[1:], strict=False)]
