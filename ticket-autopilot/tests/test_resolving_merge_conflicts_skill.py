from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "resolving-merge-conflicts" / "SKILL.md"
METADATA = ROOT / "resolving-merge-conflicts" / "agents" / "openai.yaml"


def run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
    )


def snapshot(repo: Path) -> tuple[str, str, str, str, str]:
    return (
        run(repo, "rev-parse", "HEAD").stdout,
        run(repo, "show-ref", "--head").stdout,
        run(repo, "status", "--porcelain=v2").stdout,
        run(repo, "ls-files", "--stage").stdout,
        hashlib.sha256((repo / "settings.txt").read_bytes()).hexdigest(),
    )


def conflicted_repo(*, compatible: bool) -> tempfile.TemporaryDirectory[str]:
    directory = tempfile.TemporaryDirectory()
    repo = Path(directory.name)
    run(repo, "init", "-q", "-b", "main")
    run(repo, "config", "user.name", "Fixture User")
    run(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "settings.txt").write_text("items=base\n", encoding="utf-8")
    run(repo, "add", "settings.txt")
    run(repo, "commit", "-qm", "base intent")
    run(repo, "branch", "side")

    ours = "items=base,alpha\n" if compatible else "mode=safe\n"
    theirs = "items=base,beta\n" if compatible else "mode=fast\n"
    (repo / "settings.txt").write_text(ours, encoding="utf-8")
    run(repo, "commit", "-qam", "ours intent")
    run(repo, "switch", "-q", "side")
    (repo / "settings.txt").write_text(theirs, encoding="utf-8")
    run(repo, "commit", "-qam", "theirs intent")
    run(repo, "switch", "-q", "main")
    merged = run(repo, "merge", "side", check=False)
    if merged.returncode == 0:
        directory.cleanup()
        raise AssertionError("fixture did not create a conflict")
    return directory


class ResolvingMergeConflictsSkillTests(unittest.TestCase):
    def test_skill_is_explicit_and_owns_only_intent_based_resolution(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertRegex(text, r"(?m)^name: resolving-merge-conflicts$")
        self.assertRegex(text, r"(?m)^disable-model-invocation: true$")
        self.assertIn("Owns: intent-based merge-conflict resolution", text)
        self.assertIn("Do not start from a clean repository", text)

    def test_each_hunk_records_both_intents_and_verifies_combined_behavior(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        for marker in (
            "Conflict path and hunk",
            "Intent A",
            "Intent B",
            "Evidence for each intent",
            "Compatibility decision",
            "Chosen combined behavior",
            "Validation command and observed result",
        ):
            self.assertIn(marker, text)
        self.assertIn("Do not invent new behavior", text)
        self.assertIn("verify the combined behavior", text)

    def test_compatible_fixture_preserves_both_sides_during_read_only_discovery(self) -> None:
        directory = conflicted_repo(compatible=True)
        self.addCleanup(directory.cleanup)
        repo = Path(directory.name)
        before = snapshot(repo)

        unmerged = run(repo, "ls-files", "-u").stdout
        combined = run(repo, "diff", "--cc", "--", "settings.txt").stdout
        ours = run(repo, "show", ":2:settings.txt").stdout
        theirs = run(repo, "show", ":3:settings.txt").stdout

        self.assertIn("alpha", ours)
        self.assertIn("beta", theirs)
        self.assertIn("settings.txt", unmerged)
        self.assertIn("settings.txt", combined)
        self.assertEqual(before, snapshot(repo))

    def test_authorized_compatible_edit_preserves_both_intents_without_staging(self) -> None:
        directory = conflicted_repo(compatible=True)
        self.addCleanup(directory.cleanup)
        repo = Path(directory.name)
        head_before = run(repo, "rev-parse", "HEAD").stdout
        refs_before = run(repo, "show-ref", "--head").stdout
        index_before = run(repo, "ls-files", "--stage").stdout

        (repo / "settings.txt").write_text("items=base,alpha,beta\n", encoding="utf-8")
        values = (repo / "settings.txt").read_text(encoding="utf-8").strip().split("=", 1)[1]

        self.assertEqual({"base", "alpha", "beta"}, set(values.split(",")))
        self.assertEqual(head_before, run(repo, "rev-parse", "HEAD").stdout)
        self.assertEqual(refs_before, run(repo, "show-ref", "--head").stdout)
        self.assertEqual(index_before, run(repo, "ls-files", "--stage").stdout)
        self.assertIn("settings.txt", run(repo, "ls-files", "-u").stdout)

    def test_incompatible_fixture_gates_without_mutation(self) -> None:
        directory = conflicted_repo(compatible=False)
        self.addCleanup(directory.cleanup)
        repo = Path(directory.name)
        before = snapshot(repo)

        ours = run(repo, "show", ":2:settings.txt").stdout
        theirs = run(repo, "show", ":3:settings.txt").stdout
        text = " ".join(SKILL.read_text(encoding="utf-8").split())

        self.assertNotEqual(ours, theirs)
        self.assertIn("incompatible or insufficiently evidenced", text)
        self.assertIn("stop without modifying the conflict", text)
        self.assertEqual(before, snapshot(repo))

    def test_unauthorized_operations_leave_conflict_refs_index_and_worktree_unchanged(self) -> None:
        directory = conflicted_repo(compatible=True)
        self.addCleanup(directory.cleanup)
        repo = Path(directory.name)
        before = snapshot(repo)
        text = " ".join(SKILL.read_text(encoding="utf-8").split())

        for command in (
            "`git add`",
            "`git commit`",
            "`git merge --abort`",
            "`git rebase --continue`",
        ):
            self.assertIn(command, text)
        self.assertIn("explicit caller authority", text)
        self.assertIn("scheduler-owned worktree", text)
        self.assertIn("do not modify it", text)
        self.assertEqual(before, snapshot(repo))

    def test_authority_is_operation_scoped_and_ambiguous_scope_fails_closed(self) -> None:
        text = " ".join(SKILL.read_text(encoding="utf-8").split())

        self.assertIn("Authority is operation-scoped", text)
        self.assertIn("does not authorize staging, committing, aborting, or continuing", text)
        self.assertIn("If authority or scope is ambiguous, stop and ask", text)
        self.assertIn("Never push", text)

    def test_metadata_is_explicit_and_does_not_claim_automatic_completion(self) -> None:
        metadata = METADATA.read_text(encoding="utf-8")

        self.assertIn('display_name: "Resolve Merge Conflicts"', metadata)
        self.assertIn("Trace both intents and resolve only with scoped authority", metadata)
        self.assertRegex(metadata, r"(?m)^\s*allow_implicit_invocation: false$")
        self.assertNotIn("automatically", metadata.lower())


if __name__ == "__main__":
    unittest.main()
