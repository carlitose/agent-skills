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

from autopilot.repository_authority import canonical_bytes, digest  # noqa: E402
from autopilot.repository_merge_authority import (  # noqa: E402
    AUTHORITY_SCOPE,
    RepositoryMergeAuthorityError,
    RepositoryMergeAuthorityStore,
)
from autopilot.repository_reconciliation_authority import (  # noqa: E402
    RepositoryReconciliationAuthorityError,
    RepositoryReconciliationAuthorityStore,
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


def write_legacy_state(store: object, *, revoked: bool = False) -> tuple[str, dict[str, object]]:
    kind = store.kind
    binding = store.binding.legacy_dict()
    unsigned: dict[str, object] = {
        "schema": 1,
        "grant_id": "",
        **binding,
        "scope": AUTHORITY_SCOPE,
        "actor": "legacy-operator",
        "evidence": f"decision://legacy-{kind.name}",
    }
    if kind.policy_version is not None:
        unsigned["policy_version"] = kind.policy_version
    identity = {key: value for key, value in unsigned.items() if key != "grant_id"}
    unsigned["grant_id"] = f"{kind.grant_prefix}-{digest(identity)[:20]}"
    grant = {**unsigned, "grant_digest": digest(unsigned)}
    event_unsigned = {
        "sequence": 1,
        "event": kind.grant_event,
        "details": grant,
        "previous_hash": "0" * 64,
    }
    history = [{**event_unsigned, "hash": digest(event_unsigned)}]
    revocation = None
    if revoked:
        revocation = {
            "schema": 1,
            "grant_id": grant["grant_id"],
            "grant_digest": grant["grant_digest"],
            "actor": "legacy-operator",
            "evidence": f"decision://legacy-{kind.name}-revoked",
        }
        revoke_unsigned = {
            "sequence": 2,
            "event": kind.revoke_event,
            "details": revocation,
            "previous_hash": history[-1]["hash"],
        }
        history.append({**revoke_unsigned, "hash": digest(revoke_unsigned)})
    state = {
        "schema": 1,
        "binding": binding,
        "grant": grant,
        "revocation": revocation,
        "history": history,
    }
    envelope = {
        "envelope_schema": 1,
        "integrity": digest(state),
        "payload": state,
    }
    store.path.parent.mkdir(parents=True, exist_ok=True)
    store.path.write_bytes(canonical_bytes(envelope) + b"\n")
    return hashlib.sha256(store.path.read_bytes()).hexdigest(), state


class RepositoryAuthorityMigrationTests(unittest.TestCase):
    def make_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Test")
        git(repo, "config", "user.email", "test@example.com")
        (repo / "README.md").write_text("authority\n", encoding="utf-8")
        git(repo, "add", "README.md")
        git(repo, "commit", "-m", "initial")
        git(repo, "remote", "add", "origin", "https://github.com/example/authority.git")
        return repo

    def add_linked_worktree(self, repo: Path, root: Path) -> Path:
        sibling = root / "sibling"
        git(repo, "worktree", "add", "--detach", str(sibling), "HEAD")
        return sibling

    def test_fresh_schema2_is_shared_by_linked_worktrees_not_clone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            sibling = self.add_linked_worktree(repo, root)
            original = RepositoryMergeAuthorityStore(repo)
            grant, _ = original.grant(
                actor="operator", evidence="decision://grant", scope=AUTHORITY_SCOPE
            )

            sibling_projection = RepositoryMergeAuthorityStore(sibling).inspect()
            self.assertEqual("active", sibling_projection["status"])
            self.assertEqual(grant, sibling_projection["grant"])
            self.assertNotIn("repository_identity", sibling_projection["binding"])
            self.assertEqual(str(sibling.resolve()), sibling_projection["observation"]["repository_root"])
            status = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "repository-autonomous-merge-status",
                    "--repo",
                    str(sibling),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual("active", json.loads(status.stdout)["data"]["status"])

            clone = root / "clone"
            git(root, "clone", str(repo), str(clone))
            git(clone, "remote", "set-url", "origin", "https://github.com/example/authority.git")
            self.assertEqual(
                "absent", RepositoryMergeAuthorityStore(clone).inspect()["status"]
            )

    def test_active_legacy_migration_is_explicit_exact_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            sibling = self.add_linked_worktree(repo, root)
            original = RepositoryMergeAuthorityStore(repo)
            source_sha256, legacy = write_legacy_state(original)
            before = original.path.read_bytes()

            self.assertEqual("active", original.inspect()["status"])
            sibling_store = RepositoryMergeAuthorityStore(sibling)
            sibling_projection = sibling_store.inspect()
            self.assertEqual(
                "legacy-binding-migration-required", sibling_projection["status"]
            )
            self.assertEqual(source_sha256, sibling_projection["migration"]["state_sha256"])
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "requires explicit migration"
            ):
                sibling_store.active_grant()
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "SHA-256 drifted"
            ):
                sibling_store.migrate(
                    expected_state_sha256="0" * 64,
                    actor="operator",
                    evidence="decision://migrate",
                )
            self.assertEqual(before, original.path.read_bytes())

            receipt, replayed = sibling_store.migrate(
                expected_state_sha256=source_sha256,
                actor="operator",
                evidence="decision://migrate",
            )
            same, replayed_again = original.migrate(
                expected_state_sha256=source_sha256,
                actor="operator",
                evidence="decision://migrate",
            )
            self.assertFalse(replayed)
            self.assertTrue(replayed_again)
            self.assertEqual(receipt, same)
            self.assertEqual("migrated", receipt["result"])
            intent_path, receipt_path = original._migration_paths(source_sha256)
            self.assertEqual(
                hashlib.sha256(intent_path.read_bytes()).hexdigest(),
                receipt["intent_sha256"],
            )
            self.assertTrue(receipt_path.is_file())
            self.assertEqual("active", original.inspect()["status"])
            self.assertEqual("active", sibling_store.inspect()["status"])
            state = original.load()
            self.assertEqual(2, state["schema"])
            self.assertEqual(legacy, state["provenance"]["predecessor"]["state"])
            self.assertEqual(
                source_sha256,
                state["provenance"]["migration"]["source_state_sha256"],
            )
            self.assertEqual(original.active_grant(), sibling_store.active_grant())

            sibling_store.revoke(
                actor="operator", evidence="decision://post-migration-revoke"
            )
            revoked_state = original.load()
            self.assertEqual(
                [
                    "repository-autonomous-merge-granted",
                    "repository-authority-migrated",
                    "repository-autonomous-merge-revoked",
                ],
                [event["event"] for event in revoked_state["history"]],
            )
            replay_after_revoke, was_replayed = original.migrate(
                expected_state_sha256=source_sha256,
                actor="operator",
                evidence="decision://migrate",
            )
            self.assertTrue(was_replayed)
            self.assertEqual(receipt, replay_after_revoke)

    def test_revoked_reconciliation_migration_and_cli_readback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            sibling = self.add_linked_worktree(repo, root)
            store = RepositoryReconciliationAuthorityStore(repo)
            source_sha256, legacy = write_legacy_state(store, revoked=True)

            command = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "migrate-repository-authority",
                    "--repo",
                    str(sibling),
                    "--kind",
                    "reconciliation",
                    "--expected-state-sha256",
                    source_sha256,
                    "--actor",
                    "operator",
                    "--evidence",
                    "decision://migrate-revoked",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            result = json.loads(command.stdout)["data"]
            self.assertFalse(result["replayed"])
            self.assertEqual("revoked", result["repository_authority"]["status"])
            migrated = RepositoryReconciliationAuthorityStore(repo).load()
            self.assertEqual(
                legacy["revocation"],
                migrated["provenance"]["predecessor"]["state"]["revocation"],
            )
            self.assertIsNone(RepositoryReconciliationAuthorityStore(sibling).active_grant())

    def test_irrelevant_legacy_reconciliation_does_not_block_manual_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            tickets = repo / "tickets"
            tickets.mkdir()
            (tickets / "01.md").write_text(
                "---\nticket_schema: 1\nticket_id: MRA\nexecution_mode: AFK\nblocked_by: []\n---\n\n# Manual\n",
                encoding="utf-8",
            )
            git(repo, "add", "tickets/01.md")
            git(repo, "commit", "-m", "ticket")
            write_legacy_state(RepositoryReconciliationAuthorityStore(repo))
            sibling = self.add_linked_worktree(repo, root)

            created = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "run",
                    str(sibling / "tickets"),
                    "--repo",
                    str(sibling),
                    "--provider",
                    "github",
                    "--provider-mode",
                    "simulated",
                    "--run-id",
                    "manual-run",
                    "--base",
                    "main",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue(json.loads(created.stdout)["ok"])
            resumed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "resume",
                    "manual-run",
                    "--repo",
                    str(sibling),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            result = json.loads(resumed.stdout)
            self.assertTrue(result["ok"])
            self.assertEqual(["MRA"], result["data"]["ready"])

    def test_merge_all_requires_migrated_authority_before_provider_access(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            write_legacy_state(RepositoryMergeAuthorityStore(repo))
            sibling = self.add_linked_worktree(repo, root)
            result = subprocess.run(
                [sys.executable, "-B", str(CLI), "merge-all", "--repo", str(sibling)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("requires explicit migration", result.stdout + result.stderr)

    def test_remote_drift_and_symlinked_migration_state_fail_without_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            store = RepositoryMergeAuthorityStore(repo)
            source_sha256, _ = write_legacy_state(store)
            before = store.path.read_bytes()
            git(repo, "remote", "set-url", "origin", "https://github.com/example/other.git")
            with self.assertRaisesRegex(
                RepositoryMergeAuthorityError, "binding contradicts"
            ):
                RepositoryMergeAuthorityStore(repo).migrate(
                    expected_state_sha256=source_sha256,
                    actor="operator",
                    evidence="decision://migrate",
                )
            self.assertEqual(before, store.path.read_bytes())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            store = RepositoryReconciliationAuthorityStore(repo)
            source_sha256, _ = write_legacy_state(store)
            before = store.path.read_bytes()
            outside = root / "outside"
            outside.mkdir()
            store.migration_dir.parent.mkdir(parents=True, exist_ok=True)
            try:
                store.migration_dir.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable")
            with self.assertRaisesRegex(
                RepositoryReconciliationAuthorityError, "symbolic links"
            ):
                store.migrate(
                    expected_state_sha256=source_sha256,
                    actor="operator",
                    evidence="decision://migrate",
                )
            self.assertEqual(before, store.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
