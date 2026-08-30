from __future__ import annotations

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
    _adopt_repository_merge_authority,
    _classify_merge_all_result,
)
from autopilot.kernel import Kernel, STAGES  # noqa: E402
from autopilot.repository_merge_authority import (  # noqa: E402
    AUTHORITY_SCOPE,
    RepositoryMergeAuthorityError,
    RepositoryMergeAuthorityStore,
    discover_run_ledgers,
    is_repository_adoption_evidence,
)
from autopilot.ticket_contract import parse_ticket_folder  # noqa: E402


TICKET = """---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by: []
---

# Test ticket
"""


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


class FakeStore:
    def __init__(self) -> None:
        self.saved = 0

    def save(self, _document: dict[str, object]) -> None:
        self.saved += 1


class RepositoryMergeAuthorityTests(unittest.TestCase):
    def make_repo(self, root: Path, name: str = "repo") -> Path:
        repo = root / name
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Test")
        git(repo, "config", "user.email", "test@example.com")
        (repo / "README.md").write_text("test\n", encoding="utf-8")
        git(repo, "add", "README.md")
        git(repo, "commit", "-m", "initial")
        git(repo, "remote", "add", "origin", f"https://github.com/example/{name}.git")
        return repo

    def test_grant_exact_replay_guard_revocation_and_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            store = RepositoryMergeAuthorityStore(repo)

            grant, replayed = store.grant(
                actor="operator",
                evidence="artifact://repository-merge-authority",
                scope=AUTHORITY_SCOPE,
            )
            replay, replayed_again = store.grant(
                actor="operator",
                evidence="artifact://repository-merge-authority",
                scope=AUTHORITY_SCOPE,
            )

            self.assertFalse(replayed)
            self.assertTrue(replayed_again)
            self.assertEqual(grant, replay)
            self.assertEqual("active", store.inspect()["status"])
            evidence = store.adoption_evidence(grant)
            self.assertTrue(is_repository_adoption_evidence(evidence))
            run_grant = {
                "repository_identity": str(repo.resolve()),
                "provider": "github",
                "actor": "operator",
                "evidence": evidence,
            }
            self.assertEqual(grant, store.assert_run_grant(run_grant))
            with store.guard_run_grant(run_grant) as guarded:
                self.assertEqual(grant, guarded)

            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "contradictory provenance"
            ):
                store.grant(
                    actor="another",
                    evidence="artifact://other",
                    scope=AUTHORITY_SCOPE,
                )

            revocation, revoke_replayed = store.revoke(
                actor="operator",
                evidence="artifact://repository-merge-revocation",
            )
            same_revocation, revoke_replayed_again = store.revoke(
                actor="operator",
                evidence="artifact://repository-merge-revocation",
            )
            self.assertFalse(revoke_replayed)
            self.assertTrue(revoke_replayed_again)
            self.assertEqual(revocation, same_revocation)
            self.assertEqual("revoked", store.inspect()["status"])
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "is not active"
            ):
                store.assert_run_grant(run_grant)
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "revoked"
            ):
                store.grant(
                    actor="operator",
                    evidence="artifact://repository-merge-authority",
                    scope=AUTHORITY_SCOPE,
                )

            envelope = json.loads(store.path.read_text(encoding="utf-8"))
            envelope["payload"]["grant"]["actor"] = "forged"
            store.path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "integrity mismatch"
            ):
                store.inspect()

    def test_binding_drift_and_symlinked_state_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            store = RepositoryMergeAuthorityStore(repo)
            store.grant(
                actor="operator",
                evidence="artifact://grant",
                scope=AUTHORITY_SCOPE,
            )
            git(repo, "remote", "set-url", "origin", "https://github.com/example/other.git")
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "binding contradicts"
            ):
                RepositoryMergeAuthorityStore(repo).inspect()

            repo2 = self.make_repo(root, "repo2")
            store2 = RepositoryMergeAuthorityStore(repo2)
            store2.path.parent.mkdir(parents=True, exist_ok=True)
            target = root / "outside.json"
            target.write_text("{}", encoding="utf-8")
            try:
                store2.path.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable")
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "symbolic links"
            ):
                store2.inspect()

    def test_current_and_future_manual_runs_adopt_only_when_merge_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            tickets = repo / "tickets"
            tickets.mkdir()
            (tickets / "01.md").write_text(TICKET, encoding="utf-8")
            graph = parse_ticket_folder(tickets)
            authority = RepositoryMergeAuthorityStore(repo)
            grant, _ = authority.grant(
                actor="operator",
                evidence="artifact://grant",
                scope=AUTHORITY_SCOPE,
            )

            mismatched = Kernel.new(
                "provider-mismatch",
                graph,
                provider="azure-devops",
                repo=str(repo.resolve()),
                snapshot_manifest_digest="a" * 64,
            )
            mismatch_ticket = mismatched.ledger["tickets"]["01"]
            mismatch_candidate = {
                "contract_version": 2,
                "base_tree_oid": "a" * 40,
                "candidate_tree_oid": "b" * 40,
                "ticket_digest": mismatch_ticket["ticket_digest"],
            }
            mismatch_ticket["candidate_ref"] = mismatch_candidate
            mismatch_ticket["delivery_candidate_ref"] = dict(mismatch_candidate)
            mismatch_ticket["validated_stages"] = list(STAGES)
            mismatch_ticket["state"] = "pr-open"
            mismatch_ticket["pr"] = {
                "provider": "azure-devops",
                "pr_id": "1",
                "head_sha": "c" * 40,
            }
            mismatch_store = FakeStore()
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "provider contradicts"
            ):
                _adopt_repository_merge_authority(mismatch_store, mismatched)
            self.assertEqual(0, mismatch_store.saved)
            self.assertEqual("manual", mismatched.ledger["merge_policy"])

            for run_id in ("current-run", "future-run"):
                kernel = Kernel.new(
                    run_id,
                    graph,
                    provider="github",
                    repo=str(repo.resolve()),
                    snapshot_manifest_digest="a" * 64,
                )
                ticket = kernel.ledger["tickets"]["01"]
                candidate = {
                    "contract_version": 2,
                    "base_tree_oid": "a" * 40,
                    "candidate_tree_oid": "b" * 40,
                    "ticket_digest": ticket["ticket_digest"],
                }
                ticket["candidate_ref"] = candidate
                ticket["delivery_candidate_ref"] = dict(candidate)
                ticket["validated_stages"] = list(STAGES)
                ticket["state"] = "pr-open"
                ticket["pr"] = {
                    "provider": "github",
                    "pr_id": "1",
                    "head_sha": "c" * 40,
                }
                fake = FakeStore()

                adoption = _adopt_repository_merge_authority(fake, kernel)

                self.assertIsNotNone(adoption)
                self.assertEqual(1, fake.saved)
                self.assertEqual("autonomous", kernel.ledger["merge_policy"])
                run_grant = kernel.ledger["autonomous_merge_grant"]
                self.assertEqual(grant["actor"], run_grant["actor"])
                self.assertEqual(
                    authority.adoption_evidence(grant), run_grant["evidence"]
                )

            authority.revoke(actor="operator", evidence="artifact://revoke")
            kernel = Kernel.new(
                "post-revoke",
                graph,
                provider="github",
                repo=str(repo.resolve()),
                snapshot_manifest_digest="a" * 64,
            )
            ticket = kernel.ledger["tickets"]["01"]
            candidate = {
                "contract_version": 2,
                "base_tree_oid": "a" * 40,
                "candidate_tree_oid": "b" * 40,
                "ticket_digest": ticket["ticket_digest"],
            }
            ticket["candidate_ref"] = candidate
            ticket["delivery_candidate_ref"] = dict(candidate)
            ticket["validated_stages"] = list(STAGES)
            ticket["state"] = "pr-open"
            ticket["pr"] = {"provider": "github", "pr_id": "1", "head_sha": "c" * 40}
            self.assertIsNone(
                _adopt_repository_merge_authority(FakeStore(), kernel)
            )
            self.assertEqual("manual", kernel.ledger["merge_policy"])

    def test_discovery_is_sorted_and_rejects_symlinked_run_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            runs = Path(git(repo, "rev-parse", "--git-common-dir"))
            if not runs.is_absolute():
                runs = (repo / runs).resolve()
            runs = runs / "ticket-autopilot" / "runs"
            for run_id in ("z-run", "a-run"):
                folder = runs / run_id
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "ledger.json").write_text("{}", encoding="utf-8")
            self.assertEqual(
                ["a-run", "z-run"],
                [path.parent.name for path in discover_run_ledgers(repo)],
            )
            target = root / "outside"
            target.mkdir()
            link = runs / "linked-run"
            try:
                link.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable")
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "symbolic link"
            ):
                discover_run_ledgers(repo)

    def test_merge_all_result_taxonomy_is_closed(self) -> None:
        self.assertEqual(
            "integrated", _classify_merge_all_result({"result": "integrated"})
        )
        self.assertEqual("gated", _classify_merge_all_result({"result": "gated"}))
        self.assertEqual("gated", _classify_merge_all_result({"result": "queued"}))
        self.assertEqual(
            "reconciliation-required",
            _classify_merge_all_result({"result": "unexpected"}),
        )
        self.assertEqual(
            "reconciliation-required", _classify_merge_all_result({})
        )

    def test_cli_grant_discovers_current_and_future_runs_then_revokes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            tickets = repo / "tickets"
            tickets.mkdir()
            (tickets / "01.md").write_text(TICKET, encoding="utf-8")
            git(repo, "add", "tickets/01.md")
            git(repo, "commit", "-m", "ticket")
            current = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "run",
                    str(tickets),
                    "--repo",
                    str(repo),
                    "--provider",
                    "github",
                    "--provider-mode",
                    "simulated",
                    "--run-id",
                    "current-run",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual("current-run", json.loads(current.stdout)["data"]["run_id"])
            grant = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "grant-repository-autonomous-merge",
                    "--repo",
                    str(repo),
                    "--scope",
                    AUTHORITY_SCOPE,
                    "--actor",
                    "operator",
                    "--evidence",
                    "artifact://grant",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual("active", json.loads(grant.stdout)["data"]["repository_authority"]["status"])

            merged = subprocess.run(
                [sys.executable, "-B", str(CLI), "merge-all", "--repo", str(repo)],
                text=True,
                capture_output=True,
                check=True,
            )
            current_results = json.loads(merged.stdout)["data"]["runs"]
            self.assertEqual(["current-run"], [item["run_id"] for item in current_results])
            self.assertEqual("skipped", current_results[0]["result"])

            future = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "run",
                    str(tickets),
                    "--repo",
                    str(repo),
                    "--provider",
                    "github",
                    "--provider-mode",
                    "simulated",
                    "--run-id",
                    "future-run",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual("future-run", json.loads(future.stdout)["data"]["run_id"])
            both = subprocess.run(
                [sys.executable, "-B", str(CLI), "merge-all", "--repo", str(repo)],
                text=True,
                capture_output=True,
                check=True,
            )
            both_results = json.loads(both.stdout)["data"]["runs"]
            self.assertEqual(
                ["current-run", "future-run"],
                sorted(item["run_id"] for item in both_results),
            )
            self.assertTrue(all(item["result"] == "skipped" for item in both_results))

            revoked = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "revoke-repository-autonomous-merge",
                    "--repo",
                    str(repo),
                    "--actor",
                    "operator",
                    "--evidence",
                    "artifact://revoke",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual("revoked", json.loads(revoked.stdout)["data"]["repository_authority"]["status"])
            failed = subprocess.run(
                [sys.executable, "-B", str(CLI), "merge-all", "--repo", str(repo)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, failed.returncode)
            self.assertIn("requires an active", json.loads(failed.stdout)["error"]["message"])


if __name__ == "__main__":
    unittest.main()
