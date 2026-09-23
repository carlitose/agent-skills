"""Every rejection reproduced here cost a real run several turns of reading runner source.

The three cases are the ones observed in the q2 autopilot benchmark session, at turns 120,
128 and 131 (see `docs/specs/autopilot-protocol-friction-wayfinder.md`). Each asserts the
invariant still holds, the message is unchanged, and the rejection now names the field, what
was received, what was expected, and the next event or command that corrects it.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if __package__:
    from .git_test_support import GitIsolatedTestCase
    from .test_cli import configure_test_origin
else:
    from git_test_support import GitIsolatedTestCase
    from test_cli import configure_test_origin

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
sys.path.insert(0, str(SCRIPTS))

from autopilot.kernel import CandidateRef, Kernel, TransitionError
from autopilot.leaf_protocol import (
    LEAF_PHASE_CONTRACTS,
    LeafProtocolError,
    validate_leaf_result,
)
from autopilot.ticket_contract import parse_ticket_folder

DETAIL_FIELDS = {"field", "received", "expected", "next_step"}


def ticket_text(ticket_id: str) -> str:
    return (
        "---\n"
        "ticket_schema: 1\n"
        f'ticket_id: "{ticket_id}"\n'
        "execution_mode: AFK\n"
        "blocked_by: []\n"
        "---\n\n"
        f"# Ticket {ticket_id}\n\n"
        "## What to Build\nA thing.\n\n"
        "## Acceptance Criteria\n- [ ] It works.\n\n"
        "## Frontier\nReady.\n\n"
        "## Step-by-Step Implementation Plan\n1. Do it.\n\n"
        "## Testing Plan\nRun the tests.\n\n"
        "## Out of Scope\n- Everything else.\n"
    )


def leaf_result(candidate: CandidateRef, stage: str, *, quality: bool) -> dict:
    document = {
        "schema": 3,
        "complete": True,
        "candidate_ref": {
            "base_tree_oid": candidate.base_tree_oid,
            "candidate_tree_oid": candidate.candidate_tree_oid,
            "ticket_digest": candidate.ticket_digest,
            "contract_version": candidate.contract_version,
        },
        "stage": stage,
        "phase_contract": list(LEAF_PHASE_CONTRACTS[stage]),
        "scope": {"files_expected": [], "files_inspected": [], "files_remaining": []},
        "phases_remaining": [],
        "commands_run": [],
        "findings": [],
        "progress_phase": "handoff-ready",
        "stop_reason": None,
    }
    if quality:
        document["quality"] = {
            "schema": 1,
            "causal_scope": [stage],
            "evidence": [
                {
                    "id": f"evidence:{stage}",
                    "artifact": f"{stage}.json",
                    "sha256": "a" * 64,
                    "result": "pass",
                    "candidate_ref": document["candidate_ref"],
                }
            ],
            "limitations": ["local-only"],
        }
    return document


class RejectionDetailTests(unittest.TestCase):
    def kernel(self, *ticket_ids: str) -> Kernel:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        folder = Path(directory.name)
        for index, ticket_id in enumerate(ticket_ids):
            (folder / f"{index}.md").write_text(
                ticket_text(ticket_id), encoding="utf-8", newline="\n"
            )
        return Kernel.new("run-detail", parse_ticket_folder(folder), provider="github")

    @staticmethod
    def candidate(suffix: str = "a") -> CandidateRef:
        return CandidateRef(
            base_tree_oid=f"base-{suffix}",
            candidate_tree_oid=f"tree-{suffix}",
            ticket_digest=f"ticket-{suffix}",
            contract_version=2,
        )

    def assert_detail(self, detail: object) -> dict:
        self.assertIsInstance(detail, dict)
        assert isinstance(detail, dict)
        self.assertEqual(DETAIL_FIELDS, set(detail))
        self.assertIsInstance(detail["field"], str)
        self.assertTrue(detail["field"])
        self.assertIsInstance(detail["next_step"], str)
        self.assertTrue(detail["next_step"].strip())
        return detail

    def test_second_activate_names_the_active_ticket_and_its_next_event(self) -> None:
        """Turn 128 of the q2 session: 'another ticket is already active'."""
        kernel = self.kernel("01", "02")
        candidate = self.candidate()
        kernel.activate("01", candidate)
        before = json.dumps(kernel.ledger, sort_keys=True)

        with self.assertRaises(TransitionError) as caught:
            kernel.activate("02", candidate)

        self.assertEqual("another ticket is already active", str(caught.exception))
        detail = self.assert_detail(caught.exception.detail)
        self.assertEqual("tickets.<id>.state", detail["field"])
        self.assertEqual("01", detail["received"]["active_ticket_id"])
        self.assertEqual("02", detail["received"]["requested_ticket_id"])
        self.assertEqual("implement", detail["received"]["stage"])
        self.assertIn("'01'", detail["next_step"])
        self.assertIn("stage", detail["next_step"])
        self.assertEqual(before, json.dumps(kernel.ledger, sort_keys=True))

    def test_leaf_result_outside_a_leaf_stage_names_the_stage_and_the_stage_event(self) -> None:
        """Turn 120 of the q2 session: 'bounded leaf results require an active leaf stage'."""
        kernel = self.kernel("01")
        candidate = self.candidate()
        kernel.activate("01", candidate)
        self.assertEqual("implement", kernel.ledger["tickets"]["01"]["stage"])
        before = json.dumps(kernel.ledger, sort_keys=True)

        with self.assertRaises(TransitionError) as caught:
            kernel.record_leaf_result(
                "01",
                leaf_result(candidate, "review", quality=False),
                candidate,
                expected_files=[],
            )

        self.assertEqual(
            "bounded leaf results require an active leaf stage", str(caught.exception)
        )
        detail = self.assert_detail(caught.exception.detail)
        self.assertEqual("tickets.01.stage", detail["field"])
        self.assertEqual({"state": "active", "stage": "implement"}, detail["received"])
        self.assertEqual(
            {"state": "active", "stage": ["review", "qa-plan", "qa-execute", "verify"]},
            detail["expected"],
        )
        self.assertIn("'stage'", detail["next_step"])
        self.assertIn("'implement'", detail["next_step"])
        self.assertEqual(before, json.dumps(kernel.ledger, sort_keys=True))

    def test_quality_stage_without_quality_names_the_shape_it_wants(self) -> None:
        """Turn 131 of the q2 session: 'quality leaf result requires structured quality evidence'."""
        candidate = self.candidate()
        for stage in ("qa-plan", "qa-execute", "verify"):
            with self.subTest(stage=stage):
                with self.assertRaises(LeafProtocolError) as caught:
                    validate_leaf_result(leaf_result(candidate, stage, quality=False))

                self.assertEqual(
                    "quality leaf result requires structured quality evidence",
                    str(caught.exception),
                )
                detail = self.assert_detail(caught.exception.detail)
                self.assertEqual("quality", detail["field"])
                self.assertEqual("absent", detail["received"])
                self.assertEqual(
                    {"schema", "causal_scope", "evidence", "limitations"},
                    set(detail["expected"]),
                )
                self.assertEqual(
                    {"id", "artifact", "sha256", "result", "candidate_ref"},
                    set(detail["expected"]["evidence"][0]),
                )
                self.assertIn(stage, detail["next_step"])

    def test_the_named_shape_is_the_one_the_validator_accepts(self) -> None:
        """The advice has to be true: filling that shape must pass validation."""
        candidate = self.candidate()
        for stage in ("qa-plan", "qa-execute", "verify"):
            with self.subTest(stage=stage):
                document = leaf_result(candidate, stage, quality=True)
                normalized = validate_leaf_result(document, expected_stage=stage)
                self.assertEqual(
                    {"schema", "causal_scope", "evidence", "limitations"},
                    set(normalized["quality"]),
                )

    def test_a_rejection_without_detail_keeps_its_former_shape(self) -> None:
        """Only named rejections carry detail; the rest must not gain an attribute error."""
        kernel = self.kernel("01")
        candidate = self.candidate()
        kernel.activate("01", candidate)

        with self.assertRaises(TransitionError) as caught:
            kernel.record_stage("01", "implement", "gated", candidate)

        self.assertIn("non-empty reason", str(caught.exception))
        self.assertIsNone(caught.exception.detail)


class ResumeRejectionEnvelopeTests(GitIsolatedTestCase):
    """The detail has to survive the CLI, which is where a caller actually reads it."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        template = self.repository_template(
            self._build_baseline_repository, name="apf02-baseline"
        )
        self.repo = self.copy_of_template(template, Path(self.directory.name) / "repo")
        remote = Path(self.directory.name) / "origin.git"
        subprocess.run(
            ["git", "clone", "--bare", str(self.repo), str(remote)],
            check=True,
            capture_output=True,
        )
        configure_test_origin(self.repo, remote)

    @staticmethod
    def _build_baseline_repository(repo: Path) -> None:
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
        tickets = repo / "tickets"
        tickets.mkdir()
        (tickets / "01.md").write_text(ticket_text("01"), encoding="utf-8", newline="\n")
        (repo / "README.md").write_text("baseline\n", encoding="utf-8", newline="\n")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "baseline"], check=True, capture_output=True
        )

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(CLI), *args],
            cwd=self.repo,
            text=True,
            capture_output=True,
        )

    def test_resume_error_envelope_carries_the_detail(self) -> None:
        subprocess.run(
            ["git", "push", "--force", "origin", "main"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )
        created = json.loads(
            self.cli(
                "run",
                str(self.repo / "tickets"),
                "--repo",
                str(self.repo),
                "--provider",
                "github",
                "--run-id",
                "apf02-detail",
                "--final-tree-mode",
                "off",
            ).stdout
        )
        self.assertTrue(created["ok"], created)
        run_id = created["data"]["run_id"]

        events = Path(self.directory.name) / "events.json"
        events.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "events": [
                        {"operation": "activate", "ticket_id": "01"},
                        {"operation": "activate", "ticket_id": "01"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        result = self.cli(
            "resume", run_id, "--repo", str(self.repo), "--events", str(events)
        )

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual("TransitionError", payload["error"]["type"])
        self.assertEqual(
            "another ticket is already active", payload["error"]["message"]
        )
        self.assertEqual(DETAIL_FIELDS, set(payload["error"]["detail"]))
        self.assertEqual("01", payload["error"]["detail"]["received"]["active_ticket_id"])

    def test_an_error_without_detail_still_has_type_and_message_only(self) -> None:
        result = self.cli("resume", "missing-run", "--repo", str(self.repo))

        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual({"type", "message"}, set(payload["error"]))


if __name__ == "__main__":
    unittest.main()
