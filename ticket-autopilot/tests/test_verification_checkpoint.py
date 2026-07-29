from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.verification_checkpoint import (  # noqa: E402
    CheckpointCorruption,
    CheckpointPhaseFailure,
    inspect_verification_checkpoints,
    run_verification_checkpoints,
)


CANDIDATE = {
    "contract_version": 1,
    "base_sha": "base-a",
    "tree_oid": "tree-a",
    "ticket_digest": "ticket-a",
}


class VerificationCheckpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.calls: list[str] = []

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def adapters(self):
        def build(inputs):
            self.calls.append("build")
            return {"evidence": inputs["evidence"]}

        def validate(bundle):
            self.calls.append("validate")
            return {"structurally_valid": True, "semantic_pass": False, "bundle": bundle}

        def reduce(validated):
            self.calls.append("reduce")
            return {
                "claim_ceiling": "partial",
                "semantic_pass": validated["semantic_pass"],
            }

        return build, validate, reduce

    def execute(self, *, candidate=CANDIDATE, inputs=None):
        build, validate, reduce = self.adapters()
        return run_verification_checkpoints(
            self.root,
            candidate,
            inputs or {"evidence": [{"command": "unit", "status": "passed"}]},
            builder=build,
            validator=validate,
            reducer=reduce,
        )

    def test_builds_candidate_bound_canonical_content_addressed_chain(self) -> None:
        outcome = self.execute()

        self.assertEqual(
            outcome.phases_executed,
            (
                "context-loaded",
                "bundle-built",
                "bundle-validated",
                "bundle-reduced",
                "handoff-ready",
            ),
        )
        self.assertEqual(self.calls, ["build", "validate", "reduce"])
        self.assertEqual(outcome.leaf_interactions_consumed, 0)
        self.assertFalse(outcome.handoff["semantic_pass"])
        for artifact in outcome.artifacts.values():
            document = json.loads(artifact.path.read_text())
            self.assertEqual(document["candidate_ref"], CANDIDATE)
            self.assertEqual(document["artifact_hash"], artifact.digest)

    def test_identical_inputs_are_a_cache_hit_without_rewriting(self) -> None:
        first = self.execute()
        mtimes = {
            path: path.stat().st_mtime_ns for path in self.root.rglob("*.json")
        }
        self.calls.clear()

        second = self.execute()

        self.assertTrue(second.cache_hit)
        self.assertEqual(second.phases_executed, ())
        self.assertEqual(self.calls, [])
        self.assertEqual(
            mtimes,
            {path: path.stat().st_mtime_ns for path in self.root.rglob("*.json")},
        )
        self.assertEqual(first.handoff, second.handoff)

    def test_changed_candidate_or_inputs_do_not_reuse_prior_chain(self) -> None:
        first = self.execute()
        self.calls.clear()
        changed_input = self.execute(inputs={"evidence": [{"command": "other"}]})
        self.assertFalse(changed_input.cache_hit)
        self.assertEqual(self.calls, ["build", "validate", "reduce"])
        self.assertNotEqual(first.input_hash, changed_input.input_hash)

        self.calls.clear()
        changed_candidate = self.execute(candidate={**CANDIDATE, "tree_oid": "tree-b"})
        self.assertFalse(changed_candidate.cache_hit)
        self.assertEqual(self.calls, ["build", "validate", "reduce"])
        self.assertNotEqual(first.candidate_hash, changed_candidate.candidate_hash)

    def test_missing_indexed_checkpoint_is_corruption(self) -> None:
        first = self.execute()
        first.artifacts["bundle-validated"].path.unlink()

        with self.assertRaises(CheckpointCorruption):
            self.execute()

    def test_interruption_persists_the_completed_prefix(self) -> None:
        def build(inputs):
            self.calls.append("build")
            return {"evidence": inputs["evidence"]}

        def interrupt(_bundle):
            self.calls.append("validate-interrupted")
            raise RuntimeError("interrupted")

        with self.assertRaisesRegex(
            CheckpointPhaseFailure,
            "bundle-validated.*interrupted",
        ):
            run_verification_checkpoints(
                self.root,
                CANDIDATE,
                {"evidence": [{"command": "unit", "status": "passed"}]},
                builder=build,
                validator=interrupt,
                reducer=lambda _validated: self.fail("reducer must not run"),
            )

        status = inspect_verification_checkpoints(
            self.root,
            CANDIDATE,
            {"evidence": [{"command": "unit", "status": "passed"}]},
        )
        self.assertEqual(
            status.phases_complete,
            ("context-loaded", "bundle-built"),
        )
        self.assertFalse(status.complete)
        self.calls.clear()

        resumed = self.execute()

        self.assertEqual(
            resumed.phases_executed,
            ("bundle-validated", "bundle-reduced", "handoff-ready"),
        )
        self.assertEqual(self.calls, ["validate", "reduce"])

    def test_inspection_of_an_absent_chain_is_pure(self) -> None:
        checkpoint_dir = self.root / "not-created"

        status = inspect_verification_checkpoints(
            checkpoint_dir,
            CANDIDATE,
            {"evidence": []},
        )

        self.assertEqual(status.phases_complete, ())
        self.assertFalse(status.complete)
        self.assertFalse(checkpoint_dir.exists())

    def test_corruption_is_rejected_instead_of_becoming_evidence(self) -> None:
        first = self.execute()
        first.artifacts["bundle-built"].path.write_text("{}")

        with self.assertRaises(CheckpointCorruption):
            self.execute()

    def test_structural_validation_does_not_invent_a_semantic_pass(self) -> None:
        outcome = self.execute()

        self.assertTrue(outcome.handoff["structurally_valid"])
        self.assertFalse(outcome.handoff["semantic_pass"])
        self.assertEqual(outcome.handoff["claim_ceiling"], "partial")


if __name__ == "__main__":
    unittest.main()
