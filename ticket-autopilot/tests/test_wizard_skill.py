from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "wizard" / "SKILL.md"
TEMPLATE = ROOT / "wizard" / "template.sh"
METADATA = ROOT / "wizard" / "agents" / "openai.yaml"


class WizardSkillTests(unittest.TestCase):
    def test_skill_is_explicit_human_run_and_never_executes_the_wizard(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        prose = " ".join(text.split())

        self.assertRegex(text, r"(?m)^name: wizard$")
        self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
        self.assertIn("Owns: authoring human-run setup wizards", text)
        self.assertIn("Never run the generated wizard", prose)
        self.assertIn("The human runs it explicitly", prose)

    def test_progress_uses_stage_counts_without_duration_estimates(self) -> None:
        skill = SKILL.read_text(encoding="utf-8").lower()
        template = TEMPLATE.read_text(encoding="utf-8").lower()

        self.assertIn("deterministic stage counts", skill)
        self.assertIn("stage %s/%s", template)
        for text in (skill, template):
            self.assertNotRegex(text, r"\beta\b")
            for forbidden in ("minutes remaining", "hours remaining", "time estimate"):
                self.assertNotIn(forbidden, text)

    def test_template_hides_secret_input_and_has_idempotent_env_upsert(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("read -rs", text)
        self.assertIn("ask_secret", text)
        self.assertIn("write_env", text)
        self.assertIn("mktemp", text)
        self.assertIn('mv "$tmp" "$ENV_FILE"', text)
        self.assertIn("Idempotent", text)

    def test_url_opening_is_cross_platform_and_requires_human_opt_in(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8")

        for opener in ("wslview", "explorer.exe", "xdg-open", "open"):
            self.assertIn(opener, text)
        self.assertIn('WIZARD_ALLOW_BROWSER:-0', text)
        self.assertIn("browser opening not authorized", text)

    def test_fixture_mode_blocks_browser_and_provider_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            fake_bin = directory / "bin"
            fake_bin.mkdir()
            sentinel = directory / "external-effects.log"
            env_file = directory / ".env"
            for command in ("gh", "wslview", "explorer.exe", "xdg-open", "open"):
                executable = fake_bin / command
                executable.write_text(
                    '#!/bin/sh\nprintf "%s\\n" "$0" >> "$WIZARD_EFFECT_SENTINEL"\nexit 97\n',
                    encoding="utf-8",
                )
                executable.chmod(0o755)

            secret = "fixture-" + uuid.uuid4().hex
            environment = dict(os.environ)
            environment.update(
                {
                    "PATH": f"{fake_bin}:{environment['PATH']}",
                    "ENV_FILE": str(env_file),
                    "WIZARD_EFFECT_SENTINEL": str(sentinel),
                    "WIZARD_FIXTURE_MODE": "1",
                    "WIZARD_ALLOW_BROWSER": "1",
                    "WIZARD_ALLOW_PROVIDER": "1",
                }
            )
            fixture_input = f"\nexample-label\n{secret}\n"

            first = subprocess.run(
                ["bash", str(TEMPLATE)],
                cwd=directory,
                env=environment,
                input=fixture_input,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, first.returncode, first.stderr)
            first_env = env_file.read_bytes()
            second = subprocess.run(
                ["bash", str(TEMPLATE)],
                cwd=directory,
                env=environment,
                input=fixture_input,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual(first_env, env_file.read_bytes())
            self.assertEqual("WIZARD_EXAMPLE_LABEL=example-label\n", env_file.read_text())
            self.assertFalse(sentinel.exists())
            for artifact in (first.stdout, first.stderr, second.stdout, second.stderr, env_file.read_text()):
                self.assertNotIn(secret, artifact)
            self.assertIn("Stage 1/2", first.stdout)
            self.assertIn("Stage 2/2", first.stdout)
            self.assertIn("fixture mode: browser disabled", first.stdout)
            self.assertIn("fixture mode: provider disabled", first.stdout)

    def test_template_has_valid_bash_and_shellcheck_when_available(self) -> None:
        syntax = subprocess.run(
            ["bash", "-n", str(TEMPLATE)], capture_output=True, text=True, check=False
        )
        self.assertEqual(0, syntax.returncode, syntax.stderr)

        shellcheck = shutil.which("shellcheck")
        if shellcheck is not None:
            checked = subprocess.run(
                [shellcheck, str(TEMPLATE)], capture_output=True, text=True, check=False
            )
            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)

    def test_metadata_is_explicit_and_names_human_run_boundary(self) -> None:
        metadata = METADATA.read_text(encoding="utf-8")

        self.assertIn('display_name: "Wizard"', metadata)
        self.assertIn("Author a human-run staged setup wizard", metadata)
        self.assertRegex(metadata, r"(?m)^\s*allow_implicit_invocation: false$")
        self.assertIn("do not execute it", metadata)


if __name__ == "__main__":
    unittest.main()
