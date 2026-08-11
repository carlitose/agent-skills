from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"
AUTOPILOT_SKILL = REPO_ROOT / "ticket-autopilot" / "SKILL.md"
SECTION_HEADING = "### Run dependencies"


def section(text: str, heading: str) -> str:
    """Return one Markdown section body without its following sibling sections."""

    start = text.index(heading) + len(heading)
    level = heading.split(" ", 1)[0]
    remainder = text[start:]
    match = re.search(rf"^#{{1,{len(level)}}} ", remainder, re.MULTILINE)
    return remainder[: match.start()] if match else remainder


def dependency_section() -> str:
    """Return the README run-dependency section body."""

    return section(README.read_text(encoding="utf-8"), SECTION_HEADING)


def documented_composition() -> dict[str, set[str]]:
    """Read the README dependency table as composer -> composed skills."""

    composition: dict[str, set[str]] = {}
    for line in dependency_section().splitlines():
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != 3 or cells[0] in {"Composed by", "---"}:
            continue
        skill = re.search(r"\[`([^`]+)`\]", cells[1])
        if skill is None:
            continue
        composer = cells[0].strip("`")
        composition.setdefault(composer, set()).add(skill.group(1))
    return composition


def bullets(body: str) -> list[str]:
    """Join wrapped Markdown bullets so one bullet is one logical line."""

    joined: list[str] = []
    for line in body.splitlines():
        if line.startswith("- "):
            joined.append(line[2:].strip())
        elif joined and line.startswith("  ") and line.strip():
            joined[-1] = f"{joined[-1]} {line.strip()}"
    return joined


def declared_composition() -> dict[str, set[str]]:
    """Read the authoritative composition from the autopilot component boundaries."""

    body = section(AUTOPILOT_SKILL.read_text(encoding="utf-8"), "## Component boundaries")
    declared: dict[str, set[str]] = {"scheduler": set(), "execute-ticket": set()}
    for bullet in bullets(body):
        subject, _, description = bullet.partition(":")
        names = re.findall(r"`([^`]+)`", subject)
        if not names:
            continue
        target = (
            "execute-ticket"
            if "composed inside `execute-ticket`" in description
            else "scheduler"
        )
        declared[target].update(names)
    return declared


class ReadmeDependencyTests(unittest.TestCase):
    def test_readme_documents_the_declared_run_composition(self) -> None:
        documented = documented_composition()
        declared = declared_composition()
        self.assertEqual(
            documented.get("execute-ticket", set()),
            declared["execute-ticket"],
            "README leaf workers drifted from the autopilot component boundaries",
        )
        self.assertEqual(
            documented.get("scheduler", set()),
            declared["scheduler"],
            "README scheduler-composed skills drifted from the component boundaries",
        )

    def test_documented_skills_resolve_to_real_skill_files(self) -> None:
        for skills in documented_composition().values():
            for skill in skills:
                with self.subTest(skill=skill):
                    self.assertTrue(
                        (REPO_ROOT / skill / "SKILL.md").is_file(),
                        f"documented skill {skill!r} has no SKILL.md",
                    )

    def test_every_autopilot_reference_is_documented(self) -> None:
        body = dependency_section()
        references = sorted(
            (REPO_ROOT / "ticket-autopilot" / "references").glob("*.md")
        )
        self.assertTrue(references, "no autopilot references were discovered")
        for reference in references:
            relative = reference.relative_to(REPO_ROOT).as_posix()
            with self.subTest(reference=relative):
                self.assertIn(
                    relative,
                    body,
                    f"reference {relative!r} is loaded by a run but undocumented",
                )

    def test_documented_references_exist(self) -> None:
        targets = re.findall(r"\]\(([^)]+\.md)\)", dependency_section())
        self.assertTrue(targets, "the dependency section links no references")
        for target in targets:
            with self.subTest(target=target):
                self.assertTrue(
                    (REPO_ROOT / target).is_file(),
                    f"documented dependency {target!r} does not exist",
                )


if __name__ == "__main__":
    unittest.main()
