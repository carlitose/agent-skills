from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from .ticket_contract import (
    ContractError,
    migrate_ticket_text,
    parse_ticket_folder,
    parse_ticket_markdown,
    serialize_ticket_markdown,
    validate_ticket_graph,
)
from .finalizer import DeliveryBodyError, DeliveryFinalizer
from .git_ops import (
    CommandRunner,
    GitError,
    assert_cleanup_safe,
    assert_remote_head,
    assert_ticket_folder_at_ref,
    candidate_files,
    candidate_ref,
    create_isolated_worktree,
    origin_url,
    remove_isolated_worktree,
    repository_root,
    run_git,
    SubprocessCommandRunner,
    run_directory,
)
from .kernel import Kernel, TransitionError
from .leaf_protocol import LEAF_PHASE_CONTRACTS, LEAF_RESULT_SCHEMA
from .ledger import AtomicLedger, LedgerError
from .providers import (
    GET_PR_STATE,
    MERGE_EXPECTED_HEAD,
    RETARGET_PR,
    ProviderExecutor,
    ProviderError,
    REQUIRED_CAPABILITIES,
    detect_provider,
)
from .verification_checkpoint import (
    CheckpointPhaseFailure,
    CheckpointStatus,
    VerificationCheckpointError,
    inspect_verification_checkpoints,
    load_verification_adapters,
    run_verification_checkpoints,
)


OUTPUT_SCHEMA = 1


class StructuredArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        command = (
            sys.argv[1]
            if len(sys.argv) > 1 and not sys.argv[1].startswith("-")
            else "arguments"
        )
        _emit(
            _response(
                command,
                False,
                error={"type": "ArgumentError", "message": message},
            )
        )
        raise SystemExit(2)


def _response(command: str, ok: bool, **items: Any) -> dict[str, Any]:
    return {"schema": OUTPUT_SCHEMA, "ok": ok, "command": command, **items}


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def _provider(repo: Path, override: str | None) -> tuple[str, dict[str, object]]:
    remote = origin_url(repo)
    if not override and not remote:
        raise ProviderError(
            "repository has no origin; pass --provider for deterministic negotiation"
        )
    provider = detect_provider(remote or "", override=override)
    evidence = provider.negotiate(REQUIRED_CAPABILITIES)
    return provider.name, evidence


def _plan(args: argparse.Namespace) -> dict[str, Any]:
    repo = repository_root(Path(args.repo))
    graph = parse_ticket_folder(Path(args.folder))
    provider_name, capabilities = _provider(repo, args.provider)
    preview = Kernel.new("plan", graph, provider=provider_name).report()
    return {
        "ticket_folder": str(graph.folder),
        "repo": str(repo),
        "provider": capabilities,
        "ticket_order": list(graph.order),
        "ready": preview["ready"],
        "dependency_blocked": preview["dependency_blocked"],
        "human_gates": preview["open_gates"],
        "mutation_planned": False,
    }


def _run(args: argparse.Namespace) -> dict[str, Any]:
    repo = repository_root(Path(args.repo))
    graph = parse_ticket_folder(Path(args.folder))
    assert_ticket_folder_at_ref(repo, graph.folder, base_ref=args.base)
    provider_name, capabilities = _provider(repo, args.provider)
    run_id = args.run_id or uuid.uuid4().hex[:16]
    run_dir = run_directory(repo, run_id)
    ledger_path = run_dir / "ledger.json"
    store = AtomicLedger(ledger_path)
    worktree: Path | None = None
    with store.run_locked():
        if ledger_path.exists():
            raise LedgerError(f"run already exists: {run_id}")
        try:
            worktree = create_isolated_worktree(repo, run_id, base_ref=args.base)
            base_sha = run_git(worktree, "rev-parse", "HEAD")
            kernel = Kernel.new(
                run_id,
                graph,
                max_quality_failures=args.max_quality_failures,
                max_leaf_interactions=args.max_leaf_interactions,
                max_leaf_tool_calls=args.max_leaf_tool_calls,
                max_leaf_wall_time=args.max_leaf_wall_time,
                provider=provider_name,
                provider_mode=args.provider_mode,
                worktree=str(worktree),
                repo=str(repo),
                provider_capabilities=capabilities,
                base_sha=base_sha,
            )
            store.save(kernel.ledger)
        except Exception:
            if worktree is not None and worktree.exists():
                remove_isolated_worktree(repo, worktree)
            raise
    return {
        **kernel.report(),
        "repo": str(repo),
        "worktree": str(worktree),
        "ledger": str(ledger_path),
        "provider": capabilities,
        "provider_mode": args.provider_mode,
    }


def _store(repo_value: str, run_id: str) -> tuple[Path, AtomicLedger]:
    repo = repository_root(Path(repo_value))
    store = AtomicLedger(run_directory(repo, run_id) / "ledger.json")
    return repo, store


def _load(repo_value: str, run_id: str) -> tuple[AtomicLedger, Kernel]:
    repo, store = _store(repo_value, run_id)
    document = store.load()
    if Path(document.get("repo", "")).resolve() != repo:
        raise LedgerError("ledger repository binding does not match --repo")
    return store, Kernel(document)


