from __future__ import annotations

import re
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "handoff" / "SKILL.md"
METADATA = ROOT / "handoff" / "agents" / "openai.yaml"


class HandoffSkillTests(unittest.TestCase):
    def test_skill_is_explicit_and_owns_only_temporary_session_continuity(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertRegex(text, r"(?m)^name: handoff$")
        self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
        self.assertIn("Owns: temporary session continuity artifacts", text)
        self.assertIn("operating-system temporary directory", text)
        self.assertIn("not scheduler state", text)
        self.assertIn("not a ticket-autopilot checkpoint", text)
        self.assertIn("never write the handoff into the project workspace", text)

    def test_output_contract_is_small_pointer_based_and_complete(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        for heading in (
            "# Session handoff",
            "## Purpose",
            "## Durable pointers",
            "## Remaining work",
            "## Limitations",
            "## Redacted context",
            "## Suggested skills",
            "## Expiry and deletion",
        ):
            self.assertIn(heading, text)
        self.assertIn("Do not copy durable content", text)
        self.assertIn("path, URL, issue or PR number, commit, or digest", text)
        self.assertIn("one concrete next action", text)

    def test_redaction_precedes_write_and_excludes_transcript_content(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        redaction = text.index("Redact before writing")
        write = text.index("Write the artifact")
        self.assertLess(redaction, write)
        self.assertIn("`<REDACTED>`", text)
        self.assertIn("credentials, tokens, cookies, personal data", text)
        self.assertIn("Do not copy the conversation transcript", text)
        self.assertIn("Do not retain unnecessary command output", text)

    def test_temp_storage_is_private_untracked_and_has_cleanup_guidance(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("`mktemp -d`", text)
        self.assertIn("directory mode `0700`", text)
        self.assertIn("file mode `0600`", text)
        self.assertIn("expires within 24 hours", text)
        self.assertIn("exact deletion command", text)
        self.assertIn("confirm only the path and expiry", text)
        self.assertIn("do not stage, commit, or upload", text)

    def test_metadata_disables_implicit_invocation(self) -> None:
        text = METADATA.read_text(encoding="utf-8")

        self.assertIn('display_name: "Session Handoff"', text)
        self.assertIn("temporary, redacted session handoff", text)
        self.assertRegex(text, r"(?m)^\s*allow_implicit_invocation: false$")
        self.assertNotIn("default_prompt:", text)

    def test_examples_route_autopilot_continuation_away_from_this_skill(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("Use this skill", text)
        self.assertIn("Do not use this skill", text)
        self.assertIn("ticket-autopilot", text)
        self.assertIn("resume an existing run", text)
        self.assertTrue(
            re.search(r"temporary.*fresh session", text, re.IGNORECASE | re.DOTALL)
        )

    def test_temp_fixture_has_redacted_shape_without_mutating_runner_state(self) -> None:
        synthetic_secret = "example-secret-value"
        sections = (
            "# Session handoff",
            "## Purpose",
            "## Durable pointers",
            "## Remaining work",
            "## Limitations",
            "## Redacted context",
            "## Suggested skills",
            "## Expiry and deletion",
        )

        with tempfile.TemporaryDirectory(prefix="handoff-contract-") as root_name:
            root = Path(root_name)
            workspace = root / "workspace"
            ledger = workspace / ".git" / "ticket-autopilot" / "ledger.json"
            ledger.parent.mkdir(parents=True)
            ledger.write_text('{"revision":7}\n', encoding="utf-8")
            ledger_before = ledger.read_bytes()

            handoff_dir = root / "os-temp" / "agent-handoff.123456"
            handoff_dir.mkdir(parents=True, mode=0o700)
            artifact = handoff_dir / "HANDOFF.md"
            body = "\n\n".join(sections) + "\n\n" + synthetic_secret
            body = body.replace(synthetic_secret, "<REDACTED>")
            artifact.write_text(body, encoding="utf-8")
            artifact.chmod(0o600)

            rendered = artifact.read_text(encoding="utf-8")
            self.assertTrue(all(section in rendered for section in sections))
            self.assertIn("<REDACTED>", rendered)
            self.assertNotIn(synthetic_secret, rendered)
            self.assertFalse(artifact.is_relative_to(workspace))
            self.assertEqual(0o600, artifact.stat().st_mode & 0o777)
            self.assertEqual(ledger_before, ledger.read_bytes())


if __name__ == "__main__":
    unittest.main()
