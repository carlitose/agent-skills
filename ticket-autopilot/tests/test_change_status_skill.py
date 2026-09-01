from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "change-status-ticket" / "SKILL.md"
ROUTER = REPO_ROOT / "ask-skills" / "SKILL.md"
POLICY = REPO_ROOT / "extensions" / "mandatory-agent-skills.ts"


class ChangeStatusSkillTests(unittest.TestCase):
    def test_public_skill_has_narrow_model_trigger_and_exact_inputs(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertRegex(text, r'(?s)^---\nname: "change-status-ticket"\n')
        description = re.search(r'^description: "([^"]+)"$', text, re.MULTILINE)
        self.assertIsNotNone(description)
        for trigger in ("hold", "cancel", "reopen", "disposition"):
            self.assertIn(trigger, description.group(1))
        for negative in (
            "implementing",
            "completing",
            "pausing",
            "blocking",
            "stopping",
            "waiting",
            "inspecting",
        ):
            self.assertIn(negative, description.group(1))
        self.assertNotIn("disable-model-invocation", text)
        for field in (
            "repository_identity",
            "actor",
            "reason",
            "authority_ref",
            "reopen_gate_id",
            "ticket digest",
            "Artifact ID",
            "source mode",
        ):
            self.assertIn(field, text)

    def test_skill_delegates_once_to_repository_transaction_and_not_quality_stages(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        command = text.split("```bash", 1)[1].split("```", 1)[0]
        self.assertEqual(command.count("status-change-transaction"), 1)
        for option in (
            "--repo",
            "--ticket-id",
            "--artifact-id",
            "--ticket-digest",
            "--from-disposition",
            "--to-disposition",
            "--source-mode",
            "--actor",
            "--reason",
            "--authority-ref",
            "--base",
        ):
            self.assertIn(option, command)
        self.assertIn('append `--reopen-gate-id "$REOPEN_GATE_ID"`', text)
        self.assertIn("Do not invoke\n`execute-ticket`", text)
        self.assertIn("completed-success replay returns `already-applied`", text)
        self.assertIn("gated replay returns the\nsame named gate", text)
        self.assertNotIn("qa-plan", command)
        self.assertNotIn("verification", command)

    def test_terminal_report_keeps_axes_results_and_non_authorities_separate(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        report = text.split("```text", 1)[1].split("```", 1)[0]
        for field in (
            "result:",
            "transaction_id:",
            "transaction_phase:",
            "disposition:",
            "execution_lifecycle:",
            "readiness:",
            "stop_reason:",
            "provider_state:",
            "merge_authority:",
            "terminal_proof:",
            "run_projection:",
            "gate:",
            "non_authorities:",
        ):
            self.assertIn(field, report)
        for result in (
            "changed-integrated",
            "external-unpublished",
            "already-applied",
            "gated",
            "rejected",
        ):
            self.assertIn(result, report)
        self.assertIn("/reload", text)

    def test_router_precedence_and_negatives_are_explicit(self) -> None:
        text = ROUTER.read_text(encoding="utf-8")
        status_route = text.index("Explicit request to hold, cancel, reopen")
        delivery_route = text.index("Loose feature, decision")
        self.assertLess(status_route, delivery_route)
        for negative in (
            "Bare ticket paths",
            "implement",
            "complete",
            "Blocked",
            "pause/unpause",
            "stop",
            "waiting",
            "gated",
            "readiness",
            "lifecycle questions",
        ):
            self.assertIn(negative, text)
        self.assertIn("generic docs-only or small-change bypass", text)

    def test_package_policy_names_only_the_lifecycle_lane(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        self.assertIn('"change-status-ticket"', text)
        self.assertIn("sole lifecycle-only exception", text)
        self.assertNotRegex(text, r"generic (?:docs-only|small-change) exception")


if __name__ == "__main__":
    unittest.main()
