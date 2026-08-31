from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.cli import main as cli_main
from autopilot.git_ops import CommandResult, run_directory
from autopilot.kernel import Kernel
from autopilot.ledger import AtomicLedger
from autopilot.providers import (
    CREATE_RUNNER_DEFECT_ISSUE,
    RUNNER_DEFECT_ISSUE_CAPABILITIES,
    SEARCH_RUNNER_DEFECT_ISSUES,
    AzureDevOpsProvider,
    GitHubProvider,
    ProviderError,
    ProviderExecutor,
)
from autopilot.runner_defect_issues import (
    TARGET_REPOSITORY,
    GitHubIssueAdapter,
    IssueOutbox,
    PublicationAuthority,
    RunnerDefectError,
    RunnerDefectEscalator,
    SimulatedIssueCrash,
    defect_fingerprint,
    marker_for,
    render_issue,
    protected_run_ledger,
    target_repository_from_remote,
    validate_defect_record,
)
from autopilot.ticket_contract import Ticket, TicketGraph


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def make_repo(root: Path, *, remote: str = "git@github.com:carlitose/agent-skills.git") -> Path:
    repo = root / "repo"
    repo.mkdir()
    git(repo, "init")
    git(repo, "remote", "add", "origin", remote)
    return repo


def make_run_ledger(repo: Path, run_id: str = "example-run") -> tuple[Path, str]:
    folder = repo / "tickets"
    folder.mkdir(exist_ok=True)
    ticket_path = folder / "ticket.md"
    ticket_path.write_text("ticket", encoding="utf-8")
    ticket_digest = "e" * 64
    graph = TicketGraph(
        folder=folder,
        tickets={
            "RD-X": Ticket(
                ticket_id="RD-X",
                execution_mode="AFK",
                blocked_by=(),
                path=ticket_path,
                digest=ticket_digest,
            )
        },
        order=("RD-X",),
        completed_ids=frozenset(),
    )
    ledger = Kernel.new(
        run_id,
        graph,
        provider="github",
        repo=str(repo),
        worktree=str(repo),
        base_sha="0" * 40,
    ).ledger
    path = run_directory(repo, run_id) / "ledger.json"
    AtomicLedger(path).save(ledger)
    return path, ticket_digest


def binding() -> dict[str, object]:
    return {
        "schema": 1,
        "run_id": "example-run",
        "ledger_sha256": "d" * 64,
        "ticket_id": "RD-X",
        "ticket_digest": "e" * 64,
    }


def record() -> dict[str, object]:
    return {
        "schema": 1,
        "classification": "runner-defect",
        "repository": TARGET_REPOSITORY,
        "run_binding": binding(),
        "owner": {
            "component": "ticket-autopilot",
            "module": "autopilot.kernel",
            "anchor": "Kernel.preflight_mutation_boundary",
        },
        "failure": {
            "code": "mutation-boundary-regression",
            "phase": "pre-provider-mutation",
            "invariant": "A canonical ticket must pass the last safe mutation check.",
            "symptom": "The deterministic fixture rejects the unchanged ticket.",
            "exception_family": "TransitionError",
        },
        "confidence": {
            "level": "high",
            "basis": ["deterministic-reproduction", "runner-source-trace"],
        },
        "feedback_loop": {
            "kind": "unit-test",
            "anchor": "ticket-autopilot.tests.test_kernel.Example.test_case",
            "observed": "The baseline fails with the sanitized invariant mismatch.",
            "artifact_sha256": "a" * 64,
        },
        "evidence": [
            {
                "class": "local-deterministic",
                "summary": "The valid fixture reaches the incorrect rejection branch.",
                "artifact_sha256": "b" * 64,
            },
            {
                "class": "static-source",
                "summary": "The source trace identifies the reversed boundary condition.",
                "artifact_sha256": "c" * 64,
            },
        ],
        "redaction": {
            "contract": "diagnose/references/secret-redaction.md",
            "applied": True,
        },
    }


