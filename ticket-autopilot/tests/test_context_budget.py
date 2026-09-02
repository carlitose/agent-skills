from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
SCRIPTS = SKILL_ROOT / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
REFERENCE = SKILL_ROOT / "references" / "context-budget-v1.md"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from controlled_inventory import REPOSITORY_ONLY_SKILLS  # noqa: E402
from autopilot.context_budget import (  # noqa: E402
    ContextBudgetError,
    measure_context_budget,
    normalized_bytes,
)


def skill_text(
    name: str,
    description: str,
    *,
    hidden: bool = False,
    newline: str = "\n",
) -> str:
    lines = ["---", f'name: "{name}"', f'description: "{description}"']
    if hidden:
        lines.append("disable-model-invocation: true")
    lines.extend(["---", "", f"# {name}", ""])
    return newline.join(lines)


class NormalizedByteTests(unittest.TestCase):
    def test_newlines_unicode_and_invalid_utf8_follow_the_frozen_unit(self) -> None:
        self.assertEqual(4, normalized_bytes("a\r\nb\r"))
        self.assertEqual(3, normalized_bytes("€"))
        with self.assertRaises(UnicodeDecodeError):
            normalized_bytes(b"\xff")


class ContextBudgetTests(unittest.TestCase):
    def make_repo(self, root: Path) -> tuple[Path, Path]:
        repo = root / "repo"
        install = root / "installed"
        repo.mkdir()
        install.mkdir()
        return repo, install

    def add_skill(
        self,
        root: Path,
        name: str,
        description: str,
        *,
        hidden: bool = False,
        newline: str = "\n",
    ) -> None:
        folder = root / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(
            skill_text(name, description, hidden=hidden, newline=newline),
            encoding="utf-8",
            newline="",
        )

    def add_bounded_skill(self, root: Path, name: str, bound: int) -> None:
        folder = root / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(
            skill_text(name, f"Bounded {name}.")
            + "\n## Volatile intake bound\n\n"
            + f"- `max_volatile_bytes`: `{bound}` normalized UTF-8 bytes.\n",
            encoding="utf-8",
        )

    def write_ceiling(
        self, path: Path, *, workflow: str, ceiling_bytes: int
    ) -> None:
        path.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "unit": "normalized-utf8-bytes",
                    "workflows": {
                        workflow: {
                            "ceiling_bytes": ceiling_bytes,
                            "rationale": "Reviewed fixture ceiling.",
                            "raised_by": "test-fixture",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_listing_distinguishes_visible_hidden_and_repository_only_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, install = self.make_repo(Path(temporary))
            self.add_skill(repo, "visible", "Shown to the model.")
            self.add_skill(repo, "hidden", "Typed by a person.", hidden=True)
            self.add_skill(repo, "not-installed", "Costs nothing today.")
            self.add_skill(install, "visible", "Shown to the model.")
            self.add_skill(install, "hidden", "Typed by a person.", hidden=True)

            report = measure_context_budget(
                repo, install_root=install, workflow=None
            )

        listing = report["always_on_listing"]
        self.assertEqual(1, listing["visible_skill_count"])
        self.assertEqual(1, listing["hidden_skill_count"])
        self.assertEqual(1, listing["repository_only_skill_count"])
        self.assertEqual(
            ["installed-hidden", "repository-only", "installed-visible"],
            [item["status"] for item in listing["skills"]],
        )
        self.assertGreater(report["components"]["always_on_listing_bytes"], 0)
        self.assertGreater(listing["hidden_listing_bytes"], 0)
        self.assertEqual([], report["diagnostics"])
        self.assertTrue(report["complete"])

    def test_malformed_and_missing_front_matter_are_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, install = self.make_repo(Path(temporary))
            broken = repo / "broken"
            broken.mkdir()
            (broken / "SKILL.md").write_text("# no front matter\n", encoding="utf-8")
            shutil.copytree(broken, install / "broken")
            malformed = repo / "malformed"
            malformed.mkdir()
            (malformed / "SKILL.md").write_text(
                "---\nname: malformed\ndescription: |\n  unsupported\n---\n",
                encoding="utf-8",
            )
            shutil.copytree(malformed, install / "malformed")

            report = measure_context_budget(
                repo, install_root=install, workflow=None
            )

        self.assertEqual(
            ["malformed-front-matter", "malformed-front-matter"],
            [item["code"] for item in report["diagnostics"]],
        )
        self.assertEqual(
            ["malformed", "malformed"],
            [item["status"] for item in report["always_on_listing"]["skills"]],
        )
        self.assertFalse(report["complete"])
        self.assertFalse(report["always_on_listing"]["complete"])
        self.assertIsNone(report["components"]["always_on_listing_bytes"])

    def test_empty_catalogue_is_a_valid_zero_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, install = self.make_repo(Path(temporary))
            report = measure_context_budget(
                repo, install_root=install, workflow=None
            )

        self.assertEqual(1, report["schema"])
        self.assertEqual(0, report["components"]["always_on_listing_bytes"])
        self.assertEqual([], report["always_on_listing"]["skills"])
        self.assertEqual([], report["diagnostics"])
        self.assertTrue(report["complete"])

    def test_workflow_manifest_is_ordered_normalized_and_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, install = self.make_repo(Path(temporary))
            self.add_skill(repo, "root", "Root workflow.", newline="\r\n")
            self.add_skill(install, "root", "Root workflow.", newline="\r\n")
            reference = repo / "root" / "reference.md"
            reference.write_text("é\r\nline\r", encoding="utf-8", newline="")

            report = measure_context_budget(
                repo,
                install_root=install,
                workflow="root",
                workflow_manifests={"root": ("root/SKILL.md", "root/reference.md")},
            )

            with self.assertRaisesRegex(ContextBudgetError, "duplicate logical source"):
                measure_context_budget(
                    repo,
                    install_root=install,
                    workflow="root",
                    workflow_manifests={"root": ("root/SKILL.md", "root/SKILL.md")},
                )

        closure = report["workflow_static_closure"]
        self.assertEqual(
            ["root/SKILL.md", "root/reference.md"],
            [item["path"] for item in closure["sources"]],
        )
        self.assertEqual(
            sum(item["normalized_bytes"] for item in closure["sources"]),
            closure["normalized_bytes"],
        )
        self.assertTrue(closure["complete"])
        self.assertEqual(2, closure["expected_source_count"])

    def test_unreadable_workflow_source_cannot_produce_an_authoritative_total(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, install = self.make_repo(Path(temporary))
            report = measure_context_budget(
                repo,
                install_root=install,
                workflow="missing",
                workflow_manifests={"missing": ("absent.md",)},
            )

        self.assertFalse(report["complete"])
        self.assertFalse(report["workflow_static_closure"]["complete"])
        self.assertIsNone(report["components"]["workflow_static_closure_bytes"])
        self.assertEqual(
            ["unreadable-workflow-source"],
            [item["code"] for item in report["diagnostics"]],
        )

    def test_cli_json_is_versioned_read_only_and_provider_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, install = self.make_repo(Path(temporary))
            self.add_skill(repo, "visible", "Shown to the model.")
            self.add_skill(install, "visible", "Shown to the model.")
            before = sorted(
                (path.relative_to(repo).as_posix(), path.read_bytes())
                for path in repo.rglob("*")
                if path.is_file()
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "context-budget",
                    str(repo),
                    "--install-root",
                    str(install),
                    "--no-workflow",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            after = sorted(
                (path.relative_to(repo).as_posix(), path.read_bytes())
                for path in repo.rglob("*")
                if path.is_file()
            )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual("context-budget", payload["command"])
        self.assertEqual(1, payload["data"]["schema"])
        self.assertEqual(before, after)

    def test_human_output_and_schema_reference_cover_the_public_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, install = self.make_repo(Path(temporary))
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(CLI),
                    "context-budget",
                    str(repo),
                    "--install-root",
                    str(install),
                    "--no-workflow",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("UNIT\tnormalized-utf8-bytes", completed.stdout)
        self.assertIn("ALWAYS_ON_LISTING\t0", completed.stdout)
        reference = REFERENCE.read_text(encoding="utf-8")
        for field in (
            "always_on_listing_bytes",
            "workflow_static_closure_bytes",
            "variable_leaf_input_bytes",
            "composed_total_bytes",
            "hidden_listing_bytes",
            "repository_only_skill_count",
            "external_installed_skills",
            "expected_source_count",
            "logical_source",
            "sha256",
            "worst_case_scenario",
            "observed_consumption",
            "--check-ceiling",
            "diagnostics",
        ):
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", reference)

    def test_repository_baseline_reproduces_the_autopilot_inventory(self) -> None:
        absent = REPOSITORY_ONLY_SKILLS
        with tempfile.TemporaryDirectory() as temporary:
            install = Path(temporary) / "installed"
            install.mkdir()
            for skill in sorted(REPO_ROOT.glob("*/SKILL.md")):
                if skill.parent.name not in absent:
                    shutil.copytree(skill.parent, install / skill.parent.name)

            report = measure_context_budget(
                REPO_ROOT,
                install_root=install,
                workflow="ticket-autopilot",
            )

        listing = report["always_on_listing"]
        closure = report["workflow_static_closure"]
        self.assertEqual(23, listing["visible_skill_count"])
        self.assertEqual(7, listing["hidden_skill_count"])
        self.assertEqual(4, listing["repository_only_skill_count"])
        self.assertEqual(11, closure["source_count"])
        self.assertEqual(8_327, closure["word_count"])
        self.assertEqual(65_319, closure["normalized_bytes"])
        self.assertEqual(5_280, listing["normalized_bytes"])
        self.assertEqual(
            107_656, report["components"]["variable_leaf_input_bytes"]
        )
        self.assertEqual(178_255, report["components"]["composed_total_bytes"])
        self.assertEqual("code-review", report["worst_case_scenario"]["leaf"])
        self.assertEqual("exceeded", report["ceiling"]["status"])
        self.assertEqual(1_352, report["ceiling"]["delta_bytes"])
        self.assertTrue(report["complete"])

    def test_composed_ceiling_uses_static_prefix_and_largest_applicable_leaf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, install = self.make_repo(Path(temporary))
            self.add_skill(repo, "root", "Root workflow.")
            self.add_skill(install, "root", "Root workflow.")
            self.add_bounded_skill(repo, "leaf-a", 100)
            self.add_bounded_skill(repo, "leaf-b", 250)
            source = repo / "root" / "reference.md"
            source.write_text("static reference\n", encoding="utf-8")
            ceiling = Path(temporary) / "ceilings.json"

            informational = measure_context_budget(
                repo,
                install_root=install,
                workflow="root",
                workflow_manifests={
                    "root": ("root/SKILL.md", "root/reference.md")
                },
                workflow_leaf_skills={"root": ("leaf-a", "leaf-b")},
            )
            total = informational["components"]["composed_total_bytes"]
            self.write_ceiling(ceiling, workflow="root", ceiling_bytes=total)
            report = measure_context_budget(
                repo,
                install_root=install,
                workflow="root",
                workflow_manifests={
                    "root": ("root/SKILL.md", "root/reference.md")
                },
                workflow_leaf_skills={"root": ("leaf-a", "leaf-b")},
                ceiling_config=ceiling,
            )

        components = report["components"]
        fixed = (
            components["always_on_listing_bytes"]
            + components["workflow_static_closure_bytes"]
        )
        self.assertEqual(250, components["variable_leaf_input_bytes"])
        self.assertEqual(fixed + 250, components["composed_total_bytes"])
        self.assertEqual("leaf-b", report["worst_case_scenario"]["leaf"])
        self.assertEqual("within", report["ceiling"]["status"])
        self.assertEqual("upper-bound", report["measurement_kind"])
        self.assertFalse(report["observed_consumption"])
        self.assertGreaterEqual(len(report["worst_case_assumptions"]), 4)

    def test_absent_ceiling_is_informational(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo, install = self.make_repo(Path(temporary))
            self.add_skill(repo, "root", "Root workflow.")
            self.add_skill(install, "root", "Root workflow.")
            self.add_bounded_skill(repo, "leaf", 100)
            report = measure_context_budget(
                repo,
                install_root=install,
                workflow="root",
                workflow_manifests={"root": ("root/SKILL.md",)},
                workflow_leaf_skills={"root": ("leaf",)},
            )

        self.assertEqual("informational", report["ceiling"]["status"])
        self.assertFalse(report["ceiling"]["configured"])

    def test_cli_check_distinguishes_breach_from_deliberate_raise(self) -> None:
        absent = {"peer-programming", "pr-antipattern-review", "project-blueprint"}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = root / "installed"
            install.mkdir()
            for skill in sorted(REPO_ROOT.glob("*/SKILL.md")):
                if skill.parent.name not in absent:
                    shutil.copytree(skill.parent, install / skill.parent.name)
            ceiling = root / "ceilings.json"
            self.write_ceiling(
                ceiling, workflow="ticket-autopilot", ceiling_bytes=1
            )
            command = [
                sys.executable,
                "-B",
                str(CLI),
                "context-budget",
                str(REPO_ROOT),
                "--install-root",
                str(install),
                "--ceiling-config",
                str(ceiling),
                "--check-ceiling",
                "--json",
            ]

            breached = subprocess.run(
                command, text=True, capture_output=True, check=False
            )
            self.write_ceiling(
                ceiling,
                workflow="ticket-autopilot",
                ceiling_bytes=10_000_000,
            )
            raised = subprocess.run(
                command, text=True, capture_output=True, check=False
            )

        self.assertEqual(2, breached.returncode)
        self.assertIn("exceeds configured ceiling", breached.stdout)
        self.assertEqual(0, raised.returncode, raised.stderr)
        self.assertEqual(
            "within", json.loads(raised.stdout)["data"]["ceiling"]["status"]
        )


if __name__ == "__main__":
    unittest.main()
