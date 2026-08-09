from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "improve-codebase-architecture" / "SKILL.md"
REFERENCE = REPO_ROOT / "improve-codebase-architecture" / "REFERENCE.md"
FULL_REPO_SKILL = REPO_ROOT / "codebase-improver" / "SKILL.md"


class ImproveCodebaseArchitectureScopeTests(unittest.TestCase):
    def test_shared_design_vocabulary_is_linked_not_redefined(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")

        self.assertIn("[codebase-design](../codebase-design/SKILL.md)", skill)
        self.assertIn(
            "[dependency categories](../codebase-design/DEEPENING.md)",
            skill,
        )
        self.assertIn(
            "[design exercises](../codebase-design/DESIGN-IT-TWICE.md)",
            skill,
        )
        self.assertIn("../codebase-design/DEEPENING.md", reference)
        self.assertNotIn("### 1. In-process", reference)
        self.assertNotIn("### 4. True external (Mock)", reference)
        self.assertNotIn("- **In-process**", reference)
        self.assertIn("canonical dependency category", reference)
        for target in (
            "../codebase-design/SKILL.md",
            "../codebase-design/DEEPENING.md",
            "../codebase-design/DESIGN-IT-TWICE.md",
        ):
            with self.subTest(target=target):
                self.assertTrue((SKILL.parent / target).resolve().is_file())

    def test_discovery_starts_recent_and_widens_only_by_evidence(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        normalized = " ".join(skill.split())

        self.assertIn("Start with recent-change hot spots", normalized)
        for source in ("unstaged changes", "staged changes", "recent commits"):
            with self.subTest(source=source):
                self.assertIn(source, normalized)
        self.assertIn("Recent change is a seed, not proof", normalized)
        self.assertIn("Widen only when observed evidence crosses", normalized)
        self.assertIn("Record the evidence and newly included scope", normalized)

    def test_visual_report_is_optional_ephemeral_and_rfc_is_durable(self) -> None:
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())

        self.assertIn("Visual reports are optional and ephemeral by default", skill)
        self.assertIn("Do not write or commit one unless the user explicitly asks", skill)
        self.assertIn("The refactor RFC is the only default durable output", skill)

    def test_bounded_survey_does_not_take_full_repo_or_routing_ownership(self) -> None:
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        full_repo = FULL_REPO_SKILL.read_text(encoding="utf-8")

        self.assertIn("Owns: a bounded survey", skill)
        self.assertIn("[codebase-improver](../codebase-improver/SKILL.md)", skill)
        self.assertIn("separate human-gated full-repository workflow", skill)
        self.assertNotIn("grilling", skill.lower())
        self.assertNotIn("wayfinder", skill.lower())
        self.assertIn("Self-contained", full_repo)
        self.assertIn("Human-in-the-loop at every gate", full_repo)


if __name__ == "__main__":
    unittest.main()
