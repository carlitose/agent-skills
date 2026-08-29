from __future__ import annotations

import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from model import (
    EscalationCoordinator,
    EscalationStore,
    FakeIssueAdapter,
    ProviderIssue,
    RecordRejected,
    RunBindingRejected,
    SimulatedCrash,
    accepted_record,
    canonical_bytes,
    fingerprint,
    fingerprint_projection,
    marker_for,
    protected_run_state,
    render_issue,
    valid_run_binding,
    validate_record,
)


HERE = Path(__file__).resolve().parent


def seeded_issue(state: str = "open", *, issue_id: int = 41) -> ProviderIssue:
    value = fingerprint(accepted_record())
    return ProviderIssue(
        repository="carlitose/agent-skills",
        issue_id=issue_id,
        state=state,
        fingerprint=value,
        title="existing synthetic issue",
        body=marker_for(value),
    )


class RecordContractTests(unittest.TestCase):
    def test_accepted_record_is_copied_and_has_deterministic_fingerprint(self) -> None:
        record = accepted_record()
        normalized = validate_record(record)
        self.assertEqual(record, normalized)
        self.assertIsNot(record, normalized)
        self.assertEqual(64, len(fingerprint(normalized)))
        self.assertEqual(fingerprint(normalized), fingerprint(copy.deepcopy(record)))

    def test_projection_ignores_excluded_volatile_fixture_fields_but_validation_rejects_them(self) -> None:
        baseline = accepted_record()
        value = fingerprint(baseline)
        excluded = {
            "absolute_path": "/Users/example/repository/file.py",
            "run_id": "runner-defect-issues-20260829",
            "timestamp": "2026-08-29T12:00:00Z",
            "branch": "refs/heads/feature/example",
            "worktree": "/tmp/worktree",
            "actor": "user:example",
            "provider_request_id": "request-123",
            "stack_line": "line 947",
        }
        for key, transient in excluded.items():
            with self.subTest(key=key):
                fixture = copy.deepcopy(baseline)
                fixture[key] = transient
                self.assertEqual(
                    fingerprint_projection(baseline), fingerprint_projection(fixture)
                )
                self.assertEqual(value, fingerprint(fixture))
                with self.assertRaisesRegex(RecordRejected, "record-shape"):
                    validate_record(fixture)

    def test_symptom_and_evidence_order_do_not_split_equivalent_failure(self) -> None:
        first = accepted_record()
        second = copy.deepcopy(first)
        second["failure"]["symptom"] = "A second sanitized observer sees the same rejection."
        second["evidence"].reverse()
        self.assertEqual(fingerprint(first), fingerprint(second))
        self.assertEqual(validate_record(second), second)

    def test_owner_failure_code_phase_and_invariant_are_fingerprint_sensitive(self) -> None:
        baseline = accepted_record()
        for path, replacement in (
            (("owner", "module"), "autopilot.ledger"),
            (("owner", "anchor"), "AtomicLedger.save"),
            (("failure", "code"), "ledger-replay-regression"),
            (("failure", "phase"), "ledger-replay"),
            (("failure", "invariant"), "A validated replay must preserve semantic state."),
        ):
            with self.subTest(path=path):
                changed = copy.deepcopy(baseline)
                changed[path[0]][path[1]] = replacement
                self.assertNotEqual(fingerprint(baseline), fingerprint(changed))

    def test_every_non_defect_taxonomy_family_is_rejected(self) -> None:
        for classification in (
            "project-failure",
            "provider-environment-failure",
            "expected-gate",
            "unsupported-configuration",
            "user-input-error",
        ):
            with self.subTest(classification=classification):
                record = accepted_record()
                record["classification"] = classification
                with self.assertRaisesRegex(
                    RecordRejected, "classification-not-runner-defect"
                ):
                    validate_record(record)

    def test_low_and_medium_confidence_are_rejected_before_rd03_decision(self) -> None:
        for level in ("low", "medium"):
            with self.subTest(level=level):
                record = accepted_record()
                record["confidence"]["level"] = level
                with self.assertRaisesRegex(RecordRejected, "confidence-below"):
                    validate_record(record)

    def test_unknown_metadata_unredacted_evidence_and_authority_are_rejected(self) -> None:
        fixtures = []
        unknown = accepted_record()
        unknown["raw_exception"] = "safe-looking but forbidden"
        fixtures.append(unknown)
        evidence_extra = accepted_record()
        evidence_extra["evidence"][0]["stdout"] = "raw output"
        fixtures.append(evidence_extra)
        authority = accepted_record()
        authority["merge_grant"] = "grant:123"
        fixtures.append(authority)
        unredacted = accepted_record()
        unredacted["redaction"]["applied"] = False
        fixtures.append(unredacted)
        for index, fixture in enumerate(fixtures):
            with self.subTest(index=index):
                with self.assertRaises(RecordRejected):
                    validate_record(fixture)

    def test_secret_path_private_content_markdown_and_stack_line_fixtures_are_rejected(self) -> None:
        unsafe_values = (
            "Authorization Bearer abc123 reaches the adapter.",
            "The fixture reads /Users/example/private/file.txt.",
            "The fixture contains private content from the candidate.",
            "The stack fails at line 947.",
            "`raw Markdown passthrough` is present.",
            "A **bold Markdown payload** is present.",
            "A [link](https://example.invalid) is present.",
            "A ghp_abcdefghijklmnopqrstuvwxyz token value is present.",
            "The run runner-defect-issues-20260829 fails.",
        )
        for unsafe in unsafe_values:
            with self.subTest(unsafe=unsafe):
                record = accepted_record()
                record["evidence"][0]["summary"] = unsafe
                with self.assertRaises(RecordRejected):
                    validate_record(record)

    def test_schema_bounds_digests_and_required_evidence_are_strict(self) -> None:
        bad_schema = accepted_record()
        bad_schema["schema"] = 2
        bad_digest = accepted_record()
        bad_digest["feedback_loop"]["artifact_sha256"] = "ABC"
        no_local = accepted_record()
        no_local["evidence"] = [
            {
                "class": "static-source",
                "summary": "Only a source trace exists.",
                "artifact_sha256": "e" * 64,
            }
        ]
        long_text = accepted_record()
        long_text["failure"]["symptom"] = "x" * 241
        for fixture in (bad_schema, bad_digest, no_local, long_text):
            with self.subTest(fixture=fixture):
                with self.assertRaises(RecordRejected):
                    validate_record(fixture)

    def test_issue_rendering_contains_only_stable_sanitized_record_fields(self) -> None:
        record = validate_record(accepted_record())
        value = fingerprint(record)
        title, body = render_issue(record, value)
        self.assertIn(record["failure"]["code"], title)
        self.assertIn(marker_for(value), body)
        self.assertIn(record["failure"]["invariant"], body)
        self.assertNotIn("run_id", body)
        self.assertNotIn("Authorization", body)
        self.assertNotIn("merge_grant", body)


class EscalationLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="rd02-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = EscalationStore(self.root / "sidecar")
        self.record = accepted_record()
        self.binding = valid_run_binding()
        self.protected = protected_run_state()
        self.protected_bytes = canonical_bytes(self.protected)

    def coordinator(self, adapter: FakeIssueAdapter) -> EscalationCoordinator:
        return EscalationCoordinator(self.store, adapter)

    def escalate(
        self,
        adapter: FakeIssueAdapter,
        *,
        crash_at: str | None = None,
    ):
        return self.coordinator(adapter).escalate(
            self.record,
            run_binding=self.binding,
            protected_state=self.protected,
            crash_at=crash_at,
        )

    def assert_protected_unchanged(self) -> None:
        self.assertEqual(self.protected_bytes, canonical_bytes(self.protected))

    def test_absent_search_creates_once_and_persists_published_receipt(self) -> None:
        adapter = FakeIssueAdapter()
        result = self.escalate(adapter)
        self.assertEqual("published", result.state)
        self.assertEqual(["search", "create"], [name for name, _ in adapter.calls])
        self.assertEqual(1, adapter.call_count("create"))
        self.assertEqual("created", result.as_dict()["receipt"]["disposition"])
        self.assertEqual((f"{result.fingerprint}.json",), self.store.list_documents())
        self.assert_protected_unchanged()

    def test_open_and_closed_exact_matches_deduplicate_without_mutation(self) -> None:
        for state in ("open", "closed"):
            with self.subTest(state=state):
                store = EscalationStore(self.root / state)
                adapter = FakeIssueAdapter(issues=(seeded_issue(state),))
                result = EscalationCoordinator(store, adapter).escalate(
                    self.record,
                    run_binding=self.binding,
                    protected_state=self.protected,
                )
                self.assertEqual("deduplicated", result.state)
                self.assertEqual(state, result.as_dict()["receipt"]["issue_state"])
                self.assertEqual(0, adapter.call_count("create"))
        self.assert_protected_unchanged()

    def test_offline_is_retryable_and_permission_failure_is_terminal(self) -> None:
        offline = FakeIssueAdapter(search_mode="offline")
        result = self.escalate(offline)
        self.assertEqual("retryable-failure", result.state)
        self.assertEqual("offline", result.as_dict()["failure"]["code"])
        self.assertEqual(0, offline.call_count("create"))
        offline.search_mode = "normal"
        recovered = self.escalate(offline)
        self.assertEqual("published", recovered.state)
        self.assertEqual(1, offline.call_count("create"))

        permission_store = EscalationStore(self.root / "permission")
        permission = FakeIssueAdapter(search_mode="permission")
        coordinator = EscalationCoordinator(permission_store, permission)
        denied = coordinator.escalate(
            self.record,
            run_binding=self.binding,
            protected_state=self.protected,
        )
        before = list(permission.calls)
        replay = coordinator.escalate(
            self.record,
            run_binding=self.binding,
            protected_state=self.protected,
        )
        self.assertEqual("terminal-failure", denied.state)
        self.assertEqual(denied.document_bytes, replay.document_bytes)
        self.assertEqual(before, permission.calls)
        self.assert_protected_unchanged()

    def test_ambiguous_and_inconclusive_search_never_create(self) -> None:
        scenarios = (
            FakeIssueAdapter(search_mode="ambiguous", issues=(seeded_issue(),)),
            FakeIssueAdapter(search_mode="inconclusive-absent"),
        )
        for index, adapter in enumerate(scenarios):
            with self.subTest(index=index):
                store = EscalationStore(self.root / f"search-{index}")
                result = EscalationCoordinator(store, adapter).escalate(
                    self.record,
                    run_binding=self.binding,
                    protected_state=self.protected,
                )
                self.assertEqual("retryable-failure", result.state)
                self.assertEqual(0, adapter.call_count("create"))
        self.assert_protected_unchanged()

    def test_exact_replay_is_byte_identical_and_performs_no_provider_call(self) -> None:
        adapter = FakeIssueAdapter()
        coordinator = self.coordinator(adapter)
        first = coordinator.escalate(
            self.record,
            run_binding=self.binding,
            protected_state=self.protected,
        )
        calls = list(adapter.calls)
        second = coordinator.escalate(
            copy.deepcopy(self.record),
            run_binding=self.binding,
            protected_state=self.protected,
        )
        self.assertEqual(first.document_bytes, second.document_bytes)
        self.assertEqual(calls, adapter.calls)
        self.assert_protected_unchanged()

    def test_crash_before_reservation_leaves_no_document_and_replay_creates_once(self) -> None:
        adapter = FakeIssueAdapter()
        with self.assertRaisesRegex(SimulatedCrash, "before-reservation"):
            self.escalate(adapter, crash_at="before-reservation")
        self.assertEqual((), self.store.list_documents())
        result = self.escalate(adapter)
        self.assertEqual("published", result.state)
        self.assertEqual(1, adapter.call_count("create"))
        self.assert_protected_unchanged()

    def test_crash_after_reservation_and_after_search_resume_safely(self) -> None:
        for crash_at in ("after-reservation", "after-search"):
            with self.subTest(crash_at=crash_at):
                store = EscalationStore(self.root / crash_at)
                adapter = FakeIssueAdapter()
                coordinator = EscalationCoordinator(store, adapter)
                with self.assertRaisesRegex(SimulatedCrash, crash_at):
                    coordinator.escalate(
                        self.record,
                        run_binding=self.binding,
                        protected_state=self.protected,
                        crash_at=crash_at,
                    )
                result = coordinator.escalate(
                    self.record,
                    run_binding=self.binding,
                    protected_state=self.protected,
                )
                self.assertEqual("published", result.state)
                self.assertEqual(1, adapter.call_count("create"))
        self.assert_protected_unchanged()

    def test_crash_before_create_searches_again_then_makes_the_only_create_call(self) -> None:
        adapter = FakeIssueAdapter()
        with self.assertRaisesRegex(SimulatedCrash, "before-create"):
            self.escalate(adapter, crash_at="before-create")
        self.assertEqual(0, adapter.call_count("create"))
        first_calls = list(adapter.calls)
        result = self.escalate(adapter)
        self.assertEqual("published", result.state)
        self.assertEqual(1, adapter.call_count("create"))
        self.assertEqual("search", adapter.calls[len(first_calls)][0])
        self.assert_protected_unchanged()

    def test_crash_after_create_recovers_by_exact_search_without_second_create(self) -> None:
        adapter = FakeIssueAdapter()
        with self.assertRaisesRegex(SimulatedCrash, "after-create"):
            self.escalate(adapter, crash_at="after-create")
        self.assertEqual(1, adapter.call_count("create"))
        result = self.escalate(adapter)
        self.assertEqual("deduplicated", result.state)
        self.assertEqual(1, adapter.call_count("create"))
        self.assertEqual(1, len(adapter.issues))
        self.assert_protected_unchanged()

    def test_lost_response_remains_ambiguous_then_search_deduplicates(self) -> None:
        adapter = FakeIssueAdapter(create_mode="lost-response")
        ambiguous = self.escalate(adapter)
        self.assertEqual("dispatch-ambiguous", ambiguous.state)
        self.assertEqual("lost-response", ambiguous.as_dict()["failure"]["code"])
        self.assertEqual(1, adapter.call_count("create"))
        recovered = self.escalate(adapter)
        self.assertEqual("deduplicated", recovered.state)
        self.assertEqual(1, adapter.call_count("create"))
        self.assert_protected_unchanged()

    def test_ambiguous_dispatch_with_inconclusive_absence_never_retries_create(self) -> None:
        adapter = FakeIssueAdapter()
        with self.assertRaises(SimulatedCrash):
            self.escalate(adapter, crash_at="before-create")
        adapter.search_mode = "inconclusive-absent"
        result = self.escalate(adapter)
        self.assertEqual("dispatch-ambiguous", result.state)
        self.assertEqual(0, adapter.call_count("create"))
        second = self.escalate(adapter)
        self.assertEqual("dispatch-ambiguous", second.state)
        self.assertEqual(0, adapter.call_count("create"))
        self.assert_protected_unchanged()

    def test_contradictory_create_receipt_fails_closed_and_is_not_retried(self) -> None:
        adapter = FakeIssueAdapter(create_mode="contradictory")
        first = self.escalate(adapter)
        self.assertEqual("terminal-failure", first.state)
        self.assertEqual(
            "contradictory-provider-receipt", first.as_dict()["failure"]["code"]
        )
        second = self.escalate(adapter)
        self.assertEqual(first.document_bytes, second.document_bytes)
        self.assertEqual(1, adapter.call_count("create"))
        self.assert_protected_unchanged()

    def test_concurrent_equivalent_reports_share_one_reservation_and_one_create(self) -> None:
        adapter = FakeIssueAdapter()
        coordinator = self.coordinator(adapter)

        def invoke(_index: int):
            variant = copy.deepcopy(self.record)
            variant["failure"]["symptom"] = (
                "A concurrent sanitized observer sees the same rejection."
            )
            return coordinator.escalate(
                variant,
                run_binding=self.binding,
                protected_state=self.protected,
            )

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(invoke, range(16)))
        self.assertEqual({"published"}, {item.state for item in results})
        self.assertEqual(1, len({item.document_bytes for item in results}))
        self.assertEqual(1, adapter.call_count("create"))
        self.assertEqual(1, adapter.call_count("search"))
        self.assert_protected_unchanged()

    def test_missing_malformed_corrupt_and_unbound_ledgers_perform_no_provider_operation(self) -> None:
        bindings = []
        bindings.append(None)
        malformed = valid_run_binding()
        malformed.pop("schema")
        bindings.append(malformed)
        corrupt = valid_run_binding()
        corrupt["integrity"] = "invalid"
        bindings.append(corrupt)
        unbound = valid_run_binding()
        unbound["repository"] = "other/repository"
        bindings.append(unbound)
        for index, binding in enumerate(bindings):
            with self.subTest(index=index):
                store = EscalationStore(self.root / f"binding-{index}")
                adapter = FakeIssueAdapter()
                with self.assertRaises(RunBindingRejected):
                    EscalationCoordinator(store, adapter).escalate(
                        self.record,
                        run_binding=binding,
                        protected_state=self.protected,
                    )
                self.assertEqual([], adapter.calls)
                self.assertEqual((), store.list_documents())
        self.assert_protected_unchanged()

    def test_rejected_record_performs_no_provider_operation_or_durable_capture(self) -> None:
        adapter = FakeIssueAdapter()
        unsafe = accepted_record()
        unsafe["evidence"][0]["summary"] = "Authorization token abc is exposed."
        with self.assertRaises(RecordRejected):
            self.coordinator(adapter).escalate(
                unsafe,
                run_binding=self.binding,
                protected_state=self.protected,
            )
        self.assertEqual([], adapter.calls)
        self.assertEqual((), self.store.list_documents())
        self.assert_protected_unchanged()


