from __future__ import annotations

import copy
import importlib.util
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "ticket-autopilot" / "scripts" / "ticket-autopilot.py"
sys.path.insert(0, str(CLI.parent))

from autopilot.cli import (
    _assert_resume_ticket_source_states,
    _assert_target_base_sha,
    _cache_digest,
    _derive_reconciliation_candidate,
    _derive_reconciliation_refresh_candidate,
    _fetch_target_base,
    _merge_intent_key,
    _verification_cache_inputs,
    main as cli_main,
)
from autopilot.docs_only import APPROVED_SCOPE
from autopilot.git_ops import (
    CommandResult,
    GitError,
    candidate_files,
    candidate_ref,
)
from autopilot.kernel import Kernel, TransitionError
from autopilot.history_codec import decode_history
from autopilot.ledger import AtomicLedger, LedgerError
from autopilot.leaf_protocol import LEAF_PHASE_CONTRACTS
from autopilot.providers import AZURE_DESCRIPTION_TERMINATOR, ProviderError
from autopilot.ticket_contract import ticket_source_digest
from autopilot.ticket_lifecycle import LifecycleError


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
        self.pr_cwds: dict[str, Path] = {}
        self.next_number = 77
        self.readback_body_override: str | None = None
        self.fail_after_merge_once = False
        self.fail_merge_before_apply_once = False
        self.fail_get_pr_state_once = False
        self.merge_commands = 0
        self.checks: list[dict[str, object]] = []
        self.checks_by_pr: dict[str, list[dict[str, object]]] = {}
        self.review_decision = ""
        self.mergeable = "MERGEABLE"
        self.merge_state_status = "CLEAN"
        self.active_rules: list[dict[str, object]] = []
        self.active_rules_after_first_read: list[dict[str, object]] | None = None
        self.fail_active_rules_once = False
        self.private_plan_rules_unavailable = False
        self.active_rule_reads = 0
        self.queue_entries: dict[str, dict[str, object]] = {}
        self.queue_mutations = 0
        self.crash_before_queue_mutation_once = False
        self.view_count = 0
        self.head_change_on_view: int | None = None
        self.head_change_value = "provider-head-drift"

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
            self.pr_cwds[number] = cwd
            self.prs[number] = {
                "id": f"PR_{number}",
                "number": int(number),
                "url": f"https://github.example/pr/{number}",
                "state": "OPEN",
                "mergedAt": None,
                "headRefName": branch,
                "headRefOid": git(cwd, "rev-parse", "HEAD"),
                "baseRefName": base,
                "body": command[command.index("--body") + 1],
                "reviewDecision": "",
                "reviews": [],
                "mergeable": self.mergeable,
                "mergeStateStatus": self.merge_state_status,
            }
            return CommandResult(
                f"https://github.example/pr/{number}", "", 0
            )
        if command[:3] == ["gh", "pr", "merge"]:
            number = command[3]
            expected_head = command[
                command.index("--match-head-commit") + 1
            ]
            if self.prs[number]["headRefOid"] != expected_head:
                return CommandResult("", "head changed", 1)
            self.merge_commands += 1
            if self.fail_merge_before_apply_once:
                self.fail_merge_before_apply_once = False
                return CommandResult("", "merge failed before mutation", 1)
            self.merge(number, expected_head, cwd=cwd)
            if self.fail_after_merge_once:
                self.fail_after_merge_once = False
                return CommandResult("", "merge response was lost", 1)
            return CommandResult("merged", "", 0)
        if command[:3] == ["gh", "api", "graphql"]:
            fields = {
                item.split("=", 1)[0]: item.split("=", 1)[1]
                for item in command
                if "=" in item
            }
            node_id = fields["pullRequestId"]
            number = node_id.removeprefix("PR_")
            pr = self.prs[number]
            if "enqueuePullRequest" in fields["query"]:
                if self.crash_before_queue_mutation_once:
                    self.crash_before_queue_mutation_once = False
                    raise RuntimeError("crash before queue provider mutation")
                expected_head = fields["expectedHeadOid"]
                if pr["headRefOid"] != expected_head:
                    return CommandResult("", "head changed", 1)
                self.queue_mutations += 1
                entry = {
                    "id": f"MQE_{number}",
                    "position": 1,
                    "state": "QUEUED",
                    "enqueuedAt": "2026-08-06T09:14:16Z",
                }
                self.queue_entries[number] = entry
                return CommandResult(
                    json.dumps(
                        {
                            "data": {
                                "enqueuePullRequest": {
                                    "clientMutationId": fields[
                                        "clientMutationId"
                                    ],
                                    "mergeQueueEntry": entry,
                                }
                            }
                        }
                    ),
                    "",
                    0,
                )
            return CommandResult(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "headRefOid": pr["headRefOid"],
                                "mergeQueueEntry": self.queue_entries.get(number),
                            }
                        }
                    }
                ),
                "",
                0,
            )
        if (
            command[:2] == ["gh", "api"]
            and "/rules/branches/" in command[2]
        ):
            self.active_rule_reads += 1
            if self.fail_active_rules_once:
                self.fail_active_rules_once = False
                return CommandResult(
                    "",
                    "HTTP 403: Resource not accessible by integration",
                    1,
                )
            if self.private_plan_rules_unavailable:
                return CommandResult(
                    json.dumps(
                        {
                            "message": (
                                "Upgrade to GitHub Pro or make this repository public "
                                "to enable this feature."
                            ),
                            "documentation_url": (
                                "https://docs.github.com/rest/repos/rules"
                                "#get-rules-for-a-branch"
                            ),
                            "status": "403",
                        }
                    ),
                    "gh: plan feature unavailable (HTTP 403)",
                    1,
                )
            if (
                self.active_rule_reads > 1
                and self.active_rules_after_first_read is not None
            ):
                self.active_rules = self.active_rules_after_first_read
            return CommandResult(json.dumps(self.active_rules), "", 0)
        if command[:2] == ["gh", "api"]:
            number = command[2].rsplit("/", 1)[-1]
            self.prs[number]["baseRefName"] = next(
                item.split("=", 1)[1]
                for item in command
                if item.startswith("base=")
            )
            self.prs[number]["body"] = next(
                item.split("=", 1)[1]
                for item in command
                if item.startswith("body=")
            )
            self.prs[number]["headRefOid"] = git(cwd, "rev-parse", "HEAD")
            return CommandResult("", "", 0)
        if command[:3] == ["gh", "pr", "edit"]:
            number = command[3]
            self.prs[number]["baseRefName"] = command[
                command.index("--base") + 1
            ]
            if "--body" in command:
                self.prs[number]["body"] = command[
                    command.index("--body") + 1
                ]
            self.prs[number]["headRefOid"] = git(cwd, "rev-parse", "HEAD")
            return CommandResult("", "", 0)
        if command[:3] == ["gh", "pr", "view"]:
            self.view_count += 1
            if self.view_count == self.head_change_on_view:
                self.prs[command[3]]["headRefOid"] = self.head_change_value
            if self.fail_get_pr_state_once:
                self.fail_get_pr_state_once = False
                return CommandResult("", "provider readback failed", 1)
            document = dict(self.prs[command[3]])
            document["reviewDecision"] = self.review_decision
            document["mergeable"] = self.mergeable
            document["mergeStateStatus"] = self.merge_state_status
            if "statusCheckRollup" in command[-1]:
                rollup: list[dict[str, object]] = []
                for item in self.checks_by_pr.get(command[3], self.checks):
                    if not isinstance(item, dict):
                        rollup.append(item)  # type: ignore[arg-type]
                        continue
                    bucket = str(item.get("bucket", "unknown")).casefold()
                    state = str(item.get("state", ""))
                    rollup.append(
                        {
                            "__typename": "CheckRun",
                            "name": item.get("name"),
                            "status": (
                                state
                                if bucket == "pending"
                                else "COMPLETED"
                            ),
                            "conclusion": (
                                None if bucket == "pending" else state
                            ),
                            "workflowName": item.get("workflow", ""),
                        }
                    )
                document["statusCheckRollup"] = rollup
            if self.readback_body_override is not None:
                document["body"] = self.readback_body_override
            return CommandResult(json.dumps(document), "", 0)
        if command[:3] == ["gh", "pr", "checks"]:
            return CommandResult(
                json.dumps(self.checks_by_pr.get(command[3], self.checks)),
                "",
                0,
            )
        return CommandResult("", f"unexpected provider command: {command}", 1)

    def merge(
        self, pr_id: str, head_sha: str, *, cwd: Path | None = None
    ) -> None:
        merge_cwd = cwd or self.pr_cwds[pr_id]
        base = str(self.prs[pr_id]["baseRefName"])
        remote = git(
            merge_cwd,
            "ls-remote",
            "--heads",
            "origin",
            f"refs/heads/{base}",
        )
        base_sha = remote.split()[0] if remote else None
        head_tree = git(merge_cwd, "rev-parse", f"{head_sha}^{{tree}}")
        base_tree = (
            git(merge_cwd, "rev-parse", f"{base_sha}^{{tree}}")
            if base_sha
            else None
        )
        merge_sha = base_sha if base_tree == head_tree else head_sha
        if base_sha and base_tree != head_tree and subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_sha, head_sha],
            cwd=merge_cwd,
            capture_output=True,
        ).returncode:
            merge_tree = git(
                merge_cwd,
                "merge-tree",
                "--write-tree",
                base_sha,
                head_sha,
            ).splitlines()[0]
            merge_sha = git(
                merge_cwd,
                "commit-tree",
                merge_tree,
                "-p",
                base_sha,
                "-p",
                head_sha,
                "-m",
                "fake provider merge",
            )
        if merge_sha != base_sha:
            git(merge_cwd, "push", "origin", f"{merge_sha}:refs/heads/{base}")
        self.prs[pr_id]["state"] = "MERGED"
        self.prs[pr_id]["mergedAt"] = "2026-07-26T12:00:00Z"
        self.prs[pr_id]["headRefOid"] = head_sha
        self.prs[pr_id]["mergeCommit"] = {"oid": merge_sha}


def _azure_description(command: list[str]) -> str:
    """Reconstruct the description Azure DevOps would store from the argument vector.

    `--description` is `nargs='+'` and the service joins the values with newlines, so the
    whole slice up to the next option is the body. Reading only the first value would
    reproduce the truncation this fake exists to catch.
    """

    start = command.index("--description") + 1
    end = command.index(AZURE_DESCRIPTION_TERMINATOR, start)
    return "\n".join(command[start:end])


class FakeAzureRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.prs: dict[str, dict[str, object]] = {}
        self.pr_cwds: dict[str, Path] = {}

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
            self.pr_cwds[pr_id] = cwd
            self.prs[pr_id] = {
                "pullRequestId": int(pr_id),
                "url": f"https://dev.azure.example/pr/{pr_id}",
                "status": "active",
                "sourceRefName": f"refs/heads/{branch}",
                "targetRefName": f"refs/heads/{base}",
                "description": _azure_description(command),
                "lastMergeSourceCommit": {
                    "commitId": git(cwd, "rev-parse", "HEAD")
                },
                "reviewers": [],
            }
            return CommandResult(json.dumps(self.prs[pr_id]), "", 0)
        if command[:4] == ["az", "repos", "pr", "update"]:
            pr_id = command[command.index("--id") + 1]
            self.prs[pr_id]["title"] = command[command.index("--title") + 1]
            self.prs[pr_id]["description"] = _azure_description(command)
            return CommandResult(json.dumps(self.prs[pr_id]), "", 0)
        if command[:4] == ["az", "repos", "pr", "show"]:
            pr_id = command[command.index("--id") + 1]
            return CommandResult(json.dumps(self.prs[pr_id]), "", 0)
        return CommandResult("", f"unexpected provider command: {command}", 1)

    def merge(self, pr_id: str, head_sha: str) -> None:
        cwd = self.pr_cwds[pr_id]
        base = str(self.prs[pr_id]["targetRefName"]).removeprefix(
            "refs/heads/"
        )
        remote = git(
            cwd,
            "ls-remote",
            "--heads",
            "origin",
            f"refs/heads/{base}",
        )
        base_sha = remote.split()[0] if remote else None
        head_tree = git(cwd, "rev-parse", f"{head_sha}^{{tree}}")
        base_tree = (
            git(cwd, "rev-parse", f"{base_sha}^{{tree}}")
            if base_sha
            else None
        )
        merge_sha = base_sha if base_tree == head_tree else head_sha
        if base_sha and base_tree != head_tree and subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_sha, head_sha],
            cwd=cwd,
            capture_output=True,
        ).returncode:
            merge_tree = git(
                cwd,
                "merge-tree",
                "--write-tree",
                base_sha,
                head_sha,
            ).splitlines()[0]
            merge_sha = git(
                cwd,
                "commit-tree",
                merge_tree,
                "-p",
                base_sha,
                "-p",
                head_sha,
                "-m",
                "fake provider merge",
            )
        if merge_sha != base_sha:
            git(cwd, "push", "origin", f"{merge_sha}:refs/heads/{base}")
        self.prs[pr_id]["status"] = "completed"
        self.prs[pr_id]["lastMergeSourceCommit"] = {"commitId": head_sha}
        self.prs[pr_id]["lastMergeCommit"] = {"commitId": merge_sha}


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


