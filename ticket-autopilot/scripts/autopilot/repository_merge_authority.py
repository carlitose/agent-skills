"""Repository-wide autonomous merge authority and canonical run discovery."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import common_git_dir, origin_url, repository_root
from .providers import detect_provider
from .repository_bootstrap import normalized_github_remote


AUTHORITY_SCOPE = "current-and-future-runs"
STATE_RELATIVE_PATH = Path("ticket-autopilot/repository-merge-authority.json")
SCHEDULER_LOCK_RELATIVE_PATH = Path("ticket-autopilot/repository-merge-all.lock")
ADOPTION_PREFIX = "repository-autonomous-merge:"
ZERO_HASH = "0" * 64
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_GRANT_ID = re.compile(r"^rma-[0-9a-f]{20}$")


class RepositoryMergeAuthorityError(RuntimeError):
    """Repository merge authority is absent, contradictory, corrupt, or unsafe."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_text(value: str, *, field: str) -> str:
    if not value or value != value.strip():
        raise RepositoryMergeAuthorityError(
            f"repository merge authority {field} must be non-empty and trimmed"
        )
    return value


def _normalized_remote(provider: str, remote: str) -> str:
    if provider == "github":
        try:
            return normalized_github_remote(remote)
        except Exception as error:
            raise RepositoryMergeAuthorityError(str(error)) from error
    try:
        parsed = urlparse(remote)
    except ValueError as error:
        raise RepositoryMergeAuthorityError("origin URL is invalid") from error
    if parsed.password or parsed.query or parsed.fragment:
        raise RepositoryMergeAuthorityError(
            "origin URL must not contain credentials or parameters"
        )
    # Non-GitHub adapters do not yet expose a canonical repository parser. Bind a digest
    # of the exact trimmed URL rather than guessing equivalence or persisting credentials.
    return f"{provider}:sha256:{hashlib.sha256(remote.strip().encode('utf-8')).hexdigest()}"


@dataclass(frozen=True)
class RepositoryBinding:
    repository_identity: str
    git_common_dir: str
    provider: str
    normalized_remote: str

    @classmethod
    def inspect(cls, repository: Path) -> "RepositoryBinding":
        root = repository_root(repository)
        remote = origin_url(root)
        if not remote:
            raise RepositoryMergeAuthorityError(
                "repository-wide merge authority requires an origin"
            )
        provider = detect_provider(remote).name
        return cls(
            repository_identity=str(root),
            git_common_dir=str(common_git_dir(root)),
            provider=provider,
            normalized_remote=_normalized_remote(provider, remote),
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "repository_identity": self.repository_identity,
            "git_common_dir": self.git_common_dir,
            "provider": self.provider,
            "normalized_remote": self.normalized_remote,
        }


