from __future__ import annotations

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

if __package__:
    from . import test_cli as cli_cases
    from .git_test_support import GitIsolatedTestCase
else:
    import test_cli as cli_cases
    from git_test_support import GitIsolatedTestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from autopilot import finalizer
from autopilot.final_tree_transaction import FinalTreeTransactionError
from autopilot.final_tree_workflow import FinalTreeWorkflow
from autopilot.ledger import AtomicLedger


class FinalTreeWorkflowTests(GitIsolatedTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.harness = cli_cases.CliTests()
        self.addCleanup(self.harness.doCleanups)
        self.harness.setUp()
        self.repo = self.harness.repo
        remote = Path(self.harness.directory.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        cli_cases.git(self.repo, "remote", "add", "origin", str(remote))
        created = self.harness.parse(cli_cases.run(
            "run", str(self.harness.tickets), "--repo", str(self.repo),
            "--provider", "github", "--run-id", "workflow", "--final-tree-mode", "enabled",
            cwd=self.repo,
        ))
        self.worktree = Path(created["data"]["worktree"])
        self.store = AtomicLedger(self.repo / ".git/ticket-autopilot/runs/workflow/ledger.json")
        self.provider = cli_cases.FakeGitHubRunner()
        self.resume([{"operation": "activate", "ticket_id": "01"}])
        (self.worktree / "implementation.txt").write_text("candidate\n", encoding="utf-8", newline="\n")
        cli_cases.git(self.worktree, "add", "implementation.txt")
        self.implementation_tree = cli_cases.git(self.worktree, "write-tree")

    def resume(self, events: list[dict[str, object]]) -> dict[str, object]:
        return self.harness.resume_events_in_process("workflow", events, self.provider)["data"]

    def stages(self) -> list[dict[str, object]]:
        return [{"operation": "stage", "ticket_id": "01", "stage": stage,
                 "result": "pass", "expected_tree_oid": self.implementation_tree}
                for stage in ("implement", "simplify")]

    def test_cli_routes_stages_through_workflow_with_unchanged_wire_results(self) -> None:
        with mock.patch.object(FinalTreeWorkflow, "record_stage", autospec=True,
                               side_effect=FinalTreeWorkflow.record_stage) as advance:
            result = self.resume(self.stages())
        self.assertEqual(2, advance.call_count)
        self.assertEqual({"operation": "stage", "ticket_id": "01", "stage": "implement",
                          "result": "pass", "tree_oid": self.implementation_tree}, result["processed"][0])
        outcome = result["processed"][1]
        self.assertEqual("projected-not-integrated", outcome["projection"])
        self.assertEqual(self.implementation_tree, outcome["tree_oid"])
        ticket = result["tickets"]["01"]
        self.assertNotEqual(self.implementation_tree, outcome["projected_tree_oid"])
        self.assertEqual(outcome["projected_tree_oid"], ticket["candidate_ref"]["candidate_tree_oid"])
        self.assertEqual("review", ticket["stage"])
        self.assertEqual(["implement", "simplify"], ticket["validated_stages"])
        self.assertEqual("done/01.md", ticket["current_source_relative_path"])
        self.assertEqual([], self.provider.commands)
        events = [event["event"] for event in self.store.load()["history"]]
        self.assertLess(events.index("final-tree-projection-final-tree-bound"),
                        events.index("final-tree-projection-quality-candidate-adopted"))
        self.assertEqual(1, events.count("final-tree-projection-quality-candidate-adopted"))

    def test_cli_recovers_persisted_intent_once_before_next_event(self) -> None:
        apply = finalizer.apply_projection_transaction

        def interrupted(*args, **kwargs):
            persist_started = kwargs["persist_effect_started"]

            def after_intent(effect_key):
                persist_started(effect_key)
                raise FinalTreeTransactionError("injected interruption before repository effect")
            return apply(*args, **{**kwargs, "persist_effect_started": after_intent})

        with mock.patch.object(finalizer, "apply_projection_transaction", side_effect=interrupted):
            stopped = self.resume(self.stages())
        self.assertEqual("recovery-required", stopped["processed"][-1]["projection"])
        transaction = stopped["tickets"]["01"]["final_tree_projection"]["transaction"]
        self.assertIsNotNone(transaction["active_effect"])
        planned_tree = transaction["planned_delivery_candidate_ref"]["candidate_tree_oid"]
        event = {"operation": "delivery-revalidate", "ticket_id": "01"}
        with mock.patch.object(FinalTreeWorkflow, "recover", autospec=True,
                               side_effect=FinalTreeWorkflow.recover) as recover:
            resumed = self.resume([event])
        self.assertEqual(1, recover.call_count)
        self.assertEqual({"operation": "final-tree-projection-recovery", "ticket_id": "01",
                          "result": "resumed", "tree_oid": planned_tree}, resumed["processed"][0])
        self.assertEqual({**event, "result": "revalidation-required", "tree_oid": planned_tree},
                         resumed["processed"][1])
        fixed = resumed["tickets"]["01"]["final_tree_projection"]["transaction"]
        self.assertIsNone(fixed["active_effect"])
        self.assertEqual(len(fixed["effect_bindings"]), len(fixed["effects_applied"]))
        before = self.store.path.read_bytes()
        replayed = self.resume([event])
        # Preserve the existing repeated recovery notification, not new effects.
        self.assertEqual(resumed["processed"], replayed["processed"])
        self.assertEqual(before, self.store.path.read_bytes())
        self.assertEqual([], self.provider.commands)
        events = [item["event"] for item in self.store.load()["history"]]
        self.assertEqual(1, events.count("final-tree-projection-intent-persisted"))
        self.assertEqual(1, events.count("final-tree-projection-final-tree-bound"))

    def test_unreceipted_move_retains_existing_fail_closed_source_boundary(self) -> None:
        # Baseline limitation: interruption before the completion receipt exists
        # is rejected by source discovery, before workflow recovery can run.
        apply = finalizer.apply_projection_transaction

        def interrupted(*args, **kwargs):
            def after_effect(_effect_key):
                raise FinalTreeTransactionError("injected interruption before receipt")
            return apply(*args, **kwargs, after_repository_effect=after_effect)

        with mock.patch.object(finalizer, "apply_projection_transaction", side_effect=interrupted):
            stopped = self.resume(self.stages())
        self.assertEqual("recovery-required", stopped["processed"][-1]["projection"])
        before = self.store.path.read_bytes()
        with self.assertRaisesRegex(AssertionError, "unknown ticket '01'"):
            self.resume([{"operation": "delivery-revalidate", "ticket_id": "01"}])
        self.assertEqual(before, self.store.path.read_bytes())
        self.assertEqual([], self.provider.commands)
        self.assertFalse((self.worktree / "tickets/01.md").exists())

    def test_wrong_stage_tree_is_rejected_without_ledger_mutation(self) -> None:
        before = self.store.path.read_bytes()
        event = {**self.stages()[0], "expected_tree_oid": "f" * 40}
        with self.assertRaisesRegex(AssertionError, "expected_tree_oid differs"):
            self.resume([event])
        self.assertEqual(before, self.store.path.read_bytes())
        self.assertEqual([], self.provider.commands)

    def test_status_does_not_enter_workflow_or_mutate_ledger(self) -> None:
        before = self.store.path.read_bytes()
        output = io.StringIO()
        with mock.patch.object(FinalTreeWorkflow, "recover", side_effect=AssertionError("unexpected recovery")), \
             mock.patch.object(FinalTreeWorkflow, "record_stage", side_effect=AssertionError("unexpected stage")), \
             redirect_stdout(output):
            code = cli_cases.cli_main(["status", "workflow", "--repo", str(self.repo)],
                                      command_runner=self.provider)
        self.assertEqual(0, code, output.getvalue())
        self.assertEqual("implement", json.loads(output.getvalue())["data"]["tickets"]["01"]["stage"])
        self.assertEqual(before, self.store.path.read_bytes())
        self.assertEqual([], self.provider.commands)
