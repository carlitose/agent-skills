from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "crew-delivery" / "SKILL.md"
METADATA = ROOT / "crew-delivery" / "agents" / "openai.yaml"


class CrewDeliverySkillTests(unittest.TestCase):
    """DBH-40: the causes measured in lot dbh-crew (overlap, a colleague's red suite, tiny tasks,
    acknowledgement waits) each have a rule, and the lane stays skills-only."""

    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")

    def test_skill_is_routed_and_never_creates_delegation(self) -> None:
        self.assertRegex(self.text, r"(?m)^name: crew-delivery$")
        self.assertIn("Owns: multi-agent coordination on one repository", self.text)
        self.assertIn("never creates delegation", self.text)
        self.assertIn("no ticket-autopilot runner, scheduler or\ndriver", self.text)
        router = (ROOT / "ask-skills" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`crew-delivery`; it never creates delegation", router)
        self.assertIn("allow_implicit_invocation: true", METADATA.read_text(encoding="utf-8"))

    def test_each_worker_has_its_own_worktree_outside_the_repository(self) -> None:
        self.assertIn("git worktree add -b crew/<ticket-id> ../<repo-folder>-worktrees/<ticket-id> main", self.text)
        self.assertIn("Never write in the main folder or in another worker's worktree", self.text)
        self.assertIn("Do not merge into `main`", self.text)

    def test_tasks_are_whole_tickets_carried_by_execute_ticket(self) -> None:
        for rule in ("`to-spec` and `to-tickets`", "at most two tickets per worker per request",
                     "never touch the same files", "with `execute-ticket` inline (skills-only)"):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.text)

    def test_the_coordinator_integrates_tests_and_takes_over_blocked_work(self) -> None:
        for rule in ("run the repository's tests on the integrated result",
                     "A blocked task is not split again", "finish that ticket yourself",
                     "never make a worker\n   wait for an acknowledgement",
                     "A worker's \"done\", green tests in a worktree, or a ticket\n   file are not the result"):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.text)


if __name__ == "__main__":
    unittest.main()
