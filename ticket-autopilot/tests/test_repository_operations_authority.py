"""One durable, revocable operational authority for the repeatable delivery operations."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from autopilot.cli import main  # noqa: E402
from autopilot.repository_authority import AUTHORITY_SCOPE  # noqa: E402
from autopilot.repository_merge_authority import (  # noqa: E402
    RepositoryMergeAuthorityStore,
)
from autopilot.repository_operations_authority import (  # noqa: E402
    OPERATIONS_CAPABILITIES,
    OPERATIONS_POLICY_VERSION,
    RepositoryOperationsAuthorityError,
    RepositoryOperationsAuthorityStore,
    is_repository_adoption_evidence,
    repository_authority_status,
)

if __package__:
    from .git_test_support import GitIsolatedTestCase
else:
    from git_test_support import GitIsolatedTestCase  # noqa: E402


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


class OperationsAuthorityTests(GitIsolatedTestCase):
    def make_repo(self, root: Path, name: str = "repo") -> Path:
        repo = root / name
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Test")
        git(repo, "config", "user.email", "test@example.com")
        (repo / "README.md").write_text("test\n", encoding="utf-8", newline="\n")
        git(repo, "add", "README.md")
        git(repo, "commit", "-m", "initial")
        git(repo, "remote", "add", "origin", f"https://github.com/example/{name}.git")
        return repo

    def run_grant(self, store, grant) -> dict[str, object]:
        return {
            "repository_identity": store.binding.observed_repository_root,
            "provider": store.binding.provider,
            "actor": grant["actor"],
            "evidence": store.adoption_evidence(grant),
        }

    def test_the_covered_operations_are_a_closed_versioned_list(self) -> None:
        self.assertEqual(
            ("publish-pr", "sync-local-install", "request-runtime-reload"),
            OPERATIONS_CAPABILITIES,
        )
        self.assertEqual(1, OPERATIONS_POLICY_VERSION)

    def test_grant_replays_refuses_other_provenance_and_survives_revocation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            store = RepositoryOperationsAuthorityStore(repo)

            grant, replayed = store.grant(
                actor="operator",
                evidence="message://autorizzo-tutto",
                scope=AUTHORITY_SCOPE,
            )
            again, replayed_again = store.grant(
                actor="operator",
                evidence="message://autorizzo-tutto",
                scope=AUTHORITY_SCOPE,
            )
            self.assertFalse(replayed)
            self.assertTrue(replayed_again)
            self.assertEqual(grant, again)
            self.assertTrue(grant["grant_id"].startswith("roa-"))
            self.assertEqual(OPERATIONS_POLICY_VERSION, grant["policy_version"])
            self.assertEqual("active", store.inspect()["status"])

            with self.assertRaisesRegex(
                RepositoryOperationsAuthorityError, "contradictory provenance"
            ):
                store.grant(
                    actor="someone else",
                    evidence="message://other",
                    scope=AUTHORITY_SCOPE,
                )

            store.revoke(actor="operator", evidence="message://basta")
            self.assertEqual("revoked", store.inspect()["status"])
            with self.assertRaisesRegex(RepositoryOperationsAuthorityError, "revoked"):
                store.grant(
                    actor="operator",
                    evidence="message://autorizzo-tutto",
                    scope=AUTHORITY_SCOPE,
                )

    def test_a_covered_capability_passes_and_an_uncovered_one_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            store = RepositoryOperationsAuthorityStore(repo)
            grant, _ = store.grant(
                actor="operator",
                evidence="message://autorizzo-tutto",
                scope=AUTHORITY_SCOPE,
            )
            run_grant = self.run_grant(store, grant)
            self.assertTrue(is_repository_adoption_evidence(run_grant["evidence"]))

            for capability in OPERATIONS_CAPABILITIES:
                with self.subTest(capability=capability):
                    self.assertEqual(
                        grant, store.assert_capability(run_grant, capability)
                    )
                    with store.guard_capability(run_grant, capability) as guarded:
                        self.assertEqual(grant, guarded)

            for capability in ("merge", "reconciliation", "force-push", "cleanup"):
                with self.subTest(capability=capability):
                    with self.assertRaises(RepositoryOperationsAuthorityError) as raised:
                        store.assert_capability(run_grant, capability)
                    self.assertIn(capability, str(raised.exception))

    def test_a_run_grant_from_another_actor_or_repository_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            other = self.make_repo(root, name="other")
            store = RepositoryOperationsAuthorityStore(repo)
            grant, _ = store.grant(
                actor="operator",
                evidence="message://autorizzo-tutto",
                scope=AUTHORITY_SCOPE,
            )
            good = self.run_grant(store, grant)

            for field, value in [
                ("actor", "someone else"),
                ("evidence", "repository-autonomous-operations:roa-" + "0" * 20 + ":" + "0" * 64),
                ("repository_identity", str(other.resolve())),
                ("provider", "azure-devops"),
            ]:
                with self.subTest(field=field), self.assertRaisesRegex(
                    RepositoryOperationsAuthorityError, "does not match"
                ):
                    store.assert_capability({**good, field: value}, "publish-pr")

    def test_without_a_grant_every_capability_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            store = RepositoryOperationsAuthorityStore(repo)
            self.assertEqual("absent", store.inspect()["status"])
            run_grant = {
                "repository_identity": store.binding.observed_repository_root,
                "provider": "github",
                "actor": "operator",
                "evidence": "repository-autonomous-operations:roa-"
                + "0" * 20
                + ":"
                + "0" * 64,
            }
            with self.assertRaisesRegex(
                RepositoryOperationsAuthorityError, "is not active"
            ):
                store.assert_capability(run_grant, "publish-pr")

    def test_another_worktree_of_the_same_repository_reads_the_same_grant(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = self.make_repo(root)
            grant, _ = RepositoryOperationsAuthorityStore(repo).grant(
                actor="operator",
                evidence="message://autorizzo-tutto",
                scope=AUTHORITY_SCOPE,
            )
            linked = root / "linked"
            git(repo, "worktree", "add", str(linked), "-b", "topic")

            store = RepositoryOperationsAuthorityStore(linked)
            self.assertEqual(grant, store.inspect()["grant"])
            self.assertEqual(
                grant,
                store.assert_capability(
                    {
                        "repository_identity": store.binding.observed_repository_root,
                        "provider": "github",
                        "actor": "operator",
                        "evidence": store.adoption_evidence(grant),
                    },
                    "sync-local-install",
                ),
            )

    def test_one_read_reports_every_authority_kind_without_granting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))
            merge, _ = RepositoryMergeAuthorityStore(repo).grant(
                actor="operator",
                evidence="message://mergia-tutto",
                scope=AUTHORITY_SCOPE,
            )

            status = repository_authority_status(repo)

            self.assertEqual({"merge", "reconciliation", "operations"}, set(status))
            self.assertEqual("active", status["merge"]["status"])
            self.assertEqual(merge["grant_id"], status["merge"]["grant"]["grant_id"])
            self.assertEqual("absent", status["reconciliation"]["status"])
            self.assertEqual("absent", status["operations"]["status"])
            self.assertEqual(
                list(OPERATIONS_CAPABILITIES), status["operations"]["capabilities"]
            )
            self.assertEqual("absent", RepositoryOperationsAuthorityStore(repo).inspect()["status"])


class OperationsAuthorityCommandTests(OperationsAuthorityTests):
    def cli(self, *args: str) -> dict[str, object]:
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(list(args))
        self.assertEqual(0, code, output.getvalue())
        response = json.loads(output.getvalue())
        self.assertTrue(response["ok"], response)
        return response["data"]

    def test_grant_status_and_revoke_travel_through_the_command_line(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.make_repo(Path(temporary))

            granted = self.cli(
                "grant-repository-autonomous-operations",
                "--repo", str(repo),
                "--scope", AUTHORITY_SCOPE,
                "--actor", "operator",
                "--evidence", "message://autorizzo-tutto",
            )
            self.assertFalse(granted["replayed"])
            self.assertTrue(granted["grant"]["grant_id"].startswith("roa-"))
            self.assertEqual(
                list(OPERATIONS_CAPABILITIES),
                granted["repository_operations_authority"]["capabilities"],
            )

            status = self.cli(
                "repository-autonomous-operations-status", "--repo", str(repo)
            )
            self.assertEqual("active", status["status"])

            combined = self.cli("repository-authority-status", "--repo", str(repo))
            self.assertEqual("active", combined["operations"]["status"])
            self.assertEqual("absent", combined["merge"]["status"])

            revoked = self.cli(
                "revoke-repository-autonomous-operations",
                "--repo", str(repo),
                "--actor", "operator",
                "--evidence", "message://basta",
            )
            self.assertFalse(revoked["replayed"])
            self.assertEqual(
                "revoked", revoked["repository_operations_authority"]["status"]
            )


class RoutingContractTests(unittest.TestCase):
    """The phrase must route the same way whoever reads the contract."""

    def flattened(self, *relative: str) -> str:
        return " ".join(
            " ".join(
                (REPO_ROOT / name).read_text(encoding="utf-8") for name in relative
            ).split()
        )

    def test_the_router_names_the_phrase_the_command_and_the_detailed_procedure(self) -> None:
        router = self.flattened("ask-skills/SKILL.md")

        for phrase in ("autorizzo tutto", "authorize everything", "autorizo todo"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, router)
        self.assertIn("grant-repository-autonomous-operations --scope", router)
        self.assertIn("repository-authority-status", router)
        self.assertIn("keep their own grant and revocation", router)
        self.assertIn("references/merge-and-reconciliation.md", router)
        self.assertRegex(router, r"Quoted text, examples, questions, negations")
        self.assertRegex(
            router, r"blanket authorization are not authority"
        )

    def test_the_procedure_states_the_closed_list_and_what_it_never_covers(self) -> None:
        procedure = self.flattened(
            "ticket-autopilot/references/merge-and-reconciliation.md"
        )

        for phrase in ("autorizzo tutto", "authorize everything", "autorizo todo"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, procedure)
        for capability in OPERATIONS_CAPABILITIES:
            with self.subTest(capability=capability):
                self.assertIn(capability, procedure)
        self.assertIn("repository-authority-status --repo", procedure)
        self.assertIn("revoke-repository-autonomous-operations", procedure)
        self.assertRegex(procedure, r"never covers[^.]*force push")
        self.assertRegex(procedure, r"refused by name even while the grant is active")
        self.assertRegex(procedure, r"widening the list requires a new policy version")
        self.assertRegex(procedure, r"permitted, never whether a claim is proven")


if __name__ == "__main__":
    unittest.main()
