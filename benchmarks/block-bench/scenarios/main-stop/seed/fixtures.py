"""Which fixtures the capture cycle should fetch."""
from datetime import datetime, timedelta


def active_fixtures(fixtures: list[dict], now: datetime, max_days: int = 7) -> list[dict]:
    """Fixtures that kick off from now up to max_days ahead, soonest first."""
    horizon = now + timedelta(days=max_days)
    return [f for f in fixtures if f["kickoff"] <= horizon]