def _status(args: argparse.Namespace) -> dict[str, Any]:
    store, kernel = _load(args.repo, args.run_id)
    return {**kernel.report(), "ledger": str(store.path), "worktree": kernel.ledger["worktree"]}


def _resume(args: argparse.Namespace) -> dict[str, Any]:
    _, store = _store(args.repo, args.run_id)
    with store.run_locked():
        document = store.load()
        kernel = Kernel(document)
        worktree = Path(kernel.ledger["worktree"])
        if not worktree.is_dir():
            raise GitError(f"isolated worktree is missing: {worktree}")
        repository_root(worktree)
        processed: list[dict[str, object]] = []
        if args.events:
            processed = _process_events(
                args,
                store,
                kernel,
                worktree,
                runner=getattr(args, "_command_runner", None),
            )
        return {
            **kernel.report(),
            "ledger": str(store.path),
            "worktree": str(worktree),
            "resumed": True,
            "processed": processed,
        }


def _assemble_verification_bundle(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VerificationCheckpointError(
            "verification inputs must be a JSON object"
        )
    return dict(value)


def _verification_summary(handoff: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "implementation_status",
        "max_claim",
        "release_status",
        "final_disposition",
    )
    if any(
        not isinstance(handoff.get(field), str) or not handoff[field]
        for field in fields
    ):
        raise VerificationCheckpointError(
            "canonical verification reduction is incomplete"
        )
    final_disposition = handoff["final_disposition"]
    stage_pass_eligible = (
        handoff["implementation_status"] == "complete"
        and handoff["release_status"] == "eligible"
        and final_disposition
        in {
            "implementation-complete",
            "deployable-for-test",
            "behavior-verified",
            "production-ready",
        }
    )
    return {
        **{field: handoff[field] for field in fields},
        "stage_pass_eligible": stage_pass_eligible,
    }


_SENSITIVE_CACHE_FIELDS = {
    "access_token",
    "api_key",
    "authorization_header",
    "cookie",
    "password",
    "refresh_token",
    "secret",
    "set_cookie",
    "token",
}


def _cache_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_cache_safe(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TransitionError(f"{path} cache key names must be strings")
            normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
            if normalized in _SENSITIVE_CACHE_FIELDS:
                raise TransitionError(
                    f"{path}.{key} cannot be persisted in evidence cache"
                )
            _assert_cache_safe(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_cache_safe(item, path=f"{path}[{index}]")


def _verification_cache_inputs(
    validated_inputs: Any,
    *,
    candidate: Any,
    ticket_id: str,
    verification_root: Path,
    provider: str,
    provider_mode: str,
) -> dict[str, Any]:
    _assert_cache_safe(validated_inputs)
    if isinstance(validated_inputs, Mapping):
        artifact_hashes = {
            str(key): _cache_digest(value)
            for key, value in sorted(validated_inputs.items())
        }
    else:
        artifact_hashes = {"validated_inputs": _cache_digest(validated_inputs)}
    contract_script = verification_root / "scripts" / "verification_contract.py"
    cache_contract = {
        "artifact_hashes": artifact_hashes,
        "cache_contract_version": 1,
        "candidate_ref": asdict(candidate),
        "command_identity": {
            "bundle_builder_sha256": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
            "validator_reducer_sha256": hashlib.sha256(
                contract_script.read_bytes()
            ).hexdigest(),
        },
        "declared_scope": {
            "boundary": "internal",
            "operation": "verification-checkpoint",
            "ticket_id": ticket_id,
        },
        "environment_identity": {
            "os": os.name,
            "provider": provider,
            "provider_mode": provider_mode,
            "python": sys.implementation.cache_tag,
        },
        "leaf_contract_version": LEAF_RESULT_SCHEMA,
        "limitations": [
            "Only exact key and artifact matches are reusable.",
            "Provider outputs must be sanitized before entering this cache.",
        ],
    }
    return {
        "cache_contract": cache_contract,
        "validated_inputs": validated_inputs,
    }


def _verification_checkpoint_leaf_result(
    status: CheckpointStatus,
    *,
    candidate: Any,
    expected_files: list[str],
    checkpoint_dir: Path,
    complete: bool,
    verification: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not status.phases_complete:
        raise VerificationCheckpointError(
            "verification checkpoint has no durable progress"
        )
    if complete and verification is None:
        raise VerificationCheckpointError(
            "completed verification checkpoint lacks canonical reduction"
        )
    contract = list(LEAF_PHASE_CONTRACTS["verify"])
    progress_phase = status.phases_complete[-1]
    pass_eligible = bool(
        complete
        and verification is not None
        and verification["stage_pass_eligible"]
    )
    evidence_result = (
        "pass" if pass_eligible else ("fail" if complete else "planned")
    )
    findings = (
        []
        if not complete or pass_eligible
        else [
            "verification-reducer:"
            f"{verification['implementation_status']}:"
            f"{verification['release_status']}:"
            f"{verification['final_disposition']}"
        ]
    )
    disposition_limitations = (
        []
        if verification is None
        else [
            "Canonical verification disposition: "
            f"{verification['final_disposition']}; "
            f"maximum claim: {verification['max_claim']}."
        ]
    )
    return {
        "schema": 3,
        "complete": complete,
        "candidate_ref": asdict(candidate),
        "stage": "verify",
        "phase_contract": contract,
        "scope": {
            "files_expected": expected_files,
            "files_inspected": expected_files,
            "files_remaining": [],
        },
        "phases_remaining": contract[contract.index(progress_phase) + 1 :],
        "commands_run": [
            f"verification-checkpoint:{phase}"
            for phase in status.phases_complete
        ],
        "findings": findings,
        "progress_phase": progress_phase,
        "stop_reason": None if complete else "checkpoint-error",
        "quality": {
            "schema": 1,
            "causal_scope": [
                "verification bundle assembly, validation, reduction, and handoff"
            ],
            "evidence": [
                {
                    "id": f"verification-checkpoint:{phase}",
                    "artifact": str(
                        checkpoint_dir
                        / "artifacts"
                        / f"{status.artifact_hashes[phase]}.json"
                    ),
                    "sha256": status.artifact_hashes[phase],
                    "result": evidence_result,
                    "candidate_ref": asdict(candidate),
                }
                for phase in status.phases_complete
            ],
            "limitations": [
                (
                    "Checkpointing does not upgrade evidence class or resolve "
                    "live boundaries."
                ),
                *(
                    []
                    if complete
                    else ["Verification checkpoint execution is incomplete."]
                ),
                *disposition_limitations,
            ],
        },
    }


def _process_events(
    args: argparse.Namespace,
    store: AtomicLedger,
    kernel: Kernel,
    worktree: Path,
    *,
    runner: CommandRunner | None = None,
) -> list[dict[str, object]]:
    processed: list[dict[str, object]] = []
    if args.events:
        event_document = json.loads(Path(args.events).read_text(encoding="utf-8"))
        event_schema = (
            event_document.get("schema")
            if isinstance(event_document, dict)
            else None
        )
        if (
            not isinstance(event_document, dict)
            or type(event_schema) is not int
            or event_schema != 1
            or not isinstance(event_document.get("events"), list)
        ):
            raise TransitionError("event document must have schema 1 and an events list")
        for event in event_document["events"]:
            if not isinstance(event, dict):
                raise TransitionError("each orchestration event must be an object")
            operation = event.get("operation")
            ticket_id = event.get("ticket_id")
            if not isinstance(ticket_id, str):
                raise TransitionError("orchestration event requires ticket_id")
            ticket = kernel.ledger["tickets"].get(ticket_id)
            if ticket is None:
                raise TransitionError(f"unknown ticket {ticket_id!r}")
            if operation == "activate":
                fixed = candidate_ref(worktree, ticket["ticket_digest"])
                kernel.activate(ticket_id, fixed)
                processed.append(
                    {
                        "operation": operation,
                        "ticket_id": ticket_id,
                        "result": "activated",
                        "tree_oid": fixed.tree_oid,
                    }
                )
            elif operation == "leaf-result":
                expected_tree = event.get("expected_tree_oid")
                leaf_result = event.get("leaf_result")
                tool_calls = event.get("tool_calls", 0)
                wall_time = event.get("wall_time", 0)
                if not isinstance(expected_tree, str) or not isinstance(
                    leaf_result, dict
                ):
                    raise TransitionError(
                        "leaf-result event requires expected_tree_oid and leaf_result"
                    )
                if (
                    isinstance(tool_calls, bool)
                    or not isinstance(tool_calls, int)
                    or isinstance(wall_time, bool)
                    or not isinstance(wall_time, int)
                ):
                    raise TransitionError(
                        "leaf-result resource deltas must be exact integers"
                    )
                fixed = candidate_ref(worktree, ticket["ticket_digest"])
                stored = ticket["candidate_ref"]
                if stored != asdict(fixed):
                    kernel.invalidate_for_candidate_drift(ticket_id, fixed)
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "invalidated",
                            "tree_oid": fixed.tree_oid,
                        }
                    )
                    store.save(kernel.ledger)
                    break
                if fixed.tree_oid != expected_tree:
                    raise TransitionError(
                        "leaf-result expected_tree_oid differs from current Git tree"
                    )
                handoff = kernel.record_leaf_result(
                    ticket_id,
                    leaf_result,
                    fixed,
                    expected_files=candidate_files(worktree, fixed),
                    tool_calls=tool_calls,
                    wall_time=wall_time,
                )
                processed.append(
                    {
                        "operation": operation,
                        "ticket_id": ticket_id,
                        "result": (
                            "complete" if handoff["complete"] else "partial"
                        ),
                        "stage": handoff["stage"],
                        "progress_phase": handoff["progress_phase"],
                        "tree_oid": fixed.tree_oid,
                    }
                )
            elif operation == "verification-checkpoint":
                expected_tree = event.get("expected_tree_oid")
                verification_root = event.get("verification_audit_root")
                verification_inputs = event.get("verification_inputs")
                if (
                    not isinstance(expected_tree, str)
                    or not isinstance(verification_root, str)
                    or not isinstance(verification_inputs, dict)
                ):
                    raise TransitionError(
                        "verification-checkpoint requires expected_tree_oid, "
                        "verification_audit_root, and verification_inputs"
                    )
                if ticket.get("stage") != "verify":
                    raise TransitionError(
                        "verification-checkpoint requires the verify stage"
                    )
                fixed = candidate_ref(worktree, ticket["ticket_digest"])
                stored = ticket["candidate_ref"]
                if stored != asdict(fixed):
                    kernel.invalidate_for_candidate_drift(ticket_id, fixed)
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "invalidated",
                            "tree_oid": fixed.tree_oid,
                        }
                    )
                    store.save(kernel.ledger)
                    break
                if fixed.tree_oid != expected_tree:
                    raise TransitionError(
                        "verification-checkpoint expected_tree_oid differs "
                        "from current Git tree"
                    )
                checkpoint_dir = (
                    store.path.parent
                    / f"{store.path.stem}-checkpoints"
                    / ticket_id
                )
                verification_root_path = Path(verification_root)
                cache_inputs = _verification_cache_inputs(
                    verification_inputs,
                    candidate=fixed,
                    ticket_id=ticket_id,
                    verification_root=verification_root_path,
                    provider=str(kernel.ledger.get("provider", "unknown")),
                    provider_mode=str(
                        kernel.ledger.get("provider_mode", "live")
                    ),
                )
                try:
                    validator, reducer = load_verification_adapters(
                        verification_root_path,
                        current_candidate=fixed,
                    )
                    outcome = run_verification_checkpoints(
                        checkpoint_dir,
                        fixed,
                        cache_inputs,
                        builder=lambda value: _assemble_verification_bundle(
                            value["validated_inputs"]
                        ),
                        validator=validator,
                        reducer=reducer,
                    )
                    complete = True
                    cache_hit = outcome.cache_hit
                    cache_miss_reason = outcome.cache_miss_reason
                    commands_avoided = outcome.commands_avoided
                    failure = None
                    verification = _verification_summary(outcome.handoff)
                except CheckpointPhaseFailure as error:
                    complete = False
                    cache_hit = False
                    cache_miss_reason = str(error)
                    commands_avoided = 0
                    failure = str(error)
                    verification = None
                except VerificationCheckpointError as error:
                    raise TransitionError(str(error)) from error
                status = inspect_verification_checkpoints(
                    checkpoint_dir,
                    fixed,
                    cache_inputs,
                )
                cache_limitations = list(
                    cache_inputs["cache_contract"]["limitations"]
                )
                kernel.record_evidence_cache_decision(
                    ticket_id,
                    key_hash=status.input_hash,
                    hit=cache_hit,
                    commands_avoided=commands_avoided,
                    limitations=cache_limitations,
                    miss_reason=cache_miss_reason,
                )
                files = candidate_files(worktree, fixed)
                handoff = kernel.record_leaf_result(
                    ticket_id,
                    _verification_checkpoint_leaf_result(
                        status,
                        candidate=fixed,
                        expected_files=files,
                        checkpoint_dir=checkpoint_dir,
                        complete=complete,
                        verification=verification,
                    ),
                    fixed,
                    expected_files=files,
                )
                processed.append(
                    {
                        "operation": operation,
                        "ticket_id": ticket_id,
                        "result": (
                            "complete" if handoff["complete"] else "partial"
                        ),
                        "progress_phase": handoff["progress_phase"],
                        "phases_complete": list(status.phases_complete),
                        "artifact_hashes": dict(status.artifact_hashes),
                        "cache_hit": cache_hit,
                        "cache_miss_reason": cache_miss_reason,
                        "commands_avoided": commands_avoided,
                        "cache_limitations": cache_limitations,
                        "failure": failure,
                        "verification": verification,
                        "tree_oid": fixed.tree_oid,
                    }
                )
                if not complete:
                    store.save(kernel.ledger)
                    break
            elif operation == "stage":
                stage = event.get("stage")
                result = event.get("result")
                expected_tree = event.get("expected_tree_oid")
                if not all(isinstance(value, str) for value in (stage, result, expected_tree)):
                    raise TransitionError(
                        "stage event requires stage, result, and expected_tree_oid"
                    )
                fixed = candidate_ref(worktree, ticket["ticket_digest"])
                if fixed.tree_oid != expected_tree:
                    raise TransitionError(
                        "stage event expected_tree_oid differs from current Git tree"
                    )
                stored = ticket["candidate_ref"]
                if stored != asdict(fixed):
                    if ticket["stage"] == "implement" and stage == "implement":
                        kernel.adopt_implementation_candidate(ticket_id, fixed)
                    else:
                        kernel.invalidate_for_candidate_drift(ticket_id, fixed)
                        processed.append(
                            {
                                "operation": operation,
                                "ticket_id": ticket_id,
                                "result": "invalidated",
                                "tree_oid": fixed.tree_oid,
                            }
                        )
                        store.save(kernel.ledger)
                        break
                kernel.record_stage(ticket_id, stage, result, fixed)
                processed.append(
                    {
                        "operation": operation,
                        "ticket_id": ticket_id,
                        "stage": stage,
                        "result": result,
                        "tree_oid": fixed.tree_oid,
                    }
                )
            elif operation == "delivery-revalidate":
                if ticket["state"] == "active":
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "revalidation-required",
                            "tree_oid": ticket["candidate_ref"]["tree_oid"],
                        }
                    )
                    continue
                if ticket["state"] != "verified":
                    raise TransitionError(
                        "delivery revalidation requires verified ticket state"
                    )
                fixed = candidate_ref(worktree, ticket["ticket_digest"])
                if ticket["candidate_ref"] == asdict(fixed):
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "unchanged",
                            "tree_oid": fixed.tree_oid,
                        }
                    )
                else:
                    kernel.prepare_delivery_revalidation(ticket_id, fixed)
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "revalidation-required",
                            "tree_oid": fixed.tree_oid,
                        }
                    )
            elif operation == "delivery":
                if "pr_receipt" in event:
                    raise TransitionError(
                        "caller-supplied pr_receipt is forbidden; "
                        "the provider executor owns live readback"
                    )
                render_fields = {
                    "render_request_hash",
                    "expected_head_sha",
                    "rendered_body",
                    "verification_bundle",
                    "verification_audit_root",
                }
                supplied_render_fields = render_fields.intersection(event)
                if supplied_render_fields and supplied_render_fields != render_fields:
                    missing = ", ".join(sorted(render_fields - supplied_render_fields))
                    raise TransitionError(
                        f"delivery render payload is incomplete; missing: {missing}"
                    )
                render_payload = (
                    {field: event[field] for field in render_fields}
                    if supplied_render_fields
                    else None
                )
                provider = detect_provider(
                    "", override=kernel.ledger["provider"]
                )
                executor = ProviderExecutor(
                    provider,
                    cwd=worktree,
                    mode=kernel.ledger.get("provider_mode", "live"),
                    runner=runner,
                )
                try:
                    outcome = DeliveryFinalizer(
                        store, kernel, executor
                    ).apply(ticket_id, render_payload=render_payload)
                except (DeliveryBodyError, GitError, ProviderError) as error:
                    if isinstance(error, DeliveryBodyError):
                        gate_category = "delivery-pr-body"
                        failure_phase = error.phase
                    elif isinstance(error, ProviderError):
                        gate_category = "provider-environment"
                        failure_phase = "provider"
                    else:
                        gate_category = "finalization-environment"
                        failure_phase = "git"
                    kernel.record_delivery_metadata(
                        ticket_id,
                        "result",
                        {
                            "phase": failure_phase,
                            "result": "gated",
                            "gate": gate_category,
                            "reason": str(error),
                        },
                    )
                    existing = [
                        gate
                        for gate in kernel.ledger["gates"].values()
                        if gate["ticket_id"] == ticket_id
                        and gate["category"] == gate_category
                        and gate["state"] == "open"
                    ]
                    if not existing:
                        kernel.open_gate(
                            ticket_id,
                            gate_category,
                            scope="ticket",
                            reason=str(error),
                        )
                        store.save(kernel.ledger)
                    outcome = {
                        "result": "gated",
                        "gate": gate_category,
                        "reason": str(error),
                    }
                processed.append(
                    {"operation": operation, "ticket_id": ticket_id, **outcome}
                )
                if outcome["result"] == "gated":
                    break
            elif operation == "integrate":
                if "provider_receipt" in event or "head_sha" in event:
                    raise TransitionError(
                        "caller-supplied integration state is forbidden; "
                        "the provider executor owns live readback"
                    )
                if kernel.ledger.get("provider_mode", "live") != "live":
                    raise TransitionError(
                        "simulated provider evidence cannot authorize integration"
                    )
                current_pr = ticket.get("pr")
                if not current_pr:
                    raise TransitionError("integration requires a recorded PR")
                provider = detect_provider(
                    "", override=kernel.ledger["provider"]
                )
                executor = ProviderExecutor(
                    provider,
                    cwd=worktree,
                    mode="live",
                    runner=runner,
                )
                receipt = executor.execute(
                    GET_PR_STATE, pr_id=current_pr["pr_id"]
                )
                head_sha = current_pr["head_sha"]
                if (
                    receipt.get("evidence_class") != "live"
                    or receipt.get("provider") != kernel.ledger["provider"]
                    or receipt.get("operation") != GET_PR_STATE
                    or receipt.get("pr_id") != current_pr["pr_id"]
                    or receipt.get("head_sha") != head_sha
                    or receipt.get("state") != "merged"
                ):
                    raise TransitionError(
                        "integration provider receipt contradicts PR state"
                    )
                kernel.record_delivery_metadata(
                    ticket_id, "integration", receipt
                )
                kernel.record_integration(ticket_id, expected_head_sha=head_sha)
                processed.append(
                    {
                        "operation": operation,
                        "ticket_id": ticket_id,
                        "result": "integrated",
                        "head_sha": head_sha,
                    }
                )
            elif operation == "reconcile":
                if len(ticket["blocked_by"]) != 1:
                    raise TransitionError(
                        "only a single-parent stack can be reconciled"
                    )
                parent_id = ticket["blocked_by"][0]
                if kernel.ledger["tickets"][parent_id]["state"] != "integrated":
                    raise TransitionError(
                        "stack reconciliation requires an integrated parent"
                    )
                if "retarget_receipt" in event:
                    raise TransitionError(
                        "caller-supplied retarget_receipt is forbidden; "
                        "the provider executor owns live readback"
                    )
                provider = detect_provider(
                    "", override=kernel.ledger["provider"]
                )
                command_runner = SubprocessCommandRunner()
                prepared = ticket["delivery"].get("reconcile-prepare")
                if prepared is None:
                    if ticket["state"] != "pr-open" or not ticket["pr"]:
                        raise TransitionError(
                            "reconciliation preparation requires a recorded open PR"
                        )
                    parent_branch = event.get("parent_branch")
                    base_branch = event.get("base_branch")
                    expected_remote_sha = event.get("expected_remote_sha")
                    if not all(
                        isinstance(value, str)
                        for value in (
                            parent_branch,
                            base_branch,
                            expected_remote_sha,
                        )
                    ):
                        raise TransitionError(
                            "reconcile preparation requires parent/base/expected SHA"
                        )
                    branch = ticket["pr"]["branch"]
                    old_head = ticket["pr"]["head_sha"]
                    remote = run_git(
                        worktree,
                        "ls-remote",
                        "--heads",
                        "origin",
                        f"refs/heads/{branch}",
                )
                    remote_head = remote.split()[0] if remote else None
                    assert_remote_head(
                        remote_head,
                        {expected_remote_sha},
                        phase="before stack reconciliation",
                    )
                    if old_head != remote_head:
                        raise GitError(
                            "remote branch diverged before stack reconciliation"
                        )
                    current_branch = run_git(
                        worktree,
                        "symbolic-ref",
                        "--quiet",
                        "--short",
                        "HEAD",
                    )
                    if current_branch != branch:
                        switch = command_runner.run(
                            ["git", "switch", branch], cwd=worktree
                        )
                        if switch.returncode:
                            raise GitError(
                                switch.stderr
                                or switch.stdout
                                or "could not switch to stacked branch"
                            )
                    rebase = provider.reconciliation_commands(
                        branch=branch,
                        parent_branch=parent_branch,
                        base_branch=base_branch,
                        expected_remote_sha=expected_remote_sha,
                    )[0]
                    result = command_runner.run(rebase, cwd=worktree)
                    if result.returncode:
                        command_runner.run(
                            ["git", "rebase", "--abort"], cwd=worktree
                        )
                        raise GitError(
                            result.stderr
                            or result.stdout
                            or "stack reconciliation rebase failed"
                        )
                    fixed = candidate_ref(worktree, ticket["ticket_digest"])
                    kernel.prepare_reconciliation(
                        ticket_id,
                        fixed,
                        old_head=old_head,
                        base_branch=base_branch,
                        expected_remote_sha=expected_remote_sha,
                    )
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "revalidation-required",
                            "old_head": old_head,
                            "new_head": fixed.base_sha,
                            "tree_oid": fixed.tree_oid,
                        }
                    )
                else:
                    if ticket["state"] == "active":
                        processed.append(
                            {
                                "operation": operation,
                                "ticket_id": ticket_id,
                                "result": "revalidation-required",
                                "old_head": prepared["old_head"],
                                "new_head": prepared["new_head"],
                                "tree_oid": ticket["candidate_ref"]["tree_oid"],
                            }
                        )
                        store.save(kernel.ledger)
                        break
                    if ticket["state"] != "verified" or not ticket["pr"]:
                        raise TransitionError(
                            "reconciliation publication requires revalidation"
                        )
                    fixed = candidate_ref(worktree, ticket["ticket_digest"])
                    if fixed != type(fixed)(**ticket["candidate_ref"]):
                        kernel.prepare_delivery_revalidation(ticket_id, fixed)
                        processed.append(
                            {
                                "operation": operation,
                                "ticket_id": ticket_id,
                                "result": "revalidation-required",
                                "tree_oid": fixed.tree_oid,
                            }
                        )
                        store.save(kernel.ledger)
                        break
                    if kernel.ledger.get("provider_mode", "live") != "live":
                        gate_id = kernel.open_gate(
                            ticket_id,
                            "provider-retarget",
                            scope="ticket",
                            reason=(
                                "simulated provider evidence cannot authorize "
                                "stack retarget"
                            ),
                        )
                        processed.append(
                            {
                                "operation": operation,
                                "ticket_id": ticket_id,
                                "result": "gated",
                                "gate_id": gate_id,
                            }
                        )
                        store.save(kernel.ledger)
                        break
                    try:
                        provider.negotiate({RETARGET_PR})
                    except ProviderError as error:
                        gate_id = kernel.open_gate(
                            ticket_id,
                            "provider-retarget",
                            scope="ticket",
                            reason=str(error),
                        )
                        processed.append(
                            {
                                "operation": operation,
                                "ticket_id": ticket_id,
                                "result": "gated",
                                "gate_id": gate_id,
                                "reason": str(error),
                            }
                        )
                        store.save(kernel.ledger)
                        break
                    branch = ticket["pr"]["branch"]
                    old_head = prepared["old_head"]
                    new_head = prepared["new_head"]
                    expected_remote_sha = prepared["expected_remote_sha"]
                    base_branch = prepared["base"]
                    remote = run_git(
                        worktree,
                        "ls-remote",
                        "--heads",
                        "origin",
                        f"refs/heads/{branch}",
                )
                    remote_head = remote.split()[0] if remote else None
                    assert_remote_head(
                        remote_head,
                        {expected_remote_sha, new_head},
                        phase="before reconciled publish",
                    )
                    if remote_head != new_head:
                        push = provider.reconciliation_commands(
                            branch=branch,
                            parent_branch="unused-after-revalidation",
                            base_branch=base_branch,
                            expected_remote_sha=expected_remote_sha,
                        )[1]
                        result = command_runner.run(push, cwd=worktree)
                        if result.returncode:
                            raise GitError(
                                result.stderr
                                or result.stdout
                                or "stack reconciliation push failed"
                            )
                    push_receipt = {
                        "operation": "force-with-lease-push",
                        "branch": branch,
                        "expected_old_head": expected_remote_sha,
                        "new_head": new_head,
                    }
                    kernel.record_delivery_metadata(
                        ticket_id, "reconcile-push", push_receipt
                    )
                    store.save(kernel.ledger)
                    executor = ProviderExecutor(
                        provider,
                        cwd=worktree,
                        mode="live",
                        runner=runner,
                    )
                    receipt = executor.execute(
                        RETARGET_PR,
                        pr_id=ticket["pr"]["pr_id"],
                        base=base_branch,
                    )
                    if (
                        receipt.get("evidence_class") != "live"
                        or receipt.get("pr_id") != ticket["pr"]["pr_id"]
                        or receipt.get("base") != base_branch
                        or receipt.get("head_sha") != new_head
                    ):
                        raise TransitionError(
                            "retarget provider readback contradicts reconciliation"
                        )
                    kernel.record_delivery_metadata(
                        ticket_id, "reconcile-retarget", receipt
                    )
                    store.save(kernel.ledger)
                    kernel.complete_reconciliation(
                        ticket_id,
                        expected_old=old_head,
                        new_head=new_head,
                        base_branch=base_branch,
                    )
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "reconciled",
                            "old_head": old_head,
                            "new_head": new_head,
                        }
                    )
            else:
                raise TransitionError(
                    f"unsupported orchestration event operation: {operation!r}"
                )
            store.save(kernel.ledger)
    return processed