class RepositoryMergeAuthorityStore:
    """Integrity-wrapped authority state serialized by one Git-common lock."""

    def __init__(self, repository: Path):
        self.binding = RepositoryBinding.inspect(repository)
        common = Path(self.binding.git_common_dir)
        self.path = common / STATE_RELATIVE_PATH
        self.lock_path = self.path.with_suffix(".lock")
        self.scheduler_lock_path = common / SCHEDULER_LOCK_RELATIVE_PATH
        self._lock_depth = 0

    def _assert_safe_paths(self, *paths: Path) -> None:
        common = Path(self.binding.git_common_dir)
        if common.is_symlink() or not common.is_dir():
            raise RepositoryMergeAuthorityError("Git common directory is unsafe")
        for path in paths:
            try:
                path.relative_to(common)
            except ValueError as error:
                raise RepositoryMergeAuthorityError(
                    "repository authority path escapes Git common state"
                ) from error
            if path.is_symlink() or path.parent.is_symlink():
                raise RepositoryMergeAuthorityError(
                    "repository authority paths must not be symbolic links"
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
        self._assert_safe_paths(self.path, self.lock_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.parent.is_dir() or self.path.parent.is_symlink():
            raise RepositoryMergeAuthorityError(
                "repository authority directory is unsafe"
            )
        with self.lock_path.open("a+", encoding="ascii") as handle:
            try:
                acquire_file_lock(handle, blocking=True)
            except OSError as error:
                raise RepositoryMergeAuthorityError(
                    f"repository merge authority is locked: {self.lock_path}"
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

    @contextmanager
    def scheduler_locked(self) -> Iterator[None]:
        self._assert_safe_paths(self.scheduler_lock_path)
        self.scheduler_lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.scheduler_lock_path.open("a+", encoding="ascii") as handle:
            try:
                acquire_file_lock(handle, blocking=False)
            except OSError as error:
                raise RepositoryMergeAuthorityError(
                    f"repository merge-all is already running: {self.scheduler_lock_path}"
                ) from error
            try:
                handle.seek(0)
                handle.truncate()
                handle.write(f"{os.getpid()}\n")
                handle.flush()
                os.fsync(handle.fileno())
                yield
            finally:
                release_file_lock(handle)

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        descriptor, raw_tmp = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(raw_tmp)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            if os.name != "nt":
                directory = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
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
        self._assert_safe_paths(self.path)
        if not self.path.exists():
            return None
        if not self.path.is_file():
            raise RepositoryMergeAuthorityError(
                "repository merge authority state is not a regular file"
            )
        try:
            envelope = json.loads(self.path.read_bytes())
        except (OSError, json.JSONDecodeError) as error:
            raise RepositoryMergeAuthorityError(
                "repository merge authority state is unreadable"
            ) from error
        if (
            not isinstance(envelope, dict)
            or set(envelope) != {"envelope_schema", "integrity", "payload"}
            or envelope.get("envelope_schema") != 1
            or not isinstance(envelope.get("payload"), dict)
        ):
            raise RepositoryMergeAuthorityError(
                "repository merge authority integrity envelope is invalid"
            )
        state = envelope["payload"]
        if hashlib.sha256(_canonical_bytes(state)).hexdigest() != envelope.get(
            "integrity"
        ):
            raise RepositoryMergeAuthorityError(
                "repository merge authority integrity mismatch"
            )
        self._validate(state)
        return state

    def load(self) -> dict[str, Any] | None:
        self._assert_safe_paths(self.path, self.lock_path)
        if not self.path.exists() and not self.lock_path.exists():
            return None
        with self.locked():
            return self._load_unlocked()

    def _validate(self, state: dict[str, Any]) -> None:
        if set(state) != {
            "schema",
            "binding",
            "grant",
            "revocation",
            "history",
        } or state.get("schema") != 1:
            raise RepositoryMergeAuthorityError(
                "repository merge authority state is malformed"
            )
        if state.get("binding") != self.binding.as_dict():
            raise RepositoryMergeAuthorityError(
                "repository merge authority binding contradicts the repository"
            )
        grant = state.get("grant")
        expected_grant_keys = {
            "schema",
            "grant_id",
            "grant_digest",
            "repository_identity",
            "git_common_dir",
            "provider",
            "normalized_remote",
            "scope",
            "actor",
            "evidence",
        }
        if (
            not isinstance(grant, dict)
            or set(grant) != expected_grant_keys
            or grant.get("schema") != 1
            or grant.get("scope") != AUTHORITY_SCOPE
            or not _GRANT_ID.fullmatch(str(grant.get("grant_id", "")))
            or not _HEX_64.fullmatch(str(grant.get("grant_digest", "")))
            or any(
                grant.get(field) != value
                for field, value in self.binding.as_dict().items()
            )
            or any(
                not isinstance(grant.get(field), str) or not grant[field]
                for field in ("actor", "evidence")
            )
        ):
            raise RepositoryMergeAuthorityError(
                "repository merge authority grant is malformed"
            )
        unsigned = {key: value for key, value in grant.items() if key != "grant_digest"}
        identity = {
            key: value
            for key, value in unsigned.items()
            if key != "grant_id"
        }
        if (
            _digest(unsigned) != grant["grant_digest"]
            or grant["grant_id"] != f"rma-{_digest(identity)[:20]}"
        ):
            raise RepositoryMergeAuthorityError(
                "repository merge authority grant digest is invalid"
            )
        revocation = state.get("revocation")
        if revocation is not None and (
            not isinstance(revocation, dict)
            or set(revocation)
            != {"schema", "grant_id", "grant_digest", "actor", "evidence"}
            or revocation.get("schema") != 1
            or revocation.get("grant_id") != grant["grant_id"]
            or revocation.get("grant_digest") != grant["grant_digest"]
            or any(
                not isinstance(revocation.get(field), str) or not revocation[field]
                for field in ("actor", "evidence")
            )
        ):
            raise RepositoryMergeAuthorityError(
                "repository merge authority revocation is malformed"
            )
        history = state.get("history")
        if not isinstance(history, list) or len(history) not in {1, 2}:
            raise RepositoryMergeAuthorityError(
                "repository merge authority history is malformed"
            )
        previous_hash = ZERO_HASH
        for sequence, event in enumerate(history, start=1):
            if (
                not isinstance(event, dict)
                or set(event) != {
                    "sequence",
                    "event",
                    "details",
                    "previous_hash",
                    "hash",
                }
                or event.get("sequence") != sequence
                or event.get("previous_hash") != previous_hash
                or not _HEX_64.fullmatch(str(event.get("hash", "")))
            ):
                raise RepositoryMergeAuthorityError(
                    "repository merge authority history chain is invalid"
                )
            unsigned_event = {key: value for key, value in event.items() if key != "hash"}
            if _digest(unsigned_event) != event["hash"]:
                raise RepositoryMergeAuthorityError(
                    "repository merge authority history hash is invalid"
                )
            previous_hash = event["hash"]
        if history[0].get("event") != "repository-autonomous-merge-granted" or history[
            0
        ].get("details") != grant:
            raise RepositoryMergeAuthorityError(
                "repository merge authority grant event is invalid"
            )
        if revocation is None and len(history) != 1:
            raise RepositoryMergeAuthorityError(
                "repository merge authority history contains an unexplained event"
            )
        if revocation is not None and (
            len(history) != 2
            or history[1].get("event")
            != "repository-autonomous-merge-revoked"
            or history[1].get("details") != revocation
        ):
            raise RepositoryMergeAuthorityError(
                "repository merge authority revocation event is invalid"
            )

    @staticmethod
    def _event(
        event: str, details: dict[str, Any], *, sequence: int, previous_hash: str
    ) -> dict[str, Any]:
        value = {
            "sequence": sequence,
            "event": event,
            "details": details,
            "previous_hash": previous_hash,
        }
        return {**value, "hash": _digest(value)}

    def grant(
        self, *, actor: str, evidence: str, scope: str
    ) -> tuple[dict[str, Any], bool]:
        actor = _require_text(actor, field="actor")
        evidence = _require_text(evidence, field="evidence")
        if scope != AUTHORITY_SCOPE:
            raise RepositoryMergeAuthorityError(
                f"repository merge authority scope must be {AUTHORITY_SCOPE!r}"
            )
        with self.locked():
            existing = self._load_unlocked()
            if existing is not None:
                grant = existing["grant"]
                if existing["revocation"] is not None:
                    raise RepositoryMergeAuthorityError(
                        "repository merge authority was revoked and cannot be replaced"
                    )
                if grant["actor"] == actor and grant["evidence"] == evidence:
                    return grant, True
                raise RepositoryMergeAuthorityError(
                    "repository merge authority already has contradictory provenance"
                )
            unsigned = {
                "schema": 1,
                "grant_id": "",
                **self.binding.as_dict(),
                "scope": scope,
                "actor": actor,
                "evidence": evidence,
            }
            # The stable ID is derived from the binding/provenance without recursively
            # including either ID or digest.
            identity_digest = _digest(
                {key: value for key, value in unsigned.items() if key != "grant_id"}
            )
            unsigned["grant_id"] = f"rma-{identity_digest[:20]}"
            grant_digest = _digest(unsigned)
            grant = {**unsigned, "grant_digest": grant_digest}
            state = {
                "schema": 1,
                "binding": self.binding.as_dict(),
                "grant": grant,
                "revocation": None,
                "history": [
                    self._event(
                        "repository-autonomous-merge-granted",
                        grant,
                        sequence=1,
                        previous_hash=ZERO_HASH,
                    )
                ],
            }
            self._write(state)
            return grant, False

    def revoke(self, *, actor: str, evidence: str) -> tuple[dict[str, Any], bool]:
        actor = _require_text(actor, field="actor")
        evidence = _require_text(evidence, field="evidence")
        with self.locked():
            state = self._load_unlocked()
            if state is None:
                raise RepositoryMergeAuthorityError(
                    "repository merge authority does not exist"
                )
            existing = state["revocation"]
            if existing is not None:
                if existing["actor"] == actor and existing["evidence"] == evidence:
                    return existing, True
                raise RepositoryMergeAuthorityError(
                    "repository merge authority has a contradictory revocation"
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
                    "repository-autonomous-merge-revoked",
                    revocation,
                    sequence=2,
                    previous_hash=state["history"][-1]["hash"],
                )
            )
            self._write(state)
            return revocation, False

    def inspect(self) -> dict[str, Any]:
        state = self.load()
        if state is None:
            return {
                "schema": 1,
                "status": "absent",
                "binding": self.binding.as_dict(),
                "grant": None,
                "revocation": None,
            }
        return {
            "schema": 1,
            "status": "revoked" if state["revocation"] else "active",
            "binding": state["binding"],
            "grant": state["grant"],
            "revocation": state["revocation"],
        }

    def active_grant(self) -> dict[str, Any] | None:
        state = self.load()
        return (
            state["grant"]
            if state is not None and state["revocation"] is None
            else None
        )

    @staticmethod
    def adoption_evidence(grant: dict[str, Any]) -> str:
        return (
            f"{ADOPTION_PREFIX}{grant['grant_id']}:{grant['grant_digest']}"
        )

    def _assert_run_grant_unlocked(
        self, run_grant: dict[str, Any]
    ) -> dict[str, Any]:
        state = self._load_unlocked()
        if state is None or state["revocation"] is not None:
            raise RepositoryMergeAuthorityError(
                "repository-wide autonomous merge authority is not active"
            )
        grant = state["grant"]
        expected_evidence = self.adoption_evidence(grant)
        if (
            not isinstance(run_grant, dict)
            or run_grant.get("repository_identity")
            != self.binding.repository_identity
            or run_grant.get("provider") != self.binding.provider
            or run_grant.get("actor") != grant["actor"]
            or run_grant.get("evidence") != expected_evidence
        ):
            raise RepositoryMergeAuthorityError(
                "run autonomous grant does not match active repository authority"
            )
        return grant

    def assert_run_grant(self, run_grant: dict[str, Any]) -> dict[str, Any]:
        with self.locked():
            return self._assert_run_grant_unlocked(run_grant)

    @contextmanager
    def guard_run_grant(
        self, run_grant: dict[str, Any]
    ) -> Iterator[dict[str, Any]]:
        # Keep revocation serialized from the final authority check through provider
        # mutation and readback. A revoke therefore has a deterministic before/after order.
        with self.locked():
            grant = self._assert_run_grant_unlocked(run_grant)
            yield grant


def is_repository_adoption_evidence(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith(ADOPTION_PREFIX):
        return False
    parts = value[len(ADOPTION_PREFIX) :].split(":")
    return (
        len(parts) == 2
        and _GRANT_ID.fullmatch(parts[0]) is not None
        and _HEX_64.fullmatch(parts[1]) is not None
    )


def discover_run_ledgers(repository: Path) -> list[Path]:
    """Return canonical run ledgers without following symlinks or escaping Git state."""

    common = common_git_dir(repository)
    runs = common / "ticket-autopilot" / "runs"
    if not runs.exists():
        return []
    if runs.is_symlink() or not runs.is_dir():
        raise RepositoryMergeAuthorityError("run ledger directory is unsafe")
    ledgers: list[Path] = []
    for child in sorted(runs.iterdir(), key=lambda path: path.name):
        if child.is_symlink():
            raise RepositoryMergeAuthorityError(
                f"run state path must not be a symbolic link: {child.name}"
            )
        if not child.is_dir():
            continue
        ledger = child / "ledger.json"
        if not ledger.exists():
            continue
        if ledger.is_symlink() or not ledger.is_file():
            raise RepositoryMergeAuthorityError(
                f"run ledger must be a regular file: {child.name}"
            )
        resolved = ledger.resolve()
        try:
            resolved.relative_to(runs.resolve())
        except ValueError as error:
            raise RepositoryMergeAuthorityError(
                f"run ledger escapes Git common state: {child.name}"
            ) from error
        ledgers.append(resolved)
    return ledgers
