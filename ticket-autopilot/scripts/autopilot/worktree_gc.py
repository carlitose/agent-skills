"""Manifest-owned, provider-free planning for Ticket Autopilot worktree cleanup."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from .git_ops import (
    GitError,
    common_git_dir,
    origin_url,
    repository_root,
    run_directory,
    run_git,
)
from .ledger import AtomicLedger, LedgerError
from .providers import ProviderError
from .repository_authority import RepositoryBinding, canonical_bytes


OWNER_CONTRACT = "worktree-owner-v1"
PLAN_CONTRACT = "worktree-gc-plan-v1"
OWNER_FILENAME = "worktree-owner.json"
_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_OWNER_FIELDS = {
    "schema",
    "contract_version",
    "run_id",
    "repository_root",
    "git_common_dir",
    "provider",
    "normalized_remote",
    "worktree_path",
    "worktree_git_dir",
    "base_sha",
    "snapshot_manifest_digest",
    "origin",
}
_ENVELOPE_FIELDS = {"envelope_schema", "integrity", "payload"}


class WorktreeGCError(ValueError):
    """A cleanup ownership or planning contract could not be proved."""


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _strict_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise WorktreeGCError(f"{label} must be a non-empty string")
    return value


def _strict_hash(value: object, label: str, pattern: re.Pattern[str]) -> str:
    text = _strict_text(value, label)
    if not pattern.fullmatch(text):
        raise WorktreeGCError(f"{label} is invalid")
    return text


def _canonical_absolute(value: object, label: str) -> Path:
    text = _strict_text(value, label)
    path = Path(text)
    if not path.is_absolute() or os.path.normpath(text) != text:
        raise WorktreeGCError(f"{label} must be canonical and absolute")
    if path.resolve(strict=False) != path:
        raise WorktreeGCError(f"{label} must not contain aliases or symlinks")
    return path


def _assert_no_symlink_components(path: Path, *, allow_missing_leaf: bool = False) -> None:
    parts = path.parts
    current = Path(parts[0])
    for index, part in enumerate(parts[1:], start=1):
        current /= part
        if not current.exists() and not current.is_symlink():
            if allow_missing_leaf and index == len(parts) - 1:
                return
            raise WorktreeGCError(f"path component does not exist: {current}")
        if current.is_symlink():
            raise WorktreeGCError(f"path contains a symlink: {current}")


def _envelope(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "envelope_schema": 1,
        "integrity": _sha256_bytes(canonical_bytes(payload)),
        "payload": payload,
    }


def _validate_envelope(document: object, *, label: str) -> dict[str, Any]:
    if not isinstance(document, dict) or set(document) != _ENVELOPE_FIELDS:
        raise WorktreeGCError(f"{label} envelope fields are invalid")
    if document.get("envelope_schema") != 1:
        raise WorktreeGCError(f"{label} envelope schema is invalid")
    payload = document.get("payload")
    if not isinstance(payload, dict):
        raise WorktreeGCError(f"{label} payload is invalid")
    integrity = _strict_hash(document.get("integrity"), f"{label} integrity", _HEX_64)
    if integrity != _sha256_bytes(canonical_bytes(payload)):
        raise WorktreeGCError(f"{label} integrity does not match payload")
    return payload


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_temporary)
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


def _write_envelope(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    document = _envelope(payload)
    encoded = canonical_bytes(document) + b"\n"
    if path.exists():
        if path.read_bytes() != encoded:
            raise WorktreeGCError(f"immutable record already differs: {path}")
    else:
        _atomic_write(path, encoded)
    readback = json.loads(path.read_text(encoding="utf-8"))
    if _validate_envelope(readback, label=path.name) != payload:
        raise WorktreeGCError(f"record readback differs: {path}")
    return document


def owner_manifest_path(repository: Path, run_id: str) -> Path:
    return run_directory(repository, run_id) / OWNER_FILENAME


def _validate_origin(origin: object) -> dict[str, str]:
    if not isinstance(origin, dict):
        raise WorktreeGCError("owner origin is invalid")
    kind = origin.get("kind")
    if kind == "created-by-run":
        expected = {"kind", "ledger_sha256"}
    elif kind == "legacy-adoption":
        expected = {"kind", "ledger_sha256", "actor", "evidence"}
    else:
        raise WorktreeGCError("owner origin kind is invalid")
    if set(origin) != expected:
        raise WorktreeGCError("owner origin fields are invalid")
    normalized = {key: _strict_text(value, f"owner origin {key}") for key, value in origin.items()}
    _strict_hash(normalized["ledger_sha256"], "owner origin ledger_sha256", _HEX_64)
    return normalized


def validate_owner_manifest(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _OWNER_FIELDS:
        raise WorktreeGCError("owner manifest fields are invalid")
    if payload.get("schema") != 1 or payload.get("contract_version") != OWNER_CONTRACT:
        raise WorktreeGCError("owner manifest contract is invalid")
    run_id = _strict_text(payload.get("run_id"), "owner run_id")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", run_id):
        raise WorktreeGCError("owner run_id is invalid")
    normalized = dict(payload)
    for field in (
        "repository_root",
        "git_common_dir",
        "worktree_path",
        "worktree_git_dir",
    ):
        normalized[field] = str(_canonical_absolute(payload.get(field), f"owner {field}"))
    for field in ("provider", "normalized_remote"):
        normalized[field] = _strict_text(payload.get(field), f"owner {field}")
    normalized["base_sha"] = _strict_hash(payload.get("base_sha"), "owner base_sha", _HEX_40)
    normalized["snapshot_manifest_digest"] = _strict_hash(
        payload.get("snapshot_manifest_digest"),
        "owner snapshot_manifest_digest",
        _HEX_64,
    )
    normalized["origin"] = _validate_origin(payload.get("origin"))
    return normalized


def load_owner_manifest(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorktreeGCError(f"owner manifest is unreadable: {path}") from error
    return validate_owner_manifest(
        _validate_envelope(document, label="owner manifest")
    )


def _repository_binding(repository: Path) -> dict[str, str]:
    root = repository_root(repository)
    remote = origin_url(root)
    if remote is None:
        provider = "unconfigured"
        normalized = "absent"
    elif Path(remote).is_absolute() or remote.startswith("file://"):
        provider = "local-or-unsupported"
        normalized = f"sha256:{_sha256_bytes(remote.encode('utf-8'))}"
    else:
        try:
            inspected = RepositoryBinding.inspect(root)
        except ProviderError:
            parsed = urlparse(remote)
            if parsed.password or parsed.query or parsed.fragment or (
                parsed.scheme in {"http", "https"} and parsed.username
            ):
                raise WorktreeGCError(
                    "unsupported origin URL contains credentials or parameters"
                )
            provider = "local-or-unsupported"
            normalized = f"sha256:{_sha256_bytes(remote.encode('utf-8'))}"
        else:
            provider = inspected.provider
            normalized = inspected.normalized_remote
    return {
        "git_common_dir": str(common_git_dir(root)),
        "provider": provider,
        "normalized_remote": normalized,
    }


def _owner_payload(
    repository: Path,
    ledger: Mapping[str, Any],
    *,
    origin: dict[str, str],
) -> dict[str, Any]:
    binding = _repository_binding(repository)
    worktree = _canonical_absolute(ledger.get("worktree"), "ledger worktree")
    _assert_no_symlink_components(worktree)
    git_dir_raw = run_git(worktree, "rev-parse", "--git-dir")
    git_dir = Path(git_dir_raw)
    if not git_dir.is_absolute():
        git_dir = worktree / git_dir
    git_dir = git_dir.resolve()
    root = repository_root(
        _canonical_absolute(ledger.get("repo"), "ledger repository")
    )
    if common_git_dir(root) != common_git_dir(repository):
        raise WorktreeGCError("ledger repository uses another Git common directory")
    return validate_owner_manifest(
        {
            "schema": 1,
            "contract_version": OWNER_CONTRACT,
            "run_id": _strict_text(ledger.get("run_id"), "ledger run_id"),
            "repository_root": str(root),
            "git_common_dir": binding["git_common_dir"],
            "provider": binding["provider"],
            "normalized_remote": binding["normalized_remote"],
            "worktree_path": str(worktree),
            "worktree_git_dir": str(git_dir),
            "base_sha": _strict_hash(ledger.get("base_sha"), "ledger base_sha", _HEX_40),
            "snapshot_manifest_digest": _strict_hash(
                ledger.get("snapshot_manifest_digest"),
                "ledger snapshot_manifest_digest",
                _HEX_64,
            ),
            "origin": origin,
        }
    )


def persist_created_owner(
    repository: Path,
    ledger_path: Path,
    ledger: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist immutable ownership after the initial ledger has been committed."""

    payload = _owner_payload(
        repository,
        ledger,
        origin={"kind": "created-by-run", "ledger_sha256": _file_sha256(ledger_path)},
    )
    path = owner_manifest_path(repository, str(ledger["run_id"]))
    document = _write_envelope(path, payload)
    return {
        "manifest": payload,
        "manifest_path": str(path),
        "manifest_sha256": _sha256_bytes(canonical_bytes(document) + b"\n"),
        "replayed": False,
    }


