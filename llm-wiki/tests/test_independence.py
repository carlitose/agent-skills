"""The skill is independent of the LLM Wiki desktop application.

`docs/specs/llm-wiki-app-independence-decision.md` decided this: nothing here may require
that application to be installed, running, or ever to have run. The three coupling surfaces
it named are its private state directory, its HTTP API, and its MCP tools.

The forbidden strings are assembled from fragments on purpose. Written out, this file would
be the first thing its own check catches, and a check that reports its own text is a check
nobody trusts.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]

# Assembled, never written whole. See the module docstring.
STATE_DIRECTORY = "." + "llm-wiki/"
HTTP_API = "/api/" + "v1"
MCP_PREFIX = "llm" + "_wiki_"

FORBIDDEN = {
    STATE_DIRECTORY: "the application's private state directory",
    HTTP_API: "the application's HTTP API",
    MCP_PREFIX: "the application's MCP tools",
}

SKIP_DIRECTORIES = {"__pycache__", ".git"}


def skill_files() -> list[Path]:
    return [
        path
        for path in sorted(SKILL_ROOT.rglob("*"))
        if path.is_file()
        and not SKIP_DIRECTORIES & set(path.parts)
        and path.resolve() != Path(__file__).resolve()
    ]


def couplings(paths: list[Path], relative_to: Path) -> list[str]:
    """Every forbidden token found, as `<relative path>: <what it couples to>`."""

    found: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(relative_to).as_posix()
        for token, what in FORBIDDEN.items():
            if token in text:
                found.append(f"{relative}: {what}")
    return found


class IndependenceTests(unittest.TestCase):
    def test_no_file_couples_the_skill_to_the_application(self) -> None:
        self.assertEqual([], couplings(skill_files(), SKILL_ROOT))

    def test_the_check_covers_the_scripts_and_the_documents(self) -> None:
        """A check over an empty file set passes for the wrong reason."""

        covered = {path.relative_to(SKILL_ROOT).as_posix() for path in skill_files()}

        self.assertIn("SKILL.md", covered)
        self.assertIn("scripts/lint_wiki.py", covered)
        self.assertIn("scripts/scaffold.py", covered)
        self.assertIn("references/schema-guide.md", covered)
        self.assertGreater(len(covered), 15, covered)

    def test_the_check_catches_each_forbidden_token_when_seeded(self) -> None:
        """One seeded defect per token, through the same function the real check uses."""

        for token, what in FORBIDDEN.items():
            with self.subTest(token=what):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    seeded = root / "guide.md"
                    seeded.write_text(f"Call {token} to fetch the pages.\n", encoding="utf-8")
                    clean = root / "clean.md"
                    clean.write_text("Read the wiki from disk.\n", encoding="utf-8")

                    found = couplings([clean, seeded], root)

                self.assertEqual([f"guide.md: {what}"], found)

    def test_no_script_imports_a_third_party_package(self) -> None:
        """Independence includes the environment: standard library only, no install step."""

        allowed_roots = {path.stem for path in (SKILL_ROOT / "scripts").glob("*.py")}
        third_party: list[str] = []
        for script in sorted((SKILL_ROOT / "scripts").glob("*.py")):
            for number, line in enumerate(
                script.read_text(encoding="utf-8").splitlines(), start=1
            ):
                stripped = line.strip()
                if not stripped.startswith(("import ", "from ")):
                    continue
                module = stripped.split()[1].split(".")[0]
                if module in allowed_roots or module in STANDARD_LIBRARY:
                    continue
                third_party.append(f"{script.name}:{number} {module}")

        self.assertEqual([], third_party)


STANDARD_LIBRARY = {
    "__future__",
    "argparse",
    "collections",
    "dataclasses",
    "datetime",
    "hashlib",
    "itertools",
    "json",
    "os",
    "pathlib",
    "posixpath",
    "re",
    "shutil",
    "subprocess",
    "sys",
    "tempfile",
    "textwrap",
    "typing",
    "unicodedata",
}


if __name__ == "__main__":
    unittest.main()
