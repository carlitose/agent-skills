"""Fresh target and runner-owned worktree coherence before candidate quality.

Contract validation is pure. Git imports stay inside observers because git_ops
itself imports the kernel, which consumes these contract validators.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Mapping

from .candidate_contract import CandidateContractError, semantic_candidate
from .terminal_integration import canonical_digest


CONTRACT_VERSION = "pre-qa-coherence-v1"
TARGET_CONTRACT_VERSION = "candidate-target-v1"
_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_REASONS = {
    "repository-identity-mismatch",
    "worktree-identity-mismatch",
    "target-fetch-failed",
    "candidate-base-drift",
    "candidate-index-drift",
    "target-advanced-before-qa",
    "coherence-receipt-malformed",
}
_IDENTITY_FIELDS = (
    "branch", "remote", "ref", "repository_root", "git_common_dir",
    "provider", "normalized_remote",
)


class PreQaCoherenceError(ValueError):
    """One target or pre-QA receipt is malformed."""


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PreQaCoherenceError(f"{label} must be a non-empty string")
    return value


def _oid(value: object, label: str) -> str:
    text = _text(value, label)
    if _HEX_40.fullmatch(text) is None or text == "0" * 40:
        raise PreQaCoherenceError(f"{label} must be a nonzero lowercase Git SHA-1")
    return text


def validate_target_identity(value: object) -> dict[str, Any]:
    fields = {"contract_version", "sha", "tree_oid", *_IDENTITY_FIELDS}
    if not isinstance(value, Mapping) or set(value) != fields:
        raise PreQaCoherenceError("candidate target identity fields are invalid")
    document = copy.deepcopy(dict(value))
    if document["contract_version"] != TARGET_CONTRACT_VERSION:
        raise PreQaCoherenceError("candidate target identity version is invalid")
    for field in _IDENTITY_FIELDS:
        _text(document[field], f"candidate target {field}")
    _oid(document["sha"], "candidate target sha")
    _oid(document["tree_oid"], "candidate target tree_oid")
    if document["remote"] != "origin":
        raise PreQaCoherenceError("candidate target remote must be origin")
    expected_ref = f"refs/remotes/origin/{document['branch']}"
    if document["ref"] != expected_ref:
        raise PreQaCoherenceError("candidate target ref contradicts branch")
    return document


def observe_target(repository: Path, branch: str) -> dict[str, Any]:
    from .git_ops import GitError, repository_root, run_git
    from .worktree_gc import _repository_binding

    root = repository_root(repository)
    binding = _repository_binding(root)
    run_git(root, "check-ref-format", "--branch", branch)
    remote_ref = f"refs/remotes/origin/{branch}"
    try:
        run_git(
            root, "fetch", "--no-tags", "--no-write-fetch-head", "origin",
            f"+refs/heads/{branch}:{remote_ref}",
        )
        sha = run_git(root, "rev-parse", f"{remote_ref}^{{commit}}")
        tree_oid = run_git(root, "rev-parse", f"{sha}^{{tree}}")
    except GitError as error:
        # Remote stderr can include a credential-bearing transport URL. The receipt
        # needs a typed outcome, never that output or a fabricated cached success.
        raise GitError("target-fetch-failed: cannot refresh configured target") from error
    return validate_target_identity({
        "contract_version": TARGET_CONTRACT_VERSION,
        "branch": branch,
        "remote": "origin",
        "ref": remote_ref,
        "sha": sha,
        "tree_oid": tree_oid,
        "repository_root": str(root),
        "git_common_dir": binding["git_common_dir"],
        "provider": binding["provider"],
        "normalized_remote": binding["normalized_remote"],
    })


def _registered_worktrees(repository: Path) -> set[Path]:
    from .git_ops import run_git

    raw = run_git(repository, "worktree", "list", "--porcelain", "-z")
    # A missing unrelated worktree is not a failure of the selected worktree.
    return {
        Path(field.removeprefix("worktree ")).resolve()
        for field in raw.split("\0") if field.startswith("worktree ")
    }


def _legacy_branch(repository: Path) -> str:
    from .git_ops import run_git

    # No guessed `main`: ask the remote for its symbolic default branch. Legacy
    # delivery-specific targets need explicit migration rather than a guess here.
    output = run_git(repository, "ls-remote", "--symref", "origin", "HEAD")
    refs = [
        line.split()[1]
        for line in output.splitlines()
        if line.startswith("ref: ") and line.split()[-1] == "HEAD"
    ]
    if len(refs) != 1 or not refs[0].startswith("refs/heads/"):
        raise PreQaCoherenceError("legacy target is ambiguous; restart the run")
    return refs[0].removeprefix("refs/heads/")


def effective_target_branch(
    ledger: Mapping[str, Any], ticket_id: str, root_branch: str
) -> str:
    """Reuse scheduler stackability, rather than introducing a second policy."""
    from .providers import build_delivery_plan, detect_provider

    plan = build_delivery_plan(
        detect_provider("", override=ledger["provider"]),
        ledger, ticket_id, default_base=root_branch,
        title="coherence observation", body_artifact="not-published://coherence",
    )
    prepared = ledger["tickets"][ticket_id].get("delivery", {}).get("reconcile-prepare")
    if prepared is not None and prepared["target_base"]["branch"] != plan.base_branch:
        raise PreQaCoherenceError("reconciliation target contradicts scheduler target")
    return plan.base_branch


def _recorded_head_binding(ticket: Mapping[str, Any]) -> dict[str, Any] | None:
    delivery = ticket.get("delivery", {})
    prepared = delivery.get("reconcile-prepare")
    if prepared is not None:
        records = {"prepare": prepared, "lineage": ticket["delivery_lineage"]}
        source = "reconcile-prepare"
        branch = ticket["delivery_lineage"]["branch"]
        head_sha = prepared["new_head"]
        base_sha = prepared["target_base"]["sha"]
        base_tree = prepared["target_base"]["tree_oid"]
    else:
        commit, branch_record = delivery.get("commit"), delivery.get("branch")
        if commit is None and branch_record is None:
            return None
        if commit is None:
            return None
        if branch_record is None or commit["branch"] != branch_record["branch"]:
            raise PreQaCoherenceError("delivery HEAD contradicts recorded branch")
        records = {"commit": commit, "branch": branch_record}
        source = "commit"
        branch, head_sha = commit["branch"], commit["head_sha"]
        base_sha, base_tree = branch_record["base_sha"], branch_record["base_tree_oid"]
    return {
        "kind": "delivery",
        "source": source,
        "branch": branch,
        "head_sha": head_sha,
        "base_sha": base_sha,
        "base_tree_oid": base_tree,
        "record_digest": canonical_digest(records),
    }


def _observe_head_binding(worktree: Path, ticket: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    from .git_ops import run_git

    if receipt["head_tree_oid"] == receipt["candidate_ref"]["base_tree_oid"]:
        return {"kind": "base"}
    proof = _recorded_head_binding(ticket)
    if proof is None or (
        proof["head_sha"] != receipt["head_sha"]
        or proof["base_tree_oid"] != receipt["candidate_ref"]["base_tree_oid"]
        or run_git(worktree, "symbolic-ref", "--quiet", "--short", "HEAD") != proof["branch"]
        or run_git(worktree, "rev-parse", f"{proof['base_sha']}^{{tree}}") != proof["base_tree_oid"]
    ):
        raise PreQaCoherenceError("HEAD is not a recorded delivery on the candidate base")
    # Ancestry is an additional topology check, never a substitute for the exact
    # ledger head, branch, base tree, and fresh target comparisons above.
    run_git(worktree, "merge-base", "--is-ancestor", proof["base_sha"], proof["head_sha"])
    return proof


def build_receipt(
    *,
    ledger: Mapping[str, Any],
    ticket_id: str,
    candidate_ref: Mapping[str, Any],
) -> dict[str, Any]:
    from .git_ops import common_git_dir, repository_root, run_git
    from .worktree_gc import _repository_binding

    ticket = ledger["tickets"][ticket_id]
    repo = Path(str(ledger["repo"])).expanduser().resolve()
    worktree = Path(str(ledger["worktree"])).expanduser().resolve()
    receipt = {
        "contract_version": CONTRACT_VERSION,
        "status": "blocked",
        "reason": None,
        "run_id": str(ledger["run_id"]),
        "ticket_id": ticket_id,
        "artifact_generation": ticket["artifact_generation"],
        "candidate_ref": copy.deepcopy(dict(candidate_ref)),
        "repository_root": str(repo),
        "git_common_dir": None,
        "worktree_path": str(worktree),
        "target": None,
        "head_sha": None,
        "head_tree_oid": None,
        "index_tree_oid": None,
        "head_binding": None,
        "legacy_adoption": (
            ledger.get("target_identity") is None
            or bool((ticket.get("pre_qa_coherence") or {}).get("legacy_adoption"))
        ),
    }

    def blocked(reason: str) -> dict[str, Any]:
        receipt["reason"] = reason
        return validate_receipt(receipt)

    try:
        if repository_root(repo) != repo:
            return blocked("repository-identity-mismatch")
        binding = _repository_binding(repo)
        receipt["git_common_dir"] = binding["git_common_dir"]
    except (OSError, RuntimeError, ValueError):
        return blocked("repository-identity-mismatch")
    try:
        if repository_root(worktree) != worktree:
            return blocked("worktree-identity-mismatch")
        if common_git_dir(worktree) != Path(binding["git_common_dir"]):
            return blocked("repository-identity-mismatch")
        if worktree == repo or worktree not in _registered_worktrees(repo):
            return blocked("worktree-identity-mismatch")
    except (OSError, RuntimeError, ValueError):
        return blocked("worktree-identity-mismatch")

    try:
        stored = ledger.get("target_identity")
        stored = validate_target_identity(stored) if stored is not None else None
        if stored is not None and any(
            stored[field] != observed
            for field, observed in (
                ("repository_root", str(repo)),
                ("git_common_dir", binding["git_common_dir"]),
                ("provider", binding["provider"]),
                ("normalized_remote", binding["normalized_remote"]),
            )
        ):
            return blocked("repository-identity-mismatch")
        root_branch = stored["branch"] if stored is not None else _legacy_branch(repo)
        branch = effective_target_branch(ledger, ticket_id, root_branch)
        if stored is None and (branch != root_branch or ticket.get("delivery_lineage")):
            return blocked("coherence-receipt-malformed")
    except (OSError, RuntimeError, ValueError, KeyError, TypeError):
        return blocked("coherence-receipt-malformed")

    try:
        receipt["head_sha"] = run_git(worktree, "rev-parse", "HEAD^{commit}")
        receipt["head_tree_oid"] = run_git(worktree, "rev-parse", "HEAD^{tree}")
        receipt["index_tree_oid"] = run_git(worktree, "write-tree")
    except (OSError, RuntimeError, ValueError):
        return blocked("worktree-identity-mismatch")
    try:
        observed = observe_target(repo, branch)
        receipt["target"] = observed
    except (OSError, RuntimeError, ValueError):
        return blocked("target-fetch-failed")
    if stored is not None and any(
        stored[f] != observed[f]
        for f in _IDENTITY_FIELDS if f not in {"branch", "ref"}
    ):
        return blocked("repository-identity-mismatch")
    if receipt["index_tree_oid"] != candidate_ref.get("candidate_tree_oid"):
        return blocked("candidate-index-drift")
    if observed["tree_oid"] != candidate_ref.get("base_tree_oid"):
        return blocked("target-advanced-before-qa")
    try:
        receipt["head_binding"] = _observe_head_binding(worktree, ticket, receipt)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError):
        return blocked("candidate-base-drift")
    receipt["status"] = "pass"
    return validate_receipt(receipt)


def validate_receipt(value: object) -> dict[str, Any]:
    fields = {
        "contract_version", "status", "reason", "run_id", "ticket_id",
        "artifact_generation", "candidate_ref", "repository_root",
        "git_common_dir", "worktree_path", "target", "head_sha",
        "head_tree_oid", "index_tree_oid", "head_binding", "legacy_adoption",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise PreQaCoherenceError("pre-QA coherence receipt fields are invalid")
    document = copy.deepcopy(dict(value))
    if document["contract_version"] != CONTRACT_VERSION:
        raise PreQaCoherenceError("pre-QA coherence version is invalid")
    if document["status"] not in ("pass", "blocked"):
        raise PreQaCoherenceError("pre-QA coherence status is invalid")
    reason = document["reason"]
    if reason is not None and (not isinstance(reason, str) or reason not in _REASONS):
        raise PreQaCoherenceError("pre-QA coherence reason is invalid")
    passing = document["status"] == "pass"
    if passing != (reason is None):
        raise PreQaCoherenceError("pre-QA coherence status contradicts reason")
    for field in ("run_id", "ticket_id", "repository_root", "worktree_path"):
        _text(document[field], f"pre-QA coherence {field}")
    generation = document["artifact_generation"]
    if type(generation) is not int or generation < 0:
        raise PreQaCoherenceError("pre-QA artifact_generation is invalid")
    try:
        document["candidate_ref"] = semantic_candidate(document["candidate_ref"]).as_dict()
    except CandidateContractError as error:
        raise PreQaCoherenceError(str(error)) from error
    candidate = document["candidate_ref"]
    for field in ("base_tree_oid", "candidate_tree_oid"):
        _oid(candidate[field], f"pre-QA candidate {field}")
    for field in ("head_sha", "head_tree_oid", "index_tree_oid"):
        if passing or document[field] is not None:
            _oid(document[field], f"pre-QA coherence {field}")
    if passing or document["git_common_dir"] is not None:
        _text(document["git_common_dir"], "pre-QA git_common_dir")
    if type(document["legacy_adoption"]) is not bool:
        raise PreQaCoherenceError("pre-QA legacy_adoption is invalid")
    if passing or document["target"] is not None:
        document["target"] = validate_target_identity(document["target"])
    proof = document["head_binding"]
    if passing or proof is not None:
        if not isinstance(proof, Mapping):
            raise PreQaCoherenceError("pre-QA HEAD binding is required")
        if proof == {"kind": "base"}:
            head_matches = document["head_tree_oid"] == candidate["base_tree_oid"]
        elif set(proof) == {
            "kind", "source", "branch", "head_sha", "base_sha", "base_tree_oid", "record_digest"
        } and proof["kind"] == "delivery":
            if proof["source"] not in ("commit", "reconcile-prepare"):
                raise PreQaCoherenceError("pre-QA HEAD proof source is invalid")
            for field in ("head_sha", "base_sha", "base_tree_oid"):
                _oid(proof[field], f"pre-QA HEAD proof {field}")
            _text(proof["branch"], "pre-QA HEAD branch")
            digest = _text(proof["record_digest"], "pre-QA HEAD record digest")
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise PreQaCoherenceError("pre-QA HEAD record digest is invalid")
            head_matches = (
                proof["head_sha"] == document["head_sha"]
                and proof["base_tree_oid"] == candidate["base_tree_oid"]
            )
        else:
            raise PreQaCoherenceError("pre-QA HEAD proof fields are invalid")
        if passing and not head_matches:
            raise PreQaCoherenceError("pre-QA pass contradicts HEAD proof")
    if passing:
        target = document["target"]
        if not (
            document["repository_root"] == target["repository_root"]
            and document["git_common_dir"] == target["git_common_dir"]
            and document["worktree_path"] != document["repository_root"]
            and candidate["base_tree_oid"] == target["tree_oid"]
            and document["index_tree_oid"] == candidate["candidate_tree_oid"]
        ):
            raise PreQaCoherenceError("pre-QA pass contradicts observed identities")
    return document


def validate_bound_receipt(
    value: object, ledger: Mapping[str, Any], ticket_id: str
) -> dict[str, Any]:
    receipt = validate_receipt(value)
    ticket = ledger["tickets"][ticket_id]
    if (
        receipt["run_id"] != ledger["run_id"]
        or receipt["ticket_id"] != ticket_id
        or receipt["artifact_generation"] != ticket["artifact_generation"]
        or receipt["candidate_ref"] != ticket["candidate_ref"]
        or receipt["repository_root"] != ledger["repo"]
        or receipt["worktree_path"] != ledger["worktree"]
        or receipt["legacy_adoption"] != (
            ledger.get("target_identity") is None
            or bool((ticket.get("pre_qa_coherence") or {}).get("legacy_adoption"))
        )
    ):
        raise PreQaCoherenceError("pre-QA coherence receipt binding is stale or contradictory")
    stored = ledger.get("target_identity")
    if receipt["status"] == "pass":
        target = receipt["target"]
        if stored is not None:
            stored = validate_target_identity(stored)
            if any(
                target[field] != stored[field]
                for field in _IDENTITY_FIELDS if field not in {"branch", "ref"}
            ) or target["branch"] != effective_target_branch(ledger, ticket_id, stored["branch"]):
                raise PreQaCoherenceError("pre-QA pass contradicts effective delivery target")
        proof = receipt["head_binding"]
        if proof["kind"] == "delivery" and proof != _recorded_head_binding(ticket):
            raise PreQaCoherenceError("pre-QA HEAD proof contradicts ledger lineage")
    return receipt


def require_current_receipt(ledger: Mapping[str, Any], ticket_id: str) -> None:
    """Replay historical ledgers; target-aware quality cannot omit the guard."""
    if ledger.get("target_identity") is None:
        return
    receipt = validate_bound_receipt(
        ledger["tickets"][ticket_id].get("pre_qa_coherence"), ledger, ticket_id
    )
    if receipt["status"] != "pass":
        raise PreQaCoherenceError("pre-QA coherence is blocked")


def receipt_digest(value: Mapping[str, Any]) -> str:
    return canonical_digest(validate_receipt(value))
