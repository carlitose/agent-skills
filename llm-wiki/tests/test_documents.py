"""The documents describe the layout the scripts implement.

The failure this guards is drift, not absence: a document that describes a plausible layout
nobody builds is worse than no document, because a reader follows it and gets a wiki that
fails its own lint.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lint_wiki import LAYOUT_DIRECTORIES, LAYOUT_FILES, LOG_OPERATIONS  # noqa: E402

SKILL = SKILL_ROOT / "SKILL.md"
REFERENCES = sorted((SKILL_ROOT / "references").glob("*.md"))

# Paths the retired layout had. A document naming one is describing a tree the scaffold no
# longer builds.
RETIRED = (
    "CLAUDE.md",
    "log/YYYYMMDD",
    "wiki/summaries",
    "outputs/",
    "raw/articles",
    "raw/papers",
    "raw/notes",
    "plugins/obsidian-audit",
    "audit-shared",
)

# Two places name the retired shape on purpose: the migration instructions, and the note in
# scaffold.py saying what is gone.
RETIRED_ALLOWED = {
    ("references/log-guide.md", "log/YYYYMMDD"),
    ("scripts/scaffold.py", "CLAUDE.md"),
    ("scripts/scaffold.py", "log/YYYYMMDD"),
    ("scripts/scaffold.py", "wiki/summaries"),
    ("scripts/scaffold.py", "outputs/"),
}

COMMAND_RE = re.compile(r"python3? +(?:-B +)?scripts/([a-z_]+\.py)")


def documents() -> list[Path]:
    return [SKILL, *REFERENCES]


def prose_and_scripts() -> list[Path]:
    return [*documents(), *sorted(SCRIPTS.glob("*.py"))]


class LayoutAgreementTests(unittest.TestCase):
    def test_skill_md_names_every_directory_the_layout_has(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        missing = [
            relative
            for relative in LAYOUT_DIRECTORIES
            if relative.rsplit("/", 1)[-1] + "/" not in text
        ]

        self.assertEqual([], missing)

    def test_skill_md_names_every_file_the_layout_has(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        missing = [relative for relative in LAYOUT_FILES if relative not in text]

        self.assertEqual([], missing)

    def test_no_document_describes_the_retired_layout(self) -> None:
        offenders: list[str] = []
        for path in prose_and_scripts():
            relative = path.relative_to(SKILL_ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            for token in RETIRED:
                if token in text and (relative, token) not in RETIRED_ALLOWED:
                    offenders.append(f"{relative}: {token}")

        self.assertEqual([], offenders)

    def test_every_allowlisted_exception_is_still_needed(self) -> None:
        """An allowlist that outlives its reason is how drift creeps back in."""

        stale: list[str] = []
        for relative, token in sorted(RETIRED_ALLOWED):
            text = (SKILL_ROOT / relative).read_text(encoding="utf-8")
            if token not in text:
                stale.append(f"{relative}: {token} is allowlisted but absent")

        self.assertEqual([], stale)


class CommandTests(unittest.TestCase):
    def test_every_documented_command_names_a_script_that_exists(self) -> None:
        broken: list[str] = []
        found = 0
        for path in documents():
            relative = path.relative_to(SKILL_ROOT).as_posix()
            for name in COMMAND_RE.findall(path.read_text(encoding="utf-8")):
                found += 1
                if not (SCRIPTS / name).is_file():
                    broken.append(f"{relative}: scripts/{name}")

        self.assertEqual([], broken)
        self.assertGreater(found, 3, "the command regex matched almost nothing")

    def test_the_interpreter_caveat_is_stated_where_the_commands_are(self) -> None:
        """`python3` is the repository convention and does not resolve on Windows."""

        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("python3 scripts/", text)
        self.assertIn("Microsoft Store alias", text)

    def test_every_script_the_skill_ships_is_named_in_skill_md(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        unmentioned = [
            script.name
            for script in sorted(SCRIPTS.glob("*.py"))
            if script.name not in text and script.name != "console.py"
        ]

        self.assertEqual([], unmentioned)


class FrontMatterTests(unittest.TestCase):
    def test_the_description_is_one_plain_single_line_scalar(self) -> None:
        """A folded block scalar here is valid YAML that this repository's readers reject.

        It shipped once and took three unrelated tests red with it.
        """

        lines = SKILL.read_text(encoding="utf-8").splitlines()

        self.assertEqual("---", lines[0])
        self.assertEqual("---", lines[3], "front matter must be exactly name and description")
        self.assertTrue(lines[1].startswith("name: "))
        self.assertTrue(lines[2].startswith("description: "))
        for line in lines[1:3]:
            self.assertNotIn(": >", line)
            self.assertNotIn(": |", line)
            self.assertFalse(line.rstrip().endswith((">", "|")), line)
            self.assertFalse(line.startswith((" ", "\t")), line)

    def test_the_description_names_what_the_skill_now_does(self) -> None:
        description = SKILL.read_text(encoding="utf-8").splitlines()[2]

        for expected in ("audit/", "timeline", "raw/sources/", "lint"):
            self.assertIn(expected, description)


class LogOperationTests(unittest.TestCase):
    def test_every_operation_lint_accepts_is_documented(self) -> None:
        text = (SKILL_ROOT / "references" / "log-guide.md").read_text(encoding="utf-8")
        missing = [
            operation for operation in sorted(LOG_OPERATIONS) if f"`{operation}`" not in text
        ]

        self.assertEqual([], missing)


class PassTableTests(unittest.TestCase):
    """The lint table in SKILL.md against the passes that exist.

    A documented pass count that is one behind the code is how `SKILL.md` came to advertise
    seven passes while the script ran eight, and nothing caught it.
    """

    def _every_pass(self) -> list:
        import tempfile

        from lint_drift import (
            check_dangling_source,
            check_duplicate_identity,
            check_provenance,
            check_session_pointers,
            check_stale_page,
            check_timeline_coverage,
            check_un_ingested,
        )
        from lint_wiki import run_passes

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "wiki").mkdir()
            (root / "wiki" / "index.md").write_text("# Index\n", encoding="utf-8")
            structural = [
                result for result in run_passes(root) if result.name != "project-drift"
            ]
            drift = [
                check_dangling_source(root, root, [], set()),
                check_stale_page(root, root, []),
                check_duplicate_identity([]),
                check_provenance([]),
                check_timeline_coverage(root, []),
                check_session_pointers(root, []),
                check_un_ingested([], set()),
            ]
        return structural + drift

    def test_every_pass_is_in_the_table_with_its_severity(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        missing: list[str] = []
        for result in self._every_pass():
            row = f"| `{result.name}` | {result.severity} |"
            if row not in text:
                missing.append(row)

        self.assertEqual([], missing)

    def test_the_documented_pass_count_is_the_real_one(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        count = len(self._every_pass())

        self.assertIn(f"Health check, {NUMBERS[count]} passes", text)


NUMBERS = {
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
}


if __name__ == "__main__":
    unittest.main()
