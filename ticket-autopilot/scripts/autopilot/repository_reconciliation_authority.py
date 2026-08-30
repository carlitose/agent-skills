"""Persistent repository authority for exact, bounded reconciliation proposals."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import CommandRunner, GitError, common_git_dir, run_git
from .repository_merge_authority import RepositoryBinding


AUTHORITY_SCOPE = "current-and-future-runs"
STATE_RELATIVE_PATH = Path("ticket-autopilot/repository-reconciliation-authority.json")
PROPOSAL_DIRECTORY = "autonomous-reconciliation"
ZERO_HASH = "0" * 64
_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_GRANT_ID = re.compile(r"^rar-[0-9a-f]{20}$")
_ALLOWED_MODES = {"100644", "100755", "120000"}


class RepositoryReconciliationAuthorityError(RuntimeError):
    """Repository reconciliation authority or an exact proposal is unsafe."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_text(value: str, field: str) -> str:
    if not value or value != value.strip():
        raise RepositoryReconciliationAuthorityError(
            f"repository reconciliation authority {field} must be non-empty and trimmed"
        )
    return value


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


class RepositoryReconciliationAuthorityStore:
    """Integrity-wrapped append-only repository reconciliation authority."""

    def __init__(self, repository: Path):
        try:
            self.binding = RepositoryBinding.inspect(repository)
        except Exception as error:
            raise RepositoryReconciliationAuthorityError(str(error)) from error
        common = Path(self.binding.git_common_dir)
        self.path = common / STATE_RELATIVE_PATH
        self.lock_path = self.path.with_suffix(".lock")
        self._lock_depth = 0

    def _assert_safe(self, *paths: Path) -> None:
        common = Path(self.binding.git_common_dir)
        if common.is_symlink() or not common.is_dir():
            raise RepositoryReconciliationAuthorityError(
                "Git common directory is unsafe"
            )
        for path in paths:
            try:
                path.relative_to(common)
            except ValueError as error:
                raise RepositoryReconciliationAuthorityError(
                    "reconciliation authority path escapes Git common state"
                ) from error
            if path.is_symlink() or path.parent.is_symlink():
                raise RepositoryReconciliationAuthorityError(
                    "reconciliation authority paths must not be symbolic links"
                )

    @contextmanager
    def locked(self) -> Iterator[None]:
        if self._lock_depth:
            self._lock_depth += 1
            try:
                yield
            finally:
                self._lock_depth -= 1
            return
        self._assert_safe(self.path, self.lock_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="ascii") as handle:
            try:
                acquire_file_lock(handle, blocking=True)
            except OSError as error:
                raise RepositoryReconciliationAuthorityError(
                    f"repository reconciliation authority is locked: {self.lock_path}"
                ) from error
            try:
                self._lock_depth = 1
                handle.seek(0)
                handle.truncate()
                handle.write(f"{os.getpid()}\n")
                handle.flush()
                os.fsync(handle.fileno())
                yield
            finally:
                self._lock_depth = 0
                release_file_lock(handle)

    @staticmethod
    def _event(
        event: str, details: Mapping[str, Any], sequence: int, previous_hash: str
    ) -> dict[str, Any]:
        unsigned = {
            "sequence": sequence,
            "event": event,
            "details": dict(details),
            "previous_hash": previous_hash,
        }
        return {**unsigned, "hash": _digest(unsigned)}

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        descriptor, raw = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(raw)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            if os.name != "nt":
                descriptor = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        finally:
            temporary.unlink(missing_ok=True)

    def _write(self, state: dict[str, Any]) -> None:
        self._validate(state)
        payload = _canonical_bytes(state)
        envelope = {
            "envelope_schema": 1,
            "integrity": hashlib.sha256(payload).hexdigest(),
            "payload": state,
        }
        self._atomic_write(self.path, _canonical_bytes(envelope) + b"\n")

    def _load_unlocked(self) -> dict[str, Any] | None:
        self._assert_safe(self.path)
        if not self.path.exists():
            return None
        if not self.path.is_file():
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority state is not a regular file"
            )
        try:
            envelope = json.loads(self.path.read_bytes())
        except (OSError, json.JSONDecodeError) as error:
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority state is unreadable"
            ) from error
        if (
            not isinstance(envelope, dict)
            or set(envelope) != {"envelope_schema", "integrity", "payload"}
            or envelope.get("envelope_schema") != 1
            or not isinstance(envelope.get("payload"), dict)
        ):
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority envelope is invalid"
            )
        state = envelope["payload"]
        if hashlib.sha256(_canonical_bytes(state)).hexdigest() != envelope.get(
            "integrity"
        ):
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority integrity mismatch"
            )
        self._validate(state)
        return state

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists() and not self.lock_path.exists():
            return None
        with self.locked():
            return self._load_unlocked()

    def _validate(self, state: dict[str, Any]) -> None:
        if set(state) != {"schema", "binding", "grant", "revocation", "history"} or state.get("schema") != 1:
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority state is malformed"
            )
        binding = self.binding.as_dict()
        if state.get("binding") != binding:
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority binding contradicts repository"
            )
        grant = state.get("grant")
        grant_keys = {
            "schema", "grant_id", "grant_digest", "repository_identity",
            "git_common_dir", "provider", "normalized_remote", "scope",
            "policy_version", "actor", "evidence",
        }
        if (
            not isinstance(grant, dict)
            or set(grant) != grant_keys
            or grant.get("schema") != 1
            or grant.get("scope") != AUTHORITY_SCOPE
            or grant.get("policy_version") != 1
            or not _GRANT_ID.fullmatch(str(grant.get("grant_id", "")))
            or not _HEX_64.fullmatch(str(grant.get("grant_digest", "")))
            or any(grant.get(key) != value for key, value in binding.items())
            or any(not isinstance(grant.get(key), str) or not grant[key] for key in ("actor", "evidence"))
        ):
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority grant is malformed"
            )
        unsigned = {key: value for key, value in grant.items() if key != "grant_digest"}
        identity = {key: value for key, value in unsigned.items() if key != "grant_id"}
        if _digest(unsigned) != grant["grant_digest"] or grant["grant_id"] != f"rar-{_digest(identity)[:20]}":
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority grant digest is invalid"
            )
        revocation = state.get("revocation")
        if revocation is not None and (
            not isinstance(revocation, dict)
            or set(revocation) != {"schema", "grant_id", "grant_digest", "actor", "evidence"}
            or revocation.get("schema") != 1
            or revocation.get("grant_id") != grant["grant_id"]
            or revocation.get("grant_digest") != grant["grant_digest"]
            or any(not isinstance(revocation.get(key), str) or not revocation[key] for key in ("actor", "evidence"))
        ):
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority revocation is malformed"
            )
        history = state.get("history")
        if not isinstance(history, list) or len(history) not in {1, 2}:
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority history is malformed"
            )
        previous = ZERO_HASH
        for sequence, event in enumerate(history, start=1):
            if (
                not isinstance(event, dict)
                or set(event) != {"sequence", "event", "details", "previous_hash", "hash"}
                or event.get("sequence") != sequence
                or event.get("previous_hash") != previous
                or not _HEX_64.fullmatch(str(event.get("hash", "")))
                or _digest({key: value for key, value in event.items() if key != "hash"}) != event.get("hash")
            ):
                raise RepositoryReconciliationAuthorityError(
                    "repository reconciliation authority history chain is invalid"
                )
            previous = event["hash"]
        if history[0].get("event") != "repository-autonomous-reconciliation-granted" or history[0].get("details") != grant:
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority grant event is invalid"
            )
        if revocation is None and len(history) != 1:
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority history has an unexplained event"
            )
        if revocation is not None and (
            len(history) != 2
            or history[1].get("event") != "repository-autonomous-reconciliation-revoked"
            or history[1].get("details") != revocation
        ):
            raise RepositoryReconciliationAuthorityError(
                "repository reconciliation authority revocation event is invalid"
            )

    def grant(self, *, actor: str, evidence: str, scope: str) -> tuple[dict[str, Any], bool]:
        actor = _require_text(actor, "actor")
        evidence = _require_text(evidence, "evidence")
        if scope != AUTHORITY_SCOPE:
            raise RepositoryReconciliationAuthorityError(
                f"repository reconciliation authority scope must be {AUTHORITY_SCOPE!r}"
            )
        with self.locked():
            state = self._load_unlocked()
            if state is not None:
                if state["revocation"] is not None:
                    raise RepositoryReconciliationAuthorityError(
                        "repository reconciliation authority was revoked and cannot be replaced"
                    )
                grant = state["grant"]
                if grant["actor"] == actor and grant["evidence"] == evidence:
                    return grant, True
                raise RepositoryReconciliationAuthorityError(
                    "repository reconciliation authority has contradictory provenance"
                )
            unsigned = {
                "schema": 1,
                "grant_id": "",
                **self.binding.as_dict(),
                "scope": scope,
                "policy_version": 1,
                "actor": actor,
                "evidence": evidence,
            }
            identity = {key: value for key, value in unsigned.items() if key != "grant_id"}
            unsigned["grant_id"] = f"rar-{_digest(identity)[:20]}"
            grant = {**unsigned, "grant_digest": _digest(unsigned)}
            state = {
                "schema": 1,
                "binding": self.binding.as_dict(),
                "grant": grant,
                "revocation": None,
                "history": [self._event("repository-autonomous-reconciliation-granted", grant, 1, ZERO_HASH)],
            }
            self._write(state)
            return grant, False

    def revoke(self, *, actor: str, evidence: str) -> tuple[dict[str, Any], bool]:
        actor = _require_text(actor, "actor")
        evidence = _require_text(evidence, "evidence")
        with self.locked():
            state = self._load_unlocked()
            if state is None:
                raise RepositoryReconciliationAuthorityError(
                    "repository reconciliation authority does not exist"
                )
            existing = state["revocation"]
            if existing is not None:
                if existing["actor"] == actor and existing["evidence"] == evidence:
                    return existing, True
                raise RepositoryReconciliationAuthorityError(
                    "repository reconciliation authority has a contradictory revocation"
                )
            grant = state["grant"]
            revocation = {
                "schema": 1,
                "grant_id": grant["grant_id"],
                "grant_digest": grant["grant_digest"],
                "actor": actor,
                "evidence": evidence,
            }
            state["revocation"] = revocation
            state["history"].append(
                self._event(
                    "repository-autonomous-reconciliation-revoked",
                    revocation,
                    2,
                    state["history"][-1]["hash"],
                )
            )
            self._write(state)
            return revocation, False

    def active_grant(self) -> dict[str, Any] | None:
        state = self.load()
        if state is None or state["revocation"] is not None:
            return None
        return state["grant"]

    def inspect(self) -> dict[str, Any]:
        state = self.load()
        if state is None:
            return {"schema": 1, "status": "absent", "binding": self.binding.as_dict(), "grant": None, "revocation": None}
        return {
            "schema": 1,
            "status": "revoked" if state["revocation"] else "active",
            "binding": state["binding"],
            "grant": state["grant"],
            "revocation": state["revocation"],
        }

    @contextmanager
    def guard_grant(self, grant_id: str, grant_digest: str) -> Iterator[dict[str, Any]]:
        with self.locked():
            state = self._load_unlocked()
            if state is None or state["revocation"] is not None:
                raise RepositoryReconciliationAuthorityError(
                    "repository reconciliation authority is not active"
                )
            grant = state["grant"]
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
    binding = {key: grant[key] for key in ("repository_identity", "git_common_dir", "provider", "normalized_remote")}
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
