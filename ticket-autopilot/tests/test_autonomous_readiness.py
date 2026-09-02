from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.autonomous_readiness import autonomous_merge_dependencies_ready
from autopilot.kernel import Kernel
from autopilot.ledger import AtomicLedger


def lineage(base_branch: object = "main") -> dict[str, object]:
    return {"base_branch": base_branch}


def parent(
    *,
    state: str = "integrated",
    disposition: str = "open",
    candidate_ref: object = None,
    delivery_lineage: object = None,
) -> dict[str, object]:
    return {
        "state": state,
        "disposition": disposition,
        "candidate_ref": candidate_ref,
        "delivery_lineage": delivery_lineage,
        "blocked_by": [],
    }


def child(
    blockers: list[str], *, delivery_lineage: object = None
) -> dict[str, object]:
    return {
        "state": "pr-open",
        "disposition": "open",
        "candidate_ref": {"candidate": "child"},
        "delivery_lineage": delivery_lineage,
        "blocked_by": blockers,
        "merge_authorization": {"mode": "autonomous"},
        "status_barrier": None,
    }


class AutonomousReadinessTests(unittest.TestCase):
    def assert_parity(
        self,
        expected: bool,
        child_ticket: dict[str, object],
        parents: dict[str, dict[str, object]],
    ) -> None:
        tickets = {**parents, "child": child_ticket}
        self.assertEqual(
            expected,
            autonomous_merge_dependencies_ready(child_ticket, tickets),
        )
        kernel = object.__new__(Kernel)
        kernel.ledger = {"tickets": copy.deepcopy(tickets)}
        self.assertEqual(
            expected, kernel.autonomous_merge_dependencies_ready("child")
        )
        snapshot = {
            "tickets": copy.deepcopy(tickets),
            "gates": {},
            "pause": None,
        }
        self.assertEqual(
            "running" if expected else "waiting",
            AtomicLedger._derived_run_state(snapshot),
        )

    def test_precompleted_and_ordinary_single_parent_matrix(self) -> None:
        ordinary_candidate = {"candidate": "parent"}
        cases = {
            "precompleted": (
                True,
                child(["parent"]),
                parent(disposition="completed"),
            ),
            "precompleted-open": (
                False,
                child(["parent"]),
                parent(disposition="open"),
            ),
            "precompleted-held": (
                False,
                child(["parent"]),
                parent(disposition="on-hold"),
            ),
            "precompleted-canceled": (
                False,
                child(["parent"]),
                parent(disposition="canceled"),
            ),
            "precompleted-not-integrated": (
                False,
                child(["parent"]),
                parent(state="pr-open", disposition="completed"),
            ),
            "precompleted-candidate-present": (
                False,
                child(["parent"]),
                parent(
                    disposition="completed",
                    candidate_ref=ordinary_candidate,
                ),
            ),
            "ordinary-matching": (
                True,
                child(["parent"], delivery_lineage=lineage()),
                parent(
                    candidate_ref=ordinary_candidate,
                    delivery_lineage=lineage(),
                ),
            ),
            "ordinary-child-lineage-missing": (
                False,
                child(["parent"]),
                parent(
                    candidate_ref=ordinary_candidate,
                    delivery_lineage=lineage(),
                ),
            ),
            "ordinary-parent-lineage-malformed": (
                False,
                child(["parent"], delivery_lineage=lineage()),
                parent(
                    candidate_ref=ordinary_candidate,
                    delivery_lineage={},
                ),
            ),
            "ordinary-child-lineage-malformed": (
                False,
                child(["parent"], delivery_lineage={}),
                parent(
                    candidate_ref=ordinary_candidate,
                    delivery_lineage=lineage(),
                ),
            ),
            "ordinary-base-mismatch": (
                False,
                child(["parent"], delivery_lineage=lineage("release")),
                parent(
                    candidate_ref=ordinary_candidate,
                    delivery_lineage=lineage(),
                ),
            ),
        }
        for name, (expected, child_ticket, parent_ticket) in cases.items():
            with self.subTest(name=name):
                self.assert_parity(
                    expected, child_ticket, {"parent": parent_ticket}
                )

    def test_no_blocker_and_integrated_multi_parent_semantics_are_unchanged(self) -> None:
        self.assert_parity(True, child([]), {})
        self.assert_parity(
            True,
            child(["first", "second"]),
            {
                "first": parent(state="integrated"),
                "second": parent(state="integrated"),
            },
        )
        self.assert_parity(
            False,
            child(["first", "second"]),
            {
                "first": parent(state="integrated"),
                "second": parent(state="pr-open"),
            },
        )

    def test_malformed_topology_fails_closed(self) -> None:
        malformed_children = [
            {"state": "pr-open", "blocked_by": None},
            {"state": "pr-open", "blocked_by": [""]},
            {"state": "pr-open", "blocked_by": [1]},
        ]
        for ticket in malformed_children:
            with self.subTest(ticket=ticket):
                self.assertFalse(
                    autonomous_merge_dependencies_ready(ticket, {})
                )
        self.assertFalse(
            autonomous_merge_dependencies_ready(
                child(["missing"]), {"child": child(["missing"])}
            )
        )


if __name__ == "__main__":
    unittest.main()
