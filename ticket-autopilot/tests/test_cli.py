from __future__ import annotations

import json
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "ticket-autopilot" / "scripts" / "ticket-autopilot.py"
sys.path.insert(0, str(CLI.parent))

from autopilot.cli import main as cli_main
from autopilot.git_ops import CommandResult, candidate_files, candidate_ref
from autopilot.ledger import AtomicLedger


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, "-B", str(CLI), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        raise AssertionError(
            f"command failed ({result.returncode}): {result.stderr}\n{result.stdout}"
        )
    return result


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


class FakeGitHubRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.prs: dict[str, dict[str, object]] = {}
        self.next_number = 77

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(command)
        if command[:3] == ["gh", "pr", "list"]:
            branch = command[command.index("--head") + 1]
            matches = [
                {"number": pr["number"]}
                for pr in self.prs.values()
                if pr["headRefName"] == branch
            ]
            return CommandResult(json.dumps(matches[:1]), "", 0)
        if command[:3] == ["gh", "pr", "create"]:
            branch = command[command.index("--head") + 1]
            base = command[command.index("--base") + 1]
            number = str(self.next_number)
            self.next_number += 1
            self.prs[number] = {
                "number": int(number),
                "url": f"https://github.example/pr/{number}",
                "state": "OPEN",
                "mergedAt": None,
                "headRefName": branch,
                "headRefOid": git(cwd, "rev-parse", "HEAD"),
                "baseRefName": base,
                "reviewDecision": "",
                "reviews": [],
            }
            return CommandResult(
                f"https://github.example/pr/{number}", "", 0
            )
        if command[:3] == ["gh", "pr", "edit"]:
            number = command[3]
            if "--base" in command:
                self.prs[number]["baseRefName"] = command[
                    command.index("--base") + 1
                ]
            self.prs[number]["headRefOid"] = git(cwd, "rev-parse", "HEAD")
            return CommandResult("", "", 0)
        if command[:3] == ["gh", "pr", "view"]:
            return CommandResult(json.dumps(self.prs[command[3]]), "", 0)
        return CommandResult("", f"unexpected provider command: {command}", 1)

    def merge(self, pr_id: str, head_sha: str) -> None:
        self.prs[pr_id]["state"] = "MERGED"
        self.prs[pr_id]["mergedAt"] = "2026-07-26T12:00:00Z"
        self.prs[pr_id]["headRefOid"] = head_sha


class FakeAzureRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.prs: dict[str, dict[str, object]] = {}

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(command)
        if command[:4] == ["az", "repos", "pr", "list"]:
            branch = command[command.index("--source-branch") + 1]
            matches = [
                pr
                for pr in self.prs.values()
                if pr["sourceRefName"] == f"refs/heads/{branch}"
            ]
            return CommandResult(json.dumps(matches), "", 0)
        if command[:4] == ["az", "repos", "pr", "create"]:
            branch = command[command.index("--source-branch") + 1]
            base = command[command.index("--target-branch") + 1]
            pr_id = "91"
            self.prs[pr_id] = {
                "pullRequestId": int(pr_id),
                "url": f"https://dev.azure.example/pr/{pr_id}",
                "status": "active",
                "sourceRefName": f"refs/heads/{branch}",
                "targetRefName": f"refs/heads/{base}",
                "lastMergeSourceCommit": {
                    "commitId": git(cwd, "rev-parse", "HEAD")
                },
                "reviewers": [],
            }
            return CommandResult(json.dumps(self.prs[pr_id]), "", 0)
        if command[:4] == ["az", "repos", "pr", "show"]:
            pr_id = command[command.index("--id") + 1]
            return CommandResult(json.dumps(self.prs[pr_id]), "", 0)
        return CommandResult("", f"unexpected provider command: {command}", 1)

    def merge(self, pr_id: str, head_sha: str) -> None:
        self.prs[pr_id]["status"] = "completed"
        self.prs[pr_id]["lastMergeSourceCommit"] = {"commitId": head_sha}


