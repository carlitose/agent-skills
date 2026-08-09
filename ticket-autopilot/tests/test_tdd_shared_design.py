from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TDD_ROOT = REPO_ROOT / "tdd"


def text(name: str) -> str:
    return (TDD_ROOT / name).read_text(encoding="utf-8")


class TddSharedDesignTests(unittest.TestCase):
    def test_tdd_keeps_only_its_owned_guidance(self) -> None:
        self.assertEqual(
            {"SKILL.md", "mocking.md", "tests.md"},
            {
                str(path.relative_to(TDD_ROOT))
                for path in TDD_ROOT.rglob("*")
                if path.is_file()
            },
        )

    def test_planning_uses_shared_design_vocabulary_and_gates_only_ambiguity(self) -> None:
        skill = text("SKILL.md")

        self.assertIn("[codebase-design](../codebase-design/SKILL.md)", skill)
        self.assertIn("[deepening guidance](../codebase-design/DEEPENING.md)", skill)
        self.assertIn("agree the Seam before mocking", skill)
        self.assertIn("materially unresolved", skill)
        self.assertIn("open an explicit human gate", skill)
        self.assertIn("Do not add a ceremonial gate", skill)

    def test_mocking_requires_an_agreed_boundary(self) -> None:
        mocking = text("mocking.md")

        self.assertIn("Mock only across an agreed Seam", mocking)
        self.assertIn("do not invent a boundary in the test", mocking)
        self.assertIn("return to the TDD planning gate", mocking)
        self.assertIn("observable behavior", mocking)

    def test_tests_reject_tautologies_and_include_a_causal_red_green_example(self) -> None:
        tests = text("tests.md")

        self.assertIn("Tautological tests", tests)
        self.assertIn("restates a production constant", tests)
        self.assertIn("mirrors the implementation branch or algorithm", tests)
        self.assertIn("asserts only mock-call choreography", tests)
        self.assertIn("What production behavior change would make this fail?", tests)
        self.assertRegex(tests, r"(?s)### Causal RED.*### Minimal GREEN")

    def test_post_green_quality_stays_with_existing_owners(self) -> None:
        skill = text("SKILL.md")
        executor = (REPO_ROOT / "execute-ticket" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("[code-simplification](../code-simplification/SKILL.md)", skill)
        self.assertIn("[code-review](../code-review/SKILL.md)", skill)
        self.assertIn("TDD does not own either quality stage", skill)
        self.assertIn("Never refactor while RED", skill)
        self.assertIn("Invoke focused cleanup through `code-simplification`", executor)
        self.assertIn("Invoke read-only `code-review`", executor)

    def test_removed_local_guides_have_no_inbound_links(self) -> None:
        removed = {"deep-modules.md", "interface-design.md", "refactoring.md"}

        for name in removed:
            self.assertFalse((TDD_ROOT / name).exists())
        for path in REPO_ROOT.rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            targets = set(re.findall(r"\[[^]]+\]\(([^)#?]+\.md)", content))
            for name in removed:
                with self.subTest(path=path, target=name):
                    self.assertFalse(any(target.endswith(f"/{name}") or target == name for target in targets))


if __name__ == "__main__":
    unittest.main()
