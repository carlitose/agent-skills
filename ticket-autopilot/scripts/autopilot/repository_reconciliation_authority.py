"""Persistent repository authority for exact, bounded reconciliation proposals."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping

from .git_ops import CommandRunner, run_git
from .repository_authority import (
    AUTHORITY_SCOPE,
    AuthorityKind,
    RepositoryAuthorityStore,
    canonical_bytes as _canonical_bytes,
    digest as _digest,
)


STATE_RELATIVE_PATH = Path("ticket-autopilot/repository-reconciliation-authority.json")
PROPOSAL_DIRECTORY = "autonomous-reconciliation"
_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_MODES = {"100644", "100755", "120000"}


class RepositoryReconciliationAuthorityError(RuntimeError):
    """Repository reconciliation authority or an exact proposal is unsafe."""


_RECONCILIATION_KIND = AuthorityKind(
    name="reconciliation",
    grant_prefix="rar",
    state_relative_path=STATE_RELATIVE_PATH,
    grant_event="repository-autonomous-reconciliation-granted",
    revoke_event="repository-autonomous-reconciliation-revoked",
    error_type=RepositoryReconciliationAuthorityError,
    policy_version=1,
)


def _safe_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal path is invalid"
        )
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal path must be normalized and relative"
        )
    return value


def proposal_path(run_directory: Path, ticket_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", ticket_id):
        raise RepositoryReconciliationAuthorityError("ticket ID is unsafe")
    return run_directory / "artifacts" / PROPOSAL_DIRECTORY / f"{ticket_id}.json"


class RepositoryReconciliationAuthorityStore(RepositoryAuthorityStore):
    """Worktree-stable reconciliation authority and exact proposal guard."""

    def __init__(self, repository: Path):
        super().__init__(repository, _RECONCILIATION_KIND)

    @contextmanager
    def guard_grant(self, grant_id: str, grant_digest: str) -> Iterator[dict[str, Any]]:
        with self.locked():
            record = self._load_unlocked()
            if (
                record is None
                or record[0]["schema"] == 1
                or record[0]["revocation"] is not None
            ):
                raise RepositoryReconciliationAuthorityError(
                    "repository reconciliation authority is not active"
                )
            grant = record[0]["grant"]
            if grant["grant_id"] != grant_id or grant["grant_digest"] != grant_digest:
                raise RepositoryReconciliationAuthorityError(
                    "reconciliation proposal authority is stale"
                )
            yield grant


def load_proposal(
    path: Path,
    *,
    grant: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        path.is_symlink()
        or not path.is_file()
        or path.parent.is_symlink()
        or path.parent.parent.is_symlink()
    ):
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal must be a regular non-symlink file"
        )
    try:
        proposal = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal is unreadable"
        ) from error
    keys = {
        "schema", "binding", "authority", "run_id", "ticket_id", "ticket_digest",
        "candidate_ref", "branch", "old_remote_head", "old_local_head", "old_local_tree", "old_target_sha",
        "old_target_tree", "new_target_sha", "new_target_tree", "conflict_paths",
        "resolutions", "patch_sha256", "result_tree_oid",
    }
    if not isinstance(proposal, dict) or set(proposal) != keys or proposal.get("schema") != 1:
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal schema is malformed"
        )
    binding = {key: grant[key] for key in ("git_common_dir", "provider", "normalized_remote")}
    if proposal.get("binding") != binding or proposal.get("authority") != {
        "grant_id": grant["grant_id"], "grant_digest": grant["grant_digest"]
    }:
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal binding or authority is stale"
        )
    for field, expected in context.items():
        if proposal.get(field) != expected:
            raise RepositoryReconciliationAuthorityError(
                f"reconciliation proposal {field} drifted"
            )
    if not _HEX_64.fullmatch(str(proposal.get("ticket_digest", ""))):
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal ticket digest is invalid"
        )
    candidate = proposal.get("candidate_ref")
    if (
        not isinstance(candidate, dict)
        or set(candidate)
        != {
            "contract_version",
            "base_tree_oid",
            "candidate_tree_oid",
            "ticket_digest",
        }
        or candidate.get("contract_version") != 2
        or not _HEX_40.fullmatch(str(candidate.get("base_tree_oid", "")))
        or not _HEX_40.fullmatch(str(candidate.get("candidate_tree_oid", "")))
        or candidate.get("ticket_digest") != proposal["ticket_digest"]
        or candidate.get("base_tree_oid") != proposal["old_target_tree"]
        or candidate.get("candidate_tree_oid") != proposal["old_local_tree"]
    ):
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal CandidateRef is invalid"
        )
    for field in (
        "old_remote_head", "old_local_head", "old_local_tree", "old_target_sha",
        "old_target_tree", "new_target_sha", "new_target_tree", "result_tree_oid",
    ):
        if not _HEX_40.fullmatch(str(proposal.get(field, ""))):
            raise RepositoryReconciliationAuthorityError(
                f"reconciliation proposal {field} is not an object ID"
            )
    conflicts = proposal.get("conflict_paths")
    if not isinstance(conflicts, list) or not conflicts:
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal requires conflict paths"
        )
    safe_conflicts = [_safe_relative_path(value) for value in conflicts]
    if safe_conflicts != sorted(set(safe_conflicts)):
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal conflict paths must be sorted and unique"
        )
    resolutions = proposal.get("resolutions")
    if not isinstance(resolutions, list) or len(resolutions) != len(safe_conflicts):
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal resolutions must cover every conflict"
        )
    resolution_paths: list[str] = []
    for resolution in resolutions:
        if not isinstance(resolution, dict):
            raise RepositoryReconciliationAuthorityError(
                "reconciliation proposal resolution is malformed"
            )
        action = resolution.get("action")
        path_value = _safe_relative_path(resolution.get("path"))
        resolution_paths.append(path_value)
        if action == "delete":
            if set(resolution) != {"path", "action"}:
                raise RepositoryReconciliationAuthorityError(
                    "delete resolution has unexpected fields"
                )
        elif action == "write":
            if (
                set(resolution) != {"path", "action", "mode", "blob_oid"}
                or resolution.get("mode") not in _ALLOWED_MODES
                or not _HEX_40.fullmatch(str(resolution.get("blob_oid", "")))
            ):
                raise RepositoryReconciliationAuthorityError(
                    "write resolution is malformed"
                )
        else:
            raise RepositoryReconciliationAuthorityError(
                "reconciliation resolution action is unsupported"
            )
    if resolution_paths != safe_conflicts:
        raise RepositoryReconciliationAuthorityError(
            "reconciliation resolutions do not exactly match conflict paths"
        )
    if proposal.get("patch_sha256") != _digest(resolutions):
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal patch digest is invalid"
        )
    return proposal


def apply_conflict_proposal(
    worktree: Path,
    proposal: Mapping[str, Any],
    *,
    runner: CommandRunner,
) -> dict[str, Any]:
    raw_conflicts = runner.run(
        ["git", "diff", "--name-only", "--diff-filter=U", "-z"], cwd=worktree
    )
    if raw_conflicts.returncode:
        raise RepositoryReconciliationAuthorityError(
            raw_conflicts.stderr or raw_conflicts.stdout or "could not inspect conflicts"
        )
    observed = sorted(path for path in raw_conflicts.stdout.split("\x00") if path)
    if observed != proposal["conflict_paths"]:
        raise RepositoryReconciliationAuthorityError(
            "observed Git conflict paths differ from the exact proposal"
        )
    for resolution in proposal["resolutions"]:
        path = resolution["path"]
        if resolution["action"] == "delete":
            result = runner.run(
                ["git", "rm", "-f", "--ignore-unmatch", "--", path], cwd=worktree
            )
        else:
            oid = resolution["blob_oid"]
            object_type = runner.run(["git", "cat-file", "-t", oid], cwd=worktree)
            if object_type.returncode or object_type.stdout.strip() != "blob":
                raise RepositoryReconciliationAuthorityError(
                    f"resolution blob is unavailable: {path}"
                )
            blob = subprocess.run(
                ["git", "cat-file", "blob", oid],
                cwd=worktree,
                capture_output=True,
                check=False,
            )
            if blob.returncode:
                raise RepositoryReconciliationAuthorityError(
                    f"resolution blob cannot be read: {path}"
                )
            if any(
                marker in blob.stdout
                for marker in (b"<<<<<<<", b"=======", b">>>>>>>")
            ):
                raise RepositoryReconciliationAuthorityError(
                    f"resolution retains conflict markers: {path}"
                )
            result = runner.run(
                ["git", "update-index", "--add", "--cacheinfo", resolution["mode"], oid, path],
                cwd=worktree,
            )
            if not result.returncode:
                result = runner.run(
                    ["git", "checkout-index", "--force", "--", path], cwd=worktree
                )
        if result.returncode:
            raise RepositoryReconciliationAuthorityError(
                result.stderr or result.stdout or f"could not apply resolution: {path}"
            )
    unresolved = runner.run(
        ["git", "diff", "--name-only", "--diff-filter=U"], cwd=worktree
    )
    if unresolved.returncode or unresolved.stdout.strip():
        raise RepositoryReconciliationAuthorityError(
            "reconciliation proposal left unresolved Git entries"
        )
    continued = runner.run(
        ["git", "-c", "core.editor=true", "rebase", "--continue"], cwd=worktree
    )
    if continued.returncode:
        raise RepositoryReconciliationAuthorityError(
            continued.stderr or continued.stdout or "rebase did not complete after exact resolution"
        )
    result_tree = run_git(worktree, "rev-parse", "HEAD^{tree}")
    if result_tree != proposal["result_tree_oid"]:
        raise RepositoryReconciliationAuthorityError(
            "applied reconciliation tree differs from the exact proposal"
        )
    return {
        "schema": 1,
        "grant_id": proposal["authority"]["grant_id"],
        "grant_digest": proposal["authority"]["grant_digest"],
        "proposal_sha256": hashlib.sha256(_canonical_bytes(proposal)).hexdigest(),
        "patch_sha256": proposal["patch_sha256"],
        "conflict_paths": list(proposal["conflict_paths"]),
        "result_head": run_git(worktree, "rev-parse", "HEAD"),
        "result_tree_oid": result_tree,
        "result": "applied",
    }
