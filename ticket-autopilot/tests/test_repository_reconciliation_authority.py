from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from autopilot.cli import (  # noqa: E402
    _authorized_reconciliation_event_path,
    _reconciliation_conflict_resolver,
    _reconciliation_proposal_candidate_ref,
    _recover_authorized_reconciliation_application,
)
from autopilot.git_ops import SubprocessCommandRunner  # noqa: E402
from autopilot.kernel import Kernel, STAGES  # noqa: E402
from autopilot.repository_reconciliation_authority import (  # noqa: E402
    AUTHORITY_SCOPE,
    RepositoryReconciliationAuthorityError,
    RepositoryReconciliationAuthorityStore,
    apply_conflict_proposal,
    load_proposal,
)
from autopilot.ticket_contract import parse_ticket_folder  # noqa: E402


TICKET = """---
ticket_schema: 1
ticket_id: "T-1"
execution_mode: AFK
blocked_by: []
---

# Reconcile
"""


class FakeStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.saved = 0

    def save(self, _document: dict[str, object]) -> None:
        self.saved += 1


def git(repo: Path, *args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        input=input_text,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class RepositoryReconciliationAuthorityTests(unittest.TestCase):
    def test_proposal_candidate_prefers_delivery_and_falls_back_only_when_absent(
        self,
    ) -> None:
        semantic = {"candidate_tree_oid": "semantic"}
        delivery = {"candidate_tree_oid": "delivery"}
        malformed_delivery: list[object] = []

        self.assertIs(
            delivery,
            _reconciliation_proposal_candidate_ref(
                {
                    "candidate_ref": semantic,
                    "delivery_candidate_ref": delivery,
                }
            ),
        )
        self.assertIs(
            semantic,
            _reconciliation_proposal_candidate_ref(
                {"candidate_ref": semantic, "delivery_candidate_ref": None}
            ),
        )
        self.assertIs(
            semantic,
            _reconciliation_proposal_candidate_ref(
                {"candidate_ref": semantic}
            ),
        )
        self.assertIs(
            malformed_delivery,
            _reconciliation_proposal_candidate_ref(
                {
                    "candidate_ref": semantic,
                    "delivery_candidate_ref": malformed_delivery,
                }
            ),
        )

    def make_repo(self, root: Path, name: str = "repo") -> Path:
        repo = root / name
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Test")
        git(repo, "config", "user.email", "test@example.com")
        (repo / "file.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "file.txt")
        git(repo, "commit", "-m", "base")
        git(repo, "remote", "add", "origin", f"https://github.com/example/{name}.git")
        return repo

    def test_grant_replay_revocation_binding_and_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            store = RepositoryReconciliationAuthorityStore(repo)
            grant, replayed = store.grant(
                actor="operator",
                evidence="decision://repository-reconciliation",
                scope=AUTHORITY_SCOPE,
            )
            same, replayed_again = store.grant(
                actor="operator",
                evidence="decision://repository-reconciliation",
                scope=AUTHORITY_SCOPE,
            )
            self.assertFalse(replayed)
            self.assertTrue(replayed_again)
            self.assertEqual(grant, same)
            self.assertEqual("active", store.inspect()["status"])
            with store.guard_grant(grant["grant_id"], grant["grant_digest"]):
                pass
            with self.assertRaisesRegex(
                RepositoryReconciliationAuthorityError, "contradictory provenance"
            ):
                store.grant(
                    actor="other",
                    evidence="decision://other",
                    scope=AUTHORITY_SCOPE,
                )

            revocation, replayed = store.revoke(
                actor="operator", evidence="decision://revoke"
            )
            same_revocation, replayed_again = store.revoke(
                actor="operator", evidence="decision://revoke"
            )
            self.assertFalse(replayed)
            self.assertTrue(replayed_again)
            self.assertEqual(revocation, same_revocation)
            self.assertEqual("revoked", store.inspect()["status"])
            with self.assertRaisesRegex(
                RepositoryReconciliationAuthorityError, "not active"
            ):
                with store.guard_grant(grant["grant_id"], grant["grant_digest"]):
                    pass

            envelope = json.loads(store.path.read_text(encoding="utf-8"))
            envelope["payload"]["grant"]["actor"] = "forged"
            store.path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaisesRegex(
                RepositoryReconciliationAuthorityError, "integrity mismatch"
            ):
                store.inspect()

    def test_binding_drift_and_symlinked_state_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            store = RepositoryReconciliationAuthorityStore(repo)
            store.grant(
                actor="operator",
                evidence="decision://grant",
                scope=AUTHORITY_SCOPE,
            )
            git(
                repo,
                "remote",
                "set-url",
                "origin",
                "https://github.com/example/other.git",
            )
            with self.assertRaisesRegex(
                RepositoryReconciliationAuthorityError,
                "binding contradicts",
            ):
                RepositoryReconciliationAuthorityStore(repo).inspect()

            other = self.make_repo(root, "other")
            other_store = RepositoryReconciliationAuthorityStore(other)
            other_store.path.parent.mkdir(parents=True, exist_ok=True)
            outside = root / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            try:
                other_store.path.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable")
            with self.assertRaisesRegex(
                RepositoryReconciliationAuthorityError,
                "symbolic links",
            ):
                other_store.inspect()

    def test_cli_grant_status_and_revoke_are_durable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            grant = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "grant-repository-autonomous-reconciliation",
                    "--repo",
                    str(repo),
                    "--scope",
                    AUTHORITY_SCOPE,
                    "--actor",
                    "operator",
                    "--evidence",
                    "decision://grant",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual(
                "active",
                json.loads(grant.stdout)["data"][
                    "repository_reconciliation_authority"
                ]["status"],
            )
            status = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "repository-autonomous-reconciliation-status",
                    "--repo",
                    str(repo),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual("active", json.loads(status.stdout)["data"]["status"])
            revoke = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "revoke-repository-autonomous-reconciliation",
                    "--repo",
                    str(repo),
                    "--actor",
                    "operator",
                    "--evidence",
                    "decision://revoke",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual(
                "revoked",
                json.loads(revoke.stdout)["data"][
                    "repository_reconciliation_authority"
                ]["status"],
            )

    def test_exact_proposal_resolves_only_observed_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            base = git(repo, "rev-parse", "HEAD")
            base_tree = git(repo, "rev-parse", "HEAD^{tree}")
            git(repo, "switch", "-c", "feature")
            (repo / "file.txt").write_text("feature\n", encoding="utf-8")
            git(repo, "commit", "-am", "feature")
            feature = git(repo, "rev-parse", "HEAD")
            feature_tree = git(repo, "rev-parse", "HEAD^{tree}")
            git(repo, "switch", "main")
            (repo / "file.txt").write_text("main\n", encoding="utf-8")
            git(repo, "commit", "-am", "main")
            target = git(repo, "rev-parse", "HEAD")
            target_tree = git(repo, "rev-parse", "HEAD^{tree}")
            resolved_blob = git(repo, "hash-object", "-w", "--stdin", input_text="combined\n")
            result_tree = git(
                repo,
                "mktree",
                input_text=f"100644 blob {resolved_blob}\tfile.txt\n",
            )
            store = RepositoryReconciliationAuthorityStore(repo)
            grant, _ = store.grant(
                actor="operator",
                evidence="decision://grant",
                scope=AUTHORITY_SCOPE,
            )
            binding = {
                key: grant[key]
                for key in (
                    "repository_identity",
                    "git_common_dir",
                    "provider",
                    "normalized_remote",
                )
            }
            resolutions = [
                {
                    "path": "file.txt",
                    "action": "write",
                    "mode": "100644",
                    "blob_oid": resolved_blob,
                }
            ]
            proposal = {
                "schema": 1,
                "binding": binding,
                "authority": {
                    "grant_id": grant["grant_id"],
                    "grant_digest": grant["grant_digest"],
                },
                "run_id": "run-1",
                "ticket_id": "T-1",
                "ticket_digest": "d" * 64,
                "candidate_ref": {
                    "contract_version": 2,
                    "base_tree_oid": base_tree,
                    "candidate_tree_oid": feature_tree,
                    "ticket_digest": "d" * 64,
                },
                "branch": "feature",
                "old_remote_head": feature,
                "old_local_head": feature,
                "old_local_tree": feature_tree,
                "old_target_sha": base,
                "old_target_tree": base_tree,
                "new_target_sha": target,
                "new_target_tree": target_tree,
                "conflict_paths": ["file.txt"],
                "resolutions": resolutions,
                "patch_sha256": digest(resolutions),
                "result_tree_oid": result_tree,
            }
            path = repo / "proposal.json"
            path.write_text(json.dumps(proposal), encoding="utf-8")
            context = {
                key: proposal[key]
                for key in (
                    "run_id",
                    "ticket_id",
                    "ticket_digest",
                    "candidate_ref",
                    "branch",
                    "old_remote_head",
                    "old_local_head",
                    "old_local_tree",
                    "old_target_sha",
                    "old_target_tree",
                    "new_target_sha",
                    "new_target_tree",
                )
            }
            validated = load_proposal(path, grant=grant, context=context)
            git(repo, "switch", "feature")
            rebase = subprocess.run(
                ["git", "rebase", "--onto", target, base, "feature"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, rebase.returncode)
            with store.guard_grant(grant["grant_id"], grant["grant_digest"]):
                receipt = apply_conflict_proposal(
                    repo,
                    validated,
                    runner=SubprocessCommandRunner(),
                )
            self.assertEqual("applied", receipt["result"])
            self.assertEqual(result_tree, git(repo, "rev-parse", "HEAD^{tree}"))
            self.assertEqual("combined\n", (repo / "file.txt").read_text(encoding="utf-8"))

    def test_scheduler_discovers_and_applies_proposal_without_chat_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            tickets = root / "tickets"
            tickets.mkdir()
            (tickets / "01.md").write_text(TICKET, encoding="utf-8")
            graph = parse_ticket_folder(tickets)
            base = git(repo, "rev-parse", "HEAD")
            base_tree = git(repo, "rev-parse", "HEAD^{tree}")
            git(repo, "switch", "-c", "feature")
            (repo / "file.txt").write_text("feature\n", encoding="utf-8")
            git(repo, "commit", "-am", "feature")
            semantic_tree = git(repo, "rev-parse", "HEAD^{tree}")
            (repo / "completion.txt").write_text(
                "tracked completion projection\n", encoding="utf-8"
            )
            git(repo, "add", "completion.txt")
            git(repo, "commit", "-m", "project completion")
            feature = git(repo, "rev-parse", "HEAD")
            feature_tree = git(repo, "rev-parse", "HEAD^{tree}")
            completion_blob = git(repo, "rev-parse", "HEAD:completion.txt")
            git(repo, "switch", "main")
            (repo / "file.txt").write_text("main\n", encoding="utf-8")
            git(repo, "commit", "-am", "main")
            target = git(repo, "rev-parse", "HEAD")
            target_tree = git(repo, "rev-parse", "HEAD^{tree}")
            resolved_blob = git(
                repo,
                "hash-object",
                "-w",
                "--stdin",
                input_text="approved exact result\n",
            )
            result_tree = git(
                repo,
                "mktree",
                input_text=(
                    f"100644 blob {completion_blob}\tcompletion.txt\n"
                    f"100644 blob {resolved_blob}\tfile.txt\n"
                ),
            )
            authority = RepositoryReconciliationAuthorityStore(repo)
            grant, _ = authority.grant(
                actor="operator",
                evidence="decision://persistent-reconciliation",
                scope=AUTHORITY_SCOPE,
            )
            run_directory = root / "run"
            run_directory.mkdir()
            store = FakeStore(run_directory / "ledger.json")
            kernel = Kernel.new(
                "run-1",
                graph,
                provider="github",
                repo=str(repo.resolve()),
                worktree=str(repo.resolve()),
                snapshot_manifest_digest="a" * 64,
            )
            ticket = kernel.ledger["tickets"]["T-1"]
            candidate = {
                "contract_version": 2,
                "base_tree_oid": base_tree,
                "candidate_tree_oid": semantic_tree,
                "ticket_digest": ticket["ticket_digest"],
            }
            delivery_candidate = {
                **candidate,
                "candidate_tree_oid": feature_tree,
            }
            ticket["candidate_ref"] = candidate
            ticket["delivery_candidate_ref"] = dict(delivery_candidate)
            ticket["validated_stages"] = list(STAGES)
            ticket["state"] = "pr-open"
            ticket["pr"] = {
                "provider": "github",
                "pr_id": "1",
                "head_sha": feature,
                "branch": "feature",
            }
            ticket["delivery_lineage"] = {
                "contract_version": 1,
                "provider": "github",
                "pr_id": "1",
                "branch": "feature",
                "base_branch": "main",
                "base_sha": base,
                "head_sha": feature,
            }
            gate_id = kernel.open_gate(
                "T-1",
                "stack-reconciliation",
                scope="ticket",
                reason="real rebase conflict",
            )
            resolutions = [
                {
                    "path": "file.txt",
                    "action": "write",
                    "mode": "100644",
                    "blob_oid": resolved_blob,
                }
            ]
            proposal = {
                "schema": 1,
                "binding": {
                    key: grant[key]
                    for key in (
                        "repository_identity",
                        "git_common_dir",
                        "provider",
                        "normalized_remote",
                    )
                },
                "authority": {
                    "grant_id": grant["grant_id"],
                    "grant_digest": grant["grant_digest"],
                },
                "run_id": "run-1",
                "ticket_id": "T-1",
                "ticket_digest": ticket["ticket_digest"],
                "candidate_ref": dict(delivery_candidate),
                "branch": "feature",
                "old_remote_head": feature,
                "old_local_head": feature,
                "old_local_tree": feature_tree,
                "old_target_sha": base,
                "old_target_tree": base_tree,
                "new_target_sha": target,
                "new_target_tree": target_tree,
                "conflict_paths": ["file.txt"],
                "resolutions": resolutions,
                "patch_sha256": digest(resolutions),
                "result_tree_oid": result_tree,
            }
            proposal_file = (
                run_directory
                / "artifacts"
                / "autonomous-reconciliation"
                / "T-1.json"
            )
            proposal_file.parent.mkdir(parents=True)
            proposal_file.write_text(json.dumps(proposal), encoding="utf-8")

            event_file = _authorized_reconciliation_event_path(store, kernel)
            self.assertIsNotNone(event_file)
            self.assertEqual(
                [{"operation": "reconcile", "ticket_id": "T-1"}],
                json.loads(event_file.read_text(encoding="utf-8"))["events"],
            )
            git(repo, "switch", "feature")
            rebase = subprocess.run(
                ["git", "rebase", "--onto", target, base, "feature"],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, rebase.returncode)
            resolver = _reconciliation_conflict_resolver(
                store,
                kernel,
                "T-1",
                repo,
                runner=SubprocessCommandRunner(),
            )
            receipt = resolver(
                {
                    key: proposal[key]
                    for key in (
                        "branch",
                        "old_remote_head",
                        "old_local_head",
                        "old_local_tree",
                        "old_target_sha",
                        "old_target_tree",
                        "new_target_sha",
                        "new_target_tree",
                    )
                }
            )

            self.assertEqual("applied", receipt["result"])
            self.assertEqual("passed", kernel.ledger["gates"][gate_id]["state"])
            delivery = kernel.ledger["tickets"]["T-1"]["delivery"]
            self.assertEqual(
                receipt,
                delivery["repository-reconciliation-application"],
            )
            self.assertEqual(
                grant["grant_id"],
                delivery["repository-reconciliation-adoption"]["grant_id"],
            )
            self.assertGreaterEqual(store.saved, 2)
            self.assertEqual(result_tree, git(repo, "rev-parse", "HEAD^{tree}"))

            crash_kernel = Kernel.new(
                "run-1",
                graph,
                provider="github",
                repo=str(repo.resolve()),
                worktree=str(repo.resolve()),
                snapshot_manifest_digest="a" * 64,
            )
            crash_ticket = crash_kernel.ledger["tickets"]["T-1"]
            crash_ticket["candidate_ref"] = dict(candidate)
            crash_ticket["delivery_candidate_ref"] = dict(delivery_candidate)
            crash_ticket["validated_stages"] = list(STAGES)
            crash_ticket["state"] = "pr-open"
            crash_ticket["pr"] = dict(ticket["pr"])
            crash_ticket["delivery_lineage"] = dict(ticket["delivery_lineage"])
            crash_gate = crash_kernel.open_gate(
                "T-1",
                "stack-reconciliation",
                scope="ticket",
                reason="crash after exact tree application",
            )
            proposal_sha256 = hashlib.sha256(
                json.dumps(
                    proposal, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest()
            proposal_context = {
                "run_id": "run-1",
                "ticket_id": "T-1",
                "ticket_digest": crash_ticket["ticket_digest"],
                "candidate_ref": dict(delivery_candidate),
                **{
                    key: proposal[key]
                    for key in (
                        "branch",
                        "old_remote_head",
                        "old_local_head",
                        "old_local_tree",
                        "old_target_sha",
                        "old_target_tree",
                        "new_target_sha",
                        "new_target_tree",
                    )
                },
            }
            crash_kernel.record_delivery_metadata(
                "T-1",
                "repository-reconciliation-adoption",
                {
                    "schema": 1,
                    "grant_id": grant["grant_id"],
                    "grant_digest": grant["grant_digest"],
                    "proposal_sha256": proposal_sha256,
                    "proposal_path": str(proposal_file),
                    "context": proposal_context,
                    "result": "adopted",
                },
            )
            crash_store = FakeStore(run_directory / "ledger.json")
            _recover_authorized_reconciliation_application(
                crash_store,
                crash_kernel,
                repo,
                runner=SubprocessCommandRunner(),
            )
            recovered = crash_kernel.ledger["tickets"]["T-1"]["delivery"][
                "repository-reconciliation-application"
            ]
            self.assertEqual("recovered", recovered["result"])
            self.assertEqual(
                "passed", crash_kernel.ledger["gates"][crash_gate]["state"]
            )
            self.assertEqual(1, crash_store.saved)

    def test_proposal_drift_extra_paths_and_digest_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            store = RepositoryReconciliationAuthorityStore(repo)
            grant, _ = store.grant(
                actor="operator", evidence="decision://grant", scope=AUTHORITY_SCOPE
            )
            oid = git(repo, "rev-parse", "HEAD")
            tree = git(repo, "rev-parse", "HEAD^{tree}")
            resolutions = [{"path": "file.txt", "action": "delete"}]
            proposal = {
                "schema": 1,
                "binding": {
                    key: grant[key]
                    for key in (
                        "repository_identity",
                        "git_common_dir",
                        "provider",
                        "normalized_remote",
                    )
                },
                "authority": {
                    "grant_id": grant["grant_id"],
                    "grant_digest": grant["grant_digest"],
                },
                "run_id": "run-1",
                "ticket_id": "T-1",
                "ticket_digest": "d" * 64,
                "candidate_ref": {
                    "contract_version": 2,
                    "base_tree_oid": tree,
                    "candidate_tree_oid": tree,
                    "ticket_digest": "d" * 64,
                },
                "branch": "feature",
                "old_remote_head": oid,
                "old_local_head": oid,
                "old_local_tree": tree,
                "old_target_sha": oid,
                "old_target_tree": tree,
                "new_target_sha": oid,
                "new_target_tree": tree,
                "conflict_paths": ["file.txt"],
                "resolutions": resolutions,
                "patch_sha256": "0" * 64,
                "result_tree_oid": tree,
            }
            path = repo / "proposal.json"
            path.write_text(json.dumps(proposal), encoding="utf-8")
            context = {
                key: proposal[key]
                for key in (
                    "run_id", "ticket_id", "ticket_digest", "candidate_ref",
                    "branch", "old_remote_head", "old_local_head", "old_local_tree", "old_target_sha",
                    "old_target_tree", "new_target_sha", "new_target_tree",
                )
            }
            with self.assertRaisesRegex(
                RepositoryReconciliationAuthorityError, "patch digest"
            ):
                load_proposal(path, grant=grant, context=context)
            proposal["patch_sha256"] = digest(resolutions)
            proposal["conflict_paths"] = ["../escape"]
            proposal["resolutions"] = [{"path": "../escape", "action": "delete"}]
            proposal["patch_sha256"] = digest(proposal["resolutions"])
            path.write_text(json.dumps(proposal), encoding="utf-8")
            with self.assertRaisesRegex(
                RepositoryReconciliationAuthorityError, "normalized"
            ):
                load_proposal(path, grant=grant, context=context)


if __name__ == "__main__":
    unittest.main()
