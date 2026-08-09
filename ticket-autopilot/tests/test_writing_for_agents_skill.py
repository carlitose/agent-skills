from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "writing-for-agents"


def text(name: str) -> str:
    return (SKILL_ROOT / name).read_text(encoding="utf-8")


class WritingForAgentsSkillTests(unittest.TestCase):
    def test_package_contains_only_the_owned_artifacts(self) -> None:
        self.assertEqual(
            {"SKILL.md", "SKILL-MECHANICS.md", "agents/openai.yaml"},
            {
                str(path.relative_to(SKILL_ROOT))
                for path in SKILL_ROOT.rglob("*")
                if path.is_file()
            },
        )

    def test_frontmatter_supports_implicit_agent_document_invocation(self) -> None:
        skill = text("SKILL.md")
        frontmatter = skill.split("---", 2)[1]

        self.assertRegex(frontmatter, r"(?m)^name: writing-for-agents$")
        for trigger in ("agent", "skill", "AGENTS.md", "CLAUDE.md"):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, frontmatter)
        self.assertNotIn("disable-model-invocation", frontmatter)

    def test_skill_owns_writing_quality_but_not_scaffolding(self) -> None:
        skill = text("SKILL.md")

        self.assertIn("Owns: writing clarity for agent-consumed documents", skill)
        self.assertIn("`skill-creator` remains the scaffold owner", skill)
        self.assertIn("does not create package structure", skill)
        self.assertIn("[SKILL-MECHANICS.md](SKILL-MECHANICS.md)", skill)
        self.assertIn("[SKILL.md](SKILL.md)", text("SKILL-MECHANICS.md"))

    def test_reference_covers_the_required_writing_levers(self) -> None:
        skill = text("SKILL.md")

        for marker in (
            "Context pointer",
            "Context load",
            "Cognitive load",
            "Information hierarchy",
            "Completion criterion",
            "Leading word",
            "Single source of truth",
            "Prune",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)
        self.assertIn("checkable and exhaustive", skill)
        self.assertIn("positive target behavior", skill)

    def test_examples_separate_writing_guidance_from_skill_generation(self) -> None:
        skill = text("SKILL.md")

        self.assertIn("Rewrite this AGENTS.md pointer", skill)
        self.assertIn("Use this reference", skill)
        self.assertIn("Create a new reusable skill package", skill)
        self.assertIn("Use `skill-creator`", skill)
        self.assertNotIn("Create the skill directory", skill)

    def test_skill_mechanics_and_metadata_are_linked_and_valid(self) -> None:
        mechanics = text("SKILL-MECHANICS.md")
        metadata = text("agents/openai.yaml")

        self.assertIn("Model-invoked", mechanics)
        self.assertIn("User-invoked", mechanics)
        self.assertIn("Router skill", mechanics)
        self.assertIn("description is the always-loaded context pointer", mechanics)
        self.assertIn('display_name: "Writing for Agents"', metadata)
        self.assertIn(
            'short_description: "Write clear documents for agents"', metadata
        )
        self.assertIn("$writing-for-agents", metadata)
        for document in (text("SKILL.md"), mechanics):
            for target in re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", document):
                with self.subTest(target=target):
                    self.assertTrue((SKILL_ROOT / target).is_file())


if __name__ == "__main__":
    unittest.main()
