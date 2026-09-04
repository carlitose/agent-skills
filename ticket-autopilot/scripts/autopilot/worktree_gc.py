"""Manifest-owned, provider-free planning for Ticket Autopilot worktree cleanup."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlparse

from .git_ops import (
    GitError,
    common_git_dir,
    origin_url,
    remove_isolated_worktree,
    repository_root,
    run_directory,
    run_git,
)
from .kernel import Kernel
from .ledger import AtomicLedger, LedgerError
from .providers import ProviderError
from .repository_authority import RepositoryBinding, canonical_bytes


OWNER_CONTRACT = "worktree-owner-v1"
PLAN_CONTRACT = "worktree-gc-plan-v1"
OWNER_FILENAME = "worktree-owner.json"
APPLY_CONTRACT = "worktree-gc-apply-v1"
ENTRY_RECEIPT_CONTRACT = "worktree-gc-entry-applied-v1"
COMPLETION_RECEIPT_CONTRACT = "worktree-gc-completion-v1"
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
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_components(path.parent)
    if path.is_symlink():
        raise WorktreeGCError(f"record path is a symlink: {path}")
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
        if invalid_manifests:
            reasons.add("ownership-inventory-invalid")
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


_PLAN_FIELDS = {
    "schema",
    "contract_version",
    "repository",
    "inventory_sha256",
    "protected_paths",
    "entries",
    "invalid_manifests",
    "unmanaged_worktrees",
    "authority",
}
_PLAN_ENTRY_FIELDS = {
    "run_id",
    "worktree_path",
    "manifest_path",
    "disposition",
    "reasons",
    "observed",
}
_OBSERVED_FIELDS = {
    "manifest_sha256",
    "ledger_sha256",
    "head_sha",
    "branch",
    "clean",
}
_AUTHORITY_FIELDS = {
    "cleanup",
    "merge",
    "pi_sync",
    "provider",
    "publication",
    "reload",
}
_INTENT_FIELDS = {
    "schema",
    "contract_version",
    "plan_sha256",
    "plan_path",
    "repository",
    "actor",
    "evidence",
    "inventory",
    "entries",
    "authority",
}
_INTENT_ENTRY_FIELDS = {
    "ordinal",
    "run_id",
    "repository_root",
    "worktree_path",
    "manifest_path",
    "manifest_sha256",
    "ledger_sha256",
    "head_sha",
    "branch",
}
_ENTRY_RECEIPT_FIELDS = {
    "schema",
    "contract_version",
    "plan_sha256",
    "intent_sha256",
    "ordinal",
    "run_id",
    "repository_root",
    "worktree_path",
    "manifest_sha256",
    "ledger_sha256_before",
    "ledger_sha256_after",
    "head_sha",
    "branch",
    "filesystem_absent",
    "registration_absent",
    "cleanup",
    "authority",
}
_COMPLETION_FIELDS = {
    "schema",
    "contract_version",
    "plan_sha256",
    "intent_sha256",
    "entry_receipts",
    "complete",
    "authority",
}
_INVENTORY_FIELDS = {
    "worktree",
    "HEAD",
    "branch",
    "bare",
    "detached",
    "locked",
    "locked_reason",
    "prunable",
    "prunable_reason",
}
FaultHook = Callable[[str, Mapping[str, Any]], None]


def _validate_no_authority(value: object, label: str) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != _AUTHORITY_FIELDS:
        raise WorktreeGCError(f"{label} authority fields are invalid")
    if any(item is not False for item in value.values()):
        raise WorktreeGCError(f"{label} cannot grant authority")
    return dict(value)


def _validate_string_list(value: object, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or value != sorted(set(value))
    ):
        raise WorktreeGCError(f"{label} must be sorted unique strings")
    return list(value)


def _validate_plan_structure(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _PLAN_FIELDS:
        raise WorktreeGCError("cleanup plan fields are invalid")
    if payload.get("schema") != 1 or payload.get("contract_version") != PLAN_CONTRACT:
        raise WorktreeGCError("cleanup plan contract is invalid")
    repository = payload.get("repository")
    if not isinstance(repository, dict) or set(repository) != {
        "git_common_dir",
        "provider",
        "normalized_remote",
    }:
        raise WorktreeGCError("cleanup plan repository fields are invalid")
    _strict_hash(payload.get("inventory_sha256"), "cleanup plan inventory", _HEX_64)
    _validate_no_authority(payload.get("authority"), "cleanup plan")
    protected = payload.get("protected_paths")
    unmanaged = payload.get("unmanaged_worktrees")
    if not isinstance(protected, list) or not isinstance(unmanaged, list):
        raise WorktreeGCError("cleanup plan path lists are invalid")
    invalid = payload.get("invalid_manifests")
    if not isinstance(invalid, list) or any(
        not isinstance(item, dict)
        or set(item) != {"manifest_path", "reason"}
        or not all(isinstance(value, str) and value for value in item.values())
        for item in invalid
    ):
        raise WorktreeGCError("cleanup plan invalid-manifest records are invalid")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise WorktreeGCError("cleanup plan entries are invalid")
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != _PLAN_ENTRY_FIELDS:
            raise WorktreeGCError("cleanup plan entry fields are invalid")
        observed = entry.get("observed")
        if not isinstance(observed, dict) or frozenset(observed) not in {
            frozenset(_OBSERVED_FIELDS),
            frozenset({*_OBSERVED_FIELDS, "referenced_by"}),
        }:
            raise WorktreeGCError("cleanup plan observed fields are invalid")
        if "referenced_by" in observed:
            _validate_string_list(observed["referenced_by"], "cleanup plan references")
        if entry.get("disposition") not in {"eligible", "protected"}:
            raise WorktreeGCError("cleanup plan disposition is invalid")
        _validate_string_list(entry.get("reasons"), "cleanup plan reasons")
    return dict(payload)


def validate_gc_plan(payload: object) -> dict[str, Any]:
    normalized = _validate_plan_structure(payload)
    repository = dict(normalized["repository"])
    repository["git_common_dir"] = str(
        _canonical_absolute(repository["git_common_dir"], "cleanup plan Git common directory")
    )
    repository["provider"] = _strict_text(repository["provider"], "cleanup plan provider")
    repository["normalized_remote"] = _strict_text(
        repository["normalized_remote"], "cleanup plan normalized remote"
    )
    normalized["repository"] = repository
    normalized["protected_paths"] = [
        str(_canonical_absolute(path, "cleanup plan protected path"))
        for path in normalized["protected_paths"]
    ]
    if normalized["protected_paths"] != sorted(set(normalized["protected_paths"])):
        raise WorktreeGCError("cleanup plan protected paths are not sorted and unique")
    normalized["unmanaged_worktrees"] = [
        str(_canonical_absolute(path, "cleanup plan unmanaged path"))
        for path in normalized["unmanaged_worktrees"]
    ]
    if normalized["unmanaged_worktrees"] != sorted(set(normalized["unmanaged_worktrees"])):
        raise WorktreeGCError("cleanup plan unmanaged paths are not sorted and unique")
    normalized_invalid: list[dict[str, str]] = []
    for item in normalized["invalid_manifests"]:
        normalized_invalid.append(
            {
                "manifest_path": str(
                    _canonical_absolute(item["manifest_path"], "invalid manifest path")
                ),
                "reason": _strict_text(item["reason"], "invalid manifest reason"),
            }
        )
    if normalized_invalid != sorted(
        normalized_invalid, key=lambda item: (item["manifest_path"], item["reason"])
    ):
        raise WorktreeGCError("cleanup plan invalid manifests are not sorted")
    normalized["invalid_manifests"] = normalized_invalid
    normalized_entries: list[dict[str, Any]] = []
    for entry in normalized["entries"]:
        item = dict(entry)
        item["run_id"] = _strict_text(item["run_id"], "cleanup plan run ID")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", item["run_id"]):
            raise WorktreeGCError("cleanup plan run ID is invalid")
        item["worktree_path"] = str(
            _canonical_absolute(item["worktree_path"], "cleanup plan worktree")
        )
        item["manifest_path"] = str(
            _canonical_absolute(item["manifest_path"], "cleanup plan manifest")
        )
        observed = dict(item["observed"])
        observed["manifest_sha256"] = _strict_hash(
            observed.get("manifest_sha256"), "observed manifest SHA-256", _HEX_64
        )
        for field in ("ledger_sha256", "head_sha"):
            value = observed.get(field)
            if value is not None:
                observed[field] = _strict_hash(
                    value,
                    f"observed {field}",
                    _HEX_64 if field == "ledger_sha256" else _HEX_40,
                )
        if observed.get("branch") is not None:
            observed["branch"] = _strict_text(observed["branch"], "observed branch")
        if observed.get("clean") is not None and type(observed["clean"]) is not bool:
            raise WorktreeGCError("observed cleanliness is invalid")
        item["observed"] = observed
        if item["disposition"] == "eligible":
            if item["reasons"] or any(
                observed.get(field) is None
                for field in ("ledger_sha256", "head_sha", "branch", "clean")
            ) or observed["clean"] is not True or "referenced_by" in observed:
                raise WorktreeGCError("eligible cleanup plan entry is incomplete")
        elif not item["reasons"]:
            raise WorktreeGCError("protected cleanup plan entry lacks a reason")
        normalized_entries.append(item)
    if normalized_entries != sorted(
        normalized_entries,
        key=lambda item: (item["run_id"], item["worktree_path"]),
    ):
        raise WorktreeGCError("cleanup plan entries are not sorted")
    if len({item["run_id"] for item in normalized_entries}) != len(normalized_entries):
        raise WorktreeGCError("cleanup plan contains duplicate run IDs")
    normalized["entries"] = normalized_entries
    return normalized


def load_gc_plan(
    repository: Path,
    plan_path: Path,
    *,
    expected_plan_sha256: str,
) -> dict[str, Any]:
    expected_sha = _strict_hash(expected_plan_sha256, "expected plan SHA-256", _HEX_64)
    root = repository_root(repository)
    common = common_git_dir(root)
    canonical_path = _canonical_absolute(str(plan_path), "cleanup plan path")
    expected_path = common / "ticket-autopilot" / "worktree-gc" / "plans" / f"{expected_sha}.json"
    if canonical_path != expected_path:
        raise WorktreeGCError("cleanup plan path is not the expected content address")
    _assert_no_symlink_components(canonical_path)
    if _file_sha256(canonical_path) != expected_sha:
        raise WorktreeGCError("cleanup plan SHA-256 differs from expected")
    try:
        document = json.loads(canonical_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorktreeGCError("cleanup plan is unreadable") from error
    payload = validate_gc_plan(_validate_envelope(document, label="cleanup plan"))
    if canonical_bytes(_envelope(payload)) + b"\n" != canonical_path.read_bytes():
        raise WorktreeGCError("cleanup plan bytes are noncanonical")
    binding = _repository_binding(root)
    if payload["repository"] != binding:
        raise WorktreeGCError("cleanup plan repository binding differs")
    for entry in payload["entries"]:
        expected_manifest = (
            common
            / "ticket-autopilot"
            / "runs"
            / entry["run_id"]
            / OWNER_FILENAME
        )
        if Path(entry["manifest_path"]) != expected_manifest:
            raise WorktreeGCError("cleanup plan manifest path differs from run ID")
        if Path(entry["worktree_path"]).name != entry["run_id"]:
            raise WorktreeGCError("cleanup plan worktree path differs from run ID")
    return payload


def _inventory_projection(repository: Path) -> list[dict[str, Any]]:
    return [
        {key: entry[key] for key in sorted(entry)}
        for entry in _parse_worktree_inventory(repository)
    ]


def _validate_inventory(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise WorktreeGCError("cleanup intent inventory is invalid")
    normalized: list[dict[str, Any]] = []
    for entry in value:
        if (
            not isinstance(entry, dict)
            or not set(entry).issubset(_INVENTORY_FIELDS)
            or not {"worktree", "HEAD"}.issubset(entry)
        ):
            raise WorktreeGCError("cleanup intent inventory entry is invalid")
        item = dict(entry)
        item["worktree"] = str(
            _canonical_absolute(item["worktree"], "cleanup intent inventory worktree")
        )
        item["HEAD"] = _strict_hash(item["HEAD"], "cleanup intent inventory HEAD", _HEX_40)
        if "branch" in item:
            item["branch"] = _strict_text(item["branch"], "cleanup intent inventory branch")
        for field in ("bare", "detached", "locked", "prunable"):
            if field in item and type(item[field]) is not bool:
                raise WorktreeGCError("cleanup intent inventory flag is invalid")
        for field in ("locked_reason", "prunable_reason"):
            if field in item:
                item[field] = _strict_text(item[field], "cleanup intent inventory reason")
        normalized.append(item)
    if len({item["worktree"] for item in normalized}) != len(normalized):
        raise WorktreeGCError("cleanup intent inventory contains duplicate worktrees")
    return normalized


def _intent_entry(plan_entry: Mapping[str, Any], ordinal: int) -> dict[str, Any]:
    observed = plan_entry["observed"]
    return {
        "ordinal": ordinal,
        "run_id": plan_entry["run_id"],
        "repository_root": load_owner_manifest(
            Path(plan_entry["manifest_path"])
        )["repository_root"],
        "worktree_path": plan_entry["worktree_path"],
        "manifest_path": plan_entry["manifest_path"],
        "manifest_sha256": observed["manifest_sha256"],
        "ledger_sha256": observed["ledger_sha256"],
        "head_sha": observed["head_sha"],
        "branch": observed["branch"],
    }


def _intent_payload(
    plan: Mapping[str, Any],
    *,
    plan_path: Path,
    plan_sha256: str,
    actor: str,
    evidence: str,
    inventory: list[dict[str, Any]],
) -> dict[str, Any]:
    eligible = [entry for entry in plan["entries"] if entry["disposition"] == "eligible"]
    return {
        "schema": 1,
        "contract_version": APPLY_CONTRACT,
        "plan_sha256": plan_sha256,
        "plan_path": str(plan_path),
        "repository": dict(plan["repository"]),
        "actor": actor,
        "evidence": evidence,
        "inventory": inventory,
        "entries": [_intent_entry(entry, ordinal) for ordinal, entry in enumerate(eligible)],
        "authority": {field: False for field in sorted(_AUTHORITY_FIELDS)},
    }


def _validate_intent_structure(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _INTENT_FIELDS:
        raise WorktreeGCError("cleanup intent fields are invalid")
    if payload.get("schema") != 1 or payload.get("contract_version") != APPLY_CONTRACT:
        raise WorktreeGCError("cleanup intent contract is invalid")
    repository = payload.get("repository")
    if not isinstance(repository, dict) or set(repository) != {
        "git_common_dir",
        "provider",
        "normalized_remote",
    }:
        raise WorktreeGCError("cleanup intent repository fields are invalid")
    inventory = payload.get("inventory")
    if not isinstance(inventory, list) or any(
        not isinstance(entry, dict)
        or not set(entry).issubset(_INVENTORY_FIELDS)
        or not {"worktree", "HEAD"}.issubset(entry)
        for entry in inventory
    ):
        raise WorktreeGCError("cleanup intent inventory entry is invalid")
    entries = payload.get("entries")
    if not isinstance(entries, list) or any(
        not isinstance(entry, dict) or set(entry) != _INTENT_ENTRY_FIELDS
        for entry in entries
    ):
        raise WorktreeGCError("cleanup intent entry fields are invalid")
    _validate_no_authority(payload.get("authority"), "cleanup intent")
    return dict(payload)


def validate_gc_intent(payload: object) -> dict[str, Any]:
    normalized = _validate_intent_structure(payload)
    normalized["plan_sha256"] = _strict_hash(
        payload.get("plan_sha256"), "cleanup intent plan SHA-256", _HEX_64
    )
    normalized["plan_path"] = str(
        _canonical_absolute(payload.get("plan_path"), "cleanup intent plan path")
    )
    normalized["actor"] = _strict_text(payload.get("actor"), "cleanup intent actor")
    normalized["evidence"] = _strict_text(payload.get("evidence"), "cleanup intent evidence")
    repository = payload["repository"]
    normalized["repository"] = {
        "git_common_dir": str(
            _canonical_absolute(repository["git_common_dir"], "cleanup intent Git common directory")
        ),
        "provider": _strict_text(repository["provider"], "cleanup intent provider"),
        "normalized_remote": _strict_text(
            repository["normalized_remote"], "cleanup intent normalized remote"
        ),
    }
    normalized["inventory"] = _validate_inventory(payload.get("inventory"))
    entries = payload["entries"]
    normalized_entries: list[dict[str, Any]] = []
    for ordinal, entry in enumerate(entries):
        item = dict(entry)
        if item.get("ordinal") != ordinal:
            raise WorktreeGCError("cleanup intent entry order is invalid")
        item["run_id"] = _strict_text(item.get("run_id"), "cleanup intent run ID")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", item["run_id"]):
            raise WorktreeGCError("cleanup intent run ID is invalid")
        item["repository_root"] = str(
            _canonical_absolute(
                item.get("repository_root"), "cleanup intent repository root"
            )
        )
        item["worktree_path"] = str(
            _canonical_absolute(item.get("worktree_path"), "cleanup intent worktree")
        )
        item["manifest_path"] = str(
            _canonical_absolute(item.get("manifest_path"), "cleanup intent manifest")
        )
        item["manifest_sha256"] = _strict_hash(
            item.get("manifest_sha256"), "cleanup intent manifest SHA-256", _HEX_64
        )
        item["ledger_sha256"] = _strict_hash(
            item.get("ledger_sha256"), "cleanup intent ledger SHA-256", _HEX_64
        )
        item["head_sha"] = _strict_hash(
            item.get("head_sha"), "cleanup intent HEAD", _HEX_40
        )
        item["branch"] = _strict_text(item.get("branch"), "cleanup intent branch")
        normalized_entries.append(item)
    if len({item["run_id"] for item in normalized_entries}) != len(normalized_entries):
        raise WorktreeGCError("cleanup intent contains duplicate run IDs")
    normalized["entries"] = normalized_entries
    normalized["authority"] = _validate_no_authority(
        payload.get("authority"), "cleanup intent"
    )
    return normalized


def _receipt_path(application_dir: Path, entry: Mapping[str, Any]) -> Path:
    return application_dir / "entries" / f"{entry['ordinal']:04d}-{entry['run_id']}.json"


def _cleanup_record(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "recorded": True,
        "worktree": entry["worktree_path"],
        "worktree_removed": True,
        "resume_abandoned": False,
        "remote_state_deleted": False,
    }


def _ledger_cleanup_status(
    ledger_path: Path,
    ledger: Mapping[str, Any],
    entry: Mapping[str, Any],
) -> str:
    observed_sha = _file_sha256(ledger_path)
    if observed_sha == entry["ledger_sha256"]:
        if ledger.get("cleanup") is not None:
            raise WorktreeGCError("pre-removal ledger unexpectedly records cleanup")
        return "pending"
    if ledger.get("cleanup") != _cleanup_record(entry):
        raise WorktreeGCError("post-removal ledger cleanup record is contradictory")
    history = ledger.get("history")
    if (
        not isinstance(history, list)
        or not history
        or not isinstance(history[-1], dict)
        or history[-1].get("event") != "worktree-cleaned"
        or history[-1].get("ticket_id") is not None
        or history[-1].get("details")
        != {"worktree": entry["worktree_path"], "resume_abandoned": False}
    ):
        raise WorktreeGCError("post-removal ledger cleanup event is contradictory")
    predecessor = dict(ledger)
    predecessor["cleanup"] = None
    predecessor["history"] = list(history[:-1])
    predecessor_sha = _sha256_bytes(canonical_bytes(_envelope(predecessor)) + b"\n")
    if predecessor_sha != entry["ledger_sha256"]:
        raise WorktreeGCError("post-removal ledger differs beyond cleanup recording")
    return "recorded"


def _validate_entry_receipt(
    payload: object,
    *,
    entry: Mapping[str, Any],
    plan_sha256: str,
    intent_sha256: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _ENTRY_RECEIPT_FIELDS:
        raise WorktreeGCError("cleanup entry receipt fields are invalid")
    normalized = dict(payload)
    expected = {
        "schema": 1,
        "contract_version": ENTRY_RECEIPT_CONTRACT,
        "plan_sha256": plan_sha256,
        "intent_sha256": intent_sha256,
        "ordinal": entry["ordinal"],
        "run_id": entry["run_id"],
        "repository_root": entry["repository_root"],
        "worktree_path": entry["worktree_path"],
        "manifest_sha256": entry["manifest_sha256"],
        "ledger_sha256_before": entry["ledger_sha256"],
        "head_sha": entry["head_sha"],
        "branch": entry["branch"],
        "filesystem_absent": True,
        "registration_absent": True,
        "cleanup": _cleanup_record(entry),
        "authority": {field: False for field in sorted(_AUTHORITY_FIELDS)},
    }
    for key, value in expected.items():
        if normalized.get(key) != value:
            raise WorktreeGCError(f"cleanup entry receipt {key} is contradictory")
    normalized["ledger_sha256_after"] = _strict_hash(
        payload.get("ledger_sha256_after"), "cleanup receipt ledger SHA-256", _HEX_64
    )
    return normalized


def _validate_completion_receipt(
    payload: object,
    *,
    plan_sha256: str,
    intent_sha256: str,
    expected_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _COMPLETION_FIELDS:
        raise WorktreeGCError("cleanup completion receipt fields are invalid")
    expected = {
        "schema": 1,
        "contract_version": COMPLETION_RECEIPT_CONTRACT,
        "plan_sha256": plan_sha256,
        "intent_sha256": intent_sha256,
        "entry_receipts": expected_receipts,
        "complete": True,
        "authority": {field: False for field in sorted(_AUTHORITY_FIELDS)},
    }
    if payload != expected:
        raise WorktreeGCError("cleanup completion receipt is contradictory")
    return dict(payload)


def _load_record(path: Path, *, label: str) -> dict[str, Any]:
    _assert_no_symlink_components(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorktreeGCError(f"{label} is unreadable") from error
    payload = _validate_envelope(document, label=label)
    if canonical_bytes(_envelope(payload)) + b"\n" != path.read_bytes():
        raise WorktreeGCError(f"{label} bytes are noncanonical")
    return payload


def _invoke_fault(
    fault_hook: FaultHook | None,
    phase: str,
    context: Mapping[str, Any],
) -> None:
    if fault_hook is not None:
        fault_hook(phase, context)


def _recomputed_plan_payload(root: Path, plan: Mapping[str, Any]) -> dict[str, Any]:
    current = plan_worktree_gc(
        root,
        protected_paths=[Path(path) for path in plan["protected_paths"]],
    )
    return {field: current[field] for field in _PLAN_FIELDS}


def _preflight_present_entry(
    root: Path,
    common: Path,
    entry: Mapping[str, Any],
    inventory: list[dict[str, Any]],
    ledger: Mapping[str, Any],
    *,
    invocation_path: Path,
) -> None:
    worktree = Path(entry["worktree_path"])
    manifest_path = Path(entry["manifest_path"])
    owner_root = Path(entry["repository_root"])
    if common_git_dir(owner_root) != common:
        raise WorktreeGCError("cleanup entry owner uses another Git common directory")
    if _protected_by(worktree, [owner_root, invocation_path]):
        raise WorktreeGCError("cleanup entry became an invocation or primary path")
    _assert_no_symlink_components(worktree)
    if _file_sha256(manifest_path) != entry["manifest_sha256"]:
        raise WorktreeGCError("cleanup entry manifest changed")
    manifest = load_owner_manifest(manifest_path)
    if (
        manifest["run_id"] != entry["run_id"]
        or manifest["repository_root"] != entry["repository_root"]
        or manifest["worktree_path"] != entry["worktree_path"]
    ):
        raise WorktreeGCError("cleanup entry differs from its owner manifest")
    _validate_owner_binding(owner_root, manifest, ledger)
    registered = _assert_registered_owner(manifest, inventory)
    if registered.get("HEAD") != entry["head_sha"] or registered.get("branch") != entry["branch"]:
        raise WorktreeGCError("cleanup entry HEAD or branch changed")
    if _file_sha256(manifest_path.parent / "ledger.json") != entry["ledger_sha256"]:
        raise WorktreeGCError("cleanup entry ledger changed")
    if _worktree_dirty(worktree):
        raise WorktreeGCError("cleanup entry became dirty")
    if _interrupted_git_operation(worktree):
        raise WorktreeGCError("cleanup entry has an interrupted Git operation")
    if classify_operational_state(
        ledger, pi_sync_states=_pi_sync_states(manifest_path.parent)
    ):
        raise WorktreeGCError("cleanup entry is no longer operationally terminal")
    if _retained_head_reasons(worktree, registered, ledger):
        raise WorktreeGCError("cleanup entry retained-head proof changed")
    if _active_cross_references(common, entry["run_id"], entry["worktree_path"]):
        raise WorktreeGCError("cleanup entry gained an active cross-reference")


def _expected_inventory_after_absence(
    original: list[dict[str, Any]], absent_paths: set[str]
) -> list[dict[str, Any]]:
    return [entry for entry in original if entry["worktree"] not in absent_paths]


def _preflight_application_state(
    root: Path,
    intent: Mapping[str, Any],
    stores: Mapping[str, AtomicLedger],
    *,
    application_dir: Path,
    plan_sha256: str,
    intent_sha256: str,
    invocation_path: Path,
) -> list[dict[str, Any]]:
    common = common_git_dir(root)
    inventory = _inventory_projection(root)
    by_path = {entry["worktree"]: entry for entry in inventory}
    absent_paths: set[str] = set()
    states: list[dict[str, Any]] = []
    for entry in intent["entries"]:
        worktree = Path(entry["worktree_path"])
        filesystem_absent = not worktree.exists()
        registration_absent = entry["worktree_path"] not in by_path
        if filesystem_absent != registration_absent:
            raise WorktreeGCError("cleanup entry absence readback is contradictory")
        if filesystem_absent:
            absent_paths.add(entry["worktree_path"])
    expected_inventory = _expected_inventory_after_absence(
        intent["inventory"], absent_paths
    )
    if canonical_bytes(inventory) != canonical_bytes(expected_inventory):
        raise WorktreeGCError("cleanup inventory changed after intent")

    for entry in intent["entries"]:
        manifest_path = Path(entry["manifest_path"])
        if _file_sha256(manifest_path) != entry["manifest_sha256"]:
            raise WorktreeGCError("cleanup entry manifest changed after intent")
        if _active_cross_references(common, entry["run_id"], entry["worktree_path"]):
            raise WorktreeGCError("cleanup entry gained an active cross-reference")
        store = stores[entry["run_id"]]
        ledger = store.load()
        receipt_path = _receipt_path(application_dir, entry)
        if entry["worktree_path"] in absent_paths:
            cleanup_status = _ledger_cleanup_status(
                manifest_path.parent / "ledger.json", ledger, entry
            )
            receipt = None
            if receipt_path.exists():
                receipt = _validate_entry_receipt(
                    _load_record(receipt_path, label="cleanup entry receipt"),
                    entry=entry,
                    plan_sha256=plan_sha256,
                    intent_sha256=intent_sha256,
                )
                if receipt["ledger_sha256_after"] != _file_sha256(store.path):
                    raise WorktreeGCError("cleanup entry receipt ledger readback changed")
                if cleanup_status != "recorded":
                    raise WorktreeGCError("cleanup receipt precedes ledger cleanup")
            states.append(
                {
                    "entry": entry,
                    "state": "applied" if receipt is not None else "interrupted",
                    "cleanup_status": cleanup_status,
                    "receipt": receipt,
                    "receipt_path": receipt_path,
                }
            )
        else:
            if receipt_path.exists():
                raise WorktreeGCError("cleanup receipt exists before worktree removal")
            _preflight_present_entry(
                root,
                common,
                entry,
                inventory,
                ledger,
                invocation_path=invocation_path,
            )
            states.append(
                {
                    "entry": entry,
                    "state": "pending",
                    "cleanup_status": "pending",
                    "receipt": None,
                    "receipt_path": receipt_path,
                }
            )
    return states


def _record_cleanup(
    store: AtomicLedger,
    entry: Mapping[str, Any],
) -> str:
    ledger = store.load()
    status = _ledger_cleanup_status(store.path, ledger, entry)
    if status == "pending":
        kernel = Kernel(ledger)
        for ticket_id in kernel.ledger["ticket_order"]:
            kernel.preflight_mutation_boundary(ticket_id, "worktree:cleanup")
        kernel.record_cleanup(
            worktree=entry["worktree_path"],
            worktree_removed=True,
            resume_abandoned=False,
        )
        store.save(kernel.ledger)
    return _file_sha256(store.path)


def _entry_receipt_payload(
    entry: Mapping[str, Any],
    *,
    plan_sha256: str,
    intent_sha256: str,
    ledger_sha256_after: str,
) -> dict[str, Any]:
    return {
        "schema": 1,
        "contract_version": ENTRY_RECEIPT_CONTRACT,
        "plan_sha256": plan_sha256,
        "intent_sha256": intent_sha256,
        "ordinal": entry["ordinal"],
        "run_id": entry["run_id"],
        "repository_root": entry["repository_root"],
        "worktree_path": entry["worktree_path"],
        "manifest_sha256": entry["manifest_sha256"],
        "ledger_sha256_before": entry["ledger_sha256"],
        "ledger_sha256_after": ledger_sha256_after,
        "head_sha": entry["head_sha"],
        "branch": entry["branch"],
        "filesystem_absent": True,
        "registration_absent": True,
        "cleanup": _cleanup_record(entry),
        "authority": {field: False for field in sorted(_AUTHORITY_FIELDS)},
    }


def apply_worktree_gc(
    repository: Path,
    plan_path: Path,
    *,
    expected_plan_sha256: str,
    actor: str,
    evidence: str,
    invocation_path: Path | None = None,
    fault_hook: FaultHook | None = None,
) -> dict[str, Any]:
    """Apply one exact plan with intent-first, provider-free replay."""

    actor = _strict_text(actor, "cleanup actor")
    evidence = _strict_text(evidence, "cleanup evidence")
    root = repository_root(repository)
    invocation = (invocation_path or Path.cwd()).resolve()
    plan = load_gc_plan(
        root, plan_path, expected_plan_sha256=expected_plan_sha256
    )
    plan_sha = _strict_hash(expected_plan_sha256, "expected plan SHA-256", _HEX_64)
    canonical_plan_path = Path(plan_path).resolve()
    common = common_git_dir(root)
    application_dir = (
        common / "ticket-autopilot" / "worktree-gc" / "applications" / plan_sha
    )
    intent_path = application_dir / "intent.json"
    completion_path = application_dir / "completion.json"
    repository_lock = AtomicLedger(
        common / "ticket-autopilot" / "worktree-gc" / "repository-gc.json"
    )

    with repository_lock.run_locked():
        intent_replayed = intent_path.exists()
        removed_this_invocation: list[str] = []
        if intent_replayed:
            intent = validate_gc_intent(
                _load_record(intent_path, label="cleanup intent")
            )
            if (
                _sha256_bytes(canonical_bytes(intent["inventory"]))
                != plan["inventory_sha256"]
            ):
                raise WorktreeGCError("cleanup intent inventory differs from the exact plan")
            expected_intent = _intent_payload(
                plan,
                plan_path=canonical_plan_path,
                plan_sha256=plan_sha,
                actor=actor,
                evidence=evidence,
                inventory=intent["inventory"],
            )
            if intent != expected_intent:
                raise WorktreeGCError("cleanup intent differs from this invocation")
        else:
            current = _recomputed_plan_payload(root, plan)
            if canonical_bytes(current) != canonical_bytes(plan):
                raise WorktreeGCError("cleanup plan is stale; no worktree was removed")
            inventory = _inventory_projection(root)
            if _sha256_bytes(canonical_bytes(inventory)) != plan["inventory_sha256"]:
                raise WorktreeGCError("cleanup inventory differs before intent")
            intent = _intent_payload(
                plan,
                plan_path=canonical_plan_path,
                plan_sha256=plan_sha,
                actor=actor,
                evidence=evidence,
                inventory=inventory,
            )

        stores = {
            entry["run_id"]: AtomicLedger(Path(entry["manifest_path"]).parent / "ledger.json")
            for entry in intent["entries"]
        }
        with ExitStack() as locks:
            for run_id in sorted(stores):
                locks.enter_context(stores[run_id].run_locked())
            if not intent_path.exists():
                provisional_sha = _sha256_bytes(
                    canonical_bytes(_envelope(intent)) + b"\n"
                )
                _preflight_application_state(
                    root,
                    intent,
                    stores,
                    application_dir=application_dir,
                    plan_sha256=plan_sha,
                    intent_sha256=provisional_sha,
                    invocation_path=invocation,
                )
                _write_envelope(intent_path, intent)
                _invoke_fault(fault_hook, "after-intent", {"intent_path": str(intent_path)})
            intent_sha = _file_sha256(intent_path)
            if intent_sha != _sha256_bytes(canonical_bytes(_envelope(intent)) + b"\n"):
                raise WorktreeGCError("cleanup intent content address changed")

            while True:
                states = _preflight_application_state(
                    root,
                    intent,
                    stores,
                    application_dir=application_dir,
                    plan_sha256=plan_sha,
                    intent_sha256=intent_sha,
                    invocation_path=invocation,
                )
                remaining = [state for state in states if state["state"] != "applied"]
                if not remaining:
                    break
                state = remaining[0]
                entry = state["entry"]
                worktree = Path(entry["worktree_path"])
                if state["state"] == "pending":
                    remove_isolated_worktree(
                        Path(entry["repository_root"]), worktree
                    )
                    removed_this_invocation.append(entry["worktree_path"])
                    _invoke_fault(fault_hook, "after-remove", entry)
                    inventory_paths = {
                        item["worktree"] for item in _inventory_projection(root)
                    }
                    if worktree.exists() or entry["worktree_path"] in inventory_paths:
                        raise WorktreeGCError("cleanup removal absence readback failed")
                    _invoke_fault(fault_hook, "after-readback", entry)
                ledger_sha_after = _record_cleanup(stores[entry["run_id"]], entry)
                _invoke_fault(fault_hook, "after-ledger-save", entry)
                receipt_payload = _entry_receipt_payload(
                    entry,
                    plan_sha256=plan_sha,
                    intent_sha256=intent_sha,
                    ledger_sha256_after=ledger_sha_after,
                )
                _write_envelope(state["receipt_path"], receipt_payload)
                _invoke_fault(fault_hook, "after-entry-receipt", entry)

            receipt_references: list[dict[str, Any]] = []
            for entry in intent["entries"]:
                receipt_path = _receipt_path(application_dir, entry)
                receipt = _validate_entry_receipt(
                    _load_record(receipt_path, label="cleanup entry receipt"),
                    entry=entry,
                    plan_sha256=plan_sha,
                    intent_sha256=intent_sha,
                )
                receipt_references.append(
                    {
                        "ordinal": entry["ordinal"],
                        "run_id": entry["run_id"],
                        "receipt_path": str(receipt_path),
                        "receipt_sha256": _file_sha256(receipt_path),
                    }
                )
                if receipt["ledger_sha256_after"] != _file_sha256(
                    stores[entry["run_id"]].path
                ):
                    raise WorktreeGCError("cleanup receipt ledger changed before completion")
            completion = {
                "schema": 1,
                "contract_version": COMPLETION_RECEIPT_CONTRACT,
                "plan_sha256": plan_sha,
                "intent_sha256": intent_sha,
                "entry_receipts": receipt_references,
                "complete": True,
                "authority": {field: False for field in sorted(_AUTHORITY_FIELDS)},
            }
            _invoke_fault(fault_hook, "before-completion", completion)
            completion_replayed = completion_path.exists()
            if completion_replayed:
                _validate_completion_receipt(
                    _load_record(completion_path, label="cleanup completion receipt"),
                    plan_sha256=plan_sha,
                    intent_sha256=intent_sha,
                    expected_receipts=receipt_references,
                )
            else:
                _write_envelope(completion_path, completion)
            return {
                "contract_version": APPLY_CONTRACT,
                "plan_sha256": plan_sha,
                "intent_path": str(intent_path),
                "intent_sha256": intent_sha,
                "completion_path": str(completion_path),
                "completion_sha256": _file_sha256(completion_path),
                "confirmed_absent": [
                    entry["worktree_path"] for entry in intent["entries"]
                ],
                "removed_this_invocation": removed_this_invocation,
                "replayed": intent_replayed,
                "completion_replayed": completion_replayed,
                "authority": {field: False for field in sorted(_AUTHORITY_FIELDS)},
            }