def _approve(args: argparse.Namespace) -> dict[str, Any]:
    _, store = _store(args.repo, args.run_id)
    with store.run_locked():
        kernel = Kernel(store.load())
        if args.head_sha or args.ticket:
            if not (args.head_sha and args.ticket):
                raise TransitionError("--ticket and --head-sha must be supplied together")
            provider = detect_provider("", override=kernel.ledger["provider"])
            mode = "runner"
            try:
                provider.negotiate({MERGE_EXPECTED_HEAD})
            except ProviderError:
                if not args.external_merge:
                    raise
                mode = "external"
            kernel.authorize_merge(
                args.ticket,
                actor=args.actor,
                head_sha=args.head_sha,
                evidence=args.evidence,
                mode=mode,
            )
            approved = {
                "kind": "merge",
                "ticket": args.ticket,
                "head_sha": args.head_sha,
            }
        else:
            if not args.gate_id:
                raise TransitionError("gate ID is required for non-merge approval")
            kernel.approve_gate(args.gate_id, actor=args.actor, evidence=args.evidence)
            approved = {"kind": "gate", "gate_id": args.gate_id}
        store.save(kernel.ledger)
        return {**kernel.report(), "approved": approved}


def _abort(args: argparse.Namespace) -> dict[str, Any]:
    _, store = _store(args.repo, args.run_id)
    with store.run_locked():
        kernel = Kernel(store.load())
        kernel.abort(actor=args.actor, reason=args.reason)
        store.save(kernel.ledger)
        return {**kernel.report(), "aborted_by": args.actor}


