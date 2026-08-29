from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from codex_rollover import (
    ADAPTER_ID,
    CodexRolloverController,
    FakeAppServer,
    TriggerState,
    hook_only_report,
    load_fixture,
    project_messages,
)
from rollover_common import (
    DurablePointers,
    PrivateRegistry,
    PrototypeError,
    create_handoff,
    validate_handoff,
)


HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "codex-app-server-0.147.0.json"
NOW = 2_000_000_000


def token_event(
    last: int,
    *,
    total: int = 999_999,
    window: int = 200_000,
    thread_id: str = "source-thread",
    turn_id: str | None = None,
):
    breakdown = {
        "cachedInputTokens": 0,
        "inputTokens": 0,
        "outputTokens": 0,
        "reasoningOutputTokens": 0,
        "totalTokens": last,
    }
    total_breakdown = dict(breakdown, totalTokens=total)
    return {
        "method": "thread/tokenUsage/updated",
        "params": {
            "threadId": thread_id,
            "turnId": turn_id or (
                "turn-current" if thread_id == "source-thread" else "target-turn-1"
            ),
            "tokenUsage": {
                "last": breakdown,
                "total": total_breakdown,
                "modelContextWindow": window,
            },
        },
    }


def _assert_available_installed_schema_matches(
    test_case: unittest.TestCase,
    schema: dict,
    *,
    which=shutil.which,
    run=subprocess.run,
) -> None:
    codex = which("codex")
    if codex is None:
        raise unittest.SkipTest("Codex CLI is not installed in this test environment")
    version = run(
        [codex, "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    expected_version = schema["installed_cli"]
    if version != expected_version:
        raise unittest.SkipTest(
            "Codex CLI version does not match the version-bound fixture: "
            f"expected {expected_version}, observed {version}"
        )
    with tempfile.TemporaryDirectory() as directory:
        run(
            [
                codex,
                "app-server",
                "generate-json-schema",
                "--experimental",
                "--out",
                directory,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        generated = Path(directory)
        bundle = generated / "codex_app_server_protocol.schemas.json"
        test_case.assertEqual(
            schema["bundle_sha256"], hashlib.sha256(bundle.read_bytes()).hexdigest()
        )
        for name, expected in schema["files"].items():
            actual = hashlib.sha256((generated / "v2" / name).read_bytes()).hexdigest()
            test_case.assertEqual(expected, actual, name)


class ProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = load_fixture(FIXTURE)

    def test_fixture_is_bound_to_installed_generated_schema(self) -> None:
        schema = self.fixture["generated_schema"]
        self.assertEqual("codex-cli 0.147.0", schema["installed_cli"])
        self.assertEqual("v2", schema["protocol"])
        self.assertEqual(
            "babfd5c98cd978dd858b4762cdfbc9fba941e1a0e4053de0050e4082ae1f075a",
            schema["bundle_sha256"],
        )
        self.assertEqual(7, len(schema["files"]))

    def test_available_installed_schema_matches_version_binding(self) -> None:
        _assert_available_installed_schema_matches(
            self, self.fixture["generated_schema"]
        )

    def test_version_bound_probe_skips_when_codex_is_absent(self) -> None:
        runner = mock.Mock()
        with self.assertRaisesRegex(unittest.SkipTest, "not installed"):
            _assert_available_installed_schema_matches(
                self,
                self.fixture["generated_schema"],
                which=lambda _name: None,
                run=runner,
            )
        runner.assert_not_called()

    def test_version_bound_probe_skips_mismatch_before_schema_generation(self) -> None:
        runner = mock.Mock(
            return_value=subprocess.CompletedProcess(
                ["/tmp/codex", "--version"],
                0,
                stdout="codex-cli 0.150.1\n",
                stderr="",
            )
        )
        with self.assertRaisesRegex(
            unittest.SkipTest,
            "expected codex-cli 0.147.0.*observed codex-cli 0.150.1",
        ):
            _assert_available_installed_schema_matches(
                self,
                self.fixture["generated_schema"],
                which=lambda _name: "/tmp/codex",
                run=runner,
            )
        self.assertEqual(1, runner.call_count)

    def test_version_bound_probe_checks_hashes_for_the_exact_version(self) -> None:
        bundle_content = b"bundle"
        file_content = b"selected schema"
        schema = {
            "installed_cli": "codex-cli 0.147.0",
            "bundle_sha256": hashlib.sha256(bundle_content).hexdigest(),
            "files": {
                "ThreadReadParams.json": hashlib.sha256(file_content).hexdigest(),
            },
        }
        calls: list[list[str]] = []

        def fake_run(argv, **_kwargs):
            calls.append(list(argv))
            if argv[1:] == ["--version"]:
                return subprocess.CompletedProcess(
                    argv, 0, stdout="codex-cli 0.147.0\n", stderr=""
                )
            generated = Path(argv[-1])
            (generated / "v2").mkdir(parents=True)
            (generated / "codex_app_server_protocol.schemas.json").write_bytes(
                bundle_content
            )
            (generated / "v2" / "ThreadReadParams.json").write_bytes(file_content)
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

        _assert_available_installed_schema_matches(
            self,
            schema,
            which=lambda _name: "/tmp/codex",
            run=fake_run,
        )
        self.assertEqual(2, len(calls))

    def test_exact_cr01_projection_reports_user_assistant_and_total(self) -> None:
        report = project_messages(self.fixture["thread_read"])
        for key, expected in self.fixture["expected_message_report"].items():
            self.assertEqual(expected, report[key])
        self.assertEqual("thread/read(includeTurns=true)", report["source"])

    def test_projection_rejects_an_unbound_or_partial_read(self) -> None:
        response = json.loads(json.dumps(self.fixture["thread_read"]))
        response["params"]["includeTurns"] = False
        with self.assertRaisesRegex(PrototypeError, "includeTurns=true"):
            project_messages(response)

    def test_non_message_items_cannot_change_count(self) -> None:
        response = json.loads(json.dumps(self.fixture["thread_read"]))
        items = response["result"]["thread"]["turns"][0]["items"]
        baseline = project_messages(response)
        items.extend(
            [
                {"id": "tool-extra", "type": "mcpToolCall"},
                {"id": "reasoning-extra", "type": "reasoning"},
                {"id": "plan-extra", "type": "plan"},
                {"id": "compact-extra", "type": "contextCompaction"},
                {
                    "id": "commentary-extra",
                    "type": "agentMessage",
                    "phase": "commentary",
                },
            ]
        )
        self.assertEqual(baseline, project_messages(response))

    def test_repeated_item_identity_is_deduplicated(self) -> None:
        response = json.loads(json.dumps(self.fixture["thread_read"]))
        turns = response["result"]["thread"]["turns"]
        turns[1]["items"].append(dict(turns[0]["items"][0]))
        self.assertEqual(5, project_messages(response)["total_messages"])

    def test_ambiguous_phase_less_assistant_count_is_unavailable(self) -> None:
        response = json.loads(json.dumps(self.fixture["thread_read"]))
        response["result"]["thread"]["turns"][1]["items"].append(
            {"id": "second-unknown", "type": "agentMessage", "text": "ambiguous"}
        )
        report = project_messages(response)
        self.assertFalse(report["assistant_count_available"])
        self.assertIsNone(report["assistant_messages"])
        self.assertIsNone(report["total_messages"])
        self.assertEqual(3, report["user_messages"])

    def test_aborted_turn_without_final_answer_does_not_count_assistant(self) -> None:
        response = {
            "method": "thread/read",
            "params": {"threadId": "source-thread", "includeTurns": True},
            "result": {
                "thread": {
                    "turns": [
                        {
                            "id": "aborted",
                            "status": "interrupted",
                            "items": [
                                {"id": "u", "type": "userMessage", "content": []},
                                {"id": "a", "type": "agentMessage", "text": "partial"},
                            ],
                        }
                    ]
                }
            }
        }
        report = project_messages(response)
        self.assertEqual(1, report["user_messages"])
        self.assertEqual(0, report["assistant_messages"])


class TriggerTests(unittest.TestCase):
    def test_149999_monitors_and_150000_arms(self) -> None:
        state = TriggerState("source-thread")
        state.observe(token_event(149_999))
        self.assertEqual("monitoring", state.state)
        self.assertEqual(0, state.generation)
        state.observe(token_event(150_000))
        self.assertEqual("rollover-pending", state.state)
        self.assertEqual(1, state.generation)

    def test_cumulative_total_cannot_arm(self) -> None:
        state = TriggerState("source-thread")
        state.observe(token_event(149_999, total=9_000_000))
        self.assertEqual("monitoring", state.state)

    def test_context_window_at_or_below_threshold_fails_configuration(self) -> None:
        for window in (149_999, 150_000):
            with self.subTest(window=window):
                with self.assertRaisesRegex(PrototypeError, "cannot reach"):
                    TriggerState("source-thread").observe(
                        token_event(149_999, window=window)
                    )

    def test_duplicate_over_threshold_events_keep_one_generation(self) -> None:
        state = TriggerState("source-thread")
        state.observe(token_event(150_000))
        state.observe(token_event(170_000))
        self.assertEqual(1, state.generation)


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
        source = fixture["thread_read"]["result"]["thread"]
        self.app_server = FakeAppServer(source)
        self.controller = CodexRolloverController(
            app_server=self.app_server,
            registry=self.registry,
            workspace=self.workspace,
            source_thread_id="source-thread",
            source_session_id="secret-source-session",
        )
        self.controller.trigger.observe(token_event(150_000))
        self.pointers = DurablePointers(
            wayfinder_path=str(self.wayfinder),
            ticket_folder=str(self.tickets),
            run_id="run-42",
            next_frontier="CR-03",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_handoff(self, rollover_id: str = "rollover-1"):
        return create_handoff(
            self.private,
            workspace=self.workspace,
            host_adapter_id=ADAPTER_ID,
            source_session_id="secret-source-session",
            generation=1,
            rollover_id=rollover_id,
            pointers=self.pointers,
            now=NOW,
        )

    def reach_boundary(self) -> None:
        self.controller.mark_turn_completed()
        self.controller.mark_owner_terminal()

    def test_pending_next_prompt_is_held_until_after_bootstrap(self) -> None:
        self.assertEqual("held", self.controller.submit_or_hold("continue CR-03"))
        handoff = self.make_handoff()
        self.reach_boundary()
        result = self.controller.rollover(
            handoff.path,
            now=NOW + 1,
            target_token_notification=token_event(
                12_000, thread_id="target-thread-1"
            ),
            ticket_list=lambda path: {"root": path, "ready": ["CR-03"]},
            run_status=lambda run_id: {"run_id": run_id, "state": "waiting"},
        )
        methods = [call["method"] for call in self.app_server.calls]
        self.assertEqual(
            ["thread/read", "thread/start", "turn/start", "turn/start"], methods
        )
        bootstrap = self.app_server.calls[2]["params"]["input"][0]["text"]
        released = self.app_server.calls[3]["params"]["input"][0]["text"]
        self.assertEqual("continue CR-03", released)
        self.assertIn(str(handoff.path), bootstrap)
        self.assertNotIn("first accepted user input", bootstrap)
        self.assertTrue(result["held_prompt_released"])

    def test_complete_path_keeps_old_thread_readable_and_reconstructs_pointers(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        result = self.controller.rollover(
            handoff.path,
            now=NOW + 1,
            target_token_notification=token_event(1, thread_id="target-thread-1"),
            ticket_list=lambda path: [Path(path).name],
            run_status=lambda run_id: {"id": run_id},
        )
        self.assertEqual("source-thread", result["source_thread_id"])
        self.assertNotEqual(result["source_thread_id"], result["target_thread_id"])
        self.assertIn("source-thread", self.app_server.threads)
        old = self.app_server.request(
            "thread/read", {"threadId": "source-thread", "includeTurns": True}
        )
        self.assertEqual("source-thread", old["thread"]["id"])
        self.assertEqual(["tickets"], result["frontier"]["ticket_inventory"])
        self.assertEqual({"id": "run-42"}, result["frontier"]["run_status"])
        self.assertEqual("CR-03", result["frontier"]["next_frontier"])
        self.assertFalse(handoff.path.exists())
        self.assertEqual("restored", result["registry_state"])

    def test_active_turn_and_nonterminal_owner_block_before_new_thread(self) -> None:
        handoff = self.make_handoff()
        with self.assertRaisesRegex(PrototypeError, "safe task boundary"):
            self.controller.rollover(
                handoff.path,
                now=NOW + 1,
                target_token_notification=token_event(
                    1, thread_id="target-thread-1"
                ),
                ticket_list=lambda _: [],
                run_status=lambda _: {},
            )
        self.assertEqual([], self.app_server.calls)
        self.controller.mark_turn_completed()
        with self.assertRaisesRegex(PrototypeError, "safe task boundary"):
            self.controller.rollover(
                handoff.path,
                now=NOW + 1,
                target_token_notification=token_event(
                    1, thread_id="target-thread-1"
                ),
                ticket_list=lambda _: [],
                run_status=lambda _: {},
            )
        self.assertEqual([], self.app_server.calls)

    def test_invalid_handoffs_fail_before_thread_side_effect(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        cases = []
        cases.append((self.root / "missing" / "HANDOFF.md", NOW + 1))
        cases.append((handoff.path, NOW + 3_600))
        original = handoff.path.read_text(encoding="utf-8")
        for label, mutate in (
            ("workspace", lambda d: d.__setitem__("workspace_key", "wrong")),
            ("consumed", lambda d: d.__setitem__("consumed", True)),
            ("schema-bool", lambda d: d.__setitem__("schema", True)),
            ("rollover-id-type", lambda d: d.__setitem__("rollover_id", 7)),
        ):
            alternate_dir = self.root / f"private-{label}"
            alternate_dir.mkdir(mode=0o700)
            alternate = alternate_dir / "HANDOFF.md"
            document = json.loads(original)
            mutate(document)
            alternate.write_text(json.dumps(document), encoding="utf-8")
            os.chmod(alternate, 0o600)
            cases.append((alternate, NOW + 1))
        malformed_dir = self.root / "private-malformed"
        malformed_dir.mkdir(mode=0o700)
        malformed = malformed_dir / "HANDOFF.md"
        malformed.write_text("{", encoding="utf-8")
        os.chmod(malformed, 0o600)
        cases.append((malformed, NOW + 1))

        for path, clock in cases:
            with self.subTest(path=path):
                before = len(self.app_server.calls)
                with self.assertRaises(PrototypeError):
                    self.controller.rollover(
                        path,
                        now=clock,
                        target_token_notification=token_event(
                            1, thread_id="target-thread-1"
                        ),
                        ticket_list=lambda _: [],
                        run_status=lambda _: {},
                    )
                self.assertEqual(before, len(self.app_server.calls))

    def test_handoff_permissions_and_source_binding_are_enforced(self) -> None:
        handoff = self.make_handoff()
        os.chmod(handoff.path, 0o644)
        with self.assertRaisesRegex(PrototypeError, "mode 0600"):
            validate_handoff(
                handoff.path,
                workspace=self.workspace,
                host_adapter_id=ADAPTER_ID,
                source_session_id="secret-source-session",
                generation=1,
                now=NOW + 1,
            )
        os.chmod(handoff.path, 0o600)
        with self.assertRaisesRegex(PrototypeError, "source session mismatch"):
            validate_handoff(
                handoff.path,
                workspace=self.workspace,
                host_adapter_id=ADAPTER_ID,
                source_session_id="other-session",
                generation=1,
                now=NOW + 1,
            )

    def test_pointer_kinds_fail_before_thread_creation(self) -> None:
        handoff = self.make_handoff()
        document = json.loads(handoff.path.read_text(encoding="utf-8"))
        document["pointers"]["wayfinder_path"] = str(self.tickets)
        handoff.path.write_text(json.dumps(document), encoding="utf-8")
        self.reach_boundary()
        with self.assertRaisesRegex(PrototypeError, "Wayfinder pointer must be a file"):
            self.controller.rollover(
                handoff.path,
                now=NOW + 1,
                target_token_notification=token_event(
                    1, thread_id="target-thread-1"
                ),
                ticket_list=lambda _: [],
                run_status=lambda _: {},
            )
        self.assertEqual([], self.app_server.calls)

    def test_stale_registry_transition_is_rejected_under_lock(self) -> None:
        handoff = self.make_handoff()
        entry = self.registry.create_or_read(
            handoff=handoff, host_adapter_id=ADAPTER_ID, generation=1
        )
        current = self.registry.begin_attempt(entry)
        replay = self.registry.begin_attempt(entry)
        self.assertEqual(current, replay)
        self.assertEqual(1, replay["attempt_count"])
        target = self.registry.record_target(current, "target-1")
        duplicate_target = self.registry.record_target(current, "target-1")
        self.assertEqual(target, duplicate_target)
        bootstrapped = self.registry.record_bootstrap(target, "bootstrap-1")
        consumed = self.registry.consume(bootstrapped, "target-1")
        with self.assertRaisesRegex(PrototypeError, "stale state"):
            self.registry.consume(bootstrapped, "target-1")
        self.assertTrue(consumed["consumed"])

    def test_failed_attempt_allocates_one_retry_but_in_progress_replay_does_not(self) -> None:
        handoff = self.make_handoff()
        entry = self.registry.create_or_read(
            handoff=handoff, host_adapter_id=ADAPTER_ID, generation=1
        )
        first = self.registry.begin_attempt(entry)
        self.assertEqual(first, self.registry.begin_attempt(first))
        failed = self.registry.fail_attempt(first)
        second = self.registry.begin_attempt(failed)
        self.assertEqual(2, second["attempt_count"])
        self.assertIsNone(second["target_thread_id"])

    def test_controller_reuses_recorded_target_on_in_progress_replay(self) -> None:
        handoff = self.make_handoff()
        entry = self.registry.create_or_read(
            handoff=handoff, host_adapter_id=ADAPTER_ID, generation=1
        )
        entry = self.registry.begin_attempt(entry)
        target = self.app_server.request(
            "thread/start", {"cwd": str(self.workspace)}
        )["thread"]
        self.registry.record_target(entry, target["id"])
        self.app_server.calls.clear()
        self.reach_boundary()
        result = self.controller.rollover(
            handoff.path,
            now=NOW + 1,
            target_token_notification=token_event(1, thread_id=target["id"]),
            ticket_list=lambda _: [],
            run_status=lambda _: {},
        )
        methods = [call["method"] for call in self.app_server.calls]
        self.assertEqual(["thread/read", "thread/read", "turn/start"], methods)
        self.assertEqual(target["id"], result["target_thread_id"])

    def test_observed_thread_start_failure_consumes_attempt_before_retry(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        request = self.app_server.request

        def fail_thread_start(method, params):
            if method == "thread/start":
                raise PrototypeError("observed transport failure")
            return request(method, params)

        self.app_server.request = fail_thread_start
        with self.assertRaisesRegex(PrototypeError, "observed transport failure"):
            self.controller.rollover(
                handoff.path,
                now=NOW + 1,
                target_token_notification=token_event(
                    1, thread_id="target-thread-1"
                ),
                ticket_list=lambda _: [],
                run_status=lambda _: {},
            )
        failed = self.registry.create_or_read(
            handoff=handoff, host_adapter_id=ADAPTER_ID, generation=1
        )
        self.assertEqual("attempt-failed", failed["state"])
        self.assertEqual(1, failed["attempt_count"])

        self.app_server.request = request
        result = self.controller.rollover(
            handoff.path,
            now=NOW + 2,
            target_token_notification=token_event(
                1, thread_id="target-thread-1"
            ),
            ticket_list=lambda _: [],
            run_status=lambda _: {},
        )
        self.assertEqual("restored", result["registry_state"])

    def test_registry_is_idempotent_and_source_sessions_do_not_collide(self) -> None:
        first = self.make_handoff()
        entry = self.registry.create_or_read(
            handoff=first, host_adapter_id=ADAPTER_ID, generation=1
        )
        replay = self.registry.create_or_read(
            handoff=first, host_adapter_id=ADAPTER_ID, generation=1
        )
        self.assertEqual(entry, replay)
        second = create_handoff(
            self.root / "private-second",
            workspace=self.workspace,
            host_adapter_id=ADAPTER_ID,
            source_session_id="other-source-session",
            generation=1,
            rollover_id="rollover-2",
            pointers=self.pointers,
            now=NOW,
        )
        second_entry = self.registry.create_or_read(
            handoff=second, host_adapter_id=ADAPTER_ID, generation=1
        )
        self.assertNotEqual(entry["source_session_key"], second_entry["source_session_key"])

    def test_target_at_threshold_fails_restore_and_keeps_handoff(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        with self.assertRaisesRegex(PrototypeError, "not below threshold"):
            self.controller.rollover(
                handoff.path,
                now=NOW + 1,
                target_token_notification=token_event(
                    150_000, thread_id="target-thread-1"
                ),
                ticket_list=lambda _: [],
                run_status=lambda _: {},
            )
        self.assertTrue(handoff.path.exists())

    def test_target_context_notification_must_belong_to_replacement(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        with self.assertRaisesRegex(PrototypeError, "thread mismatch"):
            self.controller.rollover(
                handoff.path,
                now=NOW + 1,
                target_token_notification=token_event(
                    1, thread_id="some-other-thread"
                ),
                ticket_list=lambda _: [],
                run_status=lambda _: {},
            )
        self.assertTrue(handoff.path.exists())
        entry = self.registry.create_or_read(
            handoff=handoff, host_adapter_id=ADAPTER_ID, generation=1
        )
        self.assertEqual("attempt-failed", entry["state"])

    def test_target_context_notification_must_follow_bootstrap_turn(self) -> None:
        handoff = self.make_handoff()
        self.reach_boundary()
        with self.assertRaisesRegex(PrototypeError, "turn mismatch"):
            self.controller.rollover(
                handoff.path,
                now=NOW + 1,
                target_token_notification=token_event(
                    1,
                    thread_id="target-thread-1",
                    turn_id="stale-target-turn",
                ),
                ticket_list=lambda _: [],
                run_status=lambda _: {},
            )
        self.assertTrue(handoff.path.exists())

    def test_incomplete_frontier_readback_fails_before_consumption(self) -> None:
        for missing in ("map", "inventory", "status"):
            with self.subTest(missing=missing):
                self.tearDown()
                self.setUp()
                handoff = self.make_handoff()
                if missing == "map":
                    self.wayfinder.write_text("", encoding="utf-8")
                self.reach_boundary()
                with self.assertRaisesRegex(PrototypeError, "readback"):
                    self.controller.rollover(
                        handoff.path,
                        now=NOW + 1,
                        target_token_notification=token_event(
                            1, thread_id="target-thread-1"
                        ),
                        ticket_list=(
                            (lambda _: None) if missing == "inventory" else (lambda _: [])
                        ),
                        run_status=(
                            (lambda _: None)
                            if missing == "status"
                            else (lambda run_id: {"id": run_id})
                        ),
                    )
                self.assertTrue(handoff.path.exists())
                entry = self.registry.create_or_read(
                    handoff=handoff, host_adapter_id=ADAPTER_ID, generation=1
                )
                self.assertEqual("attempt-failed", entry["state"])


class HookTests(unittest.TestCase):
    def test_hook_only_surface_does_not_claim_clear_or_fresh_thread(self) -> None:
        report = hook_only_report()
        self.assertTrue(report["controller_required"])
        claims = " ".join(report["cannot_claim"])
        self.assertIn("/clear", claims)
        self.assertIn("fresh thread", claims)
        self.assertIn("arming below 150000", claims)


if __name__ == "__main__":
    unittest.main()
