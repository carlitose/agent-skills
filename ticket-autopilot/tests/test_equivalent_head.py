from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))

from autopilot.equivalent_head import (
    SINGLE_PARENT_INTEGRATION_COPY,
    TWO_PARENT_HEAD_MERGE,
    EquivalentHeadError,
    _ensure_commit,
    build_equivalent_head_receipt,
    validate_equivalent_head_receipt,
)


def git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


class EquivalentHeadTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "test@example.invalid")

    def topology(
        self,
        *,
        provider_old_blob_drift: bool = False,
        provider_new_blob_drift: bool = False,
        provider_mode_drift: bool = False,
        provider_extra_path: bool = False,
        provider_extra_commit: bool = False,
        integration_copy: bool = False,
    ) -> dict[str, str]:
        (self.repo / "shared.txt").write_text("before\n", encoding="utf-8")
        (self.repo / "deleted.txt").write_text("delete me\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "recorded base")
        recorded_base = git(self.repo, "rev-parse", "HEAD")

        git(self.repo, "switch", "-c", "recorded")
        (self.repo / "shared.txt").write_text("after\n", encoding="utf-8")
        (self.repo / "added.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        os.chmod(self.repo / "added.sh", 0o755)
        (self.repo / "deleted.txt").unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "ticket delivery")
        recorded_head = git(self.repo, "rev-parse", "HEAD")

        git(self.repo, "switch", "main")
        (self.repo / "unrelated.txt").write_text("base advanced\n", encoding="utf-8")
        if provider_old_blob_drift:
            (self.repo / "shared.txt").write_text("different before\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "provider base")
        observed_base = git(self.repo, "rev-parse", "HEAD")

        git(self.repo, "switch", "-c", "observed")
        (self.repo / "shared.txt").write_text(
            "different after\n" if provider_new_blob_drift else "after\n",
            encoding="utf-8",
        )
        (self.repo / "added.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        os.chmod(self.repo / "added.sh", 0o644 if provider_mode_drift else 0o755)
        (self.repo / "deleted.txt").unlink()
        if provider_extra_path:
            (self.repo / "extra.txt").write_text("not recorded\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "rebased ticket delivery")
        if provider_extra_commit:
            (self.repo / "second.txt").write_text("second delivery commit\n", encoding="utf-8")
            git(self.repo, "add", "second.txt")
            git(self.repo, "commit", "-m", "unexpected second delivery commit")
        observed_head = git(self.repo, "rev-parse", "HEAD")

        git(self.repo, "switch", "main")
        if integration_copy:
            merge_commit = git(
                self.repo,
                "commit-tree",
                f"{observed_head}^{{tree}}",
                "-p",
                observed_base,
                "-m",
                "provider integration copy",
            )
            git(self.repo, "reset", "--hard", merge_commit)
        else:
            git(self.repo, "merge", "--no-ff", "observed", "-m", "merge provider PR")
            merge_commit = git(self.repo, "rev-parse", "HEAD")
        return {
            "recorded_base": recorded_base,
            "recorded_head": recorded_head,
            "observed_base": observed_base,
            "observed_head": observed_head,
            "merge_commit": merge_commit,
        }

    def documents(self, commits: dict[str, str]) -> tuple[dict, dict]:
        ledger = {
            "repo": str(self.repo),
            "provider": "github",
            "tickets": {
                "06": {
                    "pr": {
                        "provider": "github",
                        "pr_id": "248",
                        "branch": "ticket-autopilot/run/06",
                        "head_sha": commits["recorded_head"],
                    },
                    "delivery_lineage": {
                        "contract_version": 1,
                        "provider": "github",
                        "pr_id": "248",
                        "branch": "ticket-autopilot/run/06",
                        "base_branch": "main",
                        "base_sha": commits["recorded_base"],
                        "head_sha": commits["recorded_head"],
                    },
                }
            },
        }
        observation = {
            "schema": 1,
            "provider": "github",
            "operation": "get-pr-state",
            "evidence_class": "live",
            "observed": True,
            "pr_id": "248",
            "branch": "ticket-autopilot/run/06",
            "base": "main",
            "head_sha": commits["observed_head"],
            "merge_commit_sha": commits["merge_commit"],
            "state": "merged",
        }
        return ledger, observation

    def build(self, commits: dict[str, str]) -> dict:
        ledger, observation = self.documents(commits)
        return build_equivalent_head_receipt(
            self.repo,
            ledger,
            "06",
            observation,
            actor="scheduler:post-merge-equivalent-head",
            evidence="fixture://equivalent-head",
            boundary_guard=lambda _boundary: self.fail("all fixture objects exist"),
        )

    def test_exact_raw_tree_transition_proves_rebased_single_commit(self) -> None:
        commits = self.topology()
        receipt = self.build(commits)

        self.assertEqual(2, receipt["schema"])
        self.assertEqual(TWO_PARENT_HEAD_MERGE, receipt["topology"])
        self.assertEqual(commits["recorded_head"], receipt["recorded_head_sha"])
        self.assertEqual(commits["observed_head"], receipt["observed_head_sha"])
        self.assertEqual(3, receipt["raw_delta_entries"])
        self.assertEqual(
            git(self.repo, "rev-parse", f"{commits['observed_head']}^{{tree}}"),
            receipt["merge_commit_tree_oid"],
        )

        ledger, _ = self.documents(commits)
        ledger["tickets"]["06"]["pr"]["head_sha"] = commits["observed_head"]
        ledger["tickets"]["06"]["delivery_lineage"]["head_sha"] = commits[
            "observed_head"
        ]
        self.assertEqual(
            receipt,
            validate_equivalent_head_receipt(ledger, "06", receipt),
        )

    def test_single_parent_integration_copy_proves_all_three_transitions(self) -> None:
        commits = self.topology(integration_copy=True)
        receipt = self.build(commits)

        self.assertEqual(2, receipt["schema"])
        self.assertEqual(SINGLE_PARENT_INTEGRATION_COPY, receipt["topology"])
        self.assertNotEqual(commits["observed_head"], commits["merge_commit"])
        self.assertEqual(
            git(self.repo, "rev-parse", f"{commits['observed_head']}^{{tree}}"),
            git(self.repo, "rev-parse", f"{commits['merge_commit']}^{{tree}}"),
        )
        self.assertEqual(3, receipt["raw_delta_entries"])

    def test_historical_schema_one_two_parent_receipt_replays_without_rewrite(self) -> None:
        commits = self.topology()
        receipt = self.build(commits)
        legacy = {
            key: value
            for key, value in receipt.items()
            if key not in {"topology", "integration_parent_shas"}
        }
        legacy["schema"] = 1
        ledger, _ = self.documents(commits)
        ledger["tickets"]["06"]["pr"]["head_sha"] = commits["observed_head"]
        ledger["tickets"]["06"]["delivery_lineage"]["head_sha"] = commits[
            "observed_head"
        ]

        self.assertEqual(
            legacy,
            validate_equivalent_head_receipt(ledger, "06", legacy),
        )

    def test_historical_betsharemarket_delta_fixture_has_diagnosed_digest(self) -> None:
        raw = (
            FIXTURES / "betsharemarket-pr-248-recorded-delta.raw"
        ).read_bytes()
        self.assertEqual(
            "21cabad17ea1144602fc2b75700d24669a8c3839fe21ed06c37a9d2fdff8a070",
            hashlib.sha256(raw).hexdigest(),
        )
        self.assertEqual(8, (len(raw.split(b"\0")) - 1) // 2)

    def test_replace_refs_cannot_spoof_tree_transition_equivalence(self) -> None:
        commits = self.topology(provider_new_blob_drift=True)
        correct_tree = git(
            self.repo,
            "merge-tree",
            "--write-tree",
            commits["observed_base"],
            commits["recorded_head"],
        ).splitlines()[0]
        fake_observed = git(
            self.repo,
            "commit-tree",
            correct_tree,
            "-p",
            commits["observed_base"],
            "-m",
            "replacement observed head",
        )
        fake_merge = git(
            self.repo,
            "commit-tree",
            correct_tree,
            "-p",
            commits["observed_base"],
            "-p",
            commits["observed_head"],
            "-m",
            "replacement merge commit",
        )
        git(self.repo, "replace", commits["observed_head"], fake_observed)
        git(self.repo, "replace", commits["merge_commit"], fake_merge)

        def raw(base: str, head: str) -> bytes:
            return subprocess.run(
                [
                    "git",
                    "diff-tree",
                    "-r",
                    "--no-commit-id",
                    "--raw",
                    "--full-index",
                    "--no-renames",
                    "-z",
                    base,
                    head,
                ],
                cwd=self.repo,
                capture_output=True,
                check=True,
            ).stdout

        self.assertEqual(
            raw(commits["recorded_base"], commits["recorded_head"]),
            raw(commits["observed_base"], commits["observed_head"]),
            "the planted replace refs would fool ordinary Git object reads",
        )
        with self.assertRaisesRegex(
            EquivalentHeadError, "raw tree transitions are not byte-identical"
        ):
            self.build(commits)

    def test_changed_provider_old_blob_fails_closed(self) -> None:
        commits = self.topology(provider_old_blob_drift=True)
        with self.assertRaisesRegex(
            EquivalentHeadError, "raw tree transitions are not byte-identical"
        ):
            self.build(commits)

    def test_changed_provider_new_blob_fails_closed(self) -> None:
        commits = self.topology(provider_new_blob_drift=True)
        with self.assertRaisesRegex(
            EquivalentHeadError, "raw tree transitions are not byte-identical"
        ):
            self.build(commits)

    def test_changed_provider_mode_fails_closed(self) -> None:
        commits = self.topology(provider_mode_drift=True)
        with self.assertRaisesRegex(
            EquivalentHeadError, "raw tree transitions are not byte-identical"
        ):
            self.build(commits)

    def test_extra_provider_path_fails_closed(self) -> None:
        commits = self.topology(provider_extra_path=True)
        with self.assertRaisesRegex(
            EquivalentHeadError, "raw tree transitions are not byte-identical"
        ):
            self.build(commits)

    def test_multi_commit_provider_delivery_fails_closed(self) -> None:
        commits = self.topology(provider_extra_commit=True)
        with self.assertRaisesRegex(
            EquivalentHeadError, "not one commit on the integration base"
        ):
            self.build(commits)

    def test_missing_object_fetch_is_sha_only_and_fails_without_commit_readback(
        self,
    ) -> None:
        commands: list[list[str]] = []
        responses = [
            subprocess.CompletedProcess([], 1, b"", b"missing"),
            subprocess.CompletedProcess([], 0, "fetched", ""),
            subprocess.CompletedProcess([], 1, b"", b"still missing"),
        ]

        def run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
            commands.append(command)
            return responses.pop(0)

        boundaries: list[str] = []
        with mock.patch("autopilot.equivalent_head.subprocess.run", side_effect=run):
            with self.assertRaisesRegex(EquivalentHeadError, "not a commit"):
                _ensure_commit(
                    self.repo,
                    "d" * 40,
                    boundary_guard=boundaries.append,
                )
        self.assertEqual(["git:equivalent-head-object-fetch"], boundaries)
        self.assertEqual(
            [
                "git",
                "--no-replace-objects",
                "fetch",
                "--no-tags",
                "--no-write-fetch-head",
                "origin",
                "d" * 40,
            ],
            commands[1],
        )
        self.assertFalse(any(":" in item for item in commands[1][2:]))

    def test_non_merge_provider_commit_fails_closed(self) -> None:
        commits = self.topology()
        _, observation = self.documents(commits)
        observation["merge_commit_sha"] = commits["observed_head"]
        ledger, _ = self.documents(commits)
        with self.assertRaisesRegex(EquivalentHeadError, "must differ"):
            build_equivalent_head_receipt(
                self.repo,
                ledger,
                "06",
                observation,
                actor="scheduler:post-merge-equivalent-head",
                evidence="fixture://equivalent-head",
                boundary_guard=lambda _boundary: None,
            )

    def test_integration_copy_wrong_parent_tree_and_equal_head_fail_closed(self) -> None:
        commits = self.topology(integration_copy=True)
        observed_tree = git(
            self.repo, "rev-parse", f"{commits['observed_head']}^{{tree}}"
        )
        wrong_parent = dict(commits)
        wrong_parent["merge_commit"] = git(
            self.repo,
            "commit-tree",
            observed_tree,
            "-p",
            commits["recorded_base"],
            "-m",
            "wrong integration parent",
        )
        with self.assertRaisesRegex(EquivalentHeadError, "integration base"):
            self.build(wrong_parent)

        wrong_tree = dict(commits)
        wrong_tree["merge_commit"] = git(
            self.repo,
            "commit-tree",
            f"{commits['observed_base']}^{{tree}}",
            "-p",
            commits["observed_base"],
            "-m",
            "wrong integration tree",
        )
        with self.assertRaisesRegex(EquivalentHeadError, "tree differs"):
            self.build(wrong_tree)

        equal_head = dict(commits)
        equal_head["merge_commit"] = commits["observed_head"]
        with self.assertRaisesRegex(EquivalentHeadError, "must differ"):
            self.build(equal_head)

    def test_unknown_schema_and_topology_fail_closed(self) -> None:
        commits = self.topology(integration_copy=True)
        receipt = self.build(commits)
        ledger, _ = self.documents(commits)
        ledger["tickets"]["06"]["pr"]["head_sha"] = commits["observed_head"]
        ledger["tickets"]["06"]["delivery_lineage"]["head_sha"] = commits[
            "observed_head"
        ]
        for field, value, message in (
            ("schema", 3, "schema"),
            ("schema", True, "schema"),
            ("topology", "same-tree", "topology"),
            ("topology", TWO_PARENT_HEAD_MERGE, "parents contradict"),
        ):
            forged = dict(receipt)
            forged[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                EquivalentHeadError, message
            ):
                validate_equivalent_head_receipt(ledger, "06", forged)

    def test_provider_branch_and_base_are_exact_bindings(self) -> None:
        commits = self.topology()
        ledger, observation = self.documents(commits)
        observation["base"] = "release"
        with self.assertRaisesRegex(
            EquivalentHeadError, "provider observation contradicts"
        ):
            build_equivalent_head_receipt(
                self.repo,
                ledger,
                "06",
                observation,
                actor="scheduler:post-merge-equivalent-head",
                evidence="fixture://equivalent-head",
                boundary_guard=lambda _boundary: None,
            )

    def test_receipt_cannot_be_rebound_after_adoption(self) -> None:
        commits = self.topology()
        receipt = self.build(commits)
        ledger, _ = self.documents(commits)
        ledger["tickets"]["06"]["pr"]["head_sha"] = "f" * 40
        ledger["tickets"]["06"]["delivery_lineage"]["head_sha"] = "f" * 40
        with self.assertRaisesRegex(EquivalentHeadError, "binding is stale"):
            validate_equivalent_head_receipt(ledger, "06", receipt)


if __name__ == "__main__":
    unittest.main()
