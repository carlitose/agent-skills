from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "ticket-autopilot" / "SKILL.md"
REFERENCES = SKILL.parent / "references"
BRANCHES = {
    "bootstrap.md": ("prepare-zero-to-autopilot", "bootstrap-private-github"),
    "worktrees.md": ("worktree-owner-adopt", "worktree-gc-apply"),
    "local-pi-sync.md": ("sync-local-pi", "--migrate-owned-source-from"),
    "merge-and-reconciliation.md": (
        "grant-autonomous-merge", "grant-repository-autonomous-reconciliation",
        "migrate-repository-authority",
    ),
    "final-tree-projection.md": ("--final-tree-mode", "grant-completion-projection"),
    "wiki-delivery.md": ("wiki-delivery-retry-status", "retry-wiki-delivery"),
    "runner-defect-issues.md": ("runner-defect-issue-grant", "runner-defect-issue-escalate"),
    "legacy-recovery.md": ("prepare-legacy-recovery", "apply-legacy-recovery"),
}


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ProgressiveReferencesTests(unittest.TestCase):
    def test_each_branch_has_a_trigger_and_one_shared_operator_owner(self) -> None:
        skill, readme = text(SKILL), text(ROOT / "README.md")
        for filename, commands in BRANCHES.items():
            with self.subTest(branch=filename):
                pointer = f"references/{filename}"
                rows = [line for line in skill.splitlines() if f"]({pointer})" in line]
                self.assertEqual(1, len(rows), f"one retrieval trigger for {filename}")
                self.assertIn("When ", rows[0])
                self.assertIn(f"ticket-autopilot/{pointer}", readme)
                owner = REFERENCES / filename
                self.assertTrue(owner.is_file(), filename)
                for command in commands:
                    self.assertIn(command, text(owner))

    def test_ordinary_work_keeps_its_decisions_without_loading_rare_commands(self) -> None:
        skill = text(SKILL)
        for required in (
            "OPERATING-DEFAULTS.md", "Default ticket execution composes serially inline",
            "CandidateRef", "leaf-result", "reason", "open_gate_records",
            "review", "qa-plan", "qa-execute", "verify", "finalize",
            "source artifact reference", "Never invent credentials", "repository-autonomous-merge-status",
            "merge-all", "render-required", "sync-local-pi",
        ):
            with self.subTest(required=required):
                self.assertIn(required, skill)
        for uncommon in (
            "--inventory-sha256", "--replace-drifted-owned",
            "--expected-ledger-sha256", "--expected-record-sha256",
            "--migrate-owned-source-from",
        ):
            with self.subTest(uncommon=uncommon):
                self.assertTrue(uncommon not in skill, f"rare detail still inline: {uncommon}")

    def test_disclosed_markdown_links_resolve_from_their_new_directory(self) -> None:
        for filename in BRANCHES:
            path = REFERENCES / filename
            self.assertTrue(path.is_file(), filename)
            for target in re.findall(r"\]\(([^\s)]+)\)", text(path)):
                if "://" in target or target.startswith("#"):
                    continue
                target = target.split("#", 1)[0]
                with self.subTest(source=filename, target=target):
                    self.assertTrue((path.parent / target).is_file())

    def test_branch_guards_remain_explicit(self) -> None:
        guards = {
            "bootstrap.md": ("separate actor/evidence", "no run", "private"),
            "worktrees.md": ("Eligibility is not cleanup authority", "without `--force`"),
            "local-pi-sync.md": ("durably integrated", "`/reload`", "unrelated future sync"),
            "merge-and-reconciliation.md": (
                "revoked, legacy, malformed, or contradictory", "Run-local grants are never overwritten",
                "force normal fresh CandidateRef", "no direct fallback",
            ),
            "final-tree-projection.md": ("projected-not-integrated", "no-extra-row proof", "descendants never inherit"),
            "wiki-delivery.md": ("no inherited verification", "only on Windows", "prior provider state"),
            "runner-defect-issues.md": ("separate", "dispatch-ambiguous", "Never delete one"),
            "legacy-recovery.md": ("without", "schema 1/2", "cannot reactivate"),
        }
        for filename, expected in guards.items():
            path = REFERENCES / filename
            self.assertTrue(path.is_file(), filename)
            content = " ".join(text(path).split())
            for phrase in expected:
                with self.subTest(branch=filename, guard=phrase):
                    self.assertIn(phrase, content)


if __name__ == "__main__":
    unittest.main()
