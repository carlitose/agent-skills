from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY = REPO_ROOT / "docs" / "model-invocation-policy.md"
CLASSIFICATIONS = {"model-invocable", "user-invoked"}


def front_matter(skill: Path) -> str:
    match = re.match(r"---\n(.*?)\n---", skill.read_text(encoding="utf-8"), re.S)
    return match.group(1) if match else ""


def repository_skills() -> dict[str, str]:
    """Return skill name -> front matter for every skill in the repository."""

    return {
        skill.parent.name: front_matter(skill)
        for skill in sorted(REPO_ROOT.glob("*/SKILL.md"))
    }


def classified() -> dict[str, str]:
    """Read the policy classification table as skill -> classification."""

    table: dict[str, str] = {}
    for line in POLICY.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != 3 or cells[1] not in CLASSIFICATIONS:
            continue
        skill = re.fullmatch(r"`([^`]+)`", cells[0])
        if skill is None:
            continue
        table[skill.group(1)] = cells[1]
    return table


def policy_row(skill: str) -> str:
    """Return the classification table row for one skill."""

    return next(
        line
        for line in POLICY.read_text(encoding="utf-8").splitlines()
        if line.startswith(f"| `{skill}` ")
    )


def hidden(matter: str) -> bool:
    return bool(re.search(r"^disable-model-invocation:\s*true\s*$", matter, re.M))


class ModelInvocationPolicyTests(unittest.TestCase):
    def test_every_skill_is_classified(self) -> None:
        missing = sorted(set(repository_skills()) - set(classified()))
        self.assertEqual(
            missing,
            [],
            "skills exist with no entry in docs/model-invocation-policy.md",
        )

    def test_policy_classifies_no_skill_that_does_not_exist(self) -> None:
        unknown = sorted(set(classified()) - set(repository_skills()))
        self.assertEqual(
            unknown,
            [],
            "the policy classifies skills that are not in this repository",
        )

    def test_flag_matches_classification(self) -> None:
        table = classified()
        for skill, matter in repository_skills().items():
            with self.subTest(skill=skill):
                self.assertEqual(
                    hidden(matter),
                    table.get(skill) == "user-invoked",
                    f"{skill!r} front matter and policy classification disagree",
                )

    def test_wait_what_is_a_user_invoked_compatibility_surface(self) -> None:
        self.assertEqual("user-invoked", classified().get("wait-what"))
        self.assertIn("Ground B:", policy_row("wait-what"))
        self.assertTrue(hidden(repository_skills()["wait-what"]))

    def test_user_invoked_skills_state_a_ground(self) -> None:
        """Every hidden skill must satisfy ground A or ground B, not just be hidden."""

        for skill, classification in classified().items():
            if classification != "user-invoked":
                continue
            with self.subTest(skill=skill):
                self.assertRegex(
                    policy_row(skill),
                    r"Ground [AB]:",
                    f"{skill!r} is hidden without naming a ground in the criterion",
                )

    def test_ground_a_skills_really_carry_an_argument_hint(self) -> None:
        matters = repository_skills()
        for skill, classification in classified().items():
            if classification != "user-invoked":
                continue
            if "Ground A:" not in policy_row(skill):
                continue
            with self.subTest(skill=skill):
                self.assertRegex(
                    matters[skill],
                    r"(?m)^argument-hint:",
                    f"{skill!r} claims ground A but has no argument-hint",
                )


if __name__ == "__main__":
    unittest.main()