def _cleanup(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        kernel = Kernel(store.load())
        state = kernel.ledger["run_state"]
        if state in {"failed", "aborted"} and not args.confirm:
            raise TransitionError(f"cleanup of {state} run requires --confirm")
        if state == "waiting" and not args.force:
            raise TransitionError("cleanup of waiting run requires --force")
        if state == "running":
            raise TransitionError("running run cannot be cleaned up")
        worktree = Path(kernel.ledger["worktree"])
        existed = worktree.exists()
        assert_cleanup_safe(worktree, kernel.ledger)
        remove_isolated_worktree(repo, worktree)
        removed = existed and not worktree.exists()
        kernel.record_cleanup(
            worktree=str(worktree),
            worktree_removed=removed,
            resume_abandoned=state == "waiting",
        )
        store.save(kernel.ledger)
        return {
            "run_id": args.run_id,
            "run_state": state,
            "worktree_removed": removed,
            "ledger_preserved": str(store.path),
            "remote_state_deleted": False,
        }


def _atomic_write_text(path: Path, text: str) -> None:
    descriptor, raw_tmp = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_tmp)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _ticket_parse(args: argparse.Namespace) -> dict[str, Any]:
    target = Path(args.ticket).resolve()
    parsed = parse_ticket_markdown(
        target.read_text(encoding="utf-8"),
        source=str(target),
    )
    return {"envelope": parsed.envelope, "body": parsed.body}


