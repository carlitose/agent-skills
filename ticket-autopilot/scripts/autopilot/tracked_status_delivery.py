"""Isolated tracked delivery for repository-owned ticket status transactions.

This module owns only the Git/provider/terminal vertical slice. Administrative intent and
run ownership remain in :mod:`status_transaction`; provider merge authority and terminal
reachability remain separate imported contracts.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, ContextManager, Mapping, Protocol

from .git_ops import GitError, origin_url, repository_root, run_git
from .link_repoint import DOCUMENT_ROOT, FROZEN_PREFIX, _repoint_text
from .providers import (
    CREATE_OR_UPDATE_PR,
    GET_APPROVALS,
    GET_CHECKS_AND_POLICIES,
    GET_PR_FOR_BRANCH,
    GET_PR_STATE,
    MERGE_WITH_EXPECTED_HEAD,
    MergeAuthorization,
    ProviderError,
    ProviderExecutor,
    detect_provider,
)
from .repository_merge_authority import (
    RepositoryMergeAuthorityError,
    RepositoryMergeAuthorityStore,
)
from .terminal_integration import (
    TerminalIntegrationError,
    build_terminal_integration_proof,
)
from .ticket_contract import ticket_source_digest
from .ticket_lifecycle import LifecycleError, transition_ticket_source


class TrackedStatusDeliveryError(RuntimeError):
    """A tracked administrative candidate or exact delivery readback is unsafe."""


class StatusProviderExecutor(Protocol):
    provider: Any

    def execute(self, operation: str, **parameters: Any) -> dict[str, Any]: ...


EventRecorder = Callable[[str, Mapping[str, Any]], None]
Checkpoint = Callable[[str], None] | None
Projection = Callable[[Mapping[str, Any], str], None]
MergeGuardFactory = Callable[[], ContextManager[Mapping[str, Any] | None]]

_OID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_RAW = re.compile(
    r"^:([0-7]{6}) ([0-7]{6}) ([0-9a-f]{40,64}) ([0-9a-f]{40,64}) ([A-Z])$"
)
_ZERO_OIDS = {"0" * 40, "0" * 64}
_PENDING_BUCKETS = {"pending", "queued", "in_progress", "waiting"}
_FAILED_BUCKETS = {"fail", "failed", "cancel", "cancelled", "canceled", "error"}
_PASS_BUCKETS = {"pass", "passed", "success", "successful", "skipping", "skipped"}


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _checkpoint(checkpoint: Checkpoint, phase: str) -> None:
    if checkpoint is not None:
        checkpoint(phase)


def _event(document: Mapping[str, Any], name: str) -> Mapping[str, Any] | None:
    for item in reversed(document["history"]):
        if item["event"] == name:
            return item["details"]
    return None


def _phase(document: Mapping[str, Any]) -> str:
    return str(document["history"][-1]["event"])


def _git_bytes(cwd: Path, *arguments: str, env: Mapping[str, str] | None = None) -> bytes:
    process_env = os.environ.copy()
    process_env["GIT_NO_REPLACE_OBJECTS"] = "1"
    if env:
        process_env.update(env)
    result = subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=cwd,
        env=process_env,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise TrackedStatusDeliveryError(
            detail or f"git {' '.join(arguments)} failed"
        )
    return result.stdout


def _git_text(cwd: Path, *arguments: str, env: Mapping[str, str] | None = None) -> str:
    try:
        return _git_bytes(cwd, *arguments, env=env).decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise TrackedStatusDeliveryError("Git identity output is not UTF-8") from error


def _refresh_target(repository: Path, branch: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,199}", branch):
        raise TrackedStatusDeliveryError("target branch is unsafe")
    result = subprocess.run(
        [
            "git",
            "fetch",
            "--no-tags",
            "--no-write-fetch-head",
            "origin",
            f"+refs/heads/{branch}:refs/remotes/origin/{branch}",
        ],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise TrackedStatusDeliveryError(detail or "target branch refresh failed")


def _target(repository: Path, branch: str) -> tuple[str, str]:
    for reference in (f"refs/remotes/origin/{branch}", f"refs/heads/{branch}"):
        result = subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "rev-parse",
                "--verify",
                f"{reference}^{{commit}}",
            ],
            cwd=repository,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
        )
        sha = result.stdout.strip()
        if result.returncode == 0 and _OID.fullmatch(sha):
            return reference, sha
    raise TrackedStatusDeliveryError(f"target branch {branch!r} is unavailable")


def _effective_target(document: Mapping[str, Any]) -> tuple[str, str]:
    refreshed = _event(document, "target-refreshed")
    if refreshed is not None:
        return str(refreshed["target_ref"]), str(refreshed["target_sha"])
    request = document["request"]
    return str(request["target_ref"]), str(request["target_sha"])


def _ticket_blob_matches(
    repository: Path, target_sha: str, source_relative: str, expected_digest: str
) -> bool:
    result = subprocess.run(
        ["git", "--no-replace-objects", "show", f"{target_sha}:{source_relative}"],
        cwd=repository,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
    )
    return result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected_digest


def _safe_state_directory(root: Path, path: Path) -> None:
    try:
        relative = path.relative_to(root)
        path.resolve(strict=False).relative_to(root.resolve())
    except ValueError as error:
        raise TrackedStatusDeliveryError("tracked status state escapes transaction state") from error
    current = root
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise TrackedStatusDeliveryError("tracked status state contains a symbolic link")


def _admin_worktree(repository: Path, transaction_id: str, parent_sha: str) -> Path:
    parent = repository.parent / f".{repository.name}-status-worktrees"
    worktree = parent / transaction_id
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        raise TrackedStatusDeliveryError("status worktree parent is unsafe")
    parent.mkdir(parents=True, exist_ok=True)
    if worktree.exists():
        if worktree.is_symlink() or not worktree.is_dir():
            raise TrackedStatusDeliveryError("status worktree is unsafe")
        try:
            if repository_root(worktree) != worktree.resolve():
                raise TrackedStatusDeliveryError("status worktree identity is contradictory")
        except GitError as error:
            raise TrackedStatusDeliveryError(str(error)) from error
        return worktree.resolve()
    try:
        run_git(repository, "worktree", "add", "--detach", str(worktree), parent_sha)
    except GitError as error:
        raise TrackedStatusDeliveryError(str(error)) from error
    if repository_root(worktree) != worktree.resolve():
        raise TrackedStatusDeliveryError("Git created an unexpected status worktree")
    return worktree.resolve()


def _status_paths(worktree: Path) -> set[str]:
    raw = _git_bytes(worktree, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    fields = raw.split(b"\0")
    paths: set[str] = set()
    index = 0
    while index < len(fields):
        field = fields[index]
        index += 1
        if not field:
            continue
        if len(field) < 4 or field[2:3] != b" ":
            raise TrackedStatusDeliveryError("status worktree porcelain is malformed")
        try:
            path = field[3:].decode("utf-8")
        except UnicodeDecodeError as error:
            raise TrackedStatusDeliveryError("status path is not UTF-8") from error
        paths.add(path)
        if field[:1] in {b"R", b"C"} or field[1:2] in {b"R", b"C"}:
            if index >= len(fields) or not fields[index]:
                raise TrackedStatusDeliveryError("status rename entry is malformed")
            try:
                paths.add(fields[index].decode("utf-8"))
            except UnicodeDecodeError as error:
                raise TrackedStatusDeliveryError("status path is not UTF-8") from error
            index += 1
    return paths


def _raw_changes(worktree: Path, parent: str, candidate_tree: str) -> list[dict[str, Any]]:
    raw = _git_bytes(
        worktree,
        "diff",
        "--raw",
        "--full-index",
        "--no-abbrev",
        "--no-renames",
        "-z",
        parent,
        candidate_tree,
    )
    fields = raw.split(b"\0")
    changes: list[dict[str, Any]] = []
    index = 0
    while index < len(fields):
        header = fields[index]
        index += 1
        if not header:
            continue
        try:
            match = _RAW.fullmatch(header.decode("ascii"))
        except UnicodeDecodeError as error:
            raise TrackedStatusDeliveryError("raw Git transition is malformed") from error
        if match is None or index >= len(fields) or not fields[index]:
            raise TrackedStatusDeliveryError("raw Git transition is malformed")
        try:
            path = fields[index].decode("utf-8")
        except UnicodeDecodeError as error:
            raise TrackedStatusDeliveryError("raw Git path is not UTF-8") from error
        index += 1
        old_mode, new_mode, old_blob, new_blob, status = match.groups()
        if old_mode in {"120000", "160000"} or new_mode in {"120000", "160000"}:
            raise TrackedStatusDeliveryError("status candidate contains a symlink or submodule")
        old_bytes = None if old_blob in _ZERO_OIDS else hashlib.sha256(
            _git_bytes(worktree, "cat-file", "blob", old_blob)
        ).hexdigest()
        new_bytes = None if new_blob in _ZERO_OIDS else hashlib.sha256(
            _git_bytes(worktree, "cat-file", "blob", new_blob)
        ).hexdigest()
        changes.append(
            {
                "path": path,
                "status": status,
                "old_mode": old_mode,
                "new_mode": new_mode,
                "old_blob": old_blob,
                "new_blob": new_blob,
                "old_bytes_sha256": old_bytes,
                "new_bytes_sha256": new_bytes,
            }
        )
    return changes


def _apply_exact_repoints(
    worktree: Path, parent_sha: str, old_path: str, new_path: str
) -> list[str]:
    raw_paths = _git_bytes(
        worktree,
        "ls-tree",
        "-r",
        "--name-only",
        "-z",
        parent_sha,
        "--",
        DOCUMENT_ROOT,
    )
    repointed: list[str] = []
    for raw_path in raw_paths.split(b"\0"):
        if not raw_path:
            continue
        try:
            relative = raw_path.decode("utf-8")
        except UnicodeDecodeError as error:
            raise TrackedStatusDeliveryError("documentation path is not UTF-8") from error
        if not relative.endswith(".md") or relative.startswith(FROZEN_PREFIX):
            continue
        original = _git_bytes(worktree, "show", f"{parent_sha}:{relative}")
        text = original.decode("utf-8", errors="replace")
        rewritten, changed = _repoint_text(relative, text, old_path, new_path)
        if not changed:
            continue
        expected = rewritten.encode("utf-8")
        path = worktree / relative
        if path.is_symlink() or not path.is_file():
            raise TrackedStatusDeliveryError("repoint source is not a regular file")
        observed = path.read_bytes()
        if observed not in {original, expected}:
            raise TrackedStatusDeliveryError("repoint source contains unexpected content")
        if observed != expected:
            path.write_bytes(expected)
        repointed.append(relative)
    return sorted(repointed)


def _freeze_candidate(
    worktree: Path,
    parent_sha: str,
    allowed_paths: set[str],
    *,
    old_path: str,
    new_path: str,
    expected_digest: str,
) -> dict[str, Any]:
    if _git_text(worktree, "ls-files", "--unmerged"):
        raise TrackedStatusDeliveryError("status candidate contains conflict stages")
    observed = _status_paths(worktree)
    if observed != allowed_paths:
        raise TrackedStatusDeliveryError(
            "status candidate changed paths differ from the exact allowlist"
        )
    for relative in sorted(allowed_paths - {old_path}):
        path = worktree / relative
        if path.is_symlink() or not path.is_file():
            raise TrackedStatusDeliveryError("status candidate path is not a regular file")
    run_git(worktree, "add", "-A", "--", *sorted(allowed_paths))
    if _status_paths(worktree) != allowed_paths:
        raise TrackedStatusDeliveryError("staged status candidate changed unexpectedly")
    candidate_tree = _git_text(worktree, "write-tree")
    parent_tree = _git_text(worktree, "rev-parse", f"{parent_sha}^{{tree}}")
    changes = _raw_changes(worktree, parent_sha, candidate_tree)
    if {item["path"] for item in changes} != allowed_paths:
        raise TrackedStatusDeliveryError("raw status candidate differs from the allowlist")
    by_path = {item["path"]: item for item in changes}
    if by_path.get(old_path, {}).get("status") != "D":
        raise TrackedStatusDeliveryError("status candidate did not delete the original path")
    if by_path.get(new_path, {}).get("status") != "A":
        raise TrackedStatusDeliveryError("status candidate did not add the destination path")
    if by_path[new_path]["new_bytes_sha256"] != expected_digest:
        raise TrackedStatusDeliveryError("status candidate destination bytes drifted")
    if by_path[old_path]["old_bytes_sha256"] != expected_digest:
        raise TrackedStatusDeliveryError("status candidate source bytes drifted")
    for relative in allowed_paths - {old_path, new_path}:
        if by_path[relative]["status"] != "M":
            raise TrackedStatusDeliveryError("status candidate repoint is not a modification")
    return {
        "schema": 1,
        "parent_sha": parent_sha,
        "parent_tree_oid": parent_tree,
        "candidate_tree_oid": candidate_tree,
        "allowed_paths": sorted(allowed_paths),
        "changes": changes,
        "raw_transition_sha256": _digest(changes),
    }


def _validate_candidate_evidence(
    worktree: Path,
    parent_sha: str,
    candidate: Mapping[str, Any],
    *,
    old_path: str,
    new_path: str,
    expected_digest: str,
) -> None:
    if set(candidate) != {
        "schema",
        "parent_sha",
        "parent_tree_oid",
        "candidate_tree_oid",
        "allowed_paths",
        "changes",
        "raw_transition_sha256",
    } or candidate.get("schema") != 1:
        raise TrackedStatusDeliveryError("tracked candidate evidence shape is invalid")
    if candidate.get("parent_sha") != parent_sha:
        raise TrackedStatusDeliveryError("tracked candidate parent is stale")
    for field in ("parent_tree_oid", "candidate_tree_oid"):
        value = candidate.get(field)
        if not isinstance(value, str) or not _OID.fullmatch(value):
            raise TrackedStatusDeliveryError("tracked candidate tree identity is malformed")
    allowed = candidate.get("allowed_paths")
    changes = candidate.get("changes")
    if (
        not isinstance(allowed, list)
        or not all(isinstance(path, str) and path for path in allowed)
        or allowed != sorted(set(allowed))
        or old_path not in allowed
        or new_path not in allowed
        or not isinstance(changes, list)
    ):
        raise TrackedStatusDeliveryError("tracked candidate allowlist is malformed")
    parent_tree = _git_text(worktree, "rev-parse", f"{parent_sha}^{{tree}}")
    if candidate["parent_tree_oid"] != parent_tree:
        raise TrackedStatusDeliveryError("tracked candidate parent tree is contradictory")
    object_type = _git_text(worktree, "cat-file", "-t", str(candidate["candidate_tree_oid"]))
    if object_type != "tree":
        raise TrackedStatusDeliveryError("tracked candidate object is not a tree")
    observed_changes = _raw_changes(
        worktree, parent_sha, str(candidate["candidate_tree_oid"])
    )
    if changes != observed_changes or candidate.get("raw_transition_sha256") != _digest(
        observed_changes
    ):
        raise TrackedStatusDeliveryError("tracked candidate raw transition is contradictory")
    if {change["path"] for change in observed_changes} != set(allowed):
        raise TrackedStatusDeliveryError("tracked candidate allowlist is contradictory")
    by_path = {change["path"]: change for change in observed_changes}
    if (
        by_path[old_path]["status"] != "D"
        or by_path[old_path]["old_bytes_sha256"] != expected_digest
        or by_path[new_path]["status"] != "A"
        or by_path[new_path]["new_bytes_sha256"] != expected_digest
    ):
        raise TrackedStatusDeliveryError("tracked candidate ticket transition is contradictory")


def _commit_identity(document: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    request = document["request"]
    transaction_id = str(document["transaction_id"])
    safe_ticket = re.sub(r"[^A-Za-z0-9._-]+", "-", str(request["ticket_id"])).strip("-")[:80]
    if not safe_ticket:
        raise TrackedStatusDeliveryError("ticket id cannot form a delivery branch")
    timestamp = 1_700_000_000 + (int(transaction_id[:8], 16) % 100_000_000)
    return {
        "schema": 1,
        "parent_sha": candidate["parent_sha"],
        "tree_oid": candidate["candidate_tree_oid"],
        "branch": f"ticket-autopilot/status-change/{safe_ticket}-{transaction_id[:12]}",
        "message": f"Status {request['ticket_id']}: {request['to_disposition']}",
        "author_name": "Ticket Autopilot",
        "author_email": "ticket-autopilot@example.invalid",
        "author_date": f"@{timestamp} +0000",
    }


def _create_or_read_commit(worktree: Path, intent: Mapping[str, Any]) -> dict[str, Any]:
    reference = f"refs/heads/{intent['branch']}"
    existing = subprocess.run(
        ["git", "--no-replace-objects", "rev-parse", "--verify", reference],
        cwd=worktree,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
    )
    commit_sha = existing.stdout.strip() if existing.returncode == 0 else None
    environment = {
        "GIT_AUTHOR_NAME": str(intent["author_name"]),
        "GIT_AUTHOR_EMAIL": str(intent["author_email"]),
        "GIT_AUTHOR_DATE": str(intent["author_date"]),
        "GIT_COMMITTER_NAME": str(intent["author_name"]),
        "GIT_COMMITTER_EMAIL": str(intent["author_email"]),
        "GIT_COMMITTER_DATE": str(intent["author_date"]),
    }
    expected_sha = _git_text(
        worktree,
        "commit-tree",
        str(intent["tree_oid"]),
        "-p",
        str(intent["parent_sha"]),
        "-m",
        str(intent["message"]),
        env=environment,
    )
    if commit_sha is None:
        try:
            run_git(worktree, "update-ref", reference, expected_sha, "0" * len(expected_sha))
        except GitError as error:
            raise TrackedStatusDeliveryError(str(error)) from error
        commit_sha = _git_text(worktree, "rev-parse", "--verify", reference)
    if commit_sha != expected_sha:
        raise TrackedStatusDeliveryError("status delivery branch points to another commit")
    parents = _git_text(worktree, "show", "-s", "--format=%P", commit_sha).split()
    tree = _git_text(worktree, "rev-parse", f"{commit_sha}^{{tree}}")
    if parents != [intent["parent_sha"]] or tree != intent["tree_oid"]:
        raise TrackedStatusDeliveryError("status commit parent or tree readback drifted")
    return {**dict(intent), "head_sha": commit_sha}


def _remote_head(worktree: Path, branch: str) -> str | None:
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}"],
        cwd=worktree,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise TrackedStatusDeliveryError(detail or "remote branch readback failed")
    lines = [line.split() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    if len(lines) != 1 or len(lines[0]) != 2 or not _OID.fullmatch(lines[0][0]):
        raise TrackedStatusDeliveryError("remote branch readback is ambiguous")
    return lines[0][0]


def _provider_body(document: Mapping[str, Any], head_sha: str) -> str:
    request = document["request"]
    return (
        "## Administrative status change\n\n"
        f"- Transaction: `{document['transaction_id']}`\n"
        f"- Ticket: `{request['ticket_id']}` / `{request['artifact_id']}`\n"
        f"- Disposition: `{request['from_disposition']}` → `{request['to_disposition']}`\n"
        f"- Actor: `{request['actor']}`\n"
        f"- Authority: `{request['authority_ref']}`\n"
        f"- Exact head: `{head_sha}`\n\n"
        f"Reason: {request['reason']}\n\n"
        "This PR changes administrative disposition only. It grants no ticket "
        "implementation, completion, issue, wiki, Pi-sync, or cleanup authority.\n"
    )


def _provider_name(executor: StatusProviderExecutor) -> str:
    name = getattr(getattr(executor, "provider", None), "name", None)
    if not isinstance(name, str) or not name:
        raise TrackedStatusDeliveryError("status provider identity is unavailable")
    return name


def _validate_lookup(receipt: Mapping[str, Any], provider: str, branch: str) -> None:
    expected = {
        "schema": 1,
        "provider": provider,
        "operation": GET_PR_FOR_BRANCH,
        "evidence_class": "live",
        "observed": True,
        "branch": branch,
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise TrackedStatusDeliveryError("provider branch readback is contradictory")
    if receipt.get("state") == "absent":
        if receipt.get("pr_id") is not None:
            raise TrackedStatusDeliveryError("absent provider readback contains a PR")
        return
    if not isinstance(receipt.get("pr_id"), str) or not receipt["pr_id"]:
        raise TrackedStatusDeliveryError("provider branch readback omitted PR identity")


def _validate_pr(
    receipt: Mapping[str, Any],
    *,
    provider: str,
    operation: str,
    branch: str,
    base: str,
    head_sha: str,
    body: str,
) -> None:
    expected = {
        "schema": 1,
        "provider": provider,
        "operation": operation,
        "evidence_class": "live",
        "observed": True,
        "branch": branch,
        "base": base,
        "head_sha": head_sha,
        "body": body,
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise TrackedStatusDeliveryError("provider PR readback is contradictory")
    if receipt.get("state") not in {"open", "merged"}:
        raise TrackedStatusDeliveryError("provider PR state is unsupported")
    if not isinstance(receipt.get("pr_id"), str) or not receipt["pr_id"]:
        raise TrackedStatusDeliveryError("provider PR identity is missing")


def _merge_gate(
    observation: Mapping[str, Any],
    checks: Mapping[str, Any],
    approvals: Mapping[str, Any],
    *,
    provider: str,
) -> str | None:
    pr_id = observation.get("pr_id")
    head = observation.get("head_sha")
    base = observation.get("base")
    if observation.get("state") != "open":
        return "provider-pr-not-open"
    if observation.get("mergeable") not in {None, "MERGEABLE"}:
        return "provider-mergeability-unproven"
    if observation.get("merge_state_status") not in {None, "CLEAN", "HAS_HOOKS"}:
        return "provider-merge-state-unsafe"
    expected_checks = {
        "provider": provider,
        "operation": GET_CHECKS_AND_POLICIES,
        "evidence_class": "live",
        "observed": True,
        "pr_id": pr_id,
    }
    if any(checks.get(key) != value for key, value in expected_checks.items()):
        return "provider-checks-readback-incomplete"
    if checks.get("head_sha") not in {None, head} or checks.get("base") not in {None, base}:
        return "provider-checks-readback-stale"
    items = checks.get("checks_and_policies")
    if not isinstance(items, list):
        return "provider-checks-readback-incomplete"
    for item in items:
        if not isinstance(item, Mapping):
            return "provider-checks-readback-malformed"
        bucket = item.get("bucket")
        if not isinstance(bucket, str):
            return "provider-checks-readback-malformed"
        normalized = bucket.casefold()
        if normalized in _PENDING_BUCKETS:
            return "provider-checks-pending"
        if normalized in _FAILED_BUCKETS:
            return "provider-checks-failed"
        if normalized not in _PASS_BUCKETS:
            return "provider-checks-readback-malformed"
    expected_approvals = {
        "provider": provider,
        "operation": GET_APPROVALS,
        "evidence_class": "live",
        "observed": True,
        "pr_id": pr_id,
    }
    if any(approvals.get(key) != value for key, value in expected_approvals.items()):
        return "provider-approvals-readback-incomplete"
    decision = approvals.get("review_decision")
    if decision not in {None, "", "APPROVED"}:
        return "provider-approval-unavailable"
    return None


def _record_merge_gate(
    document: Mapping[str, Any], record: EventRecorder, gate: str
) -> None:
    current = _event(document, "merge-gated") if _phase(document) == "merge-gated" else None
    if current is None or current.get("gate") != gate:
        record("merge-gated", {"gate": gate})


@contextmanager
def repository_merge_guard(
    repository: Path, provider: str
):
    try:
        store = RepositoryMergeAuthorityStore(repository)
        if store.binding.provider != provider:
            raise TrackedStatusDeliveryError("merge authority provider is contradictory")
        grant = store.active_grant()
    except RepositoryMergeAuthorityError as error:
        raise TrackedStatusDeliveryError(str(error)) from error
    if grant is None:
        yield None
        return
    run_grant = {
        "repository_identity": store.binding.repository_identity,
        "provider": provider,
        "actor": grant["actor"],
        "evidence": store.adoption_evidence(grant),
    }
    try:
        with store.guard_run_grant(run_grant):
            yield run_grant
    except RepositoryMergeAuthorityError as error:
        raise TrackedStatusDeliveryError(str(error)) from error


def _terminal_source(
    worktree: Path,
    proof: Mapping[str, Any],
    request: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> str:
    folder = str(request["ticket_folder_relative_path"]).rstrip("/")
    old_relative = f"{folder}/{receipt['source_relative_path']}"
    new_relative = f"{folder}/{receipt['destination_relative_path']}"
    terminal_sha = str(proof["terminal_sha"])
    old = subprocess.run(
        ["git", "--no-replace-objects", "cat-file", "-e", f"{terminal_sha}:{old_relative}"],
        cwd=worktree,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
    )
    if old.returncode == 0:
        raise TrackedStatusDeliveryError("terminal source still exists at its prior path")
    raw = _git_bytes(worktree, "show", f"{terminal_sha}:{new_relative}")
    if hashlib.sha256(raw).hexdigest() != request["ticket_digest"]:
        raise TrackedStatusDeliveryError("terminal ticket source digest is contradictory")
    return new_relative


def _default_executor(repository: Path) -> StatusProviderExecutor:
    remote = origin_url(repository)
    if not remote:
        raise TrackedStatusDeliveryError("tracked status delivery requires an origin")
    try:
        provider = detect_provider(remote)
        provider.negotiate(
            {
                CREATE_OR_UPDATE_PR,
                GET_PR_FOR_BRANCH,
                GET_PR_STATE,
                GET_CHECKS_AND_POLICIES,
                GET_APPROVALS,
            }
        )
        return ProviderExecutor(provider, cwd=repository, mode="live")
    except ProviderError as error:
        raise TrackedStatusDeliveryError(str(error)) from error


def drive_tracked_status_delivery(
    repository: Path,
    transaction_root: Path,
    document: dict[str, Any],
    *,
    record: EventRecorder,
    project: Projection,
    checkpoint: Checkpoint = None,
    provider_executor: StatusProviderExecutor | None = None,
    merge_guard_factory: MergeGuardFactory | None = None,
) -> dict[str, Any]:
    """Drive one tracked transaction until complete or a named durable gate."""

    request = document["request"]
    transaction_id = str(document["transaction_id"])
    replayed = len(document["history"]) > 2
    initial_phase = _phase(document)
    _parent_ref, parent_sha = _effective_target(document)
    source_receipts = transaction_root / "tracked-source-receipts" / transaction_id
    _safe_state_directory(transaction_root, source_receipts)
    source_journals = sorted(source_receipts.glob("*.json")) if source_receipts.exists() else []
    if len(source_journals) > 1 or any(path.is_symlink() for path in source_journals):
        raise TrackedStatusDeliveryError("tracked source receipt state is ambiguous")
    source_started = bool(source_journals)

    if _phase(document) in {"tracked-handoff-ready", "safe-boundary-armed"}:
        _refresh_target(repository, str(request["target_branch"]))
        current_ref, current_sha = _target(repository, str(request["target_branch"]))
        if current_sha != parent_sha:
            if source_started:
                return {"gate": "target-advanced-after-source-intent", "replayed": replayed}
            if not _ticket_blob_matches(
                repository,
                current_sha,
                str(request["ticket_source_relative_path"]),
                str(request["ticket_digest"]),
            ):
                return {"gate": "target-advanced-with-source-drift", "replayed": replayed}
            record("target-refreshed", {"target_ref": current_ref, "target_sha": current_sha})
            _checkpoint(checkpoint, "target-refreshed")
            parent_sha = current_sha

    worktree = _admin_worktree(repository, transaction_id, parent_sha)

    if _phase(document) in {
        "tracked-handoff-ready",
        "safe-boundary-armed",
        "target-refreshed",
    }:
        if _git_text(worktree, "rev-parse", "HEAD") != parent_sha:
            if _status_paths(worktree):
                raise TrackedStatusDeliveryError("stale status worktree contains candidate state")
            run_git(worktree, "reset", "--hard", parent_sha)
        if not source_started and _status_paths(worktree):
            raise TrackedStatusDeliveryError("status admin worktree is not initially clean")
        folder = worktree / str(request["ticket_folder_relative_path"])
        try:
            receipt = transition_ticket_source(
                folder,
                source_receipts,
                str(request["ticket_id"]),
                str(request["to_disposition"]),
                actor=str(request["actor"]),
                reason=str(request["reason"]),
                authority_ref=str(request["authority_ref"]),
                authority_gate_id=request["reopen_gate_id"],
                expected_digest=str(request["ticket_digest"]),
            )
        except LifecycleError as error:
            raise TrackedStatusDeliveryError(str(error)) from error
        new_path = (
            Path(request["ticket_folder_relative_path"])
            / str(receipt["destination_relative_path"])
        ).as_posix()
        destination = worktree / new_path
        if destination.is_symlink() or not destination.is_file():
            raise TrackedStatusDeliveryError("tracked source destination is missing")
        if ticket_source_digest(destination) != request["ticket_digest"]:
            raise TrackedStatusDeliveryError("tracked source destination digest drifted")
        _checkpoint(checkpoint, "source-effect-applied")
        record(
            "source-applied",
            {"receipt": receipt, "source_readback_relative_path": new_path},
        )
        _checkpoint(checkpoint, "source-applied")

    receipt_event = _event(document, "source-applied")
    if receipt_event is None or not isinstance(receipt_event.get("receipt"), Mapping):
        raise TrackedStatusDeliveryError("tracked source receipt is unavailable")
    receipt = receipt_event["receipt"]
    old_path = (
        Path(request["ticket_folder_relative_path"])
        / str(receipt["source_relative_path"])
    ).as_posix()
    new_path = (
        Path(request["ticket_folder_relative_path"])
        / str(receipt["destination_relative_path"])
    ).as_posix()

    if _phase(document) == "source-applied":
        _refresh_target(repository, str(request["target_branch"]))
        _current_ref, current_sha = _target(repository, str(request["target_branch"]))
        if current_sha != parent_sha:
            return {"gate": "target-advanced-after-source", "replayed": replayed}
        repointed = _apply_exact_repoints(worktree, parent_sha, old_path, new_path)
        allowed = {old_path, new_path, *repointed}
        candidate = _freeze_candidate(
            worktree,
            parent_sha,
            allowed,
            old_path=old_path,
            new_path=new_path,
            expected_digest=str(request["ticket_digest"]),
        )
        record("candidate-frozen", {"candidate": candidate})
        _checkpoint(checkpoint, "candidate-frozen")

    candidate_event = _event(document, "candidate-frozen")
    if candidate_event is None or not isinstance(candidate_event.get("candidate"), Mapping):
        raise TrackedStatusDeliveryError("tracked candidate evidence is unavailable")
    candidate = candidate_event["candidate"]
    _validate_candidate_evidence(
        worktree,
        parent_sha,
        candidate,
        old_path=old_path,
        new_path=new_path,
        expected_digest=str(request["ticket_digest"]),
    )

    if _phase(document) == "candidate-frozen":
        intent = _commit_identity(document, candidate)
        record("commit-intent", {"commit": intent})
        _checkpoint(checkpoint, "commit-intent")
    intent_event = _event(document, "commit-intent")
    if intent_event is None or not isinstance(intent_event.get("commit"), Mapping):
        raise TrackedStatusDeliveryError("status commit intent is unavailable")
    commit_intent = intent_event["commit"]
    expected_commit_intent = _commit_identity(document, candidate)
    if dict(commit_intent) != expected_commit_intent:
        raise TrackedStatusDeliveryError("status commit intent is contradictory")

    if _phase(document) == "commit-intent":
        committed = _create_or_read_commit(worktree, commit_intent)
        _checkpoint(checkpoint, "commit-effect-applied")
        record("committed", {"commit": committed})
        _checkpoint(checkpoint, "committed")
    commit_event = _event(document, "committed")
    if commit_event is None or not isinstance(commit_event.get("commit"), Mapping):
        raise TrackedStatusDeliveryError("status commit readback is unavailable")
    commit = commit_event["commit"]
    committed_readback = _create_or_read_commit(worktree, commit_intent)
    if dict(commit) != committed_readback:
        raise TrackedStatusDeliveryError("status committed readback is contradictory")
    head_sha = str(commit["head_sha"])
    branch = str(commit["branch"])

    if _phase(document) == "committed":
        _refresh_target(repository, str(request["target_branch"]))
        _current_ref, current_sha = _target(repository, str(request["target_branch"]))
        if current_sha != candidate["parent_sha"]:
            return {"gate": "target-advanced-after-candidate", "replayed": replayed}
        record("push-intent", {"branch": branch, "head_sha": head_sha})
        _checkpoint(checkpoint, "push-intent")
    if _phase(document) == "push-intent":
        record("push-armed", {"branch": branch, "head_sha": head_sha})
        _checkpoint(checkpoint, "push-armed")
    if _phase(document) == "push-armed":
        remote_head = _remote_head(worktree, branch)
        if remote_head is None:
            result = subprocess.run(
                ["git", "push", "origin", f"{head_sha}:refs/heads/{branch}"],
                cwd=worktree,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode:
                raise TrackedStatusDeliveryError(
                    result.stderr.strip() or result.stdout.strip() or "status branch push failed"
                )
            _checkpoint(checkpoint, "push-effect-applied")
            remote_head = _remote_head(worktree, branch)
        if remote_head != head_sha:
            return {"gate": "remote-status-branch-drift", "replayed": replayed}
        record(
            "pushed",
            {"branch": branch, "head_sha": head_sha, "remote_sha": remote_head},
        )
        _checkpoint(checkpoint, "pushed")

    try:
        executor = provider_executor or _default_executor(worktree)
        provider = _provider_name(executor)
    except (ProviderError, TrackedStatusDeliveryError):
        return {"gate": "provider-adapter-unavailable", "replayed": replayed}
    body = _provider_body(document, head_sha)
    base = str(request["target_branch"])
    title = f"Status {request['ticket_id']}: {request['to_disposition']}"
    provider_binding = {
        "provider": provider,
        "branch": branch,
        "base": base,
        "head_sha": head_sha,
        "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }

    if _phase(document) == "pushed":
        record("provider-intent", provider_binding)
        _checkpoint(checkpoint, "provider-intent")
    if _phase(document) == "provider-intent":
        _refresh_target(repository, str(request["target_branch"]))
        _current_ref, current_sha = _target(repository, str(request["target_branch"]))
        if current_sha != candidate["parent_sha"]:
            return {"gate": "target-advanced-after-provider-intent", "replayed": replayed}
        try:
            lookup = executor.execute(GET_PR_FOR_BRANCH, branch=branch)
        except ProviderError:
            return {"gate": "provider-readback-unavailable", "replayed": replayed}
        _validate_lookup(lookup, provider, branch)
        if lookup["state"] != "absent":
            _validate_pr(
                lookup,
                provider=provider,
                operation=GET_PR_FOR_BRANCH,
                branch=branch,
                base=base,
                head_sha=head_sha,
                body=body,
            )
            record("pr-read-back", {"observation": lookup})
        else:
            record("provider-armed", provider_binding)
            _checkpoint(checkpoint, "provider-armed")
    if _phase(document) == "provider-armed":
        try:
            observation = executor.execute(GET_PR_FOR_BRANCH, branch=branch)
        except ProviderError:
            return {"gate": "provider-readback-unavailable", "replayed": replayed}
        _validate_lookup(observation, provider, branch)
        if observation["state"] == "absent":
            if initial_phase == "provider-armed":
                return {"gate": "ambiguous-provider-dispatch", "replayed": True}
            try:
                observation = executor.execute(
                    CREATE_OR_UPDATE_PR,
                    branch=branch,
                    base=base,
                    head_sha=head_sha,
                    title=title,
                    body_artifact=body,
                )
            except ProviderError:
                return {"gate": "ambiguous-provider-dispatch", "replayed": replayed}
            _checkpoint(checkpoint, "provider-effect-applied")
            _validate_pr(
                observation,
                provider=provider,
                operation=CREATE_OR_UPDATE_PR,
                branch=branch,
                base=base,
                head_sha=head_sha,
                body=body,
            )
        else:
            _validate_pr(
                observation,
                provider=provider,
                operation=GET_PR_FOR_BRANCH,
                branch=branch,
                base=base,
                head_sha=head_sha,
                body=body,
            )
        record("pr-read-back", {"observation": observation})
        _checkpoint(checkpoint, "pr-read-back")

    pr_event = _event(document, "pr-read-back")
    if pr_event is None or not isinstance(pr_event.get("observation"), Mapping):
        raise TrackedStatusDeliveryError("provider PR readback is unavailable")
    pr = pr_event["observation"]
    pr_id = str(pr["pr_id"])

    if _phase(document) in {"pr-read-back", "merge-gated"}:
        try:
            observation = executor.execute(GET_PR_STATE, pr_id=pr_id)
        except ProviderError:
            return {"gate": "provider-readback-unavailable", "replayed": replayed}
        _validate_pr(
            observation,
            provider=provider,
            operation=GET_PR_STATE,
            branch=branch,
            base=base,
            head_sha=head_sha,
            body=body,
        )
        if observation["state"] == "merged":
            record(
                "provider-merged",
                {"observation": observation, "provenance": "external-readback"},
            )
        else:
            guard_factory = merge_guard_factory or (
                lambda: repository_merge_guard(repository, provider)
            )
            with guard_factory() as grant:
                if grant is None:
                    gate = "repository-merge-authority-unavailable"
                    _record_merge_gate(document, record, gate)
                    return {"gate": gate, "replayed": replayed}
                negotiate = getattr(getattr(executor, "provider", None), "negotiate", None)
                if callable(negotiate):
                    try:
                        negotiate({MERGE_WITH_EXPECTED_HEAD})
                    except ProviderError:
                        gate = "provider-merge-capability-unavailable"
                        _record_merge_gate(document, record, gate)
                        return {"gate": gate, "replayed": replayed}
                try:
                    checks = executor.execute(
                        GET_CHECKS_AND_POLICIES,
                        pr_id=pr_id,
                        expected_head=head_sha,
                    )
                    approvals = executor.execute(GET_APPROVALS, pr_id=pr_id)
                except ProviderError:
                    gate = "provider-merge-readback-unavailable"
                    _record_merge_gate(document, record, gate)
                    return {"gate": gate, "replayed": replayed}
                gate = _merge_gate(
                    observation, checks, approvals, provider=provider
                )
                if gate is not None:
                    _record_merge_gate(document, record, gate)
                    return {"gate": gate, "replayed": replayed}
                actor = str(grant.get("actor", ""))
                evidence = str(grant.get("evidence", ""))
                if not actor or not evidence:
                    raise TrackedStatusDeliveryError("merge authority receipt is incomplete")
                intent_key = _digest(
                    {
                        "provider": provider,
                        "pr_id": pr_id,
                        "head_sha": head_sha,
                        "actor": actor,
                        "evidence": evidence,
                    }
                )
                merge_intent = {
                    "provider": provider,
                    "pr_id": pr_id,
                    "head_sha": head_sha,
                    "actor": actor,
                    "evidence": evidence,
                    "intent_key": intent_key,
                }
                record("merge-intent", merge_intent)
                _checkpoint(checkpoint, "merge-intent")
                merge_mode = str(checks.get("merge_mode", "direct"))
                if merge_mode not in {"direct", "queue"}:
                    raise TrackedStatusDeliveryError("provider merge mode is invalid")
                record("merge-armed", {**merge_intent, "merge_mode": merge_mode})
                _checkpoint(checkpoint, "merge-armed")
                authorization = MergeAuthorization(
                    provider=provider,
                    pr_id=pr_id,
                    head_sha=head_sha,
                    actor=actor,
                    evidence=evidence,
                )
                try:
                    executor.execute(
                        MERGE_WITH_EXPECTED_HEAD,
                        pr_id=pr_id,
                        expected_head=head_sha,
                        intent_key=intent_key,
                        authorization=authorization,
                        previous_attempt_mode=merge_mode,
                    )
                except ProviderError:
                    return {"gate": "ambiguous-merge-dispatch", "replayed": replayed}
                _checkpoint(checkpoint, "merge-effect-applied")
                try:
                    observation = executor.execute(GET_PR_STATE, pr_id=pr_id)
                except ProviderError:
                    return {"gate": "provider-merge-readback-unavailable", "replayed": replayed}
                _validate_pr(
                    observation,
                    provider=provider,
                    operation=GET_PR_STATE,
                    branch=branch,
                    base=base,
                    head_sha=head_sha,
                    body=body,
                )
                if observation["state"] == "merged":
                    record(
                        "provider-merged",
                        {"observation": observation, "provenance": "runner-merge"},
                    )
                else:
                    return {"gate": "provider-merge-pending", "replayed": replayed}

    if _phase(document) == "merge-armed":
        merge = _event(document, "merge-armed")
        if merge is None:
            raise TrackedStatusDeliveryError("merge intent readback is unavailable")
        try:
            observation = executor.execute(GET_PR_STATE, pr_id=pr_id)
        except ProviderError:
            return {"gate": "provider-merge-readback-unavailable", "replayed": True}
        _validate_pr(
            observation,
            provider=provider,
            operation=GET_PR_STATE,
            branch=branch,
            base=base,
            head_sha=head_sha,
            body=body,
        )
        if observation["state"] != "merged":
            return {"gate": "ambiguous-merge-dispatch", "replayed": True}
        record(
            "provider-merged",
            {"observation": observation, "provenance": "runner-merge"},
        )

    if _phase(document) == "provider-merged":
        merged_event = _event(document, "provider-merged")
        if merged_event is None or not isinstance(merged_event.get("observation"), Mapping):
            raise TrackedStatusDeliveryError("merged provider readback is unavailable")
        observation = merged_event["observation"]
        try:
            fresh_observation = executor.execute(GET_PR_STATE, pr_id=pr_id)
        except ProviderError:
            return {"gate": "provider-merged-readback-unavailable", "replayed": replayed}
        _validate_pr(
            fresh_observation,
            provider=provider,
            operation=GET_PR_STATE,
            branch=branch,
            base=base,
            head_sha=head_sha,
            body=body,
        )
        critical_provider_fields = {
            "provider",
            "pr_id",
            "branch",
            "base",
            "head_sha",
            "merge_commit_sha",
            "body",
            "state",
        }
        if any(
            fresh_observation.get(field) != observation.get(field)
            for field in critical_provider_fields
        ):
            raise TrackedStatusDeliveryError("merged provider readback is contradictory")
        ledger = {
            "repo": str(repository),
            "provider": provider,
            "tickets": {
                str(request["ticket_id"]): {
                    "blocked_by": [],
                    "pr": {"pr_id": pr_id, "head_sha": head_sha},
                    "delivery_lineage": {
                        "provider": provider,
                        "pr_id": pr_id,
                        "head_sha": head_sha,
                        "base_branch": base,
                    },
                }
            },
        }
        try:
            proof = build_terminal_integration_proof(
                worktree,
                ledger,
                str(request["ticket_id"]),
                observation,
                provenance=str(merged_event["provenance"]),
                boundary_guard=lambda boundary: _checkpoint(checkpoint, boundary),
            )
        except TerminalIntegrationError:
            return {"gate": "terminal-reachability-unproven", "replayed": replayed}
        if proof.get("reachable_kind") != "head" or proof.get("reachable_sha") != head_sha:
            return {
                "gate": "exact-delivery-head-not-terminal-reachable",
                "replayed": replayed,
            }
        terminal_relative = _terminal_source(worktree, proof, request, receipt)
        record(
            "terminal-proved",
            {"proof": proof, "source_relative_path": terminal_relative},
        )
        _checkpoint(checkpoint, "terminal-proved")

    terminal_event = _event(document, "terminal-proved")
    if terminal_event is None:
        raise TrackedStatusDeliveryError("terminal status proof is unavailable")
    terminal_relative = str(terminal_event["source_relative_path"])
    if _phase(document) == "terminal-proved":
        project(receipt, terminal_relative)
        record(
            "projected",
            {
                "projection_run_id": request["projection_run_id"],
                "source_relative_path": terminal_relative,
                "ticket_digest": request["ticket_digest"],
            },
        )
        _checkpoint(checkpoint, "projected")
    if _phase(document) == "projected":
        record(
            "tracked-complete",
            {
                "projection_run_id": request["projection_run_id"],
                "tracked_delivery": True,
            },
        )
        _checkpoint(checkpoint, "tracked-complete")
    return {"gate": None, "replayed": replayed}
