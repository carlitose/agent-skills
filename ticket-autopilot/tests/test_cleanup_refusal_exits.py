"""A refusal that protects a human decision must say how that decision is reopened."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from autopilot.kernel import Kernel, TransitionError  # noqa: E402
from autopilot.ticket_contract import parse_ticket_folder  # noqa: E402

TICKET = (
    "---\n"
    "ticket_schema: 1\n"
    "ticket_id: CRE-01\n"
    "execution_mode: AFK\n"
    "blocked_by: []\n"
    "---\n"
    "\n"
    "# Cleanup refusal fixture\n"
)


class CleanupRefusalExitTests(unittest.TestCase):
    """The run is a fixture: no worktree, provider or repository is touched."""

    def kernel(self) -> Kernel:
        owner = tempfile.TemporaryDirectory(prefix="cleanup-refusal-")
        self.addCleanup(owner.cleanup)
        root = Path(owner.name)
        folder = root / "tickets"
        folder.mkdir()
        (folder / "01.md").write_text(TICKET, encoding="utf-8")
        return Kernel.new(
            "run-77",
            parse_ticket_folder(folder),
            provider="github",
            repo=str(root / "repo"),
            worktree=str(root / "worktree"),
            base_sha="0" * 40,
        )

    def test_a_running_run_names_abort_and_what_it_needs(self):
        kernel = self.kernel()
        kernel.ledger["run_state"] = "running"

        with self.assertRaises(TransitionError) as raised:
            kernel.record_cleanup(
                worktree="C:/nowhere/wt", worktree_removed=False, resume_abandoned=False
            )

        message = str(raised.exception)
        self.assertIn("running", message)
        self.assertIn("abort", message)
        self.assertIn("--actor", message)
        self.assertIn("--reason", message)

    def test_a_running_run_is_still_refused(self):
        kernel = self.kernel()
        kernel.ledger["run_state"] = "running"

        with self.assertRaises(TransitionError):
            kernel.record_cleanup(
                worktree="C:/nowhere/wt", worktree_removed=False, resume_abandoned=False
            )

        self.assertIsNone(kernel.ledger["cleanup"])

    def test_a_paused_run_names_unpause_and_the_run(self):
        kernel = self.kernel()
        kernel.pause_run(actor="carla", reason="thinking")

        with self.assertRaises(TransitionError) as raised:
            kernel.preflight_mutation_boundary("CRE-01", "worktree:cleanup")

        message = str(raised.exception)
        self.assertIn("paused", message)
        self.assertIn("unpause", message)
        self.assertIn("run-77", message)

    def test_a_ticket_on_hold_names_the_ticket_and_how_to_reopen_it(self):
        kernel = self.kernel()
        kernel.ledger["tickets"]["CRE-01"]["disposition"] = "on-hold"

        with self.assertRaises(TransitionError) as raised:
            kernel.preflight_mutation_boundary("CRE-01", "worktree:cleanup")

        message = str(raised.exception)
        self.assertIn("on-hold", message)
        self.assertIn("CRE-01", message)
        self.assertIn("ticket-reopen-request", message)

    def test_a_canceled_ticket_says_the_same_thing_about_itself(self):
        kernel = self.kernel()
        kernel.ledger["tickets"]["CRE-01"]["disposition"] = "canceled"

        with self.assertRaises(TransitionError) as raised:
            kernel.preflight_mutation_boundary("CRE-01", "worktree:cleanup")

        message = str(raised.exception)
        self.assertIn("canceled", message)
        self.assertIn("ticket-reopen-request", message)

    def test_an_open_ticket_in_a_live_run_still_passes_the_boundary(self):
        kernel = self.kernel()

        self.assertIsNone(
            kernel.preflight_mutation_boundary("CRE-01", "worktree:cleanup")
        )

    def test_a_ticket_on_hold_still_blocks_every_other_boundary_by_name(self):
        kernel = self.kernel()
        kernel.ledger["tickets"]["CRE-01"]["disposition"] = "on-hold"

        with self.assertRaises(TransitionError) as raised:
            kernel.preflight_mutation_boundary("CRE-01", "implementation")

        self.assertIn("implementation", str(raised.exception))

    def test_a_terminal_run_still_records_cleanup(self):
        kernel = self.kernel()
        kernel.abort(actor="carla", reason="done with it")

        kernel.record_cleanup(
            worktree="C:/nowhere/wt", worktree_removed=True, resume_abandoned=False
        )

        self.assertEqual(kernel.ledger["cleanup"]["worktree"], "C:/nowhere/wt")
        self.assertTrue(kernel.ledger["cleanup"]["worktree_removed"])


if __name__ == "__main__":
    unittest.main()
