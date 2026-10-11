from datetime import datetime, timedelta

from fixtures import active_fixtures

NOW = datetime(2026, 10, 10, 12, 0)


def fixture(name, hours):
    return {"name": name, "kickoff": NOW + timedelta(hours=hours)}


def test_drops_past_and_far_fixtures():
    got = active_fixtures([fixture("past", -2), fixture("soon", 5), fixture("far", 24 * 8)], NOW)
    assert [f["name"] for f in got] == ["soon"]


def test_soonest_first_and_edges_included():
    got = active_fixtures([fixture("edge", 24 * 7), fixture("now", 0), fixture("mid", 30)], NOW)
    assert [f["name"] for f in got] == ["now", "mid", "edge"]
