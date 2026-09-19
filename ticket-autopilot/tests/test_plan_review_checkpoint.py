"""The plan-review checkpoint must stay nameable, complete and non-authoritative.

This is a structural check: it proves the rule is written and says what it must say. It cannot
prove an agent obeys it, and nothing here claims otherwise. What it does prevent is the failure
that produced the rule — a plan that survives a compaction with its text intact and its reasons
gone, and then quietly loses the thread.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "ask-skills" / "SKILL.md"
REFERENCE = ROOT / "ask-skills" / "PLAN-REVIEW-CHECKPOINT.md"
SPEC = ROOT / "docs" / "specs" / "plan-review-checkpoint.md"


class PlanReviewCheckpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(REFERENCE.is_file(), "the checkpoint needs its own reference file")
        self.section = REFERENCE.read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("[plan review checkpoint](PLAN-REVIEW-CHECKPOINT.md)", skill,
                      "the skill must point at the reference so it is discoverable")

    def test_the_three_triggers_are_named_and_checkable(self) -> None:
        for trigger in ("context compaction", "phase end", "blocker"):
            self.assertIn(trigger, self.section, f"missing trigger: {trigger}")
        for vague in ("when it seems", "if convenient", "periodically", "from time to time"):
            self.assertNotIn(vague, self.section.casefold(),
                             "a trigger must be an event, not a mood")

    def test_reconciliation_covers_the_whole_list_and_its_six_checks(self) -> None:
        self.assertIn("complete list", self.section)
        self.assertIn("not only the active item", self.section)
        for check in ("goal", "evidence", "omissions", "duplicates",
                      "priority and dependencies", "tree state"):
            self.assertIn(check, self.section, f"missing check: {check}")

    def test_tree_state_inventories_every_checkout_and_disposes_each_path(self) -> None:
        """Dangling work is work nobody reopened; the check must reach every checkout."""

        self.assertIn("every checkout", self.section)
        self.assertIn("git worktree list", self.section)
        self.assertIn("worktree-gc-plan", self.section)
        for disposition in ("`commit`", "`discard`", "`handoff`"):
            self.assertIn(disposition, self.section, f"missing disposition: {disposition}")
        self.assertRegex(self.section, r"(?i)exactly one disposition")
        self.assertRegex(self.section, r"(?i)later[^.]*is not a disposition")

    def test_a_half_applied_projection_is_never_discarded_without_a_patch(self) -> None:
        self.assertRegex(self.section, r"(?i)projection[^.]*not integrated[^.]*patch")

    def test_a_completed_item_must_cite_an_observation(self) -> None:
        self.assertRegex(self.section, r"(?i)completed[^.]*cite[^.]*observation")

    def test_the_checkpoint_ends_with_exactly_one_next_action(self) -> None:
        self.assertIn("exactly one next action", self.section)
        self.assertRegex(self.section, r"(?i)more than one candidate[^.]*not finished")

    def test_the_plan_is_neither_evidence_nor_authority(self) -> None:
        self.assertIn("never evidence", self.section)
        self.assertIn("never authority", self.section)
        for owned in ("runner state", "investigation frontier"):
            self.assertIn(owned, self.section,
                          f"the rule must say the plan does not rewrite the {owned}")
        self.assertRegex(self.section, r"(?i)close a gate|closes no gate|does not close")

    def test_a_missing_plan_tool_is_declared_rather_than_imagined(self) -> None:
        self.assertIn("update_plan", self.section)
        self.assertRegex(self.section, r"(?i)without it[^.]*declare|declare the substitute")

    def test_the_rule_points_at_its_spec(self) -> None:
        self.assertTrue(SPEC.is_file(), "the parent spec must live in the repository")
        self.assertRegex(
            self.section,
            r"\[[^\]]+\]\(\.\./docs/specs/plan-review-checkpoint\.md\)",
            "the reference must link its spec with a working relative path",
        )

    def test_the_section_stays_short_enough_to_be_read_every_time(self) -> None:
        words = len(re.findall(r"\S+", self.section))
        self.assertLess(words, 420, "a checkpoint nobody reads is not a checkpoint")


if __name__ == "__main__":
    unittest.main()