def verification_bundle(
    candidate: dict[str, object],
    *,
    operation: str = "report",
    ticket_id: str = "01",
) -> dict[str, object]:
    fixture_path = (
        ROOT
        / "verification-audit"
        / "tests"
        / "test_verification_contract.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_ticket_autopilot_verification_fixture",
        fixture_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError("verification fixture is unavailable")
    module = importlib.util.module_from_spec(spec)
    original_path = list(sys.path)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = original_path
    original = module.candidate()

    def rebound(value):
        if isinstance(value, dict):
            if value == original:
                return dict(candidate)
            return {key: rebound(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rebound(item) for item in value]
        return value

    if operation == "merge-pr":
        bundle = rebound(module.complete_bundle())
        bundle.pop("merge_authorization", None)
        bundle["verification"]["requested_operation"] = operation
    else:
        bundle = rebound(module.bundle_without_provider(operation))
    bundle["ticket_id"] = ticket_id
    bundle["ticket_envelope_ref"] = f"tickets/{ticket_id}.md"
    bundle["verification"].update(module.reduce_claims(bundle))
    return bundle


def valid_pr_body(
    bundle: dict[str, object], *, expected_head_sha: str | None = None
) -> str:
    evidence_lines = [
        f"{item['id']}: {item['class']} {item['result']}."
        for item in bundle["evidence"]
        if item["class"] in {"simulated", "live"}
        or item["result"] == "skipped"
    ]
    gate_lines = [
        f"{item['id']}: {item['status']}."
        for item in bundle["gates"]
        if item["status"] in {"open", "failed"}
    ]
    return "\n".join(
        [
            "## Summary",
            "Candidate-bound delivery explanation.",
            *(
                [f"Bound to expected PR head {expected_head_sha}."]
                if expected_head_sha is not None
                else []
            ),
            "",
            "## Behavior",
            "The runner validates, publishes, reads back, and revalidates this body.",
            "",
            "## Verification",
            *(evidence_lines or ["Targeted local checks are recorded in the bundle."]),
            "",
            "## Risks and gates",
            *(gate_lines or ["No open or failed gate is hidden by this body."]),
            "",
            "## Reviewer checks",
            "Review the CandidateRef, evidence classes, and residual limitations.",
            "",
            "```mermaid",
            "flowchart LR",
            "    Bundle --> Validate --> Publish --> Readback --> Revalidate",
            "```",
            "",
        ]
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

    def test_reconciliation_mutators_have_immediate_lifecycle_barriers(self) -> None:
        class RecordingRunner:
            def __init__(self) -> None:
                self.commands: list[list[str]] = []

            def run(self, command: list[str], *, cwd: Path) -> CommandResult:
                self.commands.append(command)
                return CommandResult("", "", 0)

        runner = RecordingRunner()
        with self.assertRaisesRegex(TransitionError, "drift before fetch"):
            _fetch_target_base(
                self.repo,
                runner,
                "main",
                boundary_guard=lambda _boundary: (_ for _ in ()).throw(
                    TransitionError("drift before fetch")
                ),
            )
        self.assertEqual([], runner.commands)

        class Provider:
            @staticmethod
            def reconciliation_commands(**_kwargs: object) -> list[list[str]]:
                return [["git", "rebase", "--onto", "parent", "base"]]

        ticket = {
            "ticket_digest": "0" * 64,
            "pr": {"branch": "ticket/02", "head_sha": "old-head"},
        }
        cases = {
            "git:reconcile-switch": [
                "old-head refs/heads/ticket/02",
                "other-branch",
                "/missing/rebase-merge",
                "/missing/rebase-apply",
            ],
            "git:reconcile-rebase": [
                "old-head refs/heads/ticket/02",
                "ticket/02",
                "/missing/rebase-merge",
                "/missing/rebase-apply",
                "old-head",
            ],
        }
        for target, git_results in cases.items():
            with self.subTest(target=target):
                runner = RecordingRunner()

                def barrier(boundary: str) -> None:
                    if boundary == target:
                        raise TransitionError(f"drift before {boundary}")

                with mock.patch(
                    "autopilot.cli.run_git", side_effect=git_results
                ), self.assertRaisesRegex(TransitionError, "drift before"):
                    _derive_reconciliation_candidate(
                        self.repo,
                        Provider(),
                        ticket,
                        parent_head="parent",
                        base_sha="base",
                        base_tree_oid="base-tree",
                        expected_remote_sha="old-head",
                        replay_intent=False,
                        command_runner=runner,
                        boundary_guard=barrier,
                    )
                self.assertEqual([], runner.commands)

    def test_failed_reconciliation_aborts_before_post_failure_guard(self) -> None:
        events: list[str] = []

        class Provider:
            @staticmethod
            def reconciliation_commands(**_kwargs: object) -> list[list[str]]:
                return [["git", "rebase", "--onto", "base", "parent"]]

        class FailingRebaseRunner:
            def __init__(self) -> None:
                self.commands: list[list[str]] = []

            def run(self, command: list[str], *, cwd: Path) -> CommandResult:
                self.commands.append(command)
                events.append(f"command:{' '.join(command)}")
                if command == ["git", "rebase", "--abort"]:
                    return CommandResult("", "", 0)
                return CommandResult("", "content conflict", 1)

        runner = FailingRebaseRunner()

        def barrier(boundary: str) -> None:
            events.append(f"guard:{boundary}")
            if (
                boundary == "git:reconcile-abort"
                and ["git", "rebase", "--abort"] not in runner.commands
            ):
                raise LifecycleError(
                    "ticket '02' content differs from managed snapshot"
                )

        ticket = {
            "ticket_digest": "0" * 64,
            "pr": {"branch": "ticket/02", "head_sha": "old-head"},
        }
        git_results = [
            "old-head refs/heads/ticket/02",
            "ticket/02",
            "/missing/rebase-merge",
            "/missing/rebase-apply",
            "old-head",
            "/missing/rebase-merge",
            "/missing/rebase-apply",
            "ticket/02",
            "old-head",
        ]
        with mock.patch(
            "autopilot.cli.run_git", side_effect=git_results
        ), self.assertRaisesRegex(GitError, "content conflict"):
            _derive_reconciliation_candidate(
                self.repo,
                Provider(),
                ticket,
                parent_head="parent",
                base_sha="base",
                base_tree_oid="base-tree",
                expected_remote_sha="old-head",
                replay_intent=False,
                command_runner=runner,
                boundary_guard=barrier,
            )
        self.assertEqual(
            [
                "guard:git:reconcile-rebase",
                "command:git rebase --onto base parent",
                "command:git rebase --abort",
                "guard:git:reconcile-abort",
            ],
            events,
        )

    def test_failed_reconciliation_reports_abort_failure(self) -> None:
        class Provider:
            @staticmethod
            def reconciliation_commands(**_kwargs: object) -> list[list[str]]:
                return [["git", "rebase", "--onto", "base", "parent"]]

        class AbortFailureRunner:
            def run(self, command: list[str], *, cwd: Path) -> CommandResult:
                if command == ["git", "rebase", "--abort"]:
                    return CommandResult("", "abort failed", 1)
                return CommandResult("", "content conflict", 1)

        ticket = {
            "ticket_digest": "0" * 64,
            "pr": {"branch": "ticket/02", "head_sha": "old-head"},
        }
        git_results = [
            "old-head refs/heads/ticket/02",
            "ticket/02",
            "/missing/rebase-merge",
            "/missing/rebase-apply",
            "old-head",
        ]
        with mock.patch(
            "autopilot.cli.run_git", side_effect=git_results
        ), self.assertRaisesRegex(
            GitError, "content conflict.*abort failed.*explicit recovery"
        ):
            _derive_reconciliation_candidate(
                self.repo,
                Provider(),
                ticket,
                parent_head="parent",
                base_sha="base",
                base_tree_oid="base-tree",
                expected_remote_sha="old-head",
                replay_intent=False,
                command_runner=AbortFailureRunner(),
            )

    def test_failed_reconciliation_reports_incomplete_cleanup(self) -> None:
        class Provider:
            @staticmethod
            def reconciliation_commands(**_kwargs: object) -> list[list[str]]:
                return [["git", "rebase", "--onto", "base", "parent"]]

        class FailingRebaseRunner:
            def run(self, command: list[str], *, cwd: Path) -> CommandResult:
                if command == ["git", "rebase", "--abort"]:
                    return CommandResult("", "", 0)
                return CommandResult("", "content conflict", 1)

        stuck_state = self.repo / "stuck-rebase-merge"
        stuck_state.mkdir()
        ticket = {
            "ticket_digest": "0" * 64,
            "pr": {"branch": "ticket/02", "head_sha": "old-head"},
        }
        git_results = [
            "old-head refs/heads/ticket/02",
            "ticket/02",
            "/missing/rebase-merge",
            "/missing/rebase-apply",
            "old-head",
            str(stuck_state),
            "/missing/rebase-apply",
            "ticket/02",
            "old-head",
        ]
        with mock.patch(
            "autopilot.cli.run_git", side_effect=git_results
        ), self.assertRaisesRegex(
            GitError, "content conflict.*rebase state remains.*explicit recovery"
        ):
            _derive_reconciliation_candidate(
                self.repo,
                Provider(),
                ticket,
                parent_head="parent",
                base_sha="base",
                base_tree_oid="base-tree",
                expected_remote_sha="old-head",
                replay_intent=False,
                command_runner=FailingRebaseRunner(),
            )

    def test_failed_reconciliation_refresh_uses_shared_abort_contract(self) -> None:
        events: list[str] = []

        class Provider:
            @staticmethod
            def reconciliation_commands(**_kwargs: object) -> list[list[str]]:
                return [["git", "rebase", "--onto", "new-base", "old-base"]]

        class RefreshRunner:
            def __init__(self) -> None:
                self.commands: list[list[str]] = []

            def run(self, command: list[str], *, cwd: Path) -> CommandResult:
                self.commands.append(command)
                events.append(f"command:{' '.join(command)}")
                if command[:3] == ["git", "merge-base", "--is-ancestor"]:
                    return CommandResult("", "", 0)
                if command == ["git", "rebase", "--abort"]:
                    return CommandResult("", "", 0)
                return CommandResult("", "refresh conflict", 1)

        runner = RefreshRunner()

        def barrier(boundary: str) -> None:
            events.append(f"guard:{boundary}")
            if (
                boundary == "git:reconcile-refresh-abort"
                and ["git", "rebase", "--abort"] not in runner.commands
            ):
                raise LifecycleError("conflicted source")

        ticket = {
            "ticket_digest": "0" * 64,
            "pr": {"branch": "ticket/02", "head_sha": "old-head"},
        }
        refresh_intent = {
            "expected_remote_sha": "old-head",
            "old_local_head": "old-local-head",
            "old_target": {"sha": "old-base"},
            "new_target": {"sha": "new-base", "tree_oid": "new-tree"},
        }
        git_results = [
            "old-head refs/heads/ticket/02",
            "/missing/rebase-merge",
            "/missing/rebase-apply",
            "ticket/02",
            "old-local-head",
            "/missing/rebase-merge",
            "/missing/rebase-apply",
            "ticket/02",
            "old-local-head",
        ]
        with mock.patch(
            "autopilot.cli.run_git", side_effect=git_results
        ), self.assertRaisesRegex(GitError, "refresh conflict"):
            _derive_reconciliation_refresh_candidate(
                self.repo,
                Provider(),
                ticket,
                refresh_intent,
                command_runner=runner,
                boundary_guard=barrier,
            )
        self.assertEqual(
            [
                "command:git merge-base --is-ancestor old-base old-local-head",
                "guard:git:reconcile-refresh-rebase",
                "command:git rebase --onto new-base old-base",
                "command:git rebase --abort",
                "guard:git:reconcile-refresh-abort",
            ],
            events,
        )

    def test_pause_unpause_prevents_resume_provider_work(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "pause-cli",
                cwd=self.repo,
            )
        )
        paused = self.parse(
            run(
                "pause",
                "pause-cli",
                "--repo",
                str(self.repo),
                "--actor",
                "user:alice",
                "--reason",
                "maintenance window",
                cwd=self.repo,
            )
        )
        runner = FakeGitHubRunner()
        output = io.StringIO()
        with redirect_stdout(output):
            code = cli_main(
                ["resume", "pause-cli", "--repo", str(self.repo)],
                command_runner=runner,
            )

        self.assertEqual(0, code)
        self.assertEqual("paused", paused["data"]["execution_lifecycle"])
        self.assertEqual([], runner.commands)
        self.assertEqual([], json.loads(output.getvalue())["data"]["processed"])

        resumed = self.parse(
            run(
                "unpause",
                "pause-cli",
                "--repo",
                str(self.repo),
                "--actor",
                "user:alice",
                "--reason",
                "maintenance complete",
                cwd=self.repo,
            )
        )
        self.assertEqual("01", resumed["data"]["next_ready"])

    def test_hold_repoints_the_linking_map_and_reopen_repoints_it_back(self) -> None:
        """Both directions of the disposition repoint, through the real CLI path."""

        specs = self.repo / "docs" / "specs"
        specs.mkdir(parents=True)
        page = specs / "map.md"
        page.write_text(
            "# Map\n\n- [the ticket](../../tickets/01.md)\n", encoding="utf-8"
        )
        git(self.repo, "add", "docs")
        git(self.repo, "commit", "-m", "map linking the ticket")

        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "repoint-cli",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "repoint-cli", [{"operation": "activate", "ticket_id": "01"}]
        )

        held = self.parse(
            run(
                "ticket-hold",
                "repoint-cli",
                "01",
                "--repo",
                str(self.repo),
                "--actor",
                "user:alice",
                "--reason",
                "await decision",
                "--authority-ref",
                "decision:hold-01",
                cwd=self.repo,
            )
        )
        self.assertEqual("on-hold", held["data"]["tickets"]["01"]["disposition"])
        worktree_map = worktree / "docs" / "specs" / "map.md"
        held_text = worktree_map.read_text(encoding="utf-8")
        self.assertIn("(../../tickets/hold/01.md)", held_text)
        status = git(worktree, "status", "--porcelain=v1")
        self.assertIn("docs/specs/map.md", status, "the repoint shares the staged state")

        request = self.parse(
            run(
                "ticket-reopen-request",
                "repoint-cli",
                "01",
                "--repo",
                str(self.repo),
                "--actor",
                "user:alice",
                "--reason",
                "resume work",
                cwd=self.repo,
            )
        )
        gate_id = request["data"]["reopen_gate"]
        self.parse(
            run(
                "approve",
                "repoint-cli",
                gate_id,
                "--repo",
                str(self.repo),
                "--actor",
                "user:bob",
                "--evidence",
                "decision:reopen-01",
                cwd=self.repo,
            )
        )
        reopened = self.parse(
            run(
                "ticket-reopen",
                "repoint-cli",
                "01",
                gate_id,
                "--repo",
                str(self.repo),
                cwd=self.repo,
            )
        )
        self.assertEqual("open", reopened["data"]["tickets"]["01"]["disposition"])
        reopened_text = worktree_map.read_text(encoding="utf-8")
        self.assertIn("(../../tickets/01.md)", reopened_text)
        self.assertNotIn("hold/01.md", reopened_text)

    def test_hold_reopen_and_cancel_are_receipted_cli_transitions(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "lifecycle-cli",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "lifecycle-cli"
            / "ledger.json"
        )
        journal = ledger_path.parent / "ticket-lifecycle"

        def durable_state() -> tuple[bytes, str, dict[str, bytes], dict[str, bytes]]:
            sources = {
                path.relative_to(worktree / "tickets").as_posix(): path.read_bytes()
                for path in (worktree / "tickets").rglob("*.md")
            }
            receipts = {
                path.name: path.read_bytes()
                for path in journal.glob("*.json")
            }
            return ledger_path.read_bytes(), git(worktree, "write-tree"), sources, receipts

        self.resume_events(
            "lifecycle-cli", [{"operation": "activate", "ticket_id": "01"}]
        )

        held = self.parse(
            run(
                "ticket-hold",
                "lifecycle-cli",
                "01",
                "--repo",
                str(self.repo),
                "--actor",
                "user:alice",
                "--reason",
                "await decision",
                "--authority-ref",
                "decision:hold-01",
                cwd=self.repo,
            )
        )
        self.assertEqual("on-hold", held["data"]["tickets"]["01"]["disposition"])
        self.assertEqual(
            "hold/01.md",
            held["data"]["tickets"]["01"]["current_source_relative_path"],
        )
        self.assertTrue((worktree / "tickets" / "hold" / "01.md").is_file())
        self.assertEqual(
            "dependency-on-hold",
            held["data"]["tickets"]["02"]["readiness_causes"][0]["reason"],
        )
        blocked_events = Path(self.directory.name) / "held-events.json"
        blocked_events.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "events": [{"operation": "delivery", "ticket_id": "01"}],
                }
            ),
            encoding="utf-8",
        )
        held_runner = FakeGitHubRunner()
        blocked_output = io.StringIO()
        with redirect_stdout(blocked_output):
            blocked_code = cli_main(
                [
                    "resume",
                    "lifecycle-cli",
                    "--repo",
                    str(self.repo),
                    "--events",
                    str(blocked_events),
                ],
                command_runner=held_runner,
            )
        self.assertEqual(2, blocked_code)
        self.assertEqual([], held_runner.commands)

        before_fake_authority = durable_state()
        denied = run(
            "ticket-reopen",
            "lifecycle-cli",
            "01",
            "gate:fake",
            "--repo",
            str(self.repo),
            "--actor",
            "agent",
            "--authority-ref",
            "fake:authority",
            cwd=self.repo,
            check=False,
        )
        self.assertEqual(2, denied.returncode)
        self.assertEqual(before_fake_authority, durable_state())

        requested = self.parse(
            run(
                "ticket-reopen-request",
                "lifecycle-cli",
                "01",
                "--repo",
                str(self.repo),
                "--actor",
                "agent:planner",
                "--reason",
                "decision resolved",
                cwd=self.repo,
            )
        )
        gate_id = requested["data"]["reopen_gate"]
        self.parse(
            run(
                "approve",
                "lifecycle-cli",
                gate_id,
                "--repo",
                str(self.repo),
                "--actor",
                "user:alice",
                "--evidence",
                "decision:reopen-01",
                cwd=self.repo,
            )
        )
        reopened = self.parse(
            run(
                "ticket-reopen",
                "lifecycle-cli",
                "01",
                gate_id,
                "--repo",
                str(self.repo),
                cwd=self.repo,
            )
        )
        self.assertIsNone(reopened["data"]["tickets"]["01"]["candidate_ref"])
        self.assertEqual(
            "01.md",
            reopened["data"]["tickets"]["01"]["current_source_relative_path"],
        )
        self.assertTrue((worktree / "tickets" / "01.md").is_file())
        after_reopen = durable_state()
        replayed = self.parse(
            run(
                "ticket-reopen",
                "lifecycle-cli",
                "01",
                gate_id,
                "--repo",
                str(self.repo),
                cwd=self.repo,
            )
        )
        self.assertEqual(
            reopened["data"]["lifecycle_receipt"],
            replayed["data"]["lifecycle_receipt"],
        )
        self.assertEqual(after_reopen, durable_state())

        wrong_replay = run(
            "ticket-reopen",
            "lifecycle-cli",
            "01",
            "gate:wrong",
            "--repo",
            str(self.repo),
            cwd=self.repo,
            check=False,
        )
        self.assertEqual(2, wrong_replay.returncode)
        self.assertEqual(after_reopen, durable_state())

        canceled = self.parse(
            run(
                "ticket-cancel",
                "lifecycle-cli",
                "01",
                "--repo",
                str(self.repo),
                "--actor",
                "user:alice",
                "--reason",
                "superseded",
                "--authority-ref",
                "decision:cancel-01",
                cwd=self.repo,
            )
        )
        self.assertEqual("canceled", canceled["data"]["tickets"]["01"]["disposition"])
        self.assertEqual(
            "canceled/01.md",
            canceled["data"]["tickets"]["01"]["current_source_relative_path"],
        )
        self.assertEqual("open", canceled["data"]["tickets"]["02"]["disposition"])
        self.assertEqual(
            "dependency-canceled",
            canceled["data"]["tickets"]["02"]["readiness_causes"][0]["reason"],
        )
        before_invalid = durable_state()
        rejected = run(
            "ticket-hold",
            "lifecycle-cli",
            "01",
            "--repo",
            str(self.repo),
            "--actor",
            "agent",
            "--reason",
            "invalid canceled to hold",
            "--authority-ref",
            "fake:authority",
            cwd=self.repo,
            check=False,
        )

        self.assertEqual(2, rejected.returncode)
        self.assertEqual(before_invalid, durable_state())

    def test_paused_merge_approval_stops_before_provider_or_ledger_mutation(self) -> None:
        self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "paused-approve",
                cwd=self.repo,
            )
        )
        self.parse(
            run(
                "pause",
                "paused-approve",
                "--repo",
                str(self.repo),
                "--actor",
                "user:alice",
                "--reason",
                "maintenance",
                cwd=self.repo,
            )
        )
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "paused-approve"
            / "ledger.json"
        )
        before = ledger_path.read_bytes()
        provider_runner = FakeGitHubRunner()
        output = io.StringIO()
        with redirect_stdout(output):
            result = cli_main(
                [
                    "approve",
                    "paused-approve",
                    "--repo",
                    str(self.repo),
                    "--ticket",
                    "01",
                    "--head-sha",
                    "fake-head",
                    "--actor",
                    "user:alice",
                    "--evidence",
                    "approval:fake",
                ],
                command_runner=provider_runner,
            )
        self.assertEqual(2, result)
        self.assertIn("paused", output.getvalue())
        self.assertEqual([], provider_runner.commands)
        self.assertEqual(before, ledger_path.read_bytes())

    def test_unreceipted_active_source_move_fails_before_provider_work(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "source-drift-cli",
                cwd=self.repo,
            )
        )
        self.resume_events(
            "source-drift-cli", [{"operation": "activate", "ticket_id": "01"}]
        )
        worktree = Path(created["data"]["worktree"])
        hold = worktree / "tickets" / "hold"
        hold.mkdir()
        (worktree / "tickets" / "01.md").rename(hold / "01.md")
        runner = FakeGitHubRunner()
        output = io.StringIO()

        with redirect_stdout(output):
            code = cli_main(
                ["resume", "source-drift-cli", "--repo", str(self.repo)],
                command_runner=runner,
            )

        self.assertEqual(2, code)
        self.assertEqual([], runner.commands)
        self.assertIn("source disposition drift", output.getvalue())

    def test_resume_accepts_completed_source_only_on_a_sibling_branch(self) -> None:
        digest = ticket_source_digest(self.tickets / "01.md")
        git(self.repo, "switch", "-c", "completed-01")
        (self.tickets / "done").mkdir()
        git(self.repo, "mv", "tickets/01.md", "tickets/done/01.md")
        git(self.repo, "commit", "-m", "complete ticket 01")
        delivered_head = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "switch", "-c", "sibling-02", "main")
        tickets = {
            "01": {
                "disposition": "completed",
                "ticket_digest": digest,
                "delivery_lineage": {"head_sha": delivered_head},
            }
        }

        _assert_resume_ticket_source_states(self.tickets, tickets, self.repo)

        git(self.repo, "switch", "-c", "reverted-01", "completed-01")
        git(self.repo, "mv", "tickets/done/01.md", "tickets/01.md")
        git(self.repo, "commit", "-m", "reopen completed source without receipt")
        with self.assertRaisesRegex(LifecycleError, "source disposition drift"):
            _assert_resume_ticket_source_states(
                self.tickets, tickets, self.repo
            )

    def test_resume_accepts_unchanged_crlf_ticket_sources(self) -> None:
        git(self.repo, "config", "core.autocrlf", "true")
        for source in self.tickets.glob("*.md"):
            source.unlink()
        git(self.repo, "checkout", "HEAD", "--", "tickets")
        self.assertIn(b"\r\n", (self.tickets / "01.md").read_bytes())

        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "crlf-source",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.assertIn(b"\r\n", (worktree / "tickets" / "01.md").read_bytes())

        activated = self.resume_events(
            "crlf-source", [{"operation": "activate", "ticket_id": "01"}]
        )

        self.assertEqual("implement", activated["data"]["tickets"]["01"]["stage"])
        self.assertEqual([], activated["data"]["open_gates"])

    def test_source_drift_after_resume_preflight_is_rechecked_before_delivery(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "boundary-drift",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "boundary-drift", [{"operation": "activate", "ticket_id": "01"}]
        )
        (worktree / "implementation.txt").write_text("candidate\n")
        git(worktree, "add", "-A")
        tree = git(worktree, "write-tree")
        self.resume_events(
            "boundary-drift",
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
        events = Path(self.directory.name) / "boundary-drift-events.json"
        events.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "events": [{"operation": "delivery", "ticket_id": "01"}],
                }
            )
        )
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "boundary-drift"
            / "ledger.json"
        )
        before = ledger_path.read_bytes()
        source = worktree / "tickets" / "01.md"
        from autopilot.ticket_lifecycle import assert_ticket_source_state as real_assert

        calls = 0

        def drift_after_first_check(*args, **kwargs):
            nonlocal calls
            real_assert(*args, **kwargs)
            calls += 1
            if calls == 1:
                source.write_text(source.read_text() + "\ndrift\n")

        runner = FakeGitHubRunner()
        output = io.StringIO()
        with mock.patch(
            "autopilot.cli.assert_ticket_source_state",
            side_effect=drift_after_first_check,
        ), redirect_stdout(output):
            code = cli_main(
                [
                    "resume",
                    "boundary-drift",
                    "--repo",
                    str(self.repo),
                    "--events",
                    str(events),
                ],
                command_runner=runner,
            )
        self.assertEqual(2, code)
        self.assertGreaterEqual(calls, 2)
        self.assertEqual([], runner.commands)
        self.assertIn("content differs", output.getvalue())
        self.assertEqual(before, ledger_path.read_bytes())

    def test_ignored_candidate_promotion_gates_before_commit_or_provider(self) -> None:
        ignore = self.repo / ".gitignore"
        ignore.write_text("ignored-tickets/\n")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-m", "ignore ticket source")
        folder = self.repo / "ignored-tickets"
        folder.mkdir()
        source = folder / "01.md"
        source.write_text(ticket_text("01"))
        created = self.parse(
            run(
                "run",
                str(folder),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "source-mode-drift-cli",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "source-mode-drift-cli",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        promoted = worktree / "ignored-tickets" / "01.md"
        promoted.parent.mkdir()
        promoted.write_bytes(source.read_bytes())
        git(worktree, "add", "-f", "ignored-tickets/01.md")
        tree = git(worktree, "write-tree")
        self.resume_events(
            "source-mode-drift-cli",
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
        before_head = git(worktree, "rev-parse", "HEAD")
        runner = FakeGitHubRunner()

        gated = self.resume_events_in_process(
            "source-mode-drift-cli",
            [{"operation": "delivery", "ticket_id": "01"}],
            runner,
        )

        outcome = gated["data"]["processed"][0]
        self.assertEqual("gated", outcome["result"])
        self.assertEqual("source-mode-drift", outcome["gate"])
        self.assertEqual([], runner.commands)
        self.assertEqual(before_head, git(worktree, "rev-parse", "HEAD"))
        self.assertNotIn("commit", gated["data"]["tickets"]["01"]["delivery"])
        self.assertEqual(
            "pending",
            gated["data"]["tickets"]["01"]["completion_effect"]["state"],
        )
        self.assertTrue(source.is_file())
        self.assertFalse((folder / "done").exists())
        expected_details = {
            "schema": 1,
            "ticket_id": "01",
            "snapshot_classification": "ignored",
            "observed_classification": "tracked",
            "base_classification": "ignored",
            "boundary": "git:symbolic-ref",
            "source_path": "ignored-tickets/01.md",
            "recovery": (
                "publish the source tracking change separately, then start a new "
                "run from a base where the ticket folder is tracked"
            ),
        }
        self.assertEqual(expected_details, outcome["details"])
        self.assertEqual(
            expected_details,
            gated["data"]["tickets"]["01"]["source_drift_gate"]["details"],
        )
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "source-mode-drift-cli"
            / "ledger.json"
        )
        replayed = Kernel(AtomicLedger(ledger_path).load()).report()
        self.assertEqual(
            expected_details,
            replayed["tickets"]["01"]["source_drift_gate"]["details"],
        )

    def test_granted_completion_projection_delivers_only_exact_done_source_path(self) -> None:
        ignore = self.repo / ".gitignore"
        ignore.write_text("ignored-projection/\n")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-m", "ignore projected ticket source")
        remote = Path(self.directory.name) / "projection-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
        git(self.repo, "remote", "add", "origin", str(remote))
        git(self.repo, "push", "-u", "origin", "main")
        folder = self.repo / "ignored-projection"
        folder.mkdir()
        source = folder / "01.md"
        source.write_text(ticket_text("01"))
        created = self.parse(
            run(
                "run",
                str(folder),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "completion-projection-cli",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "completion-projection-cli",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        projected = worktree / "ignored-projection" / "done" / "01.md"
        projected.parent.mkdir(parents=True)
        projected.write_bytes(source.read_bytes())
        git(worktree, "add", "-f", "ignored-projection/done/01.md")
        tree = git(worktree, "write-tree")
        self.resume_events(
            "completion-projection-cli",
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
        runner = FakeGitHubRunner()
        gated = self.resume_events_in_process(
            "completion-projection-cli",
            [{"operation": "delivery", "ticket_id": "01"}],
            runner,
        )
        self.assertEqual("source-mode-drift", gated["data"]["processed"][0]["gate"])
        self.assertEqual([], runner.commands)

        output = io.StringIO()
        with redirect_stdout(output):
            result = cli_main(
                [
                    "grant-completion-projection",
                    "completion-projection-cli",
                    "--repo",
                    str(self.repo),
                    "--ticket",
                    "01",
                    "--expected-tree",
                    tree,
                    "--actor",
                    "release-operator",
                    "--evidence",
                    "artifact://completion-projection-cli",
                ],
                command_runner=runner,
            )
        granted = json.loads(output.getvalue())
        self.assertEqual(0, result, granted)
        self.assertEqual(
            gated["data"]["tickets"]["01"]["source_drift_gate"]["gate_id"],
            granted["data"]["grant"]["resolved_gate"],
        )
        opened, _body, _prepared = self.complete_delivery(
            "completion-projection-cli", "01", runner
        )

        ticket = opened["data"]["tickets"]["01"]
        self.assertEqual("pr-open", ticket["state"])
        self.assertEqual("manual", opened["data"]["merge_policy"])
        head = ticket["pr"]["head_sha"]
        self.assertEqual(
            "ignored-projection/done/01.md",
            git(
                worktree,
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                head,
            ),
        )
        self.assertFalse(source.exists())
        self.assertEqual(
            ticket_source_digest(folder / "done" / "01.md"),
            ticket["candidate_ref"]["ticket_digest"],
        )
        self.assertTrue((folder / "done" / "01.completion.json").is_file())
        self.assertFalse(any("merge" in command for command in runner.commands))

    def test_ignored_stack_reconciliation_gates_on_tracked_target_base(self) -> None:
        ignore = self.repo / ".gitignore"
        ignore.write_text("ignored-stack/\n")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-m", "ignore stacked ticket source")
        folder = self.repo / "ignored-stack"
        folder.mkdir()
        (folder / "01.md").write_text(ticket_text("01"))
        (folder / "02.md").write_text(ticket_text("02", ("01",)))
        remote = Path(self.directory.name) / "ignored-stack-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
        git(self.repo, "remote", "add", "origin", str(remote))
        created = self.parse(
            run(
                "run",
                str(folder),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "source-mode-stack",
                "--max-leaf-interactions",
                "30",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        runner = FakeGitHubRunner()

        def verify(ticket_id: str, change: str) -> None:
            self.resume_events(
                "source-mode-stack",
                [{"operation": "activate", "ticket_id": ticket_id}],
            )
            (worktree / f"implementation-{ticket_id}.txt").write_text(change)
            git(worktree, "add", "-A")
            tree = git(worktree, "write-tree")
            self.resume_events(
                "source-mode-stack",
                [
                    {
                        "operation": "stage",
                        "ticket_id": ticket_id,
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

        verify("01", "parent\n")
        parent_opened, _parent_body, _parent_prepared = self.complete_delivery(
            "source-mode-stack", "01", runner
        )
        parent_head = parent_opened["data"]["tickets"]["01"]["pr"]["head_sha"]
        verify("02", "child\n")
        self.complete_delivery("source-mode-stack", "02", runner)

        git(self.repo, "add", "-f", "ignored-stack/done")
        git(self.repo, "commit", "-m", "publish ignored source as tracked")
        git(self.repo, "push", "origin", "main")
        self.approve_in_process("source-mode-stack", "01", parent_head, runner)
        provider_commands = len(runner.commands)

        reconciled = self.resume_events_in_process(
            "source-mode-stack",
            [{"operation": "reconcile", "ticket_id": "02"}],
            runner,
        )

        outcome = reconciled["data"]["processed"][0]
        self.assertEqual("gated", outcome["result"])
        self.assertEqual("source-mode-drift", outcome["gate"])
        self.assertEqual(provider_commands, len(runner.commands))
        self.assertEqual("git:reconcile-base", outcome["details"]["boundary"])
        self.assertEqual("ignored", outcome["details"]["snapshot_classification"])
        self.assertEqual("tracked", outcome["details"]["observed_classification"])
        self.assertEqual("tracked", outcome["details"]["base_classification"])
        self.assertEqual(
            "ignored-stack/done/02.md", outcome["details"]["source_path"]
        )
        self.assertNotIn(
            "reconcile-intent",
            reconciled["data"]["tickets"]["02"]["delivery"],
        )

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
                and event.get("stage")
                in {"review", "qa-plan", "qa-execute", "verify"}
                and event.get("result") in {"pass", "fail"}
            ):
                worktree = Path(ledger["worktree"])
                ticket_id = str(event["ticket_id"])
                fixed = candidate_ref(
                    worktree,
                    ledger["tickets"][ticket_id]["ticket_digest"],
                    base_ref=(
                        ledger["tickets"][ticket_id]
                        .get("candidate_ref", {})
                        .get("base_tree_oid", "HEAD")
                    ),
                )
                files = candidate_files(worktree, fixed)
                if fixed.candidate_tree_oid != event.get("expected_tree_oid"):
                    raise AssertionError(
                        "review fixture CandidateRef differs from expected tree"
                    )
                findings = (
                    []
                    if event["result"] == "pass"
                    else ["blocker:test: review failure fixture"]
                )
                stage = str(event["stage"])
                contract = list(LEAF_PHASE_CONTRACTS[stage])
                leaf_result: dict[str, object] = {
                    "schema": 3,
                    "complete": True,
                    "candidate_ref": {
                        "base_tree_oid": fixed.base_tree_oid,
                        "candidate_tree_oid": fixed.candidate_tree_oid,
                        "ticket_digest": fixed.ticket_digest,
                        "contract_version": fixed.contract_version,
                    },
                    "stage": stage,
                    "phase_contract": contract,
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
                }
                if stage in {"qa-plan", "qa-execute", "verify"}:
                    evidence_records = [{
                        "id": f"evidence:{stage}",
                        "artifact": f"{stage}.json",
                        "sha256": "a" * 64,
                        "result": (
                            "pass"
                            if event["result"] == "pass"
                            else "fail"
                        ),
                        "candidate_ref": leaf_result["candidate_ref"],
                    }]
                    if stage == "verify" and event["result"] == "pass":
                        bundle = verification_bundle(
                            leaf_result["candidate_ref"], ticket_id=ticket_id
                        )
                        evidence_records = []
                        for phase in ("bundle-validated", "handoff-ready"):
                            artifact_payload = {
                                "schema": 1,
                                "phase": phase,
                                "candidate_ref": leaf_result["candidate_ref"],
                                "input_hash": "fixture-input",
                                "upstream_hash": "fixture-upstream",
                                "value": bundle,
                            }
                            artifact_hash = _cache_digest(artifact_payload)
                            artifact_path = (
                                ledger_path.parent
                                / "fixture-artifacts"
                                / f"{ticket_id}-{phase}.json"
                            )
                            artifact_path.parent.mkdir(parents=True, exist_ok=True)
                            artifact_path.write_text(
                                json.dumps(
                                    {
                                        **artifact_payload,
                                        "artifact_hash": artifact_hash,
                                    },
                                    sort_keys=True,
                                    separators=(",", ":"),
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                            evidence_records.append(
                                {
                                    "id": f"verification-checkpoint:{phase}",
                                    "artifact": str(artifact_path),
                                    "sha256": artifact_hash,
                                    "result": "pass",
                                    "candidate_ref": leaf_result["candidate_ref"],
                                }
                            )
                    leaf_result["quality"] = {
                        "schema": 1,
                        "causal_scope": [stage],
                        "evidence": evidence_records,
                        "limitations": ["local-only"],
                    }
                expanded.append(
                    {
                        "operation": "leaf-result",
                        "ticket_id": ticket_id,
                        "expected_tree_oid": fixed.candidate_tree_oid,
                        "leaf_result": leaf_result,
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

    def approve_in_process(
        self,
        run_id: str,
        ticket_id: str,
        head_sha: str,
        runner: FakeGitHubRunner | FakeAzureRunner,
        *,
        external_merge: bool = False,
    ) -> dict[str, object]:
        arguments = [
            "approve",
            run_id,
            "--repo",
            str(self.repo),
            "--actor",
            "human-reviewer",
            "--evidence",
            "artifact://merge-approval",
            "--ticket",
            ticket_id,
            "--head-sha",
            head_sha,
        ]
        if external_merge:
            arguments.append("--external-merge")
        output = io.StringIO()
        with redirect_stdout(output):
            result = cli_main(arguments, command_runner=runner)
        payload = json.loads(output.getvalue())
        if result:
            raise AssertionError(payload)
        return payload

    def grant_autonomous_merge_in_process(
        self,
        run_id: str,
        runner: FakeGitHubRunner | FakeAzureRunner,
        *,
        actor: str = "release-operator",
        evidence: str = "artifact://existing-run-grant",
    ) -> dict[str, object]:
        output = io.StringIO()
        with redirect_stdout(output):
            result = cli_main(
                [
                    "grant-autonomous-merge",
                    run_id,
                    "--repo",
                    str(self.repo),
                    "--actor",
                    actor,
                    "--evidence",
                    evidence,
                ],
                command_runner=runner,
            )
        payload = json.loads(output.getvalue())
        if result:
            raise AssertionError(payload)
        return payload

    def complete_delivery(
        self,
        run_id: str,
        ticket_id: str,
        runner: FakeGitHubRunner | FakeAzureRunner,
    ) -> tuple[dict[str, object], str, dict[str, object]]:
        prepared = self.resume_events_in_process(
            run_id,
            [{"operation": "delivery", "ticket_id": ticket_id}],
            runner,
        )
        request = next(
            item
            for item in prepared["data"]["processed"]
            if item.get("result") == "render-required"
        )
        self.assertEqual("render-required", request["result"], request)
        candidate = prepared["data"]["tickets"][ticket_id]["candidate_ref"]
        bundle = verification_bundle(candidate, ticket_id=ticket_id)
        body = valid_pr_body(bundle)
        opened = self.resume_events_in_process(
            run_id,
            [
                {
                    "operation": "delivery",
                    "ticket_id": ticket_id,
                    "render_request_hash": request["render_request_hash"],
                    "expected_head_sha": request["head_sha"],
                    "rendered_body": body,
                    "verification_bundle": bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            runner,
        )
        return opened, body, prepared

    def prepare_parentless_ticket(
        self,
        run_id: str,
        *,
        candidate_path: str,
        candidate_content: str,
    ) -> tuple[Path, FakeGitHubRunner, dict[str, object]]:
        git(self.repo, "rm", "tickets/02.md")
        git(self.repo, "commit", "-m", "keep one parentless ticket")
        remote = Path(self.directory.name) / f"{run_id}-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
        git(self.repo, "remote", "add", "origin", str(remote))
        git(self.repo, "push", "-u", "origin", "main")
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                run_id,
                "--max-leaf-interactions",
                "30",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            run_id,
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / candidate_path).write_text(candidate_content)
        git(worktree, "add", "-A")
        tree = git(worktree, "write-tree")
        self.resume_events(
            run_id,
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
        runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            run_id, "01", runner
        )
        return worktree, runner, opened

    def prepare_multi_parent_join(
        self,
        run_id: str,
        *,
        candidate_path: str,
        candidate_content: str,
    ) -> tuple[Path, FakeGitHubRunner, dict[str, object]]:
        done = self.tickets / "done"
        done.mkdir()
        git(self.repo, "mv", "tickets/01.md", "tickets/done/01.md")
        git(self.repo, "mv", "tickets/02.md", "tickets/done/02.md")
        (self.tickets / "03.md").write_text(
            ticket_text("03", ("01", "02"))
        )
        git(self.repo, "add", "tickets")
        git(self.repo, "commit", "-m", "add multi-parent join")
        remote = Path(self.directory.name) / f"{run_id}-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
        git(self.repo, "remote", "add", "origin", str(remote))
        git(self.repo, "push", "-u", "origin", "main")
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                run_id,
                "--max-leaf-interactions",
                "30",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            run_id,
            [{"operation": "activate", "ticket_id": "03"}],
        )
        (worktree / candidate_path).write_text(candidate_content)
        git(worktree, "add", "-A")
        tree = git(worktree, "write-tree")
        self.resume_events(
            run_id,
            [
                {
                    "operation": "stage",
                    "ticket_id": "03",
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
        runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            run_id, "03", runner
        )
        return worktree, runner, opened

    def prepare_single_autonomous_run(
        self, run_id: str, *, provider: str = "github"
    ) -> Path:
        git(self.repo, "rm", "tickets/02.md")
        git(self.repo, "commit", "-m", "single autonomous ticket")
        remote = Path(self.directory.name) / f"{run_id}-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
        git(self.repo, "remote", "add", "origin", str(remote))
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                provider,
                "--run-id",
                run_id,
                "--merge-policy",
                "autonomous",
                "--merge-actor",
                "release-operator",
                "--merge-evidence",
                "artifact://run-merge-grant",
                "--max-leaf-interactions",
                "20",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            run_id,
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / "implementation.txt").write_text("eligible\n")
        git(worktree, "add", "-A")
        tree = git(worktree, "write-tree")
        self.resume_events(
            run_id,
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
        return worktree

    def prepare_single_manual_run(self, run_id: str) -> Path:
        git(self.repo, "rm", "tickets/02.md")
        git(self.repo, "commit", "-m", "single manual ticket")
        remote = Path(self.directory.name) / f"{run_id}-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
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
                run_id,
                "--max-leaf-interactions",
                "20",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            run_id,
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / "implementation.txt").write_text("manual retry\n")
        git(worktree, "add", "-A")
        tree = git(worktree, "write-tree")
        self.resume_events(
            run_id,
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
        return worktree

    def crash_before_queue_mutation_receipt_save(
        self,
        run_id: str,
        runner: FakeGitHubRunner,
        *,
        manual_head: str | None = None,
    ) -> None:
        original_save = AtomicLedger.save
        crashed = False

        def crash_before_save(
            store: AtomicLedger, document: dict[str, object]
        ) -> None:
            nonlocal crashed
            ticket = document["tickets"]["01"]  # type: ignore[index]
            mutation = ticket["delivery"].get("merge-mutation")  # type: ignore[index,union-attr]
            if (
                not crashed
                and isinstance(mutation, dict)
                and mutation.get("merge_mode") == "queue"
            ):
                crashed = True
                raise RuntimeError("crash before queue mutation receipt save")
            original_save(store, document)

        with mock.patch.object(
            AtomicLedger,
            "save",
            autospec=True,
            side_effect=crash_before_save,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "crash before queue mutation receipt save"
            ):
                if manual_head is None:
                    self.complete_delivery(run_id, "01", runner)
                else:
                    self.approve_in_process(run_id, "01", manual_head, runner)

        self.assertTrue(crashed)
        self.assertEqual(1, runner.queue_mutations)

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

    def test_plan_keeps_canceled_hitl_terminal_and_exposes_afk_frontier(self) -> None:
        folder = self.repo / "terminal-hitl"
        canceled = folder / "canceled"
        canceled.mkdir(parents=True)
        for ticket_id in ("WT-04", "WT-05", "WT-06"):
            (folder / f"{ticket_id}.md").write_text(ticket_text(ticket_id))
        (canceled / "WT-07.md").write_text(
            ticket_text("WT-07", mode="HITL")
        )
        git(self.repo, "add", "terminal-hitl")
        git(self.repo, "commit", "-m", "add terminal HITL fixture")

        payload = self.parse(
            run(
                "plan",
                str(folder),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                cwd=self.repo,
            )
        )

        self.assertTrue(payload["ok"])
        self.assertEqual(
            ["WT-04", "WT-05", "WT-06"], payload["data"]["ready"]
        )
        self.assertEqual([], payload["data"]["human_gates"])
        self.assertEqual(
            "pending", payload["data"]["completion_effects"]["WT-07"]["state"]
        )

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

    def test_compact_run_ledger_is_explicit_hash_preserving_and_idempotent(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "compact-cli",
                cwd=self.repo,
            )
        )
        ledger_path = Path(created["data"]["ledger"])
        store = AtomicLedger(ledger_path)
        kernel = Kernel(store.load())
        kernel.pause_run(actor="test", reason="grow a second checkpoint")
        kernel.unpause_run(actor="test", reason="resume")
        store.save(kernel.ledger)
        original_hashes = [
            event["hash"] for event in kernel.ledger["history"]
        ]

        full = copy.deepcopy(kernel.ledger)
        full["history"] = decode_history(full["history"])
        store.save(full)
        full_size = ledger_path.stat().st_size

        compacted = self.parse(
            run(
                "compact-run-ledger",
                "compact-cli",
                "--repo",
                str(self.repo),
                cwd=self.repo,
            )
        )
        stats = compacted["data"]["history_compaction"]
        self.assertTrue(stats["changed"])
        self.assertLess(stats["after_bytes"], full_size)
        loaded = AtomicLedger(ledger_path).load()
        self.assertEqual(
            original_hashes,
            [event["hash"] for event in loaded["history"]],
        )

        repeated = self.parse(
            run(
                "compact-run-ledger",
                "compact-cli",
                "--repo",
                str(self.repo),
                cwd=self.repo,
            )
        )
        self.assertFalse(
            repeated["data"]["history_compaction"]["changed"]
        )

    def test_pre_feature_schema_three_ledger_remains_manual_on_status_and_resume(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "pre-grant-schema-three",
                cwd=self.repo,
            )
        )
        ledger_path = Path(created["data"]["ledger"])
        envelope = json.loads(ledger_path.read_text())
        document = envelope["payload"]
        document.pop("merge_policy")
        document.pop("autonomous_merge_grant")
        previous_hash = "0" * 64
        for event in document["history"]:
            event["snapshot"].pop("merge_policy")
            event["snapshot"].pop("autonomous_merge_grant")
            event["previous_hash"] = previous_hash
            event.pop("hash", None)
            encoded = json.dumps(
                event,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            event["hash"] = hashlib.sha256(encoded.encode()).hexdigest()
            previous_hash = event["hash"]
        payload_text = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        envelope["integrity"] = hashlib.sha256(payload_text.encode()).hexdigest()
        ledger_path.write_text(
            json.dumps(
                envelope,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
        )

        status = self.parse(
            run(
                "status",
                "pre-grant-schema-three",
                "--repo",
                str(self.repo),
                cwd=self.repo,
            )
        )
        resumed = self.resume_events(
            "pre-grant-schema-three",
            [{"operation": "activate", "ticket_id": "01"}],
        )

        self.assertEqual("manual", status["data"]["merge_policy"])
        self.assertIsNone(status["data"]["merge_grant"])
        self.assertEqual("active", resumed["data"]["tickets"]["01"]["state"])
        self.assertNotIn(
            "autonomous_merge_grant",
            AtomicLedger(ledger_path).load(),
        )

    def test_autonomous_grant_merges_an_eligible_exact_head_without_a_prompt(self) -> None:
        self.prepare_single_autonomous_run("autonomous-test")
        runner = FakeGitHubRunner()

        delivered, _body, _prepared = self.complete_delivery(
            "autonomous-test", "01", runner
        )

        ticket = delivered["data"]["tickets"]["01"]
        self.assertEqual("integrated", ticket["state"], ticket)
        self.assertEqual("autonomous", delivered["data"]["merge_policy"])
        self.assertEqual(
            "artifact://run-merge-grant",
            delivered["data"]["merge_grant"]["evidence"],
        )
        self.assertEqual("autonomous", ticket["merge_authorization"]["mode"])
        self.assertEqual("eligible", ticket["merge_eligibility"]["status"])
        self.assertEqual(1, runner.merge_commands)
        merge_command = next(
            command
            for command in runner.commands
            if command[:3] == ["gh", "pr", "merge"]
        )
        self.assertIn("--match-head-commit", merge_command)
        self.assertNotIn("--admin", merge_command)
        self.assertTrue(
            any(
                command[:3] == ["gh", "pr", "view"]
                and "statusCheckRollup" in command[-1]
                for command in runner.commands
            )
        )
        self.assertFalse(
            any(
                command[:3] == ["gh", "pr", "checks"]
                for command in runner.commands
            )
        )

    def test_autonomous_merge_accepts_private_plan_rule_unavailability(self) -> None:
        self.prepare_single_autonomous_run("autonomous-private-free-test")
        runner = FakeGitHubRunner()
        runner.private_plan_rules_unavailable = True

        delivered, _body, _prepared = self.complete_delivery(
            "autonomous-private-free-test", "01", runner
        )

        ticket = delivered["data"]["tickets"]["01"]
        self.assertEqual("integrated", ticket["state"], ticket)
        self.assertEqual("eligible", ticket["merge_eligibility"]["status"])
        self.assertEqual(
            "feature-unavailable",
            ticket["merge_eligibility"]["checks_and_policies"]
            ["rules_observation"]["status"],
        )
        self.assertEqual(1, runner.merge_commands)
        self.assertGreaterEqual(runner.active_rule_reads, 2)

    def test_manual_merge_accepts_private_plan_rule_unavailability(self) -> None:
        self.prepare_single_manual_run("manual-private-free-test")
        runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            "manual-private-free-test", "01", runner
        )
        runner.private_plan_rules_unavailable = True
        head = opened["data"]["tickets"]["01"]["pr"]["head_sha"]

        merged = self.approve_in_process(
            "manual-private-free-test", "01", head, runner
        )

        ticket = merged["data"]["tickets"]["01"]
        self.assertEqual("integrated", ticket["state"], ticket)
        self.assertEqual(1, runner.merge_commands)
        self.assertEqual([], merged["data"]["open_gates"])

    def test_existing_manual_run_grant_continues_an_open_pr_through_exact_head_merge(
        self,
    ) -> None:
        self.prepare_single_manual_run("existing-grant-test")
        runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            "existing-grant-test", "01", runner
        )
        head_sha = opened["data"]["tickets"]["01"]["pr"]["head_sha"]
        self.assertEqual(
            "pr-open", opened["data"]["tickets"]["01"]["state"]
        )
        self.assertEqual(0, runner.merge_commands)

        granted = self.grant_autonomous_merge_in_process(
            "existing-grant-test", runner
        )

        ticket = granted["data"]["tickets"]["01"]
        self.assertEqual("integrated", ticket["state"], ticket)
        self.assertEqual("autonomous", granted["data"]["merge_policy"])
        self.assertEqual(
            "artifact://existing-run-grant",
            granted["data"]["merge_grant"]["evidence"],
        )
        self.assertFalse(granted["data"]["grant"]["replayed"])
        self.assertEqual("autonomous-merge", granted["data"]["processed"][0]["operation"])
        self.assertEqual("eligible", ticket["merge_eligibility"]["status"])
        self.assertEqual("autonomous", ticket["merge_authorization"]["mode"])
        self.assertEqual(1, runner.merge_commands)
        merge_command = next(
            command
            for command in runner.commands
            if command[:3] == ["gh", "pr", "merge"]
        )
        self.assertEqual(
            head_sha,
            merge_command[merge_command.index("--match-head-commit") + 1],
        )
        self.assertTrue(
            any(
                command[:3] == ["gh", "pr", "view"]
                and "statusCheckRollup" in command[-1]
                for command in runner.commands
            )
        )

        status = self.parse(
            run(
                "status",
                "existing-grant-test",
                "--repo",
                str(self.repo),
                cwd=self.repo,
            )
        )
        self.assertEqual(granted["data"]["merge_grant"], status["data"]["merge_grant"])
        ledger = AtomicLedger(Path(status["data"]["ledger"])).load()
        self.assertEqual(
            1,
            sum(
                event["event"] == "autonomous-merge-granted"
                for event in ledger["history"]
            ),
        )

    def test_existing_run_grant_replay_is_idempotent_and_contradiction_is_effect_free(
        self,
    ) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "existing-grant-replay-test",
                cwd=self.repo,
            )
        )
        ledger_path = Path(created["data"]["ledger"])
        runner = FakeGitHubRunner()
        first = self.grant_autonomous_merge_in_process(
            "existing-grant-replay-test", runner
        )
        stable_bytes = ledger_path.read_bytes()

        replayed = self.grant_autonomous_merge_in_process(
            "existing-grant-replay-test", runner
        )

        self.assertFalse(first["data"]["grant"]["replayed"])
        self.assertTrue(replayed["data"]["grant"]["replayed"])
        self.assertEqual(stable_bytes, ledger_path.read_bytes())
        provider_calls = list(runner.commands)
        output = io.StringIO()
        with redirect_stdout(output):
            result = cli_main(
                [
                    "grant-autonomous-merge",
                    "existing-grant-replay-test",
                    "--repo",
                    str(self.repo),
                    "--actor",
                    "another-operator",
                    "--evidence",
                    "artifact://contradictory-grant",
                ],
                command_runner=runner,
            )
        failure = json.loads(output.getvalue())
        self.assertEqual(2, result)
        self.assertIn("immutable", failure["error"]["message"])
        self.assertEqual(stable_bytes, ledger_path.read_bytes())
        self.assertEqual(provider_calls, runner.commands)

    def test_existing_run_grant_persists_before_provider_crash_and_replays_once(
        self,
    ) -> None:
        self.prepare_single_manual_run("existing-grant-crash-test")
        runner = FakeGitHubRunner()
        self.complete_delivery("existing-grant-crash-test", "01", runner)
        output = io.StringIO()
        arguments = [
            "grant-autonomous-merge",
            "existing-grant-crash-test",
            "--repo",
            str(self.repo),
            "--actor",
            "release-operator",
            "--evidence",
            "artifact://existing-run-grant",
        ]

        with mock.patch(
            "autopilot.cli._drive_autonomous_merge",
            side_effect=RuntimeError("crash after grant persistence"),
        ), redirect_stdout(output), self.assertRaisesRegex(
            RuntimeError, "crash after grant persistence"
        ):
            cli_main(arguments, command_runner=runner)

        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "existing-grant-crash-test"
            / "ledger.json"
        )
        persisted = AtomicLedger(ledger_path).load()
        self.assertEqual("autonomous", persisted["merge_policy"])
        self.assertEqual(
            "artifact://existing-run-grant",
            persisted["autonomous_merge_grant"]["evidence"],
        )
        self.assertEqual(0, runner.merge_commands)

        replayed = self.grant_autonomous_merge_in_process(
            "existing-grant-crash-test", runner
        )
        self.assertTrue(replayed["data"]["grant"]["replayed"])
        self.assertEqual(
            "integrated", replayed["data"]["tickets"]["01"]["state"]
        )
        self.assertEqual(1, runner.merge_commands)
        final = AtomicLedger(ledger_path).load()
        self.assertEqual(
            1,
            sum(
                event["event"] == "autonomous-merge-granted"
                for event in final["history"]
            ),
        )

    def test_autonomous_policy_rejects_a_missing_grant(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = cli_main(
                [
                    "run",
                    str(self.tickets),
                    "--repo",
                    str(self.repo),
                    "--provider",
                    "github",
                    "--run-id",
                    "missing-grant-test",
                    "--merge-policy",
                    "autonomous",
                ]
            )
        self.assertEqual(2, result)
        self.assertIn("requires actor and durable evidence", output.getvalue())

    def test_autonomous_merge_gates_pending_and_failed_checks_then_retries(self) -> None:
        self.prepare_single_autonomous_run("autonomous-checks-test")
        runner = FakeGitHubRunner()
        runner.merge_state_status = "UNKNOWN"
        runner.checks = [
            {
                "bucket": "pending",
                "name": "required",
                "state": "IN_PROGRESS",
                "workflow": "CI",
            }
        ]

        gated, _body, _prepared = self.complete_delivery(
            "autonomous-checks-test", "01", runner
        )

        ticket = gated["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn(
            "required checks or policies are pending",
            ticket["merge_eligibility"]["reasons"],
        )
        self.assertIn(
            "provider merge state is not clean or queue pinning is uncertain",
            ticket["merge_eligibility"]["reasons"],
        )
        self.assertEqual(0, runner.merge_commands)
        self.assertEqual(1, len(gated["data"]["open_gates"]))

        runner.merge_state_status = "CLEAN"
        runner.checks = [
            {
                "bucket": "fail",
                "name": "required",
                "state": "FAILURE",
                "workflow": "CI",
            }
        ]
        failed = self.resume_events_in_process(
            "autonomous-checks-test", [], runner
        )
        self.assertEqual(
            "gated", failed["data"]["tickets"]["01"]["state"]
        )
        self.assertIn(
            "required checks or policies failed",
            failed["data"]["tickets"]["01"]["merge_eligibility"]["reasons"],
        )
        self.assertEqual(0, runner.merge_commands)
        self.assertEqual(1, len(failed["data"]["open_gates"]))

        runner.checks = []
        recovered = self.resume_events_in_process(
            "autonomous-checks-test", [], runner
        )
        self.assertEqual(
            "integrated", recovered["data"]["tickets"]["01"]["state"]
        )
        self.assertEqual(1, runner.merge_commands)
        self.assertEqual([], recovered["data"]["open_gates"])

    def test_autonomous_merge_gates_a_malformed_checks_receipt(self) -> None:
        self.prepare_single_autonomous_run("autonomous-malformed-checks-test")
        runner = FakeGitHubRunner()
        runner.checks = [None]  # type: ignore[list-item]

        gated, _body, _prepared = self.complete_delivery(
            "autonomous-malformed-checks-test", "01", runner
        )

        ticket = gated["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn(
            "GitHub status check rollup item must be an object",
            ticket["merge_eligibility"]["reasons"],
        )
        self.assertEqual(0, runner.merge_commands)

    def test_autonomous_head_race_gates_without_adopting_unvalidated_lineage(self) -> None:
        self.prepare_single_autonomous_run("autonomous-head-race-test")
        runner = FakeGitHubRunner()
        runner.head_change_on_view = 4

        gated, _body, _prepared = self.complete_delivery(
            "autonomous-head-race-test", "01", runner
        )

        ticket = gated["data"]["tickets"]["01"]
        recorded_head = ticket["pr"]["head_sha"]
        self.assertEqual("gated", ticket["state"])
        self.assertNotEqual(runner.head_change_value, recorded_head)
        self.assertEqual(recorded_head, ticket["delivery_lineage"]["head_sha"])
        self.assertIsNone(ticket["merge_authorization"])
        self.assertEqual(0, runner.merge_commands)

        retried = self.resume_events_in_process(
            "autonomous-head-race-test", [], runner
        )
        retried_ticket = retried["data"]["tickets"]["01"]
        self.assertEqual("gated", retried_ticket["state"])
        self.assertEqual(recorded_head, retried_ticket["pr"]["head_sha"])
        self.assertEqual(0, runner.merge_commands)
        gate = next(
            gate
            for gate in retried["data"]["open_gates"]
            if gate.startswith("gate:01:")
        )
        ledger = AtomicLedger(Path(retried["data"]["ledger"])).load()
        self.assertEqual(
            "; ".join(retried_ticket["merge_eligibility"]["reasons"]),
            ledger["gates"][gate]["reason"],
        )

    def test_autonomous_merge_recovers_a_lost_mutation_response_once(self) -> None:
        self.prepare_single_autonomous_run("autonomous-recovery-test")
        runner = FakeGitHubRunner()
        runner.fail_after_merge_once = True

        gated, _body, _prepared = self.complete_delivery(
            "autonomous-recovery-test", "01", runner
        )

        ticket = gated["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertEqual("autonomous", ticket["merge_authorization"]["mode"])
        self.assertEqual(1, runner.merge_commands)

        recovered = self.resume_events_in_process(
            "autonomous-recovery-test", [], runner
        )

        self.assertEqual(
            "integrated", recovered["data"]["tickets"]["01"]["state"]
        )
        self.assertEqual(1, runner.merge_commands)

    def test_autonomous_merge_accepts_github_has_hooks_success_state(self) -> None:
        self.prepare_single_autonomous_run("autonomous-has-hooks-test")
        runner = FakeGitHubRunner()
        runner.merge_state_status = "HAS_HOOKS"

        merged, _body, _prepared = self.complete_delivery(
            "autonomous-has-hooks-test", "01", runner
        )

        self.assertEqual("integrated", merged["data"]["tickets"]["01"]["state"])
        self.assertEqual(1, runner.merge_commands)

    def test_autonomous_merge_queue_waits_and_replays_without_reenqueue(self) -> None:
        self.prepare_single_autonomous_run("autonomous-queue-test")
        runner = FakeGitHubRunner()
        runner.active_rules = [{"type": "merge_queue", "ruleset_id": 42}]

        queued, _body, _prepared = self.complete_delivery(
            "autonomous-queue-test", "01", runner
        )

        ticket = queued["data"]["tickets"]["01"]
        self.assertEqual("pr-open", ticket["state"])
        self.assertEqual("queue", ticket["delivery"]["merge-mutation"]["merge_mode"])
        self.assertEqual(1, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

        waiting = self.resume_events_in_process(
            "autonomous-queue-test", [], runner
        )
        self.assertEqual("pr-open", waiting["data"]["tickets"]["01"]["state"])
        self.assertEqual(1, runner.queue_mutations)

        pr_id = waiting["data"]["tickets"]["01"]["pr"]["pr_id"]
        head_sha = waiting["data"]["tickets"]["01"]["pr"]["head_sha"]
        runner.merge(pr_id, head_sha)
        integrated = self.resume_events_in_process(
            "autonomous-queue-test", [], runner
        )

        self.assertEqual(
            "integrated", integrated["data"]["tickets"]["01"]["state"]
        )
        self.assertEqual(1, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

    def test_autonomous_first_mutation_gates_if_merge_mode_changes_after_eligibility(
        self,
    ) -> None:
        queue_rule = {"type": "merge_queue", "ruleset_id": 42}
        run_id = "autonomous-first-mode-drift-direct-to-queue-test"
        self.prepare_single_autonomous_run(run_id)
        runner = FakeGitHubRunner()
        runner.active_rules_after_first_read = [queue_rule]

        gated, _body, _prepared = self.complete_delivery(run_id, "01", runner)

        ticket = gated["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn("merge policy changed", ticket["merge_critical_path"]["error"])
        self.assertEqual(0, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

    def test_autonomous_first_mutation_gates_if_queue_requirement_disappears(
        self,
    ) -> None:
        run_id = "autonomous-first-mode-drift-queue-to-direct-test"
        self.prepare_single_autonomous_run(run_id)
        runner = FakeGitHubRunner()
        runner.active_rules = [{"type": "merge_queue", "ruleset_id": 42}]
        runner.active_rules_after_first_read = []

        gated, _body, _prepared = self.complete_delivery(run_id, "01", runner)

        ticket = gated["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn("merge policy changed", ticket["merge_critical_path"]["error"])
        self.assertEqual(0, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

    def test_autonomous_queue_replay_never_reenqueues_a_missing_entry(self) -> None:
        self.prepare_single_autonomous_run("autonomous-queue-missing-test")
        runner = FakeGitHubRunner()
        runner.active_rules = [{"type": "merge_queue", "ruleset_id": 42}]
        queued, _body, _prepared = self.complete_delivery(
            "autonomous-queue-missing-test", "01", runner
        )
        self.assertEqual("pr-open", queued["data"]["tickets"]["01"]["state"])
        self.assertEqual(1, runner.queue_mutations)

        runner.queue_entries.clear()
        gated = self.resume_events_in_process(
            "autonomous-queue-missing-test", [], runner
        )

        self.assertEqual("gated", gated["data"]["tickets"]["01"]["state"])
        self.assertIn(
            "previously applied queue entry is no longer observable",
            gated["data"]["tickets"]["01"]["merge_critical_path"]["error"],
        )
        self.assertEqual(1, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

    def test_autonomous_queue_crash_never_falls_back_to_direct_merge(self) -> None:
        self.prepare_single_autonomous_run("autonomous-queue-policy-drift-test")
        runner = FakeGitHubRunner()
        runner.active_rules = [{"type": "merge_queue", "ruleset_id": 42}]
        self.crash_before_queue_mutation_receipt_save(
            "autonomous-queue-policy-drift-test", runner
        )
        runner.active_rules = []
        resumed = self.resume_events_in_process(
            "autonomous-queue-policy-drift-test", [], runner
        )

        ticket = resumed["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn(
            "queue",
            ticket["merge_critical_path"]["error"].casefold(),
        )
        self.assertEqual(1, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

    def test_autonomous_queue_crash_with_missing_entry_never_reenqueues(self) -> None:
        self.prepare_single_autonomous_run("autonomous-queue-missing-receipt-test")
        runner = FakeGitHubRunner()
        runner.active_rules = [{"type": "merge_queue", "ruleset_id": 42}]
        self.crash_before_queue_mutation_receipt_save(
            "autonomous-queue-missing-receipt-test", runner
        )
        runner.queue_entries.clear()
        resumed = self.resume_events_in_process(
            "autonomous-queue-missing-receipt-test", [], runner
        )

        ticket = resumed["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn(
            "no durable mutation receipt",
            ticket["merge_critical_path"]["error"],
        )
        self.assertEqual(1, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

    def test_autonomous_queue_crash_before_mutation_gates_ambiguous_dispatch(self) -> None:
        self.prepare_single_autonomous_run("autonomous-queue-before-mutation-test")
        runner = FakeGitHubRunner()
        runner.active_rules = [{"type": "merge_queue", "ruleset_id": 42}]
        runner.crash_before_queue_mutation_once = True

        with self.assertRaisesRegex(
            RuntimeError, "crash before queue provider mutation"
        ):
            self.complete_delivery(
                "autonomous-queue-before-mutation-test", "01", runner
            )

        self.assertEqual(0, runner.queue_mutations)
        resumed = self.resume_events_in_process(
            "autonomous-queue-before-mutation-test", [], runner
        )

        ticket = resumed["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn(
            "no durable mutation receipt",
            ticket["merge_critical_path"]["error"],
        )
        self.assertEqual(0, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

    def test_autonomous_retry_rechecks_policies_before_a_second_mutation(self) -> None:
        self.prepare_single_autonomous_run("autonomous-recheck-test")
        runner = FakeGitHubRunner()
        runner.fail_merge_before_apply_once = True
        gated, _body, _prepared = self.complete_delivery(
            "autonomous-recheck-test", "01", runner
        )
        self.assertEqual("gated", gated["data"]["tickets"]["01"]["state"])
        self.assertEqual(1, runner.merge_commands)

        runner.checks = [
            {
                "bucket": "fail",
                "name": "required",
                "state": "FAILURE",
                "workflow": "CI",
            }
        ]
        blocked = self.resume_events_in_process(
            "autonomous-recheck-test", [], runner
        )

        self.assertEqual("gated", blocked["data"]["tickets"]["01"]["state"])
        self.assertIn(
            "required checks or policies failed",
            blocked["data"]["tickets"]["01"]["merge_eligibility"]["reasons"],
        )
        self.assertEqual(1, runner.merge_commands)

        runner.checks = []
        recovered = self.resume_events_in_process(
            "autonomous-recheck-test", [], runner
        )
        self.assertEqual(
            "integrated", recovered["data"]["tickets"]["01"]["state"]
        )
        self.assertEqual(2, runner.merge_commands)

    def test_autonomous_merge_gates_a_provider_without_atomic_expected_head(self) -> None:
        self.prepare_single_autonomous_run(
            "autonomous-unsupported-provider-test",
            provider="azure-devops",
        )
        runner = FakeAzureRunner()

        gated, _body, _prepared = self.complete_delivery(
            "autonomous-unsupported-provider-test", "01", runner
        )

        ticket = gated["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn(
            "merge-with-expected-head",
            ticket["merge_eligibility"]["reasons"][0],
        )
        self.assertFalse(
            any(
                command[:4] == ["az", "repos", "pr", "update"]
                for command in runner.commands
            )
        )

    def test_ticket_scoped_autonomous_gate_does_not_freeze_unrelated_afk_work(self) -> None:
        (self.tickets / "02.md").write_text(ticket_text("02"))
        git(self.repo, "add", "tickets/02.md")
        git(self.repo, "commit", "-m", "make tickets independent")
        remote = Path(self.directory.name) / "autonomous-independent-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
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
                "autonomous-independent-test",
                "--merge-policy",
                "autonomous",
                "--merge-actor",
                "release-operator",
                "--merge-evidence",
                "artifact://run-merge-grant",
                "--max-leaf-interactions",
                "20",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "autonomous-independent-test",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / "implementation.txt").write_text("first\n")
        git(worktree, "add", "-A")
        tree = git(worktree, "write-tree")
        self.resume_events(
            "autonomous-independent-test",
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
        runner = FakeGitHubRunner()
        runner.checks = [
            {
                "bucket": "pending",
                "name": "required",
                "state": "IN_PROGRESS",
                "workflow": "CI",
            }
        ]
        gated, _body, _prepared = self.complete_delivery(
            "autonomous-independent-test", "01", runner
        )
        self.assertEqual("gated", gated["data"]["tickets"]["01"]["state"])

        continued = self.resume_events_in_process(
            "autonomous-independent-test",
            [{"operation": "activate", "ticket_id": "02"}],
            runner,
        )

        self.assertEqual("active", continued["data"]["tickets"]["02"]["state"])
        self.assertEqual("gated", continued["data"]["tickets"]["01"]["state"])
        self.assertEqual(0, runner.merge_commands)

    def test_autonomous_stack_reconciles_new_head_and_merges_child_without_revalidation(self) -> None:
        remote = Path(self.directory.name) / "autonomous-stack-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
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
                "autonomous-stack-test",
                "--merge-policy",
                "autonomous",
                "--merge-actor",
                "release-operator",
                "--merge-evidence",
                "artifact://stack-grant",
                "--max-leaf-interactions",
                "30",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])

        def advance(ticket_id: str, path: str, content: str) -> None:
            self.resume_events(
                "autonomous-stack-test",
                [{"operation": "activate", "ticket_id": ticket_id}],
            )
            (worktree / path).write_text(content)
            git(worktree, "add", "-A")
            tree = git(worktree, "write-tree")
            self.resume_events(
                "autonomous-stack-test",
                [
                    {
                        "operation": "stage",
                        "ticket_id": ticket_id,
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

        runner = FakeGitHubRunner()
        runner.checks = [
            {
                "bucket": "pending",
                "name": "required",
                "state": "IN_PROGRESS",
                "workflow": "CI",
            }
        ]
        advance("01", "parent.txt", "parent\n")
        parent_gated, _parent_body, _parent_prepared = self.complete_delivery(
            "autonomous-stack-test", "01", runner
        )
        parent = parent_gated["data"]["tickets"]["01"]
        self.assertEqual("gated", parent["state"])

        advance("02", "child.txt", "child\n")
        child_gated, _child_body, _child_prepared = self.complete_delivery(
            "autonomous-stack-test", "02", runner
        )
        child = child_gated["data"]["tickets"]["02"]
        self.assertEqual("pr-open", child["state"])
        self.assertEqual(parent["pr"]["branch"], child["delivery_lineage"]["base_branch"])
        runner.checks_by_pr[parent["pr"]["pr_id"]] = runner.checks
        runner.checks_by_pr[child["pr"]["pr_id"]] = []
        ledger_path = Path(child_gated["data"]["ledger"])
        store = AtomicLedger(ledger_path)
        kernel = Kernel(store.load())
        self.assertEqual("01", kernel.pending_autonomous_merge_id())
        grant = child_gated["data"]["merge_grant"]

        old_intent = _merge_intent_key(
            provider="github",
            pr_id=child["pr"]["pr_id"],
            head_sha=child["pr"]["head_sha"],
            actor=grant["actor"],
            evidence=grant["evidence"],
            mode="autonomous",
        )
        kernel.record_delivery_metadata(
            "02",
            "merge-intent",
            {
                "schema": 1,
                "intent_key": old_intent,
                "provider": "github",
                "pr_id": child["pr"]["pr_id"],
                "actor": grant["actor"],
                "head_sha": child["pr"]["head_sha"],
                "evidence": grant["evidence"],
                "mode": "autonomous",
            },
        )
        kernel.authorize_merge(
            "02",
            actor=grant["actor"],
            head_sha=child["pr"]["head_sha"],
            evidence=grant["evidence"],
            mode="autonomous",
        )
        kernel.record_delivery_metadata(
            "02",
            "merge-attempt",
            {
                "schema": 1,
                "intent_key": old_intent,
                "provider": "github",
                "pr_id": child["pr"]["pr_id"],
                "head_sha": child["pr"]["head_sha"],
                "attempted_at": "2026-08-05T00:00:00+00:00",
                "attempted_at_ns": 1,
            },
        )
        kernel.record_delivery_metadata(
            "02",
            "merge-progress",
            {
                "schema": 1,
                "phase": "provider",
                "status": "gated",
                "head_sha": child["pr"]["head_sha"],
                "intent_key": old_intent,
                "started_at": "2026-08-05T00:00:00+00:00",
                "started_at_ns": 1,
                "updated_at": "2026-08-05T00:00:01+00:00",
                "updated_at_ns": 2,
                "error": "merge failed before mutation",
            },
        )
        kernel.open_gate(
            "02",
            "provider-merge",
            scope="ticket",
            reason="merge failed before mutation",
        )
        store.save(kernel.ledger)
        child_old_head = child["pr"]["head_sha"]
        child_interactions = child["verbosity"]["leaf_interactions"]

        stale_main = git(self.repo, "rev-parse", "main")
        integrated_main = git(
            self.repo,
            "commit-tree",
            f"{parent['pr']['head_sha']}^{{tree}}",
            "-p",
            stale_main,
            "-m",
            "simulate provider parent integration",
        )
        git(
            self.repo,
            "push",
            "origin",
            f"{integrated_main}:refs/heads/main",
        )
        runner.checks_by_pr[parent["pr"]["pr_id"]] = []
        reconcile_prepared = self.resume_events_in_process(
            "autonomous-stack-test",
            [
                {"operation": "reconcile", "ticket_id": "02"},
                {"operation": "reconcile", "ticket_id": "02"},
            ],
            runner,
        )
        render_request = next(
            item
            for item in reconcile_prepared["data"]["processed"]
            if item.get("result") == "render-required"
        )
        new_head = render_request["head_sha"]
        bundle = verification_bundle(
            reconcile_prepared["data"]["tickets"]["02"]["candidate_ref"],
            ticket_id="02",
        )
        stale_body = valid_pr_body(bundle)
        rejected_body = self.resume_events_in_process(
            "autonomous-stack-test",
            [
                {
                    "operation": "reconcile",
                    "ticket_id": "02",
                    "render_request_hash": render_request["render_request_hash"],
                    "expected_head_sha": new_head,
                    "rendered_body": stale_body,
                    "verification_bundle": bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            runner,
        )
        body_gate = rejected_body["data"]["processed"][0]
        self.assertEqual("gated", body_gate["result"])
        self.assertIn("exact new head SHA", body_gate["reason"])
        self.assertEqual(1, runner.merge_commands)
        self.assertNotIn(
            new_head,
            runner.prs[child["pr"]["pr_id"]]["body"],
        )
        self.parse(
            run(
                "approve",
                "autonomous-stack-test",
                body_gate["gate_id"],
                "--repo",
                str(self.repo),
                "--actor",
                "qa",
                "--evidence",
                "fresh reconciled body supplied",
                cwd=self.repo,
            )
        )
        rebound_body = valid_pr_body(bundle, expected_head_sha=new_head)
        self.assertIn(new_head, rebound_body)
        self.assertNotIn(child_old_head, rebound_body)
        render_event = {
            "operation": "reconcile",
            "ticket_id": "02",
            "render_request_hash": render_request["render_request_hash"],
            "expected_head_sha": new_head,
            "rendered_body": rebound_body,
            "verification_bundle": bundle,
            "verification_audit_root": str(ROOT / "verification-audit"),
        }
        original_save = AtomicLedger.save
        crashed_before_rebind_save = False

        def crash_before_rebind_save(
            store_to_save: AtomicLedger, document: dict[str, object]
        ) -> None:
            nonlocal crashed_before_rebind_save
            ticket = document["tickets"]["02"]  # type: ignore[index]
            body_record = ticket["delivery"].get("pr-body")  # type: ignore[index]
            if (
                not crashed_before_rebind_save
                and isinstance(body_record, dict)
                and body_record.get("schema") == 2
                and body_record.get("expected_head_sha") == new_head
            ):
                crashed_before_rebind_save = True
                raise RuntimeError("simulated crash before atomic body rebind save")
            original_save(store_to_save, document)

        with mock.patch.object(
            AtomicLedger, "save", new=crash_before_rebind_save
        ), self.assertRaisesRegex(
            RuntimeError, "simulated crash before atomic body rebind save"
        ):
            self.resume_events_in_process(
                "autonomous-stack-test", [render_event], runner
            )
        self.assertTrue(crashed_before_rebind_save)
        after_crash = AtomicLedger(ledger_path).load()["tickets"]["02"]["delivery"]
        self.assertEqual(1, after_crash["pr-body"]["schema"])
        self.assertEqual(child_old_head, after_crash["pr-body"]["expected_head_sha"])
        self.assertNotIn("lineage_rebinds", after_crash["pr-body"])
        self.assertEqual(
            render_request["render_request_hash"],
            after_crash["reconcile-pr-body-request"]["request_hash"],
        )
        provider_mutation_start = len(runner.commands)
        with mock.patch(
            "autopilot.cli._drive_autonomous_merge",
            return_value={"result": "deferred"},
        ):
            reconciled = self.resume_events_in_process(
                "autonomous-stack-test",
                [render_event],
                runner,
            )
        reconciled_child = reconciled["data"]["tickets"]["02"]
        self.assertEqual("pr-open", reconciled_child["state"])
        self.assertEqual(2, reconciled_child["delivery"]["pr-body"]["schema"])
        valid_rebind_receipt = copy.deepcopy(
            reconciled_child["delivery"]["pr-body"]
        )
        kernel = Kernel(store.load())
        forged_schema_one = copy.deepcopy(valid_rebind_receipt)
        forged_schema_one["schema"] = 1
        forged_schema_one.pop("lineage_rebinds")
        kernel.record_delivery_metadata("02", "pr-body", forged_schema_one)
        with self.assertRaisesRegex(
            LedgerError,
            "PR-body lineage cannot be downgraded",
        ):
            store.save(kernel.ledger)
        self.assertEqual(1, runner.merge_commands)
        progressed = self.resume_events_in_process(
            "autonomous-stack-test", [], runner
        )

        final_parent = progressed["data"]["tickets"]["01"]
        final_child = progressed["data"]["tickets"]["02"]
        self.assertEqual("integrated", final_parent["state"])
        self.assertEqual("integrated", final_child["state"])
        self.assertEqual(2, runner.merge_commands)
        self.assertEqual(grant, progressed["data"]["merge_grant"])
        self.assertNotEqual(child_old_head, final_child["pr"]["head_sha"])
        self.assertEqual(
            final_child["pr"]["head_sha"],
            final_child["merge_eligibility"]["head_sha"],
        )
        self.assertEqual(
            final_child["pr"]["head_sha"],
            final_child["delivery"]["pr-body"]["expected_head_sha"],
        )
        self.assertEqual(2, final_child["delivery"]["pr-body"]["schema"])
        body_rebind = final_child["delivery"]["pr-body"]["lineage_rebinds"][-1]
        self.assertEqual(child_old_head, body_rebind["old_head"])
        self.assertEqual(final_child["pr"]["head_sha"], body_rebind["new_head"])
        self.assertEqual(
            child_old_head,
            body_rebind["old_receipt"]["expected_head_sha"],
        )
        self.assertEqual(
            rebound_body,
            runner.prs[final_child["pr"]["pr_id"]]["body"],
        )
        provider_mutations = runner.commands[provider_mutation_start:]
        retarget_patches = [
            command
            for command in provider_mutations
            if command[:3]
            == [
                "gh",
                "api",
                f"repos/{{owner}}/{{repo}}/pulls/{final_child['pr']['pr_id']}",
            ]
        ]
        self.assertEqual(1, len(retarget_patches))
        self.assertIn("PATCH", retarget_patches[0])
        self.assertIn("base=main", retarget_patches[0])
        self.assertIn(f"body={rebound_body}", retarget_patches[0])
        self.assertFalse(
            any(
                command[:3] == ["gh", "pr", "edit"]
                for command in provider_mutations
            )
        )
        lineage_history = final_child["delivery"]["merge-lineage-history"]
        self.assertEqual(child_old_head, lineage_history[-1]["old_head"])
        self.assertEqual(final_child["pr"]["head_sha"], lineage_history[-1]["new_head"])
        self.assertEqual(old_intent, lineage_history[-1]["receipts"]["merge-intent"]["intent_key"])
        self.assertNotEqual(
            old_intent,
            final_child["delivery"]["merge-intent"]["intent_key"],
        )
        self.assertEqual(
            child_interactions,
            final_child["verbosity"]["leaf_interactions"],
        )
        self.assertTrue(
            any(
                event["event"] == "reconciliation-equivalent"
                and event["ticket_id"] == "02"
                for event in AtomicLedger(
                    Path(progressed["data"]["ledger"])
                ).load()["history"]
            )
        )

    def test_parentless_ticket_reconciles_an_advancing_delivery_base(self) -> None:
        _worktree, runner, opened = self.prepare_parentless_ticket(
            "parentless-reconcile-test",
            candidate_path="candidate.txt",
            candidate_content="candidate\n",
        )
        before = opened["data"]["tickets"]["01"]
        old_head = before["pr"]["head_sha"]
        old_base = before["delivery_lineage"]["base_sha"]

        git(self.repo, "commit", "--allow-empty", "-m", "advance main")
        new_base = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "push", "origin", "main")

        prepared = self.resume_events_in_process(
            "parentless-reconcile-test",
            [
                {"operation": "reconcile", "ticket_id": "01"},
                {"operation": "reconcile", "ticket_id": "01"},
            ],
            runner,
        )
        render_request = next(
            item
            for item in prepared["data"]["processed"]
            if item.get("result") == "render-required"
        )
        ticket = prepared["data"]["tickets"]["01"]
        intent = ticket["delivery"]["reconcile-intent"]
        self.assertEqual("base-advance", intent["mode"])
        self.assertEqual("main", intent["parent_branch"])
        self.assertEqual(old_base, intent["parent_head"])
        self.assertEqual("main", intent["target_base"]["branch"])
        self.assertEqual(new_base, intent["target_base"]["sha"])
        self.assertEqual("verified", ticket["state"])

        new_head = render_request["head_sha"]
        bundle = verification_bundle(ticket["candidate_ref"], ticket_id="01")
        reconciled = self.resume_events_in_process(
            "parentless-reconcile-test",
            [
                {
                    "operation": "reconcile",
                    "ticket_id": "01",
                    "render_request_hash": render_request[
                        "render_request_hash"
                    ],
                    "expected_head_sha": new_head,
                    "rendered_body": valid_pr_body(
                        bundle, expected_head_sha=new_head
                    ),
                    "verification_bundle": bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            runner,
        )
        final = reconciled["data"]["tickets"]["01"]
        self.assertEqual("pr-open", final["state"])
        self.assertNotEqual(old_head, final["pr"]["head_sha"])
        self.assertEqual(new_base, final["delivery_lineage"]["base_sha"])
        self.assertEqual(new_head, runner.prs[final["pr"]["pr_id"]]["headRefOid"])

    def test_multi_parent_join_reconciles_an_advancing_delivery_base(self) -> None:
        worktree, runner, opened = self.prepare_multi_parent_join(
            "multi-parent-reconcile-test",
            candidate_path="join.txt",
            candidate_content="join\n",
        )
        before = opened["data"]["tickets"]["03"]
        old_head = before["pr"]["head_sha"]
        old_base = before["delivery_lineage"]["base_sha"]

        git(self.repo, "commit", "--allow-empty", "-m", "advance main")
        new_base = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "push", "origin", "main")

        prepared = self.resume_events_in_process(
            "multi-parent-reconcile-test",
            [
                {"operation": "reconcile", "ticket_id": "03"},
                {"operation": "reconcile", "ticket_id": "03"},
            ],
            runner,
        )
        render_request = next(
            item
            for item in prepared["data"]["processed"]
            if item.get("result") == "render-required"
        )
        ticket = prepared["data"]["tickets"]["03"]
        intent = ticket["delivery"]["reconcile-intent"]
        self.assertEqual("base-advance", intent["mode"])
        self.assertEqual(old_base, intent["parent_head"])
        self.assertEqual("main", intent["target_base"]["branch"])
        self.assertEqual(new_base, intent["target_base"]["sha"])
        self.assertEqual("verified", ticket["state"])

        new_head = render_request["head_sha"]
        bundle = verification_bundle(ticket["candidate_ref"], ticket_id="03")
        reconciled = self.resume_events_in_process(
            "multi-parent-reconcile-test",
            [
                {
                    "operation": "reconcile",
                    "ticket_id": "03",
                    "render_request_hash": render_request[
                        "render_request_hash"
                    ],
                    "expected_head_sha": new_head,
                    "rendered_body": valid_pr_body(
                        bundle, expected_head_sha=new_head
                    ),
                    "verification_bundle": bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            runner,
        )
        final = reconciled["data"]["tickets"]["03"]
        self.assertEqual("pr-open", final["state"])
        self.assertNotEqual(old_head, final["pr"]["head_sha"])
        self.assertEqual(new_base, final["delivery_lineage"]["base_sha"])
        self.assertEqual(new_head, runner.prs[final["pr"]["pr_id"]]["headRefOid"])

    def test_multi_parent_join_resumes_after_an_explicit_conflict_resolution(self) -> None:
        worktree, runner, opened = self.prepare_multi_parent_join(
            "multi-parent-conflict-test",
            candidate_path="shared.txt",
            candidate_content="candidate\n",
        )
        before = opened["data"]["tickets"]["03"]
        old_head = before["pr"]["head_sha"]
        old_base = before["delivery_lineage"]["base_sha"]

        (self.repo / "shared.txt").write_text("upstream\n")
        git(self.repo, "add", "shared.txt")
        git(self.repo, "commit", "-m", "advance main with conflict")
        new_base = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "push", "origin", "main")

        failed = self.resume_events_in_process(
            "multi-parent-conflict-test",
            [{"operation": "reconcile", "ticket_id": "03"}],
            runner,
        )
        outcome = failed["data"]["processed"][0]
        self.assertEqual("gated", outcome["result"])
        self.assertIn("could not apply", outcome["reason"])
        failed_ticket = failed["data"]["tickets"]["03"]
        self.assertEqual("base-advance", failed_ticket["delivery"]["reconcile-intent"]["mode"])
        self.assertEqual(old_head, git(worktree, "rev-parse", "HEAD"))
        self.assertEqual("", git(worktree, "status", "--short"))

        rebase = subprocess.run(
            [
                "git",
                "rebase",
                "--onto",
                new_base,
                old_base,
                failed_ticket["pr"]["branch"],
            ],
            cwd=worktree,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, rebase.returncode)
        self.assertIn("CONFLICT", rebase.stdout + rebase.stderr)
        (worktree / "shared.txt").write_text("resolved\n")
        git(worktree, "add", "shared.txt")
        continued = subprocess.run(
            ["git", "-c", "core.editor=true", "rebase", "--continue"],
            cwd=worktree,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, continued.returncode, continued.stderr)
        resolved_head = git(worktree, "rev-parse", "HEAD")
        self.assertNotEqual(old_head, resolved_head)
        self.parse(
            run(
                "approve",
                "multi-parent-conflict-test",
                outcome["gate_id"],
                "--repo",
                str(self.repo),
                "--actor",
                "operator",
                "--evidence",
                "artifact://multi-parent-conflict-resolution",
                cwd=self.repo,
            )
        )

        invalidated = self.resume_events_in_process(
            "multi-parent-conflict-test",
            [{"operation": "reconcile", "ticket_id": "03"}],
            runner,
        )
        invalidation = invalidated["data"]["processed"][0]
        self.assertEqual("revalidation-required", invalidation["result"])
        self.assertEqual("active", invalidated["data"]["tickets"]["03"]["state"])
        candidate_tree = invalidation["tree_oid"]
        self.resume_events(
            "multi-parent-conflict-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "03",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": candidate_tree,
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
        prepared = self.resume_events_in_process(
            "multi-parent-conflict-test",
            [{"operation": "reconcile", "ticket_id": "03"}],
            runner,
        )
        render_request = prepared["data"]["processed"][0]
        self.assertEqual("render-required", render_request["result"])
        candidate = prepared["data"]["tickets"]["03"]["candidate_ref"]
        bundle = verification_bundle(candidate, ticket_id="03")
        reconciled = self.resume_events_in_process(
            "multi-parent-conflict-test",
            [
                {
                    "operation": "reconcile",
                    "ticket_id": "03",
                    "render_request_hash": render_request[
                        "render_request_hash"
                    ],
                    "expected_head_sha": render_request["head_sha"],
                    "rendered_body": valid_pr_body(
                        bundle,
                        expected_head_sha=render_request["head_sha"],
                    ),
                    "verification_bundle": bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            runner,
        )
        final = reconciled["data"]["tickets"]["03"]
        self.assertEqual("pr-open", final["state"])
        self.assertEqual(new_base, final["delivery_lineage"]["base_sha"])
        self.assertEqual(
            render_request["head_sha"],
            runner.prs[final["pr"]["pr_id"]]["headRefOid"],
        )
        self.assertEqual(
            render_request["head_sha"],
            final["delivery"]["pr-body"]["expected_head_sha"],
        )

    def test_semantic_stack_reconciliation_refreshes_advancing_target_and_rebinds_bundle(self) -> None:
        remote = Path(self.directory.name) / "semantic-rebind-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
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
                "semantic-rebind-test",
                "--merge-policy",
                "autonomous",
                "--merge-actor",
                "release-operator",
                "--merge-evidence",
                "artifact://semantic-rebind-grant",
                "--max-leaf-interactions",
                "30",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])

        def advance(ticket_id: str, path: str, content: str) -> None:
            self.resume_events(
                "semantic-rebind-test",
                [{"operation": "activate", "ticket_id": ticket_id}],
            )
            (worktree / path).write_text(content)
            git(worktree, "add", "-A")
            tree = git(worktree, "write-tree")
            self.resume_events(
                "semantic-rebind-test",
                [
                    {
                        "operation": "stage",
                        "ticket_id": ticket_id,
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

        runner = FakeGitHubRunner()
        runner.checks = [
            {
                "bucket": "pending",
                "name": "required",
                "state": "IN_PROGRESS",
                "workflow": "CI",
            }
        ]
        advance("01", "parent.txt", "parent\n")
        parent_gated, _parent_body, _parent_prepared = self.complete_delivery(
            "semantic-rebind-test", "01", runner
        )
        parent = parent_gated["data"]["tickets"]["01"]
        self.assertEqual("gated", parent["state"])

        advance("02", "child.txt", "child\n")
        child_opened, _child_body, _child_prepared = self.complete_delivery(
            "semantic-rebind-test", "02", runner
        )
        child = child_opened["data"]["tickets"]["02"]
        self.assertEqual("pr-open", child["state"])
        old_candidate = copy.deepcopy(child["candidate_ref"])
        old_generation = child["artifact_generation"]
        old_receipt = copy.deepcopy(child["delivery"]["pr-body"])
        old_bundle = json.loads(
            Path(old_receipt["bundle_path"]).read_text(encoding="utf-8")
        )
        runner.checks_by_pr[parent["pr"]["pr_id"]] = []
        runner.checks_by_pr[child["pr"]["pr_id"]] = []

        extra_blob = subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=self.repo,
            input="provider adjustment\n",
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        parent_tree = subprocess.run(
            ["git", "ls-tree", f"{parent['pr']['head_sha']}^{{tree}}"],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        integrated_tree = subprocess.run(
            ["git", "mktree"],
            cwd=self.repo,
            input=(
                parent_tree
                + f"100644 blob {extra_blob}\tprovider-adjustment.txt\n"
            ),
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        stale_main = git(self.repo, "rev-parse", "main")
        integrated_main = git(
            self.repo,
            "commit-tree",
            integrated_tree,
            "-p",
            stale_main,
            "-m",
            "simulate semantic provider parent integration",
        )
        git(
            self.repo,
            "push",
            "origin",
            f"{integrated_main}:refs/heads/main",
        )

        prepared = self.resume_events_in_process(
            "semantic-rebind-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            runner,
        )
        prepare_event = next(
            item
            for item in prepared["data"]["processed"]
            if item.get("ticket_id") == "02"
        )
        self.assertEqual("revalidation-required", prepare_event["result"])
        prepared_child = prepared["data"]["tickets"]["02"]
        self.assertEqual("active", prepared_child["state"])
        self.assertEqual("review", prepared_child["stage"])
        self.assertEqual(old_generation + 1, prepared_child["artifact_generation"])
        self.assertNotEqual(old_candidate, prepared_child["candidate_ref"])
        self.assertNotIn("verify", prepared_child.get("leaf_results", {}))

        (worktree / "child.txt").write_text("child corrected during review\n")
        git(worktree, "add", "-A")
        corrected_tree = git(worktree, "write-tree")
        invalidated = self.resume_events(
            "semantic-rebind-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "02",
                    "stage": "review",
                    "result": "pass",
                    "expected_tree_oid": corrected_tree,
                }
            ],
        )
        invalidation_event = invalidated["data"]["processed"][0]
        self.assertEqual("invalidated", invalidation_event["result"])
        self.assertEqual("implement", invalidated["data"]["tickets"]["02"]["stage"])

        self.resume_events(
            "semantic-rebind-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "02",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": corrected_tree,
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
        ledger_path = Path(prepared["data"]["ledger"])
        corrected_ledger = AtomicLedger(ledger_path).load()
        corrected = corrected_ledger["tickets"]["02"]
        self.assertEqual(corrected_tree, corrected["candidate_ref"]["candidate_tree_oid"])
        self.assertNotEqual(
            corrected["candidate_ref"], corrected["delivery_candidate_ref"]
        )
        corrected_generation = corrected["artifact_generation"]
        corrected_leaf_results = copy.deepcopy(corrected["leaf_results"])
        prior_candidate_seal_events = len(
            [
                event
                for event in corrected_ledger["history"]
                if event["event"] == "reconciliation-candidate-sealed"
                and event["ticket_id"] == "02"
            ]
        )
        old_prepared_head = corrected["delivery"]["reconcile-prepare"]["new_head"]
        git(worktree, "commit", "-m", "operator seal without runner marker")
        unexpected_head = git(worktree, "rev-parse", "HEAD")
        provider_command_count = len(runner.commands)

        recovery_gated = self.resume_events_in_process(
            "semantic-rebind-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            runner,
        )
        recovery_event = recovery_gated["data"]["processed"][0]
        self.assertEqual("gated", recovery_event["result"])
        self.assertEqual("stack-reconciliation-recovery", recovery_event["gate"])
        recovery_details = recovery_event["details"]
        self.assertEqual(1, recovery_details["schema"])
        self.assertEqual("unexpected-local-head", recovery_details["reason"])
        self.assertEqual(child["pr"]["branch"], recovery_details["branch"])
        self.assertEqual(str(worktree.resolve()), recovery_details["worktree"])
        self.assertEqual(old_prepared_head, recovery_details["expected_head"])
        self.assertEqual(unexpected_head, recovery_details["observed_head"])
        self.assertEqual(corrected_tree, recovery_details["candidate_tree_oid"])
        recovery = recovery_details["recovery"]
        self.assertEqual("human-repair-required", recovery["disposition"])
        self.assertEqual(
            f"git branch {recovery['backup_ref']} {unexpected_head}",
            recovery["preserve_command"],
        )
        self.assertEqual(
            f"git reset --soft {old_prepared_head}",
            recovery["restore_command"],
        )
        self.assertEqual("git write-tree", recovery["tree_proof_command"])
        self.assertEqual(corrected_tree, recovery["expected_tree_oid"])
        persisted_recovery_gate = AtomicLedger(ledger_path).load()["gates"][
            recovery_event["gate_id"]
        ]
        self.assertEqual(recovery_details, persisted_recovery_gate["details"])
        self.assertEqual(unexpected_head, git(worktree, "rev-parse", "HEAD"))
        self.assertEqual(provider_command_count, len(runner.commands))

        self.parse(
            run(
                "approve",
                "semantic-rebind-test",
                recovery_event["gate_id"],
                "--repo",
                str(self.repo),
                "--actor",
                "operator",
                "--evidence",
                "artifact://seal-recovery-attempt",
                cwd=self.repo,
            )
        )
        repeated = self.resume_events_in_process(
            "semantic-rebind-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            runner,
        )
        repeated_event = repeated["data"]["processed"][0]
        self.assertEqual("gated", repeated_event["result"])
        self.assertEqual(
            "stack-reconciliation-recovery", repeated_event["gate"]
        )
        self.assertNotEqual(recovery_event["gate_id"], repeated_event["gate_id"])
        self.assertEqual(unexpected_head, git(worktree, "rev-parse", "HEAD"))
        self.assertEqual(provider_command_count, len(runner.commands))

        git(
            worktree,
            "branch",
            recovery["backup_ref"],
            unexpected_head,
        )
        git(worktree, "reset", "--soft", old_prepared_head)
        self.assertEqual(corrected_tree, git(worktree, "write-tree"))
        self.parse(
            run(
                "approve",
                "semantic-rebind-test",
                repeated_event["gate_id"],
                "--repo",
                str(self.repo),
                "--actor",
                "operator",
                "--evidence",
                "artifact://seal-recovery-complete",
                cwd=self.repo,
            )
        )
        with mock.patch(
            "autopilot.cli.Kernel.seal_revalidated_reconciliation_candidate",
            side_effect=RuntimeError("crash after reconciliation candidate commit"),
        ), self.assertRaisesRegex(
            RuntimeError, "crash after reconciliation candidate commit"
        ):
            self.resume_events_in_process(
                "semantic-rebind-test",
                [{"operation": "reconcile", "ticket_id": "02"}],
                runner,
            )
        committed_replay_head = git(worktree, "rev-parse", "HEAD")
        self.assertNotEqual(old_prepared_head, committed_replay_head)
        self.assertEqual(corrected_tree, git(worktree, "rev-parse", "HEAD^{tree}"))
        after_commit_crash = AtomicLedger(ledger_path).load()
        self.assertNotEqual(
            after_commit_crash["tickets"]["02"]["candidate_ref"],
            after_commit_crash["tickets"]["02"]["delivery_candidate_ref"],
        )
        self.assertEqual(
            prior_candidate_seal_events,
            len(
                [
                    event
                    for event in after_commit_crash["history"]
                    if event["event"] == "reconciliation-candidate-sealed"
                    and event["ticket_id"] == "02"
                ]
            ),
        )
        with mock.patch(
            "autopilot.cli._assert_target_base_sha",
            side_effect=RuntimeError("crash after verified delivery rebind"),
        ), self.assertRaisesRegex(
            RuntimeError, "crash after verified delivery rebind"
        ):
            self.resume_events_in_process(
                "semantic-rebind-test",
                [{"operation": "reconcile", "ticket_id": "02"}],
                runner,
            )
        rebound = AtomicLedger(ledger_path).load()
        rebound_child = rebound["tickets"]["02"]
        self.assertEqual("verified", rebound_child["state"])
        self.assertEqual(
            rebound_child["candidate_ref"],
            rebound_child["delivery_candidate_ref"],
        )
        self.assertEqual(corrected_generation, rebound_child["artifact_generation"])
        self.assertEqual(corrected_leaf_results, rebound_child["leaf_results"])
        self.assertEqual(
            prior_candidate_seal_events + 1,
            len(
                [
                    event
                    for event in rebound["history"]
                    if event["event"] == "reconciliation-candidate-sealed"
                    and event["ticket_id"] == "02"
                ]
            ),
        )

        (worktree / "child.txt").write_text("post-verification drift\n")
        git(worktree, "add", "-A")
        drift_tree = git(worktree, "write-tree")
        drifted = self.resume_events_in_process(
            "semantic-rebind-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            runner,
        )
        drift_event = drifted["data"]["processed"][0]
        self.assertEqual("revalidation-required", drift_event["result"])
        drifted_child = drifted["data"]["tickets"]["02"]
        self.assertEqual("active", drifted_child["state"])
        self.assertEqual(drift_tree, drifted_child["candidate_ref"]["candidate_tree_oid"])
        self.assertEqual(
            rebound_child["delivery_candidate_ref"],
            drifted_child["delivery_candidate_ref"],
        )
        self.assertNotEqual(
            drifted_child["candidate_ref"], drifted_child["delivery_candidate_ref"]
        )
        self.resume_events(
            "semantic-rebind-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "02",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": drift_tree,
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
        with mock.patch(
            "autopilot.cli._assert_target_base_sha",
            side_effect=RuntimeError("crash after drift candidate seal"),
        ), self.assertRaisesRegex(
            RuntimeError, "crash after drift candidate seal"
        ):
            self.resume_events_in_process(
                "semantic-rebind-test",
                [{"operation": "reconcile", "ticket_id": "02"}],
                runner,
            )
        drift_rebound = AtomicLedger(ledger_path).load()
        drift_rebound_child = drift_rebound["tickets"]["02"]
        self.assertEqual(
            drift_rebound_child["candidate_ref"],
            drift_rebound_child["delivery_candidate_ref"],
        )
        self.assertEqual(drift_tree, git(worktree, "rev-parse", "HEAD^{tree}"))
        self.assertEqual(
            prior_candidate_seal_events + 2,
            len(
                [
                    event
                    for event in drift_rebound["history"]
                    if event["event"] == "reconciliation-candidate-sealed"
                    and event["ticket_id"] == "02"
                ]
            ),
        )

        def advance_target(parent: str, message: str) -> str:
            marker = message.replace(" ", "-") + "\n"
            marker_blob = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"],
                cwd=self.repo,
                input=marker,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            parent_tree = subprocess.run(
                ["git", "ls-tree", f"{parent}^{{tree}}"],
                cwd=self.repo,
                text=True,
                capture_output=True,
                check=True,
            ).stdout
            advanced_tree = subprocess.run(
                ["git", "mktree"],
                cwd=self.repo,
                input=(
                    parent_tree
                    + f"100644 blob {marker_blob}\trefresh-{marker_blob[:8]}.txt\n"
                ),
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            advanced = git(
                self.repo,
                "commit-tree",
                advanced_tree,
                "-p",
                parent,
                "-m",
                message,
            )
            git(
                self.repo,
                "push",
                "origin",
                f"{advanced}:refs/heads/main",
            )
            return advanced

        observed_main = git(
            self.repo,
            "ls-remote",
            "--heads",
            "origin",
            "refs/heads/main",
        ).split()[0]
        first_advanced_main = advance_target(
            observed_main,
            "advance target during required semantic revalidation",
        )
        provider_mutations_before_refresh = len(
            [
                command
                for command in runner.commands
                if command[:2] == ["gh", "api"]
                and "--method" in command
                and "PATCH" in command
            ]
        )
        refresh_event = [{"operation": "reconcile", "ticket_id": "02"}]
        old_local_head = git(worktree, "rev-parse", "HEAD")
        with mock.patch(
            "autopilot.cli._derive_reconciliation_refresh_candidate",
            side_effect=RuntimeError("crash before refresh Git mutation"),
        ), self.assertRaisesRegex(
            RuntimeError, "crash before refresh Git mutation"
        ):
            self.resume_events_in_process(
                "semantic-rebind-test", refresh_event, runner
            )
        before_mutation = AtomicLedger(ledger_path).load()["tickets"]["02"]
        self.assertIn(
            "reconcile-refresh-intent", before_mutation["delivery"]
        )
        self.assertEqual(old_local_head, git(worktree, "rev-parse", "HEAD"))

        with mock.patch(
            "autopilot.cli.Kernel.prepare_reconciliation",
            side_effect=RuntimeError("crash after refresh Git mutation"),
        ), self.assertRaisesRegex(
            RuntimeError, "crash after refresh Git mutation"
        ):
            self.resume_events_in_process(
                "semantic-rebind-test", refresh_event, runner
            )
        after_mutation_head = git(worktree, "rev-parse", "HEAD")
        self.assertNotEqual(old_local_head, after_mutation_head)
        after_mutation = AtomicLedger(ledger_path).load()["tickets"]["02"]
        self.assertIn(
            "reconcile-refresh-intent", after_mutation["delivery"]
        )

        original_refresh_save = AtomicLedger.save
        crashed_after_refresh_prepare = False

        def crash_after_refresh_prepare(
            store_to_save: AtomicLedger, document: dict[str, object]
        ) -> None:
            nonlocal crashed_after_refresh_prepare
            history = document["history"]  # type: ignore[index]
            if (
                not crashed_after_refresh_prepare
                and any(
                    item["event"] == "reconciliation-target-refreshed"
                    for item in history
                )
                and "reconcile-refresh-intent"
                not in document["tickets"]["02"]["delivery"]  # type: ignore[index]
            ):
                crashed_after_refresh_prepare = True
                raise RuntimeError("crash after refresh ledger preparation")
            original_refresh_save(store_to_save, document)

        with mock.patch.object(
            AtomicLedger, "save", new=crash_after_refresh_prepare
        ), self.assertRaisesRegex(
            RuntimeError, "crash after refresh ledger preparation"
        ):
            self.resume_events_in_process(
                "semantic-rebind-test", refresh_event, runner
            )
        self.assertTrue(crashed_after_refresh_prepare)
        after_prepare_crash = AtomicLedger(ledger_path).load()["tickets"]["02"]
        self.assertIn(
            "reconcile-refresh-intent", after_prepare_crash["delivery"]
        )

        first_refresh = self.resume_events_in_process(
            "semantic-rebind-test", refresh_event, runner
        )
        first_refresh_event = first_refresh["data"]["processed"][0]
        self.assertEqual("revalidation-required", first_refresh_event["result"])
        self.assertTrue(first_refresh_event["target_refreshed"])
        first_refreshed_child = first_refresh["data"]["tickets"]["02"]
        self.assertEqual("active", first_refreshed_child["state"])
        self.assertEqual("review", first_refreshed_child["stage"])
        self.assertEqual(
            first_advanced_main,
            first_refreshed_child["delivery"]["reconcile-intent"]["target_base"][
                "sha"
            ],
        )
        self.assertEqual(
            1,
            len(first_refreshed_child["delivery"]["reconcile-attempt-history"]),
        )
        self.assertEqual(
            provider_mutations_before_refresh,
            len(
                [
                    command
                    for command in runner.commands
                    if command[:2] == ["gh", "api"]
                    and "--method" in command
                    and "PATCH" in command
                ]
            ),
        )

        first_refresh_tree = first_refreshed_child["candidate_ref"][
            "candidate_tree_oid"
        ]
        self.resume_events(
            "semantic-rebind-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "02",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": first_refresh_tree,
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

        second_advanced_main = advance_target(
            first_advanced_main,
            "advance target a second time during revalidation",
        )
        second_refresh = self.resume_events_in_process(
            "semantic-rebind-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            runner,
        )
        second_refresh_event = second_refresh["data"]["processed"][0]
        self.assertEqual("revalidation-required", second_refresh_event["result"])
        self.assertTrue(second_refresh_event["target_refreshed"])
        second_refreshed_child = second_refresh["data"]["tickets"]["02"]
        self.assertEqual(
            second_advanced_main,
            second_refreshed_child["delivery"]["reconcile-intent"]["target_base"][
                "sha"
            ],
        )
        self.assertEqual(
            2,
            len(second_refreshed_child["delivery"]["reconcile-attempt-history"]),
        )
        second_refresh_tree = second_refreshed_child["candidate_ref"][
            "candidate_tree_oid"
        ]
        self.resume_events(
            "semantic-rebind-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "02",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": second_refresh_tree,
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
        render_prepared = self.resume_events_in_process(
            "semantic-rebind-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            runner,
        )
        render_request = render_prepared["data"]["processed"][0]
        self.assertEqual("render-required", render_request["result"])
        current_child = render_prepared["data"]["tickets"]["02"]
        current_candidate = current_child["candidate_ref"]
        new_head = render_request["head_sha"]
        request = render_request["render_request"]
        self.assertEqual(current_candidate, request["candidate_ref"])
        self.assertEqual(
            current_child["artifact_generation"],
            request["artifact_generation"],
        )

        legacy_payload = {
            key: value
            for key, value in request.items()
            if key not in {"request_hash", "bundle_sha256"}
        }
        legacy_request = {
            **legacy_payload,
            "request_hash": _cache_digest(legacy_payload),
        }
        ledger_path = Path(render_prepared["data"]["ledger"])
        migration_store = AtomicLedger(ledger_path)
        migration_kernel = Kernel(migration_store.load())
        migration_kernel.record_delivery_metadata(
            "02", "reconcile-pr-body-request", legacy_request
        )
        migration_store.save(migration_kernel.ledger)
        migrated = self.resume_events_in_process(
            "semantic-rebind-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            runner,
        )
        render_request = migrated["data"]["processed"][0]
        self.assertEqual("render-required", render_request["result"])
        request = render_request["render_request"]
        self.assertIn("bundle_sha256", request)
        self.assertNotEqual(
            legacy_request["request_hash"], request["request_hash"]
        )

        stale_body = valid_pr_body(old_bundle, expected_head_sha=new_head)
        stale_rejected = self.resume_events_in_process(
            "semantic-rebind-test",
            [
                {
                    "operation": "reconcile",
                    "ticket_id": "02",
                    "render_request_hash": render_request[
                        "render_request_hash"
                    ],
                    "expected_head_sha": new_head,
                    "rendered_body": stale_body,
                    "verification_bundle": old_bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            runner,
        )
        stale_gate = stale_rejected["data"]["processed"][0]
        self.assertEqual("gated", stale_gate["result"])
        self.assertIn("verified handoff bundle", stale_gate["reason"])
        self.parse(
            run(
                "approve",
                "semantic-rebind-test",
                stale_gate["gate_id"],
                "--repo",
                str(self.repo),
                "--actor",
                "qa",
                "--evidence",
                "fresh verified bundle supplied",
                cwd=self.repo,
            )
        )

        fresh_bundle = verification_bundle(current_candidate, ticket_id="02")
        fresh_body = valid_pr_body(fresh_bundle, expected_head_sha=new_head)
        render_event = {
            "operation": "reconcile",
            "ticket_id": "02",
            "render_request_hash": render_request["render_request_hash"],
            "expected_head_sha": new_head,
            "rendered_body": fresh_body,
            "verification_bundle": fresh_bundle,
            "verification_audit_root": str(ROOT / "verification-audit"),
        }
        original_save = AtomicLedger.save
        crashed_before_rebind_save = False

        def crash_before_rebind_save(
            store_to_save: AtomicLedger, document: dict[str, object]
        ) -> None:
            nonlocal crashed_before_rebind_save
            body_record = document["tickets"]["02"]["delivery"].get(  # type: ignore[index]
                "pr-body"
            )
            if (
                not crashed_before_rebind_save
                and isinstance(body_record, dict)
                and body_record.get("schema") == 2
                and body_record.get("expected_head_sha") == new_head
            ):
                crashed_before_rebind_save = True
                raise RuntimeError("simulated semantic rebind save crash")
            original_save(store_to_save, document)

        with mock.patch.object(
            AtomicLedger, "save", new=crash_before_rebind_save
        ), self.assertRaisesRegex(
            RuntimeError, "simulated semantic rebind save crash"
        ):
            self.resume_events_in_process(
                "semantic-rebind-test", [render_event], runner
            )
        self.assertTrue(crashed_before_rebind_save)
        after_crash = AtomicLedger(ledger_path).load()["tickets"]["02"]
        self.assertEqual(old_receipt, after_crash["delivery"]["pr-body"])

        with mock.patch(
            "autopilot.cli._drive_autonomous_merge",
            return_value={"result": "deferred"},
        ):
            reconciled = self.resume_events_in_process(
                "semantic-rebind-test", [render_event], runner
            )
        reconcile_event = reconciled["data"]["processed"][0]
        self.assertEqual("reconciled", reconcile_event["result"])
        final_child = reconciled["data"]["tickets"]["02"]
        rebound = final_child["delivery"]["pr-body"]
        self.assertEqual(2, rebound["schema"])
        self.assertNotEqual(old_receipt["bundle_sha256"], rebound["bundle_sha256"])
        self.assertEqual(
            request["bundle_sha256"], rebound["bundle_sha256"]
        )
        latest = rebound["lineage_rebinds"][-1]
        self.assertEqual(old_receipt, latest["old_receipt"])
        self.assertEqual(old_receipt["bundle_sha256"], latest["old_bundle_sha256"])
        self.assertEqual(rebound["bundle_sha256"], latest["new_bundle_sha256"])
        self.assertEqual(new_head, final_child["pr"]["head_sha"])
        self.assertEqual(
            fresh_body,
            runner.prs[final_child["pr"]["pr_id"]]["body"],
        )
        self.assertEqual(
            new_head,
            final_child["delivery"]["reconcile-retarget"]["head_sha"],
        )
        AtomicLedger._validate(AtomicLedger(ledger_path).load())

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

    def test_verification_checkpoint_uses_canonical_adapters_and_status_cache(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "verification-checkpoint-test",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "verification-checkpoint-test",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / "implementation.txt").write_text("checkpoint candidate\n")
        git(worktree, "add", "-A")
        tree_oid = git(worktree, "write-tree")
        self.resume_events(
            "verification-checkpoint-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": tree_oid,
                }
                for stage in (
                    "implement",
                    "simplify",
                    "review",
                    "qa-plan",
                    "qa-execute",
                )
            ],
        )
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "verification-checkpoint-test"
            / "ledger.json"
        )
        ledger = AtomicLedger(ledger_path).load()
        fixed = candidate_ref(
            worktree,
            ledger["tickets"]["01"]["ticket_digest"],
        )
        candidate = {
            "contract_version": fixed.contract_version,
            "base_tree_oid": fixed.base_tree_oid,
            "candidate_tree_oid": fixed.candidate_tree_oid,
            "ticket_digest": fixed.ticket_digest,
        }
        event = {
            "operation": "verification-checkpoint",
            "ticket_id": "01",
            "expected_tree_oid": tree_oid,
            "verification_audit_root": str(ROOT / "verification-audit"),
            "verification_inputs": verification_bundle(candidate),
        }
        cache_inputs = _verification_cache_inputs(
            event["verification_inputs"],
            candidate=fixed,
            ticket_id="01",
            verification_root=ROOT / "verification-audit",
            provider="github",
            provider_mode="simulated",
        )
        cache_contract = cache_inputs["cache_contract"]
        self.assertEqual(3, cache_contract["leaf_contract_version"])
        self.assertEqual(candidate, cache_contract["candidate_ref"])
        self.assertEqual(
            {
                "boundary": "internal",
                "operation": "verification-checkpoint",
                "ticket_id": "01",
            },
            cache_contract["declared_scope"],
        )
        self.assertTrue(cache_contract["artifact_hashes"])
        self.assertTrue(cache_contract["command_identity"])
        changed_environment = _verification_cache_inputs(
            event["verification_inputs"],
            candidate=fixed,
            ticket_id="01",
            verification_root=ROOT / "verification-audit",
            provider="azure-devops",
            provider_mode="simulated",
        )
        self.assertNotEqual(
            _cache_digest(cache_inputs),
            _cache_digest(changed_environment),
        )
        with self.assertRaisesRegex(
            TransitionError,
            "cannot be persisted",
        ):
            _verification_cache_inputs(
                {"access_token": "must-not-be-written"},
                candidate=fixed,
                ticket_id="01",
                verification_root=ROOT / "verification-audit",
                provider="github",
                provider_mode="simulated",
            )
        blocked = self.resume_events(
            "verification-checkpoint-test",
            [
                {
                    **event,
                    "verification_inputs": verification_bundle(
                        candidate,
                        operation="merge-pr",
                    ),
                }
            ],
        )
        blocked_result = blocked["data"]["processed"][0]
        self.assertEqual("complete", blocked_result["result"], blocked_result)
        self.assertFalse(
            blocked_result["verification"]["stage_pass_eligible"]
        )
        self.assertTrue(
            blocked["data"]["tickets"]["01"]["leaf_progress"]["handoff"][
                "findings"
            ]
        )

        stale_candidate = {
            **candidate,
            "candidate_tree_oid": "stale-tree",
        }
        partial = self.resume_events(
            "verification-checkpoint-test",
            [
                {
                    **event,
                    "verification_inputs": verification_bundle(
                        stale_candidate
                    ),
                }
            ],
        )
        partial_result = partial["data"]["processed"][0]
        self.assertEqual("partial", partial_result["result"])
        self.assertIn("stale candidate", partial_result["failure"])
        self.assertEqual(
            ["context-loaded", "bundle-built"],
            partial_result["phases_complete"],
        )
        self.assertFalse(
            partial["data"]["tickets"]["01"]["leaf_progress"]["handoff"][
                "complete"
            ]
        )

        first = self.resume_events(
            "verification-checkpoint-test",
            [event],
        )

        first_result = first["data"]["processed"][0]
        self.assertEqual("complete", first_result["result"])
        self.assertFalse(first_result["cache_hit"])
        self.assertEqual(0, first_result["commands_avoided"])
        self.assertEqual(
            "cache-entry-absent-or-incomplete",
            first_result["cache_miss_reason"],
        )
        self.assertEqual(
            list(LEAF_PHASE_CONTRACTS["verify"]),
            first_result["phases_complete"],
        )
        self.assertTrue(first_result["verification"]["stage_pass_eligible"])
        ticket = first["data"]["tickets"]["01"]
        self.assertEqual("handoff-ready", ticket["leaf_progress"]["last_phase"])

        self.assertEqual([], ticket["leaf_progress"]["handoff"]["findings"])
        interactions = ticket["verbosity"]["leaf_interactions"]

        cached = self.resume_events(
            "verification-checkpoint-test",
            [event],
        )

        cached_result = cached["data"]["processed"][0]
        self.assertTrue(cached_result["cache_hit"])
        self.assertIsNone(cached_result["cache_miss_reason"])
        self.assertEqual(3, cached_result["commands_avoided"])
        self.assertTrue(cached_result["cache_limitations"])
        cache_status = cached["data"]["tickets"]["01"]["evidence_cache"]
        self.assertEqual(1, cache_status["hits"])
        self.assertGreaterEqual(cache_status["misses"], 1)
        self.assertEqual(3, cache_status["commands_avoided"])
        self.assertTrue(cache_status["last_decision"]["hit"])
        self.assertEqual(
            interactions,
            cached["data"]["tickets"]["01"]["verbosity"]["leaf_interactions"],
        )
        verified = self.resume_events_in_process(
            "verification-checkpoint-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": "verify",
                    "result": "pass",
                    "expected_tree_oid": tree_oid,
                }
            ],
            FakeGitHubRunner(),
        )
        self.assertEqual(
            "finalize",
            verified["data"]["tickets"]["01"]["stage"],
        )

    def test_real_leaf_budget_exhaustion_is_a_durable_actionable_gate(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "leaf-budget-gate-test",
                "--max-leaf-interactions",
                "3",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "leaf-budget-gate-test",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / "implementation.txt").write_text("bounded candidate\n")
        git(worktree, "add", "-A")
        tree_oid = git(worktree, "write-tree")
        adopted = self.resume_events(
            "leaf-budget-gate-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": "implement",
                    "result": "pass",
                    "expected_tree_oid": tree_oid,
                }
            ],
        )
        self.assertEqual(
            "pass", adopted["data"]["processed"][0]["result"]
        )
        self.resume_events(
            "leaf-budget-gate-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": tree_oid,
                }
                for stage in ("simplify", "review")
            ],
        )
        (worktree / "implementation.txt").write_text("drifted candidate\n")
        git(worktree, "add", "-A")
        tree_oid = git(worktree, "write-tree")
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "leaf-budget-gate-test"
            / "ledger.json"
        )
        store = AtomicLedger(ledger_path)
        legacy_kernel = Kernel(store.load())
        legacy_ticket = legacy_kernel.ledger["tickets"]["01"]
        legacy_budget = copy.deepcopy(legacy_ticket["leaf_budget"])
        drifted = candidate_ref(
            worktree,
            legacy_ticket["ticket_digest"],
            base_ref=legacy_ticket["candidate_ref"]["base_tree_oid"],
        )
        with mock.patch(
            "autopilot.kernel.new_leaf_budget",
            return_value=copy.deepcopy(legacy_budget),
        ):
            legacy_kernel.invalidate_for_candidate_drift("01", drifted)
        store.save(legacy_kernel.ledger)
        self.resume_events(
            "leaf-budget-gate-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": tree_oid,
                }
                for stage in ("implement", "simplify")
            ],
        )

        repaired = self.resume_events(
            "leaf-budget-gate-test",
            [
                {
                    "operation": "revalidation-budget-repair",
                    "ticket_id": "01",
                    "expected_tree_oid": tree_oid,
                }
            ],
        )
        self.assertEqual(
            "repaired", repaired["data"]["processed"][0]["result"]
        )
        repaired_ticket = repaired["data"]["tickets"]["01"]
        self.assertEqual(
            0,
            repaired_ticket["budgets"]["leaf_interactions"]["consumed"],
        )
        self.assertEqual(
            1,
            repaired_ticket["verbosity"]["leaf_interactions"],
        )
        self.resume_events(
            "leaf-budget-gate-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": "review",
                    "result": "pass",
                    "expected_tree_oid": tree_oid,
                }
            ],
        )
        exhausted = self.resume_events(
            "leaf-budget-gate-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": "qa-plan",
                    "result": "pass",
                    "expected_tree_oid": tree_oid,
                }
            ],
        )

        outcome = exhausted["data"]["processed"][0]
        self.assertEqual("gated", outcome["result"])
        self.assertEqual("resource-budget", outcome["gate"])
        self.assertIn("start a new run", outcome["reason"])
        ticket = exhausted["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        restored = AtomicLedger(ledger_path).load()
        gate = restored["gates"][outcome["gate_id"]]
        self.assertEqual("open", gate["state"])
        self.assertEqual(
            ["new-run-with-larger-leaf-limits"],
            gate["details"]["recovery"],
        )

    def test_docs_only_adoption_skips_leaves_replays_and_enters_delivery(self) -> None:
        remote = Path(self.directory.name) / "docs-only-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
        git(self.repo, "remote", "add", "origin", str(remote))
        git(self.repo, "push", "-u", "origin", "main")
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "docs-only-test",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        activated = self.resume_events(
            "docs-only-test",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        ticket = activated["data"]["tickets"]["01"]
        docs = worktree / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")
        git(worktree, "add", "docs/guide.md")
        fixed = candidate_ref(
            worktree,
            ticket["candidate_ref"]["ticket_digest"],
            base_ref=ticket["candidate_ref"]["base_tree_oid"],
        )
        request = {
            "contract_version": 1,
            "ticket_envelope": {
                "ticket_schema": 1,
                "ticket_id": "01",
                "execution_mode": "AFK",
                "blocked_by": [],
            },
            "ticket_digest": ticket["candidate_ref"]["ticket_digest"],
            "source_relative_path": "01.md",
            "candidate_ref": {
                "contract_version": fixed.contract_version,
                "base_tree_oid": fixed.base_tree_oid,
                "candidate_tree_oid": fixed.candidate_tree_oid,
                "ticket_digest": fixed.ticket_digest,
            },
            "expected_changed_paths": ["docs/guide.md"],
            "approved_documentation_scope": APPROVED_SCOPE,
        }
        event = {
            "operation": "docs-only-adopt",
            "ticket_id": "01",
            "request": request,
            "verification_audit_root": str(ROOT / "verification-audit"),
        }
        import autopilot.cli as cli_module

        checkpoint_runner = cli_module.run_verification_checkpoints

        def drift_after_checkpoint(*args: object, **kwargs: object) -> object:
            outcome = checkpoint_runner(*args, **kwargs)
            (docs / "guide.md").write_text(
                "# Drifted during checkpoint\n", encoding="utf-8"
            )
            git(worktree, "add", "docs/guide.md")
            return outcome

        event_path = Path(self.directory.name) / "docs-only-drift-event.json"
        event_path.write_text(json.dumps({"schema": 1, "events": [event]}))
        output = io.StringIO()
        with mock.patch(
            "autopilot.cli.run_verification_checkpoints",
            side_effect=drift_after_checkpoint,
        ), redirect_stdout(output):
            result = cli_main(
                [
                    "resume",
                    "docs-only-test",
                    "--repo",
                    str(self.repo),
                    "--events",
                    str(event_path),
                ]
            )
        drift_rejected = json.loads(output.getvalue())
        self.assertEqual(2, result)
        self.assertIn("staged tree differs", drift_rejected["error"]["message"])
        ledger_after_drift = AtomicLedger(
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "docs-only-test"
            / "ledger.json"
        ).load()
        self.assertEqual("active", ledger_after_drift["tickets"]["01"]["state"])
        self.assertIsNone(
            ledger_after_drift["tickets"]["01"].get("docs_only")
        )
        (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")
        git(worktree, "add", "docs/guide.md")
        adopted = self.resume_events("docs-only-test", [event])
        adopted_ticket = adopted["data"]["tickets"]["01"]
        self.assertEqual("verified", adopted_ticket["state"])
        self.assertEqual(0, adopted_ticket["verbosity"]["leaf_interactions"])
        self.assertEqual(
            4, adopted_ticket["verbosity"]["leaf_interactions_avoided"]
        )
        self.assertEqual("eligible", adopted_ticket["docs_only"]["status"])
        self.assertEqual(
            "implementation-complete",
            adopted["data"]["processed"][0]["verification"]["max_claim"],
        )
        replay = self.resume_events("docs-only-test", [event])
        self.assertTrue(replay["data"]["processed"][0]["replayed"])
        ledger = AtomicLedger(
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "docs-only-test"
            / "ledger.json"
        ).load()
        self.assertEqual(
            1,
            sum(
                item["event"] == "docs-only-candidate-adopted"
                for item in ledger["history"]
            ),
        )
        untracked = docs / "untracked.md"
        untracked.write_text("# Untracked\n", encoding="utf-8")
        status_before_revalidation = git(worktree, "status", "--short")
        rejected_revalidation = self.resume_events(
            "docs-only-test",
            [{"operation": "delivery-revalidate", "ticket_id": "01"}],
            check=False,
        )
        self.assertFalse(rejected_revalidation["ok"])
        self.assertIn(
            "untracked or unstaged",
            rejected_revalidation["error"]["message"],
        )
        self.assertEqual(
            status_before_revalidation,
            git(worktree, "status", "--short"),
        )
        untracked.unlink()
        unchanged = self.resume_events(
            "docs-only-test",
            [{"operation": "delivery-revalidate", "ticket_id": "01"}],
        )
        self.assertEqual("unchanged", unchanged["data"]["processed"][0]["result"])
        delivery = self.resume_events(
            "docs-only-test",
            [{"operation": "delivery", "ticket_id": "01"}],
        )
        result = delivery["data"]["processed"][0]
        self.assertEqual("render-required", result["result"])
        self.assertTrue((worktree / "tickets" / "done" / "01.md").is_file())
        self.assertEqual(
            result["head_sha"],
            git(
                worktree,
                "ls-remote",
                "--heads",
                "origin",
                f"refs/heads/{result['branch']}",
            ).split()[0],
        )

    def test_autonomous_merge_accepts_an_eligible_docs_only_candidate(self) -> None:
        git(self.repo, "rm", "tickets/02.md")
        git(self.repo, "commit", "-m", "single docs-only autonomous ticket")
        remote = Path(self.directory.name) / "docs-only-autonomous-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
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
                "docs-only-autonomous-test",
                "--merge-policy",
                "autonomous",
                "--merge-actor",
                "release-operator",
                "--merge-evidence",
                "artifact://run-merge-grant",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        activated = self.resume_events(
            "docs-only-autonomous-test",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        ticket = activated["data"]["tickets"]["01"]
        docs = worktree / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")
        git(worktree, "add", "docs/guide.md")
        fixed = candidate_ref(
            worktree,
            ticket["candidate_ref"]["ticket_digest"],
            base_ref=ticket["candidate_ref"]["base_tree_oid"],
        )
        adopted = self.resume_events(
            "docs-only-autonomous-test",
            [
                {
                    "operation": "docs-only-adopt",
                    "ticket_id": "01",
                    "request": {
                        "contract_version": 1,
                        "ticket_envelope": {
                            "ticket_schema": 1,
                            "ticket_id": "01",
                            "execution_mode": "AFK",
                            "blocked_by": [],
                        },
                        "ticket_digest": fixed.ticket_digest,
                        "source_relative_path": "01.md",
                        "candidate_ref": {
                            "contract_version": fixed.contract_version,
                            "base_tree_oid": fixed.base_tree_oid,
                            "candidate_tree_oid": fixed.candidate_tree_oid,
                            "ticket_digest": fixed.ticket_digest,
                        },
                        "expected_changed_paths": ["docs/guide.md"],
                        "approved_documentation_scope": APPROVED_SCOPE,
                    },
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
        )
        self.assertEqual(
            ["implement"], adopted["data"]["tickets"]["01"]["validated_stages"]
        )
        self.assertEqual(
            "implementation-complete",
            adopted["data"]["processed"][0]["verification"]["max_claim"],
        )

        runner = FakeGitHubRunner()
        prepared = self.resume_events_in_process(
            "docs-only-autonomous-test",
            [{"operation": "delivery", "ticket_id": "01"}],
            runner,
        )
        request = prepared["data"]["processed"][0]
        bundle_artifact = Path(
            request["render_request"]["verification_bundle"]["artifact"]
        )
        bundle = json.loads(bundle_artifact.read_text(encoding="utf-8"))["value"]
        self.assertEqual(
            "implementation-complete", bundle["verification"]["max_claim"]
        )
        delivered = self.resume_events_in_process(
            "docs-only-autonomous-test",
            [
                {
                    "operation": "delivery",
                    "ticket_id": "01",
                    "render_request_hash": request["render_request_hash"],
                    "expected_head_sha": request["head_sha"],
                    "rendered_body": valid_pr_body(
                        bundle, expected_head_sha=request["head_sha"]
                    ),
                    "verification_bundle": bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            runner,
        )

        delivered_ticket = delivered["data"]["tickets"]["01"]
        self.assertEqual("integrated", delivered_ticket["state"], delivered_ticket)
        self.assertEqual(["implement"], delivered_ticket["validated_stages"])
        self.assertEqual(0, delivered_ticket["verbosity"]["leaf_interactions"])
        self.assertEqual("eligible", delivered_ticket["merge_eligibility"]["status"])
        self.assertEqual(1, runner.merge_commands)
        merge_command = next(
            command
            for command in runner.commands
            if command[:3] == ["gh", "pr", "merge"]
        )
        self.assertEqual(
            request["head_sha"],
            merge_command[merge_command.index("--match-head-commit") + 1],
        )
        self.assertNotIn("--admin", merge_command)

    def test_docs_only_delivery_revalidates_after_branch_switch(self) -> None:
        remote = Path(self.directory.name) / "docs-only-drift-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
        git(self.repo, "remote", "add", "origin", str(remote))
        git(self.repo, "push", "-u", "origin", "main")
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "docs-only-branch-drift",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        activated = self.resume_events(
            "docs-only-branch-drift",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        ticket = activated["data"]["tickets"]["01"]
        docs = worktree / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")
        git(worktree, "add", "docs/guide.md")
        fixed = candidate_ref(
            worktree,
            ticket["candidate_ref"]["ticket_digest"],
            base_ref=ticket["candidate_ref"]["base_tree_oid"],
        )
        request = {
            "contract_version": 1,
            "ticket_envelope": {
                "ticket_schema": 1,
                "ticket_id": "01",
                "execution_mode": "AFK",
                "blocked_by": [],
            },
            "ticket_digest": fixed.ticket_digest,
            "source_relative_path": "01.md",
            "candidate_ref": {
                "contract_version": fixed.contract_version,
                "base_tree_oid": fixed.base_tree_oid,
                "candidate_tree_oid": fixed.candidate_tree_oid,
                "ticket_digest": fixed.ticket_digest,
            },
            "expected_changed_paths": ["docs/guide.md"],
            "approved_documentation_scope": APPROVED_SCOPE,
        }
        self.resume_events(
            "docs-only-branch-drift",
            [
                {
                    "operation": "docs-only-adopt",
                    "ticket_id": "01",
                    "request": request,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
        )

        from autopilot.finalizer import DeliveryFinalizer

        original_ensure_branch = DeliveryFinalizer._ensure_branch

        def drift_after_branch(
            finalizer: DeliveryFinalizer,
            ticket_id: str,
            branch: str,
            base_branch: str,
            expected_base_tree_oid: str,
        ) -> str:
            base_sha = original_ensure_branch(
                finalizer,
                ticket_id,
                branch,
                base_branch,
                expected_base_tree_oid,
            )
            (docs / "guide.md").write_text(
                "# Drifted during branch preparation\n", encoding="utf-8"
            )
            git(worktree, "add", "docs/guide.md")
            return base_sha

        event_path = Path(self.directory.name) / "docs-only-branch-drift.json"
        event_path.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "events": [{"operation": "delivery", "ticket_id": "01"}],
                }
            )
        )
        output = io.StringIO()
        with mock.patch.object(
            DeliveryFinalizer,
            "_ensure_branch",
            drift_after_branch,
        ), redirect_stdout(output):
            code = cli_main(
                [
                    "resume",
                    "docs-only-branch-drift",
                    "--repo",
                    str(self.repo),
                    "--events",
                    str(event_path),
                ]
            )
        result = json.loads(output.getvalue())

        self.assertEqual(0, code)
        self.assertEqual("gated", result["data"]["processed"][0]["result"])
        self.assertIn(
            "staged tree differs",
            result["data"]["processed"][0]["reason"],
        )
        self.assertTrue((worktree / "tickets" / "01.md").is_file())
        self.assertFalse((worktree / "tickets" / "done" / "01.md").exists())

    def test_ineligible_docs_only_candidate_resumes_standard_path(self) -> None:
        created = self.parse(
            run(
                "run",
                str(self.tickets),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "docs-only-rejected",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        activated = self.resume_events(
            "docs-only-rejected",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        ticket = activated["data"]["tickets"]["01"]
        (worktree / "script.py").write_text("print('standard')\n", encoding="utf-8")
        git(worktree, "add", "script.py")
        fixed = candidate_ref(
            worktree,
            ticket["candidate_ref"]["ticket_digest"],
            base_ref=ticket["candidate_ref"]["base_tree_oid"],
        )
        request = {
            "contract_version": 1,
            "ticket_envelope": {
                "ticket_schema": 1,
                "ticket_id": "01",
                "execution_mode": "AFK",
                "blocked_by": [],
            },
            "ticket_digest": fixed.ticket_digest,
            "source_relative_path": "01.md",
            "candidate_ref": {
                "contract_version": fixed.contract_version,
                "base_tree_oid": fixed.base_tree_oid,
                "candidate_tree_oid": fixed.candidate_tree_oid,
                "ticket_digest": fixed.ticket_digest,
            },
            "expected_changed_paths": ["script.py"],
            "approved_documentation_scope": APPROVED_SCOPE,
        }
        rejected = self.resume_events(
            "docs-only-rejected",
            [
                {
                    "operation": "docs-only-adopt",
                    "ticket_id": "01",
                    "request": request,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
        )
        outcome = rejected["data"]["processed"][0]
        self.assertEqual("standard-path-required", outcome["result"])
        self.assertIn("outside approved", outcome["reason"])
        rejected_ticket = rejected["data"]["tickets"]["01"]
        self.assertEqual("active", rejected_ticket["state"])
        self.assertEqual("implement", rejected_ticket["stage"])
        self.assertEqual("rejected", rejected_ticket["docs_only"]["status"])
        standard = self.resume_events(
            "docs-only-rejected",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": "implement",
                    "result": "pass",
                    "expected_tree_oid": fixed.candidate_tree_oid,
                }
            ],
        )
        standard_ticket = standard["data"]["tickets"]["01"]
        self.assertEqual("simplify", standard_ticket["stage"])
        self.assertIsNone(standard_ticket["docs_only"])

    def test_completion_commit_carries_move_summary_and_repointed_map(self) -> None:
        """The single-tree property, end to end, with _ensure_commit unmodified.

        The delivery candidate is recomputed after finalize_done mutates the staging area, so
        the repointed map must ride the same commit as the move and the completion summary —
        and the commit guard must pass without having been weakened.
        """

        specs = self.repo / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "map.md").write_text(
            "# Map\n\n- [the ticket](../../tickets/01.md)\n", encoding="utf-8"
        )
        git(self.repo, "add", "docs")
        git(self.repo, "commit", "-m", "map linking the ticket")
        remote = Path(self.directory.name) / "repoint-remote.git"
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
                "repoint-delivery",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "repoint-delivery", [{"operation": "activate", "ticket_id": "01"}]
        )
        (worktree / "implementation.txt").write_text("implemented\n")
        git(worktree, "add", "-A")
        tree = git(worktree, "write-tree")
        self.resume_events(
            "repoint-delivery",
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

        provider_runner = FakeGitHubRunner()
        prepared = self.resume_events_in_process(
            "repoint-delivery",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        request = prepared["data"]["processed"][0]
        self.assertEqual("render-required", request["result"], request)
        candidate = prepared["data"]["tickets"]["01"]["candidate_ref"]
        bundle = verification_bundle(candidate)
        opened = self.resume_events_in_process(
            "repoint-delivery",
            [
                {
                    "operation": "delivery",
                    "ticket_id": "01",
                    "render_request_hash": request["render_request_hash"],
                    "expected_head_sha": request["head_sha"],
                    "rendered_body": valid_pr_body(bundle),
                    "verification_bundle": bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            provider_runner,
        )
        delivery = opened["data"]["processed"][0]
        self.assertEqual("pr-open", delivery["result"], delivery)

        message = git(worktree, "log", "-1", "--format=%s")
        self.assertEqual("ticket 01: complete", message)
        committed = git(worktree, "show", "--name-only", "--format=", "HEAD").splitlines()
        self.assertIn("tickets/done/01.md", committed)
        self.assertIn("tickets/done/01.completion.json", committed)
        self.assertIn("docs/specs/map.md", committed, "the repoint rides the same commit")
        rewritten = (worktree / "docs" / "specs" / "map.md").read_text(encoding="utf-8")
        self.assertIn("(../../tickets/done/01.md)", rewritten)
        self.assertNotIn("(../../tickets/01.md)", rewritten)
        moved = (worktree / "tickets" / "done" / "01.md").read_text(encoding="utf-8")
        self.assertEqual(ticket_text("01"), moved, "the ticket's own bytes are untouched")

    def test_delivery_uses_verified_checkout_when_local_main_is_stale_after_parent_merge(
        self,
    ) -> None:
        remote = Path(self.directory.name) / "stale-local-main-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
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
                "stale-local-main-delivery",
                "--max-leaf-interactions",
                "30",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])

        def verify(ticket_id: str, content: str) -> str:
            self.resume_events(
                "stale-local-main-delivery",
                [{"operation": "activate", "ticket_id": ticket_id}],
            )
            (worktree / "README.md").write_text(content, encoding="utf-8")
            git(worktree, "add", "-A")
            tree = git(worktree, "write-tree")
            self.resume_events(
                "stale-local-main-delivery",
                [
                    {
                        "operation": "stage",
                        "ticket_id": ticket_id,
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
            return tree

        provider_runner = FakeGitHubRunner()
        verify("01", "parent\n")
        parent_opened, _body, _prepared = self.complete_delivery(
            "stale-local-main-delivery", "01", provider_runner
        )
        parent = parent_opened["data"]["tickets"]["01"]
        parent_head = parent["pr"]["head_sha"]
        stale_local_main = git(self.repo, "rev-parse", "main")
        integrated_main = git(
            self.repo,
            "commit-tree",
            f"{parent_head}^{{tree}}",
            "-p",
            stale_local_main,
            "-p",
            parent_head,
            "-m",
            "simulate provider parent integration",
        )
        git(self.repo, "push", "origin", f"{integrated_main}:refs/heads/main")
        integrated = self.approve_in_process(
            "stale-local-main-delivery",
            "01",
            parent_head,
            provider_runner,
        )
        self.assertEqual("integrated", integrated["data"]["tickets"]["01"]["state"])
        self.assertEqual(stale_local_main, git(self.repo, "rev-parse", "main"))

        verified_child_tree = verify("02", "child\n")
        child_opened, _child_body, _child_prepared = self.complete_delivery(
            "stale-local-main-delivery", "02", provider_runner
        )
        child = child_opened["data"]["tickets"]["02"]
        child_head = child["pr"]["head_sha"]

        self.assertEqual("pr-open", child["state"])
        self.assertEqual(stale_local_main, git(self.repo, "rev-parse", "main"))
        self.assertEqual(parent_head, git(worktree, "rev-parse", f"{child_head}^"))
        self.assertEqual(parent_head, child["delivery_lineage"]["base_sha"])
        self.assertEqual(
            verified_child_tree,
            child["candidate_ref"]["candidate_tree_oid"],
        )
        self.assertEqual(
            git(worktree, "rev-parse", f"{child_head}^{{tree}}"),
            child["delivery_candidate_ref"]["candidate_tree_oid"],
        )
        replay = self.resume_events_in_process(
            "stale-local-main-delivery",
            [{"operation": "delivery", "ticket_id": "02"}],
            provider_runner,
        )
        self.assertEqual("pr-open", replay["data"]["processed"][0]["result"])
        self.assertEqual(child_head, replay["data"]["processed"][0]["head_sha"])

    def test_initial_reconciliation_persists_repeated_target_refresh_before_git(
        self,
    ) -> None:
        run_id = "preprepare-target-refresh"
        worktree = self.prepare_single_manual_run(run_id)
        runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            run_id, "01", runner
        )
        ticket = opened["data"]["tickets"]["01"]
        lineage = ticket["delivery_lineage"]
        old_target_sha = lineage["base_sha"]
        old_target_tree = git(
            self.repo, "rev-parse", f"{old_target_sha}^{{tree}}"
        )
        git(self.repo, "push", "origin", f"{old_target_sha}:refs/heads/main")
        old_intent = {
            "schema": 1,
            "mode": "base-advance",
            "branch": ticket["pr"]["branch"],
            "old_head": ticket["pr"]["head_sha"],
            "parent_branch": "main",
            "parent_head": old_target_sha,
            "expected_remote_sha": ticket["pr"]["head_sha"],
            "target_base": {
                "branch": "main",
                "ref": "refs/remotes/origin/main",
                "sha": old_target_sha,
                "tree_oid": old_target_tree,
            },
        }
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / run_id
            / "ledger.json"
        )
        store = AtomicLedger(ledger_path)
        kernel = Kernel(store.load())
        kernel.record_delivery_metadata(
            "01", "reconcile-intent", old_intent
        )
        store.save(kernel.ledger)

        def advance_target(label: str) -> str:
            (self.repo / f"{label}.txt").write_text(label + "\n")
            git(self.repo, "add", f"{label}.txt")
            git(self.repo, "commit", "-m", label)
            head = git(self.repo, "rev-parse", "HEAD")
            git(self.repo, "push", "origin", f"{head}:refs/heads/main")
            return head

        first_target = advance_target("first-target-refresh")
        tracking_ref_before = git(
            worktree,
            "for-each-ref",
            "--format=%(objectname)",
            "refs/remotes/origin/main",
        )
        with mock.patch(
            "autopilot.cli._derive_reconciliation_candidate",
            side_effect=RuntimeError("stop after first refresh persistence"),
        ), self.assertRaisesRegex(
            RuntimeError, "first refresh persistence"
        ):
            self.resume_events_in_process(
                run_id,
                [{"operation": "reconcile", "ticket_id": "01"}],
                runner,
            )
        first = AtomicLedger(ledger_path).load()["tickets"]["01"]["delivery"]
        first_refresh = first[
            "repository-reconciliation-preparation-refresh"
        ]
        self.assertEqual(
            first_target,
            first_refresh["replacement_intent"]["target_base"]["sha"],
        )
        self.assertEqual([], first_refresh["history"])
        self.assertEqual(
            tracking_ref_before,
            git(
                worktree,
                "for-each-ref",
                "--format=%(objectname)",
                "refs/remotes/origin/main",
            ),
        )
        self.assertEqual(
            ticket["pr"]["head_sha"], git(worktree, "rev-parse", "HEAD")
        )

        with mock.patch.object(
            Kernel,
            "prepare_reconciliation",
            side_effect=RuntimeError("crash after first Git mutation"),
        ), self.assertRaisesRegex(RuntimeError, "first Git mutation"):
            self.resume_events_in_process(
                run_id,
                [{"operation": "reconcile", "ticket_id": "01"}],
                runner,
            )
        first_rebased_head = git(worktree, "rev-parse", "HEAD")
        self.assertNotEqual(ticket["pr"]["head_sha"], first_rebased_head)
        persisted_after_crash = AtomicLedger(ledger_path).load()["tickets"][
            "01"
        ]["delivery"]
        self.assertEqual(
            first_refresh,
            persisted_after_crash[
                "repository-reconciliation-preparation-refresh"
            ],
        )

        second_target = advance_target("second-target-refresh")
        completed = self.resume_events_in_process(
            run_id,
            [{"operation": "reconcile", "ticket_id": "01"}],
            runner,
        )
        self.assertEqual(
            "revalidation-required", completed["data"]["processed"][0]["result"]
        )
        second = AtomicLedger(ledger_path).load()["tickets"]["01"]["delivery"]
        self.assertNotIn(
            "repository-reconciliation-preparation-refresh", second
        )
        consumed = second["reconcile-preparation-refresh-history"][-1][
            "refresh"
        ]
        self.assertEqual(
            second_target,
            consumed["replacement_intent"]["target_base"]["sha"],
        )
        self.assertEqual(1, len(consumed["history"]))
        self.assertEqual(
            first_refresh,
            {
                **consumed,
                "history": [],
                "previous_intent": old_intent,
                "replacement_intent": consumed["history"][0][
                    "replacement_intent"
                ],
            },
        )
        self.assertNotEqual(first_rebased_head, git(worktree, "rev-parse", "HEAD"))

    def test_delivery_rejects_checkout_that_no_longer_matches_verified_base(
        self,
    ) -> None:
        worktree = self.prepare_single_manual_run("delivery-base-tree-drift")
        expected_base = AtomicLedger(
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "delivery-base-tree-drift"
            / "ledger.json"
        ).load()["tickets"]["01"]["candidate_ref"]["base_tree_oid"]
        git(worktree, "commit", "-m", "external commit after verification")
        self.assertNotEqual(expected_base, git(worktree, "rev-parse", "HEAD^{tree}"))

        provider_runner = FakeGitHubRunner()
        result = self.resume_events_in_process(
            "delivery-base-tree-drift",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        delivery = result["data"]["processed"][0]

        self.assertEqual("gated", delivery["result"])
        self.assertEqual("finalization-environment", delivery["gate"])
        self.assertIn("reconciliation required", delivery["reason"])
        self.assertEqual([], provider_runner.commands)
        self.assertNotEqual(
            "ticket-autopilot/delivery-base-tree-drift/01",
            git(worktree, "branch", "--show-current"),
        )

    def test_delivery_replays_after_crash_immediately_after_branch_creation(
        self,
    ) -> None:
        worktree = self.prepare_single_manual_run("delivery-branch-crash")
        expected_base_sha = git(worktree, "rev-parse", "HEAD")
        provider_runner = FakeGitHubRunner()
        from autopilot.finalizer import DeliveryFinalizer

        original_ensure_branch = DeliveryFinalizer._ensure_branch
        crashed = False

        def crash_after_branch(
            finalizer: DeliveryFinalizer,
            ticket_id: str,
            branch: str,
            base_branch: str,
            expected_base_tree_oid: str,
        ) -> str:
            nonlocal crashed
            base_sha = original_ensure_branch(
                finalizer,
                ticket_id,
                branch,
                base_branch,
                expected_base_tree_oid,
            )
            if not crashed:
                crashed = True
                raise RuntimeError("simulated crash after delivery branch creation")
            return base_sha

        with mock.patch.object(
            DeliveryFinalizer,
            "_ensure_branch",
            crash_after_branch,
        ), self.assertRaisesRegex(RuntimeError, "after delivery branch creation"):
            self.resume_events_in_process(
                "delivery-branch-crash",
                [{"operation": "delivery", "ticket_id": "01"}],
                provider_runner,
            )
        opened, _body, _prepared = self.complete_delivery(
            "delivery-branch-crash", "01", provider_runner
        )

        ticket = opened["data"]["tickets"]["01"]
        self.assertEqual("pr-open", ticket["state"])
        self.assertEqual(expected_base_sha, ticket["delivery_lineage"]["base_sha"])
        self.assertEqual(1, len(provider_runner.prs))

    def test_delivery_replays_after_crash_immediately_after_commit(self) -> None:
        worktree = self.prepare_single_manual_run("delivery-commit-crash")
        expected_base_sha = git(worktree, "rev-parse", "HEAD")
        provider_runner = FakeGitHubRunner()
        from autopilot.finalizer import DeliveryFinalizer

        with mock.patch.object(
            DeliveryFinalizer,
            "_ensure_push",
            side_effect=RuntimeError("simulated crash after delivery commit"),
        ), self.assertRaisesRegex(RuntimeError, "after delivery commit"):
            self.resume_events_in_process(
                "delivery-commit-crash",
                [{"operation": "delivery", "ticket_id": "01"}],
                provider_runner,
            )
        committed_head = git(worktree, "rev-parse", "HEAD")
        self.assertIn(
            "Ticket-Autopilot-Run: delivery-commit-crash/01",
            git(worktree, "log", "-1", "--format=%B"),
        )
        opened, _body, _prepared = self.complete_delivery(
            "delivery-commit-crash", "01", provider_runner
        )

        ticket = opened["data"]["tickets"]["01"]
        self.assertEqual("pr-open", ticket["state"])
        self.assertEqual(committed_head, ticket["pr"]["head_sha"])
        self.assertEqual(expected_base_sha, ticket["delivery_lineage"]["base_sha"])
        self.assertEqual(1, len(provider_runner.prs))

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
                "--max-leaf-interactions",
                "30",
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

        provider_runner = FakeGitHubRunner()
        invalid_prepared = self.resume_events_in_process(
            "delivery-test",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        invalid_request = invalid_prepared["data"]["processed"][0]
        invalid_candidate = invalid_prepared["data"]["tickets"]["01"][
            "candidate_ref"
        ]
        verified_bundle = verification_bundle(invalid_candidate)
        swapped_bundle = {**verified_bundle, "ticket_envelope_ref": "tickets/other.md"}
        swapped = self.resume_events_in_process(
            "delivery-test",
            [
                {
                    "operation": "delivery",
                    "ticket_id": "01",
                    "render_request_hash": invalid_request["render_request_hash"],
                    "expected_head_sha": invalid_request["head_sha"],
                    "rendered_body": valid_pr_body(verified_bundle),
                    "verification_bundle": swapped_bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            provider_runner,
        )
        self.assertEqual("gated", swapped["data"]["processed"][0]["result"])
        self.assertIn(
            "differs from the verified handoff bundle",
            swapped["data"]["processed"][0]["reason"],
        )
        invalid = self.resume_events_in_process(
            "delivery-test",
            [
                {
                    "operation": "delivery",
                    "ticket_id": "01",
                    "render_request_hash": invalid_request["render_request_hash"],
                    "expected_head_sha": invalid_request["head_sha"],
                    "rendered_body": "invalid body",
                    "verification_bundle": verified_bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            provider_runner,
        )
        self.assertEqual("gated", invalid["data"]["processed"][0]["result"])
        self.assertEqual(
            "delivery-pr-body", invalid["data"]["processed"][0]["gate"]
        )
        self.assertEqual({}, provider_runner.prs)
        provider_runner.readback_body_override = "provider-tampered body"
        tampered, body, _prepared = self.complete_delivery(
            "delivery-test", "01", provider_runner
        )
        self.assertEqual("gated", tampered["data"]["processed"][0]["result"])
        self.assertEqual(
            "delivery-pr-body", tampered["data"]["processed"][0]["gate"]
        )
        self.assertEqual(1, len(provider_runner.prs))
        provider_runner.readback_body_override = None
        opened = self.resume_events_in_process(
            "delivery-test",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        delivery = opened["data"]["processed"][0]
        self.assertEqual("pr-open", delivery["result"], delivery)
        self.assertEqual(
            {
                "last_phase": "readback",
                "result": "pr-open",
            },
            opened["data"]["tickets"]["01"]["delivery_progress"],
        )
        branch = delivery["branch"]
        head = delivery["head_sha"]
        pr_id = delivery["pr_id"]
        self.assertEqual(body, provider_runner.prs[pr_id]["body"])
        self.assertFalse(
            any(command[:3] == ["gh", "pr", "edit"] for command in provider_runner.commands)
        )
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
        child_opened, _child_body, _child_prepared = self.complete_delivery(
            "delivery-test", "02", provider_runner
        )
        child_delivery = child_opened["data"]["processed"][0]
        child_branch = child_delivery["branch"]
        child_head = child_delivery["head_sha"]
        child_pr_id = child_delivery["pr_id"]
        self.assertEqual("pr-open", child_opened["data"]["tickets"]["02"]["state"])

        stale_local_main = git(self.repo, "rev-parse", "main")
        integrated_main = git(
            self.repo,
            "commit-tree",
            f"{head}^{{tree}}",
            "-p",
            stale_local_main,
            "-m",
            "simulate provider squash merge",
        )
        git(
            self.repo,
            "push",
            "origin",
            f"{integrated_main}:refs/heads/main",
        )
        self.assertEqual(stale_local_main, git(self.repo, "rev-parse", "main"))
        integrated = self.approve_in_process(
            "delivery-test", "01", head, provider_runner
        )
        self.assertEqual("integrated", integrated["data"]["tickets"]["01"]["state"])
        self.assertEqual("integrated", integrated["data"]["approved"]["result"])
        self.assertEqual(1, provider_runner.merge_commands)
        merge_progress = integrated["data"]["tickets"]["01"][
            "merge_critical_path"
        ]
        self.assertEqual("integrated", merge_progress["phase"])
        self.assertEqual(head, merge_progress["head_sha"])
        self.assertGreaterEqual(merge_progress["elapsed_seconds"], 0)
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "delivery-test"
            / "ledger.json"
        )
        history_size = len(AtomicLedger(ledger_path).load()["history"])
        first_status = self.parse(
            run("status", "delivery-test", "--repo", str(self.repo), cwd=self.repo)
        )
        second_status = self.parse(
            run("status", "delivery-test", "--repo", str(self.repo), cwd=self.repo)
        )
        self.assertEqual(
            first_status["data"]["tickets"]["01"]["merge_critical_path"][
                "started_at"
            ],
            second_status["data"]["tickets"]["01"]["merge_critical_path"][
                "started_at"
            ],
        )
        self.assertEqual(
            history_size, len(AtomicLedger(ledger_path).load()["history"])
        )
        reconcile_event = {
            "operation": "reconcile",
            "ticket_id": "02",
            "parent_branch": branch,
            "base_branch": "main",
            "expected_remote_sha": child_head,
        }
        def fetch_then_move_tracking_ref(
            worktree_arg: Path,
            command_runner: object,
            base_branch_arg: str,
            *,
            boundary_guard: object = None,
        ) -> tuple[str, str, str]:
            fetched = _fetch_target_base(
                worktree_arg,
                command_runner,
                base_branch_arg,
                boundary_guard=boundary_guard,
            )
            git(worktree_arg, "update-ref", fetched[0], stale_local_main)
            return fetched

        with mock.patch(
            "autopilot.cli._fetch_target_base",
            side_effect=fetch_then_move_tracking_ref,
        ), mock.patch(
            "autopilot.cli.Kernel.prepare_reconciliation",
            side_effect=RuntimeError("simulated crash after rebase"),
        ), self.assertRaisesRegex(RuntimeError, "simulated crash after rebase"):
            self.resume_events_in_process(
                "delivery-test",
                [reconcile_event],
                provider_runner,
            )
        rebased_head = git(worktree, "rev-parse", "HEAD")
        self.assertNotEqual(child_head, rebased_head)
        crashed_ledger = AtomicLedger(ledger_path).load()
        intent = crashed_ledger["tickets"]["02"]["delivery"][
            "reconcile-intent"
        ]
        self.assertEqual(integrated_main, intent["target_base"]["sha"])
        self.assertNotIn(
            "reconcile-prepare",
            crashed_ledger["tickets"]["02"]["delivery"],
        )
        reconcile_prepared = self.resume_events_in_process(
            "delivery-test",
            [reconcile_event],
            provider_runner,
        )
        self.assertEqual(
            "evidence-preserved",
            reconcile_prepared["data"]["processed"][0]["result"],
        )
        self.assertEqual(
            rebased_head,
            reconcile_prepared["data"]["processed"][0]["new_head"],
        )
        preserved = reconcile_prepared["data"]["tickets"]["02"]
        self.assertEqual("verified", preserved["state"])
        self.assertEqual(
            child_opened["data"]["tickets"]["02"]["artifact_generation"],
            preserved["artifact_generation"],
        )
        self.assertEqual(
            child_opened["data"]["tickets"]["02"]["validated_stages"],
            preserved["validated_stages"],
        )
        self.assertEqual(
            child_opened["data"]["tickets"]["02"]["budgets"],
            preserved["budgets"],
        )
        advanced_main = git(
            self.repo,
            "commit-tree",
            f"{integrated_main}^{{tree}}",
            "-p",
            integrated_main,
            "-m",
            "advance target during reconciliation",
        )
        git(
            self.repo,
            "push",
            "origin",
            f"{advanced_main}:refs/heads/main",
        )
        base_drift = self.resume_events_in_process(
            "delivery-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            provider_runner,
        )
        drift_refresh = base_drift["data"]["processed"][0]
        self.assertEqual("evidence-preserved", drift_refresh["result"])
        self.assertTrue(drift_refresh["target_refreshed"])
        refreshed_ticket = base_drift["data"]["tickets"]["02"]
        self.assertEqual("verified", refreshed_ticket["state"])
        self.assertEqual(
            advanced_main,
            refreshed_ticket["delivery"]["reconcile-intent"]["target_base"][
                "sha"
            ],
        )
        self.assertEqual(
            1,
            len(refreshed_ticket["delivery"]["reconcile-attempt-history"]),
        )
        self.assertEqual(
            child_head,
            git(
                self.repo,
                "ls-remote",
                "--heads",
                "origin",
                f"refs/heads/{child_branch}",
            ).split()[0],
        )
        render_needed = self.resume_events_in_process(
            "delivery-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            provider_runner,
        )
        render_request = render_needed["data"]["processed"][0]
        self.assertEqual("render-required", render_request["result"])
        reconcile_bundle = verification_bundle(
            render_needed["data"]["tickets"]["02"]["candidate_ref"],
            ticket_id="02",
        )
        reconcile_body = valid_pr_body(
            reconcile_bundle,
            expected_head_sha=render_request["head_sha"],
        )
        render_event = {
            "operation": "reconcile",
            "ticket_id": "02",
            "render_request_hash": render_request["render_request_hash"],
            "expected_head_sha": render_request["head_sha"],
            "rendered_body": reconcile_body,
            "verification_bundle": reconcile_bundle,
            "verification_audit_root": str(ROOT / "verification-audit"),
        }

        target_checks = 0

        def fail_after_retarget(
            worktree_arg: Path,
            base_branch_arg: str,
            expected_sha: str,
        ) -> None:
            nonlocal target_checks
            target_checks += 1
            _assert_target_base_sha(
                worktree_arg,
                base_branch_arg,
                expected_sha,
            )
            if target_checks == 3:
                raise GitError("target base changed after provider retarget")

        with mock.patch(
            "autopilot.cli._assert_target_base_sha",
            side_effect=fail_after_retarget,
        ):
            retarget_race = self.resume_events_in_process(
                "delivery-test",
                [render_event],
                provider_runner,
            )
        retarget_gate = retarget_race["data"]["processed"][0]
        self.assertEqual(3, target_checks)
        self.assertEqual("gated", retarget_gate["result"])
        self.assertEqual("provider-retarget", retarget_gate["gate"])
        self.parse(
            run(
                "approve",
                "delivery-test",
                retarget_gate["gate_id"],
                "--repo",
                str(self.repo),
                "--actor",
                "qa",
                "--evidence",
                "target base re-observed",
                cwd=self.repo,
            )
        )
        reconciled = self.resume_events_in_process(
            "delivery-test",
            [{"operation": "reconcile", "ticket_id": "02"}],
            provider_runner,
        )
        reconciliation = reconciled["data"]["processed"][0]
        self.assertEqual("reconciled", reconciliation["result"], reconciliation)
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

    def test_delivery_revalidation_commits_and_pushes_a_new_candidate(self) -> None:
        remote = Path(self.directory.name) / "revalidation-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
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
                "delivery-revalidation-test",
                "--max-leaf-interactions",
                "30",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "delivery-revalidation-test",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / "implementation.txt").write_text("first candidate\n")
        git(worktree, "add", "-A")
        first_tree = git(worktree, "write-tree")
        self.resume_events(
            "delivery-revalidation-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": first_tree,
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

        provider_runner = FakeGitHubRunner()
        first = self.resume_events_in_process(
            "delivery-revalidation-test",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        first_request = first["data"]["processed"][0]
        self.assertEqual("render-required", first_request["result"])
        first_head = first_request["head_sha"]
        branch = first_request["branch"]
        self.assertEqual(
            first_head,
            git(
                self.repo,
                "ls-remote",
                "--heads",
                "origin",
                f"refs/heads/{branch}",
            ).split()[0],
        )

        (worktree / "implementation.txt").write_text("second candidate\n")
        git(worktree, "add", "implementation.txt")
        second_tree = git(worktree, "write-tree")
        revalidation = self.resume_events_in_process(
            "delivery-revalidation-test",
            [{"operation": "delivery-revalidate", "ticket_id": "01"}],
            provider_runner,
        )
        event = revalidation["data"]["processed"][0]
        self.assertEqual("revalidation-required", event["result"])
        self.assertEqual(second_tree, event["tree_oid"])
        ticket = revalidation["data"]["tickets"]["01"]
        self.assertEqual("active", ticket["state"])
        self.assertEqual("review", ticket["stage"])
        self.assertNotIn("pr-body-request", ticket["delivery"])
        self.assertNotIn("result", ticket["delivery"])

        self.resume_events(
            "delivery-revalidation-test",
            [
                {
                    "operation": "stage",
                    "ticket_id": "01",
                    "stage": stage,
                    "result": "pass",
                    "expected_tree_oid": second_tree,
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
        second = self.resume_events_in_process(
            "delivery-revalidation-test",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        second_request = second["data"]["processed"][0]
        self.assertEqual("render-required", second_request["result"])
        second_head = second_request["head_sha"]
        self.assertNotEqual(first_head, second_head)
        self.assertNotEqual(
            first_request["render_request_hash"],
            second_request["render_request_hash"],
        )
        self.assertEqual(
            first_head,
            git(worktree, "rev-parse", f"{second_head}^"),
        )
        self.assertEqual(
            second_head,
            git(
                self.repo,
                "ls-remote",
                "--heads",
                "origin",
                f"refs/heads/{branch}",
            ).split()[0],
        )

        candidate = second["data"]["tickets"]["01"]["candidate_ref"]
        bundle = verification_bundle(candidate)
        opened = self.resume_events_in_process(
            "delivery-revalidation-test",
            [
                {
                    "operation": "delivery",
                    "ticket_id": "01",
                    "render_request_hash": second_request[
                        "render_request_hash"
                    ],
                    "expected_head_sha": second_head,
                    "rendered_body": valid_pr_body(bundle),
                    "verification_bundle": bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
            provider_runner,
        )
        self.assertEqual("pr-open", opened["data"]["processed"][0]["result"])

    def test_runner_merge_recovers_lost_response_without_second_merge(self) -> None:
        git(self.repo, "rm", "tickets/02.md")
        git(self.repo, "commit", "-m", "single merge recovery ticket")
        remote = Path(self.directory.name) / "merge-recovery-remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            capture_output=True,
        )
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
                "merge-recovery-test",
                "--max-leaf-interactions",
                "20",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "merge-recovery-test",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / "implementation.txt").write_text("merge recovery\n")
        git(worktree, "add", "-A")
        tree = git(worktree, "write-tree")
        self.resume_events(
            "merge-recovery-test",
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
        runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            "merge-recovery-test", "01", runner
        )
        delivery = opened["data"]["processed"][0]
        head = delivery["head_sha"]
        runner.fail_after_merge_once = True

        gated = self.approve_in_process(
            "merge-recovery-test", "01", head, runner
        )

        ticket = gated["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertEqual("provider-merge", gated["data"]["approved"]["gate"])
        self.assertEqual(1, runner.merge_commands)
        self.assertEqual("gated", ticket["merge_critical_path"]["status"])

        recovered = self.approve_in_process(
            "merge-recovery-test", "01", head, runner
        )

        self.assertEqual("integrated", recovered["data"]["approved"]["result"])
        self.assertEqual("integrated", recovered["data"]["tickets"]["01"]["state"])
        self.assertEqual(1, runner.merge_commands)
        self.assertEqual([], recovered["data"]["open_gates"])
        replayed = self.approve_in_process(
            "merge-recovery-test", "01", head, runner
        )
        self.assertTrue(replayed["data"]["approved"]["replayed"])
        self.assertEqual(1, runner.merge_commands)

    def test_manual_merge_retries_after_a_pre_mutation_failure(self) -> None:
        self.prepare_single_manual_run("manual-merge-retry-test")
        runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            "manual-merge-retry-test", "01", runner
        )
        head = opened["data"]["processed"][0]["head_sha"]
        runner.fail_merge_before_apply_once = True

        gated = self.approve_in_process(
            "manual-merge-retry-test", "01", head, runner
        )
        self.assertEqual("gated", gated["data"]["tickets"]["01"]["state"])
        self.assertEqual(1, runner.merge_commands)

        recovered = self.approve_in_process(
            "manual-merge-retry-test", "01", head, runner
        )

        self.assertEqual(
            "integrated", recovered["data"]["tickets"]["01"]["state"]
        )
        self.assertEqual(2, runner.merge_commands)

    def test_manual_queue_crash_with_missing_entry_never_reenqueues(self) -> None:
        run_id = "manual-queue-missing-receipt-test"
        self.prepare_single_manual_run(run_id)
        runner = FakeGitHubRunner()
        runner.active_rules = [{"type": "merge_queue", "ruleset_id": 42}]
        opened, _body, _prepared = self.complete_delivery(run_id, "01", runner)
        head = opened["data"]["processed"][0]["head_sha"]

        self.crash_before_queue_mutation_receipt_save(
            run_id, runner, manual_head=head
        )
        runner.queue_entries.clear()
        resumed = self.approve_in_process(run_id, "01", head, runner)

        ticket = resumed["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn(
            "no durable mutation receipt",
            ticket["merge_critical_path"]["error"],
        )
        self.assertEqual(1, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

    def test_manual_queue_crash_never_falls_back_to_direct_merge(self) -> None:
        run_id = "manual-queue-policy-drift-test"
        self.prepare_single_manual_run(run_id)
        runner = FakeGitHubRunner()
        runner.active_rules = [{"type": "merge_queue", "ruleset_id": 42}]
        opened, _body, _prepared = self.complete_delivery(run_id, "01", runner)
        head = opened["data"]["processed"][0]["head_sha"]

        self.crash_before_queue_mutation_receipt_save(
            run_id, runner, manual_head=head
        )
        runner.active_rules = []
        resumed = self.approve_in_process(run_id, "01", head, runner)

        ticket = resumed["data"]["tickets"]["01"]
        self.assertEqual("gated", ticket["state"])
        self.assertIn("merge policy changed", ticket["merge_critical_path"]["error"])
        self.assertEqual(1, runner.queue_mutations)
        self.assertEqual(0, runner.merge_commands)

    def test_github_external_merge_fails_closed_and_recovers_after_save_crash(
        self,
    ) -> None:
        git(self.repo, "rm", "tickets/02.md")
        git(self.repo, "commit", "-m", "single GitHub ticket")
        remote = Path(self.directory.name) / "github-external-remote.git"
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
                "github",
                "--run-id",
                "github-external",
                cwd=self.repo,
            )
        )
        worktree = Path(created["data"]["worktree"])
        self.resume_events(
            "github-external",
            [{"operation": "activate", "ticket_id": "01"}],
        )
        (worktree / "github-external.txt").write_text("implementation\n")
        git(worktree, "add", "-A")
        implementation_tree = git(worktree, "write-tree")
        self.resume_events(
            "github-external",
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
        provider_runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            "github-external", "01", provider_runner
        )
        delivery = opened["data"]["processed"][0]
        head = delivery["head_sha"]
        pr_id = delivery["pr_id"]
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "github-external"
            / "ledger.json"
        )
        initial_history_size = len(AtomicLedger(ledger_path).load()["history"])

        def rejected_approval() -> dict[str, object]:
            output = io.StringIO()
            with redirect_stdout(output):
                result = cli_main(
                    [
                        "approve",
                        "github-external",
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
                        "--external-merge",
                    ],
                    command_runner=provider_runner,
                )
            self.assertNotEqual(0, result)
            return json.loads(output.getvalue())

        open_pr = rejected_approval()
        self.assertFalse(open_pr["ok"])
        provider_runner.prs[pr_id]["state"] = "CLOSED"
        closed_pr = rejected_approval()
        self.assertFalse(closed_pr["ok"])
        provider_runner.prs[pr_id]["state"] = "OPEN"
        provider_runner.prs[pr_id]["headRefOid"] = "different-head"
        mismatched_head = rejected_approval()
        self.assertFalse(mismatched_head["ok"])
        provider_runner.prs[pr_id]["headRefOid"] = head
        provider_runner.prs[pr_id]["number"] = 999
        wrong_pr = rejected_approval()
        self.assertFalse(wrong_pr["ok"])
        provider_runner.prs[pr_id]["number"] = int(pr_id)
        provider_runner.fail_get_pr_state_once = True
        provider_failure = rejected_approval()
        self.assertFalse(provider_failure["ok"])

        persisted = AtomicLedger(ledger_path).load()
        self.assertEqual(initial_history_size, len(persisted["history"]))
        self.assertEqual("pr-open", persisted["tickets"]["01"]["state"])
        self.assertIsNone(persisted["tickets"]["01"]["merge_authorization"])

        provider_runner.merge(pr_id, head)
        with mock.patch.object(
            AtomicLedger,
            "save",
            side_effect=LedgerError("simulated crash before ledger save"),
        ):
            crashed = rejected_approval()
        self.assertEqual("LedgerError", crashed["error"]["type"])
        persisted = AtomicLedger(ledger_path).load()
        self.assertEqual(initial_history_size, len(persisted["history"]))
        self.assertEqual("pr-open", persisted["tickets"]["01"]["state"])
        self.assertIsNone(persisted["tickets"]["01"]["merge_authorization"])

        integrated = self.approve_in_process(
            "github-external",
            "01",
            head,
            provider_runner,
            external_merge=True,
        )
        ticket = integrated["data"]["tickets"]["01"]
        self.assertEqual("integrated", ticket["state"])
        self.assertEqual("completed", integrated["data"]["run_state"])
        self.assertEqual(
            "external",
            ticket["delivery"]["external-reconciliation"]["mode"],
        )
        self.assertEqual(
            pr_id,
            integrated["data"]["approved"]["receipt"]["pr_id"],
        )
        persisted = AtomicLedger(ledger_path).load()
        self.assertEqual(initial_history_size + 3, len(persisted["history"]))
        self.assertEqual(
            "external-merge-integrated",
            persisted["history"][-3]["event"],
        )
        self.assertEqual(
            ["delivery-recorded", "delivery-recorded"],
            [item["event"] for item in persisted["history"][-2:]],
        )
        self.assertEqual(
            ("skipped", "absent"),
            (
                ticket["wiki_sync"]["result"]["status"],
                ticket["wiki_sync"]["result"]["reason"],
            ),
        )
        command_count = len(provider_runner.commands)
        history_size = len(persisted["history"])
        replayed = self.approve_in_process(
            "github-external",
            "01",
            head,
            provider_runner,
            external_merge=True,
        )
        self.assertTrue(replayed["data"]["approved"]["replayed"])
        self.assertEqual(
            integrated["data"]["approved"]["receipt"],
            replayed["data"]["approved"]["receipt"],
        )
        self.assertEqual(command_count, len(provider_runner.commands))
        self.assertEqual(
            history_size,
            len(AtomicLedger(ledger_path).load()["history"]),
        )
        self.assertFalse(
            any(
                command[:3] == ["gh", "pr", "merge"]
                for command in provider_runner.commands
            )
        )

    def test_integrate_adopts_exact_rebased_provider_head_before_terminal_proof(
        self,
    ) -> None:
        run_id = "github-equivalent-head"
        self.prepare_single_manual_run(run_id)
        provider_runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            run_id, "01", provider_runner
        )
        ticket = opened["data"]["tickets"]["01"]
        recorded_base = ticket["delivery_lineage"]["base_sha"]
        recorded_head = ticket["pr"]["head_sha"]
        pr_id = ticket["pr"]["pr_id"]
        self.assertEqual(
            recorded_base,
            git(self.repo, "rev-parse", f"{recorded_head}^"),
        )

        (self.repo / "provider-base.txt").write_text("advanced\n")
        git(self.repo, "add", "provider-base.txt")
        git(self.repo, "commit", "-m", "advance provider base")
        observed_base = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "push", "origin", f"{observed_base}:refs/heads/main")

        rebased = Path(self.directory.name) / "equivalent-head-rebase"
        git(self.repo, "worktree", "add", "--detach", str(rebased), observed_base)
        self.addCleanup(
            lambda: subprocess.run(
                ["git", "worktree", "remove", "--force", str(rebased)],
                cwd=self.repo,
                capture_output=True,
                check=False,
            )
        )
        git(rebased, "cherry-pick", recorded_head)
        observed_head = git(rebased, "rev-parse", "HEAD")
        merge_commit = git(
            rebased,
            "commit-tree",
            f"{observed_head}^{{tree}}",
            "-p",
            observed_base,
            "-p",
            observed_head,
            "-m",
            "provider merge of equivalent head",
        )
        git(rebased, "push", "origin", f"{merge_commit}:refs/heads/main")
        recorded_delta = subprocess.run(
            [
                "git",
                "diff-tree",
                "-r",
                "--no-commit-id",
                "--raw",
                "--full-index",
                "--no-renames",
                "-z",
                recorded_base,
                recorded_head,
            ],
            cwd=rebased,
            capture_output=True,
            check=True,
        ).stdout
        observed_delta = subprocess.run(
            [
                "git",
                "diff-tree",
                "-r",
                "--no-commit-id",
                "--raw",
                "--full-index",
                "--no-renames",
                "-z",
                observed_base,
                observed_head,
            ],
            cwd=rebased,
            capture_output=True,
            check=True,
        ).stdout
        self.assertEqual(recorded_delta, observed_delta)

        provider_pr = provider_runner.prs[pr_id]
        provider_pr["state"] = "MERGED"
        provider_pr["mergedAt"] = "2026-08-29T14:44:06Z"
        provider_pr["headRefOid"] = observed_head
        provider_pr["mergeCommit"] = {"oid": merge_commit}

        events_path = Path(self.directory.name) / "equivalent-head-crash-events.json"
        events_path.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "events": [
                        {"operation": "integrate", "ticket_id": "01"}
                    ],
                }
            )
        )
        output = io.StringIO()
        with mock.patch(
            "autopilot.cli._terminal_integration_proof",
            side_effect=ProviderError("simulated crash after equivalence save"),
        ), redirect_stdout(output):
            result = cli_main(
                [
                    "resume",
                    run_id,
                    "--repo",
                    str(self.repo),
                    "--events",
                    str(events_path),
                ],
                command_runner=provider_runner,
            )
        self.assertNotEqual(0, result)
        self.assertEqual("ProviderError", json.loads(output.getvalue())["error"]["type"])
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / run_id
            / "ledger.json"
        )
        after_crash = AtomicLedger(ledger_path).load()
        crashed_ticket = after_crash["tickets"]["01"]
        self.assertEqual("pr-open", crashed_ticket["state"])
        self.assertEqual(observed_head, crashed_ticket["pr"]["head_sha"])
        self.assertEqual(
            1,
            sum(
                event["event"] == "external-head-equivalent"
                for event in after_crash["history"]
            ),
        )

        integrated = self.resume_events_in_process(
            run_id,
            [{"operation": "integrate", "ticket_id": "01"}],
            provider_runner,
        )

        result = integrated["data"]["processed"][0]
        final_ticket = integrated["data"]["tickets"]["01"]
        equivalence = final_ticket["delivery"]["external-head-equivalence"]
        self.assertEqual("integrated", final_ticket["state"], integrated)
        self.assertEqual(observed_head, final_ticket["pr"]["head_sha"])
        self.assertEqual(
            observed_head, final_ticket["delivery_lineage"]["head_sha"]
        )
        self.assertEqual(recorded_head, equivalence["recorded_head_sha"])
        self.assertEqual(observed_head, equivalence["observed_head_sha"])
        self.assertEqual(
            hashlib.sha256(recorded_delta).hexdigest(),
            equivalence["raw_delta_sha256"],
        )
        self.assertIsNotNone(result["equivalent_head_receipt_digest"])
        self.assertEqual(recorded_head, result["recorded_head_sha"])
        self.assertEqual(observed_head, result["adopted_head_sha"])
        self.assertTrue(result["equivalent_head_replayed"])
        self.assertEqual(
            1,
            sum(
                event["event"] == "external-head-equivalent"
                for event in AtomicLedger(ledger_path).load()["history"]
            ),
        )
        self.assertEqual(
            "external-readback",
            final_ticket["delivery"]["terminal-integration"]["provenance"],
        )
        self.assertFalse(
            any(
                command[:3] == ["gh", "pr", "merge"]
                for command in provider_runner.commands
            )
        )
        history = AtomicLedger(
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / run_id
            / "ledger.json"
        ).load()["history"]
        names = [event["event"] for event in history]
        self.assertLess(
            names.index("external-head-equivalent"),
            names.index("external-merge-integrated"),
        )

    def test_github_external_merge_recovers_from_provider_merge_gate(self) -> None:
        self.prepare_single_manual_run("github-external-after-rules-403")
        provider_runner = FakeGitHubRunner()
        opened, _body, _prepared = self.complete_delivery(
            "github-external-after-rules-403", "01", provider_runner
        )
        delivery = opened["data"]["processed"][0]
        head = delivery["head_sha"]
        pr_id = delivery["pr_id"]
        provider_runner.fail_active_rules_once = True

        gated = self.approve_in_process(
            "github-external-after-rules-403", "01", head, provider_runner
        )

        self.assertEqual("gated", gated["data"]["tickets"]["01"]["state"])
        self.assertEqual("provider-merge", gated["data"]["approved"]["gate"])
        gate_id = gated["data"]["approved"]["gate_id"]
        self.assertEqual(0, provider_runner.merge_commands)

        provider_runner.merge(pr_id, head)
        integrated = self.approve_in_process(
            "github-external-after-rules-403",
            "01",
            head,
            provider_runner,
            external_merge=True,
        )

        ticket = integrated["data"]["tickets"]["01"]
        self.assertEqual("integrated", ticket["state"])
        self.assertEqual([], integrated["data"]["open_gates"])
        self.assertEqual("external", ticket["merge_authorization"]["mode"])
        self.assertEqual(0, provider_runner.merge_commands)
        persisted = AtomicLedger(
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "github-external-after-rules-403"
            / "ledger.json"
        ).load()
        gate = persisted["gates"][gate_id]
        self.assertEqual("passed", gate["state"])
        self.assertEqual("provider:github", gate["actor"])
        self.assertEqual(
            f"external-merge-live-readback:{pr_id}:{head}",
            gate["evidence"],
        )
        gate_event_index = next(
            index
            for index, item in enumerate(persisted["history"])
            if item["event"] == "gate-passed"
            and item["details"].get("gate_id") == gate_id
        )
        integration_event_index = next(
            index
            for index, item in enumerate(persisted["history"])
            if item["event"] == "external-merge-integrated"
            and item["ticket_id"] == "01"
        )
        self.assertLess(gate_event_index, integration_event_index)

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
        render_required = self.resume_events(
            "azure-external",
            [{"operation": "delivery", "ticket_id": "01"}],
        )
        request = render_required["data"]["processed"][0]
        self.assertEqual("render-required", request["result"], request)
        candidate = render_required["data"]["tickets"]["01"]["candidate_ref"]
        bundle = verification_bundle(candidate)
        prepared = self.resume_events(
            "azure-external",
            [
                {
                    "operation": "delivery",
                    "ticket_id": "01",
                    "render_request_hash": request["render_request_hash"],
                    "expected_head_sha": request["head_sha"],
                    "rendered_body": valid_pr_body(bundle),
                    "verification_bundle": bundle,
                    "verification_audit_root": str(ROOT / "verification-audit"),
                }
            ],
        )
        self.assertEqual(
            "gated",
            prepared["data"]["processed"][0]["result"],
        )
        self.assertEqual(
            "provider-environment",
            prepared["data"]["processed"][0]["gate"],
        )
        self.assertEqual(
            {
                "last_phase": "provider",
                "result": "gated",
                "gate": "provider-environment",
                "reason": prepared["data"]["processed"][0]["reason"],
            },
            prepared["data"]["tickets"]["01"]["delivery_progress"],
        )
        provider_runner = FakeAzureRunner()
        opened = self.resume_events_in_process(
            "azure-external",
            [{"operation": "delivery", "ticket_id": "01"}],
            provider_runner,
        )
        delivery = opened["data"]["processed"][0]
        self.assertEqual("pr-open", delivery["result"], delivery)
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
        provider_runner.merge(pr_id, head)
        approved = self.approve_in_process(
            "azure-external",
            "01",
            head,
            provider_runner,
            external_merge=True,
        )
        ticket = approved["data"]["tickets"]["01"]
        self.assertEqual(
            "external",
            ticket["merge_authorization"]["mode"],
        )
        self.assertEqual("integrated", approved["data"]["approved"]["result"])
        self.assertEqual("integrated", ticket["state"])
        self.assertEqual("completed", approved["data"]["run_state"])
        self.assertEqual(
            "live",
            ticket["delivery"]["integration"]["evidence_class"],
        )
        ledger_path = (
            self.repo
            / ".git"
            / "ticket-autopilot"
            / "runs"
            / "azure-external"
            / "ledger.json"
        )
        history_size = len(AtomicLedger(ledger_path).load()["history"])
        command_count = len(provider_runner.commands)
        replayed = self.approve_in_process(
            "azure-external",
            "01",
            head,
            provider_runner,
            external_merge=True,
        )
        self.assertTrue(replayed["data"]["approved"]["replayed"])
        self.assertEqual(command_count, len(provider_runner.commands))
        self.assertEqual(
            history_size,
            len(AtomicLedger(ledger_path).load()["history"]),
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