def _parse_worktree_inventory(repository: Path) -> list[dict[str, Any]]:
    raw = run_git(repository, "worktree", "list", "--porcelain", "-z")
    records: list[dict[str, Any]] = []
    for raw_record in raw.split("\0\0"):
        tokens = [token for token in raw_record.split("\0") if token]
        if not tokens:
            continue
        record: dict[str, Any] = {"locked": False, "prunable": False}
        for token in tokens:
            key, separator, value = token.partition(" ")
            if key in {"bare", "detached", "locked", "prunable"}:
                record[key] = True
                if separator and value:
                    record[f"{key}_reason"] = value
            elif separator:
                record[key] = value
        if "worktree" not in record or "HEAD" not in record:
            raise WorktreeGCError("Git worktree inventory record is incomplete")
        path = _canonical_absolute(record["worktree"], "Git worktree path")
        record["worktree"] = str(path)
        records.append(record)
    if not records:
        raise WorktreeGCError("Git worktree inventory is empty")
    return records


def _manifest_inventory(common: Path) -> tuple[list[tuple[Path, dict[str, Any]]], list[dict[str, str]]]:
    manifests: list[tuple[Path, dict[str, Any]]] = []
    invalid: list[dict[str, str]] = []
    runs = common / "ticket-autopilot" / "runs"
    if not runs.exists():
        return manifests, invalid
    for path in sorted(runs.glob(f"*/{OWNER_FILENAME}"), key=lambda item: item.as_posix()):
        try:
            manifests.append((path, load_owner_manifest(path)))
        except WorktreeGCError as error:
            invalid.append({"manifest_path": str(path), "reason": str(error)})
    return manifests, invalid


