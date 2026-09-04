from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager, nullcontext
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterator, Mapping

from .artifact_audit import audit_artifacts, render_artifact_audit
from .context_budget import (
    ContextBudgetError,
    DEFAULT_WORKFLOW,
    measure_context_budget,
    render_context_budget,
)
from .ticket_contract import (
    ContractError,
    migrate_ticket_text,
    parse_ticket_markdown,
    read_ticket_text,
    serialize_ticket_markdown,
    validate_ticket_graph,
)
from .ticket_inventory import (
    INVENTORY_STATES,
    inventory_tickets,
    render_ticket_inventory,
)
from .final_tree_projection import (
    DEFAULT_PROJECTION_MODE,
    PROJECTION_MODES,
)
from .final_tree_transaction import TRANSACTION_STEP
from .finalizer import (
    CompletionProjectionError,
    DeliveryBodyError,
    DeliveryFinalizer,
    SourceDriftError,
    SourceModeDriftError,
    assert_ticket_source_mode,
    inspect_completion_projection,
)
from .docs_only import (
    DocsOnlyError,
    docs_only_verification_bundle,
    revalidate_docs_only_receipt,
    validate_docs_only_candidate,
)
from .git_ops import (
    CommandResult,
    CommandRunner,
    GitError,
    assert_cleanup_safe,
    assert_remote_head,
    candidate_files,
    candidate_ref,
    common_git_dir,
    create_isolated_worktree,
    origin_url,
    remove_isolated_worktree,
    repository_root,
    run_git,
    SubprocessCommandRunner,
    run_directory,
)
from .kernel import CandidateRef, Kernel, STAGES, TransitionError
from .leaf_protocol import LEAF_PHASE_CONTRACTS, LEAF_RESULT_SCHEMA
from .legacy_recovery import (
    active_legacy_retirement,
    apply_recovery_manifest,
    load_recovery_manifest,
    prepare_recovery_manifest,
    recovery_manifest_status,
    revoke_legacy_retirement,
)
from .ledger import (
    AtomicLedger,
    LedgerError,
    completion_projection_delivery_head_proof,
    completion_projection_terminal_branch,
)
from .equivalent_head import (
    DELIVERY_STEP as EQUIVALENT_HEAD_DELIVERY_STEP,
    EquivalentHeadError,
    build_equivalent_head_receipt,
)
from .repository_bootstrap import (
    BootstrapRequest,
    RepositoryBootstrapError,
    bootstrap_private_github_repository,
)
from .pi_sync import (
    PiSyncError,
    PiSyncRequest,
    PiSyncStateStore,
    integrated_pi_sync_binding,
    synchronize_local_pi,
)
from .repository_merge_authority import (
    AUTHORITY_SCOPE,
    STATE_RELATIVE_PATH,
    RepositoryMergeAuthorityError,
    RepositoryMergeAuthorityStore,
    discover_run_ledgers,
    is_repository_adoption_evidence,
)
from .reconciliation_gates import reconciliation_condition_gate_ids
from .reconciliation_intent import (
    PREPARATION_REFRESH_STEP,
    ReconciliationIntentError,
    build_preparation_refresh,
)
from .repository_reconciliation_authority import (
    AUTHORITY_SCOPE as RECONCILIATION_AUTHORITY_SCOPE,
    STATE_RELATIVE_PATH as RECONCILIATION_STATE_RELATIVE_PATH,
    RepositoryReconciliationAuthorityError,
    RepositoryReconciliationAuthorityStore,
    apply_conflict_proposal,
    load_proposal,
    proposal_path,
)
from .providers import (
    GET_APPROVALS,
    GET_CHECKS_AND_POLICIES,
    GET_PR_STATE,
    MERGE_EXPECTED_HEAD,
    RETARGET_PR,
    MergeAuthorization,
    ProviderExecutor,
    ProviderError,
    REQUIRED_CAPABILITIES,
    RUNNER_DEFECT_ISSUE_CAPABILITIES,
    detect_provider,
)
from .runner_defect_issues import (
    GitHubIssueAdapter,
    IssueOutbox,
    PublicationAuthority,
    RunnerDefectError,
    RunnerDefectEscalator,
    assert_target_repository,
    protected_run_ledger,
)
from .verification_checkpoint import (
    CheckpointPhaseFailure,
    CheckpointStatus,
    VerificationCheckpointError,
    inspect_verification_checkpoints,
    load_verification_adapters,
    run_verification_checkpoints,
)
from .ticket_source import (
    inspect_ticket_source,
    load_ticket_snapshot,
    persist_ticket_snapshot,
)
from .terminal_integration import (
    TerminalIntegrationError,
    build_terminal_integration_proof,
    canonical_digest,
)
from .link_repoint import repoint_moved_file
from .ticket_lifecycle import (
    LifecycleError,
    assert_ticket_source_state,
    transition_ticket_source,
)
from .status_transaction import (
    StatusChangeRequest,
    execute_status_transaction,
)
from .worktree_gc import (
    WorktreeGCError,
    adopt_legacy_owner,
    apply_worktree_gc,
    persist_created_owner,
    plan_worktree_gc,
)
from .wiki_sync import (
    approve_wiki_sync,
    drive_post_integration_sync,
    retry_wiki_delivery,
    wiki_delivery_retry_status,
)
from .zero_to_autopilot import (
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_TOTAL_BYTES,
    ZeroBootstrapRequest,
    ZeroToAutopilotError,
    apply_zero_to_autopilot,
    inspect_zero_to_autopilot,
    prepare_inventory,
)


OUTPUT_SCHEMA = 1


def _configure_utf8_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="strict")


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
    source = inspect_ticket_source(repo, Path(args.folder), base_ref=args.base)
    provider_name, capabilities = _provider(repo, args.provider)
    preview = Kernel.new(
        "plan",
        source.graph,
        provider=provider_name,
        repo=str(repo),
        source_mode=source.source_mode,
        snapshot_manifest_digest=source.manifest_digest,
        snapshot_manifest_path=(
            f"planned://ticket-source/{source.manifest_digest}"
        ),
        source_folder_identity=source.folder_identity,
        merge_policy=args.merge_policy,
        merge_actor=args.merge_actor,
        merge_evidence=args.merge_evidence,
        wiki_sync_merge_policy=args.wiki_sync_merge_policy,
        wiki_sync_merge_actor=args.wiki_sync_merge_actor,
        wiki_sync_merge_evidence=args.wiki_sync_merge_evidence,
        final_tree_projection_mode=args.final_tree_mode,
    ).report()
    return {
        "ticket_folder": str(source.graph.folder),
        "ticket_source_mode": source.source_mode,
        "snapshot_manifest_digest": source.manifest_digest,
        "completion_effects": {
            ticket_id: {"state": "pending"} for ticket_id in source.graph.order
        },
        "source_drift_gates": [],
        "repo": str(repo),
        "provider": capabilities,
        "merge_policy": preview["merge_policy"],
        "merge_grant": preview["merge_grant"],
        "wiki_sync_policy": preview["wiki_sync_policy"],
        "final_tree_projection": preview["final_tree_projection"],
        "ticket_order": list(source.graph.order),
        "ready": preview["ready"],
        "dependency_blocked": preview["dependency_blocked"],
        "human_gates": preview["open_gates"],
        "mutation_planned": False,
    }


def _ticket_list(args: argparse.Namespace) -> dict[str, Any]:
    return inventory_tickets(Path(args.root), state=args.state)


def _artifact_audit(args: argparse.Namespace) -> dict[str, Any]:
    return audit_artifacts(Path(args.root))


def _context_budget(args: argparse.Namespace) -> dict[str, Any]:
    install_root = (
        Path(args.install_root)
        if args.install_root is not None
        else Path.home() / ".agents" / "skills"
    )
    workflow = None if args.no_workflow else args.workflow
    report = measure_context_budget(
        Path(args.root),
        install_root=install_root,
        workflow=workflow,
        ceiling_config=(
            Path(args.ceiling_config) if args.ceiling_config is not None else None
        ),
    )
    if args.check_ceiling and report["ceiling"]["status"] == "exceeded":
        total = report["components"]["composed_total_bytes"]
        ceiling = report["ceiling"]["ceiling_bytes"]
        raise ContextBudgetError(
            f"composed context upper bound {total} exceeds configured ceiling {ceiling}"
        )
    return report


def _bootstrap_private_github(args: argparse.Namespace) -> dict[str, Any]:
    request = BootstrapRequest.normalize(
        repository=args.repo,
        target=args.target,
        visibility=args.visibility,
        base_branch=args.base,
        base_sha=args.base_sha,
        actor=args.actor,
        evidence=args.evidence,
    )
    return bootstrap_private_github_repository(
        request,
        runner=getattr(args, "_command_runner", None),
    )


def _prepare_zero_to_autopilot(args: argparse.Namespace) -> dict[str, Any]:
    return prepare_inventory(
        repository=args.repo,
        target=args.target,
        visibility=args.visibility,
        base_branch=args.base,
        output=args.output,
        excludes=args.exclude,
        max_files=args.max_files,
        max_total_bytes=args.max_total_bytes,
    )


def _zero_to_autopilot(args: argparse.Namespace) -> dict[str, Any]:
    request = ZeroBootstrapRequest.normalize(
        repository=args.repo,
        target=args.target,
        visibility=args.visibility,
        base_branch=args.base,
        inventory_path=args.inventory,
        inventory_sha256=args.inventory_sha256,
        actor=args.actor,
        evidence=args.evidence,
        base_sha=args.base_sha,
    )
    return apply_zero_to_autopilot(
        request,
        runner=getattr(args, "_command_runner", None),
    )


def _zero_to_autopilot_status(args: argparse.Namespace) -> dict[str, Any]:
    return inspect_zero_to_autopilot(args.repo)


def _grant_repository_autonomous_merge(
    args: argparse.Namespace,
) -> dict[str, Any]:
    store = RepositoryMergeAuthorityStore(Path(args.repo))
    grant, replayed = store.grant(
        actor=args.actor,
        evidence=args.evidence,
        scope=args.scope,
    )
    return {
        "repository_authority": store.inspect(),
        "grant": grant,
        "replayed": replayed,
    }


def _revoke_repository_autonomous_merge(
    args: argparse.Namespace,
) -> dict[str, Any]:
    store = RepositoryMergeAuthorityStore(Path(args.repo))
    revocation, replayed = store.revoke(
        actor=args.actor,
        evidence=args.evidence,
    )
    return {
        "repository_authority": store.inspect(),
        "revocation": revocation,
        "replayed": replayed,
    }


def _repository_autonomous_merge_status(
    args: argparse.Namespace,
) -> dict[str, Any]:
    return RepositoryMergeAuthorityStore(Path(args.repo)).inspect()


def _grant_repository_autonomous_reconciliation(
    args: argparse.Namespace,
) -> dict[str, Any]:
    store = RepositoryReconciliationAuthorityStore(Path(args.repo))
    grant, replayed = store.grant(
        actor=args.actor,
        evidence=args.evidence,
        scope=args.scope,
    )
    return {
        "repository_reconciliation_authority": store.inspect(),
        "grant": grant,
        "replayed": replayed,
    }


def _revoke_repository_autonomous_reconciliation(
    args: argparse.Namespace,
) -> dict[str, Any]:
    store = RepositoryReconciliationAuthorityStore(Path(args.repo))
    revocation, replayed = store.revoke(
        actor=args.actor,
        evidence=args.evidence,
    )
    return {
        "repository_reconciliation_authority": store.inspect(),
        "revocation": revocation,
        "replayed": replayed,
    }


def _repository_autonomous_reconciliation_status(
    args: argparse.Namespace,
) -> dict[str, Any]:
    return RepositoryReconciliationAuthorityStore(Path(args.repo)).inspect()


def _migrate_repository_authority(args: argparse.Namespace) -> dict[str, Any]:
    store: RepositoryMergeAuthorityStore | RepositoryReconciliationAuthorityStore
    if args.kind == "merge":
        store = RepositoryMergeAuthorityStore(Path(args.repo))
    else:
        store = RepositoryReconciliationAuthorityStore(Path(args.repo))
    receipt, replayed = store.migrate(
        expected_state_sha256=args.expected_state_sha256,
        actor=args.actor,
        evidence=args.evidence,
    )
    return {
        "kind": args.kind,
        "receipt": receipt,
        "replayed": replayed,
        "repository_authority": store.inspect(),
    }


def _repository_reconciliation_authority_projection(repo: Path) -> dict[str, Any]:
    try:
        return RepositoryReconciliationAuthorityStore(repo).inspect()
    except RepositoryReconciliationAuthorityError as error:
        return {"schema": 1, "status": "unavailable", "reason": str(error)}


def _repository_authority_projection(
    repo: Path, kernel: Kernel | None = None
) -> dict[str, Any]:
    try:
        projection = RepositoryMergeAuthorityStore(repo).inspect()
    except (ProviderError, RepositoryMergeAuthorityError) as error:
        return {"schema": 1, "status": "unavailable", "reason": str(error)}
    if kernel is not None:
        run_grant = kernel.ledger.get("autonomous_merge_grant")
        projection = {
            **projection,
            "run_adoption": bool(
                isinstance(run_grant, dict)
                and is_repository_adoption_evidence(run_grant.get("evidence"))
            ),
        }
    return projection


