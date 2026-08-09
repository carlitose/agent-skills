from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "to-questionnaire" / "SKILL.md"
METADATA = ROOT / "to-questionnaire" / "agents" / "openai.yaml"


def normalized_skill_text() -> str:
    return " ".join(SKILL.read_text(encoding="utf-8").split())


class ToQuestionnaireSkillTests(unittest.TestCase):
    def test_skill_is_explicit_and_owns_drafting_only(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        prose = normalized_skill_text()

        self.assertRegex(text, r"(?m)^name: to-questionnaire$")
        self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
        self.assertIn("Owns: asynchronous decision questionnaire drafting", text)
        self.assertIn("Grill the send, not the subject", text)
        self.assertIn("Do not run a live subject interview", prose)
        self.assertIn("does not replace `grilling`", prose)

    def test_destination_is_explicit_and_missing_destination_fails_closed(self) -> None:
        text = normalized_skill_text()

        self.assertIn("intended recipient", text)
        self.assertIn("intended destination", text)
        self.assertIn("Never infer or select a recipient", text)
        self.assertIn("If either is absent, do not write the questionnaire", text)
        self.assertIn("ask one bounded clarification", text)

    def test_template_covers_owner_context_questions_and_response_criteria(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        for marker in (
            "Status: Draft — not sent",
            "**Decision owner:**",
            "**Intended recipient:**",
            "**Intended destination:**",
            "## Purpose and decision needed",
            "## Context",
            "## Response criteria",
            "## Questions",
            "## Anything else?",
        ):
            self.assertIn(marker, text)
        self.assertIn("most important first", text)
        self.assertIn("one decision or fact per question", text)
        self.assertIn("answer stub", text)

    def test_sensitive_context_is_minimized_and_redacted_before_render(self) -> None:
        text = normalized_skill_text()

        self.assertLess(text.index("Minimize and redact context"), text.index("Render the draft"))
        self.assertIn("`<REDACTED>`", text)
        self.assertIn("credentials, tokens, cookies, personal data", text)
        self.assertIn("minimum context the recipient needs", text)
        self.assertIn("Do not include conversation transcripts", text)

    def test_no_send_boundary_forbids_connectors_and_provider_calls(self) -> None:
        text = normalized_skill_text()

        self.assertIn("Never send, post, email, upload, or publish", text)
        self.assertIn("Do not call a connector, provider, messaging tool, or mail client", text)
        self.assertIn("Return only the draft path", text)
        self.assertIn("Sending requires a separate explicit user action", text)

    def test_metadata_and_fake_recipient_example_preserve_no_send_boundary(self) -> None:
        metadata = METADATA.read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")

        self.assertIn('display_name: "To Questionnaire"', metadata)
        self.assertIn("Draft a decision questionnaire without sending", metadata)
        self.assertRegex(metadata, r"(?m)^\s*allow_implicit_invocation: false$")
        self.assertIn("Example Recipient", skill)
        self.assertIn("example.invalid", skill)
        self.assertIn("draft remains local", skill)


if __name__ == "__main__":
    unittest.main()
