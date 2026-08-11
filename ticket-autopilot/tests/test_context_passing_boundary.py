from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOFF = REPO_ROOT / "handoff" / "SKILL.md"
AUTOPILOT = REPO_ROOT / "ticket-autopilot" / "SKILL.md"

# The word "handoff" also names the schema-3 payload a leaf returns, which is a different
# thing from the `handoff` skill. Only a backticked token or a link to the skill file
# counts as a reference to the skill.
SKILL_REFERENCE = re.compile(r"`handoff`|handoff/SKILL\.md")
LEAF_CONTEXT = re.compile(r"\bleaf\b|\bsubagent\b|\bworker\b", re.IGNORECASE)
PROHIBITIVE = re.compile(r"\bnot\b|\bnever\b|\bno such\b", re.IGNORECASE)


def skill_files() -> list[Path]:
    return sorted(REPO_ROOT.glob("*/SKILL.md"))


def sentences(text: str) -> list[str]:
    """Split on sentence ends, so a prohibition is judged on its own clause."""

    flat = " ".join(line.strip() for line in text.splitlines())
    return [part.strip() for part in re.split(r"(?<=[.;])\s+", flat) if part.strip()]


class ContextPassingBoundaryTests(unittest.TestCase):
    def test_handoff_denies_being_the_leaf_context_channel(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")
        claim = [
            sentence
            for sentence in sentences(text)
            if LEAF_CONTEXT.search(sentence) and PROHIBITIVE.search(sentence)
        ]
        self.assertTrue(
            claim,
            "handoff/SKILL.md does not deny being the leaf or subagent context channel",
        )
        self.assertTrue(
            any("leaf-result" in sentence for sentence in claim),
            "handoff/SKILL.md denies the role without naming leaf-result as the owner",
        )

    def test_autopilot_names_the_owning_channel(self) -> None:
        text = AUTOPILOT.read_text(encoding="utf-8")
        owning = [
            sentence
            for sentence in sentences(text)
            if "leaf-result" in sentence and "only channel" in sentence
        ]
        self.assertTrue(
            owning,
            "ticket-autopilot/SKILL.md does not name leaf-result as the only leaf "
            "context channel",
        )

    def scanned_sentences(self) -> list[tuple[str, str]]:
        return [
            (skill.parent.name, sentence)
            for skill in skill_files()
            for sentence in sentences(skill.read_text(encoding="utf-8"))
            if SKILL_REFERENCE.search(sentence) and LEAF_CONTEXT.search(sentence)
        ]

    def test_no_skill_routes_leaf_context_through_handoff(self) -> None:
        for name, sentence in self.scanned_sentences():
            with self.subTest(skill=name, sentence=sentence[:60]):
                self.assertTrue(
                    PROHIBITIVE.search(sentence),
                    f"{name} mentions the handoff skill and leaf context together "
                    f"without prohibiting it: {sentence!r}",
                )

    def test_the_scan_is_not_vacuous(self) -> None:
        """A broken pattern would make the scan above pass by matching nothing."""

        scanned = self.scanned_sentences()
        self.assertTrue(
            scanned,
            "no sentence pairs the handoff skill with leaf context, so the scan proves "
            "nothing; the patterns or the boundary text have drifted",
        )
        self.assertIn(
            "ticket-autopilot",
            {name for name, _ in scanned},
            "the autopilot prohibition sentence is no longer detected by the scan",
        )

    def test_handoff_storage_boundary_is_unchanged(self) -> None:
        """This ticket must not touch storage, redaction, or expiry behaviour."""

        text = HANDOFF.read_text(encoding="utf-8")
        self.assertIn("operating-system temporary", text)
        self.assertRegex(text, r"never write the handoff into the project workspace")


if __name__ == "__main__":
    unittest.main()