def _sync_local_pi(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        document = store.load()
        if Path(document.get("repo", "")).resolve() != repo:
            raise LedgerError("ledger repository binding does not match --repo")
        _validate_managed_snapshot(repo, store, document)
        expected_head, ticket_id = integrated_pi_sync_binding(document, args.ticket)
        Kernel(document).preflight_mutation_boundary(ticket_id, "pi:local-sync")
        expected_tree = run_git(repo, "rev-parse", f"{expected_head}^{{tree}}")
        request = PiSyncRequest.normalize(
            source_repository=str(repo),
            expected_head=expected_head,
            expected_tree=expected_tree,
            checkout=args.checkout,
            agents_root=args.agents_root,
            settings_path=args.pi_settings,
            actor=args.actor,
            evidence=args.evidence,
            adopt_existing_owned=args.adopt_existing_owned,
            replace_package_source=args.replace_package_source,
            migrate_owned_source_from=args.migrate_owned_source_from,
            replace_drifted_owned=args.replace_drifted_owned,
        )
        state_path = _pi_sync_state_path(
            store,
            ticket_id,
            expected_head,
            source_repository=request.source_repository,
            migrate_owned_source_from=request.migrate_owned_source_from,
            replace_drifted_owned=request.replace_drifted_owned,
        )
        result = synchronize_local_pi(
            request,
            state_path=state_path,
            runner=getattr(args, "_command_runner", None),
        )
        return {
            **result,
            "run_id": args.run_id,
            "ticket_id": ticket_id,
            "state_path": str(state_path),
        }


def _run(args: argparse.Namespace) -> dict[str, Any]:
    repo = repository_root(Path(args.repo))
    source = inspect_ticket_source(repo, Path(args.folder), base_ref=args.base)
    provider_name, capabilities = _provider(repo, args.provider)
    run_id = args.run_id or uuid.uuid4().hex[:16]
    run_dir = run_directory(repo, run_id)
    ledger_path = run_dir / "ledger.json"
    store = AtomicLedger(ledger_path)
    worktree: Path | None = None
    with store.run_locked():
        if ledger_path.exists():
            raise LedgerError(f"run already exists: {run_id}")
        snapshot_path = run_dir / "ticket-source" / "manifest.json"
        if snapshot_path.exists():
            raise LedgerError(f"run snapshot already exists: {run_id}")
        try:
            snapshot_path = persist_ticket_snapshot(run_dir, source)
            managed_source = load_ticket_snapshot(snapshot_path, repo)
            worktree = create_isolated_worktree(
                repo,
                run_id,
                base_ref=managed_source.manifest["selected_base_sha"],
            )
            base_sha = run_git(worktree, "rev-parse", "HEAD")
            kernel = Kernel.new(
                run_id,
                managed_source.graph,
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
                source_mode=managed_source.source_mode,
                snapshot_manifest_digest=managed_source.manifest_digest,
                snapshot_manifest_path=str(snapshot_path),
                source_folder_identity=managed_source.folder_identity,
                merge_policy=args.merge_policy,
                merge_actor=args.merge_actor,
                merge_evidence=args.merge_evidence,
                wiki_sync_merge_policy=args.wiki_sync_merge_policy,
                wiki_sync_merge_actor=args.wiki_sync_merge_actor,
                wiki_sync_merge_evidence=args.wiki_sync_merge_evidence,
                final_tree_projection_mode=args.final_tree_mode,
            )
            store.save(kernel.ledger)
            ownership = persist_created_owner(repo, ledger_path, kernel.ledger)
        except Exception:
            if worktree is not None and worktree.exists():
                remove_isolated_worktree(repo, worktree)
            raise
    return {
        **kernel.report(),
        "repo": str(repo),
        "worktree": str(worktree),
        "ledger": str(ledger_path),
        "worktree_ownership": ownership,
        "provider": capabilities,
        "provider_mode": args.provider_mode,
    }


def _worktree_owner_adopt(args: argparse.Namespace) -> dict[str, Any]:
    return adopt_legacy_owner(
        Path(args.repo),
        args.run_id,
        expected_ledger_sha256=args.expected_ledger_sha256,
        actor=args.actor,
        evidence=args.evidence,
    )


def _worktree_gc_plan(args: argparse.Namespace) -> dict[str, Any]:
    return plan_worktree_gc(
        Path(args.repo),
        protected_paths=(Path(path) for path in args.protect),
        invocation_path=Path.cwd(),
    )


def _worktree_gc_apply(args: argparse.Namespace) -> dict[str, Any]:
    return apply_worktree_gc(
        Path(args.repo),
        Path(args.plan_path),
        expected_plan_sha256=args.expected_plan_sha256,
        actor=args.actor,
        evidence=args.evidence,
        invocation_path=Path.cwd(),
    )


def _store(repo_value: str, run_id: str) -> tuple[Path, AtomicLedger]:
    repo = repository_root(Path(repo_value))
    store = AtomicLedger(run_directory(repo, run_id) / "ledger.json")
    return repo, store


def _load(repo_value: str, run_id: str) -> tuple[AtomicLedger, Kernel]:
    repo, store = _store(repo_value, run_id)
    document = store.load()
    if Path(document.get("repo", "")).resolve() != repo:
        raise LedgerError("ledger repository binding does not match --repo")
    _validate_managed_snapshot(repo, store, document)
    return store, Kernel(document)


def _validate_managed_snapshot(
    repo: Path, store: AtomicLedger, document: Mapping[str, Any]
) -> None:
    raw_path = document.get("snapshot_manifest_path")
    if not isinstance(raw_path, str):
        raise LedgerError("ledger managed ticket snapshot path is missing")
    path = Path(raw_path).resolve()
    expected = (store.path.parent / "ticket-source" / "manifest.json").resolve()
    if path != expected:
        raise LedgerError("ledger managed ticket snapshot path is outside its run")
    source = load_ticket_snapshot(path, repo)
    if (
        source.manifest_digest != document.get("snapshot_manifest_digest")
        or source.source_mode != document.get("ticket_source_mode")
        or source.folder_identity != document.get("ticket_source_folder_identity")
        or str(source.graph.folder) != document.get("ticket_folder")
        or list(source.graph.order) != document.get("ticket_order")
    ):
        raise LedgerError("ledger binding differs from managed ticket snapshot")
    for ticket_id in source.graph.order:
        ticket = document.get("tickets", {}).get(ticket_id, {})
        snapshot_ticket = source.graph.tickets[ticket_id]
        if (
            ticket.get("ticket_digest") != snapshot_ticket.digest
            or ticket.get("source_relative_path")
            != snapshot_ticket.path.relative_to(source.graph.folder).as_posix()
        ):
            raise LedgerError(
                f"ticket {ticket_id!r} differs from managed ticket snapshot"
            )


def _pi_sync_state_path(
    store: AtomicLedger,
    ticket_id: str,
    head_sha: str,
    *,
    source_repository: Path | None = None,
    migrate_owned_source_from: Path | None = None,
    replace_drifted_owned: tuple[tuple[str, str], ...] = (),
) -> Path:
    filename = f"{head_sha}.json"
    if migrate_owned_source_from is not None:
        if source_repository is None:
            raise PiSyncError("Pi sync migration state requires the current source")
        migration = json.dumps(
            {
                "from": migrate_owned_source_from.as_posix(),
                "to": source_repository.as_posix(),
                "replace_drifted_owned": dict(replace_drifted_owned),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        filename = f"{head_sha}.owned-source-{hashlib.sha256(migration).hexdigest()}.json"
    return store.path.parent / "pi-sync" / ticket_id / filename


def _pi_sync_status(store: AtomicLedger, kernel: Kernel) -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    for ticket_id, ticket in kernel.ledger["tickets"].items():
        lineage = ticket.get("delivery_lineage")
        head_sha = lineage.get("head_sha") if isinstance(lineage, dict) else None
        if ticket.get("state") != "integrated" or not isinstance(head_sha, str):
            continue
        path = _pi_sync_state_path(store, ticket_id, head_sha)
        state = PiSyncStateStore(path).load()
        if state is None:
            statuses[ticket_id] = {
                "status": "not-configured",
                "head_sha": head_sha,
                "state_path": str(path),
                "reload_required": False,
            }
            continue
        receipt = state.get("receipt")
        statuses[ticket_id] = {
            "status": (
                "completed"
                if receipt is not None
                else "failed"
                if state.get("error") is not None
                else "in-progress"
            ),
            "head_sha": head_sha,
            "state_path": str(path),
            "phases": list(state["phases"]),
            "error": copy.deepcopy(state.get("error")),
            "receipt": copy.deepcopy(receipt),
            "reload_required": bool(
                isinstance(receipt, dict) and receipt.get("reload_required")
            ),
        }
    return statuses


def _wiki_delivery_retry_status(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        kernel = Kernel(store.load())
        return wiki_delivery_retry_status(repo, kernel, args.ticket)


def _retry_wiki_delivery(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        kernel = Kernel(store.load())
        kernel.preflight_mutation_boundary(args.ticket, "wiki:retry-delivery")
        return retry_wiki_delivery(
            repo,
            store,
            kernel,
            args.ticket,
            expected_record_sha256=args.expected_record_sha256,
            actor=args.actor,
            evidence=args.evidence,
        )


def _status(args: argparse.Namespace) -> dict[str, Any]:
    store, kernel = _load(args.repo, args.run_id)
    repo = repository_root(Path(args.repo))
    return {
        **kernel.report(),
        "ledger": str(store.path),
        "worktree": kernel.ledger["worktree"],
        "repository_merge_authority": _repository_authority_projection(
            repo, kernel
        ),
        "repository_reconciliation_authority": (
            _repository_reconciliation_authority_projection(repo)
        ),
        "wiki_delivery_retry": {
            ticket_id: wiki_delivery_retry_status(repo, kernel, ticket_id)
            for ticket_id in kernel.ledger["ticket_order"]
        },
        "local_pi_sync": _pi_sync_status(store, kernel),
    }


def _migrate_run_lifecycle(args: argparse.Namespace) -> dict[str, Any]:
    _repo, _binding, manifest = load_recovery_manifest(
        repository=args.repo,
        manifest_path=args.manifest,
        manifest_digest=args.manifest_sha256,
    )
    actions = manifest["actions"]
    if (
        len(actions) != 1
        or actions[0]["run_id"] != args.run_id
        or actions[0]["action"] != "migrate"
    ):
        raise LedgerError(
            "migrate-run-lifecycle requires one exact matching migration manifest"
        )
    result = apply_recovery_manifest(
        repository=args.repo,
        manifest_path=args.manifest,
        manifest_digest=args.manifest_sha256,
        actor=args.actor,
        evidence=args.evidence,
    )
    return {
        "run_id": args.run_id,
        "migrated_schema": 4,
        "application": result,
    }


def _prepare_legacy_recovery(args: argparse.Namespace) -> dict[str, Any]:
    return prepare_recovery_manifest(
        repository=args.repo,
        inventory_path=args.inventory,
        output_path=args.output,
    )


def _apply_legacy_recovery(args: argparse.Namespace) -> dict[str, Any]:
    return apply_recovery_manifest(
        repository=args.repo,
        manifest_path=args.manifest,
        manifest_digest=args.manifest_sha256,
        actor=args.actor,
        evidence=args.evidence,
    )


def _legacy_recovery_status(args: argparse.Namespace) -> dict[str, Any]:
    return recovery_manifest_status(
        repository=args.repo,
        manifest_path=args.manifest,
        manifest_digest=args.manifest_sha256,
    )


def _revoke_legacy_retirement(args: argparse.Namespace) -> dict[str, Any]:
    return revoke_legacy_retirement(
        repository=args.repo,
        run_id=args.run_id,
        actor=args.actor,
        evidence=args.evidence,
        reason=args.reason,
    )


def _compact_run_ledger(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        document = store.load()
        _validate_managed_snapshot(repo, store, document)
        Kernel(document)
        before_bytes = store.path.stat().st_size
        compacted = store.compact_history()
        after_bytes = store.path.stat().st_size
        changed = compacted != document
        kernel = Kernel(compacted)
    return {
        **kernel.report(),
        "ledger": str(store.path),
        "history_compaction": {
            "before_bytes": before_bytes,
            "after_bytes": after_bytes,
            "bytes_saved": before_bytes - after_bytes,
            "changed": changed,
        },
    }


def _change_run_pause(args: argparse.Namespace, *, paused: bool) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        document = store.load()
        _validate_managed_snapshot(repo, store, document)
        kernel = Kernel(document)
        method = kernel.pause_run if paused else kernel.unpause_run
        method(actor=args.actor, reason=args.reason)
        store.save(kernel.ledger)
    return {**kernel.report(), "ledger": str(store.path)}


def _pause(args: argparse.Namespace) -> dict[str, Any]:
    return _change_run_pause(args, paused=True)


def _unpause(args: argparse.Namespace) -> dict[str, Any]:
    return _change_run_pause(args, paused=False)


def _repository_adoptable_merge_id(kernel: Kernel) -> str | None:
    if kernel.ledger.get("merge_policy", "manual") != "manual":
        return None
    first_gated: str | None = None
    for ticket_id in kernel.ledger["ticket_order"]:
        ticket = kernel.ledger["tickets"][ticket_id]
        if ticket.get("merge_authorization") is not None:
            continue
        if not kernel.autonomous_merge_dependencies_ready(ticket_id):
            continue
        if not kernel.autonomous_merge_candidate_ready(ticket_id):
            continue
        if ticket["state"] == "pr-open":
            return ticket_id
        if ticket["state"] != "gated" or first_gated is not None:
            continue
        if any(
            gate.get("ticket_id") == ticket_id
            and gate.get("category") == "provider-merge"
            and gate.get("state") == "open"
            for gate in kernel.ledger["gates"].values()
        ):
            first_gated = ticket_id
    return first_gated


def _adopt_repository_merge_authority(
    store: AtomicLedger, kernel: Kernel
) -> dict[str, Any] | None:
    if _repository_adoptable_merge_id(kernel) is None:
        return None
    repository = Path(kernel.ledger["repo"])
    try:
        authority = RepositoryMergeAuthorityStore(repository)
    except (ProviderError, RepositoryMergeAuthorityError):
        # Existing provider-overridden runs may intentionally use a local/noncanonical
        # origin. That remains optional only while no repository authority state exists;
        # binding drift after a grant must fail closed.
        state_path = common_git_dir(repository) / STATE_RELATIVE_PATH
        if state_path.exists() or state_path.is_symlink():
            raise
        return None
    grant = authority.active_grant()
    if grant is None:
        return None
    if grant["provider"] != kernel.ledger.get("provider"):
        raise RepositoryMergeAuthorityError(
            "repository merge authority provider contradicts the run provider"
        )
    run_grant, replayed = kernel.grant_autonomous_merge(
        actor=grant["actor"],
        evidence=authority.adoption_evidence(grant),
    )
    # Persist the run adoption before provider observation. The repository grant itself
    # remains the revocable source and is rechecked under its lock before mutation.
    store.save(kernel.ledger)
    return {"grant": run_grant, "replayed": replayed}


def _open_reconciliation_gate_ticket_ids(kernel: Kernel) -> list[str]:
    return [
        ticket_id
        for ticket_id in kernel.ledger["ticket_order"]
        if reconciliation_condition_gate_ids(kernel.ledger, ticket_id)
    ]


@contextmanager
def _resolved_reconciliation_gates(
    kernel: Kernel,
    ticket_id: str,
    *,
    actor: str,
    evidence: str,
    approve_before: bool = True,
) -> Iterator[list[str]]:
    snapshot = copy.deepcopy(kernel.ledger)
    gate_ids = reconciliation_condition_gate_ids(kernel.ledger, ticket_id)
    approval_order = sorted(
        gate_ids,
        key=lambda gate_id: (
            kernel.ledger["gates"][gate_id]["resume_state"] != "gated"
        ),
    )

    def approve() -> None:
        for gate_id in approval_order:
            kernel.approve_gate(gate_id, actor=actor, evidence=evidence)

    try:
        if approve_before:
            approve()
        yield gate_ids
        if not approve_before:
            approve()
    except Exception:
        kernel.ledger.clear()
        kernel.ledger.update(snapshot)
        raise


def _recover_authorized_reconciliation_application(
    store: AtomicLedger,
    kernel: Kernel,
    worktree: Path,
    *,
    runner: CommandRunner,
) -> None:
    pending: list[str] = []
    for ticket_id in kernel.ledger["ticket_order"]:
        delivery = kernel.ledger["tickets"][ticket_id].get("delivery", {})
        adoption = delivery.get("repository-reconciliation-adoption")
        application = delivery.get("repository-reconciliation-application")
        if isinstance(adoption, dict) and not (
            isinstance(application, dict)
            and application.get("proposal_sha256")
            == adoption.get("proposal_sha256")
        ):
            pending.append(ticket_id)
    if not pending:
        return
    repository = Path(kernel.ledger["repo"])
    state_path = common_git_dir(repository) / RECONCILIATION_STATE_RELATIVE_PATH
    if not state_path.exists() and not state_path.is_symlink():
        return
    authority = RepositoryReconciliationAuthorityStore(repository)
    grant = authority.active_grant()
    if grant is None:
        return
    for ticket_id in pending:
        ticket = kernel.ledger["tickets"][ticket_id]
        delivery = ticket.get("delivery", {})
        adoption = delivery["repository-reconciliation-adoption"]
        path = proposal_path(store.path.parent, ticket_id)
        if not path.exists():
            continue
        context = adoption.get("context")
        if not isinstance(context, dict) or any(
            not isinstance(key, str) for key in context
        ):
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation adoption context is malformed"
            )
        proposal = load_proposal(path, grant=grant, context=context)
        proposal_sha256 = hashlib.sha256(
            json.dumps(
                proposal,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        if proposal_sha256 != adoption.get("proposal_sha256"):
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation adoption proposal drifted"
            )
        observed_tree = run_git(worktree, "rev-parse", "HEAD^{tree}")
        if observed_tree != proposal["result_tree_oid"]:
            continue
        ancestry = runner.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                proposal["new_target_sha"],
                "HEAD",
            ],
            cwd=worktree,
        )
        if ancestry.returncode:
            raise RepositoryReconciliationAuthorityError(
                "recovered reconciliation head is not based on its exact target"
            )
        with authority.guard_grant(
            grant["grant_id"], grant["grant_digest"]
        ):
            gate_actor = f"repository-reconciliation:{grant['grant_id']}"
            gate_evidence = f"proposal-sha256:{proposal_sha256}"
            with _resolved_reconciliation_gates(
                kernel,
                ticket_id,
                actor=gate_actor,
                evidence=gate_evidence,
                approve_before=False,
            ) as gate_ids:
                kernel.record_delivery_metadata(
                    ticket_id,
                    "repository-reconciliation-application",
                    {
                        "schema": 1,
                        "grant_id": grant["grant_id"],
                        "grant_digest": grant["grant_digest"],
                        "proposal_sha256": proposal_sha256,
                        "patch_sha256": proposal["patch_sha256"],
                        "conflict_paths": list(proposal["conflict_paths"]),
                        "result_head": run_git(worktree, "rev-parse", "HEAD"),
                        "result_tree_oid": observed_tree,
                        "result": "recovered",
                        "actor": grant["actor"],
                        "evidence": grant["evidence"],
                        "proposal_path": str(path),
                        "resolved_gate_ids": gate_ids,
                    },
                )
            store.save(kernel.ledger)


def _authorized_reconciliation_event_path(
    store: AtomicLedger, kernel: Kernel
) -> Path | None:
    eligible_ids = set(_open_reconciliation_gate_ticket_ids(kernel))
    for ticket_id in kernel.ledger["ticket_order"]:
        delivery = kernel.ledger["tickets"][ticket_id].get("delivery", {})
        if (
            (
                isinstance(delivery.get("repository-reconciliation-adoption"), dict)
                or isinstance(
                    delivery.get("repository-reconciliation-application"), dict
                )
            )
            and (
                isinstance(delivery.get("reconcile-refresh-intent"), dict)
                or (
                    isinstance(delivery.get("reconcile-intent"), dict)
                    and not isinstance(delivery.get("reconcile-prepare"), dict)
                )
            )
        ):
            eligible_ids.add(ticket_id)
    if not eligible_ids:
        return None
    try:
        authority = RepositoryReconciliationAuthorityStore(
            Path(kernel.ledger["repo"])
        )
        if authority.active_grant() is None:
            return None
    except RepositoryReconciliationAuthorityError:
        state_path = (
            common_git_dir(Path(kernel.ledger["repo"]))
            / RECONCILIATION_STATE_RELATIVE_PATH
        )
        if state_path.exists() or state_path.is_symlink():
            raise
        return None
    events = []
    for ticket_id in kernel.ledger["ticket_order"]:
        if ticket_id not in eligible_ids:
            continue
        path = proposal_path(store.path.parent, ticket_id)
        if path.exists() or path.is_symlink():
            events.append({"operation": "reconcile", "ticket_id": ticket_id})
    if not events:
        return None
    path = store.path.parent / "artifacts" / "autonomous-reconciliation-events.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.parent.is_symlink():
        raise RepositoryReconciliationAuthorityError(
            "autonomous reconciliation event artifact is unsafe"
        )
    content = json.dumps(
        {"schema": 1, "events": events},
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        descriptor, raw_temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(raw_temporary)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    return path


def _drive_authorized_reconciliation(
    args: argparse.Namespace,
    store: AtomicLedger,
    kernel: Kernel,
    worktree: Path,
    *,
    runner: CommandRunner | None,
) -> list[dict[str, object]]:
    effective_runner = runner or SubprocessCommandRunner()
    _recover_authorized_reconciliation_application(
        store,
        kernel,
        worktree,
        runner=effective_runner,
    )
    event_path = _authorized_reconciliation_event_path(store, kernel)
    if event_path is None:
        return []
    derived_args = copy.copy(args)
    derived_args.events = str(event_path)
    return _process_events(
        derived_args,
        store,
        kernel,
        worktree,
        runner=runner,
    )


def _reconciliation_proposal_candidate_ref(
    ticket: Mapping[str, Any],
) -> Any:
    delivery_candidate = ticket.get("delivery_candidate_ref")
    if delivery_candidate is not None:
        return delivery_candidate
    return ticket["candidate_ref"]


def _reconciliation_conflict_resolver(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    worktree: Path,
    *,
    runner: CommandRunner,
) -> Callable[[Mapping[str, Any]], dict[str, Any] | None]:
    def resolve(context: Mapping[str, Any]) -> dict[str, Any] | None:
        authority = RepositoryReconciliationAuthorityStore(
            Path(kernel.ledger["repo"])
        )
        grant = authority.active_grant()
        path = proposal_path(store.path.parent, ticket_id)
        if grant is None or not path.exists():
            return None
        ticket = kernel.ledger["tickets"][ticket_id]
        proposal_context = {
            "run_id": kernel.ledger["run_id"],
            "ticket_id": ticket_id,
            "ticket_digest": ticket["ticket_digest"],
            "candidate_ref": copy.deepcopy(
                _reconciliation_proposal_candidate_ref(ticket)
            ),
            **context,
        }
        proposal = load_proposal(
            path,
            grant=grant,
            context=proposal_context,
        )
        proposal_sha256 = hashlib.sha256(
            json.dumps(
                proposal,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        adoption = {
            "schema": 1,
            "grant_id": grant["grant_id"],
            "grant_digest": grant["grant_digest"],
            "proposal_sha256": proposal_sha256,
            "proposal_path": str(path),
            "context": dict(proposal_context),
            "result": "adopted",
        }
        existing_adoption = kernel.ledger["tickets"][ticket_id].get(
            "delivery", {}
        ).get("repository-reconciliation-adoption")
        if existing_adoption is not None and existing_adoption != adoption:
            delivery = kernel.ledger["tickets"][ticket_id].get("delivery", {})
            history = delivery.get("repository-reconciliation-history", [])
            if not isinstance(history, list):
                raise RepositoryReconciliationAuthorityError(
                    "repository reconciliation history is malformed"
                )
            archived = {
                "schema": 1,
                "adoption": existing_adoption,
                "application": delivery.get(
                    "repository-reconciliation-application"
                ),
            }
            if not history or history[-1] != archived:
                kernel.record_delivery_metadata(
                    ticket_id,
                    "repository-reconciliation-history",
                    [*history, archived],
                )
                store.save(kernel.ledger)
        kernel.record_delivery_metadata(
            ticket_id,
            "repository-reconciliation-adoption",
            adoption,
        )
        store.save(kernel.ledger)
        with authority.guard_grant(
            grant["grant_id"], grant["grant_digest"]
        ):
            receipt = apply_conflict_proposal(
                worktree,
                proposal,
                runner=runner,
            )
            gate_actor = f"repository-reconciliation:{grant['grant_id']}"
            gate_evidence = f"proposal-sha256:{receipt['proposal_sha256']}"
            with _resolved_reconciliation_gates(
                kernel,
                ticket_id,
                actor=gate_actor,
                evidence=gate_evidence,
                approve_before=False,
            ) as gate_ids:
                receipt = {
                    **receipt,
                    "actor": grant["actor"],
                    "evidence": grant["evidence"],
                    "proposal_path": str(path),
                    "resolved_gate_ids": gate_ids,
                }
                kernel.record_delivery_metadata(
                    ticket_id,
                    "repository-reconciliation-application",
                    receipt,
                )
            store.save(kernel.ledger)
            return receipt

    return resolve


def _drive_pending_merge(
    store: AtomicLedger,
    kernel: Kernel,
    *,
    runner: CommandRunner | None,
) -> dict[str, object] | None:
    pending_merge = kernel.pending_runner_merge_id()
    if pending_merge is not None:
        authorization = kernel.ledger["tickets"][pending_merge][
            "merge_authorization"
        ]
        if authorization["mode"] == "autonomous":
            outcome = _drive_autonomous_merge(
                store, kernel, pending_merge, runner=runner
            )
        else:
            outcome = _drive_runner_merge(
                store,
                kernel,
                pending_merge,
                actor=authorization["actor"],
                head_sha=authorization["head_sha"],
                evidence=authorization["evidence"],
                runner=runner,
                authorization_mode=authorization["mode"],
            )
        return {
            "operation": "merge-critical-path",
            "ticket_id": pending_merge,
            **outcome,
        }
    adoption = _adopt_repository_merge_authority(store, kernel)
    autonomous_ticket = kernel.pending_autonomous_merge_id()
    if autonomous_ticket is None:
        return None
    return {
        "operation": "autonomous-merge",
        "ticket_id": autonomous_ticket,
        "repository_grant_adopted": adoption is not None,
        **_drive_autonomous_merge(
            store, kernel, autonomous_ticket, runner=runner
        ),
    }


def _classify_merge_all_result(outcome: Mapping[str, object]) -> str:
    result = outcome.get("result")
    if result in {"integrated", "gated"}:
        return str(result)
    if result == "queued":
        return "gated"
    return "reconciliation-required"


def _merge_all(args: argparse.Namespace) -> dict[str, Any]:
    repo = repository_root(Path(args.repo))
    authority = RepositoryMergeAuthorityStore(repo)
    with authority.scheduler_locked():
        active_grant = authority.active_grant()
        if active_grant is None:
            raise RepositoryMergeAuthorityError(
                "merge-all requires an active repository-wide autonomous merge grant"
            )
        preflight: list[tuple[Path, AtomicLedger, dict[str, Any]]] = []
        results: list[dict[str, Any]] = []
        seen_run_ids: set[str] = set()
        for ledger_path in discover_run_ledgers(repo):
            store = AtomicLedger(ledger_path)
            try:
                retirement = active_legacy_retirement(repo, ledger_path)
                if retirement is not None:
                    run_id = ledger_path.parent.name
                    if run_id in seen_run_ids:
                        raise RepositoryMergeAuthorityError(
                            f"duplicate run identity discovered: {run_id}"
                        )
                    seen_run_ids.add(run_id)
                    results.append(
                        {
                            "run_id": run_id,
                            "result": "retired-legacy",
                            "reason": retirement["reason"],
                            "ledger_sha256": retirement["ledger_sha256"],
                            "retirement_event_hash": retirement["event_hash"],
                        }
                    )
                    continue
                document = store.load()
                run_id = document.get("run_id")
                if not isinstance(run_id, str) or not run_id:
                    raise LedgerError("run ledger omitted its run ID")
                if run_id in seen_run_ids:
                    raise RepositoryMergeAuthorityError(
                        f"duplicate run identity discovered: {run_id}"
                    )
                seen_run_ids.add(run_id)
                if ledger_path.parent.name != run_id:
                    raise RepositoryMergeAuthorityError(
                        f"run ledger directory contradicts run identity: {run_id}"
                    )
                if Path(document.get("repo", "")).resolve() != repo:
                    results.append(
                        {
                            "run_id": run_id,
                            "result": "skipped",
                            "reason": "run belongs to another repository identity",
                        }
                    )
                    continue
                _validate_managed_snapshot(repo, store, document)
                preflight.append((ledger_path, store, document))
            except RepositoryMergeAuthorityError:
                raise
            except (LedgerError, OSError) as error:
                results.append(
                    {
                        "run_id": ledger_path.parent.name,
                        "result": "failed-before-mutation",
                        "reason": str(error),
                    }
                )
        for _ledger_path, store, _document in preflight:
            run_id = _document["run_id"]
            try:
                with store.run_locked():
                    document = store.load()
                    _validate_managed_snapshot(repo, store, document)
                    kernel = Kernel(document)
                    if kernel.ledger.get("run_state") in {
                        "completed",
                        "failed",
                        "aborted",
                    }:
                        results.append(
                            {
                                "run_id": run_id,
                                "result": (
                                    "already-integrated"
                                    if kernel.ledger.get("run_state") == "completed"
                                    else "skipped"
                                ),
                                "reason": f"terminal run state: {kernel.ledger.get('run_state')}",
                            }
                        )
                        continue
                    if kernel.ledger.get("pause") is not None:
                        results.append(
                            {
                                "run_id": run_id,
                                "result": "skipped",
                                "reason": "run is paused",
                            }
                        )
                        continue
                    reconciliation = _drive_authorized_reconciliation(
                        args,
                        store,
                        kernel,
                        Path(kernel.ledger["worktree"]),
                        runner=getattr(args, "_command_runner", None),
                    )
                    run_grant = kernel.ledger.get("autonomous_merge_grant")
                    if (
                        isinstance(run_grant, dict)
                        and not is_repository_adoption_evidence(
                            run_grant.get("evidence")
                        )
                    ):
                        results.append(
                            {
                                "run_id": run_id,
                                "result": (
                                    "reconciliation-required"
                                    if reconciliation
                                    else "gated"
                                ),
                                "reason": (
                                    "authorized exact reconciliation advanced; distinct run-local merge authority remains unchanged"
                                    if reconciliation
                                    else "run has a distinct run-local autonomous grant"
                                ),
                                "reconciliation": reconciliation,
                            }
                        )
                        continue
                    outcome = _drive_pending_merge(
                        store,
                        kernel,
                        runner=getattr(args, "_command_runner", None),
                    )
                    if outcome is None:
                        results.append(
                            {
                                "run_id": run_id,
                                "result": (
                                    "reconciliation-required"
                                    if reconciliation
                                    else "skipped"
                                ),
                                "reason": (
                                    "authorized exact reconciliation advanced; normal quality or publication work remains"
                                    if reconciliation
                                    else "no merge-ready PR; non-merge work remains unchanged"
                                ),
                                "reconciliation": reconciliation,
                            }
                        )
                    else:
                        results.append(
                            {
                                "run_id": run_id,
                                "result": _classify_merge_all_result(outcome),
                                "ticket_id": outcome.get("ticket_id"),
                                "operation": outcome.get("operation"),
                                "detail": outcome,
                            }
                        )
            except (
                LedgerError,
                ProviderError,
                RepositoryMergeAuthorityError,
                RepositoryReconciliationAuthorityError,
                TransitionError,
                OSError,
            ) as error:
                results.append(
                    {
                        "run_id": run_id,
                        "result": "failed-before-mutation",
                        "reason": str(error),
                    }
                )
        return {
            "repository_authority": authority.inspect(),
            "repository_reconciliation_authority": (
                _repository_reconciliation_authority_projection(repo)
            ),
            "grant_id": active_grant["grant_id"],
            "runs": results,
            "summary": {
                result: sum(item["result"] == result for item in results)
                for result in sorted({item["result"] for item in results})
            },
        }


def _grant_autonomous_merge(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        document = store.load()
        if Path(document.get("repo", "")).resolve() != repo:
            raise LedgerError("ledger repository binding does not match --repo")
        _validate_managed_snapshot(repo, store, document)
        kernel = Kernel(document)
        grant, replayed = kernel.grant_autonomous_merge(
            actor=args.actor,
            evidence=args.evidence,
        )
        # Persist authority before any provider observation or mutation so a crash can
        # resume from the immutable run grant without requesting authority again.
        store.save(kernel.ledger)
        processed: list[dict[str, object]] = []
        if kernel.ledger.get("pause") is None:
            pending = _drive_pending_merge(
                store,
                kernel,
                runner=getattr(args, "_command_runner", None),
            )
            if pending is not None:
                processed.append(pending)
            processed.extend(
                drive_post_integration_sync(
                    repo,
                    store,
                    kernel,
                    runner=getattr(args, "_command_runner", None),
                    boundary_guard=lambda ticket_id, boundary: _mutation_boundary(
                        kernel, ticket_id, boundary
                    ),
                )
            )
        return {
            **kernel.report(),
            "ledger": str(store.path),
            "grant": {
                "kind": "autonomous-merge",
                "replayed": replayed,
                "value": grant,
            },
            "processed": processed,
        }


def _completion_projection_delivery_head_proof(
    kernel: Kernel,
    ticket_id: str,
    worktree: Path,
    command_runner: CommandRunner,
) -> dict[str, Any] | None:
    ticket = kernel.ledger["tickets"][ticket_id]
    current_grant = ticket.get("completion_projection_grant")
    projection_gates = [
        gate
        for gate in kernel.ledger["gates"].values()
        if gate.get("ticket_id") == ticket_id
        and gate.get("category") == "source-mode-drift"
        and gate.get("state") == "open"
    ]
    replay_proof: dict[str, Any] | None = None
    if len(projection_gates) == 1:
        gate = projection_gates[0]
    elif projection_gates:
        return None
    else:
        resolved_gates = [
            gate
            for gate in kernel.ledger["gates"].values()
            if gate.get("ticket_id") == ticket_id
            and gate.get("category") == "source-mode-drift"
            and gate.get("state") == "passed"
            and isinstance(
                gate.get("completion_projection_delivery_head_proof"), dict
            )
            and gate["completion_projection_delivery_head_proof"].get(
                "candidate_ref"
            )
            == ticket.get("candidate_ref")
            and isinstance(current_grant, dict)
            and gate.get("actor") == current_grant.get("actor")
            and gate.get("evidence") == current_grant.get("evidence")
        ]
        if len(resolved_gates) != 1:
            return None
        gate = resolved_gates[0]
        replay_proof = gate["completion_projection_delivery_head_proof"]
    details = gate.get("details")
    if not isinstance(details, dict):
        return None
    if details.get("base_classification") == "ignored":
        return None
    if details.get("base_classification") != "tracked":
        return None

    delivery = ticket.get("delivery")
    branch_receipt = delivery.get("branch") if isinstance(delivery, dict) else None
    if not isinstance(branch_receipt, dict):
        raise CompletionProjectionError(
            "tracked completion projection gate has no prepared delivery branch"
        )
    branch = run_git(worktree, "symbolic-ref", "--short", "HEAD")
    if branch != branch_receipt.get("branch"):
        raise CompletionProjectionError(
            "tracked completion projection HEAD is not the prepared delivery branch"
        )
    head_sha = run_git(worktree, "rev-parse", "HEAD")
    head_tree_oid = run_git(worktree, "rev-parse", "HEAD^{tree}")
    head_parent_sha = run_git(worktree, "rev-parse", "HEAD^")
    head_parent_tree_oid = run_git(
        worktree, "rev-parse", f"{head_parent_sha}^{{tree}}"
    )
    head_commit_message = run_git(worktree, "show", "-s", "--format=%s", "HEAD")
    terminal_target = completion_projection_terminal_branch(
        kernel.ledger, ticket_id
    )
    if terminal_target is None:
        raise CompletionProjectionError(
            "tracked completion projection terminal branch is unavailable"
        )
    _base_ref, terminal_sha, terminal_tree_oid = _fetch_target_base(
        worktree, command_runner, terminal_target
    )
    destination = details.get("source_path")
    if not isinstance(destination, str) or not destination:
        raise CompletionProjectionError(
            "tracked completion projection gate destination is missing"
        )
    if run_git(worktree, "ls-tree", terminal_sha, "--", destination):
        raise CompletionProjectionError(
            "tracked completion projection destination exists in the terminal base"
        )
    ancestry = command_runner.run(
        ["git", "merge-base", "--is-ancestor", head_sha, terminal_sha],
        cwd=worktree,
    )
    if ancestry.returncode == 0:
        raise CompletionProjectionError(
            "tracked completion projection HEAD is already integrated"
        )
    if ancestry.returncode != 1:
        raise CompletionProjectionError(
            ancestry.stderr
            or ancestry.stdout
            or "tracked completion projection ancestry readback failed"
        )
    _assert_target_base_sha(worktree, terminal_target, terminal_sha)
    if (
        run_git(worktree, "symbolic-ref", "--short", "HEAD") != branch
        or run_git(worktree, "rev-parse", "HEAD") != head_sha
        or run_git(worktree, "rev-parse", "HEAD^{tree}") != head_tree_oid
        or run_git(worktree, "rev-parse", "HEAD^") != head_parent_sha
        or run_git(worktree, "show", "-s", "--format=%s", "HEAD")
        != head_commit_message
    ):
        raise CompletionProjectionError(
            "tracked completion projection delivery HEAD changed during proof"
        )
    observation = {
        "branch": branch,
        "head_sha": head_sha,
        "head_tree_oid": head_tree_oid,
        "head_parent_sha": head_parent_sha,
        "head_parent_tree_oid": head_parent_tree_oid,
        "head_commit_message": head_commit_message,
        "terminal_branch": terminal_target,
        "terminal_sha": terminal_sha,
        "terminal_tree_oid": terminal_tree_oid,
    }
    replay_observation = {
        **observation,
        "terminal_destination_state": "absent",
        "head_reachable_from_terminal": False,
    }
    if replay_proof is not None:
        if any(
            replay_proof.get(key) != value
            for key, value in replay_observation.items()
        ):
            raise CompletionProjectionError(
                "tracked completion projection delivery-head replay drifted"
            )
        return copy.deepcopy(replay_proof)
    try:
        return completion_projection_delivery_head_proof(
            kernel.ledger,
            ticket_id,
            gate_id=gate["gate_id"],
            **observation,
        )
    except ValueError as error:
        raise CompletionProjectionError(str(error)) from error


def _grant_completion_projection(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        document = store.load()
        if Path(document.get("repo", "")).resolve() != repo:
            raise LedgerError("ledger repository binding does not match --repo")
        _validate_managed_snapshot(repo, store, document)
        kernel = Kernel(document)
        ticket = kernel.ledger["tickets"].get(args.ticket)
        if not isinstance(ticket, dict) or not isinstance(
            ticket.get("candidate_ref"), dict
        ):
            raise TransitionError(
                "completion projection grant requires a ticket CandidateRef"
            )
        stored = ticket["candidate_ref"]
        if stored.get("candidate_tree_oid") != args.expected_tree:
            raise TransitionError(
                "--expected-tree differs from the ticket CandidateRef"
            )
        worktree = Path(kernel.ledger["worktree"]).resolve()
        fixed = CandidateRef(
            base_tree_oid=run_git(
                worktree, "rev-parse", f"{stored['base_tree_oid']}^{{tree}}"
            ),
            candidate_tree_oid=run_git(worktree, "write-tree"),
            ticket_digest=ticket["ticket_digest"],
            contract_version=stored["contract_version"],
        )
        if asdict(fixed) != stored:
            raise CompletionProjectionError(
                "completion projection candidate differs from the frozen CandidateRef"
            )
        projection = inspect_completion_projection(
            kernel,
            args.ticket,
            expected_tree_oid=args.expected_tree,
            base_ref=stored["base_tree_oid"],
        )
        grant, replayed = kernel.grant_completion_projection(
            args.ticket,
            candidate=fixed,
            destination_relative_path=projection["destination_relative_path"],
            actor=args.actor,
            evidence=args.evidence,
        )
        # Persist authority before resolving a gate. A crash here replays the exact grant,
        # then continues with the still-open matching gate.
        store.save(kernel.ledger)
        active = (
            kernel.ledger["tickets"][args.ticket].get(
                "completion_projection_grant"
            )
            == grant
        )
        delivery_head_proof = (
            _completion_projection_delivery_head_proof(
                kernel,
                args.ticket,
                worktree,
                getattr(args, "_command_runner", None)
                or SubprocessCommandRunner(),
            )
            if active
            else None
        )
        if active:
            confirmed_projection = inspect_completion_projection(
                kernel,
                args.ticket,
                expected_tree_oid=args.expected_tree,
                base_ref=fixed.base_tree_oid,
            )
            if confirmed_projection != projection:
                raise CompletionProjectionError(
                    "completion projection changed during grant recovery"
                )
        resolved_gate = (
            kernel.resolve_completion_projection_gate(
                args.ticket,
                delivery_head_proof=delivery_head_proof,
            )
            if active
            else None
        )
        if resolved_gate is not None:
            store.save(kernel.ledger)
        return {
            **kernel.report(),
            "ledger": str(store.path),
            "grant": {
                "kind": "tracked-completion-projection",
                "replayed": replayed,
                "active": active,
                "resolved_gate": resolved_gate,
                "delivery_head_proof": (
                    {
                        "proof_id": delivery_head_proof["proof_id"],
                        "provenance": delivery_head_proof["provenance"],
                    }
                    if delivery_head_proof is not None
                    else None
                ),
                "value": grant,
            },
            "processed": [],
        }


def _lifecycle_folder(repo: Path, kernel: Kernel) -> tuple[Path, Path | None]:
    source_folder = Path(kernel.ledger["ticket_folder"]).resolve()
    try:
        relative = source_folder.relative_to(repo.resolve())
    except ValueError as error:
        raise LifecycleError("ticket lifecycle folder is outside its repository") from error
    if kernel.ledger["ticket_source_mode"] == "ignored":
        return source_folder, None
    worktree = Path(kernel.ledger["worktree"]).resolve()
    repository_root(worktree)
    return worktree / relative, relative


def _reconciliation_authority_guard(
    kernel: Kernel, ticket_id: str
):
    ticket = kernel.ledger["tickets"][ticket_id]
    application = ticket.get("delivery", {}).get(
        "repository-reconciliation-application"
    )
    if not isinstance(application, dict):
        return nullcontext()
    authority = RepositoryReconciliationAuthorityStore(
        Path(kernel.ledger["repo"])
    )
    return authority.guard_grant(
        str(application.get("grant_id", "")),
        str(application.get("grant_digest", "")),
    )


def _mutation_boundary(
    kernel: Kernel,
    ticket_id: str,
    boundary: str,
    *,
    check_reconciliation_authority: bool = True,
) -> None:
    """Recheck administrative and source truth at the last safe boundary."""

    kernel.preflight_mutation_boundary(ticket_id, boundary)
    repo = Path(kernel.ledger["repo"])
    if not repo.is_dir():
        if str(kernel.ledger.get("snapshot_manifest_path", "")).startswith(
            "memory://"
        ):
            return
        raise LifecycleError("bound repository is missing at mutation boundary")
    folder, _ = _lifecycle_folder(repo, kernel)
    ticket = kernel.ledger["tickets"][ticket_id]
    if check_reconciliation_authority:
        with _reconciliation_authority_guard(kernel, ticket_id):
            pass
    assert_ticket_source_state(
        folder,
        ticket_id,
        ticket["disposition"],
        ticket["ticket_digest"],
    )
    assert_ticket_source_mode(kernel, ticket_id, boundary)


def _guarded_execute(
    executor: ProviderExecutor,
    kernel: Kernel,
    ticket_id: str,
    operation: str,
    **parameters: Any,
) -> dict[str, Any]:
    _mutation_boundary(kernel, ticket_id, f"provider:{operation}")
    delegate = executor.runner

    class GuardedRunner:
        def run(self, command: list[str], *, cwd: Path):
            _mutation_boundary(
                kernel,
                ticket_id,
                f"provider-command:{operation}",
                check_reconciliation_authority=False,
            )
            return delegate.run(command, cwd=cwd)

    executor.runner = GuardedRunner()
    try:
        with _reconciliation_authority_guard(kernel, ticket_id):
            return executor.execute(operation, **parameters)
    finally:
        executor.runner = delegate


def _exact_reopen_replay(
    kernel: Kernel, ticket_id: str, gate_id: str
) -> tuple[dict[str, Any], dict[str, str | None]] | None:
    ticket = kernel.ledger["tickets"][ticket_id]
    receipt = ticket.get("disposition_receipt")
    gate = kernel.ledger["gates"].get(gate_id)
    request = gate.get("lifecycle_request") if isinstance(gate, dict) else None
    if (
        ticket.get("disposition") != "open"
        or ticket.get("state") != "pending"
        or not isinstance(receipt, dict)
        or receipt.get("to_disposition") != "open"
        or receipt.get("authority_gate_id") != gate_id
        or receipt.get("destination_relative_path")
        != ticket.get("current_source_relative_path")
        or not isinstance(gate, dict)
        or gate.get("ticket_id") != ticket_id
        or gate.get("kind") != "reopen"
        or gate.get("category") != "human"
        or gate.get("state") != "passed"
        or gate.get("consumed_by_transition_id") != receipt.get("transition_id")
        or not isinstance(request, dict)
        or request.get("ticket_id") != ticket_id
        or request.get("target_disposition") != "open"
        or request.get("reason") != receipt.get("reason")
        or gate.get("actor") != receipt.get("actor")
        or gate.get("evidence") != receipt.get("authority_ref")
    ):
        return None
    authority = {
        "actor": receipt["actor"],
        "reason": receipt["reason"],
        "authority_ref": receipt["authority_ref"],
        "authority_gate_id": gate_id,
    }
    return copy.deepcopy(receipt), authority


def _change_ticket_disposition(
    args: argparse.Namespace, disposition: str
) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        document = store.load()
        _validate_managed_snapshot(repo, store, document)
        kernel = Kernel(document)
        ticket = kernel.ledger["tickets"].get(args.ticket_id)
        if ticket is None:
            raise TransitionError(f"unknown ticket {args.ticket_id!r}")
        replay = (
            _exact_reopen_replay(kernel, args.ticket_id, args.gate_id)
            if disposition == "open"
            else None
        )
        if replay is not None:
            expected_receipt, authority = replay
            folder, _ = _lifecycle_folder(repo, kernel)
            receipt = transition_ticket_source(
                folder,
                store.path.parent / "ticket-lifecycle",
                args.ticket_id,
                disposition,
                actor=str(authority["actor"]),
                reason=str(authority["reason"]),
                authority_ref=str(authority["authority_ref"]),
                expected_digest=ticket["ticket_digest"],
                authority_gate_id=authority["authority_gate_id"],
            )
            if receipt != expected_receipt:
                raise LifecycleError("reopen replay receipt contradicts the ledger")
            return {
                **kernel.report(),
                "ledger": str(store.path),
                "lifecycle_receipt": receipt,
            }
        if disposition == "open":
            authority = kernel.preflight_disposition_transition(
                args.ticket_id,
                disposition,
                authority_gate_id=args.gate_id,
            )
        else:
            authority = kernel.preflight_disposition_transition(
                args.ticket_id,
                disposition,
                actor=args.actor,
                reason=args.reason,
                authority_ref=args.authority_ref,
            )
        folder, tracked_relative = _lifecycle_folder(repo, kernel)
        receipt = transition_ticket_source(
            folder,
            store.path.parent / "ticket-lifecycle",
            args.ticket_id,
            disposition,
            actor=str(authority["actor"]),
            reason=str(authority["reason"]),
            authority_ref=str(authority["authority_ref"]),
            expected_digest=ticket["ticket_digest"],
            authority_gate_id=authority["authority_gate_id"],
        )
        if tracked_relative is not None:
            worktree = Path(kernel.ledger["worktree"])
            # Same rule as finalize_done: the move and the repoint share one staged state, so
            # whatever commits the one commits the other. A reopen is the same call with the
            # receipt's own paths, which already point the other way.
            tracked_posix = PurePosixPath(tracked_relative.as_posix())
            repointed = repoint_moved_file(
                worktree,
                (tracked_posix / receipt["source_relative_path"]).as_posix(),
                (tracked_posix / receipt["destination_relative_path"]).as_posix(),
            )
            run_git(
                worktree, "add", "-A", "--", str(tracked_relative), *repointed
            )
        kernel.record_disposition_transition(args.ticket_id, receipt)
        store.save(kernel.ledger)
    return {
        **kernel.report(),
        "ledger": str(store.path),
        "lifecycle_receipt": receipt,
    }


def _ticket_hold(args: argparse.Namespace) -> dict[str, Any]:
    return _change_ticket_disposition(args, "on-hold")


def _ticket_cancel(args: argparse.Namespace) -> dict[str, Any]:
    return _change_ticket_disposition(args, "canceled")


def _ticket_reopen(args: argparse.Namespace) -> dict[str, Any]:
    return _change_ticket_disposition(args, "open")


def _status_change_transaction(args: argparse.Namespace) -> dict[str, Any]:
    return execute_status_transaction(
        Path(args.repo),
        StatusChangeRequest(
            ticket_source=Path(args.ticket_source),
            ticket_id=args.ticket_id,
            artifact_id=args.artifact_id,
            ticket_digest=args.ticket_digest,
            from_disposition=args.from_disposition,
            to_disposition=args.to_disposition,
            source_mode=args.source_mode,
            actor=args.actor,
            reason=args.reason,
            authority_ref=args.authority_ref,
            reopen_gate_id=args.reopen_gate_id,
            target_branch=args.base,
        ),
        tracked_delivery=args.source_mode == "tracked",
    )


def _ticket_reopen_request(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        document = store.load()
        _validate_managed_snapshot(repo, store, document)
        kernel = Kernel(document)
        gate_id = kernel.request_reopen(
            args.ticket_id,
            requested_by=args.actor,
            reason=args.reason,
        )
        store.save(kernel.ledger)
    return {**kernel.report(), "ledger": str(store.path), "reopen_gate": gate_id}


def _assert_resume_ticket_source_states(
    lifecycle_folder: Path,
    tickets: Mapping[str, Mapping[str, Any]],
    worktree: Path,
    *,
    command_runner: CommandRunner | None = None,
) -> None:
    """Validate source state without confusing completed sibling branches with drift."""

    runner = command_runner or SubprocessCommandRunner()
    current_head = run_git(worktree, "rev-parse", "HEAD")
    for ticket_id, ticket in tickets.items():
        disposition = str(ticket["disposition"])
        digest = str(ticket["ticket_digest"])
        try:
            assert_ticket_source_state(
                lifecycle_folder, ticket_id, disposition, digest
            )
            continue
        except LifecycleError as original_error:
            lineage = ticket.get("delivery_lineage")
            delivered_head = (
                lineage.get("head_sha")
                if isinstance(lineage, Mapping)
                else None
            )
            if disposition != "completed" or not isinstance(
                delivered_head, str
            ):
                raise
            try:
                assert_ticket_source_state(
                    lifecycle_folder, ticket_id, "open", digest
                )
            except LifecycleError as source_error:
                raise source_error from original_error
            ancestry = runner.run(
                [
                    "git",
                    "merge-base",
                    "--is-ancestor",
                    delivered_head,
                    current_head,
                ],
                cwd=worktree,
            )
            if ancestry.returncode == 1:
                continue
            if ancestry.returncode:
                raise LifecycleError(
                    f"ticket {ticket_id!r} delivery ancestry cannot be proven: "
                    f"{ancestry.stderr or ancestry.stdout or 'git merge-base failed'}"
                ) from original_error
            raise original_error


def _resume(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        document = store.load()
        _validate_managed_snapshot(repo, store, document)
        kernel = Kernel(document)
        worktree = Path(kernel.ledger["worktree"])
        if not worktree.is_dir():
            raise GitError(f"isolated worktree is missing: {worktree}")
        repository_root(worktree)
        lifecycle_folder, _tracked_relative = _lifecycle_folder(repo, kernel)
        _assert_resume_ticket_source_states(
            lifecycle_folder, kernel.ledger["tickets"], worktree
        )
        processed: list[dict[str, object]] = []
        if kernel.ledger.get("pause") is not None:
            return {
                **kernel.report(),
                "ledger": str(store.path),
                "worktree": str(worktree),
                "resumed": False,
                "processed": processed,
            }
        processed.extend(
            _drive_authorized_reconciliation(
                args,
                store,
                kernel,
                worktree,
                runner=getattr(args, "_command_runner", None),
            )
        )
        events = (
            _load_orchestration_events(Path(args.events), kernel)
            if args.events
            else []
        )
        pending_before_events = kernel.pending_runner_merge_id()
        priority_events: list[dict[str, Any]] = []
        remaining_events = events
        pending_before_head = None
        if pending_before_events is not None:
            pending_before_head = kernel.ledger["tickets"][pending_before_events][
                "merge_authorization"
            ]["head_sha"]
            priority_events = []
            remaining_events = []
            for event in events:
                if (
                    event["operation"] == "reconcile"
                    and event["ticket_id"] == pending_before_events
                ):
                    priority_events.append(event)
                else:
                    remaining_events.append(event)
            if priority_events:
                for event in priority_events:
                    _validate_reconciliation_event(kernel, event)
                processed.extend(
                    _process_events(
                        args,
                        store,
                        kernel,
                        worktree,
                        runner=getattr(args, "_command_runner", None),
                        events=priority_events,
                    )
                )
        pending_after_events = kernel.pending_runner_merge_id()
        stale_pending_reconciliation = (
            bool(priority_events)
            and pending_after_events == pending_before_events
            and kernel.ledger["tickets"][pending_after_events][
                "merge_authorization"
            ]["head_sha"]
            == pending_before_head
            and not any(
                item.get("operation") == "reconcile"
                and item.get("ticket_id") == pending_before_events
                and item.get("result") == "reconciled"
                for item in processed
            )
        )
        pending = None
        if not stale_pending_reconciliation:
            pending = _drive_pending_merge(
                store,
                kernel,
                runner=getattr(args, "_command_runner", None),
            )
            if pending is not None:
                processed.append(pending)
        if remaining_events:
            processed.extend(
                _process_events(
                    args,
                    store,
                    kernel,
                    worktree,
                    runner=getattr(args, "_command_runner", None),
                    events=remaining_events,
                )
            )
        merge_blocked = stale_pending_reconciliation or (
            pending is not None
            and pending.get("result") in {"gated", "queued"}
        )
        if not merge_blocked:
            autonomous_ticket = kernel.pending_autonomous_merge_id()
            if autonomous_ticket is not None:
                outcome = _drive_autonomous_merge(
                    store,
                    kernel,
                    autonomous_ticket,
                    runner=getattr(args, "_command_runner", None),
                )
                processed.append(
                    {
                        "operation": "autonomous-merge",
                        "ticket_id": autonomous_ticket,
                        **outcome,
                    }
                )
        processed.extend(
            drive_post_integration_sync(
                repo,
                store,
                kernel,
                runner=getattr(args, "_command_runner", None),
                boundary_guard=lambda ticket_id, boundary: _mutation_boundary(
                    kernel, ticket_id, boundary
                ),
            )
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


def _candidate_ref_for_ticket(
    worktree: Path, ticket: Mapping[str, Any]
) -> CandidateRef:
    stored = ticket.get("candidate_ref")
    base_ref = (
        stored["base_tree_oid"]
        if isinstance(stored, Mapping)
        and isinstance(stored.get("base_tree_oid"), str)
        else "HEAD"
    )
    return candidate_ref(
        worktree,
        str(ticket["ticket_digest"]),
        base_ref=base_ref,
    )


def _reset_stale_pre_provider_preparation(
    kernel: Kernel, ticket_id: str, candidate: CandidateRef
) -> bool:
    ticket = kernel.ledger["tickets"][ticket_id]
    if ticket.get("pr") is not None:
        return False
    return kernel.reset_stale_delivery_preparation(ticket_id, candidate)


class ReconciliationSealRecoveryError(GitError):
    def __init__(
        self,
        *,
        worktree: Path,
        branch: str,
        expected_head: str,
        observed_head: str,
        candidate_tree_oid: str,
    ) -> None:
        resolved_worktree = str(worktree.resolve())
        backup_ref = f"ticket-autopilot-recovery/{observed_head}"
        self.details = {
            "schema": 1,
            "reason": "unexpected-local-head",
            "worktree": resolved_worktree,
            "branch": branch,
            "expected_head": expected_head,
            "observed_head": observed_head,
            "candidate_tree_oid": candidate_tree_oid,
            "recovery": {
                "disposition": "human-repair-required",
                "backup_ref": backup_ref,
                "preserve_command": f"git branch {backup_ref} {observed_head}",
                "restore_command": f"git reset --soft {expected_head}",
                "tree_proof_command": "git write-tree",
                "expected_tree_oid": candidate_tree_oid,
                "resume_instruction": (
                    "approve this exact recovery gate with evidence, then resume "
                    "reconciliation"
                ),
                "intentional_head_instruction": (
                    "if the unexpected head is intentional, abort this run and start "
                    "a new run from that lineage"
                ),
            },
        }
        super().__init__(
            "reconciliation head changed outside the replay-safe sealing step; "
            f"expected {expected_head}, observed {observed_head}, "
            f"worktree {resolved_worktree}; preserve the unexpected head, restore "
            "the prepared head with the verified tree staged, approve the recovery "
            "gate with evidence, and resume"
        )


def _reconciliation_gate(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    *,
    category: str,
    reason: str,
    details: dict[str, Any] | None = None,
) -> dict[str, object]:
    gate_id = kernel.open_gate(
        ticket_id,
        category,
        scope="ticket",
        reason=reason,
        details=details,
    )
    store.save(kernel.ledger)
    outcome: dict[str, object] = {
        "operation": "reconcile",
        "ticket_id": ticket_id,
        "result": "gated",
        "gate_id": gate_id,
        "gate": category,
        "reason": reason,
    }
    if details is not None:
        outcome["details"] = copy.deepcopy(details)
    return outcome


def _reconciliation_error_gate(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    error: Exception,
    *,
    default_category: str,
) -> dict[str, object]:
    if isinstance(error, ReconciliationSealRecoveryError):
        return _reconciliation_gate(
            store,
            kernel,
            ticket_id,
            category="stack-reconciliation-recovery",
            reason=str(error),
            details=error.details,
        )
    if isinstance(error, SourceModeDriftError):
        return _reconciliation_gate(
            store,
            kernel,
            ticket_id,
            category="source-mode-drift",
            reason=str(error),
            details=error.details,
        )
    return _reconciliation_gate(
        store,
        kernel,
        ticket_id,
        category=default_category,
        reason=str(error),
    )


_LEAF_BUDGET_EXHAUSTION_REASONS = frozenset(
    {
        "leaf interaction budget is exhausted",
        "leaf interaction budget is reserved for mandatory stages",
        "leaf tool-call budget is exhausted",
        "leaf wall-time budget is exhausted",
    }
)


def _leaf_budget_exhaustion_gate(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    error: TransitionError,
    *,
    operation: str,
) -> dict[str, object] | None:
    reason = str(error)
    if reason not in _LEAF_BUDGET_EXHAUSTION_REASONS:
        return None
    actionable_reason = (
        f"{reason}. The run budget is immutable; start a new run with larger "
        "leaf limits."
    )
    gate_id = kernel.open_gate(
        ticket_id,
        "resource-budget",
        scope="ticket",
        reason=actionable_reason,
        details={
            "schema": 1,
            "operation": operation,
            "recovery": ["new-run-with-larger-leaf-limits"],
        },
    )
    store.save(kernel.ledger)
    return {
        "operation": operation,
        "ticket_id": ticket_id,
        "result": "gated",
        "gate_id": gate_id,
        "gate": "resource-budget",
        "reason": actionable_reason,
    }


def _record_leaf_result_with_budget_recovery(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    result: dict[str, Any],
    candidate: CandidateRef,
    *,
    expected_files: list[str],
    operation: str,
    tool_calls: int = 0,
    wall_time: int = 0,
) -> tuple[dict[str, Any] | None, bool, dict[str, object] | None]:
    try:
        return (
            kernel.record_leaf_result(
                ticket_id,
                result,
                candidate,
                expected_files=expected_files,
                tool_calls=tool_calls,
                wall_time=wall_time,
            ),
            False,
            None,
        )
    except TransitionError as first_error:
        if str(first_error) not in _LEAF_BUDGET_EXHAUSTION_REASONS:
            raise
        try:
            repaired = kernel.repair_revalidation_leaf_budget(
                ticket_id, candidate
            )
        except TransitionError:
            repaired = False
        if repaired:
            try:
                return (
                    kernel.record_leaf_result(
                        ticket_id,
                        result,
                        candidate,
                        expected_files=expected_files,
                        tool_calls=tool_calls,
                        wall_time=wall_time,
                    ),
                    True,
                    None,
                )
            except TransitionError as retry_error:
                first_error = retry_error
        gated = _leaf_budget_exhaustion_gate(
            store,
            kernel,
            ticket_id,
            first_error,
            operation=operation,
        )
        if gated is None:
            raise first_error
        return None, repaired, gated


def _resolve_or_abort_reconciliation_conflict(
    worktree: Path,
    command_runner: CommandRunner,
    rebase_result: CommandResult,
    *,
    context: Mapping[str, Any],
    conflict_resolver: Callable[[Mapping[str, Any]], dict[str, Any] | None] | None,
    branch: str,
    expected_head: str,
    fallback: str,
    boundary_guard: Callable[[str], None],
    boundary: str,
) -> None:
    resolution = None
    resolution_error: RepositoryReconciliationAuthorityError | None = None
    if conflict_resolver is not None:
        try:
            resolution = conflict_resolver(context)
        except RepositoryReconciliationAuthorityError as error:
            resolution_error = error
    if resolution is not None:
        return
    cleanup = (
        _recover_failed_authorized_proposal
        if resolution_error is not None
        else _abort_failed_reconciliation_rebase
    )
    failure = cleanup(
        worktree,
        command_runner,
        rebase_result,
        branch=branch,
        expected_head=expected_head,
        fallback=fallback,
        boundary_guard=boundary_guard,
        boundary=boundary,
    )
    if resolution_error is not None:
        failure = f"{failure}; autonomous proposal rejected: {resolution_error}"
    raise GitError(failure)


def _derive_reconciliation_candidate(
    worktree: Path,
    provider: Any,
    ticket: Mapping[str, Any],
    *,
    parent_head: str,
    base_sha: str,
    base_tree_oid: str,
    expected_remote_sha: str,
    replay_intent: bool,
    preparation_refresh: Mapping[str, Any] | None = None,
    command_runner: CommandRunner | None = None,
    boundary_guard: Callable[[str], None] | None = None,
    conflict_resolver: Callable[[Mapping[str, Any]], dict[str, Any] | None] | None = None,
) -> tuple[str, str, str, str, CandidateRef]:
    command_runner = command_runner or SubprocessCommandRunner()
    guard = boundary_guard or (lambda _boundary: None)
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
        raise GitError("remote branch diverged before stack reconciliation")
    current_branch = run_git(
        worktree,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
    )
    for state_name in ("rebase-merge", "rebase-apply"):
        state_path = Path(run_git(worktree, "rev-parse", "--git-path", state_name))
        if not state_path.is_absolute():
            state_path = worktree / state_path
        if state_path.exists():
            raise GitError(
                "interrupted stack reconciliation requires explicit recovery"
            )
    if current_branch != branch:
        guard("git:reconcile-switch")
        switch = command_runner.run(["git", "switch", branch], cwd=worktree)
        if switch.returncode:
            raise GitError(
                switch.stderr
                or switch.stdout
                or "could not switch to stacked branch"
            )
    current_head = run_git(worktree, "rev-parse", "HEAD")
    old_local_tree = (
        run_git(worktree, "rev-parse", "HEAD^{tree}")
        if conflict_resolver is not None
        else ""
    )
    if current_head == old_head:
        rebase = provider.reconciliation_commands(
            branch=branch,
            parent_branch=parent_head,
            base_branch=base_sha,
            expected_remote_sha=expected_remote_sha,
        )[0]
        guard("git:reconcile-rebase")
        result = command_runner.run(rebase, cwd=worktree)
        if result.returncode:
            _resolve_or_abort_reconciliation_conflict(
                worktree,
                command_runner,
                result,
                context={
                    "branch": branch,
                    "old_remote_head": remote_head,
                    "old_local_head": old_head,
                    "old_local_tree": old_local_tree,
                    "old_target_sha": parent_head,
                    "old_target_tree": (
                        run_git(
                            worktree, "rev-parse", f"{parent_head}^{{tree}}"
                        )
                        if conflict_resolver is not None
                        else ""
                    ),
                    "new_target_sha": base_sha,
                    "new_target_tree": base_tree_oid,
                },
                conflict_resolver=conflict_resolver,
                branch=branch,
                expected_head=old_head,
                fallback="stack reconciliation rebase failed",
                boundary_guard=guard,
                boundary="git:reconcile-abort",
            )
    elif replay_intent:
        ancestor = command_runner.run(
            ["git", "merge-base", "--is-ancestor", base_sha, "HEAD"],
            cwd=worktree,
        )
        if ancestor.returncode:
            if preparation_refresh is None:
                raise GitError(
                    "reconciliation replay head is not based on the recorded target"
                )
            previous_target = preparation_refresh.get(
                "previous_intent", {}
            ).get("target_base", {})
            previous_sha = previous_target.get("sha")
            previous_tree = previous_target.get("tree_oid")
            if not isinstance(previous_sha, str) or not isinstance(
                previous_tree, str
            ):
                raise GitError(
                    "pre-prepare reconciliation refresh predecessor is malformed"
                )
            previous_ancestor = command_runner.run(
                [
                    "git",
                    "merge-base",
                    "--is-ancestor",
                    previous_sha,
                    "HEAD",
                ],
                cwd=worktree,
            )
            if previous_ancestor.returncode:
                raise GitError(
                    "reconciliation replay head is not based on the prior target"
                )
            rebase = provider.reconciliation_commands(
                branch=branch,
                parent_branch=previous_sha,
                base_branch=base_sha,
                expected_remote_sha=expected_remote_sha,
            )[0]
            guard("git:reconcile-preparation-refresh-rebase")
            result = command_runner.run(rebase, cwd=worktree)
            if result.returncode:
                _resolve_or_abort_reconciliation_conflict(
                    worktree,
                    command_runner,
                    result,
                    context={
                        "branch": branch,
                        "old_remote_head": remote_head,
                        "old_local_head": current_head,
                        "old_local_tree": old_local_tree,
                        "old_target_sha": previous_sha,
                        "old_target_tree": previous_tree,
                        "new_target_sha": base_sha,
                        "new_target_tree": base_tree_oid,
                    },
                    conflict_resolver=conflict_resolver,
                    branch=branch,
                    expected_head=current_head,
                    fallback="pre-prepare target refresh rebase failed",
                    boundary_guard=guard,
                    boundary="git:reconcile-preparation-refresh-abort",
                )
    else:
        raise GitError("local child head changed before reconciliation intent")
    new_head = run_git(worktree, "rev-parse", "HEAD")
    guard("git:reconcile-candidate")
    fixed = candidate_ref(
        worktree,
        ticket["ticket_digest"],
        base_ref=base_sha,
    )
    return old_head, new_head, base_sha, base_tree_oid, fixed


def _derive_reconciliation_refresh_candidate(
    worktree: Path,
    provider: Any,
    ticket: Mapping[str, Any],
    refresh_intent: Mapping[str, Any],
    *,
    command_runner: CommandRunner | None = None,
    boundary_guard: Callable[[str], None] | None = None,
    conflict_resolver: Callable[[Mapping[str, Any]], dict[str, Any] | None] | None = None,
) -> tuple[str, str, str, str, CandidateRef]:
    command_runner = command_runner or SubprocessCommandRunner()
    guard = boundary_guard or (lambda _boundary: None)
    branch = ticket["pr"]["branch"]
    old_head = ticket["pr"]["head_sha"]
    expected_remote_sha = refresh_intent["expected_remote_sha"]
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
        phase="before reconciliation target refresh",
    )
    if old_head != remote_head:
        raise GitError("remote branch diverged before reconciliation target refresh")
    for state_name in ("rebase-merge", "rebase-apply"):
        state_path = Path(run_git(worktree, "rev-parse", "--git-path", state_name))
        if not state_path.is_absolute():
            state_path = worktree / state_path
        if state_path.exists():
            raise GitError(
                "interrupted reconciliation target refresh requires explicit recovery"
            )
    current_branch = run_git(
        worktree,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
    )
    if current_branch != branch:
        guard("git:reconcile-refresh-switch")
        switch = command_runner.run(["git", "switch", branch], cwd=worktree)
        if switch.returncode:
            raise GitError(
                switch.stderr
                or switch.stdout
                or "could not switch to reconciliation refresh branch"
            )
    old_local_head = refresh_intent["old_local_head"]
    old_target_sha = refresh_intent["old_target"]["sha"]
    new_target = refresh_intent["new_target"]
    new_target_sha = new_target["sha"]
    current_head = run_git(worktree, "rev-parse", "HEAD")
    observed_old_local_tree = (
        run_git(worktree, "rev-parse", "HEAD^{tree}")
        if conflict_resolver is not None
        else ""
    )
    if current_head == old_local_head:
        old_ancestor = command_runner.run(
            ["git", "merge-base", "--is-ancestor", old_target_sha, current_head],
            cwd=worktree,
        )
        if old_ancestor.returncode:
            raise GitError(
                "reconciliation refresh head is not based on the old target"
            )
        rebase = provider.reconciliation_commands(
            branch=branch,
            parent_branch=old_target_sha,
            base_branch=new_target_sha,
            expected_remote_sha=expected_remote_sha,
        )[0]
        guard("git:reconcile-refresh-rebase")
        result = command_runner.run(rebase, cwd=worktree)
        if result.returncode:
            _resolve_or_abort_reconciliation_conflict(
                worktree,
                command_runner,
                result,
                context={
                    "branch": branch,
                    "old_remote_head": remote_head,
                    "old_local_head": old_local_head,
                    "old_local_tree": observed_old_local_tree,
                    "old_target_sha": old_target_sha,
                    "old_target_tree": (
                        run_git(
                            worktree, "rev-parse", f"{old_target_sha}^{{tree}}"
                        )
                        if conflict_resolver is not None
                        else ""
                    ),
                    "new_target_sha": new_target_sha,
                    "new_target_tree": new_target["tree_oid"],
                },
                conflict_resolver=conflict_resolver,
                branch=branch,
                expected_head=old_local_head,
                fallback="reconciliation target refresh rebase failed",
                boundary_guard=guard,
                boundary="git:reconcile-refresh-abort",
            )
    else:
        replay_ancestor = command_runner.run(
            ["git", "merge-base", "--is-ancestor", new_target_sha, current_head],
            cwd=worktree,
        )
        if replay_ancestor.returncode:
            raise GitError(
                "reconciliation refresh replay head is not based on its new target"
            )
    new_head = run_git(worktree, "rev-parse", "HEAD")
    guard("git:reconcile-refresh-candidate")
    fixed = candidate_ref(
        worktree,
        ticket["ticket_digest"],
        base_ref=new_target_sha,
    )
    return (
        old_head,
        new_head,
        new_target_sha,
        new_target["tree_oid"],
        fixed,
    )


def _recover_failed_authorized_proposal(
    worktree: Path,
    command_runner: CommandRunner,
    rebase_result: CommandResult,
    *,
    branch: str,
    expected_head: str,
    fallback: str,
    boundary_guard: Callable[[str], None],
    boundary: str,
) -> str:
    active_rebase = False
    for state_name in ("rebase-merge", "rebase-apply"):
        state_path = Path(
            run_git(worktree, "rev-parse", "--git-path", state_name)
        )
        if not state_path.is_absolute():
            state_path = worktree / state_path
        active_rebase = active_rebase or state_path.exists()
    if active_rebase:
        return _abort_failed_reconciliation_rebase(
            worktree,
            command_runner,
            rebase_result,
            branch=branch,
            expected_head=expected_head,
            fallback=fallback,
            boundary_guard=boundary_guard,
            boundary=boundary,
        )
    failure = rebase_result.stderr or rebase_result.stdout or fallback
    restore = command_runner.run(
        ["git", "switch", "--force", branch], cwd=worktree
    )
    if not restore.returncode:
        restore = command_runner.run(
            ["git", "reset", "--hard", expected_head], cwd=worktree
        )
    if restore.returncode:
        raise _reconciliation_cleanup_error(
            worktree,
            failure,
            restore.stderr or restore.stdout or "guarded head restore failed",
        )
    observed_branch = run_git(
        worktree, "symbolic-ref", "--quiet", "--short", "HEAD"
    )
    observed_head = run_git(worktree, "rev-parse", "HEAD")
    if observed_branch != branch or observed_head != expected_head:
        raise _reconciliation_cleanup_error(
            worktree,
            failure,
            f"guarded restore observed branch={observed_branch} head={observed_head}",
        )
    boundary_guard(boundary)
    return failure


def _abort_failed_reconciliation_rebase(
    worktree: Path,
    command_runner: CommandRunner,
    rebase_result: CommandResult,
    *,
    branch: str,
    expected_head: str,
    fallback: str,
    boundary_guard: Callable[[str], None],
    boundary: str,
) -> str:
    """Restore the last guarded Git state after a failed reconciliation rebase."""

    rebase_failure = rebase_result.stderr or rebase_result.stdout or fallback
    abort = command_runner.run(["git", "rebase", "--abort"], cwd=worktree)
    if abort.returncode:
        abort_failure = abort.stderr or abort.stdout or "git rebase --abort failed"
        raise _reconciliation_cleanup_error(
            worktree,
            rebase_failure,
            abort_failure,
        )

    try:
        remaining_states = []
        for state_name in ("rebase-merge", "rebase-apply"):
            state_path = Path(
                run_git(worktree, "rev-parse", "--git-path", state_name)
            )
            if not state_path.is_absolute():
                state_path = worktree / state_path
            if state_path.exists():
                remaining_states.append(state_name)
        observed_branch = run_git(
            worktree,
            "symbolic-ref",
            "--quiet",
            "--short",
            "HEAD",
        )
        observed_head = run_git(worktree, "rev-parse", "HEAD")
    except GitError as error:
        raise _reconciliation_cleanup_error(
            worktree,
            rebase_failure,
            f"cleanup readback failed: {error}",
        ) from error

    cleanup_failures = []
    if remaining_states:
        cleanup_failures.append(
            f"rebase state remains: {', '.join(remaining_states)}"
        )
    if observed_branch != branch:
        cleanup_failures.append(
            f"expected branch {branch!r}, observed {observed_branch!r}"
        )
    if observed_head != expected_head:
        cleanup_failures.append(
            f"expected head {expected_head!r}, observed {observed_head!r}"
        )
    if cleanup_failures:
        raise _reconciliation_cleanup_error(
            worktree,
            rebase_failure,
            "; ".join(cleanup_failures),
        )

    boundary_guard(boundary)
    return rebase_failure


def _reconciliation_cleanup_error(
    worktree: Path,
    rebase_failure: str,
    cleanup_failure: str,
) -> GitError:
    return GitError(
        f"{rebase_failure}; automatic rebase cleanup failed in worktree "
        f"{worktree}: {cleanup_failure}; interrupted rebase requires "
        "explicit recovery"
    )


def _fetch_target_base(
    worktree: Path,
    command_runner: CommandRunner,
    base_branch: str,
    *,
    boundary_guard: Callable[[str], None] | None = None,
) -> tuple[str, str, str]:
    run_git(worktree, "check-ref-format", "--branch", base_branch)
    base_ref = f"refs/remotes/origin/{base_branch}"
    if boundary_guard is not None:
        boundary_guard("git:reconcile-fetch")
    observed = command_runner.run(
        [
            "git",
            "ls-remote",
            "--heads",
            "origin",
            f"refs/heads/{base_branch}",
        ],
        cwd=worktree,
    )
    if observed.returncode:
        raise GitError(
            observed.stderr
            or observed.stdout
            or "target base observation failed"
        )
    base_sha = observed.stdout.split()[0] if observed.stdout.split() else ""
    if not base_sha:
        raise GitError("target base branch is missing")
    present = command_runner.run(
        ["git", "cat-file", "-e", f"{base_sha}^{{commit}}"],
        cwd=worktree,
    )
    if present.returncode:
        fetch = command_runner.run(
            [
                "git",
                "fetch",
                "--no-tags",
                "--no-write-fetch-head",
                "origin",
                base_sha,
            ],
            cwd=worktree,
        )
        if fetch.returncode:
            raise GitError(
                fetch.stderr or fetch.stdout or "target base fetch failed"
            )
    base_tree_oid = run_git(worktree, "rev-parse", f"{base_sha}^{{tree}}")
    return base_ref, base_sha, base_tree_oid


def _assert_target_base_sha(
    worktree: Path,
    base_branch: str,
    expected_sha: str,
) -> None:
    run_git(worktree, "check-ref-format", "--branch", base_branch)
    observed = run_git(
        worktree,
        "ls-remote",
        "--heads",
        "origin",
        f"refs/heads/{base_branch}",
    )
    observed_sha = observed.split()[0] if observed else None
    if observed_sha != expected_sha:
        raise GitError(
            "target base changed after reconciliation intent: "
            f"expected {expected_sha}, observed {observed_sha or 'missing'}"
        )


def _seal_revalidated_reconciliation_head(
    worktree: Path,
    ticket_id: str,
    ticket: Mapping[str, Any],
    candidate: CandidateRef,
    *,
    run_id: str,
    command_runner: CommandRunner,
    boundary_guard: Callable[[], None] | None = None,
) -> str:
    prepared = ticket.get("delivery", {}).get("reconcile-prepare")
    if not isinstance(prepared, dict):
        raise GitError("revalidated reconciliation requires prepared lineage")
    branch = ticket.get("pr", {}).get("branch")
    if not isinstance(branch, str) or not branch:
        raise GitError("revalidated reconciliation requires a recorded branch")
    current_branch = run_git(
        worktree, "symbolic-ref", "--quiet", "--short", "HEAD"
    )
    if current_branch != branch:
        raise GitError("revalidated reconciliation branch changed before sealing")
    old_local_head = prepared.get("new_head")
    target_sha = prepared.get("target_base", {}).get("sha")
    if not all(isinstance(value, str) and value for value in (old_local_head, target_sha)):
        raise GitError("revalidated reconciliation lineage is incomplete")
    expected = asdict(candidate)
    staged_tree = run_git(worktree, "write-tree")
    if staged_tree != candidate.candidate_tree_oid:
        raise GitError(
            "staged reconciliation tree differs from the verified CandidateRef"
        )
    current_head = run_git(worktree, "rev-parse", "HEAD")
    marker = f"Ticket-Autopilot-Reconciliation: {run_id}/{ticket_id}"
    if current_head == old_local_head:
        committed_tree = run_git(worktree, "rev-parse", "HEAD^{tree}")
        if committed_tree != candidate.candidate_tree_oid:
            staged = command_runner.run(
                ["git", "diff", "--cached", "--quiet"], cwd=worktree
            )
            if staged.returncode == 0:
                raise GitError("revalidated reconciliation has no staged changes")
            if staged.returncode != 1:
                raise GitError(
                    staged.stderr or "Git could not inspect reconciliation changes"
                )
            if boundary_guard is not None:
                boundary_guard()
            committed = command_runner.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"ticket {ticket_id}: seal reconciled candidate",
                    "-m",
                    marker,
                ],
                cwd=worktree,
            )
            if committed.returncode:
                raise GitError(
                    committed.stderr
                    or committed.stdout
                    or "could not seal the revalidated reconciliation candidate"
                )
            current_head = run_git(worktree, "rev-parse", "HEAD")
    else:
        try:
            parent = run_git(worktree, "rev-parse", "HEAD^")
            message = run_git(worktree, "log", "-1", "--format=%B")
        except GitError as error:
            raise ReconciliationSealRecoveryError(
                worktree=worktree,
                branch=branch,
                expected_head=old_local_head,
                observed_head=current_head,
                candidate_tree_oid=candidate.candidate_tree_oid,
            ) from error
        if parent != old_local_head or marker not in message:
            raise ReconciliationSealRecoveryError(
                worktree=worktree,
                branch=branch,
                expected_head=old_local_head,
                observed_head=current_head,
                candidate_tree_oid=candidate.candidate_tree_oid,
            )
    committed_tree = run_git(worktree, "rev-parse", "HEAD^{tree}")
    fixed = candidate_ref(
        worktree,
        ticket["ticket_digest"],
        base_ref=target_sha,
    )
    if committed_tree != candidate.candidate_tree_oid or asdict(fixed) != expected:
        raise GitError(
            "sealed reconciliation head differs from the verified CandidateRef"
        )
    return current_head


def _publish_reconciled_branch(
    worktree: Path,
    provider: Any,
    command_runner: CommandRunner,
    *,
    branch: str,
    base_branch: str,
    expected_remote_sha: str,
    new_head: str,
    boundary_guard: Callable[[], None] | None = None,
) -> dict[str, str]:
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
        if boundary_guard is not None:
            boundary_guard()
        result = command_runner.run(push, cwd=worktree)
        if result.returncode:
            raise GitError(
                result.stderr
                or result.stdout
                or "stack reconciliation push failed"
            )
    return {
        "operation": "force-with-lease-push",
        "branch": branch,
        "expected_old_head": expected_remote_sha,
        "new_head": new_head,
    }


_ORCHESTRATION_OPERATIONS = {
    "activate",
    "docs-only-adopt",
    "revalidation-budget-repair",
    "leaf-result",
    "verification-checkpoint",
    "stage",
    "delivery-revalidate",
    "delivery",
    "integrate",
    "reconcile",
}
_RECONCILIATION_RENDER_FIELDS = {
    "render_request_hash",
    "expected_head_sha",
    "rendered_body",
    "verification_bundle",
    "verification_audit_root",
}
_RECONCILIATION_FORBIDDEN_CLAIMS = {
    "candidate_ref",
    "old_semantic_ref",
    "new_semantic_ref",
    "base_tree_oid",
    "candidate_tree_oid",
    "equivalent",
}


def _reconciliation_render_payload(
    event: Mapping[str, Any],
) -> dict[str, Any] | None:
    supplied = _RECONCILIATION_RENDER_FIELDS.intersection(event)
    if supplied and supplied != _RECONCILIATION_RENDER_FIELDS:
        missing = ", ".join(sorted(_RECONCILIATION_RENDER_FIELDS - supplied))
        raise TransitionError(
            f"reconciliation render payload is incomplete; missing: {missing}"
        )
    if _RECONCILIATION_FORBIDDEN_CLAIMS.intersection(event):
        raise TransitionError(
            "caller-supplied semantic equivalence claims are forbidden; "
            "Git state is authoritative"
        )
    if "retarget_receipt" in event:
        raise TransitionError(
            "caller-supplied retarget_receipt is forbidden; "
            "the provider executor owns live readback"
        )
    return (
        {field: event[field] for field in _RECONCILIATION_RENDER_FIELDS}
        if supplied
        else None
    )


def _validate_reconciliation_event(
    kernel: Kernel, event: Mapping[str, Any]
) -> dict[str, Any] | None:
    ticket_id = event["ticket_id"]
    ticket = kernel.ledger["tickets"][ticket_id]
    render_payload = _reconciliation_render_payload(event)
    blockers = ticket["blocked_by"]
    if any(
        kernel.ledger["tickets"][blocker_id]["state"] != "integrated"
        for blocker_id in blockers
    ):
        raise TransitionError(
            "reconciliation requires every blocker to be integrated"
        )
    prepared = ticket["delivery"].get("reconcile-prepare")
    if prepared is None:
        if render_payload is not None:
            raise TransitionError(
                "reconciliation render payload precedes Git-derived preparation"
            )
        if ticket["state"] not in {"pr-open", "gated"} or not ticket["pr"]:
            raise TransitionError(
                "reconciliation preparation requires a recorded open PR"
            )
        if not isinstance(ticket.get("delivery_lineage"), dict):
            raise TransitionError(
                "reconciliation requires recorded delivery lineage"
            )
        if len(blockers) == 1 and not isinstance(
            kernel.ledger["tickets"][blockers[0]].get("delivery_lineage"),
            dict,
        ):
            raise TransitionError(
                "reconciliation requires recorded parent lineage"
            )
    elif (
        ticket["state"] != "active"
        and (ticket["state"] != "verified" or not ticket["pr"])
        and not (
            ticket["state"] == "gated"
            and ticket["pr"]
            and prepared.get("pending_resume_state")
            in {"active", "verified"}
        )
    ):
        raise TransitionError(
            "reconciliation publication requires revalidation"
        )
    return render_payload


def _load_orchestration_events(
    path: Path, kernel: Kernel
) -> list[dict[str, Any]]:
    event_document = json.loads(path.read_text(encoding="utf-8"))
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
    events: list[dict[str, Any]] = []
    for event in event_document["events"]:
        if not isinstance(event, dict):
            raise TransitionError("each orchestration event must be an object")
        operation = event.get("operation")
        if operation not in _ORCHESTRATION_OPERATIONS:
            raise TransitionError(
                f"unsupported orchestration event operation: {operation!r}"
            )
        ticket_id = event.get("ticket_id")
        if not isinstance(ticket_id, str):
            raise TransitionError("orchestration event requires ticket_id")
        if ticket_id not in kernel.ledger["tickets"]:
            raise TransitionError(f"unknown ticket {ticket_id!r}")
        if operation == "reconcile":
            _reconciliation_render_payload(event)
        events.append(event)
    return events


def _project_before_final_quality(
    store: AtomicLedger,
    kernel: Kernel,
    worktree: Path,
    ticket_id: str,
    *,
    runner: CommandRunner | None,
) -> dict[str, Any] | None:
    provider = detect_provider("", override=kernel.ledger["provider"])
    executor = ProviderExecutor(
        provider,
        cwd=worktree,
        mode=kernel.ledger.get("provider_mode", "live"),
        runner=runner,
    )
    return DeliveryFinalizer(
        store,
        kernel,
        executor,
        boundary_guard=lambda guarded_ticket, boundary: _mutation_boundary(
            kernel, guarded_ticket, boundary
        ),
    ).project_before_final_quality(ticket_id)


def _process_events(
    args: argparse.Namespace,
    store: AtomicLedger,
    kernel: Kernel,
    worktree: Path,
    *,
    runner: CommandRunner | None = None,
    events: list[dict[str, Any]] | None = None,
) -> list[dict[str, object]]:
    processed: list[dict[str, object]] = []
    orchestration_events = (
        _load_orchestration_events(Path(args.events), kernel)
        if events is None and args.events
        else events or []
    )
    if orchestration_events:
        for event in orchestration_events:
            operation = event["operation"]
            ticket_id = event["ticket_id"]
            ticket = kernel.ledger["tickets"][ticket_id]
            if operation in _ORCHESTRATION_OPERATIONS:
                kernel.preflight_mutation_boundary(
                    ticket_id, f"orchestration:{operation}"
                )
            transaction = ticket.get("delivery", {}).get(TRANSACTION_STEP)
            projection_recovery_required = (
                isinstance(transaction, dict)
                and (
                    transaction.get("status") != "projected-not-integrated"
                    or ticket.get("candidate_ref")
                    != transaction.get("planned_delivery_candidate_ref")
                    or ticket.get("completion_effect", {}).get("state")
                    != "applied"
                )
            )
            if (
                operation != "activate"
                and ticket["state"] == "active"
                and ticket["stage"] == "review"
                and ticket["validated_stages"] == ["implement", "simplify"]
                and projection_recovery_required
            ):
                try:
                    resumed_projection = _project_before_final_quality(
                        store,
                        kernel,
                        worktree,
                        ticket_id,
                        runner=runner,
                    )
                except CompletionProjectionError as error:
                    processed.append(
                        {
                            "operation": "final-tree-projection-recovery",
                            "ticket_id": ticket_id,
                            "result": "blocked",
                            "reason": str(error),
                        }
                    )
                    store.save(kernel.ledger)
                    break
                if resumed_projection is not None:
                    processed.append(
                        {
                            "operation": "final-tree-projection-recovery",
                            "ticket_id": ticket_id,
                            "result": "resumed",
                            "tree_oid": resumed_projection[
                                "candidate_tree_oid"
                            ],
                        }
                    )
                ticket = kernel.ledger["tickets"][ticket_id]
            if operation == "activate":
                fixed = _candidate_ref_for_ticket(worktree, ticket)
                kernel.activate(ticket_id, fixed)
                processed.append(
                    {
                        "operation": operation,
                        "ticket_id": ticket_id,
                        "result": "activated",
                        "tree_oid": fixed.candidate_tree_oid,
                    }
                )
            elif operation == "docs-only-adopt":
                request = event.get("request")
                verification_root_value = event.get("verification_audit_root")
                if not isinstance(request, dict) or not isinstance(
                    verification_root_value, str
                ) or not verification_root_value:
                    raise TransitionError(
                        "docs-only-adopt requires request and verification_audit_root"
                    )
                evidence_dir = store.path.parent / "evidence"
                existing = ticket.get("docs_only")
                if (
                    ticket.get("state") == "verified"
                    and isinstance(existing, dict)
                    and existing.get("status") == "eligible"
                ):
                    try:
                        revalidate_docs_only_receipt(
                            worktree,
                            ticket,
                            existing,
                            evidence_dir=evidence_dir,
                        )
                    except DocsOnlyError as error:
                        raise TransitionError(str(error)) from error
                    if existing.get("request") != request:
                        raise TransitionError(
                            "docs-only replay request differs from the adopted request"
                        )
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "verified",
                            "replayed": True,
                            "tree_oid": ticket["candidate_ref"][
                                "candidate_tree_oid"
                            ],
                            "leaf_interactions_avoided": existing.get(
                                "leaf_interactions_avoided", 0
                            ),
                        }
                    )
                    continue
                try:
                    validation = validate_docs_only_candidate(
                        worktree,
                        ticket,
                        request,
                        evidence_dir=evidence_dir,
                    )
                except DocsOnlyError as error:
                    kernel.record_docs_only_rejection(
                        ticket_id, reason=str(error)
                    )
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "standard-path-required",
                            "reason": str(error),
                        }
                    )
                    store.save(kernel.ledger)
                    break
                verification_root = Path(verification_root_value)
                bundle = docs_only_verification_bundle(ticket, validation)
                validator, reducer = load_verification_adapters(
                    verification_root,
                    current_candidate=validation.candidate,
                )
                cache_inputs = _verification_cache_inputs(
                    bundle,
                    candidate=validation.candidate,
                    ticket_id=ticket_id,
                    verification_root=verification_root,
                    provider=kernel.ledger["provider"],
                    provider_mode=kernel.ledger.get(
                        "provider_mode", "live"
                    ),
                )
                checkpoint_dir = (
                    store.path.parent / "ledger-checkpoints" / ticket_id
                )
                try:
                    outcome = run_verification_checkpoints(
                        checkpoint_dir,
                        validation.candidate,
                        cache_inputs,
                        builder=lambda value: _assemble_verification_bundle(
                            value["validated_inputs"]
                        ),
                        validator=validator,
                        reducer=reducer,
                    )
                except (
                    CheckpointPhaseFailure,
                    VerificationCheckpointError,
                ) as error:
                    raise TransitionError(str(error)) from error
                status = inspect_verification_checkpoints(
                    checkpoint_dir,
                    validation.candidate,
                    cache_inputs,
                )
                handoff = _verification_checkpoint_leaf_result(
                    status,
                    candidate=validation.candidate,
                    expected_files=list(validation.changed_paths),
                    checkpoint_dir=checkpoint_dir,
                    complete=True,
                    verification=_verification_summary(outcome.handoff),
                )
                receipt = validation.receipt()
                receipt["checkpoint"] = {
                    "input_hash": status.input_hash,
                    "artifact_hashes": dict(status.artifact_hashes),
                    "phases_complete": list(status.phases_complete),
                }
                try:
                    revalidate_docs_only_receipt(
                        worktree,
                        ticket,
                        receipt,
                        evidence_dir=evidence_dir,
                    )
                except DocsOnlyError as error:
                    raise TransitionError(str(error)) from error
                _reset_stale_pre_provider_preparation(
                    kernel, ticket_id, validation.candidate
                )
                adopted = kernel.complete_docs_only_candidate(
                    ticket_id,
                    validation.candidate,
                    receipt=receipt,
                    verification_handoff=handoff,
                )
                processed.append(
                    {
                        "operation": operation,
                        "ticket_id": ticket_id,
                        "result": "verified",
                        "replayed": not adopted,
                        "tree_oid": validation.candidate.candidate_tree_oid,
                        "changed_paths": list(validation.changed_paths),
                        "checks": [dict(item) for item in validation.checks],
                        "verification": _verification_summary(outcome.handoff),
                        "leaf_interactions_avoided": receipt[
                            "leaf_interactions_avoided"
                        ],
                    }
                )
            elif operation == "revalidation-budget-repair":
                expected_tree = event.get("expected_tree_oid")
                if not isinstance(expected_tree, str):
                    raise TransitionError(
                        "revalidation-budget-repair requires expected_tree_oid"
                    )
                fixed = _candidate_ref_for_ticket(worktree, ticket)
                if ticket["candidate_ref"] != asdict(fixed):
                    raise TransitionError(
                        "revalidation-budget-repair requires the persisted "
                        "CandidateRef to match the current Git tree"
                    )
                if fixed.candidate_tree_oid != expected_tree:
                    raise TransitionError(
                        "revalidation-budget-repair expected_tree_oid differs "
                        "from current Git tree"
                    )
                repaired = kernel.repair_revalidation_leaf_budget(
                    ticket_id, fixed
                )
                processed.append(
                    {
                        "operation": operation,
                        "ticket_id": ticket_id,
                        "result": "repaired" if repaired else "not-needed",
                        "tree_oid": fixed.candidate_tree_oid,
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
                fixed = _candidate_ref_for_ticket(worktree, ticket)
                stored = ticket["candidate_ref"]
                if stored != asdict(fixed):
                    _reset_stale_pre_provider_preparation(
                        kernel, ticket_id, fixed
                    )
                    kernel.invalidate_for_candidate_drift(ticket_id, fixed)
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "invalidated",
                            "tree_oid": fixed.candidate_tree_oid,
                        }
                    )
                    store.save(kernel.ledger)
                    break
                if fixed.candidate_tree_oid != expected_tree:
                    raise TransitionError(
                        "leaf-result expected_tree_oid differs from current Git tree"
                    )
                handoff, budget_repaired, gated = (
                    _record_leaf_result_with_budget_recovery(
                        store,
                        kernel,
                        ticket_id,
                        leaf_result,
                        fixed,
                        expected_files=candidate_files(worktree, fixed),
                        tool_calls=tool_calls,
                        wall_time=wall_time,
                        operation=operation,
                    )
                )
                if gated is not None:
                    processed.append(gated)
                    break
                assert handoff is not None
                leaf_outcome: dict[str, object] = {
                    "operation": operation,
                    "ticket_id": ticket_id,
                    "result": (
                        "complete" if handoff["complete"] else "partial"
                    ),
                    "stage": handoff["stage"],
                    "progress_phase": handoff["progress_phase"],
                    "tree_oid": fixed.candidate_tree_oid,
                }
                if budget_repaired:
                    leaf_outcome["budget_repaired"] = True
                processed.append(leaf_outcome)
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
                fixed = _candidate_ref_for_ticket(worktree, ticket)
                stored = ticket["candidate_ref"]
                if stored != asdict(fixed):
                    _reset_stale_pre_provider_preparation(
                        kernel, ticket_id, fixed
                    )
                    kernel.invalidate_for_candidate_drift(ticket_id, fixed)
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "invalidated",
                            "tree_oid": fixed.candidate_tree_oid,
                        }
                    )
                    store.save(kernel.ledger)
                    break
                if fixed.candidate_tree_oid != expected_tree:
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
                handoff, budget_repaired, gated = (
                    _record_leaf_result_with_budget_recovery(
                        store,
                        kernel,
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
                        operation=operation,
                    )
                )
                if gated is not None:
                    processed.append(gated)
                    break
                assert handoff is not None
                checkpoint_outcome: dict[str, object] = {
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
                    "tree_oid": fixed.candidate_tree_oid,
                }
                if budget_repaired:
                    checkpoint_outcome["budget_repaired"] = True
                processed.append(checkpoint_outcome)
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
                fixed = _candidate_ref_for_ticket(worktree, ticket)
                if fixed.candidate_tree_oid != expected_tree:
                    raise TransitionError(
                        "stage event expected_tree_oid differs from current Git tree"
                    )
                stored = ticket["candidate_ref"]
                if stored != asdict(fixed):
                    _reset_stale_pre_provider_preparation(
                        kernel, ticket_id, fixed
                    )
                    if ticket["stage"] == "implement" and stage == "implement":
                        kernel.adopt_implementation_candidate(ticket_id, fixed)
                    else:
                        kernel.invalidate_for_candidate_drift(ticket_id, fixed)
                        processed.append(
                            {
                                "operation": operation,
                                "ticket_id": ticket_id,
                                "result": "invalidated",
                                "tree_oid": fixed.candidate_tree_oid,
                            }
                        )
                        store.save(kernel.ledger)
                        break
                kernel.record_stage(ticket_id, stage, result, fixed)
                stage_outcome: dict[str, object] = {
                    "operation": operation,
                    "ticket_id": ticket_id,
                    "stage": stage,
                    "result": result,
                    "tree_oid": fixed.candidate_tree_oid,
                }
                processed.append(stage_outcome)
                if stage == "simplify" and result == "pass":
                    try:
                        projected = _project_before_final_quality(
                            store,
                            kernel,
                            worktree,
                            ticket_id,
                            runner=runner,
                        )
                    except CompletionProjectionError as error:
                        stage_outcome["projection"] = "recovery-required"
                        stage_outcome["reason"] = str(error)
                        store.save(kernel.ledger)
                        break
                    if projected is not None:
                        stage_outcome["projection"] = "projected-not-integrated"
                        stage_outcome["projected_tree_oid"] = projected[
                            "candidate_tree_oid"
                        ]
                if stage == "finalize" and result == "pass":
                    if kernel.record_final_tree_projection_quality_complete(
                        ticket_id
                    ):
                        store.save(kernel.ledger)
                        stage_outcome["projection_quality"] = "quality-complete"
            elif operation == "delivery-revalidate":
                if ticket["state"] == "active":
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "revalidation-required",
                            "tree_oid": ticket["candidate_ref"]["candidate_tree_oid"],
                        }
                    )
                    continue
                if ticket["state"] != "verified":
                    raise TransitionError(
                        "delivery revalidation requires verified ticket state"
                    )
                docs_only = ticket.get("docs_only")
                if (
                    isinstance(docs_only, dict)
                    and docs_only.get("status") == "eligible"
                ):
                    try:
                        validation = revalidate_docs_only_receipt(
                            worktree,
                            ticket,
                            docs_only,
                            evidence_dir=store.path.parent / "evidence",
                        )
                    except DocsOnlyError as error:
                        raise TransitionError(str(error)) from error
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "unchanged",
                            "tree_oid": validation.candidate.candidate_tree_oid,
                        }
                    )
                    continue
                fixed = _candidate_ref_for_ticket(worktree, ticket)
                if ticket["candidate_ref"] == asdict(fixed):
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "unchanged",
                            "tree_oid": fixed.candidate_tree_oid,
                        }
                    )
                else:
                    _reset_stale_pre_provider_preparation(
                        kernel, ticket_id, fixed
                    )
                    kernel.prepare_delivery_revalidation(ticket_id, fixed)
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": "revalidation-required",
                            "tree_oid": fixed.candidate_tree_oid,
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
                        store,
                        kernel,
                        executor,
                        boundary_guard=lambda guarded_ticket, boundary: _mutation_boundary(
                            kernel, guarded_ticket, boundary
                        ),
                    ).apply(ticket_id, render_payload=render_payload)
                except (DeliveryBodyError, GitError, ProviderError) as error:
                    if isinstance(error, DeliveryBodyError):
                        gate_category = "delivery-pr-body"
                        failure_phase = error.phase
                    elif isinstance(error, SourceModeDriftError):
                        gate_category = "source-mode-drift"
                        failure_phase = "source-mode-revalidation"
                    elif isinstance(error, SourceDriftError):
                        gate_category = "source-drift"
                        failure_phase = "source-finalization"
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
                            details=(
                                error.details
                                if isinstance(error, SourceModeDriftError)
                                else None
                            ),
                        )
                        store.save(kernel.ledger)
                    outcome = {
                        "result": "gated",
                        "gate": gate_category,
                        "reason": str(error),
                    }
                    if isinstance(error, SourceModeDriftError):
                        outcome["details"] = copy.deepcopy(error.details)
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
                receipt = _guarded_execute(
                    executor, kernel, ticket_id, GET_PR_STATE,
                    pr_id=current_pr["pr_id"]
                )
                _validate_merge_observation(
                    receipt,
                    provider=provider.name,
                    pr_id=current_pr["pr_id"],
                )
                head_sha = current_pr["head_sha"]
                if receipt.get("state") != "merged":
                    raise TransitionError(
                        "integration provider receipt contradicts PR state"
                    )
                equivalent_receipt = ticket.get("delivery", {}).get(
                    EQUIVALENT_HEAD_DELIVERY_STEP
                )
                equivalent_replayed = equivalent_receipt is not None
                if receipt.get("head_sha") != head_sha:
                    proposed_equivalence = _equivalent_head_receipt(
                        kernel, ticket_id, receipt
                    )
                    equivalent_receipt, equivalent_replayed = (
                        kernel.adopt_equivalent_external_head(
                            ticket_id, proposed_equivalence
                        )
                    )
                    store.save(kernel.ledger)
                    readback = store.load()
                    if (
                        readback["tickets"][ticket_id]
                        .get("delivery", {})
                        .get(EQUIVALENT_HEAD_DELIVERY_STEP)
                        != equivalent_receipt
                    ):
                        raise TransitionError(
                            "equivalent-head adoption readback is contradictory"
                        )
                    kernel.ledger = Kernel(readback).ledger
                    ticket = kernel.ledger["tickets"][ticket_id]
                    current_pr = ticket["pr"]
                    head_sha = current_pr["head_sha"]
                    readback_receipt = _guarded_execute(
                        executor,
                        kernel,
                        ticket_id,
                        GET_PR_STATE,
                        pr_id=current_pr["pr_id"],
                    )
                    _validate_merge_observation(
                        readback_receipt,
                        provider=provider.name,
                        pr_id=current_pr["pr_id"],
                    )
                    binding_fields = (
                        "provider",
                        "pr_id",
                        "branch",
                        "base",
                        "head_sha",
                        "merge_commit_sha",
                        "state",
                    )
                    if any(
                        readback_receipt.get(field) != receipt.get(field)
                        for field in binding_fields
                    ):
                        raise TransitionError(
                            "equivalent-head provider readback changed after adoption"
                        )
                    receipt = readback_receipt
                authorization = ticket.get("merge_authorization")
                runner_initiated = (
                    isinstance(authorization, dict)
                    and authorization.get("head_sha") == head_sha
                    and authorization.get("mode") in {"runner", "autonomous"}
                )
                provenance = (
                    "runner-merge" if runner_initiated else "external-readback"
                )
                terminal_proof = _terminal_integration_proof(
                    kernel,
                    ticket_id,
                    receipt,
                    provenance=provenance,
                )
                for gate_id in _merge_gate_ids(kernel, ticket_id):
                    kernel.approve_gate(
                        gate_id,
                        actor=f"provider:{provider.name}",
                        evidence=(
                            "terminal-integration-live-readback:"
                            f"{current_pr['pr_id']}:{head_sha}:"
                            f"{canonical_digest(terminal_proof)}"
                        ),
                    )
                if runner_initiated:
                    kernel.record_delivery_metadata(
                        ticket_id, "integration", receipt
                    )
                    kernel.record_integration(
                        ticket_id,
                        expected_head_sha=head_sha,
                        terminal_proof=terminal_proof,
                    )
                    replayed = False
                else:
                    proof_digest = canonical_digest(terminal_proof)
                    _external_receipt, replayed = kernel.record_external_integration(
                        ticket_id,
                        actor="scheduler:terminal-integration",
                        head_sha=head_sha,
                        evidence=f"terminal-integration-proof:{proof_digest}",
                        provider_observation=receipt,
                        terminal_proof=terminal_proof,
                    )
                processed.append(
                    {
                        "operation": operation,
                        "ticket_id": ticket_id,
                        "result": "integrated",
                        "head_sha": head_sha,
                        "recorded_head_sha": (
                            equivalent_receipt.get("recorded_head_sha")
                            if isinstance(equivalent_receipt, dict)
                            else None
                        ),
                        "adopted_head_sha": (
                            equivalent_receipt.get("observed_head_sha")
                            if isinstance(equivalent_receipt, dict)
                            else None
                        ),
                        "provenance": provenance,
                        "replayed": replayed,
                        "terminal_proof_digest": canonical_digest(terminal_proof),
                        "equivalent_head_receipt_digest": (
                            canonical_digest(equivalent_receipt)
                            if equivalent_receipt is not None
                            else None
                        ),
                        "equivalent_head_topology": (
                            equivalent_receipt.get("topology")
                            if isinstance(equivalent_receipt, dict)
                            else None
                        ),
                        "equivalent_head_replayed": equivalent_replayed,
                    }
                )
            elif operation == "reconcile":
                render_payload = _validate_reconciliation_event(kernel, event)
                blockers = ticket["blocked_by"]
                provider = detect_provider(
                    "", override=kernel.ledger["provider"]
                )
                command_runner = SubprocessCommandRunner()
                prepared = ticket["delivery"].get("reconcile-prepare")
                if prepared is None:
                    child_lineage = ticket["delivery_lineage"]
                    reconciliation_mode = "stack"
                    if len(blockers) == 1:
                        parent = kernel.ledger["tickets"][blockers[0]]
                        parent_lineage = parent["delivery_lineage"]
                        parent_branch = parent_lineage["branch"]
                        parent_head = parent_lineage["head_sha"]
                        base_branch = parent_lineage["base_branch"]
                    else:
                        reconciliation_mode = "base-advance"
                        parent_branch = child_lineage["base_branch"]
                        parent_head = child_lineage["base_sha"]
                        base_branch = child_lineage["base_branch"]
                    expected_remote_sha = child_lineage["head_sha"]
                    claimed_inputs = {
                        "parent_branch": parent_branch,
                        "base_branch": base_branch,
                        "expected_remote_sha": expected_remote_sha,
                    }
                    for field, authoritative in claimed_inputs.items():
                        supplied = event.get(field)
                        if supplied is not None and supplied != authoritative:
                            raise TransitionError(
                                f"caller-supplied {field} contradicts delivery lineage"
                            )
                    try:
                        _mutation_boundary(
                            kernel, ticket_id, "git:reconcile-fetch"
                        )
                        base_ref, base_sha, base_tree_oid = _fetch_target_base(
                            worktree,
                            command_runner,
                            base_branch,
                            boundary_guard=lambda boundary: _mutation_boundary(
                                kernel, ticket_id, boundary
                            ),
                        )
                        assert_ticket_source_mode(
                            kernel,
                            ticket_id,
                            "git:reconcile-base",
                            base_ref=base_sha,
                        )
                        intent = {
                            "schema": 1,
                            "branch": child_lineage["branch"],
                            "old_head": child_lineage["head_sha"],
                            "parent_branch": parent_branch,
                            "parent_head": parent_head,
                            "expected_remote_sha": expected_remote_sha,
                            "target_base": {
                                "branch": base_branch,
                                "ref": base_ref,
                                "sha": base_sha,
                                "tree_oid": base_tree_oid,
                            },
                        }
                        if reconciliation_mode == "base-advance":
                            intent["mode"] = reconciliation_mode
                        existing_intent = ticket["delivery"].get(
                            "reconcile-intent"
                        )
                        replay_intent = existing_intent is not None
                        preparation_refresh = None
                        if existing_intent is None:
                            kernel.record_delivery_metadata(
                                ticket_id,
                                "reconcile-intent",
                                intent,
                            )
                            store.save(kernel.ledger)
                        else:
                            try:
                                preparation_refresh = build_preparation_refresh(
                                    existing_intent,
                                    ticket["delivery"].get(
                                        PREPARATION_REFRESH_STEP
                                    ),
                                    intent,
                                )
                            except ReconciliationIntentError as error:
                                raise GitError(str(error)) from error
                            if (
                                preparation_refresh is not None
                                and ticket["delivery"].get(
                                    PREPARATION_REFRESH_STEP
                                )
                                != preparation_refresh
                            ):
                                kernel.record_delivery_metadata(
                                    ticket_id,
                                    PREPARATION_REFRESH_STEP,
                                    preparation_refresh,
                                )
                                store.save(kernel.ledger)
                                persisted_refresh = store.load()["tickets"][
                                    ticket_id
                                ]["delivery"].get(PREPARATION_REFRESH_STEP)
                                if persisted_refresh != preparation_refresh:
                                    raise GitError(
                                        "pre-prepare target refresh readback drifted"
                                    )
                                ticket = kernel.ledger["tickets"][ticket_id]
                        _mutation_boundary(
                            kernel, ticket_id, "git:reconcile-worktree"
                        )
                        (
                            old_head,
                            new_head,
                            observed_base_sha,
                            observed_base_tree_oid,
                            fixed,
                        ) = _derive_reconciliation_candidate(
                            worktree,
                            provider,
                            ticket,
                            parent_head=parent_head,
                            base_sha=base_sha,
                            base_tree_oid=base_tree_oid,
                            expected_remote_sha=expected_remote_sha,
                            replay_intent=replay_intent,
                            preparation_refresh=preparation_refresh,
                            command_runner=command_runner,
                            boundary_guard=lambda boundary: _mutation_boundary(
                                kernel, ticket_id, boundary
                            ),
                            conflict_resolver=_reconciliation_conflict_resolver(
                                store,
                                kernel,
                                ticket_id,
                                worktree,
                                runner=command_runner,
                            ),
                        )
                    except (GitError, ProviderError) as error:
                        processed.append(
                            _reconciliation_error_gate(
                                store,
                                kernel,
                                ticket_id,
                                error,
                                default_category="stack-reconciliation",
                            )
                        )
                        break
                    gate_actor = "scheduler:stack-reconciliation"
                    gate_evidence = f"head-replacement:{old_head}:{new_head}"
                    with _resolved_reconciliation_gates(
                        kernel,
                        ticket_id,
                        actor=gate_actor,
                        evidence=gate_evidence,
                    ) as resolved_gate_ids:
                        equivalent = kernel.prepare_reconciliation(
                            ticket_id,
                            fixed,
                            old_head=old_head,
                            new_head=new_head,
                            base_branch=base_branch,
                            base_sha=observed_base_sha,
                            base_tree_oid=observed_base_tree_oid,
                            expected_remote_sha=expected_remote_sha,
                            resolved_gate_ids=resolved_gate_ids,
                            gate_actor=gate_actor,
                            gate_evidence=gate_evidence,
                        )
                    processed.append(
                        {
                            "operation": operation,
                            "ticket_id": ticket_id,
                            "result": (
                                "evidence-preserved"
                                if equivalent
                                else "revalidation-required"
                            ),
                            "old_head": old_head,
                            "new_head": new_head,
                            "tree_oid": fixed.candidate_tree_oid,
                            "semantic_candidate": asdict(fixed),
                            "target_refreshed_before_prepare": (
                                preparation_refresh is not None
                            ),
                            "resolved_gate_ids": resolved_gate_ids,
                        }
                    )
                else:
                    pending_resume_state = prepared.get("pending_resume_state")
                    if ticket["state"] == "active" or (
                        ticket["state"] == "gated"
                        and pending_resume_state in {"active", "verified"}
                    ):
                        processed.append(
                            {
                                "operation": operation,
                                "ticket_id": ticket_id,
                                "result": (
                                    "evidence-preserved"
                                    if pending_resume_state == "verified"
                                    else "revalidation-required"
                                ),
                                "old_head": prepared["old_head"],
                                "new_head": prepared["new_head"],
                                "tree_oid": ticket["candidate_ref"]["candidate_tree_oid"],
                                "resolved_gate_ids": prepared.get(
                                    "resolved_gate_ids", []
                                ),
                            }
                        )
                        store.save(kernel.ledger)
                        break
                    refresh_intent = ticket["delivery"].get(
                        "reconcile-refresh-intent"
                    )
                    if refresh_intent is not None and not isinstance(
                        refresh_intent, dict
                    ):
                        raise TransitionError(
                            "reconciliation refresh intent is malformed"
                        )
                    fixed = _candidate_ref_for_ticket(worktree, ticket)
                    fixed_document = asdict(fixed)
                    if (
                        refresh_intent is None
                        and fixed_document != ticket["delivery_candidate_ref"]
                    ):
                        if fixed_document != ticket["candidate_ref"]:
                            kernel.prepare_reconciliation_delivery_revalidation(
                                ticket_id, fixed
                            )
                            processed.append(
                                {
                                    "operation": operation,
                                    "ticket_id": ticket_id,
                                    "result": "revalidation-required",
                                    "tree_oid": fixed.candidate_tree_oid,
                                }
                            )
                            store.save(kernel.ledger)
                            break
                        old_local_head = prepared["new_head"]
                        try:
                            new_local_head = _seal_revalidated_reconciliation_head(
                                worktree,
                                ticket_id,
                                ticket,
                                fixed,
                                run_id=kernel.ledger["run_id"],
                                command_runner=command_runner,
                                boundary_guard=lambda: _mutation_boundary(
                                    kernel,
                                    ticket_id,
                                    "git:reconcile-revalidation-commit",
                                ),
                            )
                            kernel.seal_revalidated_reconciliation_candidate(
                                ticket_id,
                                fixed,
                                expected_old_local_head=old_local_head,
                                new_local_head=new_local_head,
                            )
                            store.save(kernel.ledger)
                        except GitError as error:
                            processed.append(
                                _reconciliation_error_gate(
                                    store,
                                    kernel,
                                    ticket_id,
                                    error,
                                    default_category="stack-reconciliation-recovery",
                                )
                            )
                            break
                        ticket = kernel.ledger["tickets"][ticket_id]
                        prepared = ticket["delivery"]["reconcile-prepare"]
                    if refresh_intent is None:
                        target = prepared["target_base"]
                        try:
                            _assert_target_base_sha(
                                worktree,
                                target["branch"],
                                target["sha"],
                            )
                        except GitError:
                            try:
                                if any(
                                    step in ticket["delivery"]
                                    for step in (
                                        "reconcile-push",
                                        "reconcile-retarget",
                                    )
                                ):
                                    raise GitError(
                                        "reconciliation target cannot refresh after "
                                        "provider mutation"
                                    )
                                (
                                    target_ref,
                                    refreshed_base_sha,
                                    refreshed_base_tree_oid,
                                ) = _fetch_target_base(
                                    worktree,
                                    command_runner,
                                    target["branch"],
                                    boundary_guard=lambda boundary: _mutation_boundary(
                                        kernel, ticket_id, boundary
                                    ),
                                )
                                if refreshed_base_sha == target["sha"]:
                                    raise GitError(
                                        "target base observation changed without a new SHA"
                                    )
                                prior_intent = ticket["delivery"].get(
                                    "reconcile-intent"
                                )
                                if not isinstance(prior_intent, dict):
                                    raise GitError(
                                        "reconciliation target refresh requires its prior intent"
                                    )
                                replacement_intent = copy.deepcopy(prior_intent)
                                replacement_intent["target_base"] = {
                                    "branch": target["branch"],
                                    "ref": target_ref,
                                    "sha": refreshed_base_sha,
                                    "tree_oid": refreshed_base_tree_oid,
                                }
                                refresh_intent = {
                                    "schema": 1,
                                    "branch": ticket["pr"]["branch"],
                                    "old_head": ticket["pr"]["head_sha"],
                                    "expected_remote_sha": prepared[
                                        "expected_remote_sha"
                                    ],
                                    "old_local_head": prepared["new_head"],
                                    "old_target": copy.deepcopy(target),
                                    "new_target": copy.deepcopy(
                                        replacement_intent["target_base"]
                                    ),
                                    "old_intent": copy.deepcopy(prior_intent),
                                    "old_prepare": copy.deepcopy(prepared),
                                    "replacement_intent": replacement_intent,
                                }
                                kernel.record_delivery_metadata(
                                    ticket_id,
                                    "reconcile-refresh-intent",
                                    refresh_intent,
                                )
                                store.save(kernel.ledger)
                                ticket = kernel.ledger["tickets"][ticket_id]
                            except (GitError, ProviderError) as error:
                                processed.append(
                                    _reconciliation_error_gate(
                                        store,
                                        kernel,
                                        ticket_id,
                                        error,
                                        default_category="stack-reconciliation",
                                    )
                                )
                                break
                    if isinstance(refresh_intent, dict):
                        try:
                            (
                                refresh_old_head,
                                refresh_new_head,
                                refresh_base_sha,
                                refresh_base_tree_oid,
                                refresh_candidate,
                            ) = _derive_reconciliation_refresh_candidate(
                                worktree,
                                provider,
                                ticket,
                                refresh_intent,
                                command_runner=command_runner,
                                boundary_guard=lambda boundary: _mutation_boundary(
                                    kernel, ticket_id, boundary
                                ),
                                conflict_resolver=_reconciliation_conflict_resolver(
                                    store,
                                    kernel,
                                    ticket_id,
                                    worktree,
                                    runner=command_runner,
                                ),
                            )
                            gate_actor = "scheduler:stack-reconciliation"
                            gate_evidence = (
                                "head-replacement:"
                                f"{refresh_old_head}:{refresh_new_head}"
                            )
                            with _resolved_reconciliation_gates(
                                kernel,
                                ticket_id,
                                actor=gate_actor,
                                evidence=gate_evidence,
                            ) as resolved_gate_ids:
                                equivalent = kernel.prepare_reconciliation(
                                    ticket_id,
                                    refresh_candidate,
                                    old_head=refresh_old_head,
                                    new_head=refresh_new_head,
                                    base_branch=refresh_intent["new_target"][
                                        "branch"
                                    ],
                                    base_sha=refresh_base_sha,
                                    base_tree_oid=refresh_base_tree_oid,
                                    expected_remote_sha=refresh_intent[
                                        "expected_remote_sha"
                                    ],
                                    refresh_intent=refresh_intent,
                                    replacement_intent=refresh_intent[
                                        "replacement_intent"
                                    ],
                                    resolved_gate_ids=resolved_gate_ids,
                                    gate_actor=gate_actor,
                                    gate_evidence=gate_evidence,
                                )
                        except (GitError, ProviderError, TransitionError) as error:
                            processed.append(
                                _reconciliation_error_gate(
                                    store,
                                    kernel,
                                    ticket_id,
                                    error,
                                    default_category="stack-reconciliation",
                                )
                            )
                            break
                        processed.append(
                            {
                                "operation": operation,
                                "ticket_id": ticket_id,
                                "result": (
                                    "evidence-preserved"
                                    if equivalent
                                    else "revalidation-required"
                                ),
                                "target_refreshed": True,
                                "old_head": refresh_old_head,
                                "new_head": refresh_new_head,
                                "old_target_sha": refresh_intent["old_target"][
                                    "sha"
                                ],
                                "new_target_sha": refresh_base_sha,
                                "tree_oid": refresh_candidate.candidate_tree_oid,
                                "semantic_candidate": asdict(refresh_candidate),
                                "resolved_gate_ids": resolved_gate_ids,
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
                    base_branch = prepared["target_base"]["branch"]
                    target_base_sha = prepared["target_base"]["sha"]
                    executor = ProviderExecutor(
                        provider,
                        cwd=worktree,
                        mode="live",
                        runner=runner,
                    )
                    body_finalizer = DeliveryFinalizer(
                        store,
                        kernel,
                        executor,
                        boundary_guard=lambda guarded_ticket, boundary: _mutation_boundary(
                            kernel, guarded_ticket, boundary
                        ),
                    )
                    request = body_finalizer.reconcile_render_request(
                        ticket_id,
                        branch=branch,
                        base_branch=base_branch,
                        old_head=old_head,
                        new_head=new_head,
                    )
                    rendered = body_finalizer.load_reconcile_rendered_body(
                        ticket_id, request
                    )
                    if rendered is None:
                        if render_payload is None:
                            processed.append(
                                {
                                    "operation": operation,
                                    "ticket_id": ticket_id,
                                    "result": "render-required",
                                    "head_sha": new_head,
                                    "branch": branch,
                                    "render_request_hash": request["request_hash"],
                                    "render_request": request,
                                }
                            )
                            store.save(kernel.ledger)
                            break
                        try:
                            rendered = body_finalizer.accept_reconcile_render_payload(
                                ticket_id,
                                request=request,
                                payload=render_payload,
                            )
                        except DeliveryBodyError as error:
                            processed.append(
                                _reconciliation_gate(
                                    store,
                                    kernel,
                                    ticket_id,
                                    category="delivery-pr-body",
                                    reason=str(error),
                                )
                            )
                            break
                    elif render_payload is not None:
                        raise TransitionError(
                            "reconciled PR body is already validated for this head"
                        )
                    body, bundle, body_validator = rendered
                    try:
                        _assert_target_base_sha(
                            worktree,
                            base_branch,
                            target_base_sha,
                        )
                        with _reconciliation_authority_guard(
                            kernel, ticket_id
                        ):
                            push_receipt = _publish_reconciled_branch(
                                worktree,
                                provider,
                                command_runner,
                                branch=branch,
                                base_branch=base_branch,
                                expected_remote_sha=expected_remote_sha,
                                new_head=new_head,
                                boundary_guard=lambda: _mutation_boundary(
                                    kernel,
                                    ticket_id,
                                    "git:reconcile-push",
                                    check_reconciliation_authority=False,
                                ),
                            )
                    except (GitError, ProviderError) as error:
                        processed.append(
                            _reconciliation_error_gate(
                                store,
                                kernel,
                                ticket_id,
                                error,
                                default_category="stack-reconciliation",
                            )
                        )
                        break
                    kernel.record_delivery_metadata(
                        ticket_id, "reconcile-push", push_receipt
                    )
                    store.save(kernel.ledger)
                    try:
                        receipt = _guarded_execute(
                            executor, kernel, ticket_id, RETARGET_PR,
                            pr_id=ticket["pr"]["pr_id"],
                            base=base_branch,
                            body_artifact=body,
                        )
                        if (
                            receipt.get("evidence_class") != "live"
                            or receipt.get("pr_id") != ticket["pr"]["pr_id"]
                            or receipt.get("base") != base_branch
                            or receipt.get("head_sha") != new_head
                        ):
                            raise ProviderError(
                                "retarget provider readback contradicts reconciliation"
                            )
                        _assert_target_base_sha(
                            worktree,
                            base_branch,
                            target_base_sha,
                        )
                        try:
                            body_validator(receipt["body"], bundle, new_head)
                        except VerificationCheckpointError as error:
                            raise DeliveryBodyError(
                                "reconcile-body-readback",
                                f"provider PR-body readback validation failed: {error}",
                            ) from error
                    except (DeliveryBodyError, GitError, ProviderError) as error:
                        processed.append(
                            _reconciliation_error_gate(
                                store,
                                kernel,
                                ticket_id,
                                error,
                                default_category="provider-retarget",
                            )
                        )
                        break
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


def _timestamp() -> tuple[int, str]:
    value = time.time_ns()
    rendered = datetime.fromtimestamp(
        value / 1_000_000_000, tz=timezone.utc
    ).isoformat()
    return value, rendered


def _merge_intent_key(
    *,
    provider: str,
    pr_id: str,
    head_sha: str,
    actor: str,
    evidence: str,
    mode: str = "runner",
) -> str:
    payload = {
        "schema": 1,
        "provider": provider,
        "pr_id": pr_id,
        "head_sha": head_sha,
        "actor": actor,
        "evidence": evidence,
        "mode": mode,
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _record_merge_progress(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    *,
    phase: str,
    status: str,
    head_sha: str,
    intent_key: str,
    error: str | None = None,
    gate_id: str | None = None,
) -> None:
    ticket = kernel.ledger["tickets"][ticket_id]
    previous = ticket["delivery"].get("merge-progress", {})
    now_ns, now_text = _timestamp()
    started_ns = previous.get("started_at_ns", now_ns)
    started_at = previous.get("started_at", now_text)
    progress: dict[str, Any] = {
        "schema": 1,
        "phase": phase,
        "status": status,
        "head_sha": head_sha,
        "intent_key": intent_key,
        "started_at": started_at,
        "started_at_ns": started_ns,
        "updated_at": now_text,
        "updated_at_ns": now_ns,
    }
    if error is not None:
        progress["error"] = error
    if gate_id is not None:
        progress["gate_id"] = gate_id
    kernel.record_delivery_metadata(ticket_id, "merge-progress", progress)
    store.save(kernel.ledger)


def _merge_gate_ids(kernel: Kernel, ticket_id: str) -> list[str]:
    return [
        gate_id
        for gate_id, gate in kernel.ledger["gates"].items()
        if gate["ticket_id"] == ticket_id
        and gate["category"] == "provider-merge"
        and gate["state"] == "open"
    ]


def _terminal_integration_proof(
    kernel: Kernel,
    ticket_id: str,
    observation: Mapping[str, Any],
    *,
    provenance: str,
) -> dict[str, Any]:
    try:
        return build_terminal_integration_proof(
            Path(kernel.ledger["worktree"]),
            kernel.ledger,
            ticket_id,
            observation,
            provenance=provenance,
            boundary_guard=lambda boundary: _mutation_boundary(
                kernel, ticket_id, boundary
            ),
        )
    except TerminalIntegrationError as error:
        raise ProviderError(str(error)) from error


def _equivalent_head_receipt(
    kernel: Kernel,
    ticket_id: str,
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    ticket = kernel.ledger["tickets"][ticket_id]
    pr = ticket.get("pr", {})
    recorded_head = pr.get("head_sha")
    observed_head = observation.get("head_sha")
    actor = "scheduler:post-merge-equivalent-head"
    evidence = (
        "provider-merged-head-equivalence:"
        f"{kernel.ledger.get('provider')}:{pr.get('pr_id')}:"
        f"{recorded_head}:{observed_head}"
    )
    try:
        return build_equivalent_head_receipt(
            Path(kernel.ledger["worktree"]),
            kernel.ledger,
            ticket_id,
            observation,
            actor=actor,
            evidence=evidence,
            boundary_guard=lambda boundary: _mutation_boundary(
                kernel, ticket_id, boundary
            ),
        )
    except EquivalentHeadError as error:
        raise ProviderError(str(error)) from error


def _validate_merge_observation(
    receipt: dict[str, Any],
    *,
    provider: str,
    pr_id: str,
) -> None:
    expected = {
        "provider": provider,
        "operation": GET_PR_STATE,
        "evidence_class": "live",
        "observed": True,
        "pr_id": pr_id,
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise ProviderError("merge provider observation contradicts the recorded PR")
    if receipt.get("state") not in {"open", "merged"}:
        raise ProviderError("merge provider observation is neither open nor merged")
    if not isinstance(receipt.get("head_sha"), str) or not receipt["head_sha"]:
        raise ProviderError("merge provider observation omitted the exact head SHA")


def _autonomous_eligibility(
    kernel: Kernel,
    ticket_id: str,
    *,
    runner: CommandRunner | None,
) -> dict[str, Any]:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    grant = kernel.ledger.get("autonomous_merge_grant")
    if kernel.ledger.get("merge_policy") != "autonomous" or not isinstance(
        grant, dict
    ):
        raise TransitionError("autonomous merge requires a persisted run grant")
    if ticket is None or not ticket.get("pr"):
        raise TransitionError("autonomous merge requires a recorded PR")
    if is_repository_adoption_evidence(grant.get("evidence")):
        try:
            RepositoryMergeAuthorityStore(
                Path(kernel.ledger["repo"])
            ).assert_run_grant(grant)
        except RepositoryMergeAuthorityError as error:
            raise ProviderError(str(error)) from error
    if kernel.ledger.get("provider_mode") != "live":
        raise ProviderError("simulated provider evidence cannot authorize merge")
    if not kernel.autonomous_merge_candidate_ready(ticket_id):
        raise ProviderError(
            "autonomous merge requires the exact semantic candidate to be fully validated"
        )
    lineage = ticket.get("delivery_lineage")
    pr = ticket["pr"]
    if (
        not isinstance(lineage, dict)
        or lineage.get("provider") != grant["provider"]
        or lineage.get("pr_id") != pr.get("pr_id")
        or lineage.get("head_sha") != pr.get("head_sha")
    ):
        raise ProviderError(
            "autonomous merge delivery lineage contradicts the recorded PR"
        )

    provider = detect_provider("", override=kernel.ledger["provider"])
    provider.negotiate(
        {
            GET_PR_STATE,
            GET_CHECKS_AND_POLICIES,
            GET_APPROVALS,
            MERGE_EXPECTED_HEAD,
        }
    )
    executor = ProviderExecutor(
        provider,
        cwd=Path(kernel.ledger["worktree"]),
        mode="live",
        runner=runner,
    )
    observation = _guarded_execute(
        executor, kernel, ticket_id, GET_PR_STATE, pr_id=pr["pr_id"]
    )
    _validate_merge_observation(
        observation,
        provider=provider.name,
        pr_id=pr["pr_id"],
    )
    authorization = ticket.get("merge_authorization")
    merge_attempt = ticket.get("delivery", {}).get("merge-attempt")
    if observation["state"] == "merged":
        if (
            isinstance(authorization, dict)
            and authorization.get("mode") == "autonomous"
            and authorization.get("head_sha") == pr["head_sha"]
            and isinstance(merge_attempt, dict)
            and merge_attempt.get("head_sha") == pr["head_sha"]
        ):
            return {
                "schema": 1,
                "status": "reconcile",
                "ticket_id": ticket_id,
                "candidate_ref": ticket["candidate_ref"],
                "delivery_candidate_ref": ticket["delivery_candidate_ref"],
                "head_sha": pr["head_sha"],
                "grant": grant,
                "provider_observation": observation,
                "checks_and_policies": None,
                "approvals": None,
                "reasons": [],
            }
        return {
            "schema": 1,
            "status": "external-reconcile",
            "ticket_id": ticket_id,
            "candidate_ref": ticket["candidate_ref"],
            "delivery_candidate_ref": ticket["delivery_candidate_ref"],
            "head_sha": pr["head_sha"],
            "grant": grant,
            "provider_observation": observation,
            "checks_and_policies": None,
            "approvals": None,
            "reasons": [],
        }
    if not kernel.autonomous_merge_dependencies_ready(ticket_id):
        raise ProviderError(
            "autonomous merge requires integrated blockers and reconciled stack lineage"
        )
    checks = _guarded_execute(
        executor, kernel, ticket_id, GET_CHECKS_AND_POLICIES,
        pr_id=pr["pr_id"],
        expected_head=observation["head_sha"],
    )
    approvals = _guarded_execute(
        executor, kernel, ticket_id, GET_APPROVALS, pr_id=pr["pr_id"]
    )
    reasons: list[str] = []
    if observation["state"] != "open":
        reasons.append("provider PR is not open")
    if observation["head_sha"] != pr["head_sha"]:
        reasons.append("provider PR head differs from the validated delivery head")
    if observation.get("mergeable") != "MERGEABLE":
        reasons.append("provider mergeability is not proven")
    if observation.get("merge_state_status") not in {"CLEAN", "HAS_HOOKS"}:
        reasons.append("provider merge state is not clean or queue pinning is uncertain")
    if (
        checks.get("provider") != provider.name
        or checks.get("operation") != GET_CHECKS_AND_POLICIES
        or checks.get("evidence_class") != "live"
        or checks.get("observed") is not True
        or checks.get("pr_id") != pr["pr_id"]
        or checks.get("head_sha") != observation["head_sha"]
        or checks.get("base") != observation["base"]
        or checks.get("merge_mode") not in {"direct", "queue"}
        or not isinstance(checks.get("active_rules"), list)
        or not isinstance(checks.get("checks_and_policies"), list)
    ):
        reasons.append("provider checks/policies receipt is incomplete")
    else:
        check_items = checks["checks_and_policies"]
        malformed_items = [
            item
            for item in check_items
            if not isinstance(item, dict)
            or set(item) != {"bucket", "name", "state", "workflow"}
            or any(
                not isinstance(item.get(field), str) or not item[field]
                for field in ("bucket", "name", "state")
            )
            or not isinstance(item.get("workflow"), str)
        ]
        if malformed_items:
            reasons.append("provider returned a malformed checks/policies item")
        buckets = {
            item["bucket"].casefold()
            for item in check_items
            if isinstance(item, dict) and isinstance(item.get("bucket"), str)
        }
        if buckets.intersection({"pending", "queued", "in_progress", "waiting"}):
            reasons.append("required checks or policies are pending")
        if buckets.intersection(
            {"fail", "failed", "cancel", "cancelled", "canceled", "error"}
        ):
            reasons.append("required checks or policies failed")
        if buckets.difference(
            {
                "pass",
                "passed",
                "success",
                "successful",
                "skipping",
                "skipped",
                "pending",
                "queued",
                "in_progress",
                "waiting",
                "fail",
                "failed",
                "cancel",
                "cancelled",
                "canceled",
                "error",
            }
        ):
            reasons.append("provider returned an unknown checks/policies state")
    review_decision = approvals.get("review_decision")
    if (
        approvals.get("provider") != provider.name
        or approvals.get("operation") != GET_APPROVALS
        or approvals.get("evidence_class") != "live"
        or approvals.get("observed") is not True
        or approvals.get("pr_id") != pr["pr_id"]
    ):
        reasons.append("provider approvals receipt is incomplete")
    elif review_decision not in {None, "", "APPROVED"}:
        reasons.append(f"provider review decision is {review_decision}")
    return {
        "schema": 1,
        "status": "eligible" if not reasons else "gated",
        "ticket_id": ticket_id,
        "candidate_ref": ticket["candidate_ref"],
        "delivery_candidate_ref": ticket["delivery_candidate_ref"],
        "head_sha": pr["head_sha"],
        "grant": grant,
        "provider_observation": observation,
        "checks_and_policies": checks,
        "approvals": approvals,
        "reasons": reasons,
    }


def _record_autonomous_merge_gate(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    *,
    grant: dict[str, Any],
    reason: str,
    head_sha: str,
) -> dict[str, Any]:
    ticket = kernel.ledger["tickets"][ticket_id]
    existing_gates = _merge_gate_ids(kernel, ticket_id)
    if existing_gates:
        gate_id = existing_gates[0]
        kernel.refresh_gate_reason(gate_id, reason=reason)
    else:
        gate_id = kernel.open_gate(
            ticket_id,
            "provider-merge",
            scope="ticket",
            reason=reason,
        )
    _record_merge_progress(
        store,
        kernel,
        ticket_id,
        phase="eligibility",
        status="gated",
        head_sha=head_sha,
        intent_key=_merge_intent_key(
            provider=kernel.ledger["provider"],
            pr_id=ticket["pr"]["pr_id"],
            head_sha=head_sha,
            actor=grant["actor"],
            evidence=grant["evidence"],
            mode="autonomous",
        ),
        error=reason,
        gate_id=gate_id,
    )
    return {
        "result": "gated",
        "gate": "provider-merge",
        "gate_id": gate_id,
        "reason": reason,
        "head_sha": head_sha,
    }


def _drive_autonomous_merge(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    *,
    runner: CommandRunner | None,
) -> dict[str, Any]:
    ticket = kernel.ledger["tickets"][ticket_id]
    grant = kernel.ledger.get("autonomous_merge_grant")
    if not isinstance(grant, dict):
        raise TransitionError("autonomous merge grant is missing")
    try:
        eligibility = _autonomous_eligibility(
            kernel,
            ticket_id,
            runner=runner,
        )
    except ProviderError as error:
        eligibility = {
            "schema": 1,
            "status": "gated",
            "ticket_id": ticket_id,
            "candidate_ref": ticket.get("candidate_ref"),
            "delivery_candidate_ref": ticket.get("delivery_candidate_ref"),
            "head_sha": ticket.get("pr", {}).get("head_sha"),
            "grant": grant,
            "provider_observation": None,
            "checks_and_policies": None,
            "approvals": None,
            "reasons": [str(error)],
        }
    kernel.record_delivery_metadata(
        ticket_id,
        "autonomous-eligibility",
        eligibility,
    )
    existing_gates = _merge_gate_ids(kernel, ticket_id)
    if eligibility["status"] not in {
        "eligible",
        "reconcile",
        "external-reconcile",
    }:
        return _record_autonomous_merge_gate(
            store,
            kernel,
            ticket_id,
            grant=grant,
            reason="; ".join(eligibility["reasons"]),
            head_sha=ticket["pr"]["head_sha"],
        )
    authority_guard = nullcontext()
    if is_repository_adoption_evidence(grant.get("evidence")):
        authority_guard = RepositoryMergeAuthorityStore(
            Path(kernel.ledger["repo"])
        ).guard_run_grant(grant)
    try:
        # Keep revocation serialized from this final check through exact-head provider
        # mutation and readback. Provider-derived gates are consumed only inside it.
        with authority_guard:
            terminal_proof = None
            if eligibility["status"] == "external-reconcile":
                observation = eligibility["provider_observation"]
                if not isinstance(observation, dict):
                    raise ProviderError(
                        "external reconciliation lost its provider observation"
                    )
                terminal_proof = _terminal_integration_proof(
                    kernel,
                    ticket_id,
                    observation,
                    provenance="external-readback",
                )
            for gate_id in existing_gates:
                kernel.approve_gate(
                    gate_id,
                    actor=f"provider:{kernel.ledger['provider']}",
                    evidence=(
                        "autonomous-eligibility:"
                        f"{ticket['pr']['pr_id']}:{ticket['pr']['head_sha']}"
                    ),
                )
            if terminal_proof is not None:
                proof_digest = canonical_digest(terminal_proof)
                receipt, replayed = kernel.record_external_integration(
                    ticket_id,
                    actor="scheduler:terminal-integration",
                    head_sha=ticket["pr"]["head_sha"],
                    evidence=f"terminal-integration-proof:{proof_digest}",
                    provider_observation=eligibility["provider_observation"],
                    terminal_proof=terminal_proof,
                )
                store.save(kernel.ledger)
                return {
                    "result": "integrated",
                    "head_sha": ticket["pr"]["head_sha"],
                    "replayed": replayed,
                    "provenance": "external-readback",
                    "receipt": receipt,
                    "terminal_proof_digest": proof_digest,
                }
            store.save(kernel.ledger)
            return _drive_runner_merge(
                store,
                kernel,
                ticket_id,
                actor=grant["actor"],
                head_sha=ticket["pr"]["head_sha"],
                evidence=grant["evidence"],
                runner=runner,
                authorization_mode="autonomous",
                expected_merge_mode=(
                    eligibility["checks_and_policies"].get("merge_mode")
                    if isinstance(eligibility.get("checks_and_policies"), dict)
                    else None
                ),
            )
    except (ProviderError, RepositoryMergeAuthorityError) as error:
        return _record_autonomous_merge_gate(
            store,
            kernel,
            ticket_id,
            grant=grant,
            reason=str(error),
            head_sha=ticket["pr"]["head_sha"],
        )


def _complete_runner_merge(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    *,
    actor: str,
    head_sha: str,
    evidence: str,
    runner: CommandRunner | None,
    authorization_mode: str = "runner",
    expected_merge_mode: str | None = None,
) -> dict[str, Any]:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if ticket is None or not ticket.get("pr"):
        raise TransitionError("runner merge requires a recorded PR")
    if ticket["state"] == "integrated":
        if ticket["pr"]["head_sha"] != head_sha:
            raise TransitionError("integrated ticket belongs to another head SHA")
        return {"result": "integrated", "head_sha": head_sha, "replayed": True}
    merge_gates = _merge_gate_ids(kernel, ticket_id)
    if ticket["state"] not in {"pr-open", "gated"} or (
        ticket["state"] == "gated" and not merge_gates
    ):
        raise TransitionError("runner merge requires an open PR or resumable merge gate")
    if kernel.ledger.get("provider_mode", "live") != "live":
        raise ProviderError("simulated provider evidence cannot authorize merge")

    provider = detect_provider("", override=kernel.ledger["provider"])
    provider.negotiate({GET_CHECKS_AND_POLICIES, MERGE_EXPECTED_HEAD})
    current_pr = ticket["pr"]
    pr_id = current_pr["pr_id"]
    if current_pr["head_sha"] != head_sha:
        raise TransitionError("merge authorization head SHA is stale")
    delivery = ticket.get("delivery", {})
    body_receipt = delivery.get("pr-body")
    reconcile_receipt = delivery.get("reconcile-retarget")
    provider_receipt = reconcile_receipt or delivery.get("pr")
    reconciled = isinstance(reconcile_receipt, dict)
    rebinds = (
        body_receipt.get("lineage_rebinds")
        if isinstance(body_receipt, dict)
        else None
    )
    latest_rebind = rebinds[-1] if isinstance(rebinds, list) and rebinds else None
    valid_body_lineage = not reconciled or (
        isinstance(body_receipt, dict)
        and body_receipt.get("schema") == 2
        and isinstance(latest_rebind, dict)
        and latest_rebind.get("new_head") == head_sha
        and latest_rebind.get("render_request_hash") == body_receipt.get("request_hash")
        and isinstance(latest_rebind.get("old_receipt"), dict)
    )
    if (
        not isinstance(body_receipt, dict)
        or not isinstance(provider_receipt, dict)
        or body_receipt.get("schema") not in {1, 2}
        or not valid_body_lineage
        or body_receipt.get("expected_head_sha") != head_sha
        or provider_receipt.get("pr_id") != pr_id
        or provider_receipt.get("head_sha") != head_sha
        or provider_receipt.get("evidence_class") != "live"
        or provider_receipt.get("observed") is not True
        or not isinstance(provider_receipt.get("body"), str)
        or hashlib.sha256(provider_receipt["body"].encode("utf-8")).hexdigest()
        != body_receipt.get("body_sha256")
        or delivery.get("result", {}).get("result") != "pr-open"
    ):
        raise TransitionError(
            "validated PR-body publication and readback are required before merge"
        )

    intent_key = _merge_intent_key(
        provider=provider.name,
        pr_id=pr_id,
        head_sha=head_sha,
        actor=actor,
        evidence=evidence,
        mode=authorization_mode,
    )
    existing_intent = delivery.get("merge-intent")
    if isinstance(existing_intent, dict) and existing_intent.get(
        "intent_key"
    ) not in {None, intent_key}:
        raise TransitionError("merge critical path belongs to another authorization")

    _record_merge_progress(
        store,
        kernel,
        ticket_id,
        phase="observe-head",
        status="running",
        head_sha=head_sha,
        intent_key=intent_key,
    )
    executor = ProviderExecutor(
        provider,
        cwd=Path(kernel.ledger["worktree"]),
        mode="live",
        runner=runner,
    )
    observation = _guarded_execute(
        executor, kernel, ticket_id, GET_PR_STATE, pr_id=pr_id
    )
    _validate_merge_observation(
        observation,
        provider=provider.name,
        pr_id=pr_id,
    )
    for gate_id in merge_gates:
        kernel.approve_gate(
            gate_id,
            actor=f"provider:{provider.name}",
            evidence=f"live-readback:{pr_id}:{observation['head_sha']}",
        )
    observed_head = observation["head_sha"]
    if observed_head != head_sha:
        raise ProviderError(
            "provider PR head changed before guarded merge; recorded delivery "
            "lineage was not adopted and requires Git reconciliation or revalidation"
        )
    kernel.record_delivery_metadata(
        ticket_id,
        "merge-observation",
        {**observation, "intent_key": intent_key},
    )
    store.save(kernel.ledger)

    if observation["state"] == "open" and expected_merge_mode is None:
        policy_observation = _guarded_execute(
            executor, kernel, ticket_id, GET_CHECKS_AND_POLICIES,
            pr_id=pr_id,
            expected_head=head_sha,
        )
        if (
            policy_observation.get("provider") != provider.name
            or policy_observation.get("operation") != GET_CHECKS_AND_POLICIES
            or policy_observation.get("evidence_class") != "live"
            or policy_observation.get("observed") is not True
            or policy_observation.get("pr_id") != pr_id
            or policy_observation.get("head_sha") != head_sha
            or policy_observation.get("base") != observation.get("base")
            or policy_observation.get("merge_mode") not in {"direct", "queue"}
            or not isinstance(policy_observation.get("active_rules"), list)
        ):
            raise ProviderError(
                "provider merge-policy receipt is incomplete or belongs to another head"
            )
        expected_merge_mode = policy_observation["merge_mode"]

    authorization = ticket.get("merge_authorization")
    expected_authorization = {
        "actor": actor,
        "head_sha": head_sha,
        "evidence": evidence,
        "mode": authorization_mode,
    }
    if authorization is None:
        if observation["state"] == "merged":
            raise TransitionError(
                "PR is already merged; reconcile it with --external-merge"
            )
        kernel.record_delivery_metadata(
            ticket_id,
            "merge-intent",
            {
                "schema": 1,
                "intent_key": intent_key,
                "provider": provider.name,
                "pr_id": pr_id,
                **expected_authorization,
            },
        )
        kernel.authorize_merge(
            ticket_id,
            actor=actor,
            head_sha=head_sha,
            evidence=evidence,
            mode=authorization_mode,
        )
        store.save(kernel.ledger)
    elif authorization != expected_authorization:
        raise TransitionError("persisted merge authorization is contradictory")

    mutation = ticket["delivery"].get("merge-mutation")
    if observation["state"] == "open":
        attempt = ticket["delivery"].get("merge-attempt")
        matching_attempt = (
            isinstance(attempt, dict)
            and attempt.get("intent_key") == intent_key
        )
        existing_queue_mutation = (
            isinstance(mutation, dict)
            and mutation.get("intent_key") == intent_key
            and mutation.get("merge_mode") == "queue"
        )
        if (
            isinstance(mutation, dict)
            and mutation.get("intent_key") == intent_key
            and not existing_queue_mutation
        ):
            raise ProviderError(
                "provider reports an open PR after accepting the guarded merge"
            )
        previous_attempt_mode = (
            "queue"
            if existing_queue_mutation
            else attempt.get("merge_mode")
            if matching_attempt
            else None
        )
        if (
            matching_attempt
            and previous_attempt_mode not in {"direct", "queue"}
        ):
            raise ProviderError(
                "persisted merge attempt omitted its provider merge mode"
            )
        if not matching_attempt:
            if expected_merge_mode not in {None, "direct", "queue"}:
                raise ProviderError("fresh eligibility returned an invalid merge mode")
            attempt_ns, attempt_at = _timestamp()
            attempt_receipt: dict[str, Any] = {
                "schema": 1,
                "intent_key": intent_key,
                "provider": provider.name,
                "pr_id": pr_id,
                "head_sha": head_sha,
                "attempted_at": attempt_at,
                "attempted_at_ns": attempt_ns,
            }
            if expected_merge_mode is not None:
                attempt_receipt["merge_mode"] = expected_merge_mode
            kernel.record_delivery_metadata(
                ticket_id,
                "merge-attempt",
                attempt_receipt,
            )
            previous_attempt_mode = expected_merge_mode
        _record_merge_progress(
            store,
            kernel,
            ticket_id,
            phase=(
                "merge-queue-readback"
                if existing_queue_mutation
                else "merge-command"
            ),
            status="running",
            head_sha=head_sha,
            intent_key=intent_key,
        )
        mutation = _guarded_execute(
            executor, kernel, ticket_id, MERGE_EXPECTED_HEAD,
            pr_id=pr_id,
            expected_head=head_sha,
            intent_key=intent_key,
            previous_attempt_mode=previous_attempt_mode,
            mutation_previously_applied=existing_queue_mutation,
            queue_dispatch_ambiguous=(
                matching_attempt
                and previous_attempt_mode == "queue"
                and not existing_queue_mutation
            ),
            authorization=MergeAuthorization(
                provider=provider.name,
                pr_id=pr_id,
                head_sha=head_sha,
                actor=actor,
                evidence=evidence,
            ),
        )
        if mutation.get("intent_key") != intent_key:
            raise ProviderError("merge mutation receipt lost its intent binding")
        kernel.record_delivery_metadata(ticket_id, "merge-mutation", mutation)
        store.save(kernel.ledger)

    _record_merge_progress(
        store,
        kernel,
        ticket_id,
        phase="readback",
        status="running",
        head_sha=head_sha,
        intent_key=intent_key,
    )
    readback = _guarded_execute(
        executor, kernel, ticket_id, GET_PR_STATE, pr_id=pr_id
    )
    _validate_merge_observation(
        readback,
        provider=provider.name,
        pr_id=pr_id,
    )
    if readback["head_sha"] != head_sha:
        raise ProviderError("guarded merge readback did not confirm the exact merged head")
    if readback["state"] != "merged":
        queue_entry = (
            mutation.get("queue_entry")
            if isinstance(mutation, dict)
            and mutation.get("intent_key") == intent_key
            and mutation.get("merge_mode") == "queue"
            else None
        )
        if readback["state"] != "open" or not isinstance(queue_entry, dict):
            raise ProviderError(
                "guarded merge readback did not confirm the exact merged head"
            )
        kernel.record_delivery_metadata(
            ticket_id,
            "merge-readback",
            {
                **readback,
                "intent_key": intent_key,
                "merge_mode": "queue",
                "queue_entry": queue_entry,
            },
        )
        _record_merge_progress(
            store,
            kernel,
            ticket_id,
            phase="merge-queue",
            status="waiting",
            head_sha=head_sha,
            intent_key=intent_key,
        )
        return {
            "result": "queued",
            "head_sha": head_sha,
            "replayed": bool(mutation.get("replayed")),
            "queue_entry": queue_entry,
        }
    terminal_proof = _terminal_integration_proof(
        kernel,
        ticket_id,
        readback,
        provenance="runner-merge",
    )
    kernel.record_delivery_metadata(
        ticket_id,
        "merge-readback",
        {**readback, "intent_key": intent_key},
    )
    kernel.record_delivery_metadata(ticket_id, "integration", readback)
    kernel.record_integration(
        ticket_id,
        expected_head_sha=head_sha,
        terminal_proof=terminal_proof,
    )
    _record_merge_progress(
        store,
        kernel,
        ticket_id,
        phase="integrated",
        status="integrated",
        head_sha=head_sha,
        intent_key=intent_key,
    )
    return {"result": "integrated", "head_sha": head_sha, "replayed": False}


def _drive_runner_merge(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    *,
    actor: str,
    head_sha: str,
    evidence: str,
    runner: CommandRunner | None,
    authorization_mode: str = "runner",
    expected_merge_mode: str | None = None,
) -> dict[str, Any]:
    try:
        return _complete_runner_merge(
            store,
            kernel,
            ticket_id,
            actor=actor,
            head_sha=head_sha,
            evidence=evidence,
            runner=runner,
            authorization_mode=authorization_mode,
            expected_merge_mode=expected_merge_mode,
        )
    except ProviderError as error:
        ticket = kernel.ledger["tickets"][ticket_id]
        pr_id = ticket.get("pr", {}).get("pr_id", "")
        intent_key = _merge_intent_key(
            provider=kernel.ledger["provider"],
            pr_id=pr_id,
            head_sha=head_sha,
            actor=actor,
            evidence=evidence,
            mode=authorization_mode,
        )
        existing_gates = _merge_gate_ids(kernel, ticket_id)
        gate_id = existing_gates[0] if existing_gates else None
        _record_merge_progress(
            store,
            kernel,
            ticket_id,
            phase="provider",
            status="gated",
            head_sha=head_sha,
            intent_key=intent_key,
            error=str(error),
            gate_id=gate_id,
        )
        if gate_id is None:
            gate_id = kernel.open_gate(
                ticket_id,
                "provider-merge",
                scope="ticket",
                reason=str(error),
            )
            _record_merge_progress(
                store,
                kernel,
                ticket_id,
                phase="provider",
                status="gated",
                head_sha=head_sha,
                intent_key=intent_key,
                error=str(error),
                gate_id=gate_id,
            )
        store.save(kernel.ledger)
        return {
            "result": "gated",
            "gate": "provider-merge",
            "gate_id": gate_id,
            "reason": str(error),
            "head_sha": head_sha,
        }


def _complete_external_merge(
    kernel: Kernel,
    ticket_id: str,
    *,
    actor: str,
    head_sha: str,
    evidence: str,
    runner: CommandRunner | None,
) -> dict[str, Any]:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if ticket is None or not ticket.get("pr"):
        raise TransitionError(
            "external merge reconciliation requires a recorded PR"
        )
    if not actor or not evidence:
        raise TransitionError(
            "external merge reconciliation requires actor and evidence"
        )
    current_pr = ticket["pr"]
    if current_pr.get("provider") != kernel.ledger["provider"]:
        raise TransitionError(
            "external merge reconciliation provider contradicts the recorded PR"
        )
    if current_pr["head_sha"] != head_sha:
        raise TransitionError("external merge reconciliation head SHA is stale")
    if kernel.ledger.get("provider_mode", "live") != "live":
        raise ProviderError(
            "simulated provider evidence cannot authorize external reconciliation"
        )

    merge_gates = _merge_gate_ids(kernel, ticket_id)
    open_ticket_gates = [
        gate_id
        for gate_id, gate in kernel.ledger["gates"].items()
        if gate["ticket_id"] == ticket_id and gate["state"] == "open"
    ]
    resumable_merge_gate = (
        ticket["state"] == "gated"
        and bool(merge_gates)
        and set(open_ticket_gates) == set(merge_gates)
        and all(
            kernel.ledger["gates"][gate_id]["resume_state"] == "pr-open"
            for gate_id in merge_gates
        )
    )
    if ticket["state"] == "integrated":
        observation = ticket.get("delivery", {}).get("integration")
        terminal_proof = ticket.get("delivery", {}).get(
            "terminal-integration"
        )
        if not isinstance(observation, dict) or not isinstance(
            terminal_proof, dict
        ):
            raise TransitionError(
                "integrated ticket has no terminal provider proof"
            )
    elif ticket["state"] != "pr-open" and not resumable_merge_gate:
        raise TransitionError(
            "external merge reconciliation requires an open PR or a resumable "
            "provider-merge gate"
        )
    else:
        provider = detect_provider("", override=kernel.ledger["provider"])
        provider.negotiate({GET_PR_STATE})
        executor = ProviderExecutor(
            provider,
            cwd=Path(kernel.ledger["worktree"]),
            mode="live",
            runner=runner,
        )
        observation = _guarded_execute(
            executor, kernel, ticket_id, GET_PR_STATE,
            pr_id=current_pr["pr_id"],
        )
        _validate_merge_observation(
            observation,
            provider=provider.name,
            pr_id=current_pr["pr_id"],
        )
        if observation["head_sha"] != head_sha:
            raise ProviderError(
                "external merge observation differs from the authorized head SHA"
            )
        if observation["state"] != "merged":
            raise ProviderError(
                "external merge observation did not confirm a merged PR"
            )
        terminal_proof = _terminal_integration_proof(
            kernel,
            ticket_id,
            observation,
            provenance="external-readback",
        )
        for gate_id in merge_gates:
            kernel.approve_gate(
                gate_id,
                actor=f"provider:{provider.name}",
                evidence=(
                    "external-merge-live-readback:"
                    f"{current_pr['pr_id']}:{observation['head_sha']}"
                ),
            )
    receipt, replayed = kernel.record_external_integration(
        ticket_id,
        actor=actor,
        head_sha=head_sha,
        evidence=evidence,
        provider_observation=observation,
        terminal_proof=terminal_proof,
    )
    return {
        "result": "integrated",
        "head_sha": head_sha,
        "replayed": replayed,
        "receipt": receipt,
    }


def _approve(args: argparse.Namespace) -> dict[str, Any]:
    repo, store = _store(args.repo, args.run_id)
    with store.run_locked():
        kernel = Kernel(store.load())
        if args.wiki_sync:
            if not (args.ticket and args.head_sha):
                raise TransitionError(
                    "--wiki-sync requires --ticket and --head-sha"
                )
            if args.external_merge or args.gate_id:
                raise TransitionError(
                    "wiki-sync approval cannot target a gate or external merge"
                )
            kernel.preflight_mutation_boundary(args.ticket, "wiki:approve-sync")
            record = approve_wiki_sync(
                repo,
                store,
                kernel,
                args.ticket,
                actor=args.actor,
                head_sha=args.head_sha,
                evidence=args.evidence,
                runner=getattr(args, "_command_runner", None),
            )
            return {
                **kernel.report(),
                "approved": {
                    "kind": "wiki-sync-merge",
                    "ticket": args.ticket,
                    "head_sha": args.head_sha,
                    "wiki_sync": record,
                },
            }
        if args.head_sha or args.ticket:
            if not (args.head_sha and args.ticket):
                raise TransitionError("--ticket and --head-sha must be supplied together")
            _mutation_boundary(kernel, args.ticket, "approve:merge")
            if args.external_merge:
                mode = "external"
                outcome = _complete_external_merge(
                    kernel,
                    args.ticket,
                    actor=args.actor,
                    head_sha=args.head_sha,
                    evidence=args.evidence,
                    runner=getattr(args, "_command_runner", None),
                )
            else:
                provider = detect_provider("", override=kernel.ledger["provider"])
                provider.negotiate({MERGE_EXPECTED_HEAD})
                mode = "runner"
                outcome = _drive_runner_merge(
                    store,
                    kernel,
                    args.ticket,
                    actor=args.actor,
                    head_sha=args.head_sha,
                    evidence=args.evidence,
                    runner=getattr(args, "_command_runner", None),
                )
            approved = {
                "kind": "merge",
                "ticket": args.ticket,
                "head_sha": args.head_sha,
                "mode": mode,
                **outcome,
            }
        else:
            if not args.gate_id:
                raise TransitionError("gate ID is required for non-merge approval")
            kernel.approve_gate(args.gate_id, actor=args.actor, evidence=args.evidence)
            approved = {"kind": "gate", "gate_id": args.gate_id}
        store.save(kernel.ledger)
        wiki_sync = drive_post_integration_sync(
            repo,
            store,
            kernel,
            runner=getattr(args, "_command_runner", None),
            boundary_guard=lambda ticket_id, boundary: _mutation_boundary(
                kernel, ticket_id, boundary
            ),
        )
        return {
            **kernel.report(),
            "approved": approved,
            "post_integration": wiki_sync,
        }


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
        for ticket_id in kernel.ledger["ticket_order"]:
            kernel.preflight_mutation_boundary(ticket_id, "worktree:cleanup")
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
        with os.fdopen(
            descriptor, "w", encoding="utf-8", newline="\n"
        ) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _ticket_parse(args: argparse.Namespace) -> dict[str, Any]:
    target = Path(args.ticket).resolve()
    parsed = parse_ticket_markdown(
        read_ticket_text(target),
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


def _runner_defect_issue_grant(args: argparse.Namespace) -> dict[str, Any]:
    repo = repository_root(Path(args.repo))
    assert_target_repository(repo)
    grant = PublicationAuthority(repo).grant(
        actor=args.actor,
        evidence=args.evidence,
    )
    return {"grant": grant, "mutation_scope": "runner-defect-publication-authority"}


def _runner_defect_issue_revoke(args: argparse.Namespace) -> dict[str, Any]:
    repo = repository_root(Path(args.repo))
    assert_target_repository(repo)
    revocation = PublicationAuthority(repo).revoke(
        authority_id=args.authority_id,
        actor=args.actor,
        evidence=args.evidence,
    )
    return {
        "revocation": revocation,
        "mutation_scope": "runner-defect-publication-authority",
    }


def _runner_defect_issue_status(args: argparse.Namespace) -> dict[str, Any]:
    repo = repository_root(Path(args.repo))
    assert_target_repository(repo)
    return PublicationAuthority(repo).inspect()


def _runner_defect_issue_escalate(args: argparse.Namespace) -> dict[str, Any]:
    repo = repository_root(Path(args.repo))
    assert_target_repository(repo)
    try:
        record = json.loads(Path(args.record).read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        raise RunnerDefectError("runner-defect record must be UTF-8") from error
    authority = PublicationAuthority(repo)
    with protected_run_ledger(repo, args.run_id, record) as (normalized, _ledger, digest):
        if args.dry_run:
            result = RunnerDefectEscalator(
                authority,
                IssueOutbox(repo),
                adapter=None,
            ).dry_run(normalized)
        else:
            remote = origin_url(repo) or ""
            provider = detect_provider(remote)
            provider.negotiate(RUNNER_DEFECT_ISSUE_CAPABILITIES)
            executor = ProviderExecutor(
                provider,
                cwd=repo,
                mode="live",
                runner=args._command_runner,
            )
            result = RunnerDefectEscalator(
                authority,
                IssueOutbox(repo),
                GitHubIssueAdapter(executor),
            ).escalate(normalized)
    return {
        **asdict(result),
        "run_id": args.run_id,
        "protected_run_ledger_sha256": digest,
        "dry_run": bool(args.dry_run),
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
    plan.add_argument("--base", default="HEAD")
    plan.add_argument(
        "--merge-policy", choices=("manual", "autonomous"), default="manual"
    )
    plan.add_argument("--merge-actor")
    plan.add_argument("--merge-evidence")
    plan.add_argument(
        "--wiki-sync-merge-policy",
        choices=("manual", "autonomous"),
        default="manual",
    )
    plan.add_argument("--wiki-sync-merge-actor")
    plan.add_argument("--wiki-sync-merge-evidence")
    plan.add_argument(
        "--final-tree-mode",
        choices=PROJECTION_MODES,
        default=DEFAULT_PROJECTION_MODE,
    )
    plan.set_defaults(handler=_plan)

    bootstrap = commands.add_parser(
        "bootstrap-private-github",
        help="create or adopt one exact private GitHub repository and publish its base",
    )
    bootstrap.add_argument("--repo", required=True)
    bootstrap.add_argument("--target", required=True)
    bootstrap.add_argument("--visibility", choices=("private",), required=True)
    bootstrap.add_argument("--base", required=True)
    bootstrap.add_argument("--base-sha", required=True)
    bootstrap.add_argument("--actor", required=True)
    bootstrap.add_argument("--evidence", required=True)
    bootstrap.set_defaults(handler=_bootstrap_private_github)

    prepare_zero = commands.add_parser(
        "prepare-zero-to-autopilot",
        help="write a provider-free exact initial inventory outside the source directory",
    )
    prepare_zero.add_argument("--repo", required=True)
    prepare_zero.add_argument("--target", required=True)
    prepare_zero.add_argument("--visibility", choices=("private",), required=True)
    prepare_zero.add_argument("--base", required=True)
    prepare_zero.add_argument("--output", required=True)
    prepare_zero.add_argument("--exclude", action="append", default=[])
    prepare_zero.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    prepare_zero.add_argument(
        "--max-total-bytes", type=int, default=DEFAULT_MAX_TOTAL_BYTES
    )
    prepare_zero.set_defaults(handler=_prepare_zero_to_autopilot)

    zero = commands.add_parser(
        "zero-to-autopilot",
        help="initialize or prove one exact local base and bootstrap one private repository",
    )
    zero.add_argument("--repo", required=True)
    zero.add_argument("--target", required=True)
    zero.add_argument("--visibility", choices=("private",), required=True)
    zero.add_argument("--base", required=True)
    zero.add_argument("--base-sha")
    zero.add_argument("--inventory", required=True)
    zero.add_argument("--inventory-sha256", required=True)
    zero.add_argument("--actor", required=True)
    zero.add_argument("--evidence", required=True)
    zero.set_defaults(handler=_zero_to_autopilot)

    zero_status = commands.add_parser(
        "zero-to-autopilot-status",
        help="inspect the local zero-bootstrap transaction without provider mutation",
    )
    zero_status.add_argument("--repo", required=True)
    zero_status.set_defaults(handler=_zero_to_autopilot_status)

    repository_grant = commands.add_parser(
        "grant-repository-autonomous-merge",
        help="grant autonomous merge authority across current and future runs",
    )
    repository_grant.add_argument("--repo", required=True)
    repository_grant.add_argument(
        "--scope", choices=(AUTHORITY_SCOPE,), required=True
    )
    repository_grant.add_argument("--actor", required=True)
    repository_grant.add_argument("--evidence", required=True)
    repository_grant.set_defaults(handler=_grant_repository_autonomous_merge)

    repository_revoke = commands.add_parser(
        "revoke-repository-autonomous-merge",
        help="revoke the repository-wide autonomous merge grant",
    )
    repository_revoke.add_argument("--repo", required=True)
    repository_revoke.add_argument("--actor", required=True)
    repository_revoke.add_argument("--evidence", required=True)
    repository_revoke.set_defaults(handler=_revoke_repository_autonomous_merge)

    repository_merge_status = commands.add_parser(
        "repository-autonomous-merge-status",
        help="inspect repository-wide autonomous merge authority",
    )
    repository_merge_status.add_argument("--repo", required=True)
    repository_merge_status.set_defaults(handler=_repository_autonomous_merge_status)

    reconciliation_grant = commands.add_parser(
        "grant-repository-autonomous-reconciliation",
        help="grant exact proposal-bound reconciliation across current and future runs",
    )
    reconciliation_grant.add_argument("--repo", required=True)
    reconciliation_grant.add_argument(
        "--scope", choices=(RECONCILIATION_AUTHORITY_SCOPE,), required=True
    )
    reconciliation_grant.add_argument("--actor", required=True)
    reconciliation_grant.add_argument("--evidence", required=True)
    reconciliation_grant.set_defaults(
        handler=_grant_repository_autonomous_reconciliation
    )

    reconciliation_revoke = commands.add_parser(
        "revoke-repository-autonomous-reconciliation",
        help="revoke repository-wide autonomous reconciliation authority",
    )
    reconciliation_revoke.add_argument("--repo", required=True)
    reconciliation_revoke.add_argument("--actor", required=True)
    reconciliation_revoke.add_argument("--evidence", required=True)
    reconciliation_revoke.set_defaults(
        handler=_revoke_repository_autonomous_reconciliation
    )

    reconciliation_status = commands.add_parser(
        "repository-autonomous-reconciliation-status",
        help="inspect repository-wide autonomous reconciliation authority",
    )
    reconciliation_status.add_argument("--repo", required=True)
    reconciliation_status.set_defaults(
        handler=_repository_autonomous_reconciliation_status
    )

    migrate_authority = commands.add_parser(
        "migrate-repository-authority",
        help="explicitly migrate one exact schema-1 repository authority to schema 2",
    )
    migrate_authority.add_argument("--repo", required=True)
    migrate_authority.add_argument(
        "--kind", choices=("merge", "reconciliation"), required=True
    )
    migrate_authority.add_argument("--expected-state-sha256", required=True)
    migrate_authority.add_argument("--actor", required=True)
    migrate_authority.add_argument("--evidence", required=True)
    migrate_authority.set_defaults(handler=_migrate_repository_authority)

    merge_all = commands.add_parser(
        "merge-all",
        help="merge every independently eligible PR under repository authority",
    )
    merge_all.add_argument("--repo", required=True)
    merge_all.set_defaults(handler=_merge_all)

    sync_local_pi = commands.add_parser(
        "sync-local-pi",
        help="synchronize one durably integrated agent-skills ticket into local Pi",
    )
    sync_local_pi.add_argument("run_id")
    sync_local_pi.add_argument("--repo", default=".")
    sync_local_pi.add_argument("--ticket", required=True)
    sync_local_pi.add_argument("--checkout", required=True)
    sync_local_pi.add_argument("--agents-root", required=True)
    sync_local_pi.add_argument("--pi-settings", required=True)
    sync_local_pi.add_argument("--actor", required=True)
    sync_local_pi.add_argument("--evidence", required=True)
    sync_local_pi.add_argument("--adopt-existing-owned", action="store_true")
    sync_local_pi.add_argument("--replace-package-source", action="store_true")
    sync_local_pi.add_argument("--migrate-owned-source-from")
    sync_local_pi.add_argument(
        "--replace-drifted-owned",
        action="append",
        default=[],
        metavar="NAME=SHA256",
    )
    sync_local_pi.set_defaults(handler=_sync_local_pi)

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
    run.add_argument(
        "--merge-policy", choices=("manual", "autonomous"), default="manual"
    )
    run.add_argument("--merge-actor")
    run.add_argument("--merge-evidence")
    run.add_argument(
        "--wiki-sync-merge-policy",
        choices=("manual", "autonomous"),
        default="manual",
    )
    run.add_argument("--wiki-sync-merge-actor")
    run.add_argument("--wiki-sync-merge-evidence")
    run.add_argument(
        "--final-tree-mode",
        choices=PROJECTION_MODES,
        default=DEFAULT_PROJECTION_MODE,
    )
    run.set_defaults(handler=_run)

    owner_adopt = commands.add_parser(
        "worktree-owner-adopt",
        help="adopt one exact legacy runner worktree without cleanup authority",
    )
    owner_adopt.add_argument("run_id")
    owner_adopt.add_argument("--repo", default=".")
    owner_adopt.add_argument("--expected-ledger-sha256", required=True)
    owner_adopt.add_argument("--actor", required=True)
    owner_adopt.add_argument("--evidence", required=True)
    owner_adopt.set_defaults(handler=_worktree_owner_adopt)

    gc_plan = commands.add_parser(
        "worktree-gc-plan",
        help="persist a provider-free exact plan for owned orphan worktrees",
    )
    gc_plan.add_argument("--repo", default=".")
    gc_plan.add_argument("--protect", action="append", default=[])
    gc_plan.set_defaults(handler=_worktree_gc_plan)

    gc_apply = commands.add_parser(
        "worktree-gc-apply",
        help="apply one exact provider-free cleanup plan with durable replay",
    )
    gc_apply.add_argument("plan_path")
    gc_apply.add_argument("--repo", default=".")
    gc_apply.add_argument("--expected-plan-sha256", required=True)
    gc_apply.add_argument("--actor", required=True)
    gc_apply.add_argument("--evidence", required=True)
    gc_apply.set_defaults(handler=_worktree_gc_apply)

    for name, handler in (("resume", _resume), ("status", _status)):
        command = commands.add_parser(name)
        command.add_argument("run_id")
        command.add_argument("--repo", default=".")
        if name == "resume":
            command.add_argument("--events")
        command.set_defaults(handler=handler)

    wiki_retry_status = commands.add_parser(
        "wiki-delivery-retry-status",
        help="inspect exact provider-free eligibility for one terminal wiki delivery retry",
    )
    wiki_retry_status.add_argument("run_id")
    wiki_retry_status.add_argument("--repo", default=".")
    wiki_retry_status.add_argument("--ticket", required=True)
    wiki_retry_status.set_defaults(handler=_wiki_delivery_retry_status)

    retry_wiki = commands.add_parser(
        "retry-wiki-delivery",
        help="prepare one exact terminal pre-provider wiki delivery for ordinary resume",
    )
    retry_wiki.add_argument("run_id")
    retry_wiki.add_argument("--repo", default=".")
    retry_wiki.add_argument("--ticket", required=True)
    retry_wiki.add_argument("--expected-record-sha256", required=True)
    retry_wiki.add_argument("--actor", required=True)
    retry_wiki.add_argument("--evidence", required=True)
    retry_wiki.set_defaults(handler=_retry_wiki_delivery)

    prepare_legacy = commands.add_parser(
        "prepare-legacy-recovery",
        help="prepare a provider-free exact legacy-ledger action manifest",
    )
    prepare_legacy.add_argument("--repo", default=".")
    prepare_legacy.add_argument("--inventory", required=True)
    prepare_legacy.add_argument("--output", required=True)
    prepare_legacy.set_defaults(handler=_prepare_legacy_recovery)

    apply_legacy = commands.add_parser(
        "apply-legacy-recovery",
        help="apply one exact authority-bound legacy-ledger manifest",
    )
    apply_legacy.add_argument("--repo", default=".")
    apply_legacy.add_argument("--manifest", required=True)
    apply_legacy.add_argument("--manifest-sha256", required=True)
    apply_legacy.add_argument("--actor", required=True)
    apply_legacy.add_argument("--evidence", required=True)
    apply_legacy.set_defaults(handler=_apply_legacy_recovery)

    legacy_status = commands.add_parser(
        "legacy-recovery-status",
        help="read back exact migrated, retired, failed, and untouched state",
    )
    legacy_status.add_argument("--repo", default=".")
    legacy_status.add_argument("--manifest", required=True)
    legacy_status.add_argument("--manifest-sha256", required=True)
    legacy_status.set_defaults(handler=_legacy_recovery_status)

    revoke_retirement = commands.add_parser(
        "revoke-legacy-retirement",
        help="append an exact legacy-run retirement revocation",
    )
    revoke_retirement.add_argument("run_id")
    revoke_retirement.add_argument("--repo", default=".")
    revoke_retirement.add_argument("--actor", required=True)
    revoke_retirement.add_argument("--evidence", required=True)
    revoke_retirement.add_argument("--reason", required=True)
    revoke_retirement.set_defaults(handler=_revoke_legacy_retirement)

    migrate_run = commands.add_parser("migrate-run-lifecycle")
    migrate_run.add_argument("run_id")
    migrate_run.add_argument("--repo", default=".")
    migrate_run.add_argument("--manifest", required=True)
    migrate_run.add_argument("--manifest-sha256", required=True)
    migrate_run.add_argument("--actor", required=True)
    migrate_run.add_argument("--evidence", required=True)
    migrate_run.set_defaults(handler=_migrate_run_lifecycle)

    compact_run = commands.add_parser("compact-run-ledger")
    compact_run.add_argument("run_id")
    compact_run.add_argument("--repo", default=".")
    compact_run.set_defaults(handler=_compact_run_ledger)

    for name, handler in (("pause", _pause), ("unpause", _unpause)):
        command = commands.add_parser(name)
        command.add_argument("run_id")
        command.add_argument("--repo", default=".")
        command.add_argument("--actor", required=True)
        command.add_argument("--reason", required=True)
        command.set_defaults(handler=handler)

    grant_autonomous_merge = commands.add_parser(
        "grant-autonomous-merge",
        help="add one immutable autonomous merge grant to a non-terminal manual run",
    )
    grant_autonomous_merge.add_argument("run_id")
    grant_autonomous_merge.add_argument("--repo", default=".")
    grant_autonomous_merge.add_argument("--actor", required=True)
    grant_autonomous_merge.add_argument("--evidence", required=True)
    grant_autonomous_merge.set_defaults(handler=_grant_autonomous_merge)

    grant_completion_projection = commands.add_parser(
        "grant-completion-projection",
        help="grant one exact tracked done-path projection to an ignored-source ticket",
    )
    grant_completion_projection.add_argument("run_id")
    grant_completion_projection.add_argument("--repo", default=".")
    grant_completion_projection.add_argument("--ticket", required=True)
    grant_completion_projection.add_argument("--expected-tree", required=True)
    grant_completion_projection.add_argument("--actor", required=True)
    grant_completion_projection.add_argument("--evidence", required=True)
    grant_completion_projection.set_defaults(handler=_grant_completion_projection)

    approve = commands.add_parser("approve")
    approve.add_argument("run_id")
    approve.add_argument("gate_id", nargs="?")
    approve.add_argument("--repo", default=".")
    approve.add_argument("--actor", required=True)
    approve.add_argument("--evidence", required=True)
    approve.add_argument("--ticket")
    approve.add_argument("--head-sha")
    approve.add_argument("--external-merge", action="store_true")
    approve.add_argument("--wiki-sync", action="store_true")
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

    ticket_list = commands.add_parser("ticket-list")
    ticket_list.add_argument("root", nargs="?", default=".")
    ticket_list.add_argument("--state", choices=INVENTORY_STATES)
    ticket_list.add_argument("--json", action="store_true")
    ticket_list.set_defaults(handler=_ticket_list)

    issue_grant = commands.add_parser(
        "runner-defect-issue-grant",
        help="register exact repository-scoped issue-publication authority",
    )
    issue_grant.add_argument("--repo", default=".")
    issue_grant.add_argument("--actor", required=True)
    issue_grant.add_argument("--evidence", required=True)
    issue_grant.set_defaults(handler=_runner_defect_issue_grant)

    issue_revoke = commands.add_parser(
        "runner-defect-issue-revoke",
        help="revoke the exact active runner-defect publication grant",
    )
    issue_revoke.add_argument("authority_id")
    issue_revoke.add_argument("--repo", default=".")
    issue_revoke.add_argument("--actor", required=True)
    issue_revoke.add_argument("--evidence", required=True)
    issue_revoke.set_defaults(handler=_runner_defect_issue_revoke)

    issue_status = commands.add_parser(
        "runner-defect-issue-status",
        help="inspect repository-scoped runner-defect publication authority",
    )
    issue_status.add_argument("--repo", default=".")
    issue_status.set_defaults(handler=_runner_defect_issue_status)

    issue_escalate = commands.add_parser(
        "runner-defect-issue-escalate",
        help="validate and optionally publish one eligible runner defect",
    )
    issue_escalate.add_argument("run_id")
    issue_escalate.add_argument("record")
    issue_escalate.add_argument("--repo", default=".")
    issue_escalate.add_argument("--dry-run", action="store_true")
    issue_escalate.set_defaults(handler=_runner_defect_issue_escalate)

    artifact_audit = commands.add_parser("artifact-audit")
    artifact_audit.add_argument("root", nargs="?", default=".")
    artifact_audit.add_argument("--json", action="store_true")
    artifact_audit.set_defaults(handler=_artifact_audit)

    context_budget = commands.add_parser("context-budget")
    context_budget.add_argument("root", nargs="?", default=".")
    context_budget.add_argument("--install-root")
    workflow = context_budget.add_mutually_exclusive_group()
    workflow.add_argument("--workflow", default=DEFAULT_WORKFLOW)
    workflow.add_argument("--no-workflow", action="store_true")
    context_budget.add_argument("--ceiling-config")
    context_budget.add_argument("--check-ceiling", action="store_true")
    context_budget.add_argument("--json", action="store_true")
    context_budget.set_defaults(handler=_context_budget)

    for name, handler in (
        ("ticket-hold", _ticket_hold),
        ("ticket-cancel", _ticket_cancel),
    ):
        lifecycle = commands.add_parser(name)
        lifecycle.add_argument("run_id")
        lifecycle.add_argument("ticket_id")
        lifecycle.add_argument("--repo", default=".")
        lifecycle.add_argument("--actor", required=True)
        lifecycle.add_argument("--reason", required=True)
        lifecycle.add_argument("--authority-ref", required=True)
        lifecycle.set_defaults(handler=handler)

    reopen_request = commands.add_parser("ticket-reopen-request")
    reopen_request.add_argument("run_id")
    reopen_request.add_argument("ticket_id")
    reopen_request.add_argument("--repo", default=".")
    reopen_request.add_argument("--actor", required=True)
    reopen_request.add_argument("--reason", required=True)
    reopen_request.set_defaults(handler=_ticket_reopen_request)

    reopen = commands.add_parser("ticket-reopen")
    reopen.add_argument("run_id")
    reopen.add_argument("ticket_id")
    reopen.add_argument("gate_id")
    reopen.add_argument("--repo", default=".")
    reopen.set_defaults(handler=_ticket_reopen)

    status_change = commands.add_parser(
        "status-change-transaction",
        help="run one repository-owned administrative disposition transaction",
    )
    status_change.add_argument("ticket_source")
    status_change.add_argument("--repo", default=".")
    status_change.add_argument("--ticket-id", required=True)
    status_change.add_argument("--artifact-id", required=True)
    status_change.add_argument("--ticket-digest", required=True)
    status_change.add_argument(
        "--from-disposition",
        choices=("open", "on-hold", "canceled", "completed"),
        required=True,
    )
    status_change.add_argument(
        "--to-disposition", choices=("open", "on-hold", "canceled"), required=True
    )
    status_change.add_argument(
        "--source-mode", choices=("tracked", "ignored"), required=True
    )
    status_change.add_argument("--actor", required=True)
    status_change.add_argument("--reason", required=True)
    status_change.add_argument("--authority-ref", required=True)
    status_change.add_argument("--reopen-gate-id")
    status_change.add_argument("--base", default="main")
    status_change.set_defaults(handler=_status_change_transaction)

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
    _configure_utf8_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    args._command_runner = command_runner
    command = args.command
    try:
        data = args.handler(args)
    except (
        ContractError,
        ContextBudgetError,
        GitError,
        LifecycleError,
        json.JSONDecodeError,
        LedgerError,
        ProviderError,
        RepositoryBootstrapError,
        RepositoryMergeAuthorityError,
        RepositoryReconciliationAuthorityError,
        ZeroToAutopilotError,
        PiSyncError,
        RunnerDefectError,
        TransitionError,
        WorktreeGCError,
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
    if command == "ticket-list" and not args.json:
        print(render_ticket_inventory(data), end="")
    elif command == "artifact-audit" and not args.json:
        print(render_artifact_audit(data), end="")
    elif command == "context-budget" and not args.json:
        print(render_context_budget(data), end="")
    else:
        _emit(_response(command, True, data=data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
