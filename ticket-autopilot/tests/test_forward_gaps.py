from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.git_ops import GitError, assert_remote_head
from autopilot.kernel import CandidateRef, Kernel
from autopilot.ticket_contract import parse_ticket_folder


PIPELINE = (
    "implement",
    "simplify",
    "review",
    "qa-plan",
    "qa-execute",
    "verify",
    "finalize",
)


def ticket_text(ticket_id: str) -> str:
    return (
        "---\n"
        "ticket_schema: 1\n"
        f'ticket_id: "{ticket_id}"\n'
        "execution_mode: AFK\n"
        "blocked_by: []\n"
        "---\n\n"
        f"# Ticket {ticket_id}\n"
    )


def candidate(suffix: str = "one") -> CandidateRef:
    return CandidateRef(
        base_sha=f"base-{suffix}",
        tree_oid=f"tree-{suffix}",
        ticket_digest=f"ticket-{suffix}",
        contract_version=1,
    )


class ForwardGapTests(unittest.TestCase):
    def make_kernel(self) -> Kernel:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        folder = Path(directory.name)
        (folder / "01.md").write_text(ticket_text("01"))
        return Kernel.new("forward-gap", parse_ticket_folder(folder))

    def test_open_pr_waits_and_only_integration_completes_the_run(self) -> None:
        kernel = self.make_kernel()
        fixed = candidate()
        kernel.activate("01", fixed)
        for stage in PIPELINE:
            kernel.record_stage("01", stage, "pass", fixed)
        kernel.record_pr(
            "01",
            provider="github",
            pr_id="7",
            head_sha="head-one",
            branch="ticket/01",
        )

        self.assertEqual("waiting", kernel.report()["run_state"])
        kernel.authorize_merge(
            "01",
            actor="human",
            head_sha="head-one",
            evidence="artifact://approval",
        )
        kernel.record_integration("01", expected_head_sha="head-one")
        self.assertEqual("completed", kernel.report()["run_state"])

    def test_qa_implementation_failure_restarts_the_quality_pipeline(self) -> None:
        kernel = self.make_kernel()
        fixed = candidate()
        kernel.activate("01", fixed)
        for stage in PIPELINE[:4]:
            kernel.record_stage("01", stage, "pass", fixed)

        kernel.record_stage("01", "qa-execute", "fail", fixed)

        ticket = kernel.report()["tickets"]["01"]
        self.assertEqual("active", ticket["state"])
        self.assertEqual("implement", ticket["stage"])
        self.assertEqual(1, ticket["quality_failures"])
        self.assertEqual([], ticket["validated_stages"])

    def test_remote_divergence_guard_accepts_only_explicit_heads(self) -> None:
        self.assertEqual(
            "old-head",
            assert_remote_head(
                "old-head",
                {"old-head", "new-head"},
                phase="before reconciled publish",
            ),
        )
        self.assertEqual(
            "new-head",
            assert_remote_head(
                "new-head",
                {"old-head", "new-head"},
                phase="before reconciled publish",
            ),
        )
        with self.assertRaisesRegex(
            GitError,
            "remote branch diverged before reconciled publish",
        ):
            assert_remote_head(
                "other-head",
                {"old-head", "new-head"},
                phase="before reconciled publish",
            )


if __name__ == "__main__":
    unittest.main()
