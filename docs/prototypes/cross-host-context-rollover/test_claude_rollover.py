from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from claude_rollover import (
    ADAPTER_ID,
    AmbiguousSessionStart,
    ClaudeRolloverController,
    ClaudeSurface,
    FakeClaudeProcess,
    ObservedSessionStartFailure,
    StatusTrigger,
    hook_only_report,
    load_fixture,
    project_context_pressure,
    project_messages,
)
from rollover_common import (
    DurablePointers,
    PrivateRegistry,
    PrototypeError,
    create_handoff,
)


HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "claude-code-2.1.223.json"
SOURCE = "11111111-1111-4111-8111-111111111111"
TARGET_1 = "22222222-2222-4222-8222-222222222222"
TARGET_2 = "33333333-3333-4333-8333-333333333333"
NOW = 2_000_000_000


def status_line(
    input_tokens: int | None,
    output_tokens: int | None,
    *,
    session_id: str = SOURCE,
    window: int = 200_000,
) -> dict:
    current = (
        None
        if input_tokens is None or output_tokens is None
        else input_tokens + output_tokens
    )
    used = None if current is None else current / window * 100
    return {
        "session_id": session_id,
        "context_window": {
            "total_input_tokens": input_tokens,
            "total_output_tokens": output_tokens,
            "context_window_size": window,
            "used_percentage": used,
            "remaining_percentage": None if used is None else 100 - used,
            "current_usage": None if current is None else {"total": current},
        },
        "cost": {"total_cost_usd": 9_999_999},
    }


class SurfaceAndProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = load_fixture(FIXTURE)

    def test_user_local_cli_matches_the_version_bound_surface(self) -> None:
        selected = Path.home() / ".local" / "bin" / "claude"
        if not selected.exists():
            self.skipTest("the selected user-local Claude installation is unavailable")
        version = subprocess.run(
            [selected, "--version"], check=True, capture_output=True, text=True
        ).stdout
        help_text = subprocess.run(
            [selected, "--help"], check=True, capture_output=True, text=True
        ).stdout
        installed = self.fixture["installed_surface"]
        self.assertEqual(installed["version"], version.strip())
        self.assertEqual(
            installed["version_sha256"], hashlib.sha256(version.encode()).hexdigest()
        )
        self.assertEqual(
            installed["help_sha256"], hashlib.sha256(help_text.encode()).hexdigest()
        )
        for flag in installed["observed_flags"]:
            self.assertIn(flag, help_text)

    def test_fixture_loader_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text(
                '{"schema":1,"schema":1,"adapter":"claude-code-stream-json"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PrototypeError, "duplicate"):
                load_fixture(path)

    def test_surface_requires_every_controller_flag_and_safe_autocompact(self) -> None:
        surface = ClaudeSurface.from_fixture(self.fixture)
        self.assertEqual("2.1.223 (Claude Code)", surface.version)
        missing = ClaudeSurface(surface.version, ("--session-id",), 160_000)
        with self.assertRaisesRegex(PrototypeError, "lacks required flags"):
            missing.validate()
        for tokens in (150_000, True):
            with self.subTest(tokens=tokens):
                invalid = ClaudeSurface(
                    surface.version, surface.observed_flags, tokens
                )
                with self.assertRaisesRegex(PrototypeError, "autocompact"):
                    invalid.validate()

    def test_exact_cr01_projection_matches_codex_report_shape(self) -> None:
        report = project_messages(self.fixture["stream"])
        for key, expected in self.fixture["expected_message_report"].items():
            self.assertEqual(expected, report[key])
        self.assertEqual(ADAPTER_ID, report["adapter"])
        self.assertEqual("prospective stream-json controller events", report["source"])

    def test_partial_hooks_tools_subagents_replays_and_duplicates_do_not_count(self) -> None:
        stream = json.loads(json.dumps(self.fixture["stream"]))
        baseline = project_messages(stream)
        stream["events"].extend(
            [
                {"type": "stream_event", "uuid": "partial-extra", "event": {}},
                {"type": "hook_response", "uuid": "hook-extra"},
                {
                    "type": "assistant",
                    "uuid": "forwarded-extra",
                    "parent_tool_use_id": "agent-tool-extra",
                    "message": {
                        "role": "assistant",
                        "id": "forwarded-message-extra",
                        "content": [{"type": "text", "text": "forwarded"}],
                    },
                },
                {
                    "type": "user",
                    "uuid": "replay-extra",
                    "isReplay": True,
                    "parent_tool_use_id": None,
                    "message": {"role": "user", "content": "replayed"},
                },
            ]
        )
        self.assertEqual(baseline, project_messages(stream))

    def test_replay_cannot_consume_a_later_original_event_identity(self) -> None:
        stream = {
            "schema": 1,
            "identity_source": "controller-owned-event-id",
            "events": [
                {
                    "type": "user",
                    "controller_event_id": "same-id",
                    "isReplay": True,
                    "parent_tool_use_id": None,
                    "message": {"role": "user", "content": "replayed"},
                },
                {
                    "type": "user",
                    "controller_event_id": "same-id",
                    "isReplay": False,
                    "parent_tool_use_id": None,
                    "message": {"role": "user", "content": "accepted"},
                },
            ],
        }
        self.assertEqual(1, project_messages(stream)["user_messages"])

    def test_failed_result_and_tool_result_do_not_create_visible_messages(self) -> None:
        stream = {
            "schema": 1,
            "identity_source": "controller-owned-event-id",
            "events": [
                {
                    "type": "user",
                    "uuid": "tool-result",
                    "isReplay": False,
                    "parent_tool_use_id": None,
                    "message": {
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": "x"}],
                    },
                },
                {
                    "type": "result",
                    "uuid": "failed",
                    "subtype": "error_during_execution",
                    "is_error": True,
                    "result": "failed",
                },
            ],
        }
        report = project_messages(stream)
        self.assertEqual(0, report["total_messages"])

    def test_projection_rejects_missing_direct_event_identity(self) -> None:
        stream = {
            "schema": 1,
            "identity_source": "controller-owned-event-id",
            "events": [
                {
                    "type": "user",
                    "message": {"role": "user", "content": "missing id"},
                }
            ],
        }
        with self.assertRaisesRegex(PrototypeError, "identity"):
            project_messages(stream)

    def test_context_pressure_is_separate_from_message_count(self) -> None:
        precompact = self.fixture["hook_events"]["precompact"]
        pressure = project_context_pressure(
            self.fixture["context_status_cases"][0], precompact=precompact
        )
        self.assertEqual(149_999, pressure["current_context_tokens"])
        self.assertTrue(pressure["precompact_seen"])
        self.assertEqual("auto", pressure["precompact_trigger"])
        self.assertIsNone(pressure["message_count_source"])


class TriggerTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = load_fixture(FIXTURE)
        self.surface = ClaudeSurface.from_fixture(fixture)

    def test_149999_monitors_and_150000_arms(self) -> None:
        trigger = StatusTrigger(SOURCE, self.surface)
        trigger.observe(status_line(120_000, 29_999))
        self.assertEqual("monitoring", trigger.state)
        self.assertEqual(0, trigger.generation)
        trigger.observe(status_line(120_000, 30_000))
        self.assertEqual("rollover-pending", trigger.state)
        self.assertEqual(1, trigger.generation)

    def test_cumulative_cost_cannot_arm(self) -> None:
        payload = status_line(120_000, 29_999)
        payload["cost"]["total_cost_usd"] = 10**12
        trigger = StatusTrigger(SOURCE, self.surface)
        trigger.observe(payload)
        self.assertEqual("monitoring", trigger.state)

    def test_null_before_first_call_waits(self) -> None:
        trigger = StatusTrigger(SOURCE, self.surface)
        trigger.observe(status_line(None, None))
        self.assertIsNone(trigger.current_context_tokens)
        self.assertEqual("monitoring", trigger.state)

    def test_partially_null_or_wrong_session_status_fails(self) -> None:
        trigger = StatusTrigger(SOURCE, self.surface)
        with self.assertRaisesRegex(PrototypeError, "incomplete"):
            trigger.observe(status_line(None, 1))
        with self.assertRaisesRegex(PrototypeError, "session mismatch"):
            trigger.observe(status_line(1, 1, session_id=TARGET_1))

    def test_context_window_at_or_below_threshold_fails_configuration(self) -> None:
        for window in (149_999, 150_000):
            with self.subTest(window=window):
                with self.assertRaisesRegex(PrototypeError, "cannot reach"):
                    StatusTrigger(SOURCE, self.surface).observe(
                        status_line(100_000, 1, window=window)
                    )

    def test_duplicate_threshold_events_keep_one_generation(self) -> None:
        trigger = StatusTrigger(SOURCE, self.surface)
        trigger.observe(status_line(120_000, 30_000))
        trigger.observe(status_line(150_000, 20_000))
        self.assertEqual(1, trigger.generation)

    def test_precompact_preserves_pending_but_cannot_arm_early(self) -> None:
        fixture = load_fixture(FIXTURE)
        event = fixture["hook_events"]["precompact"]
        trigger = StatusTrigger(SOURCE, self.surface)
        trigger.observe(status_line(120_000, 29_999))
        with self.assertRaisesRegex(PrototypeError, "before"):
            trigger.observe_precompact(event)
        self.assertEqual("monitoring", trigger.state)
        trigger.observe(status_line(120_000, 30_000))
        self.assertEqual("pending-generation-preserved", trigger.observe_precompact(event))


class RolloverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.wayfinder = self.workspace / "map.md"
        self.wayfinder.write_text("# map\n", encoding="utf-8")
        self.tickets = self.workspace / "tickets"
        self.tickets.mkdir()
        self.private = self.root / "private"
        self.registry = PrivateRegistry(self.root / "registry")
        fixture = load_fixture(FIXTURE)
        self.surface = ClaudeSurface.from_fixture(fixture)
        self.stop_event = fixture["hook_events"]["stop"]
        self.process = FakeClaudeProcess(SOURCE)
        self.controller = ClaudeRolloverController(
            process=self.process,
            registry=self.registry,
            surface=self.surface,
            workspace=self.workspace,
            source_session_id=SOURCE,
        )
        self.controller.trigger.observe(status_line(120_000, 30_000))
        self.pointers = DurablePointers(
            wayfinder_path=str(self.wayfinder),
            ticket_folder=str(self.tickets),
            run_id="cross-host-run",
            next_frontier="CR-04",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_handoff(self, rollover_id: str = "claude-rollover-1"):
        return create_handoff(
            self.private,
            workspace=self.workspace,
            host_adapter_id=ADAPTER_ID,
            source_session_id=SOURCE,
            generation=1,
            rollover_id=rollover_id,
            pointers=self.pointers,
            now=NOW,
        )

    def reach_boundary(self) -> None:
        self.assertTrue(self.controller.observe_stop(self.stop_event))
        self.controller.mark_owner_terminal()

    def complete(self, handoff, *, target: str = TARGET_1, status=None):
        return self.controller.rollover(
            handoff.path,
            now=NOW + 1,
            target_status_line=status or status_line(1_000, 100, session_id=target),
            ticket_list=lambda path: {"root": path, "ready": ["CR-04"]},
            run_status=lambda run_id: {"run_id": run_id, "state": "waiting"},
            session_id_factory=lambda: target,
        )

    def test_complete_path_uses_fresh_uuid_and_keeps_source_resumable(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        result = self.complete(handoff)
        self.assertEqual(SOURCE, result["source_session_id"])
        self.assertTrue(result["source_resumable"])
        self.assertEqual(TARGET_1, result["target_session_id"])
        self.assertNotEqual(SOURCE, result["target_session_id"])
        self.assertEqual("fresh-uuid-session", result["target_mode"])
        self.assertEqual("CR-04", result["frontier"]["next_frontier"])
        self.assertEqual("restored", result["registry_state"])
        self.assertFalse(handoff.path.exists())

    def test_bootstrap_is_pointer_only_and_uses_required_controller_flags(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        result = self.complete(handoff)
        call = self.process.calls[0]
        argv = call["argv"]
        for flag in (
            "--input-format",
            "--output-format",
            "--include-hook-events",
            "--include-partial-messages",
            "--forward-subagent-text",
            "--replay-user-messages",
            "--session-id",
            "--autocompact",
        ):
            self.assertIn(flag, argv)
        text = call["stream_input"]["message"]["content"][0]["text"]
        self.assertEqual(result["bootstrap"], text)
        self.assertIn(str(handoff.path), text)
        self.assertNotIn("first accepted user input", text)
        self.assertNotIn("transcript", text.lower().replace("do not read or copy transcript content", ""))

    def test_pending_prompt_is_released_only_after_restore(self) -> None:
        self.assertEqual("held", self.controller.submit_or_hold("continue CR-04"))
        handoff = self.make_handoff()
        self.reach_boundary()
        result = self.complete(handoff)
        self.assertTrue(result["held_prompt_released"])
        self.assertEqual(["start-session", "send-prompt"], [c["operation"] for c in self.process.calls])
        self.assertEqual("continue CR-04", self.process.calls[-1]["prompt"])

    def test_active_turn_or_nonterminal_owner_blocks_before_new_session(self) -> None:
        handoff = self.make_handoff()
        with self.assertRaisesRegex(PrototypeError, "safe Claude"):
            self.complete(handoff)
        self.assertEqual([], self.process.calls)
        self.controller.observe_stop(self.stop_event)
        with self.assertRaisesRegex(PrototypeError, "safe Claude"):
            self.complete(handoff)
        self.assertEqual([], self.process.calls)

    def test_interrupted_or_recursive_stop_does_not_establish_boundary(self) -> None:
        interrupted = dict(self.stop_event, interrupted=True)
        self.assertFalse(self.controller.observe_stop(interrupted))
        self.assertTrue(self.controller.active_turn)
        recursive = dict(self.stop_event, stop_hook_active=True)
        with self.assertRaisesRegex(PrototypeError, "recursive"):
            self.controller.observe_stop(recursive)

    def test_invalid_handoff_fails_before_session_start(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        for path, clock in (
            (self.root / "missing" / "HANDOFF.md", NOW + 1),
            (handoff.path, NOW + 3_600),
        ):
            with self.subTest(path=path):
                with self.assertRaises(PrototypeError):
                    self.controller.rollover(
                        path,
                        now=clock,
                        target_status_line=status_line(1, 1, session_id=TARGET_1),
                        ticket_list=lambda _: [],
                        run_status=lambda _: {},
                        session_id_factory=lambda: TARGET_1,
                    )
                self.assertEqual([], self.process.calls)

    def test_mismatched_consumed_or_malformed_handoff_fails_closed(self) -> None:
        cases = (
            ("adapter", "host_adapter_id", "another-adapter", "adapter mismatch"),
            ("source", "source_session_key", "wrong-digest", "source session mismatch"),
            ("consumed", "consumed", True, "already consumed"),
            ("malformed", None, None, "malformed"),
        )
        for label, field, value, error in cases:
            with self.subTest(label=label):
                self.tearDown()
                self.setUp()
                handoff = self.make_handoff()
                if field is None:
                    handoff.path.write_text("{", encoding="utf-8")
                else:
                    document = json.loads(handoff.path.read_text(encoding="utf-8"))
                    document[field] = value
                    handoff.path.write_text(json.dumps(document), encoding="utf-8")
                os.chmod(handoff.path, 0o600)
                self.reach_boundary()
                with self.assertRaisesRegex(PrototypeError, error):
                    self.complete(handoff)
                self.assertEqual([], self.process.calls)

    def test_wrong_or_threshold_target_status_prevents_consumption(self) -> None:
        for mode in ("wrong-session", "threshold"):
            with self.subTest(mode=mode):
                self.tearDown()
                self.setUp()
                handoff = self.make_handoff()
                self.reach_boundary()
                target_status = (
                    status_line(1, 1, session_id=TARGET_2)
                    if mode == "wrong-session"
                    else status_line(120_000, 30_000, session_id=TARGET_1)
                )
                with self.assertRaises(PrototypeError):
                    self.complete(handoff, status=target_status)
                self.assertTrue(handoff.path.exists())
                entry = self.registry.create_or_read(
                    handoff=handoff, host_adapter_id=ADAPTER_ID, generation=1
                )
                self.assertEqual("attempt-failed", entry["state"])

    def test_incomplete_frontier_prevents_consumption(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        with self.assertRaisesRegex(PrototypeError, "ticket-list readback"):
            self.controller.rollover(
                handoff.path,
                now=NOW + 1,
                target_status_line=status_line(1, 1, session_id=TARGET_1),
                ticket_list=lambda _: None,
                run_status=lambda _: {},
                session_id_factory=lambda: TARGET_1,
            )
        self.assertTrue(handoff.path.exists())

    def test_ambiguous_start_replays_the_persisted_target_uuid(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        self.process.next_start_failure = "ambiguous"
        with self.assertRaises(AmbiguousSessionStart):
            self.complete(handoff)
        self.assertIn(TARGET_1, self.process.sessions)
        result = self.controller.rollover(
            handoff.path,
            now=NOW + 2,
            target_status_line=status_line(1, 1, session_id=TARGET_1),
            ticket_list=lambda _: [],
            run_status=lambda _: {},
            session_id_factory=lambda: (_ for _ in ()).throw(
                AssertionError("persisted target must be reused")
            ),
        )
        self.assertEqual(TARGET_1, result["target_session_id"])
        self.assertEqual(
            [TARGET_1, TARGET_1],
            [call["session_id"] for call in self.process.calls if call["operation"] == "start-session"],
        )

    def test_observed_start_failure_advances_one_bounded_attempt(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        self.process.next_start_failure = "observed"
        with self.assertRaises(ObservedSessionStartFailure):
            self.complete(handoff)
        entry = self.registry.create_or_read(
            handoff=handoff, host_adapter_id=ADAPTER_ID, generation=1
        )
        self.assertEqual("attempt-failed", entry["state"])
        self.assertEqual(1, entry["attempt_count"])
        result = self.complete(
            handoff,
            target=TARGET_2,
            status=status_line(1, 1, session_id=TARGET_2),
        )
        self.assertEqual(TARGET_2, result["target_session_id"])

    def test_non_uuid_or_source_uuid_target_fails_without_start(self) -> None:
        for target in ("not-a-uuid", SOURCE):
            with self.subTest(target=target):
                self.tearDown()
                self.setUp()
                handoff = self.make_handoff()
                self.reach_boundary()
                with self.assertRaisesRegex(PrototypeError, "fresh UUID"):
                    self.complete(handoff, target=target)
                self.assertEqual([], self.process.calls)

    def test_missing_source_resume_receipt_fails_before_target_start(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        del self.process.sessions[SOURCE]
        with self.assertRaisesRegex(PrototypeError, "not resumable"):
            self.complete(handoff)
        self.assertEqual([], self.process.calls)


class HookTests(unittest.TestCase):
    def test_hook_only_surface_keeps_fresh_session_authority_in_controller(self) -> None:
        fixture = load_fixture(FIXTURE)
        report = hook_only_report(fixture["hook_events"])
        self.assertTrue(report["controller_required"])
        self.assertEqual(
            ["SessionStart", "Stop", "PreCompact", "PostCompact"],
            report["fixture_surface"],
        )
        claims = " ".join(report["cannot_claim"])
        self.assertIn("150000", claims)
        self.assertIn("fresh UUID", claims)
        self.assertIn("successful live rollover", claims)

    def test_incomplete_hook_fixture_fails_closed(self) -> None:
        fixture = load_fixture(FIXTURE)
        incomplete = dict(fixture["hook_events"])
        del incomplete["postcompact"]
        with self.assertRaisesRegex(PrototypeError, "lacks"):
            hook_only_report(incomplete)


if __name__ == "__main__":
    unittest.main()
