"""Print a deterministic RD-02 dry-run transcript without network access."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from model import (
    EscalationCoordinator,
    EscalationStore,
    FakeIssueAdapter,
    ProviderIssue,
    SimulatedCrash,
    accepted_record,
    fingerprint,
    marker_for,
    protected_run_state,
    valid_run_binding,
)


def _seeded_issue(state: str) -> ProviderIssue:
    value = fingerprint(accepted_record())
    return ProviderIssue(
        repository="carlitose/agent-skills",
        issue_id=41,
        state=state,
        fingerprint=value,
        title="existing synthetic issue",
        body=marker_for(value),
    )


def _run_one(
    root: Path,
    name: str,
    adapter: FakeIssueAdapter,
    *,
    crash_at: str | None = None,
    replay: bool = False,
) -> dict[str, Any]:
    coordinator = EscalationCoordinator(EscalationStore(root / name), adapter)
    try:
        result = coordinator.escalate(
            accepted_record(),
            run_binding=valid_run_binding(),
            protected_state=protected_run_state(),
            crash_at=crash_at,
        )
        crashed = False
    except SimulatedCrash:
        crashed = True
        result = coordinator.escalate(
            accepted_record(),
            run_binding=valid_run_binding(),
            protected_state=protected_run_state(),
        ) if replay else None
    return {
        "crashed": crashed,
        "state": result.state if result else "crashed",
        "search_calls": adapter.call_count("search"),
        "create_calls": adapter.call_count("create"),
        "receipt": result.as_dict().get("receipt") if result else None,
    }


def transcript() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="rd02-prototype-") as directory:
        root = Path(directory)
        return {
            "question": "Can a no-network sidecar prove secret-safe at-most-one escalation?",
            "branch": "logic",
            "scenarios": {
                "absent-create": _run_one(root, "absent", FakeIssueAdapter()),
                "open-match": _run_one(
                    root,
                    "open",
                    FakeIssueAdapter(issues=(_seeded_issue("open"),)),
                ),
                "closed-match": _run_one(
                    root,
                    "closed",
                    FakeIssueAdapter(issues=(_seeded_issue("closed"),)),
                ),
                "offline": _run_one(
                    root,
                    "offline",
                    FakeIssueAdapter(search_mode="offline"),
                ),
                "permission": _run_one(
                    root,
                    "permission",
                    FakeIssueAdapter(search_mode="permission"),
                ),
                "ambiguous-match": _run_one(
                    root,
                    "ambiguous",
                    FakeIssueAdapter(
                        search_mode="ambiguous",
                        issues=(_seeded_issue("open"),),
                    ),
                ),
                "crash-before-create-replay": _run_one(
                    root,
                    "before-create",
                    FakeIssueAdapter(),
                    crash_at="before-create",
                    replay=True,
                ),
                "crash-after-create-replay": _run_one(
                    root,
                    "after-create",
                    FakeIssueAdapter(),
                    crash_at="after-create",
                    replay=True,
                ),
                "lost-response": _run_one(
                    root,
                    "lost-response",
                    FakeIssueAdapter(create_mode="lost-response"),
                ),
                "contradictory-receipt": _run_one(
                    root,
                    "contradictory",
                    FakeIssueAdapter(create_mode="contradictory"),
                ),
            },
        }


if __name__ == "__main__":
    print(json.dumps(transcript(), indent=2, sort_keys=True))
