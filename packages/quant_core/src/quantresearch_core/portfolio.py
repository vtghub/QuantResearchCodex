from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class PortfolioHolding:
    symbol: str
    weight: float
    signal: float
    momentum_score: float
    volatility: float


@dataclass(frozen=True)
class PortfolioConstructionResult:
    holdings: list[PortfolioHolding]
    cash_weight: float


def annualized_volatility(returns: list[float]) -> float:
    if not returns:
        return 0.0
    mean_return = sum(returns) / len(returns)
    variance = sum((value - mean_return) ** 2 for value in returns) / len(returns)
    return sqrt(variance) * sqrt(252)


def construct_long_only_momentum_portfolio(
    symbol_returns: dict[str, list[float]],
    latest_signals: dict[str, float],
) -> PortfolioConstructionResult:
    raw_scores: dict[str, float] = {}
    diagnostics: dict[str, tuple[float, float]] = {}

    for symbol, returns in symbol_returns.items():
        if not returns:
            continue
        lookback = returns[-63:] if len(returns) >= 63 else returns
        momentum_score = max(0.0, sum(lookback))
        volatility = annualized_volatility(lookback)
        signal = max(0.0, latest_signals.get(symbol, 0.0))
        raw_scores[symbol] = signal * momentum_score / max(volatility, 0.01)
        diagnostics[symbol] = (momentum_score, volatility)

    score_total = sum(raw_scores.values())
    if score_total <= 0:
        return PortfolioConstructionResult(holdings=[], cash_weight=1.0)

    holdings = [
        PortfolioHolding(
            symbol=symbol,
            weight=score / score_total,
            signal=latest_signals.get(symbol, 0.0),
            momentum_score=diagnostics[symbol][0],
            volatility=diagnostics[symbol][1],
        )
        for symbol, score in sorted(raw_scores.items())
        if score > 0
    ]
    allocated = sum(holding.weight for holding in holdings)
    return PortfolioConstructionResult(holdings=holdings, cash_weight=max(0.0, 1.0 - allocated))
