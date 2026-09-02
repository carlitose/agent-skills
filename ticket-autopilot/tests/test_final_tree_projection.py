from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "ticket-autopilot" / "scripts" / "ticket-autopilot.py"
sys.path.insert(0, str(CLI.parent))

from autopilot.final_tree_projection import (
    FinalTreeProjectionError,
    ProjectionExcluded,
    canonical_bytes,
    canonical_digest,
    compare_projection,
    plan_tracked_completion,
    projection_config,
    validate_manifest,
    validate_projection_config,
)
from autopilot.link_repoint import repoint_moved_file
from autopilot.ticket_contract import ticket_source_digest


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


class FinalTreeProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "tests@example.invalid")
        git(self.repo, "config", "user.name", "Projection Tests")
        source = self.repo / "docs/tickets/feature/01.md"
        source.parent.mkdir(parents=True)
        source.write_text("# Ticket\n\nExact bytes.\n", encoding="utf-8")
        spec = self.repo / "docs/specs/map.md"
        spec.parent.mkdir(parents=True)
        spec.write_text(
            "[Ticket](../tickets/feature/01.md#acceptance)\n",
            encoding="utf-8",
        )
        implementation = self.repo / "implementation.txt"
        implementation.write_text("before\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "base")
        self.base_tree = git(self.repo, "rev-parse", "HEAD^{tree}")
        implementation.write_text("after\n", encoding="utf-8")
        git(self.repo, "add", "implementation.txt")
        self.implementation_tree = git(self.repo, "write-tree")
        self.ticket_digest = ticket_source_digest(source)
        self.candidate = {
            "contract_version": 2,
            "base_tree_oid": self.base_tree,
            "candidate_tree_oid": self.implementation_tree,
            "ticket_digest": self.ticket_digest,
        }
        self.summary = {
            "schema": 1,
            "run_id": "projection-run",
            "ticket_id": "FTV-01",
            "implementation_status": "complete",
            "candidate_ref": self.candidate,
            "ticket_source_mode": "tracked",
            "snapshot_manifest_digest": "a" * 64,
        }

    def plan(self, **overrides: object):
        arguments: dict[str, object] = {
            "run_id": "projection-run",
            "ticket_id": "FTV-01",
            "artifact_generation": 0,
            "configuration": projection_config("observe"),
            "candidate_ref": self.candidate,
            "source_relative_path": "docs/tickets/feature/01.md",
            "destination_relative_path": "docs/tickets/feature/done/01.md",
            "receipt_document": self.summary,
            "source_mode": "tracked",
            "delivery_metadata": {"branch": {"branch": "ticket/FTV-01"}},
        }
        arguments.update(overrides)
        return plan_tracked_completion(self.repo, **arguments)  # type: ignore[arg-type]

    def apply_expected_completion(self) -> dict[str, object]:
        source = self.repo / "docs/tickets/feature/01.md"
        destination = self.repo / "docs/tickets/feature/done/01.md"
        destination.parent.mkdir()
        source.replace(destination)
        destination.with_suffix(".completion.json").write_bytes(
            canonical_bytes(self.summary)
        )
        links = repoint_moved_file(
            self.repo,
            "docs/tickets/feature/01.md",
            "docs/tickets/feature/done/01.md",
        )
        git(
            self.repo,
            "add",
            "-A",
            "--",
            "docs/tickets/feature/01.md",
            "docs/tickets/feature/done/01.md",
            "docs/tickets/feature/done/01.completion.json",
            *links,
        )
        return {
            **self.candidate,
            "candidate_tree_oid": git(self.repo, "write-tree"),
        }

    def test_mode_configuration_is_strict_and_defaults_to_observe(self) -> None:
        self.assertEqual("observe", projection_config()["mode"])
        for mode in ("off", "observe", "enabled"):
            self.assertEqual(mode, validate_projection_config(projection_config(mode))["mode"])
        for value in (
            {"schema": 1, "contract_version": 1, "mode": "unknown"},
            {"schema": 1, "mode": "observe"},
            "observe",
        ):
            with self.subTest(value=value), self.assertRaises(
                FinalTreeProjectionError
            ):
                validate_projection_config(value)

    def test_plan_is_deterministic_complete_and_non_authoritative(self) -> None:
        before = git(self.repo, "status", "--short")
        first = self.plan()
        second = self.plan(
            candidate_ref=dict(reversed(tuple(self.candidate.items()))),
            receipt_document=dict(reversed(tuple(self.summary.items()))),
            delivery_metadata={
                "branch": {"head": None, "branch": "ticket/FTV-01"}
            },
        )
        self.assertEqual(before, git(self.repo, "status", "--short"))
        self.assertEqual(first.bytes, second.bytes)
        self.assertEqual(first.manifest, second.manifest)
        self.assertEqual(
            {
                "completion": False,
                "provider": False,
                "merge": False,
                "terminal": False,
                "quality": False,
                "publication": False,
                "recovery": False,
                "wiki": False,
                "pi": False,
                "status_change": False,
                "cleanup": False,
            },
            first.manifest["authority"],
        )
        self.assertTrue(first.manifest["negative_proof"]["complete"])
        self.assertEqual(0, first.manifest["negative_proof"]["extra_diff_rows"])
        self.assertEqual(
            [
                "docs/specs/map.md",
                "docs/tickets/feature/01.md",
                "docs/tickets/feature/done/01.completion.json",
                "docs/tickets/feature/done/01.md",
            ],
            [row["path"] for row in first.manifest["expected_diff"]],
        )
        self.assertEqual(
            len(first.manifest["effects"]),
            len({effect["effect_key"] for effect in first.manifest["effects"]}),
        )
        self.assertEqual(1, len(first.manifest["link_closure"]))

    def test_planned_tree_matches_actual_completion_and_records_parity(self) -> None:
        planned = self.plan()
        actual = self.apply_expected_completion()
        self.assertEqual(
            planned.manifest["planned_delivery_candidate_ref"], actual
        )
        observation = compare_projection(self.repo, planned.manifest, actual)
        replay = compare_projection(self.repo, planned.manifest, actual)
        self.assertEqual(observation.bytes, replay.bytes)
        self.assertEqual("parity", observation.document["status"])
        self.assertEqual([], observation.document["discrepancies"])
        self.assertFalse(observation.document["authority"]["completion"])
        self.assertEqual(observation.bytes, canonical_bytes(observation.document))

    def test_extra_actual_change_is_a_discrepancy_not_parity(self) -> None:
        planned = self.plan()
        self.apply_expected_completion()
        extra = self.repo / "unexpected.txt"
        extra.write_text("unexpected\n", encoding="utf-8")
        git(self.repo, "add", "unexpected.txt")
        actual = {
            **self.candidate,
            "candidate_tree_oid": git(self.repo, "write-tree"),
        }
        observation = compare_projection(self.repo, planned.manifest, actual)
        self.assertEqual("discrepancy", observation.document["status"])
        self.assertEqual(2, len(observation.document["discrepancies"]))
        self.assertFalse(observation.document["authority"]["completion"])

    def test_changed_implementation_blob_is_visible_as_a_discrepancy(self) -> None:
        planned = self.plan()
        self.apply_expected_completion()
        (self.repo / "implementation.txt").write_text(
            "changed after planning\n", encoding="utf-8"
        )
        git(self.repo, "add", "implementation.txt")
        actual = {
            **self.candidate,
            "candidate_tree_oid": git(self.repo, "write-tree"),
        }
        observation = compare_projection(self.repo, planned.manifest, actual)
        self.assertEqual("discrepancy", observation.document["status"])
        self.assertIn(
            "actual I-to-D tree diff differs from expected diff",
            observation.document["discrepancies"],
        )

    def test_missed_link_update_is_visible_as_a_discrepancy(self) -> None:
        planned = self.plan()
        source = self.repo / "docs/tickets/feature/01.md"
        destination = self.repo / "docs/tickets/feature/done/01.md"
        destination.parent.mkdir()
        source.replace(destination)
        destination.with_suffix(".completion.json").write_bytes(
            canonical_bytes(self.summary)
        )
        git(
            self.repo,
            "add",
            "-A",
            "--",
            "docs/tickets/feature/01.md",
            "docs/tickets/feature/done",
        )
        actual = {
            **self.candidate,
            "candidate_tree_oid": git(self.repo, "write-tree"),
        }
        observation = compare_projection(self.repo, planned.manifest, actual)
        self.assertEqual("discrepancy", observation.document["status"])
        self.assertIn(
            "actual I-to-D tree diff differs from expected diff",
            observation.document["discrepancies"],
        )

    def test_tamper_and_duplicate_effects_fail_closed(self) -> None:
        manifest = self.plan().manifest
        tampered = copy.deepcopy(manifest)
        tampered["ticket"]["source_oid"] = "0" * 40
        with self.assertRaisesRegex(
            FinalTreeProjectionError, "contradictory|digest"
        ):
            validate_manifest(tampered)

        receipt_tamper = copy.deepcopy(manifest)
        receipt_tamper["completion_receipt"]["document"]["ticket_id"] = "OTHER"
        receipt_tamper["completion_receipt"]["sha256"] = hashlib.sha256(
            canonical_bytes(receipt_tamper["completion_receipt"]["document"])
        ).hexdigest()
        receipt_payload = {
            key: value
            for key, value in receipt_tamper.items()
            if key != "manifest_digest"
        }
        receipt_tamper["manifest_digest"] = canonical_digest(receipt_payload)
        with self.assertRaisesRegex(FinalTreeProjectionError, "binding"):
            validate_manifest(receipt_tamper)

        duplicate = copy.deepcopy(manifest)
        duplicate["effects"].append(copy.deepcopy(duplicate["effects"][0]))
        payload = {
            key: value for key, value in duplicate.items() if key != "manifest_digest"
        }
        duplicate["manifest_digest"] = canonical_digest(payload)
        with self.assertRaisesRegex(FinalTreeProjectionError, "unique"):
            validate_manifest(duplicate)

    def test_ineligible_inputs_are_never_classified_as_eligible(self) -> None:
        cases = (
            ("source mode", {"source_mode": "ignored"}),
            ("provider state", {"pr": {"pr_id": "17"}}),
            (
                "provider delivery effect",
                {"delivery_metadata": {"push": {"head_sha": "a" * 40}}},
            ),
            (
                "reconciliation",
                {"delivery_metadata": {"reconcile-intent": {"schema": 1}}},
            ),
            (
                "recovery",
                {"excluded_reasons": ["completion-projection-recovery"]},
            ),
            ("off", {"configuration": projection_config("off")}),
        )
        for label, overrides in cases:
            with self.subTest(label=label), self.assertRaises(ProjectionExcluded):
                self.plan(**overrides)

    def test_enabled_mode_produces_the_same_exact_plan_identity(self) -> None:
        observed = self.plan().manifest
        enabled = self.plan(
            configuration=projection_config("enabled")
        ).manifest
        self.assertEqual("observe", observed["configuration"]["mode"])
        self.assertEqual("enabled", enabled["configuration"]["mode"])
        self.assertEqual(
            observed["planned_delivery_candidate_ref"],
            enabled["planned_delivery_candidate_ref"],
        )
        self.assertEqual(observed["effects"], enabled["effects"])
        self.assertEqual(observed["expected_diff"], enabled["expected_diff"])

    def test_candidate_drift_untracked_paths_and_ticket_mode_drift_are_excluded(self) -> None:
        stale = copy.deepcopy(self.candidate)
        stale["candidate_tree_oid"] = self.base_tree
        with self.assertRaisesRegex(ProjectionExcluded, "index tree"):
            self.plan(candidate_ref=stale)

        untracked = self.repo / "untracked.txt"
        untracked.write_text("not staged\n", encoding="utf-8")
        with self.assertRaisesRegex(ProjectionExcluded, "untracked"):
            self.plan()
        untracked.unlink()

        source = self.repo / "docs/tickets/feature/01.md"
        source.write_text("# Drifted ticket\n", encoding="utf-8")
        git(self.repo, "add", "docs/tickets/feature/01.md")
        changed_bytes = {
            **self.candidate,
            "candidate_tree_oid": git(self.repo, "write-tree"),
        }
        with self.assertRaisesRegex(ProjectionExcluded, "digest"):
            self.plan(candidate_ref=changed_bytes)
        git(self.repo, "checkout", self.implementation_tree, "--", "docs/tickets/feature/01.md")

        source.chmod(0o755)
        git(self.repo, "add", "docs/tickets/feature/01.md")
        changed_mode = {
            **self.candidate,
            "candidate_tree_oid": git(self.repo, "write-tree"),
        }
        with self.assertRaisesRegex(ProjectionExcluded, "mode"):
            self.plan(candidate_ref=changed_mode)

    def test_manifest_bytes_have_one_canonical_lf_terminated_encoding(self) -> None:
        planned = self.plan()
        self.assertTrue(planned.bytes.endswith(b"\n"))
        self.assertNotIn(b"\r", planned.bytes)
        self.assertEqual(
            hashlib.sha256(planned.bytes).hexdigest(),
            hashlib.sha256(canonical_bytes(planned.manifest)).hexdigest(),
        )
        decoded = json.loads(planned.bytes)
        self.assertEqual(planned.manifest, decoded)


if __name__ == "__main__":
    unittest.main()
