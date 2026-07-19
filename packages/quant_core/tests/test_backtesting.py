import pytest
from quantresearch_core.backtesting import (
    BacktestInput,
    moving_average_signals,
    returns_from_prices,
    run_vector_backtest,
)


def test_vector_backtest_returns_metrics_and_equity_curve() -> None:
    result = run_vector_backtest(
        BacktestInput(
            returns=[0.01, -0.005, 0.02, -0.01],
            signals=[0.0, 1.0, 1.0, 0.0],
            fee_bps=1.0,
            slippage_bps=1.0,
        )
    )

    assert len(result.equity_curve) == 4
    assert result.turnover == 2.0
    assert result.max_drawdown <= 0


def test_vector_backtest_rejects_mismatched_series() -> None:
    with pytest.raises(ValueError, match="same length"):
        run_vector_backtest(BacktestInput(returns=[0.01], signals=[1.0, 0.0]))


def test_moving_average_signals_align_with_next_period_returns() -> None:
    prices = [100, 101, 102, 103, 104, 105]

    signals = moving_average_signals(prices, fast_window=2, slow_window=3)
    returns = returns_from_prices(prices)

    assert signals[:2] == [0.0, 0.0]
    assert len(signals[1:]) == len(returns)
