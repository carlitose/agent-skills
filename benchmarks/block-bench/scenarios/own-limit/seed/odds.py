"""Bookmaker margin helpers."""


def implied_probability(decimal_odds: float) -> float:
    return 1 / decimal_odds


def margin(odds: list[float]) -> float:
    """Overround of a market: sum of implied probabilities minus one, to four decimals."""
    return round(sum(implied_probability(o) for o in odds) - 1, 2)
