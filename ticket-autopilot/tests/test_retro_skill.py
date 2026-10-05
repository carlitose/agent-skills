from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "retro" / "SKILL.md"
METADATA = ROOT / "retro" / "agents" / "openai.yaml"
DIGEST = ROOT / "retro" / "scripts" / "session_digest.py"


def prose() -> str:
    return " ".join(SKILL.read_text(encoding="utf-8").split())


def assistant(cost: float, *calls: tuple[str, str, dict]) -> dict:
    content = [
        {"type": "toolCall", "id": call_id, "name": name, "arguments": args}
        for call_id, name, args in calls
    ]
    return {
        "type": "message",
        "message": {"role": "assistant", "content": content, "usage": {"cost": {"total": cost}}},
    }


def result(call_id: str, name: str, text: str, error: bool = False) -> dict:
    return {
        "type": "message",
        "message": {
            "role": "toolResult",
            "toolCallId": call_id,
            "toolName": name,
            "isError": error,
            "content": [{"type": "text", "text": text}],
        },
    }


class RetroSkillTests(unittest.TestCase):
    def test_skill_is_user_invoked_read_only_and_redacting(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        body = prose()

        self.assertRegex(text, r"(?m)^name: retro$")
        self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
        self.assertRegex(text, r"(?m)^argument-hint:")
        self.assertIn("Owns: session retrospective suggestions", text)
        self.assertIn("Read-only", body)
        self.assertIn("never edits steering files, settings, or code", body)
        self.assertIn("`<REDACTED>`", body)
        self.assertIn("no subagents", body)
        self.assertIn("PI_SESSION_FILE", body)
        self.assertIn("deterministic check", body)

    def test_skill_names_categories_and_ranked_output(self) -> None:
        body = prose()

        for category in (
            "Navigation",
            "Automated checks",
            "Coding standards",
            "Steering files",
            "Tool economy",
            "Information access",
        ):
            self.assertIn(f"**{category}**", body)
        self.assertIn("read the repository's own check commands and CI", body)
        self.assertIn("no guardrail", body)
        for field in ("Severity", "Evidence", "Proposed change"):
            self.assertIn(field, body)

    def test_metadata_matches_user_invoked_policy(self) -> None:
        metadata = METADATA.read_text(encoding="utf-8")

        self.assertIn('display_name: "Session Retro"', metadata)
        self.assertIn("allow_implicit_invocation: false", metadata)

    def test_digest_summarizes_cost_errors_repeats_and_redacts(self) -> None:
        secret = "sk-" + "a1B2" * 8
        events = [
            {"type": "session", "id": "s"},
            assistant(0.30, ("c1", "bash", {"command": f"curl -H 'Authorization: Bearer {secret}' x"})),
            result("c1", "bash", "boom: failed", error=True),
            assistant(0.05, ("c2", "read", {"path": "a.md"}), ("c3", "read", {"path": "a.md"})),
            result("c2", "read", "x" * 500),
            result("c3", "read", "x" * 500),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "session.jsonl"
            log.write_bytes(
                "".join(json.dumps(event) + "\n" for event in events).encode("utf-8")
            )
            completed = subprocess.run(
                [sys.executable, "-B", str(DIGEST), str(log)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertNotIn(secret, completed.stdout)
        self.assertIn("<REDACTED>", completed.stdout)
        digest = json.loads(completed.stdout)
        self.assertEqual(2, digest["assistant_turns"])
        self.assertEqual(3, digest["tool_calls"])
        self.assertEqual(1, digest["single_call_turns"])
        self.assertAlmostEqual(0.35, digest["total_cost"])
        self.assertEqual({"bash": 1, "read": 2}, digest["calls_by_tool"])
        self.assertEqual("bash", digest["errors"][0]["tool"])
        self.assertEqual(0.30, digest["costliest_turns"][0]["cost"])
        self.assertEqual(2, digest["repeated_calls"][0]["count"])
        self.assertEqual("read", digest["largest_results"][0]["tool"])

    def test_digest_without_a_log_fails_closed(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(DIGEST), str(ROOT / "missing.jsonl")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertEqual("", completed.stdout)


if __name__ == "__main__":
    unittest.main()
