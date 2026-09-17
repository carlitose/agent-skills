from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import test_wiki_sync as support
from test_kernel import record_review_handoff
from autopilot.kernel import CandidateRef
from autopilot.ledger import AtomicLedger

wiki_sync = support.wiki_sync
git = support.git
NO_DIFF_FAILURE = "tracked wiki candidate unexpectedly has no Git diff"


class WikiNoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "--initial-branch=main")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "core.autocrlf", "false")
        git(self.repo, "remote", "add", "origin", "https://github.com/example/wiki-noop.git")
        wiki = self.repo / "knowledge"
        (wiki / "wiki").mkdir(parents=True)
        (wiki / "llm-wiki-project.json").write_text(json.dumps({
            "schema": 1, "project_root": "..", "docs_globs": ["docs/specs/*.md"],
            "git_mode": "auto", "session_providers": [], "auto_sync": "enabled",
        }) + "\n", encoding="utf-8")
        (wiki / "wiki/index.md").write_text("# Old\n", encoding="utf-8")
        (wiki / "wiki/log.md").write_text("# Old log\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "integrated source before separate wiki delivery")
        self.source = git(self.repo, "rev-parse", "HEAD")
        self.candidate = support.frozen_candidate(self.repo)
        for name in ("index.md", "log.md"):
            shutil.copyfile(Path(self.candidate["candidate_path"]) / "wiki" / name, wiki / "wiki" / name)
        git(self.repo, "add", "knowledge")
        git(self.repo, "commit", "-m", "wiki already delivered by preceding ticket")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.remote = self.root / "remote.git"
        self.remote.mkdir()
        git(self.remote, "init", "--bare")
        git(self.repo, "push", str(self.remote), "main")
        (self.repo / "keep-local.txt").write_text("unrelated\n", encoding="utf-8")
        self.before = git(self.repo, "status", "--porcelain")
        self.real_run_git = wiki_sync.run_git
        self.main_reads = 0
        self.advance_to: str | None = None
        patch = mock.patch.object(wiki_sync, "run_git", side_effect=self.local_git)
        patch.start()
        self.addCleanup(patch.stop)

    def local_git(self, repo: Path, *arguments: str) -> str:
        # Only transport is redirected. Canonical GitHub identity/target validation,
        # Git objects, frozen bytes, indexes and driver/retry code remain real.
        if arguments[:2] == ("ls-remote", "--heads") and arguments[-1] == "refs/heads/main":
            self.main_reads += 1
            if self.main_reads == 2 and self.advance_to:
                git(self.repo, "push", str(self.remote), f"{self.advance_to}:refs/heads/main")
        if arguments and arguments[0] in {"ls-remote", "fetch", "push"}:
            arguments = tuple(str(self.remote) if arg == "origin" else arg for arg in arguments)
        return self.real_run_git(repo, *arguments)

    def deliver(self) -> dict:
        return wiki_sync.deliver_tracked_candidate(
            self.repo, self.candidate, base_branch="main", provider_name="github", provider_mode="live",
        )

    def assert_protected(self) -> None:
        self.assertEqual(self.base, git(self.repo, "rev-parse", "HEAD"))
        self.assertEqual(self.before, git(self.repo, "status", "--porcelain"))
        self.assertEqual("unrelated\n", (self.repo / "keep-local.txt").read_text())
        self.assertEqual("", git(self.repo, "branch", "--list", "ticket-autopilot/wiki-sync-*"))
        self.assertEqual("refs/heads/main", git(self.remote, "for-each-ref", "--format=%(refname)", "refs/heads"))

    def legacy_failure(self) -> tuple[support.Kernel, support.MemoryStore, dict]:
        kernel = support.integrated_kernel(self.repo, self.source)
        store = support.MemoryStore(self.root)

        def fail_delivery(*_args, **_kwargs):
            raise support.TransitionError(NO_DIFF_FAILURE)

        wiki_sync.drive_post_integration_sync(
            self.repo, store, kernel,
            sync_operation=lambda *_args, **_kwargs: copy.deepcopy(self.candidate),
            delivery_operation=fail_delivery,
        )
        record = copy.deepcopy(kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"])
        self.assertEqual("terminal", record["state"])
        self.assertIsNotNone(record["delivery_target"])
        return kernel, store, record

    def retry(self, kernel: support.Kernel, store: support.MemoryStore, digest: str) -> dict:
        return wiki_sync.retry_wiki_delivery(
            self.repo, store, kernel, "01", expected_record_sha256=digest,
            actor="operator", evidence="session://exact-wiki-noop-retry",
        )

    def test_exact_noop_has_bound_identity_and_no_provider_or_git_mutation(self) -> None:
        with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")):
            result = self.deliver()
        self.assertEqual("unchanged", result["status"])
        self.assertEqual("already-at-target", result["reason"])
        self.assertEqual(self.base, result["base_sha"])
        self.assertEqual(git(self.repo, "rev-parse", "HEAD^{tree}"), result["base_tree_oid"])
        self.assertEqual(self.candidate["candidate_ref"], result["candidate_ref"])
        self.assertEqual(self.candidate["validation_receipt"]["sha256"], result["validation_receipt_sha256"])
        self.assertNotIn("pr_id", result)
        self.assertNotIn("head_sha", result)
        self.assertGreaterEqual(self.main_reads, 2)
        self.assert_protected()

    def test_driver_completes_once_without_merge_or_application_evidence_transfer(self) -> None:
        for autonomous in (False, True):
            with self.subTest(autonomous=autonomous):
                kernel = support.integrated_kernel(self.repo, self.source, wiki_autonomous=autonomous)
                original = copy.deepcopy(kernel.ledger["tickets"]["01"])
                store = support.MemoryStore(self.root)
                with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")):
                    first = wiki_sync.drive_post_integration_sync(
                        self.repo, store, kernel,
                        sync_operation=lambda *_args, **_kwargs: copy.deepcopy(self.candidate),
                    )
                    saved = len(store.saved)
                    second = wiki_sync.drive_post_integration_sync(self.repo, store, kernel)
                record = kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"]
                self.assertEqual("complete", first[0]["result"])
                self.assertEqual("unchanged", record["delivery"]["status"])
                self.assertEqual([], second)
                self.assertEqual(saved, len(store.saved))
                self.assertIsNone(record["authorization"])
                for field in ("state", "candidate_ref", "validated_stages"):
                    self.assertEqual(original[field], kernel.ledger["tickets"]["01"][field])
        self.assert_protected()

    def test_noop_completion_survives_atomic_ledger_reload(self) -> None:
        # Build the fixture through real lifecycle transitions: MemoryStore alone
        # cannot detect a record that the durable ledger refuses to replay.
        template = support.integrated_kernel(self.repo, self.source)
        kernel = support.Kernel.new(
            "wiki-sync-run", support.parse_ticket_folder(support.FIXTURES / "happy"),
            provider="github", provider_mode="live", repo=str(self.repo),
            worktree=str(self.repo), snapshot_manifest_digest="a" * 64,
        )
        tree = git(self.repo, "rev-parse", f"{self.source}^{{tree}}")
        candidate = CandidateRef(tree, tree, kernel.ledger["tickets"]["01"]["ticket_digest"], 2)
        kernel.activate("01", candidate)
        for stage in ("implement", "simplify", "review", "qa-plan", "qa-execute", "verify", "finalize"):
            if stage in ("review", "qa-plan", "qa-execute", "verify"):
                record_review_handoff(kernel, "01", candidate, stage=stage)
            kernel.record_stage("01", stage, "pass", candidate)
        kernel.record_pr(
            "01", provider="github", pr_id="12", head_sha=self.source,
            branch="ticket/01", base_branch="main", base_sha=self.source,
        )
        kernel.authorize_merge("01", actor="fixture", head_sha=self.source, evidence="fixture://merge")
        integration = template.ledger["tickets"]["01"]["delivery"]
        kernel.record_delivery_metadata("01", "integration", integration["integration"])
        kernel.record_integration(
            "01", expected_head_sha=self.source, terminal_proof=integration["terminal-integration"],
        )
        store = AtomicLedger(self.root / "durable-ledger.json")
        store.save(kernel.ledger)
        with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")):
            wiki_sync.drive_post_integration_sync(
                self.repo, store, kernel,
                sync_operation=lambda *_args, **_kwargs: copy.deepcopy(self.candidate),
            )
            saved_bytes = store.path.read_bytes()
            reopened = AtomicLedger(store.path)
            resumed = support.Kernel(reopened.load())
            record = resumed.ledger["tickets"]["01"]["delivery"]["wiki-sync"]
            self.assertEqual("complete", record["state"])
            self.assertEqual("unchanged", record["delivery"]["status"])
            self.assertEqual(self.base, record["delivery"]["base_sha"])
            self.assertEqual([], wiki_sync.drive_post_integration_sync(self.repo, reopened, resumed))
            self.assertEqual(saved_bytes, store.path.read_bytes())
        self.assert_protected()

    def test_failed_git_diff_is_not_unchanged(self) -> None:
        real_run = subprocess.run

        def fail_diff(command, *args, **kwargs):
            if "diff" in command and "--cached" in command and "--name-only" in command:
                return subprocess.CompletedProcess(command, 1, stdout=b"", stderr=b"fixture Git failure")
            return real_run(command, *args, **kwargs)

        with mock.patch.object(wiki_sync.subprocess, "run", side_effect=fail_diff), mock.patch.object(
            wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")
        ):
            with self.assertRaises(wiki_sync.GitError):
                self.deliver()
        self.assert_protected()

    def test_remote_base_move_during_materialization_cannot_be_noop_success(self) -> None:
        tree = git(self.repo, "rev-parse", "HEAD^{tree}")
        self.advance_to = git(self.repo, "commit-tree", tree, "-p", self.base, "-m", "concurrent base advance")
        with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")):
            with self.assertRaises(wiki_sync.GitError):
                self.deliver()
        self.assertEqual(self.advance_to, git(self.remote, "rev-parse", "main"))
        self.assert_protected()

    def test_corrupt_frozen_content_is_rejected_before_noop(self) -> None:
        (Path(self.candidate["candidate_path"]) / "wiki/index.md").write_text("# Corrupt\n", encoding="utf-8")
        with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")):
            with self.assertRaises(support.TransitionError):
                self.deliver()
        self.assert_protected()

    def assert_changed_destination_is_not_noop(self) -> None:
        git(self.repo, "commit", "-m", "different destination corpus or mode")
        changed_head = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "push", str(self.remote), "main")
        with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")):
            # These changes are outside the candidate's exact declared diff. They
            # must fail ordinary scope validation, never become an empty success.
            with self.assertRaises(wiki_sync.GitError):
                self.deliver()
        self.assertEqual(changed_head, git(self.repo, "rev-parse", "HEAD"))
        self.assertEqual(self.before, git(self.repo, "status", "--porcelain"))

    def test_extra_tracked_markdown_is_not_noop(self) -> None:
        (self.repo / "knowledge/wiki/extra.md").write_text("# Extra\n", encoding="utf-8")
        git(self.repo, "add", "knowledge/wiki/extra.md")
        self.assert_changed_destination_is_not_noop()

    def test_missing_tracked_markdown_is_not_noop(self) -> None:
        git(self.repo, "rm", "knowledge/wiki/log.md")
        self.assert_changed_destination_is_not_noop()

    def test_executable_target_git_mode_is_not_noop(self) -> None:
        # POSIX observes the filesystem bit; Windows needs the index bit as well.
        (self.repo / "knowledge/wiki/log.md").chmod(0o755)
        git(self.repo, "update-index", "--chmod=+x", "knowledge/wiki/log.md")
        self.assert_changed_destination_is_not_noop()

    def test_exact_historical_retry_retains_predecessor_then_resumes_noop(self) -> None:
        kernel, store, previous = self.legacy_failure()
        digest = wiki_sync._digest(previous)
        with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")):
            self.assertTrue(wiki_sync.wiki_delivery_retry_status(self.repo, kernel, "01")["eligible"])
            first = self.retry(kernel, store, digest)
            writes = len(store.saved)
            replay = self.retry(kernel, store, digest)
            self.assertEqual(writes, len(store.saved))
            pending = kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"]
            self.assertEqual("delivery-pending", pending["state"])
            self.assertEqual(previous, pending["delivery_retry"]["previous_record"])
            self.assertEqual(previous["delivery_target"], pending["delivery_target"])
            self.assertFalse(first["replayed"])
            self.assertTrue(replay["replayed"])
            wiki_sync.drive_post_integration_sync(
                self.repo, store, kernel,
                sync_operation=mock.Mock(side_effect=AssertionError("unexpected recompile")),
            )
            completed = kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"]
            self.assertEqual("complete", completed["state"])
            self.assertEqual("unchanged", completed["delivery"]["status"])
            self.assertEqual(previous, completed["delivery_retry"]["previous_record"])
        self.assert_protected()

    def test_historical_retry_resumes_exact_interrupted_intent(self) -> None:
        kernel, store, previous = self.legacy_failure()
        digest = wiki_sync._digest(previous)
        with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")):
            self.retry(kernel, store, digest)
            expected = copy.deepcopy(kernel.ledger)
            interrupted = copy.deepcopy(store.saved[-2])
            resumed = support.Kernel(interrupted)
            resumed_store = support.MemoryStore(self.root)
            resumed_store.save(interrupted)
            self.assertEqual("intent-persisted", wiki_sync.wiki_delivery_retry_status(self.repo, resumed, "01")["status"])
            self.retry(resumed, resumed_store, digest)
            self.assertEqual(expected, resumed.ledger)
        self.assert_protected()

    def test_applied_retry_rechecks_frozen_integrity(self) -> None:
        kernel, store, previous = self.legacy_failure()
        digest = wiki_sync._digest(previous)
        self.retry(kernel, store, digest)
        before = copy.deepcopy(kernel.ledger)
        writes = len(store.saved)
        (Path(self.candidate["candidate_path"]) / "wiki/index.md").write_text("# Corrupt\n", encoding="utf-8")
        self.assertFalse(wiki_sync.wiki_delivery_retry_status(self.repo, kernel, "01")["eligible"])
        self.assertEqual("ineligible", wiki_sync.wiki_delivery_retry_status(self.repo, kernel, "01")["status"])
        with self.assertRaises(support.TransitionError):
            self.retry(kernel, store, digest)
        self.assertEqual(before, kernel.ledger)
        self.assertEqual(writes, len(store.saved))

    def test_historical_retry_rejects_stale_digest_without_mutation(self) -> None:
        kernel, store, _previous = self.legacy_failure()
        before = copy.deepcopy(kernel.ledger)
        writes = len(store.saved)
        with self.assertRaises(support.TransitionError):
            self.retry(kernel, store, "0" * 64)
        self.assertEqual(before, kernel.ledger)
        self.assertEqual(writes, len(store.saved))

    def test_historical_retry_rejects_target_and_provider_contradictions(self) -> None:
        kernel, _store, previous = self.legacy_failure()
        mutations = {
            "missing-target": lambda r: r.update(delivery_target=None),
            "forged-target": lambda r: r["delivery_target"].update(project_root=str(self.root / "other")),
            "prior-authorization": lambda r: r.update(authorization={"actor": "someone"}),
            "prior-publication": lambda r: r.update(publication_authorization={"actor": "someone"}),
            "prior-pr": lambda r: r["delivery"].update(pr_id="91"),
            "other-error": lambda r: r["delivery"].update(detail="arbitrary failure"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                current = copy.deepcopy(kernel.ledger)
                record = copy.deepcopy(previous)
                mutate(record)
                current["tickets"]["01"]["delivery"]["wiki-sync"] = record
                case = support.Kernel(current)
                store = support.MemoryStore(self.root)
                store.save(current)
                before = copy.deepcopy(current)
                with mock.patch.object(wiki_sync, "ProviderExecutor", side_effect=AssertionError("provider called")):
                    self.assertFalse(wiki_sync.wiki_delivery_retry_status(self.repo, case, "01")["eligible"])
                    with self.assertRaises(support.TransitionError):
                        self.retry(case, store, wiki_sync._digest(record))
                self.assertEqual(before, case.ledger)
                self.assertEqual(1, len(store.saved))
        self.assert_protected()


if __name__ == "__main__":
    unittest.main()