def ticket_text(
    ticket_id: str,
    blocked_by: tuple[str, ...] = (),
    *,
    mode: str = "AFK",
) -> str:
    blockers = "\n".join(f'  - "{item}"' for item in blocked_by)
    blocker_field = (
        f"blocked_by:\n{blockers}\n" if blockers else "blocked_by: []\n"
    )
    return (
        "---\n"
        "ticket_schema: 1\n"
        f'ticket_id: "{ticket_id}"\n'
        f"execution_mode: {mode}\n"
        f"{blocker_field}"
        "---\n\n"
        f"# Ticket {ticket_id}\n"
    )


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "tests@example.invalid")
        git(self.repo, "config", "user.name", "Ticket Tests")
        (self.repo / "README.md").write_text("baseline\n")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-m", "baseline")
        self.tickets = self.repo / "tickets"
        self.tickets.mkdir()
        (self.tickets / "01.md").write_text(ticket_text("01"))
        (self.tickets / "02.md").write_text(ticket_text("02", ("01",)))
        git(self.repo, "add", "tickets")
        git(self.repo, "commit", "-m", "add tickets")

    def parse(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        return json.loads(result.stdout)

    def resume_events(
        self,
        run_id: str,
        events: list[dict[str, object]],
        *,
        check: bool = True,
    ) -> dict[str, object]:
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / run_id
            / "ledger.json"
        )
        ledger = AtomicLedger(ledger_path).load()
        expanded: list[dict[str, object]] = []
        for event in events:
            if (
                event.get("operation") == "stage"
                and event.get("stage") == "review"
                and event.get("result") in {"pass", "fail"}
            ):
                worktree = Path(ledger["worktree"])
                ticket_id = str(event["ticket_id"])
                fixed = candidate_ref(
                    worktree,
                    ledger["tickets"][ticket_id]["ticket_digest"],
                )
                files = candidate_files(worktree, fixed)
                if fixed.tree_oid != event.get("expected_tree_oid"):
                    raise AssertionError(
                        "review fixture CandidateRef differs from expected tree"
                    )
                findings = (
                    []
                    if event["result"] == "pass"
                    else ["blocker:test: review failure fixture"]
                )
                expanded.append(
                    {
                        "operation": "leaf-result",
                        "ticket_id": ticket_id,
                        "expected_tree_oid": fixed.tree_oid,
                        "leaf_result": {
                            "schema": 3,
                            "complete": True,
                            "candidate_ref": {
                                "base_sha": fixed.base_sha,
                                "tree_oid": fixed.tree_oid,
                                "ticket_digest": fixed.ticket_digest,
                                "contract_version": fixed.contract_version,
                            },
                            "stage": "review",
                            "phase_contract": [
                                "context-loaded",
                                "diff-inspected",
                                "findings-normalized",
                                "handoff-ready",
                            ],
                            "scope": {
                                "files_expected": files,
                                "files_inspected": files,
                                "files_remaining": [],
                            },
                            "phases_remaining": [],
                            "commands_run": [],
                            "findings": findings,
                            "progress_phase": "handoff-ready",
                            "stop_reason": None,
                        },
                    }
                )
            expanded.append(event)
        path = Path(self.directory.name) / f"{run_id}-events.json"
        path.write_text(json.dumps({"schema": 1, "events": expanded}))
        return self.parse(
            run(
                "resume",
                run_id,
                "--repo",
                str(self.repo),
                "--events",
                str(path),
                cwd=self.repo,
                check=check,
            )
        )

    def resume_events_in_process(
        self,
        run_id: str,
        events: list[dict[str, object]],
        runner: FakeGitHubRunner | FakeAzureRunner,
    ) -> dict[str, object]:
        path = Path(self.directory.name) / f"{run_id}-in-process-events.json"
        path.write_text(json.dumps({"schema": 1, "events": events}))
        output = io.StringIO()
        with redirect_stdout(output):
            result = cli_main(
                [
                    "resume",
                    run_id,
                    "--repo",
                    str(self.repo),
                    "--events",
                    str(path),
                ],
                command_runner=runner,
            )
        payload = json.loads(output.getvalue())
        if result:
            raise AssertionError(payload)
        return payload

    def test_plan_is_read_only_and_returns_stable_structured_graph(self) -> None:
        before = git(self.repo, "status", "--porcelain=v1", "--untracked-files=all")

        result = run(
            "plan",
            str(self.tickets),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            cwd=self.repo,
        )

        payload = self.parse(result)
        self.assertEqual(1, payload["schema"])
        self.assertTrue(payload["ok"])
        self.assertEqual("plan", payload["command"])
        self.assertEqual(["01"], payload["data"]["ready"])
        self.assertEqual(["02"], payload["data"]["dependency_blocked"])
        after = git(self.repo, "status", "--porcelain=v1", "--untracked-files=all")
        self.assertEqual(before, after)

    def test_run_uses_isolated_worktree_and_common_dir_ledger(self) -> None:
        caller_marker = self.repo / "caller-untracked.txt"
        caller_marker.write_text("preserve me\n")
        result = run(
            "run",
            str(self.tickets),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--run-id",
            "cli-test",
            cwd=self.repo,
        )
        payload = self.parse(result)
        worktree = Path(payload["data"]["worktree"])
        ledger = Path(payload["data"]["ledger"])
        common_dir = Path(git(self.repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))

        self.assertNotEqual(self.repo.resolve(), worktree.resolve())
        self.assertTrue(worktree.is_dir())
        self.assertTrue(ledger.is_file())
        self.assertTrue(ledger.is_relative_to(common_dir))
        self.assertEqual("preserve me\n", caller_marker.read_text())

        status = self.parse(
            run(
                "status",
                "cli-test",
                "--repo",
                str(self.repo),
                cwd=self.repo,
            )
        )
        self.assertEqual("01", status["data"]["next_ready"])
        self.assertEqual("running", status["data"]["run_state"])

    def test_resume_rejects_coercible_event_document_schema(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "event-schema-test",
                cwd=self.repo,
            )
        )
        path = Path(self.directory.name) / "coercible-events.json"
        path.write_text(json.dumps({"schema": 1.0, "events": []}))

        result = run(
            "resume",
            created["data"]["run_id"],
            "--repo",
            str(self.repo),
            "--events",
            str(path),
            cwd=self.repo,
            check=False,
        )

        self.assertNotEqual(0, result.returncode)

    def test_run_rejects_untracked_ticket_contract_before_creating_worktree(self) -> None:
        untracked = self.repo / "untracked-tickets"
        untracked.mkdir()
        (untracked / "09.md").write_text(ticket_text("09"))
        result = run(
            "run",
            str(untracked),
            "--repo",
            str(self.repo),
            "--provider",
            "github",
            "--run-id",
            "untracked-test",
            cwd=self.repo,
            check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(
            (self.repo.parent / ".repo-ticket-autopilot-worktrees" / "untracked-test").exists()
        )

    def test_abort_and_cleanup_follow_confirmation_and_preserve_ledger(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "azure-devops",
                "--run-id",
                "cleanup-test",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        ledger = Path(created["data"]["ledger"])
        run(
            "abort",
            "cleanup-test",
            "--repo",
            str(self.repo),
            "--actor",
            "operator",
            "--reason",
            "test stop",
            cwd=self.repo,
        )

        refused = run(
            "cleanup",
            "cleanup-test",
            "--repo",
            str(self.repo),
            cwd=self.repo,
            check=False,
        )
        self.assertNotEqual(0, refused.returncode)
        self.assertTrue(worktree.exists())

        cleaned = self.parse(
            run(
                "cleanup",
                "cleanup-test",
                "--repo",
                str(self.repo),
                "--confirm",
                cwd=self.repo,
            )
        )
        self.assertTrue(cleaned["data"]["worktree_removed"])
        self.assertFalse(worktree.exists())
        self.assertTrue(ledger.exists())
        envelope = json.loads(ledger.read_text())
        self.assertTrue(envelope["payload"]["cleanup"]["recorded"])

    def test_cleanup_never_discards_dirty_isolated_worktree(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "dirty-cleanup",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        marker = worktree / "unpublished.txt"
        marker.write_text("retain\n")
        run(
            "abort",
            "dirty-cleanup",
            "--repo",
            str(self.repo),
            "--actor",
            "operator",
            "--reason",
            "test dirty cleanup",
            cwd=self.repo,
        )
        refused = run(
            "cleanup",
            "dirty-cleanup",
            "--repo",
            str(self.repo),
            "--confirm",
            cwd=self.repo,
            check=False,
        )
        self.assertNotEqual(0, refused.returncode)
        self.assertEqual("retain\n", marker.read_text())

    def test_cleanup_rejects_running_even_with_force(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "running-cleanup",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        refused = run(
            "cleanup",
            "running-cleanup",
            "--repo",
            str(self.repo),
            "--force",
            cwd=self.repo,
            check=False,
        )
        self.assertNotEqual(0, refused.returncode)
        self.assertTrue(worktree.exists())

    def test_cleanup_requires_every_local_commit_to_be_published(self) -> None:
        remote = Path(self.directory.name) / "cleanup-remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        git(self.repo, "remote", "add", "origin", str(remote))
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "publication-cleanup",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        git(worktree, "switch", "-c", "retained/local")
        (worktree / "local.txt").write_text("local\n")
        git(worktree, "add", "local.txt")
        git(worktree, "commit", "-m", "local")
        run(
            "abort",
            "publication-cleanup",
            "--repo",
            str(self.repo),
            "--actor",
            "operator",
            "--reason",
            "publication test",
            cwd=self.repo,
        )
        unpublished = run(
            "cleanup",
            "publication-cleanup",
            "--repo",
            str(self.repo),
            "--confirm",
            cwd=self.repo,
            check=False,
        )
        self.assertNotEqual(0, unpublished.returncode)
        self.assertTrue(worktree.exists())
        git(worktree, "push", "-u", "origin", "retained/local")
        published = self.parse(
            run(
                "cleanup",
                "publication-cleanup",
                "--repo",
                str(self.repo),
                "--confirm",
                cwd=self.repo,
            )
        )
        self.assertTrue(published["data"]["worktree_removed"])

    def test_migrate_previews_then_atomically_writes_legacy_ticket(self) -> None:
        legacy = self.repo / "legacy"
        legacy.mkdir()
        dependency = legacy / "01-canonical.md"
        dependency.write_text(ticket_text("01"))
        path = legacy / "03-legacy.md"
        original = (
            "## Execution Mode\n\nAFK\n\n"
            "## Blocked By\n\n- 01\n\n"
            "## Outcome\n\nLegacy content.\n"
        )
        path.write_text(original)

        preview = self.parse(run("migrate", str(legacy), cwd=self.repo))
        self.assertEqual(["03-legacy.md"], preview["data"]["changed"])
        self.assertEqual(["01-canonical.md"], preview["data"]["skipped"])
        self.assertEqual(original, path.read_text())

        written = self.parse(run("migrate", str(legacy), "--write", cwd=self.repo))
        self.assertTrue(written["data"]["written"])
        self.assertTrue(path.read_text().startswith("---\nticket_schema: 1\n"))

    def test_all_public_commands_have_structured_errors(self) -> None:
        result = run(
            "resume",
            "missing-run",
            "--repo",
            str(self.repo),
            cwd=self.repo,
            check=False,
        )
        payload = self.parse(result)
        self.assertFalse(payload["ok"])
        self.assertEqual("resume", payload["command"])
        self.assertIn("error", payload)

    def test_resume_drives_stages_and_invalidates_stale_downstream_evidence(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "drive-test",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        activated = self.resume_events(
            "drive-test", [{"operation": "activate", "ticket_id": "01"}]
        )
        self.assertEqual(
            "implement", activated["data"]["tickets"]["01"]["stage"]
        )

        implementation = worktree / "implementation.txt"
        implementation.write_text("version one\n")
        git(worktree, "add", "-A")
        first_tree = git(worktree, "write-tree")
        reviewed = self.resume_events(
            "drive-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": first_tree,
                }
                for stage in ("implement", "simplify", "review")
            ],
        )
        self.assertEqual(
            ["implement", "simplify", "review"],
            reviewed["data"]["tickets"]["01"]["validated_stages"],
        )

        implementation.write_text("version two\n")
        git(worktree, "add", "-A")
        second_tree = git(worktree, "write-tree")
        invalidated = self.resume_events(
            "drive-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": "qa-plan",
                    "result": "pass",
                    "expected_tree_oid": second_tree,
                }
            ],
        )
        self.assertEqual("invalidated", invalidated["data"]["processed"][0]["result"])
        ticket = invalidated["data"]["tickets"]["01"]
        self.assertEqual("implement", ticket["stage"])
        self.assertEqual([], ticket["validated_stages"])

    def test_delivery_is_crash_resumable_idempotent_and_never_auto_merges(self) -> None:
        remote = Path(self.directory.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        git(self.repo, "remote", "add", "origin", str(remote))
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "delivery-test",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "delivery-test", [{"operation": "activate", "ticket_id": "01"}]
        )
        (worktree / "implementation.txt").write_text("implemented\n")
        git(worktree, "add", "-A")
        tree = git(worktree, "write-tree")
        self.resume_events(
            "delivery-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": tree,
                }
                for stage in (
                    "implement",
                    "simplify",
                    "review",
                    "qa-plan",
                    "qa-execute",
                    "verify",
                    "finalize",
                )
            ],
        )

        prepared = self.resume_events(
            "delivery-test", [{"operation": "delivery", "ticket_id": "01"}]
        )
        self.assertEqual(
            "revalidation-required", prepared["data"]["processed"][0]["result"]
        )
        self.assertEqual("review", prepared["data"]["tickets"]["01"]["stage"])
        self.assertEqual("", git(self.repo, "ls-remote", "--heads", "origin"))
        prepared_tree = git(worktree, "write-tree")
        self.resume_events(
            "delivery-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": prepared_tree,
                }
                for stage in (
                    "review",
                    "qa-plan",
                    "qa-execute",
                    "verify",
                    "finalize",
                )
            ],
        )
        provider_runner = FakeGitHubRunner()
        opened = self.resume_events_in_process(
            "delivery-test",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        delivery = opened["data"]["processed"][0]
        self.assertEqual("pr-open", delivery["result"])
        branch = delivery["branch"]
        head = delivery["head_sha"]
        pr_id = delivery["pr_id"]
        self.assertEqual(
            head,
            git(self.repo, "ls-remote", "--heads", "origin", f"refs/heads/{branch}").split()[0],
        )
        self.assertTrue((worktree / "tickets" / "done" / "01.md").exists())
        self.assertTrue(
            (worktree / "tickets" / "done" / "01.completion.json").exists()
        )
        receipt = {
            "provider": "github",
            "operation": "create-or-update-pr",
            "branch": branch,
            "base": "main",
            "head_sha": head,
            "pr_id": "77",
        }
        contradictory_path = Path(self.directory.name) / "contradictory-pr.json"
        contradictory_path.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "events": [
                        {
                            "operation": "delivery",
                            "ticket_id": "01",
                            "pr_receipt": {**receipt, "head_sha": "wrong-head"},
                        }
                    ],
                }
            )
        )
        contradiction = run(
            "resume",
            "delivery-test",
            "--repo",
            str(self.repo),
            "--events",
            str(contradictory_path),
            cwd=self.repo,
            check=False,
        )
        self.assertNotEqual(0, contradiction.returncode)
        self.assertEqual("pr-open", opened["data"]["tickets"]["01"]["state"])
        repeated = self.resume_events_in_process(
            "delivery-test",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        self.assertEqual("pr-open", repeated["data"]["processed"][0]["result"])
        self.assertIsNone(repeated["data"]["tickets"]["01"]["merge_authorization"])

        self.resume_events(
            "delivery-test", [{"operation": "activate", "ticket_id": "02"}]
        )
        (worktree / "child.txt").write_text("stacked child\n")
        git(worktree, "add", "-A")
        child_tree = git(worktree, "write-tree")
        self.resume_events(
            "delivery-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "02",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": child_tree,
                }
                for stage in (
                    "implement",
                    "simplify",
                    "review",
                    "qa-plan",
                    "qa-execute",
                    "verify",
                    "finalize",
                )
            ],
        )
        child_prepared = self.resume_events(
            "delivery-test", [{"operation": "delivery", "ticket_id": "02"}]
        )
        self.assertEqual(
            "revalidation-required",
            child_prepared["data"]["processed"][0]["result"],
        )
        child_prepared_tree = git(worktree, "write-tree")
        self.resume_events(
            "delivery-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "02",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": child_prepared_tree,
                }
                for stage in (
                    "review",
                    "qa-plan",
                    "qa-execute",
                    "verify",
                    "finalize",
                )
            ],
        )
        child_opened = self.resume_events_in_process(
            "delivery-test",
            [{"operation": "delivery", "ticket_id": "02"}],
            provider_runner,
        )
        child_delivery = child_opened["data"]["processed"][0]
        child_branch = child_delivery["branch"]
        child_head = child_delivery["head_sha"]
        child_pr_id = child_delivery["pr_id"]
        self.assertEqual("pr-open", child_opened["data"]["tickets"]["02"]["state"])

        git(self.repo, "merge", "--ff-only", branch)
        git(self.repo, "push", "-u", "origin", "main")
        run(
            "approve",
            "delivery-test",
            "--repo",
            str(self.repo),
            "--actor",
            "human-reviewer",
            "--evidence",
            "artifact://merge-approval",
            "--ticket",
            "01",
            "--head-sha",
            head,
            cwd=self.repo,
        )
        provider_runner.merge(pr_id, head)
        integrated = self.resume_events_in_process(
            "delivery-test",
            [
                {
                    "operation": "integrate",
                    "ticket_id": "01",
                }
            ],
            provider_runner,
        )
        self.assertEqual("integrated", integrated["data"]["tickets"]["01"]["state"])
        reconcile_prepared = self.resume_events_in_process(
            "delivery-test",
            [
                {
                    "operation": "reconcile",
                    "ticket_id": "02",
                    "parent_branch": branch,
                    "base_branch": "main",
                    "expected_remote_sha": child_head,
                }
            ],
            provider_runner,
        )
        self.assertEqual(
            "revalidation-required",
            reconcile_prepared["data"]["processed"][0]["result"],
        )
        reconciled_tree = git(worktree, "write-tree")
        self.resume_events(
            "delivery-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "02",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": reconciled_tree,
                }
                for stage in (
                    "review",
                    "qa-plan",
                    "qa-execute",
                    "verify",
                    "finalize",
                )
            ],
        )
        reconciled = self.resume_events_in_process(
            "delivery-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            provider_runner,
        )
        reconciliation = reconciled["data"]["processed"][0]
        self.assertEqual("reconciled", reconciliation["result"])
        self.assertEqual(child_pr_id, reconciled["data"]["tickets"]["02"]["pr"]["pr_id"])
        self.assertEqual(
            reconciliation["new_head"],
            git(
                self.repo,
                "ls-remote",
                "--heads",
                "origin",
                f"refs/heads/{child_branch}",
            ).split()[0],
        )

    def test_azure_external_merge_requires_exact_sha_and_live_observation(
        self,
    ) -> None:
        git(self.repo, "rm", "tickets/02.md")
        git(self.repo, "commit", "-m", "single Azure ticket")
        remote = Path(self.directory.name) / "azure-remote.git"
        remote.mkdir()
        git(remote, "init", "--bare")
        git(self.repo, "remote", "add", "origin", str(remote))
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "azure-devops",
                "--run-id",
                "azure-external",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "azure-external",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / "azure-change.txt").write_text("implementation\n")
        git(worktree, "add", "-A")
        implementation_tree = git(worktree, "write-tree")
        self.resume_events(
            "azure-external",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": implementation_tree,
                }
                for stage in (
                    "implement",
                    "simplify",
                    "review",
                    "qa-plan",
                    "qa-execute",
                    "verify",
                    "finalize",
                )
            ],
        )
        prepared = self.resume_events(
            "azure-external",
            [{"operation": "delivery", "ticket_id": "01"}],
        )
        self.assertEqual(
            "revalidation-required",
            prepared["data"]["processed"][0]["result"],
        )
        prepared_tree = git(worktree, "write-tree")
        self.resume_events(
            "azure-external",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": prepared_tree,
                }
                for stage in (
                    "review",
                    "qa-plan",
                    "qa-execute",
                    "verify",
                    "finalize",
                )
            ],
        )
        provider_runner = FakeAzureRunner()
        opened = self.resume_events_in_process(
            "azure-external",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        delivery = opened["data"]["processed"][0]
        self.assertEqual("pr-open", delivery["result"])
        head = delivery["head_sha"]
        pr_id = delivery["pr_id"]

        stale = run(
            "approve",
            "azure-external",
            "--repo",
            str(self.repo),
            "--actor",
            "human-reviewer",
            "--evidence",
            "artifact://azure-external-approval",
            "--ticket",
            "01",
            "--head-sha",
            "stale-head",
            "--external-merge",
            cwd=self.repo,
            check=False,
        )
        self.assertNotEqual(0, stale.returncode)
        approved = self.parse(
            run(
                "approve",
                "azure-external",
                "--repo",
                str(self.repo),
                "--actor",
                "human-reviewer",
                "--evidence",
                "artifact://azure-external-approval",
                "--ticket",
                "01",
                "--head-sha",
                head,
                "--external-merge",
                cwd=self.repo,
            )
        )
        self.assertEqual(
            "external",
            approved["data"]["tickets"]["01"]["merge_authorization"]["mode"],
        )

        provider_runner.merge(pr_id, head)
        integrated = self.resume_events_in_process(
            "azure-external",
            [{"operation": "integrate", "ticket_id": "01"}],
            provider_runner,
        )
        ticket = integrated["data"]["tickets"]["01"]
        self.assertEqual("integrated", ticket["state"])
        self.assertEqual("completed", integrated["data"]["run_state"])
        self.assertEqual(
            "live",
            ticket["delivery"]["integration"]["evidence_class"],
        )
        self.assertTrue(
            all(
                "merge" not in " ".join(command).casefold()
                and "complete" not in " ".join(command).casefold()
                for command in provider_runner.commands
            )
        )

    def test_approve_resolves_hitl_start_gate(self) -> None:
        (self.tickets / "01.md").write_text(ticket_text("01", mode="HITL"))
        git(self.repo, "add", "tickets/01.md")
        git(self.repo, "commit", "-m", "make ticket 01 HITL")
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "approve-test",
                cwd=self.repo,
            )
        )
        ticket = created["data"]["tickets"]["01"]
        self.assertEqual("HITL", ticket["execution_mode"])
        self.assertEqual("gated", ticket["state"])
        gate_id = created["data"]["open_gates"][0]
        self.assertIn(":01:start:", gate_id)
        denied = self.resume_events(
            "approve-test",
            [{"operation": "activate", "ticket_id": "01"}],
            check=False,
        )
        self.assertFalse(denied["ok"])
        self.assertIn("not ready", denied["error"]["message"])
        approved = self.parse(
            run(
                "approve",
                "approve-test",
                gate_id,
                "--repo",
                str(self.repo),
                "--actor",
                "operator",
                "--evidence",
                "artifact://approval",
                cwd=self.repo,
            )
        )
        self.assertEqual("gate", approved["data"]["approved"]["kind"])
        self.assertEqual(["01"], approved["data"]["ready"])
        self.assertEqual(
            0,
            approved["data"]["tickets"]["01"]["quality_failures"],
        )
        activated = self.resume_events(
            "approve-test",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        self.assertEqual("activated", activated["data"]["processed"][0]["result"])

    def test_run_help_has_no_global_supervision_override(self) -> None:
        completed = run("run", "--help", cwd=self.repo)
        self.assertNotIn("--supervision", completed.stdout)


if __name__ == "__main__":
    unittest.main()