class PrototypeBoundaryTests(unittest.TestCase):
    def test_model_imports_only_standard_library_modules(self) -> None:
        tree = ast.parse((HERE / "model.py").read_text(encoding="utf-8"))
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertEqual(
            {
                "__future__",
                "contextlib",
                "copy",
                "dataclasses",
                "fcntl",
                "hashlib",
                "json",
                "os",
                "pathlib",
                "re",
                "threading",
                "typing",
            },
            roots,
        )

    def test_fake_adapter_has_no_comment_reopen_label_close_or_network_surface(self) -> None:
        public = {
            name
            for name in dir(FakeIssueAdapter)
            if not name.startswith("_") and callable(getattr(FakeIssueAdapter, name))
        }
        self.assertEqual({"call_count", "create", "search_exact"}, public)

    def test_dry_run_transcript_is_deterministic_and_covers_required_states(self) -> None:
        command = [sys.executable, "-B", str(HERE / "runner.py")]
        first = subprocess.run(
            command, cwd=HERE, text=True, capture_output=True, check=False
        )
        second = subprocess.run(
            command, cwd=HERE, text=True, capture_output=True, check=False
        )
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        transcript = json.loads(first.stdout)
        states = {
            value["state"] for value in transcript["scenarios"].values()
        }
        self.assertTrue(
            {
                "published",
                "deduplicated",
                "retryable-failure",
                "terminal-failure",
                "dispatch-ambiguous",
            }.issubset(states)
        )
        self.assertEqual(
            1,
            transcript["scenarios"]["crash-after-create-replay"]["create_calls"],
        )


if __name__ == "__main__":
    unittest.main()
