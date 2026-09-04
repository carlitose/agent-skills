from __future__ import annotations

import copy
import shutil
import subprocess
import sys
import tempfile
import unittest
import json
import hashlib
import stat
from pathlib import Path
from typing import Any
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))

from autopilot.cli import build_parser  # noqa: E402
from autopilot.kernel import Kernel, TransitionError  # noqa: E402
from autopilot.ticket_contract import parse_ticket_folder  # noqa: E402
from autopilot.providers import (  # noqa: E402
    GET_APPROVALS,
    GET_CHECKS_AND_POLICIES,
    GET_PR_STATE,
    MERGE_EXPECTED_HEAD,
)
from autopilot.git_ops import CommandResult  # noqa: E402
from autopilot.terminal_integration import canonical_digest  # noqa: E402
from autopilot.wiki_sync import (  # noqa: E402
    _autonomous_reasons,
    _bound_project_target,
    _delivery_target,
    _digest,
    _wiki_contract_digest,
    approve_wiki_sync,
    deliver_tracked_candidate,
    drive_post_integration_sync,
    retry_wiki_delivery,
    wiki_delivery_retry_status,
)


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout.strip()


class MemoryStore:
    def __init__(self, root: Path) -> None:
        self.path = root / "ledger.json"
        self.saved: list[dict[str, Any]] = []
        self.document: dict[str, Any] | None = None

    def save(self, document: dict[str, Any]) -> None:
        self.document = copy.deepcopy(document)
        self.saved.append(copy.deepcopy(document))

    def load(self) -> dict[str, Any]:
        if self.document is None:
            raise AssertionError("memory store has no saved document")
        return copy.deepcopy(self.document)


class DeliveryGitHubRunner:
    def __init__(self) -> None:
        self.created = False
        self.branch = ""
        self.base = ""
        self.body = ""

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        if command[:3] == ["gh", "pr", "list"]:
            return CommandResult(
                json.dumps([{"number": 73}] if self.created else []), "", 0
            )
        if command[:3] == ["gh", "pr", "create"]:
            self.created = True
            self.branch = command[command.index("--head") + 1]
            self.base = command[command.index("--base") + 1]
            self.body = command[command.index("--body") + 1]
            return CommandResult("https://github.example/pr/73", "", 0)
        if command[:3] == ["gh", "pr", "view"]:
            head = git(cwd, "rev-parse", f"refs/heads/{self.branch}")
            return CommandResult(
                json.dumps(
                    {
                        "number": 73,
                        "url": "https://github.example/pr/73",
                        "state": "OPEN",
                        "mergedAt": None,
                        "headRefName": self.branch,
                        "headRefOid": head,
                        "baseRefName": self.base,
                        "body": self.body,
                        "reviewDecision": "",
                        "reviews": [],
                        "mergeable": "MERGEABLE",
                        "mergeStateStatus": "CLEAN",
                    }
                ),
                "",
                0,
            )
        raise AssertionError(command)


