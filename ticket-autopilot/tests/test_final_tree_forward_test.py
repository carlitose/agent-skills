from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "ticket-autopilot" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.final_tree_projection import (
    canonical_digest,
    plan_tracked_completion,
    projection_config,
)
from autopilot.ticket_contract import ticket_source_digest
from final_tree_forward_test import _apply_enabled, build_report


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class FinalTreeForwardTestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.repo = Path(self.directory.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "tests@example.com")
        git(self.repo, "config", "user.name", "Tests")
        source = self.repo / "tickets" / "01.md"
        source.parent.mkdir()
        source.write_text(
            """---
ticket_schema: 1
ticket_id: "01"
execution_mode: AFK
blocked_by: []
---

# Forward fixture
""",
            encoding="utf-8",
        )
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        self.base_tree = git(self.repo, "rev-parse", "HEAD^{tree}")
        (self.repo / "implementation.txt").write_text(
            "candidate\n", encoding="utf-8"
        )
        git(self.repo, "add", "implementation.txt")
        self.implementation_tree = git(self.repo, "write-tree")
        self.ticket_digest = ticket_source_digest(source)
        self.implementation_candidate = {
            "base_tree_oid": self.base_tree,
            "candidate_tree_oid": self.implementation_tree,
            "ticket_digest": self.ticket_digest,
            "contract_version": 2,
        }
        self.receipt = {
            "schema": 1,
            "run_id": "forward-fixture",
            "ticket_id": "01",
            "implementation_status": "complete",
            "candidate_ref": self.implementation_candidate,
            "ticket_source_mode": "tracked",
            "snapshot_manifest_digest": "a" * 64,
        }
        manifest = plan_tracked_completion(
            self.repo,
            run_id="forward-fixture",
            ticket_id="01",
            artifact_generation=0,
            configuration=projection_config("enabled"),
            candidate_ref=self.implementation_candidate,
            source_relative_path="tickets/01.md",
            destination_relative_path="tickets/done/01.md",
            receipt_document=self.receipt,
            source_mode="tracked",
        ).manifest
        _apply_enabled(self.repo, manifest)
        self.delivery_candidate = manifest["planned_delivery_candidate_ref"]
        git(self.repo, "commit", "-qm", "delivery")
        self.head = git(self.repo, "rev-parse", "HEAD")
        self.body = (
            "Final tree "
            + self.delivery_candidate["candidate_tree_oid"]
            + " at head "
            + self.head
        )
        provider_observation = {
            "schema": 1,
            "provider": "github",
            "pr_id": "1",
            "evidence_class": "simulated",
            "observed": True,
            "operation": "get-pr-state",
            "state": "merged",
            "base": "main",
            "head_sha": self.head,
            "merge_commit_sha": self.head,
            "body": self.body,
        }
        self.fixture = {
            "schema": 1,
            "source_repository": str(self.repo),
            "run_id": "forward-fixture",
            "ticket_id": "01",
            "artifact_generation": 0,
            "implementation_candidate_ref": self.implementation_candidate,
            "delivery_candidate_ref": self.delivery_candidate,
            "source_relative_path": "tickets/01.md",
            "destination_relative_path": "tickets/done/01.md",
            "receipt_document": self.receipt,
            "verification_bundle": {
                "candidate_ref": self.delivery_candidate,
                "verification": {
                    "candidate_ref": self.delivery_candidate,
                    "release_status": "eligible",
                },
            },
            "rendered_body": self.body,
            "expected_head_sha": self.head,
            "provider_observation": provider_observation,
            "terminal_proof": {
                "schema": 1,
                "repository_identity": str(self.repo),
                "provider": "github",
                "pr_id": "1",
                "head_sha": self.head,
                "pr_base": "main",
                "terminal_branch": "main",
                "terminal_sha": self.head,
                "terminal_tree_oid": self.delivery_candidate[
                    "candidate_tree_oid"
                ],
                "merge_commit_sha": self.head,
                "reachable_kind": "head",
                "reachable_sha": self.head,
                "provider_observation_digest": canonical_digest(
                    {
                        key: value
                        for key, value in provider_observation.items()
                        if key != "evidence_class"
                    }
                ),
                "delivery_lineage_digest": "a" * 64,
                "provenance": "runner-merge",
            },
        }

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_report_is_deterministic_exact_and_contains_logical_counts_only(
        self,
    ) -> None:
        selected_tests: list[str] = []

        def runner(check) -> bool:
            selected_tests.extend(check["tests"])
            return True

        first = build_report(self.fixture, matrix_runner=runner)
        first_selection = list(selected_tests)
        selected_tests.clear()
        second = build_report(self.fixture, matrix_runner=runner)
        self.assertEqual(first, second)
        self.assertEqual("pass", first["result"])
        self.assertEqual(29, first["matrix"]["logical_tests"])
        self.assertEqual(
            [11, 7, 5, 2, 4],
            [item["logical_tests"] for item in first["matrix"]["checks"]],
        )
        self.assertEqual(29, len(first_selection))
        self.assertEqual(29, len(set(first_selection)))
        self.assertTrue(all(".test_" in name for name in first_selection))
        self.assertEqual("parity", first["observation"]["status"])
        self.assertEqual(
            self.delivery_candidate["candidate_tree_oid"],
            first["observation"]["authoritative_tree_oid"],
        )
        self.assertEqual(
            "already-applied", first["enabled_replay"]["final_replay"]
        )
        self.assertEqual("mode", first["enabled_replay"]["new_default_off_reason"])
        self.assertTrue(first["delivery_lineage"]["recorded_head_reachable"])
        self.assertTrue(first["logical_counts_only"])
        rendered = json.dumps(first, sort_keys=True)
        self.assertNotIn(str(self.repo), rendered)
        self.assertNotIn('"duration"', rendered)
        self.assertNotIn('"elapsed"', rendered)
        self.assertNotIn('"seconds"', rendered)

    def test_stale_verification_body_provider_or_terminal_fails_closed(
        self,
    ) -> None:
        def stale_bundle_root(fixture) -> None:
            fixture["verification_bundle"]["candidate_ref"] = (
                self.implementation_candidate
            )

        def stale_bundle_result(fixture) -> None:
            fixture["verification_bundle"]["verification"][
                "candidate_ref"
            ] = self.implementation_candidate

        def stale_rendered_body(fixture) -> None:
            fixture["rendered_body"] = self.body + " changed"

        def stale_provider_body(fixture) -> None:
            fixture["provider_observation"]["body"] = self.body + " changed"

        def stale_provider_head(fixture) -> None:
            fixture["provider_observation"]["head_sha"] = "f" * 40

        def stale_terminal_head(fixture) -> None:
            fixture["terminal_proof"]["head_sha"] = "f" * 40

        mutations = (
            ("verification-bundle-root", stale_bundle_root),
            ("verification-result", stale_bundle_result),
            ("rendered-body", stale_rendered_body),
            ("provider-body", stale_provider_body),
            ("provider-head", stale_provider_head),
            ("terminal-head", stale_terminal_head),
        )
        for label, mutate in mutations:
            fixture = copy.deepcopy(self.fixture)
            mutate(fixture)
            with self.subTest(mutation=label):
                with self.assertRaisesRegex(
                    ValueError,
                    "verification, body, provider, or terminal lineage",
                ):
                    build_report(fixture, skip_matrix=True)


if __name__ == "__main__":
    unittest.main()
