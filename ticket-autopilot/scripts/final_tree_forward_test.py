#!/usr/bin/env python3
"""Produce deterministic final-tree rollout evidence from production contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from autopilot.final_tree_projection import (
    NON_AUTHORITY,
    ProjectionExcluded,
    canonical_bytes,
    canonical_digest,
    compare_projection,
    plan_tracked_completion,
    projection_config,
)
from autopilot.final_tree_transaction import (
    apply_projection_transaction,
    new_projection_transaction,
    projection_transaction_reference,
    record_effect_readback,
    record_effect_started,
    record_effects_checkpoint,
    record_final_tree_checkpoint,
    validate_projection_transaction,
)


SCHEMA = 1
CONTRACT = "tracked-final-tree-forward-evidence-v1"
ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_FIELDS = {
    "schema",
    "source_repository",
    "run_id",
    "ticket_id",
    "artifact_generation",
    "implementation_candidate_ref",
    "delivery_candidate_ref",
    "source_relative_path",
    "destination_relative_path",
    "receipt_document",
    "verification_bundle",
    "rendered_body",
    "expected_head_sha",
    "provider_observation",
    "terminal_proof",
}

_TERMINAL_FIELDS = {
    "schema",
    "repository_identity",
    "provider",
    "pr_id",
    "head_sha",
    "pr_base",
    "terminal_branch",
    "terminal_sha",
    "terminal_tree_oid",
    "merge_commit_sha",
    "reachable_kind",
    "reachable_sha",
    "provider_observation_digest",
    "delivery_lineage_digest",
    "provenance",
}

_PROJECTION_TESTS = (
    "ticket-autopilot.tests.test_final_tree_projection.FinalTreeProjectionTests."
)
_TRANSACTION_TESTS = (
    "ticket-autopilot.tests.test_final_tree_transaction.FinalTreeTransactionTests."
)
_CLI_TESTS = "ticket-autopilot.tests.test_cli.CliTests."
_FORGED_REPLAY_TESTS = (
    "ticket-autopilot.tests.test_kernel.ForgedLifecycleReplayTests."
)
_TERMINAL_TESTS = (
    "ticket-autopilot.tests.test_kernel.TerminalIntegrationProofTests."
)

MATRIX_CHECKS = (
    {
        "label": "projection-classifier-and-parity",
        "classes": (
            "narrow-positive",
            "full-path-fallbacks",
            "fail-closed-blockers",
            "mutation-coverage",
        ),
        "tests": (
            _PROJECTION_TESTS
            + "test_candidate_drift_untracked_paths_and_ticket_mode_drift_are_excluded",
            _PROJECTION_TESTS
            + "test_changed_implementation_blob_is_visible_as_a_discrepancy",
            _PROJECTION_TESTS
            + "test_enabled_mode_produces_the_same_exact_plan_identity",
            _PROJECTION_TESTS
            + "test_extra_actual_change_is_a_discrepancy_not_parity",
            _PROJECTION_TESTS
            + "test_ineligible_inputs_are_never_classified_as_eligible",
            _PROJECTION_TESTS
            + "test_manifest_bytes_have_one_canonical_lf_terminated_encoding",
            _PROJECTION_TESTS
            + "test_missed_link_update_is_visible_as_a_discrepancy",
            _PROJECTION_TESTS
            + "test_mode_configuration_is_strict_and_defaults_to_enabled",
            _PROJECTION_TESTS
            + "test_plan_is_deterministic_complete_and_non_authoritative",
            _PROJECTION_TESTS
            + "test_planned_tree_matches_actual_completion_and_records_parity",
            _PROJECTION_TESTS
            + "test_tamper_and_duplicate_effects_fail_closed",
        ),
    },
    {
        "label": "transaction-crash-and-replay",
        "classes": (
            "recoverable-checkpoints",
            "exact-replay",
            "fail-closed-blockers",
        ),
        "tests": (
            _TRANSACTION_TESTS
            + "test_applies_exact_effects_checkpoints_and_closed_replay",
            _TRANSACTION_TESTS
            + "test_contradictions_block_without_publishing_or_rolling_back",
            _TRANSACTION_TESTS
            + "test_final_quality_checkpoint_binds_only_the_exact_projected_d",
            _TRANSACTION_TESTS
            + "test_resumes_after_each_persisted_effect_and_effects_readback",
            _TRANSACTION_TESTS
            + "test_resumes_after_intent_and_every_unrecorded_repository_effect",
            _TRANSACTION_TESTS
            + "test_stale_candidate_mode_and_unexpected_index_rows_block_before_effects",
            _TRANSACTION_TESTS
            + "test_transaction_identity_effect_order_and_final_binding_are_immutable",
        ),
    },
    {
        "label": "scheduler-history-and-exclusion",
        "classes": (
            "narrow-positive",
            "full-path-fallbacks",
            "historical-compatibility",
            "authority-separation",
        ),
        "tests": (
            _CLI_TESTS
            + "test_observe_mode_records_exact_tracked_completion_parity_without_authority",
            _CLI_TESTS
            + "test_off_mode_uses_the_complete_delivery_lifecycle_without_projection_state",
            _CLI_TESTS
            + "test_default_enabled_mode_persists_projected_not_integrated_transaction",
            _CLI_TESTS
            + "test_enabled_preflight_exclusion_stays_on_the_full_lifecycle",
            _CLI_TESTS
            + "test_final_tree_mode_cli_is_explicit_and_historical_ledgers_stay_unfabricated",
        ),
    },
    {
        "label": "closed-replay-failure-and-drift",
        "classes": (
            "recoverable-checkpoints",
            "semantic-drift",
            "authority-separation",
        ),
        "tests": (
            _FORGED_REPLAY_TESTS
            + "test_projected_quality_failure_retries_d_and_semantic_drift_restarts_i",
            _FORGED_REPLAY_TESTS
            + "test_every_emitted_event_has_closed_semantic_replay",
        ),
    },
    {
        "label": "provider-head-and-terminal-lineage",
        "classes": ("provider-lineage", "terminal-lineage", "authority-separation"),
        "tests": (
            _TERMINAL_TESTS
            + "test_exact_head_reachability_is_bound_and_drift_is_rejected",
            _TERMINAL_TESTS
            + "test_explicit_provider_merge_commit_can_prove_squash_reachability",
            _TERMINAL_TESTS
            + "test_stacked_child_waits_until_exact_head_reaches_terminal_branch",
            _TERMINAL_TESTS
            + "test_terminal_branch_drift_during_fresh_proof_is_rejected",
        ),
    },
)


def _git(repo: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if check and completed.returncode:
        detail = completed.stderr.strip() or str(completed.returncode)
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _candidate(value: object, field: str) -> dict[str, Any]:
    required = {
        "base_tree_oid",
        "candidate_tree_oid",
        "ticket_digest",
        "contract_version",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(f"{field} is not an exact CandidateRef")
    if (
        value.get("contract_version") != 2
        or any(
            not isinstance(value.get(key), str) or not value[key]
            for key in ("base_tree_oid", "candidate_tree_oid", "ticket_digest")
        )
    ):
        raise ValueError(f"{field} is not an exact CandidateRef")
    return _copy_json(value)


def _fixture(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _FIXTURE_FIELDS:
        raise ValueError("final-tree forward fixture is malformed")
    if value.get("schema") != 1:
        raise ValueError("final-tree forward fixture schema is unsupported")
    fixture = _copy_json(value)
    source = Path(fixture["source_repository"])
    if not source.is_absolute() or not source.is_dir():
        raise ValueError("final-tree forward source repository is invalid")
    for field in (
        "run_id",
        "ticket_id",
        "source_relative_path",
        "destination_relative_path",
        "rendered_body",
        "expected_head_sha",
    ):
        if not isinstance(fixture.get(field), str) or not fixture[field]:
            raise ValueError(f"final-tree forward fixture {field} is invalid")
    generation = fixture.get("artifact_generation")
    if (
        not isinstance(generation, int)
        or isinstance(generation, bool)
        or generation < 0
    ):
        raise ValueError("final-tree forward artifact generation is invalid")
    fixture["implementation_candidate_ref"] = _candidate(
        fixture["implementation_candidate_ref"], "implementation_candidate_ref"
    )
    fixture["delivery_candidate_ref"] = _candidate(
        fixture["delivery_candidate_ref"], "delivery_candidate_ref"
    )
    if not isinstance(fixture.get("receipt_document"), dict):
        raise ValueError("final-tree forward receipt is invalid")
    if not isinstance(fixture.get("verification_bundle"), dict):
        raise ValueError("final-tree forward verification bundle is invalid")
    if not isinstance(fixture.get("provider_observation"), dict):
        raise ValueError("final-tree forward provider observation is invalid")
    if not isinstance(fixture.get("terminal_proof"), dict):
        raise ValueError("final-tree forward terminal proof is invalid")
    return fixture


def _materialize_tree(source: Path, tree_oid: str, destination: Path) -> None:
    completed = subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--shared",
            "--no-checkout",
            str(source),
            str(destination),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "shared clone failed")
    _git(destination, "read-tree", tree_oid)
    _git(destination, "checkout-index", "-a", "-f")


def _replace_tree(repo: Path, tree_oid: str) -> None:
    _git(repo, "read-tree", tree_oid)
    _git(repo, "clean", "-f", "-d", "-x")
    _git(repo, "checkout-index", "-a", "-f")


def _plan(repo: Path, fixture: Mapping[str, Any], mode: str) -> dict[str, Any]:
    return plan_tracked_completion(
        repo,
        run_id=fixture["run_id"],
        ticket_id=fixture["ticket_id"],
        artifact_generation=fixture["artifact_generation"],
        configuration=projection_config(mode),
        candidate_ref=fixture["implementation_candidate_ref"],
        source_relative_path=fixture["source_relative_path"],
        destination_relative_path=fixture["destination_relative_path"],
        receipt_document=fixture["receipt_document"],
        source_mode="tracked",
        delivery_metadata={},
        pr=None,
        excluded_reasons=(),
    ).manifest


def _apply_enabled(
    repo: Path,
    manifest: Mapping[str, Any],
    *,
    after_intent: Callable[[], None] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    manifest_bytes = canonical_bytes(manifest)
    reference = projection_transaction_reference(
        manifest,
        artifact=f"sha256://{_sha256(manifest_bytes)}",
        sha256=_sha256(manifest_bytes),
    )
    transaction = new_projection_transaction(reference, manifest)
    if after_intent is not None:
        after_intent()

    def current() -> Mapping[str, Any]:
        return transaction

    def started(effect_key: str) -> None:
        nonlocal transaction
        transaction, _ = record_effect_started(transaction, effect_key)

    def applied(effect_key: str, readback: Mapping[str, Any]) -> None:
        nonlocal transaction
        transaction, _ = record_effect_readback(transaction, effect_key, readback)

    def effects_read_back(tree_oid: str, diff_digest: str) -> None:
        nonlocal transaction
        transaction, _ = record_effects_checkpoint(
            transaction,
            actual_tree_oid=tree_oid,
            actual_diff_digest=diff_digest,
        )

    result = apply_projection_transaction(
        repo,
        manifest,
        get_transaction=current,
        persist_effect_started=started,
        persist_effect=applied,
        persist_effects_readback=effects_read_back,
    )
    transaction, _ = record_final_tree_checkpoint(
        transaction, result["candidate_ref"]
    )
    replay = apply_projection_transaction(
        repo,
        manifest,
        get_transaction=current,
        persist_effect_started=started,
        persist_effect=applied,
        persist_effects_readback=effects_read_back,
    )
    return validate_projection_transaction(transaction), result, replay["result"]


def _default_matrix_runner(check: Mapping[str, Any]) -> bool:
    completed = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", *check["tests"]],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def _validate_delivery_lineage(
    source: Path, fixture: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    delivery = fixture["delivery_candidate_ref"]
    bundle = fixture["verification_bundle"]
    provider = fixture["provider_observation"]
    terminal = fixture["terminal_proof"]
    body = fixture["rendered_body"]
    head = fixture["expected_head_sha"]
    expected_reachable = (
        head
        if terminal.get("reachable_kind") == "head"
        else provider.get("merge_commit_sha")
        if terminal.get("reachable_kind") == "merge-commit"
        else None
    )
    if (
        bundle.get("candidate_ref") != delivery
        or bundle.get("verification", {}).get("candidate_ref") != delivery
        or bundle.get("verification", {}).get("release_status") != "eligible"
        or delivery["candidate_tree_oid"] not in body
        or head not in body
        or provider.get("schema") != 1
        or provider.get("observed") is not True
        or provider.get("operation") != "get-pr-state"
        or provider.get("state") != "merged"
        or provider.get("head_sha") != head
        or provider.get("base") != "main"
        or provider.get("body") != body
        or provider.get("evidence_class") not in {"live", "simulated"}
        or set(terminal) != _TERMINAL_FIELDS
        or terminal.get("schema") != 1
        or terminal.get("repository_identity") != str(source)
        or terminal.get("provider") != provider.get("provider")
        or terminal.get("pr_id") != provider.get("pr_id")
        or terminal.get("head_sha") != head
        or terminal.get("pr_base") != provider.get("base")
        or terminal.get("terminal_branch") != "main"
        or terminal.get("terminal_tree_oid") != delivery["candidate_tree_oid"]
        or terminal.get("merge_commit_sha")
        != provider.get("merge_commit_sha")
        or not _is_digest(terminal.get("provider_observation_digest"))
        or not _is_digest(terminal.get("delivery_lineage_digest"))
        or terminal.get("reachable_sha") != expected_reachable
        or terminal.get("provenance")
        not in {"runner-merge", "external-merge"}
        or not isinstance(terminal.get("terminal_sha"), str)
        or not terminal["terminal_sha"]
    ):
        raise ValueError(
            "final verification, body, provider, or terminal lineage is stale"
        )
    if subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            terminal["reachable_sha"],
            terminal["terminal_sha"],
        ],
        cwd=source,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode:
        raise ValueError(
            "terminal branch does not contain the recorded reachable object"
        )
    return bundle, provider, body, head


def _matrix(
    runner: Callable[[Mapping[str, Any]], bool], *, skip: bool
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    classes: dict[str, str] = {}
    logical_tests = 0
    for check in MATRIX_CHECKS:
        tests = tuple(check["tests"])
        if not tests or len(set(tests)) != len(tests):
            raise ValueError(
                f"matrix test identities are invalid: {check['label']}"
            )
        result = "not-run" if skip else "pass" if runner(check) else "fail"
        count = len(tests)
        logical_tests += count
        checks.append(
            {
                "label": check["label"],
                "logical_tests": count,
                "result": result,
            }
        )
        for outcome_class in check["classes"]:
            previous = classes.get(outcome_class)
            if previous == "fail" or result == "fail":
                classes[outcome_class] = "fail"
            elif previous == "not-run" or result == "not-run":
                classes[outcome_class] = "not-run"
            else:
                classes[outcome_class] = "pass"
    return {
        "logical_checks": len(checks),
        "logical_tests": logical_tests,
        "checks": checks,
        "outcome_classes": dict(sorted(classes.items())),
        "result": (
            "not-run"
            if skip
            else "pass"
            if all(item["result"] == "pass" for item in checks)
            else "fail"
        ),
    }


def build_report(
    fixture_value: object,
    *,
    matrix_runner: Callable[[Mapping[str, Any]], bool] = _default_matrix_runner,
    skip_matrix: bool = False,
) -> dict[str, Any]:
    fixture = _fixture(fixture_value)
    source = Path(fixture["source_repository"])
    implementation = fixture["implementation_candidate_ref"]
    delivery = fixture["delivery_candidate_ref"]
    if (
        implementation["base_tree_oid"] != delivery["base_tree_oid"]
        or implementation["ticket_digest"] != delivery["ticket_digest"]
    ):
        raise ValueError("final-tree forward candidate lineage is contradictory")
    delivery_tree = delivery["candidate_tree_oid"]
    if _git(source, "rev-parse", f"{delivery_tree}^{{tree}}") != delivery_tree:
        raise ValueError("final-tree forward delivery tree is unavailable")

    with tempfile.TemporaryDirectory(prefix="final-tree-forward-") as directory:
        observe_repo = Path(directory) / "observe"
        _materialize_tree(source, implementation["candidate_tree_oid"], observe_repo)
        observe_manifest = _plan(observe_repo, fixture, "observe")
        if observe_manifest["planned_delivery_candidate_ref"] != delivery:
            raise ValueError("observed planned D differs from authoritative delivery D")
        _replace_tree(observe_repo, delivery["candidate_tree_oid"])
        observation = compare_projection(
            observe_repo, observe_manifest, delivery
        ).document
        if observation["status"] != "parity":
            raise ValueError("authoritative delivery differs from observed projection")

        enabled_repo = Path(directory) / "enabled"
        _materialize_tree(source, implementation["candidate_tree_oid"], enabled_repo)
        enabled_manifest = _plan(enabled_repo, fixture, "enabled")
        comparable = (
            "implementation_candidate_ref",
            "planned_delivery_candidate_ref",
            "ticket",
            "completion_receipt",
            "link_closure",
            "effects",
            "expected_diff",
            "negative_proof",
        )
        if any(observe_manifest[key] != enabled_manifest[key] for key in comparable):
            raise ValueError(
                "observe and enabled manifests disagree on delivery effects"
            )
        off_reason: str | None = None

        def select_off_after_intent() -> None:
            nonlocal off_reason
            try:
                _plan(enabled_repo, fixture, "off")
            except ProjectionExcluded as error:
                off_reason = error.code
            else:
                raise ValueError("off mode unexpectedly planned a new projection")

        transaction, apply_result, replay_result = _apply_enabled(
            enabled_repo,
            enabled_manifest,
            after_intent=select_off_after_intent,
        )
        if (
            apply_result["candidate_ref"] != delivery
            or transaction["planned_delivery_candidate_ref"] != delivery
            or transaction["status"] != "projected-not-integrated"
            or _git(enabled_repo, "write-tree") != delivery["candidate_tree_oid"]
            or replay_result != "already-applied"
        ):
            raise ValueError("enabled transaction did not close over exact D")

        if off_reason != "mode":
            raise ValueError("off rollback did not preserve the in-flight intent")

    bundle, provider, body, head = _validate_delivery_lineage(
        source, fixture
    )
    terminal = fixture["terminal_proof"]
    matrix = _matrix(matrix_runner, skip=skip_matrix)
    report_payload = {
        "schema": SCHEMA,
        "contract": CONTRACT,
        "run_id": fixture["run_id"],
        "ticket_id": fixture["ticket_id"],
        "implementation_candidate_ref": implementation,
        "delivery_candidate_ref": delivery,
        "observation": {
            "status": observation["status"],
            "manifest_digest": observe_manifest["manifest_digest"],
            "observation_digest": observation["observation_digest"],
            "planned_tree_oid": observe_manifest[
                "planned_delivery_candidate_ref"
            ]["candidate_tree_oid"],
            "authoritative_tree_oid": delivery["candidate_tree_oid"],
            "effect_count": len(observe_manifest["effects"]),
            "effects_digest": canonical_digest(observe_manifest["effects"]),
            "receipt_sha256": observe_manifest["completion_receipt"]["sha256"],
            "link_closure_digest": canonical_digest(observe_manifest["link_closure"]),
        },
        "enabled_replay": {
            "transaction_id": transaction["transaction_id"],
            "status": transaction["status"],
            "effect_count": len(transaction["effect_bindings"]),
            "checkpoints": sorted(transaction["checkpoints"]),
            "final_replay": replay_result,
            "new_default_off_reason": off_reason,
            "persisted_intent_contract_version": transaction["contract_version"],
        },
        "delivery_lineage": {
            "verification_record_canonical_sha256": _sha256(
                canonical_bytes(bundle)
            ),
            "rendered_body_sha256": _sha256(body.encode("utf-8")),
            "provider_observation_sha256": canonical_digest(provider),
            "provider_evidence_class": provider["evidence_class"],
            "provider_head_sha": head,
            "terminal_proof_sha256": canonical_digest(terminal),
            "terminal_sha": terminal["terminal_sha"],
            "terminal_tree_oid": terminal["terminal_tree_oid"],
            "recorded_head_reachable": True,
        },
        "matrix": matrix,
        "authority": _copy_json(NON_AUTHORITY),
        "logical_counts_only": True,
        "limitations": [
            "Matrix provider commands use deterministic local fakes and grant "
            "no live-provider or merge authority.",
            "The retained report contains logical command and check counts only; "
            "it makes no wall-time, token, provider-savings, or universal "
            "performance claim.",
            "The provider lineage is readback evidence supplied by the fixture; "
            "this harness performs no provider mutation.",
        ],
    }
    report = {
        **report_payload,
        "result": matrix["result"],
        "report_digest": canonical_digest(report_payload),
    }
    return report


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}."
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--skip-matrix",
        action="store_true",
        help="diagnose parity and replay without producing a passing matrix result",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    try:
        report = build_report(fixture, skip_matrix=args.skip_matrix)
    except (OSError, RuntimeError, ValueError) as error:
        print(
            json.dumps(
                {"schema": SCHEMA, "result": "fail", "error": str(error)},
                sort_keys=True,
            )
        )
        return 1
    rendered = canonical_bytes(report)
    if args.output is not None:
        _atomic_write(args.output, rendered)
    sys.stdout.buffer.write(rendered)
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
