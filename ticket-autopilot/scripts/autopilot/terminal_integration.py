from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol


class CommandResult(Protocol):
    stdout: str
    stderr: str
    returncode: int


class CommandRunner(Protocol):
    def run(self, command: list[str], *, cwd: Path) -> CommandResult: ...


class SubprocessCommandRunner:
    def run(self, command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(command, cwd=cwd, text=True, capture_output=True)


PROOF_VERSION = 1
PROVENANCE = frozenset({"runner-merge", "external-readback"})
_OID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


class TerminalIntegrationError(RuntimeError):
    """A provider merge cannot be proven reachable from its terminal branch."""


def canonical_digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def terminal_branch(ledger: Mapping[str, Any], ticket_id: str) -> str:
    """Derive the recursively inherited root delivery base for one ticket."""

    tickets = ledger.get("tickets")
    if not isinstance(tickets, Mapping) or ticket_id not in tickets:
        raise TerminalIntegrationError(f"unknown terminal integration ticket {ticket_id!r}")

    def visit(current_id: str, stack: frozenset[str]) -> str:
        if current_id in stack:
            raise TerminalIntegrationError("terminal delivery lineage contains a cycle")
        ticket = tickets.get(current_id)
        if not isinstance(ticket, Mapping):
            raise TerminalIntegrationError("terminal delivery lineage references an unknown ticket")
        lineage = ticket.get("delivery_lineage")
        if not isinstance(lineage, Mapping):
            raise TerminalIntegrationError(
                f"ticket {current_id} has no delivery lineage for terminal proof"
            )
        base = lineage.get("base_branch")
        if not isinstance(base, str) or not base:
            raise TerminalIntegrationError("terminal delivery lineage omitted its base branch")
        blockers = ticket.get("blocked_by")
        if not isinstance(blockers, list):
            raise TerminalIntegrationError("terminal delivery blockers are malformed")
        if not blockers:
            return base
        inherited: list[str] = []
        for blocker_id in blockers:
            if not isinstance(blocker_id, str) or not blocker_id:
                raise TerminalIntegrationError("terminal delivery blocker id is malformed")
            blocker = tickets.get(blocker_id)
            if not isinstance(blocker, Mapping):
                raise TerminalIntegrationError("terminal delivery blocker is missing")
            if blocker.get("delivery_lineage") is None:
                if blocker.get("preexisting_integrated") is True:
                    inherited.append(base)
                    continue
                raise TerminalIntegrationError(
                    f"blocker {blocker_id} has no delivery lineage for terminal proof"
                )
            inherited.append(visit(blocker_id, stack | {current_id}))
        if len(set(inherited)) != 1:
            raise TerminalIntegrationError(
                "multi-blocker delivery does not have one terminal branch"
            )
        return inherited[0]

    return visit(ticket_id, frozenset())


def _checked(
    runner: CommandRunner,
    worktree: Path,
    *arguments: str,
    failure: str,
) -> str:
    result = runner.run(["git", *arguments], cwd=worktree)
    if result.returncode:
        detail = result.stderr or result.stdout or failure
        raise TerminalIntegrationError(f"{failure}: {detail.strip()}")
    return result.stdout.strip()


def build_terminal_integration_proof(
    worktree: Path,
    ledger: Mapping[str, Any],
    ticket_id: str,
    provider_observation: Mapping[str, Any],
    *,
    provenance: str,
    boundary_guard: Callable[[str], None],
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Fetch terminal truth and prove the exact head or merge object reaches it."""

    if provenance not in PROVENANCE:
        raise TerminalIntegrationError("terminal integration provenance is invalid")
    tickets = ledger.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, Mapping) else None
    if not isinstance(ticket, Mapping):
        raise TerminalIntegrationError("terminal integration ticket is missing")
    pr = ticket.get("pr")
    lineage = ticket.get("delivery_lineage")
    if not isinstance(pr, Mapping) or not isinstance(lineage, Mapping):
        raise TerminalIntegrationError("terminal integration requires PR delivery lineage")
    expected = {
        "schema": 1,
        "provider": ledger.get("provider"),
        "operation": "get-pr-state",
        "evidence_class": "live",
        "observed": True,
        "pr_id": pr.get("pr_id"),
        "head_sha": pr.get("head_sha"),
        "state": "merged",
    }
    if any(provider_observation.get(key) != value for key, value in expected.items()):
        raise TerminalIntegrationError(
            "provider observation cannot prove the recorded merged PR"
        )
    pr_base = provider_observation.get("base")
    if not isinstance(pr_base, str) or not pr_base:
        raise TerminalIntegrationError("provider observation omitted the PR base")
    merge_commit = provider_observation.get("merge_commit_sha")
    if merge_commit is not None and (
        not isinstance(merge_commit, str) or not _OID.fullmatch(merge_commit)
    ):
        raise TerminalIntegrationError("provider merge commit is malformed")

    branch = terminal_branch(ledger, ticket_id)
    command_runner = runner or SubprocessCommandRunner()
    _checked(
        command_runner,
        worktree,
        "check-ref-format",
        "--branch",
        branch,
        failure="terminal branch is invalid",
    )
    terminal_ref = f"refs/remotes/origin/{branch}"
    boundary_guard("git:terminal-integration-fetch")
    _checked(
        command_runner,
        worktree,
        "fetch",
        "--no-tags",
        "origin",
        f"+refs/heads/{branch}:{terminal_ref}",
        failure="terminal branch fetch failed",
    )
    terminal_sha = _checked(
        command_runner,
        worktree,
        "rev-parse",
        terminal_ref,
        failure="terminal branch SHA readback failed",
    )
    terminal_tree = _checked(
        command_runner,
        worktree,
        "rev-parse",
        f"{terminal_ref}^{{tree}}",
        failure="terminal branch tree readback failed",
    )
    remote = _checked(
        command_runner,
        worktree,
        "ls-remote",
        "--heads",
        "origin",
        f"refs/heads/{branch}",
        failure="terminal branch remote readback failed",
    )
    remote_lines = [line.split() for line in remote.splitlines() if line.strip()]
    if len(remote_lines) != 1 or len(remote_lines[0]) != 2:
        raise TerminalIntegrationError("terminal branch remote readback is ambiguous")
    if remote_lines[0][0] != terminal_sha:
        raise TerminalIntegrationError("terminal branch changed during reachability proof")

    head_sha = str(pr["head_sha"])
    candidates = [("head", head_sha)]
    if merge_commit is not None and merge_commit != head_sha:
        candidates.append(("merge-commit", merge_commit))
    reachable_kind = None
    reachable_sha = None
    for kind, candidate in candidates:
        exists = command_runner.run(
            ["git", "cat-file", "-e", f"{candidate}^{{commit}}"], cwd=worktree
        )
        if exists.returncode:
            continue
        ancestor = command_runner.run(
            ["git", "merge-base", "--is-ancestor", candidate, terminal_sha],
            cwd=worktree,
        )
        if ancestor.returncode == 0:
            reachable_kind = kind
            reachable_sha = candidate
            break
        if ancestor.returncode not in {0, 1}:
            detail = ancestor.stderr or ancestor.stdout or "Git ancestry failed"
            raise TerminalIntegrationError(detail.strip())
    if reachable_sha is None or reachable_kind is None:
        raise TerminalIntegrationError(
            "provider PR is merged but neither its exact head nor merge commit "
            f"is reachable from terminal branch {branch} at {terminal_sha}"
        )

    proof = {
        "schema": PROOF_VERSION,
        "repository_identity": ledger.get("repo"),
        "provider": ledger.get("provider"),
        "pr_id": pr.get("pr_id"),
        "head_sha": head_sha,
        "pr_base": pr_base,
        "terminal_branch": branch,
        "terminal_sha": terminal_sha,
        "terminal_tree_oid": terminal_tree,
        "merge_commit_sha": merge_commit,
        "reachable_kind": reachable_kind,
        "reachable_sha": reachable_sha,
        "provider_observation_digest": canonical_digest(provider_observation),
        "delivery_lineage_digest": canonical_digest(lineage),
        "provenance": provenance,
    }
    validate_terminal_integration_proof(
        ledger,
        ticket_id,
        proof,
        provider_observation,
        provenance=provenance,
    )
    return proof


def validate_terminal_integration_proof(
    ledger: Mapping[str, Any],
    ticket_id: str,
    proof: Mapping[str, Any],
    provider_observation: Mapping[str, Any],
    *,
    provenance: str | None = None,
) -> dict[str, Any]:
    fields = {
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
    if not isinstance(proof, Mapping) or set(proof) != fields:
        raise TerminalIntegrationError("terminal integration proof shape is invalid")
    tickets = ledger.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, Mapping) else None
    pr = ticket.get("pr") if isinstance(ticket, Mapping) else None
    lineage = ticket.get("delivery_lineage") if isinstance(ticket, Mapping) else None
    if not isinstance(pr, Mapping) or not isinstance(lineage, Mapping):
        raise TerminalIntegrationError("terminal integration proof lost its PR lineage")
    merge_commit = provider_observation.get("merge_commit_sha")
    expected = {
        "schema": PROOF_VERSION,
        "repository_identity": ledger.get("repo"),
        "provider": ledger.get("provider"),
        "pr_id": pr.get("pr_id"),
        "head_sha": pr.get("head_sha"),
        "pr_base": provider_observation.get("base"),
        "terminal_branch": terminal_branch(ledger, ticket_id),
        "merge_commit_sha": merge_commit,
        "provider_observation_digest": canonical_digest(provider_observation),
        "delivery_lineage_digest": canonical_digest(lineage),
    }
    if any(proof.get(key) != value for key, value in expected.items()):
        raise TerminalIntegrationError("terminal integration proof binding is stale")
    if provenance is not None and proof.get("provenance") != provenance:
        raise TerminalIntegrationError("terminal integration provenance is stale")
    if proof.get("provenance") not in PROVENANCE:
        raise TerminalIntegrationError("terminal integration provenance is invalid")
    for key in ("terminal_sha", "terminal_tree_oid", "reachable_sha"):
        value = proof.get(key)
        if not isinstance(value, str) or not _OID.fullmatch(value):
            raise TerminalIntegrationError(f"terminal integration {key} is malformed")
    reachable_kind = proof.get("reachable_kind")
    if reachable_kind == "head":
        reachable_expected = pr.get("head_sha")
    elif reachable_kind == "merge-commit":
        reachable_expected = merge_commit
    else:
        raise TerminalIntegrationError("terminal integration reachability kind is invalid")
    if proof.get("reachable_sha") != reachable_expected:
        raise TerminalIntegrationError("terminal integration reachable object is stale")
    if provider_observation.get("state") != "merged":
        raise TerminalIntegrationError("terminal integration provider state is not merged")
    return dict(proof)
