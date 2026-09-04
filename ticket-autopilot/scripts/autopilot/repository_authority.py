"""Worktree-stable repository-authority state and explicit legacy migration."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Type
from urllib.parse import urlparse

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import common_git_dir, origin_url, repository_root
from .providers import detect_provider
from .repository_bootstrap import normalized_github_remote


AUTHORITY_SCOPE = "current-and-future-runs"
AUTHORITY_STATE_SCHEMA = 2
ZERO_HASH = "0" * 64
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def normalized_remote(provider: str, remote: str) -> str:
    if provider == "github":
        try:
            return normalized_github_remote(remote)
        except Exception as error:
            raise ValueError(str(error)) from error
    try:
        parsed = urlparse(remote)
    except ValueError as error:
        raise ValueError("origin URL is invalid") from error
    if parsed.password or parsed.query or parsed.fragment:
        raise ValueError("origin URL must not contain credentials or parameters")
    return f"{provider}:sha256:{hashlib.sha256(remote.strip().encode('utf-8')).hexdigest()}"


@dataclass(frozen=True)
class RepositoryBinding:
    """Stable authority identity plus the non-authoritative observing worktree."""

    observed_repository_root: str
    git_common_dir: str
    provider: str
    normalized_remote: str

    @classmethod
    def inspect(cls, repository: Path) -> "RepositoryBinding":
        root = repository_root(repository)
        remote = origin_url(root)
        if not remote:
            raise ValueError("repository authority requires an origin")
        provider = detect_provider(remote).name
        return cls(
            observed_repository_root=str(root),
            git_common_dir=str(common_git_dir(root)),
            provider=provider,
            normalized_remote=normalized_remote(provider, remote),
        )

    @property
    def repository_identity(self) -> str:
        """Compatibility accessor for run-local, checkout-bound records."""

        return self.observed_repository_root

    def as_dict(self) -> dict[str, str]:
        """Return only fields that confer repository-wide authority."""

        return {
            "git_common_dir": self.git_common_dir,
            "provider": self.provider,
            "normalized_remote": self.normalized_remote,
        }

    def legacy_dict(self) -> dict[str, str]:
        return {
            "repository_identity": self.observed_repository_root,
            **self.as_dict(),
        }

    def observation(self) -> dict[str, str]:
        return {"repository_root": self.observed_repository_root}


@dataclass(frozen=True)
class AuthorityKind:
    name: str
    grant_prefix: str
    state_relative_path: Path
    grant_event: str
    revoke_event: str
    error_type: Type[RuntimeError]
    policy_version: int | None = None


class RepositoryAuthorityStore:
    """Versioned authority state shared by merge and reconciliation boundaries."""

    def __init__(self, repository: Path, kind: AuthorityKind):
        self.kind = kind
        try:
            self.binding = RepositoryBinding.inspect(repository)
        except Exception as error:
            raise self._error(str(error)) from error
        common = Path(self.binding.git_common_dir)
        self.path = common / kind.state_relative_path
        self.lock_path = self.path.with_suffix(".lock")
        self.migration_dir = (
            common / "ticket-autopilot" / "repository-authority-migrations" / kind.name
        )
        self._lock_depth = 0

    def _error(self, message: str) -> RuntimeError:
        return self.kind.error_type(message)

    def _require_text(self, value: str, field: str) -> str:
        if not value or value != value.strip():
            raise self._error(
                f"repository {self.kind.name} authority {field} must be non-empty and trimmed"
            )
        return value

    def _assert_safe_paths(self, *paths: Path) -> None:
        common = Path(self.binding.git_common_dir)
        if common.is_symlink() or not common.is_dir():
            raise self._error("Git common directory is unsafe")
        for path in paths:
            try:
                path.relative_to(common)
            except ValueError as error:
                raise self._error("repository authority path escapes Git common state") from error
            current = path
            while current != common:
                if current.is_symlink():
                    raise self._error(
                        "repository authority paths must not be symbolic links"
                    )
                current = current.parent

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
            raise self._error("repository authority directory is unsafe")
        with self.lock_path.open("a+", encoding="ascii") as handle:
            try:
                acquire_file_lock(handle, blocking=True)
            except OSError as error:
                raise self._error(
                    f"repository {self.kind.name} authority is locked: {self.lock_path}"
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

    def _write_envelope(self, path: Path, payload: dict[str, Any]) -> None:
        envelope = {
            "envelope_schema": 1,
            "integrity": digest(payload),
            "payload": payload,
        }
        self._atomic_write(path, canonical_bytes(envelope) + b"\n")

    def _read_envelope(self, path: Path, description: str) -> tuple[dict[str, Any], str]:
        self._assert_safe_paths(path)
        if not path.is_file():
            raise self._error(f"{description} is not a regular file")
        try:
            raw = path.read_bytes()
            envelope = json.loads(raw)
        except (OSError, json.JSONDecodeError) as error:
            raise self._error(f"{description} is unreadable") from error
        if (
            not isinstance(envelope, dict)
            or set(envelope) != {"envelope_schema", "integrity", "payload"}
            or envelope.get("envelope_schema") != 1
            or not isinstance(envelope.get("payload"), dict)
        ):
            raise self._error(f"{description} integrity envelope is invalid")
        if envelope.get("integrity") != digest(envelope["payload"]):
            raise self._error(f"{description} integrity mismatch")
        return envelope["payload"], hashlib.sha256(raw).hexdigest()

    def _event(
        self, event: str, details: dict[str, Any], sequence: int, previous_hash: str
    ) -> dict[str, Any]:
        unsigned = {
            "sequence": sequence,
            "event": event,
            "details": details,
            "previous_hash": previous_hash,
        }
        return {**unsigned, "hash": digest(unsigned)}

    def _grant_keys(self, schema: int) -> set[str]:
        observed = "repository_identity" if schema == 1 else "observed_repository_root"
        keys = {
            "schema",
            "grant_id",
            "grant_digest",
            observed,
            "git_common_dir",
            "provider",
            "normalized_remote",
            "scope",
            "actor",
            "evidence",
        }
        if self.kind.policy_version is not None:
            keys.add("policy_version")
        return keys

    def _validate_grant(
        self,
        grant: Any,
        *,
        schema: int,
        binding: dict[str, str],
    ) -> dict[str, Any]:
        if (
            not isinstance(grant, dict)
            or set(grant) != self._grant_keys(schema)
            or grant.get("schema") != schema
            or grant.get("scope") != AUTHORITY_SCOPE
            or not re.fullmatch(
                rf"{re.escape(self.kind.grant_prefix)}-[0-9a-f]{{20}}",
                str(grant.get("grant_id", "")),
            )
            or not _HEX_64.fullmatch(str(grant.get("grant_digest", "")))
            or any(grant.get(field) != value for field, value in binding.items())
            or any(
                not isinstance(grant.get(field), str) or not grant[field]
                for field in ("actor", "evidence")
            )
            or (
                self.kind.policy_version is not None
                and grant.get("policy_version") != self.kind.policy_version
            )
        ):
            raise self._error(f"repository {self.kind.name} authority grant is malformed")
        observed = "repository_identity" if schema == 1 else "observed_repository_root"
        if not isinstance(grant.get(observed), str) or not grant[observed]:
            raise self._error(f"repository {self.kind.name} authority grant is malformed")
        unsigned = {key: value for key, value in grant.items() if key != "grant_digest"}
        identity = {key: value for key, value in unsigned.items() if key != "grant_id"}
        if (
            digest(unsigned) != grant["grant_digest"]
            or grant["grant_id"] != f"{self.kind.grant_prefix}-{digest(identity)[:20]}"
        ):
            raise self._error(
                f"repository {self.kind.name} authority grant digest is invalid"
            )
        return grant

    def _validate_revocation(
        self, revocation: Any, grant: dict[str, Any], *, schema: int
    ) -> dict[str, Any] | None:
        if revocation is None:
            return None
        if (
            not isinstance(revocation, dict)
            or set(revocation)
            != {"schema", "grant_id", "grant_digest", "actor", "evidence"}
            or revocation.get("schema") != schema
            or revocation.get("grant_id") != grant["grant_id"]
            or revocation.get("grant_digest") != grant["grant_digest"]
            or any(
                not isinstance(revocation.get(field), str) or not revocation[field]
                for field in ("actor", "evidence")
            )
        ):
            raise self._error(
                f"repository {self.kind.name} authority revocation is malformed"
            )
        return revocation

    def _validate_history(
        self,
        history: Any,
        grant: dict[str, Any],
        revocation: dict[str, Any] | None,
        *,
        migration: dict[str, Any] | None,
    ) -> None:
        expected = [(self.kind.grant_event, grant)]
        predecessor_revoked = False
        if migration is not None:
            predecessor_revoked = bool(migration.get("predecessor_revoked"))
        if revocation is not None and predecessor_revoked:
            expected.append((self.kind.revoke_event, revocation))
        if migration is not None:
            expected.append(("repository-authority-migrated", migration))
        if revocation is not None and not predecessor_revoked:
            expected.append((self.kind.revoke_event, revocation))
        if not isinstance(history, list) or len(history) != len(expected):
            raise self._error(f"repository {self.kind.name} authority history is malformed")
        previous = ZERO_HASH
        for sequence, (event, pair) in enumerate(zip(history, expected), start=1):
            expected_name, expected_details = pair
            if (
                not isinstance(event, dict)
                or set(event) != {"sequence", "event", "details", "previous_hash", "hash"}
                or event.get("sequence") != sequence
                or event.get("event") != expected_name
                or event.get("details") != expected_details
                or event.get("previous_hash") != previous
                or not _HEX_64.fullmatch(str(event.get("hash", "")))
                or digest({key: value for key, value in event.items() if key != "hash"})
                != event.get("hash")
            ):
                raise self._error(
                    f"repository {self.kind.name} authority history chain is invalid"
                )
            previous = event["hash"]

    def _validate_legacy(self, state: dict[str, Any]) -> None:
        if (
            set(state) != {"schema", "binding", "grant", "revocation", "history"}
            or state.get("schema") != 1
            or not isinstance(state.get("binding"), dict)
            or set(state["binding"])
            != {"repository_identity", "git_common_dir", "provider", "normalized_remote"}
        ):
            raise self._error(
                f"repository {self.kind.name} authority state is malformed"
            )
        stable = {key: state["binding"].get(key) for key in self.binding.as_dict()}
        if stable != self.binding.as_dict():
            raise self._error(
                f"repository {self.kind.name} authority binding contradicts repository"
            )
        grant = self._validate_grant(state.get("grant"), schema=1, binding=state["binding"])
        revocation = self._validate_revocation(state.get("revocation"), grant, schema=1)
        self._validate_history(state.get("history"), grant, revocation, migration=None)

    def _validate_migration(self, migration: Any) -> dict[str, Any]:
        keys = {
            "schema",
            "kind",
            "source_state_sha256",
            "source_repository_identity",
            "target_binding",
            "actor",
            "evidence",
            "predecessor_grant_id",
            "predecessor_grant_digest",
            "predecessor_revoked",
            "successor_grant_id",
            "successor_grant_digest",
            "migration_digest",
        }
        if (
            not isinstance(migration, dict)
            or set(migration) != keys
            or migration.get("schema") != 1
            or migration.get("kind") != self.kind.name
            or not _HEX_64.fullmatch(str(migration.get("source_state_sha256", "")))
            or migration.get("target_binding") != self.binding.as_dict()
            or any(
                not isinstance(migration.get(field), str) or not migration[field]
                for field in (
                    "source_repository_identity",
                    "actor",
                    "evidence",
                    "predecessor_grant_id",
                    "predecessor_grant_digest",
                    "successor_grant_id",
                    "successor_grant_digest",
                )
            )
            or type(migration.get("predecessor_revoked")) is not bool
            or not _HEX_64.fullmatch(str(migration.get("migration_digest", "")))
            or digest(
                {key: value for key, value in migration.items() if key != "migration_digest"}
            )
            != migration.get("migration_digest")
        ):
            raise self._error(
                f"repository {self.kind.name} authority migration record is malformed"
            )
        return migration

    def _validate_v2(self, state: dict[str, Any]) -> None:
        if (
            set(state)
            != {"schema", "binding", "observation", "grant", "revocation", "history", "provenance"}
            or state.get("schema") != AUTHORITY_STATE_SCHEMA
            or state.get("binding") != self.binding.as_dict()
            or not isinstance(state.get("observation"), dict)
            or set(state["observation"]) != {"repository_root"}
            or not isinstance(state["observation"].get("repository_root"), str)
        ):
            raise self._error(
                f"repository {self.kind.name} authority binding contradicts repository"
            )
        grant = self._validate_grant(
            state.get("grant"), schema=AUTHORITY_STATE_SCHEMA, binding=self.binding.as_dict()
        )
        if (
            state["observation"]["repository_root"]
            != grant["observed_repository_root"]
        ):
            raise self._error(
                f"repository {self.kind.name} authority observation is malformed"
            )
        revocation = self._validate_revocation(
            state.get("revocation"), grant, schema=AUTHORITY_STATE_SCHEMA
        )
        provenance = state.get("provenance")
        if (
            not isinstance(provenance, dict)
            or set(provenance) != {"predecessor", "migration"}
            or (provenance["predecessor"] is None) != (provenance["migration"] is None)
        ):
            raise self._error(
                f"repository {self.kind.name} authority provenance is malformed"
            )
        migration = None
        if provenance["predecessor"] is not None:
            predecessor = provenance["predecessor"]
            if (
                not isinstance(predecessor, dict)
                or set(predecessor) != {"state_sha256", "state"}
                or not _HEX_64.fullmatch(str(predecessor.get("state_sha256", "")))
                or not isinstance(predecessor.get("state"), dict)
            ):
                raise self._error(
                    f"repository {self.kind.name} authority predecessor is malformed"
                )
            self._validate_legacy(predecessor["state"])
            migration = self._validate_migration(provenance["migration"])
            if (
                migration["source_state_sha256"] != predecessor["state_sha256"]
                or migration["source_repository_identity"]
                != predecessor["state"]["binding"]["repository_identity"]
                or migration["predecessor_revoked"]
                != (predecessor["state"]["revocation"] is not None)
                or migration["predecessor_grant_id"]
                != predecessor["state"]["grant"]["grant_id"]
                or migration["predecessor_grant_digest"]
                != predecessor["state"]["grant"]["grant_digest"]
                or migration["successor_grant_id"] != grant["grant_id"]
                or migration["successor_grant_digest"] != grant["grant_digest"]
            ):
                raise self._error(
                    f"repository {self.kind.name} authority migration lineage is invalid"
                )
        self._validate_history(state.get("history"), grant, revocation, migration=migration)

    def _load_unlocked(self) -> tuple[dict[str, Any], str] | None:
        self._assert_safe_paths(self.path)
        if not self.path.exists():
            return None
        state, state_sha256 = self._read_envelope(
            self.path, f"repository {self.kind.name} authority state"
        )
        if state.get("schema") == 1:
            self._validate_legacy(state)
        elif state.get("schema") == AUTHORITY_STATE_SCHEMA:
            self._validate_v2(state)
        else:
            raise self._error(
                f"repository {self.kind.name} authority state schema is unsupported"
            )
        return state, state_sha256

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists() and not self.lock_path.exists():
            return None
        with self.locked():
            record = self._load_unlocked()
            return None if record is None else record[0]

    def _new_grant(self, *, actor: str, evidence: str) -> dict[str, Any]:
        unsigned: dict[str, Any] = {
            "schema": AUTHORITY_STATE_SCHEMA,
            "grant_id": "",
            "observed_repository_root": self.binding.observed_repository_root,
            **self.binding.as_dict(),
            "scope": AUTHORITY_SCOPE,
            "actor": actor,
            "evidence": evidence,
        }
        if self.kind.policy_version is not None:
            unsigned["policy_version"] = self.kind.policy_version
        identity = {key: value for key, value in unsigned.items() if key != "grant_id"}
        unsigned["grant_id"] = f"{self.kind.grant_prefix}-{digest(identity)[:20]}"
        return {**unsigned, "grant_digest": digest(unsigned)}

    def _state(
        self,
        grant: dict[str, Any],
        revocation: dict[str, Any] | None,
        *,
        predecessor: dict[str, Any] | None = None,
        migration: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        history = [self._event(self.kind.grant_event, grant, 1, ZERO_HASH)]
        predecessor_revoked = bool(
            migration is not None and migration.get("predecessor_revoked")
        )
        if revocation is not None and predecessor_revoked:
            history.append(
                self._event(
                    self.kind.revoke_event,
                    revocation,
                    len(history) + 1,
                    history[-1]["hash"],
                )
            )
        if migration is not None:
            history.append(
                self._event(
                    "repository-authority-migrated",
                    migration,
                    len(history) + 1,
                    history[-1]["hash"],
                )
            )
        if revocation is not None and not predecessor_revoked:
            history.append(
                self._event(
                    self.kind.revoke_event,
                    revocation,
                    len(history) + 1,
                    history[-1]["hash"],
                )
            )
        return {
            "schema": AUTHORITY_STATE_SCHEMA,
            "binding": self.binding.as_dict(),
            "observation": self.binding.observation(),
            "grant": grant,
            "revocation": revocation,
            "history": history,
            "provenance": {"predecessor": predecessor, "migration": migration},
        }

    def _write_state(self, state: dict[str, Any]) -> None:
        self._validate_v2(state)
        self._write_envelope(self.path, state)

    def grant(self, *, actor: str, evidence: str, scope: str) -> tuple[dict[str, Any], bool]:
        actor = self._require_text(actor, "actor")
        evidence = self._require_text(evidence, "evidence")
        if scope != AUTHORITY_SCOPE:
            raise self._error(
                f"repository {self.kind.name} authority scope must be {AUTHORITY_SCOPE!r}"
            )
        with self.locked():
            record = self._load_unlocked()
            if record is not None:
                state, _ = record
                if state["schema"] == 1:
                    raise self._error(
                        f"legacy repository {self.kind.name} authority requires explicit migration"
                    )
                if state["revocation"] is not None:
                    raise self._error(
                        f"repository {self.kind.name} authority was revoked and cannot be replaced"
                    )
                grant = state["grant"]
                if grant["actor"] == actor and grant["evidence"] == evidence:
                    return grant, True
                raise self._error(
                    f"repository {self.kind.name} authority has contradictory provenance"
                )
            grant = self._new_grant(actor=actor, evidence=evidence)
            self._write_state(self._state(grant, None))
            return grant, False

    def revoke(self, *, actor: str, evidence: str) -> tuple[dict[str, Any], bool]:
        actor = self._require_text(actor, "actor")
        evidence = self._require_text(evidence, "evidence")
        with self.locked():
            record = self._load_unlocked()
            if record is None:
                raise self._error(
                    f"repository {self.kind.name} authority does not exist"
                )
            state, _ = record
            if state["schema"] == 1:
                raise self._error(
                    f"legacy repository {self.kind.name} authority requires explicit migration"
                )
            existing = state["revocation"]
            if existing is not None:
                if existing["actor"] == actor and existing["evidence"] == evidence:
                    return existing, True
                raise self._error(
                    f"repository {self.kind.name} authority has a contradictory revocation"
                )
            grant = state["grant"]
            revocation = {
                "schema": AUTHORITY_STATE_SCHEMA,
                "grant_id": grant["grant_id"],
                "grant_digest": grant["grant_digest"],
                "actor": actor,
                "evidence": evidence,
            }
            state["revocation"] = revocation
            state["history"].append(
                self._event(
                    self.kind.revoke_event,
                    revocation,
                    len(state["history"]) + 1,
                    state["history"][-1]["hash"],
                )
            )
            self._write_state(state)
            return revocation, False

    def inspect(self) -> dict[str, Any]:
        with self.locked():
            record = self._load_unlocked()
        if record is None:
            return {
                "schema": AUTHORITY_STATE_SCHEMA,
                "status": "absent",
                "binding": self.binding.as_dict(),
                "observation": self.binding.observation(),
                "grant": None,
                "revocation": None,
                "migration": None,
            }
        state, state_sha256 = record
        if state["schema"] == 1:
            original = state["binding"]["repository_identity"]
            sibling = original != self.binding.observed_repository_root
            return {
                "schema": AUTHORITY_STATE_SCHEMA,
                "state_schema": 1,
                "status": (
                    "legacy-binding-migration-required"
                    if sibling
                    else ("revoked" if state["revocation"] else "active")
                ),
                "binding": state["binding"],
                "observation": self.binding.observation(),
                "grant": state["grant"],
                "revocation": state["revocation"],
                "migration": {
                    "required": True,
                    "kind": self.kind.name,
                    "state_sha256": state_sha256,
                    "command": "migrate-repository-authority",
                },
            }
        return {
            "schema": AUTHORITY_STATE_SCHEMA,
            "state_schema": AUTHORITY_STATE_SCHEMA,
            "status": "revoked" if state["revocation"] else "active",
            "binding": state["binding"],
            "observation": self.binding.observation(),
            "grant": state["grant"],
            "revocation": state["revocation"],
            "migration": state["provenance"]["migration"],
        }

    def active_grant(self) -> dict[str, Any] | None:
        state = self.load()
        if state is None:
            return None
        if state["schema"] == 1:
            raise self._error(
                f"legacy repository {self.kind.name} authority requires explicit migration"
            )
        return state["grant"] if state["revocation"] is None else None

    def _validate_original_checkout(self, legacy: dict[str, Any]) -> None:
        original_root = Path(legacy["binding"]["repository_identity"])
        try:
            original = RepositoryBinding.inspect(original_root)
        except Exception as error:
            raise self._error(
                f"legacy repository {self.kind.name} authority original checkout is unavailable"
            ) from error
        if original.legacy_dict() != legacy["binding"]:
            raise self._error(
                f"legacy repository {self.kind.name} authority original checkout binding contradicts state"
            )

    def _migration_paths(self, source_sha256: str) -> tuple[Path, Path]:
        return (
            self.migration_dir / f"{source_sha256}.intent.json",
            self.migration_dir / f"{source_sha256}.receipt.json",
        )

    def _read_exact_payload(
        self, path: Path, expected: dict[str, Any], description: str
    ) -> str:
        payload, file_sha256 = self._read_envelope(path, description)
        if payload != expected:
            raise self._error(f"{description} is contradictory")
        return file_sha256

    def _migration_receipt(
        self,
        *,
        intent_sha256: str,
        migration: dict[str, Any],
        successor_state_sha256: str,
    ) -> dict[str, Any]:
        return {
            "schema": 1,
            "kind": self.kind.name,
            "result": "migrated",
            "source_state_sha256": migration["source_state_sha256"],
            "successor_state_sha256": successor_state_sha256,
            "intent_sha256": intent_sha256,
            "migration_digest": migration["migration_digest"],
            "grant_id": migration["successor_grant_id"],
            "grant_digest": migration["successor_grant_digest"],
            "binding": self.binding.as_dict(),
            "actor": migration["actor"],
            "evidence": migration["evidence"],
        }

    def _read_migration_receipt(
        self,
        path: Path,
        *,
        intent_sha256: str,
        migration: dict[str, Any],
    ) -> dict[str, Any]:
        receipt, _ = self._read_envelope(path, "migration receipt")
        expected = self._migration_receipt(
            intent_sha256=intent_sha256,
            migration=migration,
            successor_state_sha256=str(receipt.get("successor_state_sha256", "")),
        )
        if (
            not _HEX_64.fullmatch(str(receipt.get("successor_state_sha256", "")))
            or receipt != expected
        ):
            raise self._error("migration receipt is contradictory")
        return receipt

    def migrate(
        self, *, expected_state_sha256: str, actor: str, evidence: str
    ) -> tuple[dict[str, Any], bool]:
        if not _HEX_64.fullmatch(expected_state_sha256):
            raise self._error("expected legacy authority state SHA-256 is invalid")
        actor = self._require_text(actor, "migration actor")
        evidence = self._require_text(evidence, "migration evidence")
        with self.locked():
            record = self._load_unlocked()
            if record is None:
                raise self._error(
                    f"repository {self.kind.name} authority does not exist"
                )
            state, observed_sha256 = record
            intent_path, receipt_path = self._migration_paths(expected_state_sha256)
            self._assert_safe_paths(intent_path, receipt_path)
            if state["schema"] == AUTHORITY_STATE_SCHEMA:
                migration = state["provenance"]["migration"]
                if (
                    not isinstance(migration, dict)
                    or migration["source_state_sha256"] != expected_state_sha256
                    or migration["actor"] != actor
                    or migration["evidence"] != evidence
                ):
                    raise self._error(
                        f"repository {self.kind.name} authority migration is contradictory"
                    )
                intent = {
                    "schema": 1,
                    "kind": self.kind.name,
                    "state_path": str(self.path),
                    "source_state_sha256": expected_state_sha256,
                    "source_repository_identity": migration["source_repository_identity"],
                    "target_binding": self.binding.as_dict(),
                    "actor": actor,
                    "evidence": evidence,
                }
                intent_sha256 = self._read_exact_payload(
                    intent_path, intent, "migration intent"
                )
                if receipt_path.exists():
                    receipt = self._read_migration_receipt(
                        receipt_path,
                        intent_sha256=intent_sha256,
                        migration=migration,
                    )
                else:
                    receipt = self._migration_receipt(
                        intent_sha256=intent_sha256,
                        migration=migration,
                        successor_state_sha256=observed_sha256,
                    )
                    self._write_envelope(receipt_path, receipt)
                    receipt = self._read_migration_receipt(
                        receipt_path,
                        intent_sha256=intent_sha256,
                        migration=migration,
                    )
                return receipt, True
            if observed_sha256 != expected_state_sha256:
                raise self._error(
                    f"repository {self.kind.name} authority state SHA-256 drifted"
                )
            self._validate_original_checkout(state)
            self.migration_dir.mkdir(parents=True, exist_ok=True)
            if self.migration_dir.is_symlink() or not self.migration_dir.is_dir():
                raise self._error("repository authority migration directory is unsafe")
            intent = {
                "schema": 1,
                "kind": self.kind.name,
                "state_path": str(self.path),
                "source_state_sha256": expected_state_sha256,
                "source_repository_identity": state["binding"]["repository_identity"],
                "target_binding": self.binding.as_dict(),
                "actor": actor,
                "evidence": evidence,
            }
            if not intent_path.exists():
                self._write_envelope(intent_path, intent)
            intent_sha256 = self._read_exact_payload(
                intent_path, intent, "migration intent"
            )
            grant = self._new_grant(
                actor=state["grant"]["actor"], evidence=state["grant"]["evidence"]
            )
            unsigned_migration = {
                "schema": 1,
                "kind": self.kind.name,
                "source_state_sha256": expected_state_sha256,
                "source_repository_identity": state["binding"]["repository_identity"],
                "target_binding": self.binding.as_dict(),
                "actor": actor,
                "evidence": evidence,
                "predecessor_grant_id": state["grant"]["grant_id"],
                "predecessor_grant_digest": state["grant"]["grant_digest"],
                "predecessor_revoked": state["revocation"] is not None,
                "successor_grant_id": grant["grant_id"],
                "successor_grant_digest": grant["grant_digest"],
            }
            migration = {
                **unsigned_migration,
                "migration_digest": digest(unsigned_migration),
            }
            revocation = None
            if state["revocation"] is not None:
                revocation = {
                    "schema": AUTHORITY_STATE_SCHEMA,
                    "grant_id": grant["grant_id"],
                    "grant_digest": grant["grant_digest"],
                    "actor": state["revocation"]["actor"],
                    "evidence": state["revocation"]["evidence"],
                }
            successor = self._state(
                grant,
                revocation,
                predecessor={"state_sha256": expected_state_sha256, "state": state},
                migration=migration,
            )
            self._write_state(successor)
            loaded = self._load_unlocked()
            if loaded is None or loaded[0] != successor:
                raise self._error("repository authority migration readback failed")
            successor_sha256 = loaded[1]
            receipt = self._migration_receipt(
                intent_sha256=intent_sha256,
                migration=migration,
                successor_state_sha256=successor_sha256,
            )
            if receipt_path.exists():
                self._read_exact_payload(receipt_path, receipt, "migration receipt")
            else:
                self._write_envelope(receipt_path, receipt)
                self._read_exact_payload(receipt_path, receipt, "migration receipt")
            return receipt, False
