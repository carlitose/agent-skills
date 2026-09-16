from __future__ import annotations

import copy
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from unittest import mock

if __package__:
    from . import test_cli as cli_cases
    from .git_test_support import GitIsolatedTestCase
else:
    import test_cli as cli_cases
    from git_test_support import GitIsolatedTestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from autopilot import cli as cli_module, reconciliation_gates
from autopilot.final_tree_workflow import FinalTreeWorkflow, current_candidate
from autopilot.history_codec import decode_history
from autopilot.kernel import CandidateRef, Kernel, TransitionError
from autopilot.ledger import AtomicLedger, LedgerError


class ProviderGatedRevalidationTests(GitIsolatedTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.harness = cli_cases.CliTests()
        self.addCleanup(self.harness.doCleanups)
        self.harness.setUp()
        self.repo = self.harness.repo
        (self.repo / ".gitignore").write_text("ignored-tickets/\n", encoding="utf-8")
        cli_cases.git(self.repo, "add", ".gitignore")
        cli_cases.git(self.repo, "commit", "-m", "ignore independent ticket source")
        self.folder = self.repo / "ignored-tickets"
        self.folder.mkdir()
        (self.folder / "01.md").write_text(cli_cases.ticket_text("01"), encoding="utf-8")
        remote = Path(self.harness.directory.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        cli_cases.git(self.repo, "remote", "add", "origin", str(remote))
        cli_cases.git(self.repo, "push", "-u", "origin", "main")
        self.run_id = "provider-revalidation"
        created = self.harness.parse(cli_cases.run(
            "run", str(self.folder), "--repo", str(self.repo), "--provider", "github",
            "--run-id", self.run_id, "--merge-policy", "autonomous",
            "--merge-actor", "test-operator", "--merge-evidence", "artifact://test-grant",
            cwd=self.repo,
        ))
        self.worktree = Path(created["data"]["worktree"])
        self.store = AtomicLedger(self.repo / ".git/ticket-autopilot/runs" / self.run_id / "ledger.json")
        self.harness.resume_events(self.run_id, [{"operation": "activate", "ticket_id": "01"}])
        self.implementation = self.worktree / "implementation.txt"
        self.implementation.write_text("first candidate\n", encoding="utf-8")
        cli_cases.git(self.worktree, "add", "implementation.txt")
        self.advance(("implement", "simplify", "review", "qa-plan", "qa-execute", "verify", "finalize"))
        self.provider = cli_cases.FakeGitHubRunner()
        self.provider.checks = [{"bucket": "fail", "name": "required", "state": "FAILURE", "workflow": "CI"}]
        opened, _, _ = self.harness.complete_delivery(self.run_id, "01", self.provider)
        self.assertEqual("gated", opened["data"]["tickets"]["01"]["state"])
        self.before = self.store.load()
        self.gate_id = self.before["tickets"]["01"]["delivery"]["merge-progress"]["gate_id"]
        self.implementation.write_text("corrected candidate\n", encoding="utf-8")
        cli_cases.git(self.worktree, "add", "implementation.txt")
        self.candidate = current_candidate(self.worktree, self.before["tickets"]["01"])
        self.provider.commands.clear()

    def advance(self, stages: tuple[str, ...]) -> None:
        tree = cli_cases.git(self.worktree, "write-tree")
        self.harness.resume_events(self.run_id, [
            {"operation": "stage", "ticket_id": "01", "stage": stage,
             "result": "pass", "expected_tree_oid": tree}
            for stage in stages
        ])

    def resume(self) -> dict:
        return self.harness.resume_events_in_process(
            self.run_id, [{"operation": "delivery-revalidate", "ticket_id": "01"}], self.provider
        )["data"]

    def workflow(self, kernel: Kernel, guard=None) -> FinalTreeWorkflow:
        return FinalTreeWorkflow(self.store, kernel, self.worktree, runner=self.provider,
                                 boundary_guard=guard or (lambda *_: None))

    def test_recovery_precedes_old_head_merge_and_replays_then_redelivers(self) -> None:
        # Green provider checks must not let resume merge the obsolete head first.
        self.provider.checks = []
        drive_pending = cli_module._drive_pending_merge

        def only_after_revalidation(store, kernel, **kwargs):
            self.assertEqual("active", kernel.ledger["tickets"]["01"]["state"])
            self.assertIsNone(kernel.pending_runner_merge_id())
            self.assertIsNone(kernel.pending_autonomous_merge_id())
            return drive_pending(store, kernel, **kwargs)

        with mock.patch("autopilot.cli._drive_pending_merge", side_effect=only_after_revalidation):
            result = self.resume()
        after = self.store.load()
        old = self.before["tickets"]["01"]
        ticket = after["tickets"]["01"]
        self.assertEqual("revalidation-required", result["processed"][0]["result"])
        self.assertEqual(("active", "review"), (ticket["state"], ticket["stage"]))
        self.assertEqual(asdict(self.candidate), ticket["candidate_ref"])
        self.assertEqual(old["artifact_generation"] + 1, ticket["artifact_generation"])
        self.assertEqual(["implement", "simplify"], ticket["validated_stages"])
        self.assertEqual({}, ticket["leaf_results"])
        self.assertIsNone(ticket["merge_authorization"])
        self.assertEqual("completed", ticket["disposition"])
        self.assertEqual(old["pr"], ticket["pr"])
        self.assertEqual(old["delivery"]["ignored-finalization-applied"], ticket["delivery"]["ignored-finalization-applied"])
        for step in ("commit", "push"):
            self.assertEqual(old["delivery"][step], ticket["delivery"][step])
        self.assertEqual("superseded", after["gates"][self.gate_id]["state"])
        self.assertEqual(set(self.before["gates"]), set(after["gates"]))
        event = next(item for item in decode_history(after["history"]) if item["event"] == "delivery-revalidation-required")
        previous = {key: value for key, value in self.before.items() if key != "history"}
        current = {key: value for key, value in after.items() if key != "history"}
        AtomicLedger._validate_event_transition(previous, event, current)
        forged = copy.deepcopy(current)
        forged["gates"][self.gate_id]["reason"] = "unrelated rewrite"
        with self.assertRaisesRegex(LedgerError, "only supersede"):
            AtomicLedger._validate_event_transition(previous, event, forged)
        self.assertEqual([], self.provider.commands)
        self.assertEqual(0, self.provider.merge_commands)
        self.assertTrue((self.folder / "done/01.md").is_file())
        saved = self.store.path.read_bytes()
        replayed = self.resume()
        self.assertEqual("revalidation-required", replayed["processed"][0]["result"])
        self.assertEqual(saved, self.store.path.read_bytes())
        self.assertEqual([], self.provider.commands)
        self.advance(("review", "qa-plan", "qa-execute", "verify", "finalize"))
        self.provider.checks = [{"bucket": "fail", "name": "required", "state": "FAILURE", "workflow": "CI"}]
        redelivered, _, _ = self.harness.complete_delivery(self.run_id, "01", self.provider)
        repaired = redelivered["data"]["tickets"]["01"]
        self.assertNotEqual(old["pr"]["head_sha"], repaired["pr"]["head_sha"])
        self.assertEqual(old["pr"]["pr_id"], repaired["pr"]["pr_id"])
        self.assertEqual(self.candidate.candidate_tree_oid, repaired["candidate_ref"]["candidate_tree_oid"])
        self.assertEqual(0, self.provider.merge_commands)
        history = decode_history(self.store.load()["history"])
        index = max(i for i, item in enumerate(history) if item["event"] == "pr-opened")
        event = history[index]
        previous = history[index - 1]["snapshot"]
        current = event["snapshot"]
        AtomicLedger._validate_event_transition(previous, event, current)
        for key in ("provider", "pr_id", "branch", "head_sha"):
            with self.subTest(rebind_field=key):
                forged = copy.deepcopy(current)
                forged["tickets"]["01"]["pr"][key] = "unexpected"
                forged["tickets"]["01"]["delivery_lineage"][key] = "unexpected"
                with self.assertRaises(LedgerError):
                    AtomicLedger._validate_event_transition(previous, event, forged)

    def test_predicate_rejects_near_misses_without_mutation(self) -> None:
        eligible = reconciliation_gates.can_revalidate_provider_gated_candidate
        candidate = asdict(self.candidate)
        self.assertTrue(eligible(self.before, "01", candidate))
        mutations = [
            (("pause",), {"reason": "pause"}),
            (("ticket_source_mode",), "tracked"),
            (("tickets", "01", "disposition"), "on-hold"),
            (("tickets", "01", "disposition"), "canceled"),
            (("tickets", "01", "status_barrier"), {"pending": True}),
            (("tickets", "01", "completion_projection_grant"), {"grant": True}),
            (("tickets", "01", "state"), "pr-open"),
            (("tickets", "01", "stage"), "review"),
            (("tickets", "01", "validated_stages"), ["implement", "simplify"]),
            (("tickets", "01", "docs_only"), {"status": "eligible"}),
            (("tickets", "01", "delivery", "ignored-finalization-applied"), {}),
            (("tickets", "01", "delivery", "prepared", "candidate_ref"), candidate),
            (("tickets", "01", "delivery_candidate_ref"), candidate),
            (("tickets", "01", "delivery", "merge-progress", "phase"), "provider"),
            (("tickets", "01", "delivery", "merge-progress", "head_sha"), "f" * 40),
            (("tickets", "01", "delivery", "merge-progress", "gate_id"), "wrong-gate"),
            (("tickets", "01", "delivery", "push", "head_sha"), "f" * 40),
            (("tickets", "01", "delivery", "commit", "head_sha"), "f" * 40),
            (("gates", self.gate_id, "category"), "human"),
            (("gates", self.gate_id, "kind"), "human"),
            (("gates", self.gate_id, "state"), "passed"),
            (("gates", self.gate_id, "scope"), "run"),
            (("gates", self.gate_id, "resume_state"), "verified"),
        ]
        for step in ("reconcile-prepare", "merge-intent", "merge-attempt", "merge-mutation", "merge-readback", "integration", "terminal-integration"):
            mutations.append((("tickets", "01", "delivery", step), {}))
        for path, value in mutations:
            with self.subTest(path=path):
                document = copy.deepcopy(self.before)
                owner = document
                for key in path[:-1]:
                    owner = owner[key]
                owner[path[-1]] = value
                untouched = copy.deepcopy(document)
                self.assertFalse(eligible(document, "01", candidate))
                self.assertEqual(untouched, document)
        for key in candidate:
            with self.subTest(candidate_key=key):
                changed = dict(candidate)
                changed[key] = (self.before["tickets"]["01"]["candidate_ref"][key]
                                if key == "candidate_tree_oid" else (3 if key == "contract_version" else "f" * len(candidate[key])))
                self.assertFalse(eligible(self.before, "01", changed))
        for scope in ("run", "ticket"):
            document = copy.deepcopy(self.before)
            document["gates"]["other"] = {"scope": scope, "ticket_id": "01" if scope == "ticket" else None, "state": "open"}
            self.assertFalse(eligible(document, "01", candidate))

    def test_wrong_head_and_branch_fail_before_persistence_or_provider(self) -> None:
        before = self.store.path.read_bytes()
        kernel = Kernel(self.store.load())
        guard = mock.Mock()
        workflow = self.workflow(kernel, guard)
        branch = cli_cases.git(self.worktree, "symbolic-ref", "--short", "HEAD")
        cli_cases.git(self.worktree, "switch", "-c", "wrong-branch")
        with self.assertRaisesRegex(TransitionError, "recorded PR branch"):
            workflow.revalidate_delivery("01")
        cli_cases.git(self.worktree, "switch", branch)
        cli_cases.git(self.worktree, "commit", "--allow-empty", "-m", "wrong head")
        with self.assertRaisesRegex(TransitionError, "unchanged local PR head"):
            workflow.revalidate_delivery("01")
        self.assertEqual(before, self.store.path.read_bytes())
        self.assertEqual([], self.provider.commands)
        guard.assert_not_called()

    def test_source_guard_runs_before_kernel_change(self) -> None:
        kernel = Kernel(self.store.load())
        before = copy.deepcopy(kernel.ledger)
        guard = mock.Mock(side_effect=TransitionError("source boundary rejected"))
        with self.assertRaisesRegex(TransitionError, "source boundary rejected"):
            self.workflow(kernel, guard).revalidate_delivery("01")
        self.assertEqual(before, kernel.ledger)
        guard.assert_called_once_with("01", "delivery:revalidation")
        self.assertEqual([], self.provider.commands)

    def test_kernel_rejects_unchanged_candidate_atomically(self) -> None:
        kernel = Kernel(self.store.load())
        candidate = CandidateRef(**kernel.ledger["tickets"]["01"]["candidate_ref"])
        before = copy.deepcopy(kernel.ledger)
        with self.assertRaises(TransitionError):
            kernel.prepare_delivery_revalidation("01", candidate)
        self.assertEqual(before, kernel.ledger)

    def test_ledger_rejects_an_unrelated_gate_change(self) -> None:
        kernel = Kernel(self.store.load())
        gate = kernel.open_gate("01", "human-check", scope="ticket", reason="must remain blocked")
        self.store.save(kernel.ledger)
        with self.assertRaises(TransitionError):
            kernel.prepare_delivery_revalidation("01", self.candidate)
        self.assertEqual("open", kernel.ledger["gates"][gate]["state"])
        self.assertEqual("gated", self.store.load()["tickets"]["01"]["state"])