def frozen_candidate(target: Path) -> dict[str, Any]:
    wiki_identity = str(target / "knowledge")
    wiki_ref = {
        "contract_version": "wiki-sync-v1",
        "origin": {"kind": "integrated-ticket", "id": "fixture-origin"},
        "pre_sync_tree_sha256": "b" * 64,
        "project_root": str(target),
        "triggers": ["post-integration"],
        "wiki_identity": wiki_identity,
    }
    sync_digest = _wiki_contract_digest(wiki_ref)
    wiki_ref["digest"] = sync_digest
    common_raw = Path(git(target, "rev-parse", "--git-common-dir"))
    common = (
        (target / common_raw).resolve()
        if not common_raw.is_absolute()
        else common_raw.resolve()
    )
    staging = common / "llm-wiki" / "candidates" / sync_digest / "pending"
    (staging / "wiki").mkdir(parents=True)
    (staging / "wiki" / "index.md").write_text("# Canonical\n", encoding="utf-8")
    (staging / "wiki" / "log.md").write_text("# Log\n", encoding="utf-8")
    entries = []
    for path in sorted((staging / "wiki").glob("*.md")):
        entries.append(
            {
                "path": path.relative_to(staging).as_posix(),
                "kind": "file",
                "mode": stat.S_IMODE(path.stat().st_mode),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    tree = _wiki_contract_digest(entries)
    destination = staging.parent / tree
    staging.rename(destination)
    candidate_ref = {
        "contract_version": "wiki-sync-v1",
        "profile": "wiki-sync-v1",
        "base_tree_sha256": "b" * 64,
        "candidate_tree_sha256": tree,
        "wiki_sync_ref": sync_digest,
    }
    receipt = {"claim_ceiling": "implementation-complete"}
    receipt["sha256"] = _wiki_contract_digest(receipt)
    (destination / "manifest.json").write_text(
        json.dumps(
            {"candidate_ref": candidate_ref, "validation_receipt": receipt},
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "contract_version": "wiki-sync-v1",
        "status": "candidate-created",
        "reason": "manual-authorization",
        "wiki_sync_ref": wiki_ref,
        "candidate_ref": candidate_ref,
        "candidate_path": str(destination),
        "wiki_identity": wiki_identity,
        "changed_paths": ["wiki/index.md", "wiki/log.md"],
        "validation_receipt": receipt,
        "attempt": 1,
        "retry": {"disposition": "terminal", "max_attempts": 1},
    }


def integrated_kernel(
    repo: Path, head_sha: str, *, wiki_autonomous: bool = False
) -> Kernel:
    kernel = Kernel.new(
        "wiki-sync-run",
        parse_ticket_folder(FIXTURES / "happy"),
        provider="github",
        provider_mode="live",
        repo=str(repo),
        worktree=str(repo),
        snapshot_manifest_digest="a" * 64,
        wiki_sync_merge_policy=("autonomous" if wiki_autonomous else "manual"),
        wiki_sync_merge_actor=("runner" if wiki_autonomous else None),
        wiki_sync_merge_evidence=(
            "run://afk-complete" if wiki_autonomous else None
        ),
    )
    ticket = kernel.ledger["tickets"]["01"]
    ticket["state"] = "integrated"
    ticket["preexisting_integrated"] = False
    ticket["disposition"] = "completed"
    ticket["pr"] = {
        "provider": "github",
        "pr_id": "12",
        "branch": "ticket/01",
        "base": "main",
        "head_sha": head_sha,
    }
    ticket["delivery_lineage"] = {
        "provider": "github",
        "pr_id": "12",
        "branch": "ticket/01",
        "base_branch": "main",
        "base_sha": head_sha,
        "head_sha": head_sha,
        "contract_version": 1,
    }
    observation = {
        "schema": 1,
        "provider": "github",
        "operation": "get-pr-state",
        "evidence_class": "live",
        "observed": True,
        "pr_id": "12",
        "head_sha": head_sha,
        "base": "main",
        "merge_commit_sha": head_sha,
        "state": "merged",
    }
    ticket["delivery"]["integration"] = observation
    ticket["delivery"]["terminal-integration"] = {
        "schema": 1,
        "repository_identity": str(repo),
        "provider": "github",
        "pr_id": "12",
        "head_sha": head_sha,
        "pr_base": "main",
        "terminal_branch": "main",
        "terminal_sha": head_sha,
        "terminal_tree_oid": git(repo, "rev-parse", f"{head_sha}^{{tree}}"),
        "merge_commit_sha": head_sha,
        "reachable_kind": "head",
        "reachable_sha": head_sha,
        "provider_observation_digest": canonical_digest(observation),
        "delivery_lineage_digest": canonical_digest(ticket["delivery_lineage"]),
        "provenance": "runner-merge",
    }
    candidate = {
        "contract_version": 2,
        "ticket_digest": ticket["ticket_digest"],
        "base_tree_oid": "base-tree",
        "candidate_tree_oid": "application-tree",
    }
    ticket["candidate_ref"] = candidate
    ticket["delivery_candidate_ref"] = candidate.copy()
    ticket["validated_stages"] = [
        "implement",
        "simplify",
        "review",
        "qa-plan",
        "qa-execute",
        "verify",
        "finalize",
    ]
    return kernel


class PostIntegrationWikiSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "--initial-branch=main")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "user.name", "Test")
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "fixture")
        self.head = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _same_checkout_candidate(self) -> dict[str, Any]:
        git(
            self.repo,
            "remote",
            "add",
            "origin",
            "https://github.com/example/project.git",
        )
        return frozen_candidate(self.repo)

    def test_only_durable_non_preexisting_integration_triggers_once(self) -> None:
        states = ("pending", "active", "gated", "failed", "verified", "pr-open")
        for state in states:
            with self.subTest(state=state):
                kernel = integrated_kernel(self.repo, self.head)
                kernel.ledger["tickets"]["01"]["state"] = state
                calls: list[dict[str, Any]] = []
                result = drive_post_integration_sync(
                    self.repo,
                    MemoryStore(self.root),  # type: ignore[arg-type]
                    kernel,
                    sync_operation=lambda *_args, **kwargs: calls.append(kwargs) or {},
                )
                self.assertEqual([], result)
                self.assertEqual([], calls)

        kernel = integrated_kernel(self.repo, self.head)
        calls: list[dict[str, Any]] = []

        def sync(*_args: Any, **kwargs: Any) -> dict[str, Any]:
            calls.append(kwargs)
            return {
                "contract_version": "wiki-sync-v1",
                "status": "skipped",
                "reason": "absent",
                "attempt": kwargs["attempt"],
                "retry": {"disposition": "terminal", "max_attempts": 1},
            }

        store = MemoryStore(self.root)
        first = drive_post_integration_sync(
            self.repo, store, kernel, sync_operation=sync  # type: ignore[arg-type]
        )
        second = drive_post_integration_sync(
            self.repo, store, kernel, sync_operation=sync  # type: ignore[arg-type]
        )

        self.assertEqual(1, len(calls))
        self.assertEqual("complete", first[0]["result"])
        self.assertEqual([], second)
        self.assertEqual(self.head, calls[0]["expected_source_head"])

    def test_retryable_failure_does_not_rollback_integration(self) -> None:
        kernel = integrated_kernel(self.repo, self.head)
        attempts: list[int] = []

        def sync(*_args: Any, **kwargs: Any) -> dict[str, Any]:
            attempts.append(kwargs["attempt"])
            if len(attempts) == 1:
                return {
                    "contract_version": "wiki-sync-v1",
                    "status": "failed",
                    "reason": "stale-tree",
                    "attempt": kwargs["attempt"],
                    "retry": {"disposition": "retryable", "max_attempts": 3},
                }
            return {
                "contract_version": "wiki-sync-v1",
                "status": "unchanged",
                "reason": "no-diff",
                "attempt": kwargs["attempt"],
                "retry": {"disposition": "terminal", "max_attempts": 1},
            }

        store = MemoryStore(self.root)
        first = drive_post_integration_sync(
            self.repo, store, kernel, sync_operation=sync  # type: ignore[arg-type]
        )
        second = drive_post_integration_sync(
            self.repo, store, kernel, sync_operation=sync  # type: ignore[arg-type]
        )

        self.assertEqual([1, 2], attempts)
        self.assertEqual("retryable", first[0]["result"])
        self.assertEqual("complete", second[0]["result"])
        self.assertEqual("integrated", kernel.ledger["tickets"]["01"]["state"])

    def test_tracked_candidate_uses_separate_delivery_and_stale_auth_fails(self) -> None:
        kernel = integrated_kernel(self.repo, self.head)
        application_candidate = kernel.ledger["tickets"]["01"]["candidate_ref"].copy()
        wiki_candidate = self._same_checkout_candidate()
        sync_calls = 0
        delivery_calls = 0

        def sync(*_args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal sync_calls
            sync_calls += 1
            return {**wiki_candidate, "attempt": kwargs["attempt"]}

        def deliver(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            nonlocal delivery_calls
            delivery_calls += 1
            return {
                "schema": 1,
                "status": "pr-open",
                "pr_id": "91",
                "head_sha": "wiki-head",
                "branch": "wiki/one",
                "base": "main",
            }

        store = MemoryStore(self.root)
        first = drive_post_integration_sync(
            self.repo,
            store,  # type: ignore[arg-type]
            kernel,
            sync_operation=sync,
            delivery_operation=deliver,
        )
        second = drive_post_integration_sync(
            self.repo,
            store,  # type: ignore[arg-type]
            kernel,
            sync_operation=sync,
            delivery_operation=deliver,
        )

        self.assertEqual((1, 1), (sync_calls, delivery_calls))
        self.assertEqual("awaiting-authorization", first[0]["result"])
        self.assertEqual([], second)
        self.assertEqual(
            application_candidate,
            kernel.ledger["tickets"]["01"]["candidate_ref"],
        )
        with self.assertRaisesRegex(TransitionError, "stale"):
            approve_wiki_sync(
                self.repo,
                store,  # type: ignore[arg-type]
                kernel,
                "01",
                actor="operator",
                evidence="ticket://approval",
                head_sha="application-head",
            )

    def test_wiki_autonomous_grant_is_separate_and_run_bound(self) -> None:
        with self.assertRaisesRegex(TransitionError, "wiki-sync policy requires"):
            Kernel.new(
                "wiki-grant",
                parse_ticket_folder(FIXTURES / "happy"),
                provider="github",
                repo=str(self.repo),
                wiki_sync_merge_policy="autonomous",
            )
        kernel = Kernel.new(
            "wiki-grant",
            parse_ticket_folder(FIXTURES / "happy"),
            provider="github",
            repo=str(self.repo),
            snapshot_manifest_digest="b" * 64,
            wiki_sync_merge_policy="autonomous",
            wiki_sync_merge_actor="runner",
            wiki_sync_merge_evidence="run://afk-complete",
        )
        grant = kernel.ledger["wiki_sync_policy"]["autonomous_grant"]
        self.assertEqual("wiki-sync-v1", grant["scope"])
        self.assertIsNone(kernel.ledger["autonomous_merge_grant"])

    def test_afk_complete_continues_from_candidate_to_scoped_auto_merge(self) -> None:
        kernel = integrated_kernel(self.repo, self.head, wiki_autonomous=True)
        store = MemoryStore(self.root)
        automatic_calls: list[dict[str, Any]] = []
        wiki_candidate = self._same_checkout_candidate()

        def sync(*_args: Any, **kwargs: Any) -> dict[str, Any]:
            return {**wiki_candidate, "attempt": kwargs["attempt"]}

        def deliver(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "schema": 1,
                "status": "pr-open",
                "pr_id": "91",
                "head_sha": "wiki-head",
                "branch": "wiki/one",
                "base": "main",
            }

        def automatic(*_args: Any, **kwargs: Any) -> dict[str, Any]:
            automatic_calls.append(kwargs)
            current = kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"]
            merged = {
                **current,
                "state": "merged",
                "authorization": {
                    "scope": "wiki-sync-v1",
                    "head_sha": kwargs["head_sha"],
                },
                "result": {
                    **current["result"],
                    "status": "merged-automatically",
                    "reason": "autonomous-grant",
                },
            }
            kernel.record_delivery_metadata("01", "wiki-sync", merged)
            store.save(kernel.ledger)
            return merged

        with mock.patch("autopilot.wiki_sync.approve_wiki_sync", automatic):
            processed = drive_post_integration_sync(
                self.repo,
                store,  # type: ignore[arg-type]
                kernel,
                sync_operation=sync,
                delivery_operation=deliver,
            )

        self.assertEqual(1, len(automatic_calls))
        self.assertEqual("autonomous", automatic_calls[0]["mode"])
        self.assertEqual("wiki-head", automatic_calls[0]["head_sha"])
        self.assertEqual("merged", processed[0]["result"])

    def test_manual_wiki_merge_persists_authorization_before_exact_head_mutation(
        self,
    ) -> None:
        kernel = integrated_kernel(self.repo, self.head)
        result = self._same_checkout_candidate()
        _target, target_receipt = _delivery_target(
            self.repo, result, provider_name="github"
        )
        record = {
            "schema": 1,
            "contract_version": "ticket-post-integration-wiki-sync-v1",
            "state": "awaiting-authorization",
            "origin": {"ticket_id": "01"},
            "attempt": 1,
            "result": result,
            "delivery_target": target_receipt,
            "delivery": {
                "schema": 1,
                "status": "pr-open",
                "pr_id": "91",
                "head_sha": "wiki-head",
                "branch": "wiki/one",
                "base": "main",
            },
            "authorization": None,
        }
        kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"] = record
        observations = 0
        mutation_saw_authorization = False

        class FakeExecutor:
            def __init__(self, *_args: Any, **_kwargs: Any) -> None:
                pass

            def execute(self, operation: str, **parameters: Any) -> dict[str, Any]:
                nonlocal observations, mutation_saw_authorization
                if operation == GET_PR_STATE:
                    observations += 1
                    return {
                        "head_sha": "wiki-head",
                        "state": "open" if observations == 1 else "merged",
                    }
                if operation == GET_CHECKS_AND_POLICIES:
                    return {"head_sha": "wiki-head", "merge_mode": "direct"}
                if operation == MERGE_EXPECTED_HEAD:
                    persisted = kernel.ledger["tickets"]["01"]["delivery"][
                        "wiki-sync"
                    ]["authorization"]
                    mutation_saw_authorization = (
                        persisted["scope"] == "wiki-sync-v1"
                        and persisted["head_sha"] == parameters["expected_head"]
                        == "wiki-head"
                        and parameters["authorization"].head_sha == "wiki-head"
                    )
                    return {"merge_mode": "direct", "intent_key": parameters["intent_key"]}
                raise AssertionError(operation)

        store = MemoryStore(self.root)
        with mock.patch(
            "autopilot.wiki_sync.ProviderExecutor", FakeExecutor
        ):
            merged = approve_wiki_sync(
                self.repo,
                store,  # type: ignore[arg-type]
                kernel,
                "01",
                actor="operator",
                evidence="ticket://wiki-approval",
                head_sha="wiki-head",
            )

        self.assertTrue(mutation_saw_authorization)
        self.assertEqual("merged", merged["state"])
        self.assertEqual("integrated", kernel.ledger["tickets"]["01"]["state"])

    def test_tracked_delivery_uses_a_clean_separate_exact_diff_branch(self) -> None:
        remote = self.root / "remote.git"
        remote.mkdir()
        git(remote, "init", "--bare")
        git(self.repo, "remote", "add", "origin", str(remote))
        wiki = self.repo / "knowledge"
        (wiki / "wiki").mkdir(parents=True)
        (wiki / "wiki" / "index.md").write_text("# Old\n", encoding="utf-8")
        (wiki / "wiki" / "log.md").write_text("# Log\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "tracked wiki")
        base_head = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "push", "-u", "origin", "main")

        candidate = self.root / "candidate"
        (candidate / "wiki").mkdir(parents=True)
        (candidate / "wiki" / "index.md").write_text("# New\n", encoding="utf-8")
        (candidate / "wiki" / "log.md").write_text("# Log\n", encoding="utf-8")
        entries = []
        for path in sorted((candidate / "wiki").glob("*.md")):
            entries.append(
                {
                    "path": path.relative_to(candidate).as_posix(),
                    "kind": "file",
                    "mode": stat.S_IMODE(path.stat().st_mode),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        candidate_ref = {
            "contract_version": "wiki-sync-v1",
            "profile": "wiki-sync-v1",
            "base_tree_sha256": "b" * 64,
            "candidate_tree_sha256": _wiki_contract_digest(entries),
            "wiki_sync_ref": "w" * 64,
        }
        receipt = {"claim_ceiling": "implementation-complete"}
        receipt["sha256"] = _wiki_contract_digest(receipt)
        manifest = {
            "candidate_ref": candidate_ref,
            "validation_receipt": receipt,
        }
        (candidate / "manifest.json").write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        result = {
            "wiki_identity": str(wiki),
            "wiki_sync_ref": {"digest": "w" * 64},
            "candidate_ref": candidate_ref,
            "candidate_path": str(candidate),
            "validation_receipt": receipt,
            "changed_paths": ["wiki/index.md"],
        }

        delivery = deliver_tracked_candidate(
            self.repo,
            result,
            base_branch="main",
            provider_name="github",
            provider_mode="live",
            runner=DeliveryGitHubRunner(),
        )

        self.assertEqual("pr-open", delivery["status"])
        self.assertEqual(base_head, git(self.repo, "rev-parse", "HEAD"))
        self.assertEqual("", git(self.repo, "status", "--porcelain"))
        self.assertEqual(
            ["knowledge/wiki/index.md"],
            git(
                self.repo,
                "diff",
                "--name-only",
                base_head,
                delivery["head_sha"],
            ).splitlines(),
        )
        self.assertEqual(
            base_head,
            git(self.repo, "rev-parse", f"{delivery['head_sha']}^"),
        )

    def _cross_checkout_fixture(self) -> tuple[Path, Path, str, dict[str, Any]]:
        target = self.root / "canonical"
        fake_remote = "https://github.com/example/project.git"
        (self.repo / "knowledge").mkdir()
        (self.repo / "knowledge" / "llm-wiki-project.json").write_text(
            json.dumps({"project_root": str(target)}) + "\n", encoding="utf-8"
        )
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "wiki binding")
        head = git(self.repo, "rev-parse", "HEAD")
        subprocess.run(["git", "clone", str(self.repo), str(target)], check=True, capture_output=True)
        git(self.repo, "remote", "add", "origin", fake_remote)
        git(target, "remote", "set-url", "origin", fake_remote)
        return self.repo, target, head, frozen_candidate(target)

    def test_cross_checkout_sync_and_delivery_use_canonical_target(self) -> None:
        run_repo, target, head, candidate = self._cross_checkout_fixture()
        kernel = integrated_kernel(run_repo, head)
        store = MemoryStore(self.root)
        sync_roots: list[Path] = []
        delivery_roots: list[Path] = []
        git(target, "remote", "set-url", "origin", "git@github.com:example/project.git")
        git(run_repo, "remote", "set-url", "origin", "https://github.com/example/project.git")
        (run_repo / "ambient-run.txt").write_text("keep run\n", encoding="utf-8")
        (target / "ambient-target.txt").write_text("keep target\n", encoding="utf-8")
        before_run = git(run_repo, "status", "--porcelain")
        before_target = git(target, "status", "--porcelain")

        def sync(project_root: Path, *_args: Any, **kwargs: Any) -> dict[str, Any]:
            sync_roots.append(project_root)
            return {**candidate, "attempt": kwargs["attempt"]}

        def deliver(project_root: Path, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
            delivery_roots.append(project_root)
            persisted = kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"]
            self.assertEqual(
                str(target), persisted["delivery_target"]["project_root"]
            )
            return {
                "schema": 1,
                "status": "pr-open",
                "pr_id": "91",
                "head_sha": "wiki-head",
                "branch": "wiki/one",
                "base": "main",
            }

        processed = drive_post_integration_sync(
            run_repo,
            store,  # type: ignore[arg-type]
            kernel,
            sync_operation=sync,
            delivery_operation=deliver,
        )

        self.assertEqual([target], sync_roots)
        self.assertEqual([target], delivery_roots)
        self.assertEqual("awaiting-authorization", processed[0]["result"])
        target_receipt = kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"][
            "delivery_target"
        ]
        self.assertEqual(str(target), target_receipt["project_root"])
        self.assertEqual("github.com/example/project", target_receipt["normalized_remote"])
        self.assertEqual(
            target_receipt["receipt_sha256"],
            _digest(
                {
                    key: value
                    for key, value in target_receipt.items()
                    if key != "receipt_sha256"
                }
            ),
        )
        executor_roots: list[Path] = []

        class FakeTargetExecutor:
            def __init__(self, *_args: Any, cwd: Path, **_kwargs: Any) -> None:
                executor_roots.append(cwd)

            def execute(self, operation: str, **_parameters: Any) -> dict[str, Any]:
                if operation == GET_PR_STATE:
                    return {"head_sha": "wiki-head", "state": "merged"}
                raise AssertionError(operation)

        with mock.patch("autopilot.wiki_sync.ProviderExecutor", FakeTargetExecutor):
            approve_wiki_sync(
                run_repo,
                store,  # type: ignore[arg-type]
                kernel,
                "01",
                actor="operator",
                evidence="session://wiki-approval",
                head_sha="wiki-head",
            )
        self.assertEqual([target], executor_roots)
        self.assertEqual(before_run, git(run_repo, "status", "--porcelain"))
        self.assertEqual(before_target, git(target, "status", "--porcelain"))

    def test_cross_checkout_target_rejects_another_remote_before_operations(self) -> None:
        run_repo, target, head, _candidate = self._cross_checkout_fixture()
        git(target, "remote", "set-url", "origin", "https://github.com/example/other.git")
        kernel = integrated_kernel(run_repo, head)
        store = MemoryStore(self.root)
        calls: list[str] = []

        processed = drive_post_integration_sync(
            run_repo,
            store,  # type: ignore[arg-type]
            kernel,
            sync_operation=lambda *_args, **_kwargs: calls.append("sync") or {},
            delivery_operation=lambda *_args, **_kwargs: calls.append("delivery") or {},
        )

        record = kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"]
        self.assertEqual([], calls)
        self.assertEqual("terminal", record["state"])
        self.assertEqual("broken-binding", record["result"]["reason"])
        self.assertIn("cross-repository identity", record["result"]["detail"])
        self.assertEqual("terminal", processed[0]["result"])

    def test_delivery_target_rejects_wrong_store_and_symlinked_wiki_path(self) -> None:
        run_repo, target, _head, candidate = self._cross_checkout_fixture()
        wrong_store = copy.deepcopy(candidate)
        shutil.copytree(Path(candidate["candidate_path"]), target / "candidate-copy")
        wrong_store["candidate_path"] = str(target / "candidate-copy")
        with self.assertRaisesRegex(TransitionError, "canonical target store"):
            _delivery_target(run_repo, wrong_store, provider_name="github")

        noncanonical = copy.deepcopy(candidate)
        candidate_path = Path(candidate["candidate_path"])
        noncanonical["candidate_path"] = str(
            candidate_path.parent / ".." / candidate_path.parent.name / candidate_path.name
        )
        with self.assertRaisesRegex(TransitionError, "not canonical"):
            _delivery_target(run_repo, noncanonical, provider_name="github")

        forged_ref = copy.deepcopy(candidate)
        forged_ref["wiki_sync_ref"]["triggers"] = ["forged"]
        with self.assertRaisesRegex(TransitionError, "target digest"):
            _delivery_target(run_repo, forged_ref, provider_name="github")

        forged_identity = copy.deepcopy(candidate)
        forged_identity["wiki_identity"] = str(target / "other-wiki")
        with self.assertRaisesRegex(TransitionError, "logical wiki identity"):
            _delivery_target(run_repo, forged_identity, provider_name="github")

        (target / "wiki-alias").symlink_to(target / "knowledge", target_is_directory=True)
        symlinked_wiki = copy.deepcopy(candidate)
        symlinked_wiki["wiki_identity"] = str(target / "wiki-alias")
        symlinked_wiki["wiki_sync_ref"]["wiki_identity"] = str(
            target / "wiki-alias"
        )
        with self.assertRaisesRegex(TransitionError, "symbolic link"):
            _delivery_target(run_repo, symlinked_wiki, provider_name="github")

        source = self.root / "symlink-source"
        external = self.root / "external-project"
        source.mkdir()
        external.mkdir()
        (external / "llm-wiki-project.json").write_text(
            json.dumps({"project_root": str(target)}) + "\n", encoding="utf-8"
        )
        (source / "linked-project").symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(TransitionError, "project directory is a symbolic link"):
            _bound_project_target(run_repo, source, provider_name="github")

    def test_terminal_pre_provider_delivery_retry_is_exact_and_idempotent(self) -> None:
        run_repo, target, head, candidate = self._cross_checkout_fixture()
        kernel = integrated_kernel(run_repo, head)
        record = {
            "schema": 1,
            "contract_version": "ticket-post-integration-wiki-sync-v1",
            "state": "terminal",
            "origin": {"ticket_id": "01"},
            "attempt": 4,
            "result": candidate,
            "delivery": {
                "schema": 1,
                "status": "failed",
                "reason": "delivery-invalid",
                "detail": "tracked wiki candidate is outside the project repository",
                "retry": {"disposition": "terminal", "max_attempts": 1},
            },
            "authorization": None,
        }
        kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"] = copy.deepcopy(record)
        store = MemoryStore(self.root)
        store.save(kernel.ledger)
        expected = _digest(record)

        status = wiki_delivery_retry_status(run_repo, kernel, "01")
        first = retry_wiki_delivery(
            run_repo,
            store,  # type: ignore[arg-type]
            kernel,
            "01",
            expected_record_sha256=expected,
            actor="operator",
            evidence="session://exact-retry",
        )
        replay = retry_wiki_delivery(
            run_repo,
            store,  # type: ignore[arg-type]
            kernel,
            "01",
            expected_record_sha256=expected,
            actor="operator",
            evidence="session://exact-retry",
        )

        current = kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"]
        self.assertTrue(status["eligible"])
        self.assertEqual("delivery-pending", current["state"])
        self.assertIsNone(current["delivery"])
        self.assertEqual(record, current["delivery_retry"]["previous_record"])
        self.assertEqual(str(target), first["delivery_target"]["project_root"])
        self.assertFalse(first["replayed"])
        self.assertTrue(replay["replayed"])
        self.assertEqual("applied", current["delivery_retry"]["state"])
        self.assertEqual("prepared", current["delivery_retry"]["receipt"]["result"])
        self.assertEqual(
            "intent-persisted",
            store.saved[-2]["tickets"]["01"]["delivery"]["wiki-sync"][
                "delivery_retry"
            ]["state"],
        )
        self.assertEqual(
            "applied",
            store.saved[-1]["tickets"]["01"]["delivery"]["wiki-sync"][
                "delivery_retry"
            ]["state"],
        )
        crash_ledger = copy.deepcopy(store.saved[-2])
        crash_kernel = Kernel(crash_ledger)
        crash_store = MemoryStore(self.root)
        crash_store.save(crash_ledger)
        crash_status = wiki_delivery_retry_status(run_repo, crash_kernel, "01")
        self.assertEqual("intent-persisted", crash_status["status"])
        self.assertEqual(expected, crash_status["record_sha256"])
        self.assertEqual("operator", crash_status["retry_request"]["actor"])
        malformed_intent = copy.deepcopy(crash_ledger)
        malformed_intent["tickets"]["01"]["delivery"]["wiki-sync"][
            "delivery_retry"
        ]["request"]["unexpected"] = True
        self.assertEqual(
            "ineligible",
            wiki_delivery_retry_status(
                run_repo, Kernel(malformed_intent), "01"
            )["status"],
        )
        resumed = retry_wiki_delivery(
            run_repo,
            crash_store,  # type: ignore[arg-type]
            crash_kernel,
            "01",
            expected_record_sha256=expected,
            actor="operator",
            evidence="session://exact-retry",
        )
        self.assertFalse(resumed["replayed"])
        self.assertEqual(
            current,
            crash_kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"],
        )
        malformed_applied = copy.deepcopy(kernel.ledger)
        malformed_applied["tickets"]["01"]["delivery"]["wiki-sync"][
            "delivery_retry"
        ]["receipt"]["receipt_sha256"] = "0" * 64
        self.assertEqual(
            "ineligible",
            wiki_delivery_retry_status(
                run_repo, Kernel(malformed_applied), "01"
            )["status"],
        )

    def test_wiki_delivery_retry_cli_requires_exact_record_and_provenance(self) -> None:
        status = build_parser().parse_args(
            ["wiki-delivery-retry-status", "run-one", "--ticket", "WDT-01"]
        )
        retry = build_parser().parse_args(
            [
                "retry-wiki-delivery",
                "run-one",
                "--ticket",
                "WDT-01",
                "--expected-record-sha256",
                "a" * 64,
                "--actor",
                "operator",
                "--evidence",
                "session://retry",
            ]
        )
        self.assertEqual("WDT-01", status.ticket)
        self.assertEqual("a" * 64, retry.expected_record_sha256)
        self.assertEqual("operator", retry.actor)
        self.assertEqual("session://retry", retry.evidence)

    def test_terminal_retry_rejects_prior_provider_state_without_mutation(self) -> None:
        run_repo, _target, head, candidate = self._cross_checkout_fixture()
        kernel = integrated_kernel(run_repo, head)
        record = {
            "schema": 1,
            "contract_version": "ticket-post-integration-wiki-sync-v1",
            "state": "terminal",
            "origin": {"ticket_id": "01"},
            "attempt": 4,
            "result": candidate,
            "delivery": {
                "schema": 1,
                "status": "failed",
                "reason": "delivery-invalid",
                "detail": "tracked wiki candidate is outside the project repository",
                "retry": {"disposition": "terminal", "max_attempts": 1},
                "opaque_provider_receipt": {"pr_id": "91"},
            },
            "authorization": None,
        }
        kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"] = copy.deepcopy(record)
        store = MemoryStore(self.root)
        store.save(kernel.ledger)
        with self.assertRaisesRegex(TransitionError, "terminal pre-provider"):
            retry_wiki_delivery(
                run_repo,
                store,  # type: ignore[arg-type]
                kernel,
                "01",
                expected_record_sha256=_digest(record),
                actor="operator",
                evidence="session://exact-retry",
            )
        self.assertEqual(record, kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"])

    def test_autonomous_queue_replays_only_after_persisted_attempt(self) -> None:
        kernel = integrated_kernel(self.repo, self.head, wiki_autonomous=True)
        result = self._same_checkout_candidate()
        _target, target_receipt = _delivery_target(
            self.repo, result, provider_name="github"
        )
        kernel.ledger["tickets"]["01"]["delivery"]["wiki-sync"] = {
            "schema": 1,
            "contract_version": "ticket-post-integration-wiki-sync-v1",
            "state": "awaiting-authorization",
            "origin": {"ticket_id": "01"},
            "attempt": 1,
            "result": result,
            "delivery_target": target_receipt,
            "delivery": {
                "schema": 1,
                "status": "pr-open",
                "pr_id": "91",
                "head_sha": "wiki-head",
                "branch": "wiki/one",
                "base": "main",
            },
            "authorization": None,
        }
        observations = 0
        mutations = 0

        class QueueExecutor:
            def __init__(self, *_args: Any, **_kwargs: Any) -> None:
                pass

            def execute(self, operation: str, **parameters: Any) -> dict[str, Any]:
                nonlocal observations, mutations
                if operation == GET_PR_STATE:
                    observations += 1
                    return {
                        "schema": 1,
                        "provider": "github",
                        "operation": GET_PR_STATE,
                        "evidence_class": "live",
                        "observed": True,
                        "pr_id": "91",
                        "head_sha": "wiki-head",
                        "base": "main",
                        "state": "merged" if observations == 3 else "open",
                        "mergeable": "MERGEABLE",
                        "merge_state_status": "CLEAN",
                    }
                if operation == GET_CHECKS_AND_POLICIES:
                    return {
                        "schema": 1,
                        "provider": "github",
                        "operation": GET_CHECKS_AND_POLICIES,
                        "evidence_class": "live",
                        "observed": True,
                        "pr_id": "91",
                        "head_sha": "wiki-head",
                        "base": "main",
                        "merge_mode": "queue",
                        "active_rules": [{"type": "merge_queue"}],
                        "checks_and_policies": [],
                    }
                if operation == GET_APPROVALS:
                    return {
                        "provider": "github",
                        "operation": GET_APPROVALS,
                        "evidence_class": "live",
                        "observed": True,
                        "pr_id": "91",
                        "review_decision": "APPROVED",
                    }
                if operation == MERGE_EXPECTED_HEAD:
                    mutations += 1
                    persisted = kernel.ledger["tickets"]["01"]["delivery"][
                        "wiki-sync"
                    ]["delivery"]["merge_attempt"]
                    self_outer.assertEqual(
                        parameters["intent_key"], persisted["intent_key"]
                    )
                    return {
                        "merge_mode": "queue",
                        "intent_key": parameters["intent_key"],
                        "queue_entry": {"id": "queue-91"},
                    }
                raise AssertionError(operation)

        self_outer = self
        store = MemoryStore(self.root)
        with mock.patch("autopilot.wiki_sync.ProviderExecutor", QueueExecutor):
            queued = approve_wiki_sync(
                self.repo,
                store,  # type: ignore[arg-type]
                kernel,
                "01",
                actor="runner",
                evidence="run://afk-complete",
                head_sha="wiki-head",
                mode="autonomous",
            )
            merged = approve_wiki_sync(
                self.repo,
                store,  # type: ignore[arg-type]
                kernel,
                "01",
                actor="runner",
                evidence="run://afk-complete",
                head_sha="wiki-head",
                mode="autonomous",
            )

        self.assertEqual("queued", queued["delivery"]["status"])
        self.assertEqual("merged", merged["state"])
        self.assertEqual("merged-automatically", merged["result"]["status"])
        self.assertEqual(1, mutations)

    def test_autonomous_policy_reasons_keep_pending_checks_out_of_merge(self) -> None:
        reasons = _autonomous_reasons(
            {
                "provider": "github",
                "operation": GET_PR_STATE,
                "evidence_class": "live",
                "observed": True,
                "pr_id": "91",
                "head_sha": "wiki-head",
                "base": "main",
                "state": "open",
                "mergeable": "MERGEABLE",
                "merge_state_status": "CLEAN",
            },
            {
                "provider": "github",
                "operation": GET_CHECKS_AND_POLICIES,
                "evidence_class": "live",
                "observed": True,
                "pr_id": "91",
                "head_sha": "wiki-head",
                "base": "main",
                "merge_mode": "direct",
                "active_rules": [],
                "checks_and_policies": [
                    {
                        "bucket": "pending",
                        "name": "tests",
                        "state": "EXPECTED",
                        "workflow": "",
                    }
                ],
            },
            {
                "provider": "github",
                "operation": GET_APPROVALS,
                "evidence_class": "live",
                "observed": True,
                "pr_id": "91",
                "review_decision": "APPROVED",
            },
            provider="github",
            pr_id="91",
            head_sha="wiki-head",
        )

        self.assertIn("required checks are pending, failed, or malformed", reasons)


if __name__ == "__main__":
    unittest.main()
