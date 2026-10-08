from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "crew-delivery" / "SKILL.md"
METADATA = ROOT / "crew-delivery" / "agents" / "openai.yaml"


class CrewDeliverySkillTests(unittest.TestCase):
    """DBH-40: a Crew works like a human team (PM, developers, reviewer, merge queue, cycle QA);
    the causes measured in lot dbh-crew each have a rule, and the lane stays skills-only."""

    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")

    def assert_rules(self, *rules: str) -> None:
        for rule in rules:
            with self.subTest(rule=rule):
                self.assertIn(rule, self.text)

    def test_skill_is_routed_and_never_creates_delegation(self) -> None:
        self.assertRegex(self.text, r"(?m)^name: crew-delivery$")
        self.assert_rules(
            "Owns: multi-agent coordination on one repository",
            "never creates delegation",
            "no ticket-autopilot runner, scheduler or\ndriver",
        )
        router = (ROOT / "ask-skills" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`crew-delivery`; it never creates delegation", router)
        self.assertIn("allow_implicit_invocation: true", METADATA.read_text(encoding="utf-8"))

    def test_each_role_has_its_skills(self) -> None:
        self.assert_rules(
            "| PM | spec, tickets, assignment, merge queue; writes no product code | `to-spec`, `to-tickets` |",
            "| Developer | one ticket at a time, code and tests | `execute-ticket` |",
            "| Reviewer | review of each branch; cycle QA | `code-review`, `qa-test-plan` | read-only |",
        )

    def test_nobody_writes_main_except_the_fast_forward_queue(self) -> None:
        self.assert_rules(
            "Nobody writes in the main folder",
            "`pre-commit` hook that refuses commits while the\ncurrent branch is `main`",
            "git worktree add -b crew/<ticket-id> ../<repo-folder>-worktrees/<ticket-id> main",
            "`git rebase --abort`, the ticket goes back to its developer",
            "git -C <main-folder> merge --ff-only crew/<ticket-id>",
        )

    def test_review_is_separate_and_never_edits(self) -> None:
        self.assert_rules(
            "skip its\n   review stage: the reviewer owns it",
            "from a\n   context separate from the developer's",
            "the reviewer never edits",
        )

    def test_whole_tickets_blocks_and_cycle_qa(self) -> None:
        self.assert_rules(
            "Two tickets in flight never touch the same\n   files",
            "at most two tickets per\n   developer per request",
            "never make an agent wait for an acknowledgement",
            "do not retry with smaller pieces",
            "the PM does not finish it",
            "each changes-requested verdict
   counts as a block",
            "A second block on the same ticket stops the request",
            "the reviewer runs `qa-test-plan` and the full tests\non main",
            "The\nrequest is done only when QA passes on main",
        )


if __name__ == "__main__":
    unittest.main()