def normalized_record() -> dict[str, object]:
    return validate_defect_record(
        record(),
        run_id="example-run",
        ledger_sha256="d" * 64,
        ledger={"tickets": {"RD-X": {"ticket_digest": "e" * 64}}},
    )


def issue_receipt(
    fingerprint: str,
    *,
    number: int = 11,
    state: str = "open",
    operation: str = CREATE_RUNNER_DEFECT_ISSUE,
    body: str | None = None,
) -> dict[str, object]:
    return {
        "schema": 1,
        "provider": "github",
        "operation": operation,
        "evidence_class": "live",
        "observed": True,
        "repository": TARGET_REPOSITORY,
        "fingerprint": fingerprint,
        "issue_number": number,
        "url": f"https://github.com/{TARGET_REPOSITORY}/issues/{number}",
        "state": state,
        "title": "[Runner defect] example",
        "body": body or marker_for(fingerprint),
        "labels": ["bug"],
    }


class FakeIssueAdapter:
    def __init__(self) -> None:
        self.issues: list[dict[str, object]] = []
        self.search_calls = 0
        self.create_calls = 0
        self.search_error: Exception | None = None
        self.create_error: Exception | None = None
        self.create_then_error = False

    def search_exact(self, repository: str, fingerprint: str) -> dict[str, object]:
        self.search_calls += 1
        if self.search_error is not None:
            raise self.search_error
        return {
            "schema": 1,
            "provider": "github",
            "operation": SEARCH_RUNNER_DEFECT_ISSUES,
            "evidence_class": "live",
            "observed": True,
            "repository": repository,
            "fingerprint": fingerprint,
            "conclusive": True,
            "candidate_count": len(self.issues),
            "matches": list(self.issues),
        }

    def create(
        self, repository: str, fingerprint: str, title: str, body: str
    ) -> dict[str, object]:
        self.create_calls += 1
        created = issue_receipt(fingerprint, body=body)
        if self.create_then_error:
            self.issues.append(created)
        if self.create_error is not None:
            raise self.create_error
        self.issues.append(created)
        return created


class PublicationAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = make_repo(Path(self.temp.name))
        self.authority = PublicationAuthority(self.repo)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_grant_is_idempotent_and_inspectable(self) -> None:
        first = self.authority.grant(actor="user:carlo", evidence="decision://grant/1")
        second = self.authority.grant(actor="user:carlo", evidence="decision://grant/1")
        self.assertEqual(first, second)
        status = self.authority.inspect()
        self.assertEqual(status["active_grant"], first)
        self.assertEqual(status["grant_count"], 1)

    def test_distinct_active_grant_is_rejected(self) -> None:
        self.authority.grant(actor="user:carlo", evidence="decision://grant/1")
        with self.assertRaisesRegex(RunnerDefectError, "distinct"):
            self.authority.grant(actor="user:other", evidence="decision://grant/2")

    def test_exact_revocation_blocks_and_regrant_requires_fresh_evidence(self) -> None:
        grant = self.authority.grant(actor="user:carlo", evidence="decision://grant/1")
        self.authority.revoke(
            authority_id=grant["authority_id"],
            actor="user:carlo",
            evidence="decision://revoke/1",
        )
        with self.assertRaisesRegex(RunnerDefectError, "not authorized"):
            self.authority.require_active()
        with self.assertRaisesRegex(RunnerDefectError, "was revoked"):
            self.authority.grant(actor="user:carlo", evidence="decision://grant/1")
        replacement = self.authority.grant(
            actor="user:carlo", evidence="decision://grant/2"
        )
        self.assertNotEqual(replacement["authority_id"], grant["authority_id"])

    def test_wrong_revocation_identity_fails_closed(self) -> None:
        self.authority.grant(actor="user:carlo", evidence="decision://grant/1")
        with self.assertRaisesRegex(RunnerDefectError, "exact active"):
            self.authority.revoke(
                authority_id="rdip-wrong",
                actor="user:carlo",
                evidence="decision://revoke/1",
            )

    def test_actor_and_evidence_reject_embedded_line_breaks(self) -> None:
        for actor, evidence in (
            ("user:carlo\nuser:other", "decision://grant/1"),
            ("user:carlo", "decision://grant/1\rforged"),
        ):
            with self.subTest(actor=actor, evidence=evidence), self.assertRaisesRegex(
                RunnerDefectError, "safe text"
            ):
                self.authority.grant(actor=actor, evidence=evidence)

    def test_corrupt_authority_fails_integrity_validation(self) -> None:
        self.authority.grant(actor="user:carlo", evidence="decision://grant/1")
        self.authority.store.path.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(RunnerDefectError, "integrity"):
            self.authority.inspect()


