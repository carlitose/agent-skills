from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "ticket-autopilot" / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
sys.path.insert(0, str(SCRIPTS))

from autopilot.finalizer import (
    SourceDriftError,
    SourceModeDriftError,
    assert_ticket_source_mode,
    finalize_done,
)
from autopilot.git_ops import candidate_ref
from autopilot.kernel import Kernel
from autopilot.ledger import AtomicLedger
from autopilot.leaf_protocol import LEAF_PHASE_CONTRACTS
from autopilot.ticket_contract import ticket_source_digest
from autopilot.ticket_source import (
    TicketSourceError,
    inspect_ticket_source,
    load_ticket_snapshot,
    persist_ticket_snapshot,
)


def git(cwd: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def cli(*args: str, cwd: Path, check: bool = True) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "-B", str(CLI), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    if check and result.returncode:
        raise AssertionError(payload)
    return payload


def ticket_text(ticket_id: str, blocked_by: tuple[str, ...] = ()) -> str:
    blockers = "".join(f'  - "{item}"\n' for item in blocked_by)
    blocker_field = f"blocked_by:\n{blockers}" if blockers else "blocked_by: []\n"
    return (
        "---\n"
        "ticket_schema: 1\n"
        f'ticket_id: "{ticket_id}"\n'
        "execution_mode: AFK\n"
        f"{blocker_field}"
        "---\n\n"
        f"# Ticket {ticket_id}\n"
    )


class TicketSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "tests@example.invalid")
        git(self.repo, "config", "user.name", "Ticket Tests")
        (self.repo / "README.md").write_text("baseline\n", encoding="utf-8")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-m", "baseline")
        self.sequence = 0

    def make_tracked(self) -> Path:
        folder = self.repo / "tickets"
        folder.mkdir()
        (folder / "01.md").write_text(ticket_text("01"), encoding="utf-8")
        (folder / "02.md").write_text(
            ticket_text("02", ("01",)), encoding="utf-8"
        )
        git(self.repo, "add", "tickets")
        git(self.repo, "commit", "-m", "tickets")
        return folder

    def make_ignored(self) -> Path:
        self.sequence += 1
        ignore = self.repo / ".gitignore"
        if not ignore.exists():
            ignore.write_text("docs/\n", encoding="utf-8")
            git(self.repo, "add", ".gitignore")
            git(self.repo, "commit", "-m", "ignore docs")
        folder = self.repo / "docs" / "tickets" / f"feature-{self.sequence}"
        folder.mkdir(parents=True)
        (folder / "01.md").write_text(ticket_text("01"), encoding="utf-8")
        (folder / "02.md").write_text(
            ticket_text("02", ("01",)), encoding="utf-8"
        )
        return folder

    def make_stale_main_with_integrated_tickets(self) -> tuple[Path, str, str]:
        stale_main = git(self.repo, "rev-parse", "main")
        git(self.repo, "checkout", "-b", "integrated-ticket-source")
        folder = self.repo / "tickets"
        folder.mkdir()
        (folder / "01.md").write_text(ticket_text("01"), encoding="utf-8")
        git(self.repo, "add", "tickets")
        git(self.repo, "commit", "-m", "integrate ticket source remotely")
        upstream_main = git(self.repo, "rev-parse", "HEAD")
        self.configure_main_upstream(upstream_main)
        return folder, stale_main, upstream_main

    def configure_main_upstream(self, upstream_main: str) -> None:
        git(self.repo, "config", "remote.origin.url", "https://example.invalid/repo.git")
        git(
            self.repo,
            "config",
            "remote.origin.fetch",
            "+refs/heads/*:refs/remotes/origin/*",
        )
        git(self.repo, "update-ref", "refs/remotes/origin/main", upstream_main)
        git(self.repo, "config", "branch.main.remote", "origin")
        git(self.repo, "config", "branch.main.merge", "refs/heads/main")

    def test_fast_forward_upstream_resolves_stale_local_base_without_moving_it(self) -> None:
        folder, stale_main, upstream_main = self.make_stale_main_with_integrated_tickets()

        source = inspect_ticket_source(self.repo, folder, base_ref="main")

        self.assertEqual("tracked", source.source_mode)
        self.assertEqual(upstream_main, source.manifest["selected_base_sha"])
        self.assertEqual(stale_main, git(self.repo, "rev-parse", "main"))

    def test_plan_and_run_start_from_resolved_upstream_without_moving_main(self) -> None:
        folder, stale_main, upstream_main = self.make_stale_main_with_integrated_tickets()

        planned = cli(
            "plan",
            str(folder),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--base",
            "main",
            cwd=self.repo,
        )["data"]
        created = cli(
            "run",
            str(folder),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--base",
            "main",
            "--run-id",
            "stale-base-run",
            cwd=self.repo,
        )["data"]
        worktree = Path(created["worktree"])

        self.assertEqual("tracked", planned["ticket_source_mode"])
        self.assertEqual(upstream_main, git(worktree, "rev-parse", "HEAD"))
        self.assertEqual(stale_main, git(self.repo, "rev-parse", "main"))
        git(self.repo, "worktree", "remove", str(worktree))

    def test_ignored_source_uses_fast_forward_upstream_as_its_selected_base(self) -> None:
        stale_main = git(self.repo, "rev-parse", "main")
        git(self.repo, "checkout", "-b", "integrated-ignore-rule")
        (self.repo / ".gitignore").write_text("docs/\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-m", "integrate ignore rule remotely")
        upstream_main = git(self.repo, "rev-parse", "HEAD")
        self.configure_main_upstream(upstream_main)
        folder = self.repo / "docs" / "tickets" / "private"
        folder.mkdir(parents=True)
        (folder / "01.md").write_text(ticket_text("01"), encoding="utf-8")

        source = inspect_ticket_source(self.repo, folder, base_ref="main")

        self.assertEqual("ignored", source.source_mode)
        self.assertEqual(upstream_main, source.manifest["selected_base_sha"])
        self.assertEqual(stale_main, git(self.repo, "rev-parse", "main"))

    def test_equal_and_local_ahead_upstream_keep_the_local_commit(self) -> None:
        folder = self.make_tracked()
        local_main = git(self.repo, "rev-parse", "main")
        self.configure_main_upstream(local_main)

        equal = inspect_ticket_source(self.repo, folder, base_ref="main")
        self.assertEqual(local_main, equal.manifest["selected_base_sha"])

        git(self.repo, "update-ref", "refs/remotes/origin/main", f"{local_main}^")
        ahead = inspect_ticket_source(self.repo, folder, base_ref="main")
        self.assertEqual(local_main, ahead.manifest["selected_base_sha"])

    def test_diverged_upstream_fails_closed_while_literal_remote_ref_stays_literal(self) -> None:
        git(self.repo, "checkout", "-b", "remote-main")
        remote_folder = self.repo / "tickets"
        remote_folder.mkdir()
        (remote_folder / "01.md").write_text(ticket_text("01"), encoding="utf-8")
        (self.repo / "remote-only.txt").write_text("remote\n", encoding="utf-8")
        git(self.repo, "add", "tickets", "remote-only.txt")
        git(self.repo, "commit", "-m", "remote main")
        upstream_main = git(self.repo, "rev-parse", "HEAD")

        git(self.repo, "checkout", "main")
        local_folder = self.repo / "tickets"
        local_folder.mkdir()
        (local_folder / "01.md").write_text(ticket_text("01"), encoding="utf-8")
        (self.repo / "local-only.txt").write_text("local\n", encoding="utf-8")
        git(self.repo, "add", "tickets", "local-only.txt")
        git(self.repo, "commit", "-m", "local main")
        self.configure_main_upstream(upstream_main)

        with self.assertRaisesRegex(TicketSourceError, "have diverged"):
            inspect_ticket_source(self.repo, local_folder, base_ref="main")

        literal = inspect_ticket_source(
            self.repo,
            local_folder,
            base_ref="refs/remotes/origin/main",
        )
        self.assertEqual(upstream_main, literal.manifest["selected_base_sha"])
        literal_sha = inspect_ticket_source(
            self.repo,
            local_folder,
            base_ref=upstream_main,
        )
        self.assertEqual(upstream_main, literal_sha.manifest["selected_base_sha"])

    def test_fast_forward_upstream_does_not_admit_genuinely_untracked_source(self) -> None:
        git(self.repo, "checkout", "-b", "integrated-unrelated-change")
        (self.repo / "integrated.txt").write_text("integrated\n", encoding="utf-8")
        git(self.repo, "add", "integrated.txt")
        git(self.repo, "commit", "-m", "unrelated upstream change")
        self.configure_main_upstream(git(self.repo, "rev-parse", "HEAD"))
        folder = self.repo / "untracked"
        folder.mkdir()
        (folder / "01.md").write_text(ticket_text("01"), encoding="utf-8")

        with self.assertRaisesRegex(TicketSourceError, "untracked and not ignored"):
            inspect_ticket_source(self.repo, folder, base_ref="main")

    def test_classifies_tracked_and_ignored_and_rejects_mixed_or_untracked(self) -> None:
        tracked = inspect_ticket_source(self.repo, self.make_tracked(), base_ref="HEAD")
        self.assertEqual("tracked", tracked.source_mode)

        (self.repo / ".gitignore").write_text("docs/\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-m", "ignore docs")
        ignored_folder = self.repo / "docs" / "ignored"
        ignored_folder.mkdir(parents=True)
        (ignored_folder / "03.md").write_text(ticket_text("03"), encoding="utf-8")
        ignored = inspect_ticket_source(self.repo, ignored_folder, base_ref="HEAD")
        self.assertEqual("ignored", ignored.source_mode)

        untracked = self.repo / "untracked"
        untracked.mkdir()
        (untracked / "04.md").write_text(ticket_text("04"), encoding="utf-8")
        with self.assertRaisesRegex(TicketSourceError, "untracked and not ignored"):
            inspect_ticket_source(self.repo, untracked, base_ref="HEAD")

        tracked_ticket = self.repo / "tickets" / "01.md"
        mixed = self.repo / "mixed"
        mixed.mkdir()
        os.link(tracked_ticket, mixed / "05.md")
        git(self.repo, "add", "mixed/05.md")
        git(self.repo, "commit", "-m", "one tracked mixed ticket")
        (self.repo / ".gitignore").write_text("docs/\nmixed/06.md\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-m", "ignore one mixed ticket")
        (mixed / "06.md").write_text(ticket_text("06"), encoding="utf-8")
        with self.assertRaisesRegex(TicketSourceError, "mixes tracked and ignored"):
            inspect_ticket_source(self.repo, mixed, base_ref="HEAD")

    def test_snapshot_is_atomic_normalized_and_loads_without_caller_files(self) -> None:
        folder = self.make_ignored()
        source = inspect_ticket_source(self.repo, folder, base_ref="HEAD")
        run_dir = self.repo / ".git" / "ticket-autopilot" / "runs" / "snapshot"

        manifest_path = persist_ticket_snapshot(run_dir, source)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_digest = hashlib.sha256(
            json.dumps(
                manifest["manifest"],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(expected_digest, manifest["manifest_digest"])
        self.assertEqual(2, manifest["manifest"]["snapshot_schema"])
        self.assertEqual("ignored", manifest["manifest"]["source_mode"])
        self.assertEqual(
            {"body", "disposition", "content_digest", "envelope", "relative_path"},
            set(manifest["manifest"]["tickets"][0]),
        )

        for path in folder.glob("*.md"):
            path.unlink()
        loaded = load_ticket_snapshot(manifest_path, self.repo)
        self.assertEqual(("01", "02"), loaded.graph.order)
        self.assertEqual(source.manifest_digest, loaded.manifest_digest)

    def test_snapshot_v2_preserves_all_source_dispositions(self) -> None:
        folder = self.make_ignored()
        hold = folder / "hold"
        canceled = folder / "canceled"
        hold.mkdir()
        canceled.mkdir()
        (folder / "01.md").rename(hold / "01.md")
        (folder / "02.md").rename(canceled / "02.md")

        source = inspect_ticket_source(self.repo, folder, base_ref="HEAD")
        run_dir = self.repo / ".git" / "ticket-autopilot" / "runs" / "v2"
        loaded = load_ticket_snapshot(
            persist_ticket_snapshot(run_dir, source), self.repo
        )

        self.assertEqual(2, source.manifest["snapshot_schema"])
        self.assertEqual(
            {"01": "on-hold", "02": "canceled"},
            loaded.graph.dispositions,
        )
        self.assertEqual(
            ["on-hold", "canceled"],
            [item["disposition"] for item in source.manifest["tickets"]],
        )

    def test_snapshot_v1_loads_with_completed_compatibility(self) -> None:
        folder = self.make_ignored()
        source = inspect_ticket_source(self.repo, folder, base_ref="HEAD")
        run_dir = self.repo / ".git" / "ticket-autopilot" / "runs" / "v1"
        manifest_path = persist_ticket_snapshot(run_dir, source)
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = document["manifest"]
        manifest["snapshot_schema"] = 1
        for item in manifest["tickets"]:
            item["completed"] = item.pop("disposition") == "completed"
        document["manifest_digest"] = hashlib.sha256(
            json.dumps(
                manifest,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        manifest_path.write_text(
            json.dumps(document, ensure_ascii=False), encoding="utf-8"
        )

        loaded = load_ticket_snapshot(manifest_path, self.repo)

        self.assertEqual({"01": "open", "02": "open"}, loaded.graph.dispositions)

    def test_cli_plan_run_and_status_use_ignored_snapshot_after_source_mutation(self) -> None:
        folder = self.make_ignored()
        original_digest = ticket_source_digest(folder / "01.md")

        planned = cli(
            "plan",
            str(folder),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            cwd=self.repo,
        )["data"]
        self.assertEqual("ignored", planned["ticket_source_mode"])
        self.assertEqual(
            {"01": {"state": "pending"}, "02": {"state": "pending"}},
            planned["completion_effects"],
        )

        created = cli(
            "run",
            str(folder),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--run-id",
            "ignored-cli",
            cwd=self.repo,
        )["data"]
        worktree = Path(created["worktree"])
        self.assertEqual("ignored", created["ticket_source_mode"])
        self.assertFalse((worktree / folder.relative_to(self.repo)).exists())
        self.assertTrue(Path(created["snapshot_manifest_path"]).is_file())

        (folder / "01.md").write_text(ticket_text("changed"), encoding="utf-8")
        status = cli(
            "status",
            "ignored-cli",
            "--repo",
            str(self.repo),
            cwd=self.repo,
        )["data"]
        self.assertEqual("ignored", status["ticket_source_mode"])
        ledger = AtomicLedger(
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "ignored-cli"
            / "ledger.json"
        ).load()
        self.assertEqual(original_digest, ledger["tickets"]["01"]["ticket_digest"])

    def test_ignored_lifecycle_transition_has_tracked_parity_and_replays(self) -> None:
        folder = self.make_ignored()
        created = cli(
            "run",
            str(folder),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--run-id",
            "ignored-lifecycle",
            cwd=self.repo,
        )["data"]
        arguments = (
            "ticket-hold",
            "ignored-lifecycle",
            "01",
            "--repo",
            str(self.repo),
            "--actor",
            "user:alice",
            "--reason",
            "await decision",
            "--authority-ref",
            "decision:hold-01",
        )

        first = cli(*arguments, cwd=self.repo)["data"]
        replay = cli(*arguments, cwd=self.repo)["data"]

        self.assertEqual(
            first["lifecycle_receipt"], replay["lifecycle_receipt"]
        )
        self.assertTrue((folder / "hold" / "01.md").is_file())
        self.assertFalse((folder / "01.md").exists())
        self.assertFalse(
            (Path(created["worktree"]) / folder.relative_to(self.repo)).exists()
        )

    def test_rejects_symlink_escape_before_snapshot(self) -> None:
        folder = self.make_ignored()
        outside = Path(self.directory.name) / "outside.md"
        outside.write_text(ticket_text("03"), encoding="utf-8")
        (folder / "03.md").symlink_to(outside)

        with self.assertRaisesRegex(TicketSourceError, "symlink|escapes"):
            inspect_ticket_source(self.repo, folder, base_ref="HEAD")

    def test_cli_rejects_untracked_input_before_worktree_creation(self) -> None:
        folder = self.repo / "untracked"
        folder.mkdir()
        (folder / "01.md").write_text(ticket_text("01"), encoding="utf-8")

        rejected = cli(
            "run",
            str(folder),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--run-id",
            "rejected-source",
            cwd=self.repo,
            check=False,
        )

        self.assertFalse(rejected["ok"])
        self.assertIn("untracked and not ignored", rejected["error"]["message"])
        self.assertFalse(
            (
                self.repo.parent
                / f".{self.repo.name}-ticket-autopilot-worktrees"
                / "rejected-source"
            ).exists()
        )

    def _verified_ignored_run(self) -> tuple[Path, Path, AtomicLedger, Kernel]:
        folder = self.make_ignored()
        source = inspect_ticket_source(self.repo, folder, base_ref="HEAD")
        run_id = f"finalize-{self.sequence}"
        run_dir = self.repo / ".git" / "ticket-autopilot" / "runs" / run_id
        manifest_path = persist_ticket_snapshot(run_dir, source)
        loaded = load_ticket_snapshot(manifest_path, self.repo)
        worktree = Path(self.directory.name) / f"worktree-{self.sequence}"
        git(self.repo, "worktree", "add", "--detach", str(worktree), "HEAD")
        kernel = Kernel.new(
            run_id,
            loaded.graph,
            source_mode=loaded.source_mode,
            snapshot_manifest_digest=loaded.manifest_digest,
            snapshot_manifest_path=str(manifest_path),
            worktree=str(worktree),
            repo=str(self.repo),
            base_sha=git(worktree, "rev-parse", "HEAD"),
        )
        fixed = candidate_ref(worktree, kernel.ledger["tickets"]["01"]["ticket_digest"])
        kernel.activate("01", fixed)
        for stage in (
            "implement",
            "simplify",
            "review",
            "qa-plan",
            "qa-execute",
            "verify",
            "finalize",
        ):
            if stage in {"review", "qa-plan", "qa-execute", "verify"}:
                candidate = fixed.as_dict()
                leaf_result: dict[str, object] = {
                    "schema": 3,
                    "complete": True,
                    "candidate_ref": candidate,
                    "stage": stage,
                    "phase_contract": list(LEAF_PHASE_CONTRACTS[stage]),
                    "scope": {
                        "files_expected": [],
                        "files_inspected": [],
                        "files_remaining": [],
                    },
                    "phases_remaining": [],
                    "commands_run": [],
                    "findings": [],
                    "progress_phase": "handoff-ready",
                    "stop_reason": None,
                }
                if stage in {"qa-plan", "qa-execute", "verify"}:
                    leaf_result["quality"] = {
                        "schema": 1,
                        "causal_scope": [stage],
                        "evidence": [
                            {
                                "id": f"evidence:{stage}",
                                "artifact": f"{stage}.json",
                                "sha256": "a" * 64,
                                "result": "pass",
                                "candidate_ref": candidate,
                            }
                        ],
                        "limitations": ["local-only"],
                    }
                kernel.record_leaf_result(
                    "01", leaf_result, fixed, expected_files=[]
                )
            kernel.record_stage("01", stage, "pass", fixed)
        store = AtomicLedger(run_dir / "ledger.json")
        store.save(kernel.ledger)
        return folder, worktree, store, kernel

    def test_ignored_finalization_moves_exact_source_without_git_staging(self) -> None:
        folder, worktree, store, kernel = self._verified_ignored_run()

        self.assertTrue(finalize_done(store, kernel, "01"))

        self.assertFalse((folder / "01.md").exists())
        self.assertTrue((folder / "done" / "01.md").exists())
        summary = json.loads(
            (folder / "done" / "01.completion.json").read_text(encoding="utf-8")
        )
        self.assertEqual("01", summary["ticket_id"])
        self.assertEqual("ignored", summary["ticket_source_mode"])
        self.assertEqual("", git(worktree, "diff", "--cached", "--name-only"))
        report = kernel.report()
        self.assertEqual("ignored", report["ticket_source_mode"])
        self.assertEqual(
            "applied", report["tickets"]["01"]["completion_effect"]["state"]
        )
        self.assertIsNone(report["tickets"]["01"]["source_drift_gate"])

    def test_ignored_finalization_rejects_candidate_that_tracks_source(self) -> None:
        folder, worktree, store, kernel = self._verified_ignored_run()
        relative_source = folder.relative_to(self.repo) / "01.md"
        promoted = worktree / relative_source
        promoted.parent.mkdir(parents=True)
        promoted.write_bytes((folder / "01.md").read_bytes())
        git(worktree, "add", "-f", str(relative_source))

        with self.assertRaisesRegex(
            SourceDriftError,
            "source-mode-drift.*snapshot=ignored.*observed=tracked",
        ):
            finalize_done(store, kernel, "01")

        self.assertTrue((folder / "01.md").is_file())
        self.assertFalse((folder / "done").exists())
        self.assertEqual(
            relative_source.as_posix(),
            git(worktree, "diff", "--cached", "--name-only"),
        )

    def test_ignored_source_rejects_tracking_in_reconciled_base(self) -> None:
        folder, worktree, _store, kernel = self._verified_ignored_run()
        relative_source = folder.relative_to(self.repo) / "02.md"
        git(self.repo, "add", "-f", str(relative_source))
        git(self.repo, "commit", "-m", "publish ticket source")
        integrated_base = git(self.repo, "rev-parse", "HEAD")

        with self.assertRaises(SourceModeDriftError) as raised:
            assert_ticket_source_mode(
                kernel,
                "02",
                "git:reconcile-base",
                base_ref=integrated_base,
            )

        self.assertEqual(
            {
                "schema": 1,
                "ticket_id": "02",
                "snapshot_classification": "ignored",
                "observed_classification": "tracked",
                "base_classification": "tracked",
                "boundary": "git:reconcile-base",
                "source_path": relative_source.as_posix(),
                "recovery": (
                    "publish the source tracking change separately, then start a new "
                    "run from a base where the ticket folder is tracked"
                ),
            },
            raised.exception.details,
        )
        self.assertEqual("", git(worktree, "diff", "--cached", "--name-only"))
        self.assertTrue((folder / "02.md").is_file())

    def test_ignored_finalization_replays_after_move_and_gates_drift_or_duplicate(self) -> None:
        folder, _worktree, store, kernel = self._verified_ignored_run()
        real_move = os.replace

        def move_then_crash(source: Path, destination: Path) -> None:
            real_move(source, destination)
            raise OSError("injected crash after move")

        with mock.patch("autopilot.finalizer._move_ignored_source", move_then_crash):
            with self.assertRaisesRegex(OSError, "injected crash"):
                finalize_done(store, kernel, "01")
        reloaded = Kernel(store.load())
        self.assertTrue(finalize_done(store, reloaded, "01"))
        self.assertTrue((folder / "done" / "01.completion.json").exists())

        folder2, _worktree2, store2, kernel2 = self._verified_ignored_run()
        (folder2 / "01.md").write_text(ticket_text("changed"), encoding="utf-8")
        with self.assertRaisesRegex(SourceDriftError, "digest"):
            finalize_done(store2, kernel2, "01")
        gate_id = kernel2.open_gate(
            "01",
            "source-drift",
            scope="ticket",
            reason="ignored ticket content digest changed after snapshot",
        )
        store2.save(kernel2.ledger)
        self.assertEqual(
            gate_id, kernel2.report()["tickets"]["01"]["source_drift_gate"]["gate_id"]
        )

        folder3, _worktree3, store3, kernel3 = self._verified_ignored_run()
        destination = folder3 / "done" / "01.md"
        destination.parent.mkdir()
        destination.write_text(ticket_text("01"), encoding="utf-8")
        with self.assertRaisesRegex(SourceDriftError, "both source and destination"):
            finalize_done(store3, kernel3, "01")

    def test_ignored_finalization_never_clobbers_racing_destinations(self) -> None:
        folder, _worktree, store, kernel = self._verified_ignored_run()

        def race_ticket(_source: Path, destination: Path) -> None:
            destination.write_text("racing ticket\n", encoding="utf-8")
            raise FileExistsError(destination)

        with mock.patch(
            "autopilot.finalizer._rename_no_replace",
            side_effect=race_ticket,
            create=True,
        ):
            with self.assertRaisesRegex(SourceDriftError, "appeared concurrently"):
                finalize_done(store, kernel, "01")
        self.assertEqual("racing ticket\n", (folder / "done" / "01.md").read_text())
        self.assertTrue((folder / "01.md").exists())

        folder2, _worktree2, store2, kernel2 = self._verified_ignored_run()
        real_replace = os.replace

        def race_summary(source: Path, destination: Path) -> None:
            if destination.name.endswith(".completion.json"):
                destination.write_text("racing summary\n", encoding="utf-8")
                raise FileExistsError(destination)
            real_replace(source, destination)

        with mock.patch(
            "autopilot.finalizer._rename_no_replace",
            side_effect=race_summary,
            create=True,
        ):
            with self.assertRaisesRegex(SourceDriftError, "appeared concurrently"):
                finalize_done(store2, kernel2, "01")
        self.assertEqual(
            "racing summary\n",
            (folder2 / "done" / "01.completion.json").read_text(),
        )

    def test_ignored_finalization_rejects_post_snapshot_folder_substitution(self) -> None:
        folder, _worktree, store, kernel = self._verified_ignored_run()
        original = folder.with_name(f"{folder.name}-original")
        folder.rename(original)
        substituted = self.repo / "docs" / "substituted"
        substituted.mkdir()
        (substituted / "01.md").write_text(ticket_text("01"), encoding="utf-8")
        folder.symlink_to(substituted, target_is_directory=True)

        with self.assertRaisesRegex(SourceDriftError, "folder|symlink|identity"):
            finalize_done(store, kernel, "01")

        self.assertTrue((substituted / "01.md").exists())
        self.assertFalse((substituted / "done").exists())


if __name__ == "__main__":
    unittest.main()
