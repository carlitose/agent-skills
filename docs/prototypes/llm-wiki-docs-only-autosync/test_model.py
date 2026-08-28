from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from model import (
    CandidateRef,
    FileChange,
    IdentityDesign,
    Outcome,
    Probe,
    RequestDesign,
    assess_designs,
    classify,
    scenario_matrix,
)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ORIGIN = CandidateRef("origin-base", "origin-integrated", "origin-ticket")


class SyncContractPrototypeTests(unittest.TestCase):
    def test_state_matrix_is_normalized(self) -> None:
        expected = {
            "absent": Outcome.ABSENT,
            "unchanged": Outcome.UNCHANGED,
            "untracked": Outcome.DIRECT_VALIDATED,
            "tracked": Outcome.TRACKED_CANDIDATE,
            "partial": Outcome.PARTIAL_TRACKING,
            "multiple": Outcome.AMBIGUOUS_ROOT,
            "broken": Outcome.BROKEN_BINDING,
            "mixed-code": Outcome.FORBIDDEN_SCOPE,
            "configuration-wiki": Outcome.FORBIDDEN_SCOPE,
            "ticket-source": Outcome.FORBIDDEN_SCOPE,
            "raw-binary": Outcome.FORBIDDEN_SCOPE,
            "lint-failed": Outcome.LINT_FAILED,
        }
        observed = {
            name: classify(probe, ORIGIN).outcome
            for name, probe in scenario_matrix().items()
        }
        self.assertEqual(expected, observed)

    def test_rejections_leave_protected_tree_unchanged(self) -> None:
        rejected = {
            Outcome.ABSENT,
            Outcome.AMBIGUOUS_ROOT,
            Outcome.BROKEN_BINDING,
            Outcome.PARTIAL_TRACKING,
            Outcome.FORBIDDEN_SCOPE,
            Outcome.LINT_FAILED,
        }
        for name, probe in scenario_matrix().items():
            result = classify(probe, ORIGIN)
            if result.outcome in rejected:
                with self.subTest(name=name):
                    self.assertEqual(probe.before_tree_oid, result.protected_tree_oid)
                    self.assertIsNone(result.candidate_ref)

    def test_generated_markdown_is_precise_about_file_kind_and_mode(self) -> None:
        for bad_change in (
            FileChange("wiki/concepts/link.md", kind="symlink"),
            FileChange("wiki/concepts/tool.md", executable=True),
            FileChange("wiki/assets/image.png"),
            FileChange("../wiki/concepts/escape.md"),
        ):
            with self.subTest(path=bad_change.path):
                result = classify(Probe(("knowledge",), (bad_change,)), ORIGIN)
                self.assertEqual(Outcome.FORBIDDEN_SCOPE, result.outcome)
                self.assertEqual("tree-before", result.protected_tree_oid)

    def test_tracked_and_untracked_delivery_are_separate(self) -> None:
        matrix = scenario_matrix()
        direct = classify(matrix["untracked"], ORIGIN)
        tracked = classify(matrix["tracked"], ORIGIN)
        self.assertEqual("tree-after", direct.protected_tree_oid)
        self.assertIsNone(direct.candidate_ref)
        self.assertEqual("tree-before", tracked.protected_tree_oid)
        self.assertEqual("tree-after", tracked.candidate_ref.candidate_tree_oid)

    def test_two_fresh_identity_designs_are_distinct_and_origin_reuse_fails(self) -> None:
        probe = scenario_matrix()["tracked"]
        synthetic = classify(
            probe, ORIGIN, identity_design=IdentityDesign.SYNTHETIC_TICKET
        )
        effect = classify(
            probe, ORIGIN, identity_design=IdentityDesign.COMPLETION_EFFECT
        )
        reused = classify(probe, ORIGIN, identity_design=IdentityDesign.REUSE_ORIGIN)
        self.assertEqual(Outcome.TRACKED_CANDIDATE, synthetic.outcome)
        self.assertEqual(Outcome.TRACKED_CANDIDATE, effect.outcome)
        self.assertNotEqual(
            synthetic.candidate_ref.ticket_digest, effect.candidate_ref.ticket_digest
        )
        self.assertNotEqual(ORIGIN.ticket_digest, effect.candidate_ref.ticket_digest)
        self.assertEqual(Outcome.STALE_IDENTITY, reused.outcome)
        self.assertEqual(probe.before_tree_oid, reused.protected_tree_oid)

    def test_request_designs_expose_the_caller_allowlist_counterexample(self) -> None:
        assessments = {item.design: item for item in assess_designs()}
        self.assertTrue(assessments[RequestDesign.VERSIONED_PROFILE].viable)
        self.assertTrue(assessments[RequestDesign.SEPARATE_REQUEST].viable)
        caller = assessments[RequestDesign.CALLER_ALLOWLIST]
        self.assertFalse(caller.viable)
        self.assertIn("llm-wiki-project.json", caller.counterexample)
        result = classify(
            scenario_matrix()["tracked"],
            ORIGIN,
            request_design=RequestDesign.CALLER_ALLOWLIST,
        )
        self.assertEqual(Outcome.UNSAFE_POLICY, result.outcome)

    def test_scaffolded_generated_markdown_passes_real_wiki_lint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ws02-wiki-") as directory:
            wiki_root = Path(directory) / "knowledge"
            scaffold = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(REPO / "llm-wiki/scripts/scaffold.py"),
                    str(wiki_root),
                    "WS-02 Fixture",
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, scaffold.returncode, scaffold.stderr or scaffold.stdout)
            generated = (
                FileChange("wiki/index.md"),
                FileChange("wiki/log.md"),
            )
            scope = classify(Probe((str(wiki_root),), generated), ORIGIN)
            self.assertEqual(Outcome.DIRECT_VALIDATED, scope.outcome)
            lint = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(REPO / "llm-wiki/scripts/lint_wiki.py"),
                    str(wiki_root),
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, lint.returncode, lint.stderr or lint.stdout)


if __name__ == "__main__":
    unittest.main()
