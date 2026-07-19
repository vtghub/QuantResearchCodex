from quantresearch_core.portfolio import construct_long_only_momentum_portfolio


def test_construct_long_only_momentum_portfolio_allocates_positive_scores() -> None:
    result = construct_long_only_momentum_portfolio(
        {
            "SPY": [0.01, 0.02, 0.01],
            "QQQ": [0.03, -0.01, 0.02],
            "IWM": [-0.01, -0.02, 0.0],
        },
        {"SPY": 1.0, "QQQ": 1.0, "IWM": 0.0},
    )

    assert [holding.symbol for holding in result.holdings] == ["QQQ", "SPY"]
    assert round(sum(holding.weight for holding in result.holdings), 6) == 1.0
    assert result.cash_weight == 0.0


def test_construct_long_only_momentum_portfolio_moves_to_cash_without_signals() -> None:
    result = construct_long_only_momentum_portfolio(
        {"SPY": [0.01, 0.02]},
        {"SPY": 0.0},
    )

    assert result.holdings == []
    assert result.cash_weight == 1.0