def _assert_registered_owner(
    payload: Mapping[str, Any], inventory: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    matches = [entry for entry in inventory if entry.get("worktree") == payload["worktree_path"]]
    if len(matches) != 1:
        raise WorktreeGCError("owner worktree is not uniquely registered by Git")
    entry = dict(matches[0])
    if entry.get("locked") or entry.get("prunable"):
        raise WorktreeGCError("owner worktree registration is locked or prunable")
    worktree = Path(str(payload["worktree_path"]))
    if run_git(worktree, "rev-parse", "HEAD") != entry["HEAD"]:
        raise WorktreeGCError("owner worktree HEAD differs from Git inventory")
    git_dir_raw = run_git(worktree, "rev-parse", "--git-dir")
    git_dir = Path(git_dir_raw)
    if not git_dir.is_absolute():
        git_dir = worktree / git_dir
    if str(git_dir.resolve()) != payload["worktree_git_dir"]:
        raise WorktreeGCError("owner worktree Git directory differs")
    return entry


def _validate_owner_binding(
    repository: Path,
    payload: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> None:
    binding = _repository_binding(repository)
    if (
        payload["git_common_dir"] != binding["git_common_dir"]
        or payload["provider"] != binding["provider"]
        or payload["normalized_remote"] != binding["normalized_remote"]
    ):
        raise WorktreeGCError("owner repository binding differs")
    if payload["run_id"] != ledger.get("run_id"):
        raise WorktreeGCError("owner run ID differs from ledger")
    if payload["worktree_path"] != ledger.get("worktree"):
        raise WorktreeGCError("owner worktree differs from ledger")
    if payload["base_sha"] != ledger.get("base_sha"):
        raise WorktreeGCError("owner base SHA differs from ledger")
    if payload["snapshot_manifest_digest"] != ledger.get("snapshot_manifest_digest"):
        raise WorktreeGCError("owner ticket snapshot differs from ledger")
    owner_repo = _canonical_absolute(ledger.get("repo"), "ledger repository")
    if str(owner_repo) != payload["repository_root"]:
        raise WorktreeGCError("owner repository root differs from ledger")
    if common_git_dir(owner_repo) != Path(binding["git_common_dir"]):
        raise WorktreeGCError("ledger repository uses another Git common directory")
    expected_parent = owner_repo.parent / f".{owner_repo.name}-ticket-autopilot-worktrees"
    if Path(str(payload["worktree_path"])).parent != expected_parent:
        raise WorktreeGCError("owner worktree is outside its exact managed parent")
    if Path(str(payload["worktree_path"])).name != payload["run_id"]:
        raise WorktreeGCError("owner worktree path does not match its run ID")


def adopt_legacy_owner(
    repository: Path,
    run_id: str,
    *,
    expected_ledger_sha256: str,
    actor: str,
    evidence: str,
) -> dict[str, Any]:
    _strict_hash(expected_ledger_sha256, "expected ledger SHA-256", _HEX_64)
    actor = _strict_text(actor, "actor")
    evidence = _strict_text(evidence, "evidence")
    root = repository_root(repository)
    ledger_path = run_directory(root, run_id) / "ledger.json"
    store = AtomicLedger(ledger_path)
    with store.run_locked():
        if not ledger_path.is_file():
            raise WorktreeGCError(f"run ledger does not exist: {run_id}")
        observed_sha = _file_sha256(ledger_path)
        if observed_sha != expected_ledger_sha256:
            raise WorktreeGCError("run ledger SHA-256 differs from expected")
        ledger = store.load()
        payload = _owner_payload(
            root,
            ledger,
            origin={
                "kind": "legacy-adoption",
                "ledger_sha256": observed_sha,
                "actor": actor,
                "evidence": evidence,
            },
        )
        _validate_owner_binding(root, payload, ledger)
        inventory = _parse_worktree_inventory(root)
        _assert_registered_owner(payload, inventory)
        manifests, invalid = _manifest_inventory(common_git_dir(root))
        if invalid:
            raise WorktreeGCError("ownership inventory contains an invalid manifest")
        duplicate = [
            path
            for path, manifest in manifests
            if manifest["worktree_path"] == payload["worktree_path"]
            and manifest["run_id"] != run_id
        ]
        if duplicate:
            raise WorktreeGCError("worktree is already claimed by another owner manifest")
        path = owner_manifest_path(root, run_id)
        replayed = path.exists()
        document = _write_envelope(path, payload)
        return {
            "manifest": payload,
            "manifest_path": str(path),
            "manifest_sha256": _sha256_bytes(canonical_bytes(document) + b"\n"),
            "replayed": replayed,
            "authority": {
                "cleanup": False,
                "merge": False,
                "pi_sync": False,
                "provider": False,
                "publication": False,
                "reload": False,
            },
        }


def classify_operational_state(
    ledger: Mapping[str, Any],
    *,
    pi_sync_states: Iterable[Mapping[str, Any]] = (),
) -> list[str]:
    reasons: set[str] = set()
    if ledger.get("run_state") != "completed":
        reasons.add("run-not-completed")
    if ledger.get("cleanup") is not None:
        reasons.add("cleanup-already-recorded")
    gates = ledger.get("gates")
    if not isinstance(gates, dict):
        reasons.add("gates-invalid")
    elif any(
        not isinstance(gate, dict)
        or gate.get("state") not in {"passed", "consumed", "closed"}
        for gate in gates.values()
    ):
        reasons.add("gate-open")
    tickets = ledger.get("tickets")
    order = ledger.get("ticket_order")
    if not isinstance(tickets, dict) or not isinstance(order, list):
        reasons.add("tickets-invalid")
    else:
        for ticket_id in order:
            ticket = tickets.get(ticket_id)
            if not isinstance(ticket, dict) or ticket.get("state") != "integrated":
                reasons.add("ticket-not-integrated")
                continue
            delivery = ticket.get("delivery")
            terminal = delivery.get("terminal-integration") if isinstance(delivery, dict) else None
            lineage = ticket.get("delivery_lineage")
            if (
                not isinstance(terminal, dict)
                or not isinstance(lineage, dict)
                or terminal.get("head_sha") != lineage.get("head_sha")
                or not _HEX_40.fullmatch(str(terminal.get("terminal_sha", "")))
            ):
                reasons.add("integration-proof-invalid")
            wiki = delivery.get("wiki-sync") if isinstance(delivery, dict) else None
            if isinstance(wiki, dict):
                result = wiki.get("result")
                wiki_delivery = wiki.get("delivery")
                unchanged = (
                    isinstance(result, dict)
                    and result.get("status") == "unchanged"
                    and result.get("reason") == "no-diff"
                )
                merged = (
                    isinstance(wiki_delivery, dict)
                    and wiki_delivery.get("status") == "merged"
                )
                if not (unchanged or merged):
                    reasons.add("wiki-delivery-nonterminal")
    for state in pi_sync_states:
        if not isinstance(state, Mapping) or not isinstance(state.get("receipt"), dict):
            reasons.add("pi-sync-incomplete")
    return sorted(reasons)


def _read_integrity_payload(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return _validate_envelope(document, label=path.name)


def _pi_sync_states(run_dir: Path) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    root = run_dir / "pi-sync"
    if not root.exists():
        return states
    for path in sorted(root.glob("**/*.json"), key=lambda item: item.as_posix()):
        try:
            states.append(_read_integrity_payload(path))
        except (OSError, json.JSONDecodeError, WorktreeGCError):
            states.append({"receipt": None, "invalid": True})
    return states


def _worktree_dirty(worktree: Path) -> bool:
    return bool(
        run_git(
            worktree,
            "--no-optional-locks",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignored=matching",
        )
    )


def _interrupted_git_operation(worktree: Path) -> bool:
    markers = (
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "BISECT_LOG",
        "rebase-apply",
        "rebase-merge",
        "sequencer",
    )
    for marker in markers:
        raw = run_git(worktree, "rev-parse", "--git-path", marker)
        path = Path(raw)
        if not path.is_absolute():
            path = worktree / path
        if path.exists():
            return True
    return False


def _current_ledger_payload(path: Path) -> dict[str, Any] | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        return _validate_envelope(document, label="run ledger")
    except (OSError, json.JSONDecodeError, WorktreeGCError):
        return None


def _contains_path(value: object, expected: str) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_path(item, expected)
            for key, item in value.items()
            if key != "history"
        )
    if isinstance(value, list):
        return any(_contains_path(item, expected) for item in value)
    return value == expected


def _active_cross_references(common: Path, owner_run_id: str, worktree: str) -> list[str]:
    references: list[str] = []
    runs = common / "ticket-autopilot" / "runs"
    if not runs.exists():
        return references
    for path in sorted(runs.glob("*/ledger.json"), key=lambda item: item.as_posix()):
        payload = _current_ledger_payload(path)
        if not payload or payload.get("run_id") == owner_run_id:
            continue
        if payload.get("run_state") != "completed" and _contains_path(payload, worktree):
            references.append(str(payload.get("run_id", path.parent.name)))
    return references


def _retained_head_reasons(
    worktree: Path,
    entry: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    head = run_git(worktree, "rev-parse", "HEAD")
    if head != entry.get("HEAD"):
        reasons.append("head-inventory-drift")
    order = ledger.get("ticket_order")
    tickets = ledger.get("tickets")
    if not isinstance(order, list) or not order or not isinstance(tickets, dict):
        return [*reasons, "retained-head-unproven"]
    last = tickets.get(order[-1])
    if not isinstance(last, dict):
        return [*reasons, "retained-head-unproven"]
    pr = last.get("pr")
    expected_head = pr.get("head_sha") if isinstance(pr, dict) else None
    if head != expected_head:
        reasons.append("head-not-terminal-ticket")
    branch = entry.get("branch")
    expected_branch = pr.get("branch") if isinstance(pr, dict) else None
    if branch != f"refs/heads/{expected_branch}":
        reasons.append("branch-not-terminal-ticket")
    terminal = last.get("delivery", {}).get("terminal-integration")
    if not isinstance(terminal, dict) or terminal.get("head_sha") != head:
        reasons.append("retained-head-unproven")
    else:
        terminal_sha = str(terminal.get("terminal_sha", ""))
        result = subprocess_run_git_ancestor(worktree, head, terminal_sha)
        if not result:
            reasons.append("terminal-ancestry-unproven")
    return reasons


def subprocess_run_git_ancestor(repository: Path, ancestor: str, descendant: str) -> bool:
    """Return local ancestry only; never fetch or consult a provider."""

    if not _HEX_40.fullmatch(ancestor) or not _HEX_40.fullmatch(descendant):
        return False
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repository,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _protected_by(path: Path, protected: Iterable[Path]) -> bool:
    for candidate in protected:
        if path == candidate:
            return True
        try:
            candidate.relative_to(path)
        except ValueError:
            continue
        return True
    return False


def plan_worktree_gc(
    repository: Path,
    *,
    protected_paths: Iterable[Path] = (),
    invocation_path: Path | None = None,
) -> dict[str, Any]:
    root = repository_root(repository)
    binding = _repository_binding(root)
    common = Path(binding["git_common_dir"])
    inventory = _parse_worktree_inventory(root)
    manifests, invalid_manifests = _manifest_inventory(common)
    path_counts: dict[str, int] = {}
    for _path, manifest in manifests:
        worktree_path = str(manifest["worktree_path"])
        path_counts[worktree_path] = path_counts.get(worktree_path, 0) + 1

    protected: set[Path] = {root, Path(str(inventory[0]["worktree"]))}
    if invocation_path is not None:
        protected.add(invocation_path.resolve())
    for path in protected_paths:
        canonical = _canonical_absolute(str(path), "protected path")
        _assert_no_symlink_components(canonical)
        protected.add(canonical)
    protected_list = sorted(protected, key=lambda item: item.as_posix())
    by_path = {str(entry["worktree"]): entry for entry in inventory}
    entries: list[dict[str, Any]] = []

    for manifest_path, manifest in manifests:
        reasons: set[str] = set()
        run_id = str(manifest["run_id"])
        worktree = Path(str(manifest["worktree_path"]))
        ledger_path = manifest_path.parent / "ledger.json"
        observed: dict[str, Any] = {
            "manifest_sha256": _file_sha256(manifest_path),
            "ledger_sha256": None,
            "head_sha": None,
            "branch": None,
            "clean": None,
        }
        if path_counts[str(worktree)] != 1:
            reasons.add("duplicate-owner-claim")
        if manifest_path.parent.name != run_id:
            reasons.add("manifest-run-directory-mismatch")
        if _protected_by(worktree, protected_list):
            reasons.add("protected-path")
        if worktree.exists():
            try:
                _assert_no_symlink_components(worktree)
            except WorktreeGCError:
                reasons.add("symlink-or-path-alias")
        else:
            reasons.add("worktree-missing")
        entry = by_path.get(str(worktree))
        if entry is None:
            reasons.add("git-registration-missing")
        else:
            if entry.get("locked"):
                reasons.add("git-worktree-locked")
            if entry.get("prunable"):
                reasons.add("git-worktree-prunable")
            observed["head_sha"] = entry.get("HEAD")
            observed["branch"] = entry.get("branch")
        store = AtomicLedger(ledger_path)
        ledger: dict[str, Any] | None = None
        try:
            with store.run_locked():
                observed["ledger_sha256"] = _file_sha256(ledger_path)
                ledger = store.load()
                _validate_owner_binding(root, manifest, ledger)
                reasons.update(
                    classify_operational_state(
                        ledger,
                        pi_sync_states=_pi_sync_states(manifest_path.parent),
                    )
                )
                if entry is not None and worktree.exists():
                    try:
                        _assert_registered_owner(manifest, inventory)
                    except WorktreeGCError:
                        reasons.add("owner-git-mismatch")
                    try:
                        dirty = _worktree_dirty(worktree)
                        observed["clean"] = not dirty
                        if dirty:
                            reasons.add("worktree-dirty")
                        if _interrupted_git_operation(worktree):
                            reasons.add("git-operation-interrupted")
                        reasons.update(_retained_head_reasons(worktree, entry, ledger))
                    except (OSError, ValueError):
                        reasons.add("git-state-unreadable")
                references = _active_cross_references(common, run_id, str(worktree))
                if references:
                    reasons.add("active-cross-reference")
                    observed["referenced_by"] = references
                if observed["ledger_sha256"] != _file_sha256(ledger_path):
                    reasons.add("ledger-drift")
        except (GitError, LedgerError, OSError, WorktreeGCError, ValueError):
            reasons.add("run-lock-or-ledger-invalid")
        entries.append(
            {
                "run_id": run_id,
                "worktree_path": str(worktree),
                "manifest_path": str(manifest_path),
                "disposition": "eligible" if not reasons else "protected",
                "reasons": sorted(reasons),
                "observed": observed,
            }
        )

    entries.sort(key=lambda item: (str(item["run_id"]), str(item["worktree_path"])))
    owned_paths = {str(manifest["worktree_path"]) for _path, manifest in manifests}
    unmanaged = sorted(
        str(entry["worktree"])
        for entry in inventory
        if str(entry["worktree"]) not in owned_paths
    )
    inventory_projection = [
        {key: entry[key] for key in sorted(entry)} for entry in inventory
    ]
    payload = {
        "schema": 1,
        "contract_version": PLAN_CONTRACT,
        "repository": binding,
        "inventory_sha256": _sha256_bytes(canonical_bytes(inventory_projection)),
        "protected_paths": [str(path) for path in protected_list],
        "entries": entries,
        "invalid_manifests": invalid_manifests,
        "unmanaged_worktrees": unmanaged,
        "authority": {
            "cleanup": False,
            "merge": False,
            "pi_sync": False,
            "provider": False,
            "publication": False,
            "reload": False,
        },
    }
    document = _envelope(payload)
    plan_sha = _sha256_bytes(canonical_bytes(document) + b"\n")
    plan_path = common / "ticket-autopilot" / "worktree-gc" / "plans" / f"{plan_sha}.json"
    _write_envelope(plan_path, payload)
    return {
        **payload,
        "plan_sha256": plan_sha,
        "plan_path": str(plan_path),
    }