def _ticket_emit(args: argparse.Namespace) -> dict[str, Any]:
    envelope_path = Path(args.envelope).resolve()
    body_path = Path(args.body).resolve()
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    body = body_path.read_text(encoding="utf-8")
    markdown = serialize_ticket_markdown(envelope, body)
    output = Path(args.output).resolve() if args.output else None
    if output is not None:
        _atomic_write_text(output, markdown)
    parsed = parse_ticket_markdown(markdown)
    return {
        "envelope": parsed.envelope,
        "body": parsed.body,
        "markdown": None if output is not None else markdown,
        "output": str(output) if output is not None else None,
    }


def _migrate(args: argparse.Namespace) -> dict[str, Any]:
    target = Path(args.target).resolve()
    single_file = target.is_file()
    if single_file:
        folder = (
            target.parent.parent
            if target.parent.name == "done"
            else target.parent
        )
    else:
        folder = target
    discovered = [*folder.glob("*.md"), *(folder / "done").glob("*.md")]
    paths = sorted({*discovered, target}) if single_file else sorted(discovered)
    if not paths:
        raise ContractError(f"no Markdown tickets at {target}")
    changed: list[str] = []
    skipped: list[str] = []
    migrated: dict[Path, str] = {}
    post_migration: dict[Path, str] = {}
    for path in paths:
        display = path.name if single_file else str(path.relative_to(folder))
        report = not single_file or path == target
        text = path.read_text(encoding="utf-8")
        if text.startswith("---\n"):
            parse_ticket_markdown(text, source=str(path))
            if report:
                skipped.append(display)
            post_migration[path] = text
            continue
        match = re.match(r"([A-Za-z0-9]+)", path.stem)
        fallback_id = match.group(1) if match else None
        migrated[path] = migrate_ticket_text(
            text,
            fallback_id=fallback_id,
            source=display,
        )
        post_migration[path] = migrated[path]
        if report:
            changed.append(display)
    validate_ticket_graph(
        folder,
        post_migration,
        completed_paths=(
            path for path in paths if path.parent.name == "done"
        ),
    )
    if args.write:
        for path, text in migrated.items():
            if not single_file or path == target:
                _atomic_write_text(path, text)
    return {
        "target": str(target),
        "changed": changed,
        "skipped": skipped,
        "written": bool(args.write),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = StructuredArgumentParser(prog="ticket-autopilot")
    commands = parser.add_subparsers(
        dest="command", required=True, parser_class=StructuredArgumentParser
    )

    plan = commands.add_parser("plan")
    plan.add_argument("folder")
    plan.add_argument("--repo", default=".")
    plan.add_argument("--provider")
    plan.set_defaults(handler=_plan)

    run = commands.add_parser("run")
    run.add_argument("folder")
    run.add_argument("--repo", default=".")
    run.add_argument("--provider")
    run.add_argument(
        "--provider-mode",
        choices=("live", "simulated"),
        default="live",
    )
    run.add_argument("--run-id")
    run.add_argument("--base", default="HEAD")
    run.add_argument("--max-quality-failures", type=int, default=3)
    run.add_argument("--max-leaf-interactions", type=int, default=10)
    run.add_argument("--max-leaf-tool-calls", type=int)
    run.add_argument("--max-leaf-wall-time", type=int)
    run.set_defaults(handler=_run)

    for name, handler in (("resume", _resume), ("status", _status)):
        command = commands.add_parser(name)
        command.add_argument("run_id")
        command.add_argument("--repo", default=".")
        if name == "resume":
            command.add_argument("--events")
        command.set_defaults(handler=handler)

    approve = commands.add_parser("approve")
    approve.add_argument("run_id")
    approve.add_argument("gate_id", nargs="?")
    approve.add_argument("--repo", default=".")
    approve.add_argument("--actor", required=True)
    approve.add_argument("--evidence", required=True)
    approve.add_argument("--ticket")
    approve.add_argument("--head-sha")
    approve.add_argument("--external-merge", action="store_true")
    approve.set_defaults(handler=_approve)

    abort = commands.add_parser("abort")
    abort.add_argument("run_id")
    abort.add_argument("--repo", default=".")
    abort.add_argument("--actor", required=True)
    abort.add_argument("--reason", required=True)
    abort.set_defaults(handler=_abort)

    cleanup = commands.add_parser("cleanup")
    cleanup.add_argument("run_id")
    cleanup.add_argument("--repo", default=".")
    cleanup.add_argument("--confirm", action="store_true")
    cleanup.add_argument("--force", action="store_true")
    cleanup.set_defaults(handler=_cleanup)

    ticket_parse = commands.add_parser("ticket-parse")
    ticket_parse.add_argument("ticket")
    ticket_parse.set_defaults(handler=_ticket_parse)

    ticket_emit = commands.add_parser("ticket-emit")
    ticket_emit.add_argument("envelope")
    ticket_emit.add_argument("body")
    ticket_emit.add_argument("--output")
    ticket_emit.set_defaults(handler=_ticket_emit)

    migrate = commands.add_parser("migrate")
    migrate.add_argument("target")
    migrate.add_argument("--write", action="store_true")
    migrate.set_defaults(handler=_migrate)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    command_runner: CommandRunner | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args._command_runner = command_runner
    command = args.command
    try:
        data = args.handler(args)
    except (
        ContractError,
        GitError,
        json.JSONDecodeError,
        LedgerError,
        ProviderError,
        TransitionError,
        OSError,
    ) as error:
        _emit(
            _response(
                command,
                False,
                error={"type": type(error).__name__, "message": str(error)},
            )
        )
        return 2
    _emit(_response(command, True, data=data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
