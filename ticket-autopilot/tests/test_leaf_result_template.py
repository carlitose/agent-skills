"""`leaf-result-template` writes down what the q2 benchmark run spent 115 turns inferring.

Turns 61-175 of that run went to reading `leaf_protocol.py`, `kernel.py` and `cli.py`
to reconstruct the leaf-result shape by hand (see
`docs/specs/autopilot-protocol-friction-wayfinder.md`). Everything the model was
reconstructing is in the ledger and the contract: the CandidateRef, the stage, its phase
names, whether `quality` is required and what it contains, the tree the event must bind.
The command emits the whole `resume --events` document with those filled and
`<<FILL: ...>>` where only the leaf knows the answer.

These tests hold the template to the validator, and hold every piece of advice the runner
gives around it to actual execution: the advice is applied literally and must be accepted.
Two things that caught: the stage-event advice from APF-02 omitted `expected_tree_oid`,
which the kernel requires, and a first draft of this command offered `--stage` to prepare
the next leaf result ahead, which cannot work because the completion projection at
simplify -> review rewrites the worktree tree and with it the CandidateRef.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if __package__:
    from .git_test_support import GitIsolatedTestCase
else:
    from git_test_support import GitIsolatedTestCase

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
sys.path.insert(0, str(SCRIPTS))

from autopilot.leaf_protocol import (
    LEAF_PHASE_CONTRACTS,
    LEAF_RESULT_STAGES,
    QUALITY_LEAF_STAGES,
    validate_leaf_result,
)

TICKET = (
    b'---\nticket_schema: 1\nticket_id: "X-01"\nexecution_mode: AFK\n'
    b"blocked_by: []\n---\n\n# X-01\n\n## What to Build\na\n"
)
MARKER = re.compile(r"^<<FILL: .+>>$")


def markers_in(value: object, path: str = "$") -> list[str]:
    if isinstance(value, str):
        return [path] if MARKER.match(value) else []
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in markers_in(v, f"{path}.{k}")]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in markers_in(v, f"{path}[{i}]")]
    return []


def fill(document: dict) -> dict:
    """Replace the markers the way a leaf would: with real, shape-respecting values."""
    event = document["events"][0]
    result = event["leaf_result"]
    result["scope"]["files_inspected"] = list(result["scope"]["files_expected"])
    result["scope"]["files_remaining"] = []
    result["commands_run"] = ["python -B -m unittest discover -q"]
    result["findings"] = []
    if "quality" in result:
        result["quality"]["causal_scope"] = [result["stage"]]
        result["quality"]["evidence"][0].update(
            id="E-tests", artifact="receipt.json", sha256="0" * 64, result="pass"
        )
    event["tool_calls"], event["wall_time"] = 3, 10
    return document


class LeafResultTemplateTest(GitIsolatedTestCase):
    """One seeded run with one ticket; each test activates it and walks it as needed."""

    def setUp(self) -> None:
        super().setUp()
        self.temporary = tempfile.TemporaryDirectory(prefix="apf01-")
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.repo, upstream = root / "repo", root / "upstream.git"
        self.repo.mkdir()
        self.git("init", "-b", "main", str(self.repo))
        self.git("-C", str(self.repo), "config", "user.email", "t@example.com")
        self.git("-C", str(self.repo), "config", "user.name", "Test")
        folder = self.repo / "docs/tickets/x"
        folder.mkdir(parents=True)
        (folder / "01-a.md").write_bytes(TICKET)
        self.git("-C", str(self.repo), "add", "-A")
        self.git("-C", str(self.repo), "commit", "-m", "init")
        self.git("init", "--bare", "-b", "main", str(upstream))
        self.git("-C", str(self.repo), "remote", "add", "origin", str(upstream))
        self.git("-C", str(self.repo), "push", "-q", "origin", "main")
        started = self.cli("run", str(folder), "--repo", str(self.repo), "--base", "main",
                           "--provider", "github", "--run-id", "tpl")
        self.assertTrue(started["ok"], started)
        self.ledger = Path(started["data"]["ledger"])
        self.worktree = Path(started["data"]["worktree"])
        self.counter = 0

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True)

    def cli(self, *args: str) -> dict:
        completed = subprocess.run(
            [sys.executable, "-B", str(CLI), *args],
            capture_output=True, text=True, cwd=str(self.repo), timeout=300, check=False,
        )
        return json.loads(completed.stdout or completed.stderr)

    def resume(self, *events: dict) -> dict:
        self.counter += 1
        path = Path(self.temporary.name) / f"events-{self.counter}.json"
        path.write_text(json.dumps({"schema": 1, "events": list(events)}), encoding="utf-8")
        return self.cli("resume", "tpl", "--repo", str(self.repo), "--events", str(path))

    def ticket(self) -> dict:
        return self.cli("status", "tpl", "--repo", str(self.repo))["data"]["tickets"]["X-01"]

    def activate(self) -> None:
        self.assertTrue(self.resume({"operation": "activate", "ticket_id": "X-01"})["ok"])

    def template(self, *args: str) -> dict:
        return self.cli("leaf-result-template", "tpl", "--repo", str(self.repo), *args)

    @staticmethod
    def advised_event(next_step: str, result: str = "pass") -> dict:
        """Take the dict literal the advice shows and send exactly that."""
        literal = re.search(r"\{'operation'.*?\}", next_step).group(0)
        return ast.literal_eval(literal.replace("'pass' | 'fail' | 'gated'", repr(result)))

    def advance_to(self, stage: str) -> None:
        """Walk the ticket forward by doing only what the runner's own messages say.

        At a stage-event stage the template refuses and its `next_step` is the event.
        At a leaf stage the template is accepted, the filled result is recorded, and
        `after_acceptance` is the event.
        """
        while (current := self.ticket()["stage"]) != stage:
            response = self.template()
            if response["ok"]:
                advice = self.record(current)["after_acceptance"]
            else:
                advice = response["error"]["detail"]["next_step"]
            advanced = self.resume(self.advised_event(advice))
            self.assertTrue(advanced["ok"], advanced)

    def record(self, stage: str) -> dict:
        """Template the current stage, fill it, send it, and require it to be recorded."""
        response = self.template()
        self.assertTrue(response["ok"], response)
        filled = fill(response["data"]["events_document"])
        recorded = self.resume(filled["events"][0])
        self.assertTrue(recorded["ok"], recorded)
        processed = recorded["data"]["processed"][0]
        self.assertEqual(
            (processed["operation"], processed["stage"], processed["result"]),
            ("leaf-result", stage, "complete"),
        )
        return response["data"]

    # -- refusals -------------------------------------------------------------------

    def test_before_activation_the_refusal_names_the_ticket_and_the_activation(self) -> None:
        response = self.template()
        self.assertFalse(response["ok"])
        detail = response["error"]["detail"]
        self.assertEqual(detail["field"], "--ticket")
        self.assertIn("activate", detail["next_step"])
        self.assertIn("X-01", detail["next_step"])

    def test_at_a_stage_that_takes_no_leaf_result_the_refusal_is_the_stage_event(self) -> None:
        self.activate()
        response = self.template()
        self.assertFalse(response["ok"])
        detail = response["error"]["detail"]
        self.assertEqual(detail["received"], {"state": "active", "stage": "implement"})
        self.assertEqual(detail["expected"], {"state": "active", "stage": list(LEAF_RESULT_STAGES)})
        event = self.advised_event(detail["next_step"])
        self.assertEqual(event["stage"], "implement")
        self.assertRegex(event["expected_tree_oid"], r"^[0-9a-f]{40}$")
        self.assertTrue(self.resume(event)["ok"])

    def test_there_is_no_way_to_prepare_a_stage_ahead(self) -> None:
        """The tree changes between stages, so an early template would bind a stale one."""
        self.activate()
        response = self.template("--stage", "review")
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["type"], "ArgumentError")

    def test_the_resume_rejection_and_the_template_give_the_same_stage_event(self) -> None:
        """A leaf-result sent too early is refused with advice; applying it literally works.

        Two refusals in a row, each followed to the letter: the tree one names the
        tree to use, the stage one names the event to send. The stage advice used to
        omit `expected_tree_oid`, which the kernel requires, so following it failed
        with `stage event requires stage, result, and expected_tree_oid`.
        """
        self.activate()
        early = {
            "operation": "leaf-result", "ticket_id": "X-01", "expected_tree_oid": "0" * 40,
            "leaf_result": {}, "tool_calls": 1, "wall_time": 1,
        }
        wrong_tree = self.resume(early)
        self.assertFalse(wrong_tree["ok"])
        detail = wrong_tree["error"]["detail"]
        self.assertEqual(detail["field"], "events[].expected_tree_oid")
        self.assertEqual(detail["received"], "0" * 40)
        rejected = self.resume(dict(early, expected_tree_oid=detail["expected"]))
        self.assertFalse(rejected["ok"])
        advice = rejected["error"]["detail"]["next_step"]
        self.assertIn("leaf-result-template", advice)
        self.assertEqual(
            self.advised_event(advice),
            self.advised_event(self.template()["error"]["detail"]["next_step"]),
        )
        advanced = self.resume(self.advised_event(advice))
        self.assertTrue(advanced["ok"], advanced)
        self.assertEqual(advanced["data"]["tickets"]["X-01"]["stage"], "simplify")

    def test_the_activation_advice_names_the_tree_a_stage_event_must_carry(self) -> None:
        self.activate()
        second = self.resume({"operation": "activate", "ticket_id": "X-01"})
        self.assertFalse(second["ok"])
        event = self.advised_event(second["error"]["detail"]["next_step"])
        self.assertIn("expected_tree_oid", event)
        self.assertRegex(event["expected_tree_oid"], r"^[0-9a-f]{40}$")

    # -- the template ----------------------------------------------------------------

    def test_the_review_template_binds_the_tree_the_projection_produced(self) -> None:
        self.activate()
        before = self.ticket()["candidate_ref"]
        self.advance_to("review")
        after = self.ticket()["candidate_ref"]
        self.assertNotEqual(
            before["candidate_tree_oid"], after["candidate_tree_oid"],
            "the completion projection at simplify -> review is expected to rewrite the tree",
        )
        event = self.template()["data"]["events_document"]["events"][0]
        self.assertEqual(event["expected_tree_oid"], after["candidate_tree_oid"])
        self.assertEqual(event["leaf_result"]["candidate_ref"], after)
        self.assertIn("docs/tickets/x/done/01-a.md", event["leaf_result"]["scope"]["files_expected"])

    def test_every_accepting_stage_templates_to_a_document_the_validator_accepts(self) -> None:
        """Walk review -> qa-plan -> qa-execute -> verify, templating and recording each."""
        self.activate()
        self.advance_to("review")
        for index, stage in enumerate(LEAF_RESULT_STAGES):
            with self.subTest(stage=stage):
                response = self.template()
                self.assertTrue(response["ok"], response)
                data = response["data"]
                self.assertIsNone(data["drift"])
                document = data["events_document"]
                event = document["events"][0]
                result = event["leaf_result"]
                self.assertEqual(sorted(markers_in(document)), data["markers"])
                self.assertEqual(result["stage"], stage)
                self.assertEqual(result["phase_contract"], list(LEAF_PHASE_CONTRACTS[stage]))
                self.assertEqual(result["progress_phase"], "handoff-ready")
                self.assertEqual(("quality" in result), stage in QUALITY_LEAF_STAGES)
                self.assertEqual(event["expected_tree_oid"], result["candidate_ref"]["candidate_tree_oid"])
                if "quality" in result:
                    self.assertEqual(
                        result["quality"]["evidence"][0]["candidate_ref"], result["candidate_ref"]
                    )
                filled = fill(json.loads(json.dumps(document)))
                self.assertEqual(markers_in(filled), [])
                validate_leaf_result(
                    filled["events"][0]["leaf_result"],
                    expected_candidate_ref=result["candidate_ref"],
                    expected_stage=stage,
                )
                self.record(stage)
                if index + 1 < len(LEAF_RESULT_STAGES):
                    self.advance_to(LEAF_RESULT_STAGES[index + 1])

    def test_a_stage_pass_before_the_leaf_result_names_the_leaf_result(self) -> None:
        self.activate()
        self.advance_to("review")
        advice = self.template()["data"]["after_acceptance"]
        too_soon = self.resume(self.advised_event(advice))
        self.assertFalse(too_soon["ok"])
        detail = too_soon["error"]["detail"]
        self.assertEqual(detail["field"], "tickets.X-01.leaf_handoff")
        self.assertIsNone(detail["received"])
        self.assertIn("leaf-result-template", detail["next_step"])
        self.record("review")
        self.assertTrue(self.resume(self.advised_event(advice))["ok"])

    def test_a_stage_event_with_a_stale_tree_names_the_current_one(self) -> None:
        self.activate()
        event = dict(self.advised_event(self.template()["error"]["detail"]["next_step"]))
        event["expected_tree_oid"] = "0" * 40
        rejected = self.resume(event)
        self.assertFalse(rejected["ok"])
        detail = rejected["error"]["detail"]
        self.assertEqual(detail["field"], "events[].expected_tree_oid")
        self.assertTrue(self.resume(dict(event, expected_tree_oid=detail["expected"]))["ok"])

    def test_markers_sit_only_where_the_leaf_knows_better_than_the_runner(self) -> None:
        self.activate()
        self.advance_to("qa-plan")
        markers = self.template()["data"]["markers"]
        leaf_only = {
            "$.events[0].leaf_result.scope.files_inspected[0]",
            "$.events[0].leaf_result.scope.files_remaining[0]",
            "$.events[0].leaf_result.commands_run[0]",
            "$.events[0].leaf_result.findings[0]",
            "$.events[0].leaf_result.quality.causal_scope[0]",
            "$.events[0].leaf_result.quality.evidence[0].id",
            "$.events[0].leaf_result.quality.evidence[0].artifact",
            "$.events[0].leaf_result.quality.evidence[0].sha256",
            "$.events[0].leaf_result.quality.evidence[0].result",
            "$.events[0].tool_calls",
            "$.events[0].wall_time",
        }
        self.assertEqual(set(markers), leaf_only)

    def test_the_template_is_read_only(self) -> None:
        self.activate()
        self.advance_to("review")
        before = self.ledger.read_bytes()
        self.assertTrue(self.template()["ok"])
        self.assertEqual(before, self.ledger.read_bytes())

    def test_drift_between_worktree_and_bound_candidate_is_named_up_front(self) -> None:
        self.activate()
        self.advance_to("review")
        (self.worktree / "stray.txt").write_text("drift\n", encoding="utf-8")
        response = self.template()
        self.assertTrue(response["ok"], response)
        self.assertIn("invalidated", response["data"]["drift"])


if __name__ == "__main__":
    unittest.main()
