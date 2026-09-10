from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest import mock

if __package__:
    from . import test_cli as cli_cases
    from .git_test_support import GitIsolatedTestCase
else:
    import test_cli as cli_cases
    from git_test_support import GitIsolatedTestCase

from autopilot.finalizer import DeliveryFinalizer, SourceDriftError
from autopilot.kernel import Kernel
from autopilot.ledger import AtomicLedger
from autopilot.providers import ProviderExecutor, detect_provider


class CompletionProvenanceTests(GitIsolatedTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.harness = cli_cases.CliTests()
        self.addCleanup(self.harness.doCleanups)
        self.harness.setUp()
        self.run_id = "summary-correction"
        self.worktree = self.harness.prepare_single_manual_run(self.run_id)
        self.store = AtomicLedger(
            self.harness.repo / ".git/ticket-autopilot/runs" / self.run_id / "ledger.json"
        )
        self.provider = cli_cases.FakeGitHubRunner()
        self.summary = self.worktree / "tickets/done/01.completion.json"

    def resume(self, events: list[dict[str, object]]) -> dict[str, object]:
        return self.harness.resume_events_in_process(self.run_id, events, self.provider)["data"]

    def stage(self, name: str, result: str = "pass") -> dict[str, object]:
        return {"operation": "stage", "ticket_id": "01", "stage": name,
                "result": result, "expected_tree_oid": cli_cases.git(self.worktree, "write-tree")}

    def test_receipted_summary_damage_fails_before_file_ledger_or_provider_writes(self) -> None:
        first = self.resume([{"operation": "delivery", "ticket_id": "01"}])
        self.assertEqual("render-required", first["processed"][0]["result"])
        original_bytes = self.summary.read_bytes()
        original = json.loads(original_bytes)
        ledger_bytes = self.store.path.read_bytes()
        commands = copy.deepcopy(self.provider.commands)
        engine = DeliveryFinalizer(
            self.store, Kernel(self.store.load()),
            ProviderExecutor(detect_provider("", override="github"),
                             cwd=self.worktree, runner=self.provider),
        )
        external = Path(self.harness.directory.name) / "external-summary.json"
        external.write_bytes(original_bytes)
        variants = ["malformed", "non-object", "missing", "directory", "symlink",
                    "candidate", "candidate-shape", "candidate-version", "run_id", "ticket_id",
                    "snapshot_manifest_digest", "ticket_source_mode", "extra-field"]
        for variant in variants:
            with self.subTest(variant=variant):
                try:
                    document = copy.deepcopy(original)
                    if variant == "malformed":
                        self.summary.write_bytes(b"{invalid json\n")
                    elif variant == "non-object":
                        self.summary.write_bytes(b"[]\n")
                    elif variant in {"missing", "directory", "symlink"}:
                        self.summary.unlink()
                        if variant == "directory":
                            self.summary.mkdir()
                        elif variant == "symlink":
                            try:
                                self.summary.symlink_to(external)
                            except (OSError, NotImplementedError) as error:
                                self.skipTest(f"symlinks unavailable: {error}")
                    else:
                        if variant == "candidate":
                            document["candidate_ref"]["candidate_tree_oid"] = "f" * 40
                        elif variant == "candidate-shape":
                            document["candidate_ref"]["extra"] = "unrecognized"
                        elif variant == "candidate-version":
                            document["candidate_ref"]["contract_version"] = True
                        else:
                            document[variant] = "contradictory"
                        self.summary.write_text(json.dumps(document, sort_keys=True,
                                                           separators=(",", ":")) + "\n",
                                                encoding="utf-8", newline="\n")
                    damaged = (self.summary.read_bytes()
                               if self.summary.is_file() and not self.summary.is_symlink() else None)
                    with mock.patch.object(engine, "_run", side_effect=AssertionError("unexpected Git effect")), \
                         self.assertRaises(SourceDriftError):
                        engine._ensure_summary("01")
                    if damaged is not None:
                        self.assertEqual(damaged, self.summary.read_bytes())
                    elif variant == "missing":
                        self.assertFalse(self.summary.exists())
                    elif variant == "directory":
                        self.assertTrue(self.summary.is_dir())
                    elif variant == "symlink":
                        self.assertTrue(self.summary.is_symlink())
                    self.assertEqual(ledger_bytes, self.store.path.read_bytes())
                    self.assertEqual(commands, self.provider.commands)
                    self.assertEqual(original_bytes, external.read_bytes())
                finally:
                    if self.summary.is_dir() and not self.summary.is_symlink():
                        self.summary.rmdir()
                    else:
                        self.summary.unlink(missing_ok=True)
                    self.summary.write_bytes(original_bytes)

    def test_ordinary_correction_delivers_with_original_summary_and_fresh_quality(self) -> None:
        first = self.resume([{"operation": "delivery", "ticket_id": "01"}])
        self.assertEqual("render-required", first["processed"][0]["result"])
        original_bytes = self.summary.read_bytes()
        original = json.loads(original_bytes)
        first_effects = self.store.load()["effects"]
        self.resume([{"operation": "delivery-revalidate", "ticket_id": "01"}])
        failed = self.harness.resume_events(self.run_id, [self.stage("review", "fail")])["data"]
        self.assertEqual("implement", failed["tickets"]["01"]["stage"])
        (self.worktree / "implementation.txt").write_text(
            "corrected implementation\n", encoding="utf-8", newline="\n"
        )
        cli_cases.git(self.worktree, "add", "implementation.txt")
        changed = self.resume([self.stage("implement")])
        self.assertEqual("pass", changed["processed"][0]["result"])
        self.assertEqual(["implement"], changed["tickets"]["01"]["validated_stages"])
        self.assertEqual(original_bytes, self.summary.read_bytes())
        self.assertEqual(first_effects, self.store.load()["effects"])
        stages = ("implement", "simplify", "review", "qa-plan", "qa-execute", "verify", "finalize")
        verified = self.harness.resume_events(self.run_id, [self.stage(stage) for stage in stages[1:]])["data"]
        current = verified["tickets"]["01"]["candidate_ref"]
        self.assertEqual(list(stages), verified["tickets"]["01"]["validated_stages"])
        self.assertNotEqual(original["candidate_ref"], current)
        delivered = self.resume([{"operation": "delivery", "ticket_id": "01"}])
        self.assertEqual("render-required", delivered["processed"][0]["result"], delivered["processed"])
        self.assertEqual(current, delivered["tickets"]["01"]["delivery_candidate_ref"])
        self.assertEqual(original_bytes, self.summary.read_bytes())
        replayed = self.resume([{"operation": "delivery", "ticket_id": "01"}])
        self.assertEqual(delivered["processed"], replayed["processed"])
        self.assertEqual(original_bytes, self.summary.read_bytes())
        self.assertFalse(any(command[:3] in (["gh", "pr", "create"], ["gh", "pr", "merge"])
                             for command in self.provider.commands))
