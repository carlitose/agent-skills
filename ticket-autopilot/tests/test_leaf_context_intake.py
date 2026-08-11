from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = {
    "code-simplification": {
        "max_volatile_bytes": 103232,
        "max_single_output_bytes": 32596,
        "derivation": 96393 + 2380 + 4459,
        "duties": (
            "externally observable behavior and public contracts",
            "Never claim equivalence or passing checks without observed evidence.",
        ),
    },
    "code-review": {
        "max_volatile_bytes": 107656,
        "max_single_output_bytes": 32596,
        "derivation": 96393 + 2380 + 4459 + 4424,
        "duties": (
            "A complete review must reach `handoff-ready`, inspect the declared scope",
            "Review each axis separately and report only evidence-backed findings",
        ),
    },
    "qa-test-plan": {
        "max_volatile_bytes": 103998,
        "max_single_output_bytes": 32596,
        "derivation": 96393 + 2380 + 5225,
        "duties": (
            "For each changed behavior:",
            "Do not label a mocked provider or fake browser as live.",
        ),
    },
    "verification-audit": {
        "max_volatile_bytes": 12017,
        "max_single_output_bytes": 12017,
        "derivation": 12017,
        "duties": (
            "Confirm evidence crosses the changed causal mechanism",
            "The declared implementation status, maximum claim,",
        ),
    },
}


def declared_bound(text: str, field: str) -> int:
    match = re.search(rf"`{re.escape(field)}`: `(\d+)`", text)
    if match is None:
        raise AssertionError(f"missing {field}")
    return int(match.group(1))


class LeafContextIntakeTests(unittest.TestCase):
    def test_each_leaf_declares_observation_derived_bounds(self) -> None:
        for name, expected in SKILLS.items():
            with self.subTest(skill=name):
                text = (ROOT / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertEqual(
                    expected["derivation"], expected["max_volatile_bytes"]
                )
                self.assertEqual(
                    expected["max_volatile_bytes"],
                    declared_bound(text, "max_volatile_bytes"),
                )
                self.assertEqual(
                    expected["max_single_output_bytes"],
                    declared_bound(text, "max_single_output_bytes"),
                )
                self.assertIn("observed", text)
                if name == "verification-audit":
                    self.assertIn("compact TK-01 and TK-02 checkpoint events", text)
                else:
                    self.assertIn("git diff --no-ext-diff --no-color", text)
                    for ticket_id in (
                        "TK-01",
                        "TK-02",
                        "TK-05",
                        "TK-07",
                        "TK-08",
                    ):
                        self.assertIn(ticket_id, text)

    def test_prompt_contract_honours_the_bound_fail_closed(self) -> None:
        required = (
            "normalized UTF-8 bytes",
            "truncate command output before it enters context",
            "path plus SHA-256 references over pasted artifacts",
            "budget-exhausted",
        )
        for name in SKILLS:
            with self.subTest(skill=name):
                text = (ROOT / name / "SKILL.md").read_text(encoding="utf-8")
                normalized = " ".join(text.split())
                for phrase in required:
                    self.assertIn(phrase, normalized)
                self.assertRegex(
                    normalized, r"(?i)(remaining references|remaining scope)"
                )

    def test_verification_duties_remain_literal(self) -> None:
        for name, expected in SKILLS.items():
            with self.subTest(skill=name):
                text = (ROOT / name / "SKILL.md").read_text(encoding="utf-8")
                for duty in expected["duties"]:
                    self.assertIn(duty, text)

    def test_execute_ticket_composes_limits_without_weakening_scope(self) -> None:
        text = (ROOT / "execute-ticket" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("enforce each leaf's declared normalized-byte intake", text)
        self.assertIn("continue a `budget-exhausted` partial result", text)
        self.assertIn("without dropping remaining scope", text)


if __name__ == "__main__":
    unittest.main()
