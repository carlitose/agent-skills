from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "codebase-design"


def text(name: str) -> str:
    return (SKILL_ROOT / name).read_text(encoding="utf-8")


class CodebaseDesignSkillTests(unittest.TestCase):
    def test_package_contains_exactly_the_four_owned_artifacts(self) -> None:
        self.assertEqual(
            {
                "DEEPENING.md",
                "DESIGN-IT-TWICE.md",
                "SKILL.md",
                "agents/openai.yaml",
            },
            {
                str(path.relative_to(SKILL_ROOT))
                for path in SKILL_ROOT.rglob("*")
                if path.is_file()
            },
        )

    def test_skill_owns_vocabulary_without_execution_authority(self) -> None:
        skill = text("SKILL.md")
        frontmatter = skill.split("---", 2)[1]

        self.assertRegex(frontmatter, r"(?m)^name: codebase-design$")
        for trigger in ("module", "interface", "seam", "adapter", "testable"):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, frontmatter.lower())
        self.assertIn("Owns: shared codebase-design vocabulary", skill)
        self.assertIn("does not implement, review, schedule, or deliver", skill)
        for term in (
            "**Module**",
            "**Interface**",
            "**Implementation**",
            "**Depth**",
            "**Seam**",
            "**Adapter**",
            "**Leverage**",
            "**Locality**",
        ):
            with self.subTest(term=term):
                self.assertIn(term, skill)

    def test_internal_links_are_reciprocal_and_resolve(self) -> None:
        skill = text("SKILL.md")
        deepening = text("DEEPENING.md")
        design_twice = text("DESIGN-IT-TWICE.md")

        self.assertIn("[DEEPENING.md](DEEPENING.md)", skill)
        self.assertIn("[DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md)", skill)
        self.assertIn("[SKILL.md](SKILL.md)", deepening)
        self.assertIn("[DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md)", deepening)
        self.assertIn("[SKILL.md](SKILL.md)", design_twice)
        self.assertIn("[DEEPENING.md](DEEPENING.md)", design_twice)
        for document in (skill, deepening, design_twice):
            for target in re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", document):
                with self.subTest(target=target):
                    self.assertTrue((SKILL_ROOT / target).is_file())

    def test_deepening_and_design_it_twice_keep_safe_local_contracts(self) -> None:
        deepening = text("DEEPENING.md")
        design_twice = text("DESIGN-IT-TWICE.md")

        for category in (
            "In-process",
            "Local-substitutable",
            "Remote but owned",
            "True external",
        ):
            with self.subTest(category=category):
                self.assertIn(category, deepening)
        self.assertIn("replace, don't layer", deepening.lower())
        self.assertIn("explicit delegation authority", design_twice)
        self.assertIn("serially inline", design_twice)
        self.assertIn("Do not claim independent or parallel", design_twice)
        for criterion in ("depth", "locality", "seam placement"):
            self.assertIn(criterion, design_twice.lower())
        self.assertNotIn("Spawn 3+ sub-agents in parallel", design_twice)

    def test_openai_metadata_matches_the_skill(self) -> None:
        metadata = text("agents/openai.yaml")

        self.assertIn('display_name: "Codebase Design"', metadata)
        self.assertIn('short_description: "Shared vocabulary for deep module design"', metadata)
        self.assertIn("$codebase-design", metadata)


if __name__ == "__main__":
    unittest.main()