class RecordContractTests(unittest.TestCase):
    def test_strict_record_is_accepted_and_stable(self) -> None:
        first = normalized_record()
        second = normalized_record()
        self.assertEqual(defect_fingerprint(first), defect_fingerprint(second))
        title, body = render_issue(first, defect_fingerprint(first))
        self.assertTrue(title.startswith("[Runner defect]"))
        self.assertIn(marker_for(defect_fingerprint(first)), body)
        self.assertNotIn("example-run", body)

    def test_fingerprint_excludes_wording_but_binds_diagnostic_signature(self) -> None:
        first = normalized_record()
        changed = copy.deepcopy(first)
        changed["failure"]["symptom"] = "Different sanitized wording."
        self.assertEqual(defect_fingerprint(first), defect_fingerprint(changed))
        changed["failure"]["code"] = "different-code"
        self.assertNotEqual(defect_fingerprint(first), defect_fingerprint(changed))

    def test_stale_run_binding_is_rejected(self) -> None:
        with self.assertRaisesRegex(RunnerDefectError, "missing or stale"):
            validate_defect_record(
                record(),
                run_id="example-run",
                ledger_sha256="f" * 64,
                ledger={"tickets": {"RD-X": {"ticket_digest": "e" * 64}}},
            )

    def test_low_confidence_is_rejected(self) -> None:
        value = record()
        value["confidence"]["level"] = "medium"
        with self.assertRaisesRegex(RunnerDefectError, "confidence"):
            validate_defect_record(
                value,
                run_id="example-run",
                ledger_sha256="d" * 64,
                ledger={"tickets": {"RD-X": {"ticket_digest": "e" * 64}}},
            )

    def test_missing_source_evidence_is_rejected(self) -> None:
        value = record()
        value["evidence"][1]["class"] = "local-deterministic"
        with self.assertRaisesRegex(RunnerDefectError, "both eligibility"):
            validate_defect_record(
                value,
                run_id="example-run",
                ledger_sha256="d" * 64,
                ledger={"tickets": {"RD-X": {"ticket_digest": "e" * 64}}},
            )

    def test_secret_and_local_path_material_are_rejected(self) -> None:
        for unsafe in ("token=ghp_abcdefghijklmnopqrstuvwxyz", "/Users/carlo/private"):
            value = record()
            value["failure"]["symptom"] = unsafe
            with self.subTest(unsafe=unsafe), self.assertRaisesRegex(
                RunnerDefectError, "secret or local-path"
            ):
                validate_defect_record(
                    value,
                    run_id="example-run",
                    ledger_sha256="d" * 64,
                    ledger={"tickets": {"RD-X": {"ticket_digest": "e" * 64}}},
                )

    def test_target_normalization_accepts_only_exact_repository(self) -> None:
        self.assertEqual(
            target_repository_from_remote(
                "https://github.com/carlitose/agent-skills.git"
            ),
            TARGET_REPOSITORY,
        )
        self.assertEqual(
            target_repository_from_remote(
                "git@github.com:carlitose/agent-skills.git"
            ),
            TARGET_REPOSITORY,
        )
        for remote in (
            "https://github.com/carlitose/agent-skills-lookalike.git",
            "https://example.com/carlitose/agent-skills.git",
        ):
            with self.subTest(remote=remote), self.assertRaises(RunnerDefectError):
                target_repository_from_remote(remote)


class EscalationLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = make_repo(Path(self.temp.name))
        self.authority = PublicationAuthority(self.repo)
        self.grant = self.authority.grant(
            actor="user:carlo", evidence="decision://grant/1"
        )
        self.adapter = FakeIssueAdapter()
        self.escalator = RunnerDefectEscalator(
            self.authority, IssueOutbox(self.repo), self.adapter
        )
        self.record = normalized_record()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_dry_run_writes_no_outbox_and_calls_no_provider(self) -> None:
        result = self.escalator.dry_run(self.record)
        self.assertEqual(result.state, "dry-run")
        self.assertFalse(IssueOutbox(self.repo).root.exists())
        self.assertEqual(self.adapter.search_calls, 0)

    def test_new_issue_is_created_once_with_bound_receipt(self) -> None:
        result = self.escalator.escalate(self.record)
        self.assertEqual(result.state, "published")
        self.assertEqual(result.disposition, "created")
        self.assertEqual(self.adapter.create_calls, 1)
        self.assertEqual(result.receipt["authority_id"], self.grant["authority_id"])
        self.assertEqual(result.receipt["actor"], "user:carlo")
        self.assertEqual(result.receipt["repository"], TARGET_REPOSITORY)
        self.assertEqual(len(result.receipt["sanitized_body_sha256"]), 64)
        self.assertEqual(result.receipt["provider"]["name"], "github")

    def test_open_or_closed_exact_match_deduplicates_without_create(self) -> None:
        for state in ("open", "closed"):
            with self.subTest(state=state):
                temp = tempfile.TemporaryDirectory()
                repo = make_repo(Path(temp.name))
                authority = PublicationAuthority(repo)
                authority.grant(actor="user:carlo", evidence="decision://grant/1")
                adapter = FakeIssueAdapter()
                fingerprint = defect_fingerprint(self.record)
                adapter.issues = [issue_receipt(fingerprint, state=state)]
                result = RunnerDefectEscalator(
                    authority, IssueOutbox(repo), adapter
                ).escalate(self.record)
                self.assertEqual(result.state, "deduplicated")
                self.assertEqual(result.disposition, "deduplicated")
                self.assertEqual(adapter.create_calls, 0)
                temp.cleanup()

    def test_final_replay_has_no_provider_effect(self) -> None:
        first = self.escalator.escalate(self.record)
        searches = self.adapter.search_calls
        creates = self.adapter.create_calls
        second = self.escalator.escalate(self.record)
        self.assertEqual(second.outbox_sha256, first.outbox_sha256)
        self.assertEqual(self.adapter.search_calls, searches)
        self.assertEqual(self.adapter.create_calls, creates)

    def test_crash_after_create_recovers_by_read_only_exact_search(self) -> None:
        with self.assertRaises(SimulatedIssueCrash):
            self.escalator.escalate(self.record, crash_at="after-create")
        self.assertEqual(self.adapter.create_calls, 1)
        result = self.escalator.escalate(self.record)
        self.assertEqual(result.state, "deduplicated")
        self.assertEqual(self.adapter.create_calls, 1)

    def test_known_non_send_crash_can_retry_after_fresh_search(self) -> None:
        with self.assertRaises(SimulatedIssueCrash):
            self.escalator.escalate(self.record, crash_at="before-create")
        self.assertEqual(self.adapter.create_calls, 0)
        result = self.escalator.escalate(self.record)
        self.assertEqual(result.state, "published")
        self.assertEqual(self.adapter.create_calls, 1)

    def test_lost_response_with_visible_issue_deduplicates_on_replay(self) -> None:
        self.adapter.create_then_error = True
        self.adapter.create_error = ProviderError("response lost")
        first = self.escalator.escalate(self.record)
        self.assertEqual(first.state, "dispatch-ambiguous")
        self.adapter.create_error = None
        second = self.escalator.escalate(self.record)
        self.assertEqual(second.state, "deduplicated")
        self.assertEqual(self.adapter.create_calls, 1)

    def test_ambiguous_send_without_match_never_retries_create(self) -> None:
        self.adapter.create_error = ProviderError("unknown dispatch outcome")
        first = self.escalator.escalate(self.record)
        self.assertEqual(first.state, "dispatch-ambiguous")
        self.adapter.create_error = None
        second = self.escalator.escalate(self.record)
        self.assertEqual(second.state, "dispatch-ambiguous")
        self.assertEqual(second.receipt, None)
        self.assertEqual(self.adapter.create_calls, 1)

    def test_revocation_blocks_new_dispatch_but_allows_ambiguous_readback(self) -> None:
        self.adapter.create_error = ProviderError("unknown dispatch outcome")
        self.escalator.escalate(self.record)
        self.authority.revoke(
            authority_id=self.grant["authority_id"],
            actor="user:carlo",
            evidence="decision://revoke/1",
        )
        self.adapter.create_error = None
        result = self.escalator.escalate(self.record)
        self.assertEqual(result.state, "dispatch-ambiguous")
        self.assertEqual(self.adapter.create_calls, 1)

    def test_revoked_grant_blocks_new_reservation(self) -> None:
        self.authority.revoke(
            authority_id=self.grant["authority_id"],
            actor="user:carlo",
            evidence="decision://revoke/1",
        )
        with self.assertRaisesRegex(RunnerDefectError, "not authorized"):
            self.escalator.escalate(self.record)
        self.assertEqual(self.adapter.search_calls, 0)

    def test_multiple_exact_matches_fail_without_mutation(self) -> None:
        fingerprint = defect_fingerprint(self.record)
        self.adapter.issues = [
            issue_receipt(fingerprint, number=11),
            issue_receipt(fingerprint, number=12),
        ]
        result = self.escalator.escalate(self.record)
        self.assertEqual(result.state, "search-failed")
        self.assertEqual(self.adapter.create_calls, 0)

    def test_search_failure_is_retryable_before_any_send(self) -> None:
        self.adapter.search_error = ProviderError("search unavailable")
        first = self.escalator.escalate(self.record)
        self.assertEqual(first.state, "search-failed")
        self.adapter.search_error = None
        second = self.escalator.escalate(self.record)
        self.assertEqual(second.state, "published")
        self.assertEqual(self.adapter.create_calls, 1)

    def test_contradictory_provider_receipt_never_finalizes(self) -> None:
        fingerprint = defect_fingerprint(self.record)
        bad = issue_receipt(fingerprint)
        bad["repository"] = "other/repository"
        self.adapter.issues = [bad]
        result = self.escalator.escalate(self.record)
        self.assertEqual(result.state, "search-failed")
        self.assertIsNone(result.receipt)


class FakeGitHubIssueRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.issues: dict[int, dict[str, object]] = {}

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(command)
        if command[:3] == ["gh", "issue", "list"]:
            return CommandResult(json.dumps(list(self.issues.values())), "", 0)
        if command[:3] == ["gh", "issue", "create"]:
            number = 21
            self.issues[number] = {
                "number": number,
                "url": f"https://github.com/{TARGET_REPOSITORY}/issues/{number}",
                "state": "OPEN",
                "title": command[command.index("--title") + 1],
                "body": command[command.index("--body") + 1],
                "labels": [{"name": command[command.index("--label") + 1]}],
            }
            return CommandResult(self.issues[number]["url"] + "\n", "", 0)
        if command[:3] == ["gh", "issue", "view"]:
            number = int(command[3])
            return CommandResult(json.dumps(self.issues[number]), "", 0)
        return CommandResult("", "unexpected command", 1)


class ProviderIssueOperationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = make_repo(Path(self.temp.name))
        self.runner = FakeGitHubIssueRunner()
        self.executor = ProviderExecutor(
            GitHubProvider(), cwd=self.repo, runner=self.runner
        )
        self.adapter = GitHubIssueAdapter(self.executor)
        self.fingerprint = "a" * 64

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_github_negotiates_issue_capabilities_and_azure_rejects(self) -> None:
        GitHubProvider().negotiate(RUNNER_DEFECT_ISSUE_CAPABILITIES)
        with self.assertRaisesRegex(ProviderError, "lacks required"):
            AzureDevOpsProvider().negotiate(RUNNER_DEFECT_ISSUE_CAPABILITIES)

    def test_exact_search_filters_decoys_and_includes_closed_issues(self) -> None:
        self.runner.issues = {
            1: {
                "number": 1,
                "url": f"https://github.com/{TARGET_REPOSITORY}/issues/1",
                "state": "CLOSED",
                "title": "match",
                "body": marker_for(self.fingerprint),
                "labels": [{"name": "bug"}],
            },
            2: {
                "number": 2,
                "url": f"https://github.com/{TARGET_REPOSITORY}/issues/2",
                "state": "OPEN",
                "title": "decoy",
                "body": "same search term but no marker",
                "labels": [],
            },
        }
        receipt = self.adapter.search_exact(TARGET_REPOSITORY, self.fingerprint)
        self.assertTrue(receipt["conclusive"])
        self.assertEqual([item["issue_number"] for item in receipt["matches"]], [1])
        command = self.runner.commands[0]
        self.assertEqual(command[command.index("--repo") + 1], TARGET_REPOSITORY)
        self.assertEqual(command[command.index("--state") + 1], "all")

    def test_create_uses_only_bug_label_and_exact_readback(self) -> None:
        body = "sanitized\n\n" + marker_for(self.fingerprint)
        receipt = self.adapter.create(
            TARGET_REPOSITORY, self.fingerprint, "safe title", body
        )
        self.assertEqual(receipt["issue_number"], 21)
        self.assertEqual(receipt["body"], body)
        create = self.runner.commands[0]
        self.assertEqual(create[create.index("--label") + 1], "bug")
        self.assertNotIn("comment", create)

    def test_contradictory_issue_url_is_rejected(self) -> None:
        self.runner.issues = {
            1: {
                "number": 1,
                "url": "https://github.com/other/repository/issues/1",
                "state": "OPEN",
                "title": "match",
                "body": marker_for(self.fingerprint),
                "labels": [{"name": "bug"}],
            }
        }
        with self.assertRaisesRegex(ProviderError, "malformed"):
            self.adapter.search_exact(TARGET_REPOSITORY, self.fingerprint)

    def test_wrong_repository_fails_before_command(self) -> None:
        with self.assertRaisesRegex(ProviderError, "exactly"):
            self.adapter.search_exact("other/repository", self.fingerprint)
        self.assertEqual(self.runner.commands, [])


class ProtectedRunLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = make_repo(Path(self.temp.name))
        self.path, ticket_digest = make_run_ledger(self.repo)
        self.record = record()
        self.record["run_binding"]["ledger_sha256"] = hashlib.sha256(
            self.path.read_bytes()
        ).hexdigest()
        self.record["run_binding"]["ticket_digest"] = ticket_digest

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_context_preserves_run_ledger_byte_for_byte(self) -> None:
        before = self.path.read_bytes()
        with protected_run_ledger(self.repo, "example-run", self.record) as (
            normalized,
            ledger,
            digest,
        ):
            self.assertEqual(normalized["classification"], "runner-defect")
            self.assertIn("RD-X", ledger["tickets"])
            self.assertEqual(digest, hashlib.sha256(before).hexdigest())
        self.assertEqual(self.path.read_bytes(), before)

    def test_context_detects_any_noncanonical_run_mutation(self) -> None:
        with self.assertRaisesRegex(RunnerDefectError, "changed protected"):
            with protected_run_ledger(self.repo, "example-run", self.record):
                self.path.write_bytes(self.path.read_bytes() + b" ")


class CliAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = make_repo(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def call(
        self,
        *arguments: str,
        runner: FakeGitHubIssueRunner | None = None,
    ) -> tuple[int, dict[str, object]]:
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = cli_main(list(arguments), command_runner=runner)
        return code, json.loads(stream.getvalue())

    def test_grant_status_and_revoke_commands_are_separate_from_run_state(self) -> None:
        code, granted = self.call(
            "runner-defect-issue-grant",
            "--repo",
            str(self.repo),
            "--actor",
            "user:carlo",
            "--evidence",
            "decision://grant/1",
        )
        self.assertEqual(code, 0)
        authority_id = granted["data"]["grant"]["authority_id"]
        code, status = self.call(
            "runner-defect-issue-status", "--repo", str(self.repo)
        )
        self.assertEqual(code, 0)
        self.assertEqual(status["data"]["active_grant"]["authority_id"], authority_id)
        code, revoked = self.call(
            "runner-defect-issue-revoke",
            authority_id,
            "--repo",
            str(self.repo),
            "--actor",
            "user:carlo",
            "--evidence",
            "decision://revoke/1",
        )
        self.assertEqual(code, 0)
        self.assertEqual(revoked["data"]["revocation"]["authority_id"], authority_id)

    def test_dry_run_validates_real_run_without_provider_or_outbox_mutation(self) -> None:
        path, ticket_digest = make_run_ledger(self.repo)
        value = record()
        value["run_binding"]["ledger_sha256"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        value["run_binding"]["ticket_digest"] = ticket_digest
        record_path = Path(self.temp.name) / "record.json"
        record_path.write_text(json.dumps(value), encoding="utf-8")
        PublicationAuthority(self.repo).grant(
            actor="user:carlo", evidence="decision://grant/1"
        )
        before = path.read_bytes()
        code, result = self.call(
            "runner-defect-issue-escalate",
            "example-run",
            str(record_path),
            "--repo",
            str(self.repo),
            "--dry-run",
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["data"]["state"], "dry-run")
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse(IssueOutbox(self.repo).root.exists())

    def test_live_command_uses_provider_seam_and_preserves_real_run_ledger(self) -> None:
        path, ticket_digest = make_run_ledger(self.repo)
        value = record()
        value["run_binding"]["ledger_sha256"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        value["run_binding"]["ticket_digest"] = ticket_digest
        record_path = Path(self.temp.name) / "live-record.json"
        record_path.write_text(json.dumps(value), encoding="utf-8")
        PublicationAuthority(self.repo).grant(
            actor="user:carlo", evidence="decision://grant/1"
        )
        before = path.read_bytes()
        runner = FakeGitHubIssueRunner()
        code, result = self.call(
            "runner-defect-issue-escalate",
            "example-run",
            str(record_path),
            "--repo",
            str(self.repo),
            runner=runner,
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["data"]["state"], "published")
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(
            [command[:3] for command in runner.commands],
            [["gh", "issue", "list"], ["gh", "issue", "create"], ["gh", "issue", "view"]],
        )

    def test_wrong_origin_rejects_grant_before_authority_file(self) -> None:
        git(self.repo, "remote", "set-url", "origin", "git@github.com:other/repo.git")
        code, result = self.call(
            "runner-defect-issue-grant",
            "--repo",
            str(self.repo),
            "--actor",
            "user:carlo",
            "--evidence",
            "decision://grant/1",
        )
        self.assertEqual(code, 2)
        self.assertEqual(result["error"]["type"], "RunnerDefectError")
        self.assertFalse(PublicationAuthority(self.repo).store.path.exists())


if __name__ == "__main__":
    unittest.main()
