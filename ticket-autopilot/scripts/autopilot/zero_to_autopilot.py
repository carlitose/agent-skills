"""Exact-inventory bootstrap from a local directory to a private GitHub repository."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterator, Sequence

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import CommandRunner, SubprocessCommandRunner
from .repository_bootstrap import (
    BootstrapRequest,
    RepositoryBootstrapError,
    bootstrap_private_github_repository,
    canonical_remote_url,
    normalized_github_remote,
)


MANIFEST_SCHEMA = 1
STATE_SCHEMA = 1
STATE_RELATIVE_PATH = Path("ticket-autopilot/zero-to-autopilot.json")
BOOTSTRAP_MESSAGE = "Initial private repository bootstrap"
DEFAULT_MAX_FILES = 10_000
DEFAULT_MAX_TOTAL_BYTES = 100 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_STATE_BYTES = 4 * 1024 * 1024
REDIRECTING_GIT_ENVIRONMENT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
        "GIT_SHALLOW_FILE",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
    }
)
WINDOWS_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{number}" for number in range(1, 10)}
    | {f"LPT{number}" for number in range(1, 10)}
)
ENTRY_KEYS = frozenset(
    {"path", "type", "sha256", "size", "mode", "disposition", "findings"}
)
MANIFEST_KEYS = frozenset(
    {
        "schema",
        "repository",
        "target",
        "visibility",
        "base_branch",
        "initial_git_state",
        "entries",
        "empty_directories",
        "limits",
    }
)
INTENT_KEYS = frozenset(
    {
        "repository",
        "git_common_dir",
        "target",
        "visibility",
        "base_branch",
        "requested_base_sha",
        "local_mode",
        "inventory_path",
        "inventory_sha256",
        "actor",
        "evidence",
        "authority_scope",
    }
)
STATE_KEYS = frozenset(
    {"schema", "intent", "intent_digest", "history", "local_base", "receipt"}
)
RECEIPT_KEYS = frozenset(
    {
        "schema",
        "status",
        "repository",
        "target",
        "visibility",
        "base_branch",
        "local_mode",
        "inventory_sha256",
        "initial_tree_oid",
        "base_sha",
        "normalized_remote",
        "observed_default_branch",
        "actor",
        "evidence",
        "repository_bootstrap_receipt_digest",
        "authority_scope",
    }
)
EVENT_KINDS = frozenset(
    {
        "intent-persisted",
        "git-initialized",
        "tree-prepared",
        "base-committed",
        "repository-bootstrap-completed",
        "zero-bootstrap-completed",
    }
)
RISKY_NAMES = frozenset(
    {
        ".env",
        ".npmrc",
        ".pypirc",
        ".netrc",
        "credentials",
        "credentials.json",
        "id_rsa",
        "id_ed25519",
    }
)
RISKY_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
RISKY_CONTENT = (
    (b"-----BEGIN PRIVATE KEY-----", "private-key-marker"),
    (b"-----BEGIN RSA PRIVATE KEY-----", "private-key-marker"),
    (b"-----BEGIN OPENSSH PRIVATE KEY-----", "private-key-marker"),
    (b"github_pat_", "github-token-marker"),
    (b"ghp_", "github-token-marker"),
    (b"OPENAI_API_KEY=", "api-key-marker"),
    (b"ANTHROPIC_API_KEY=", "api-key-marker"),
    (b"Authorization: Bearer ", "bearer-token-marker"),
)


class ZeroToAutopilotError(RuntimeError):
    """The requested local inventory/bootstrap transaction is unsafe or contradictory."""


@dataclass(frozen=True)
class ZeroBootstrapRequest:
    repository: Path
    target: str
    visibility: str
    base_branch: str
    inventory_path: Path
    inventory_sha256: str
    actor: str
    evidence: str
    base_sha: str | None = None

    @classmethod
    def normalize(
        cls,
        *,
        repository: str,
        target: str,
        visibility: str,
        base_branch: str,
        inventory_path: str,
        inventory_sha256: str,
        actor: str,
        evidence: str,
        base_sha: str | None = None,
    ) -> "ZeroBootstrapRequest":
        root = _canonical_directory(repository)
        manifest = _canonical_external_file(inventory_path, root)
        _validate_target_visibility_branch(target, visibility, base_branch)
        if not re.fullmatch(r"[0-9a-fA-F]{64}", inventory_sha256):
            raise ZeroToAutopilotError("inventory SHA-256 must be 64 hexadecimal characters")
        if not actor or actor != actor.strip() or not evidence or evidence != evidence.strip():
            raise ZeroToAutopilotError("zero-bootstrap actor and evidence must be non-empty and trimmed")
        if base_sha is not None and not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", base_sha):
            raise ZeroToAutopilotError("existing Git mode requires an exact base object ID")
        return cls(
            repository=root,
            target=target.casefold(),
            visibility=visibility,
            base_branch=base_branch,
            inventory_path=manifest,
            inventory_sha256=inventory_sha256.casefold(),
            actor=actor,
            evidence=evidence,
            base_sha=base_sha.casefold() if base_sha else None,
        )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_directory(value: str | Path) -> Path:
    raw = Path(value)
    if not raw.is_absolute():
        raise ZeroToAutopilotError("repository path must be absolute")
    if raw.is_symlink():
        raise ZeroToAutopilotError("repository root must not be a symbolic link")
    resolved = raw.resolve()
    if raw != resolved:
        raise ZeroToAutopilotError("repository path must be canonical and contain no symbolic-link ancestors")
    if not resolved.is_dir():
        raise ZeroToAutopilotError("repository path must identify an existing directory")
    return resolved


def _canonical_external_file(value: str | Path, repository: Path) -> Path:
    raw = Path(value)
    if not raw.is_absolute():
        raise ZeroToAutopilotError("inventory path must be absolute")
    resolved = raw.resolve()
    if raw != resolved or raw.is_symlink():
        raise ZeroToAutopilotError(
            "inventory path must be canonical and contain no symbolic-link ancestors"
        )
    try:
        resolved.relative_to(repository)
    except ValueError:
        return resolved
    raise ZeroToAutopilotError("inventory artifact must remain outside the source directory")


def _validate_target_visibility_branch(target: str, visibility: str, branch: str) -> None:
    parts = target.split("/")
    if (
        len(parts) != 2
        or any(part in {".", ".."} for part in parts)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", parts[0])
        or not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[1])
        or target.casefold().endswith(".git")
    ):
        raise ZeroToAutopilotError("target must be OWNER/REPOSITORY")
    if visibility != "private":
        raise ZeroToAutopilotError("zero-to-autopilot supports private visibility only")
    forbidden = ("..", "//", "@{", "\\", "~", "^", ":", "?", "*", "[")
    if (
        not branch
        or branch != branch.strip()
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", branch)
        or any(value in branch for value in forbidden)
        or branch.endswith(("/", ".", ".lock"))
        or any(part in {"", ".", ".."} or part.endswith(".lock") for part in branch.split("/"))
    ):
        raise ZeroToAutopilotError("base branch is not a safe Git branch name")


def _validate_relative(value: str) -> str:
    pure = PurePosixPath(value)
    parts = pure.parts
    if (
        not value
        or pure.is_absolute()
        or unicodedata.normalize("NFC", value) != value
        or any(
            part in {"", ".", ".."}
            or part.casefold() == ".git"
            or part.endswith((" ", "."))
            or part.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES
            or any(character in '<>:"\\|?*' for character in part)
            for part in parts
        )
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ZeroToAutopilotError(f"inventory path is unsafe: {value!r}")
    return value


def _safe_relative(path: Path, root: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise ZeroToAutopilotError("inventory path escapes the repository") from error
    return _validate_relative(relative.as_posix())


def _read_regular_file(path: Path, info: os.stat_result, relative: str, limit: int) -> bytes:
    try:
        if path.resolve(strict=True) != path:
            raise ZeroToAutopilotError(f"inventory path became unsafe: {relative}")
    except OSError as error:
        raise ZeroToAutopilotError(f"inventory file is unreadable: {relative}") from error
    if info.st_size > limit:
        raise ZeroToAutopilotError("inventory exceeds configured file or byte bounds")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ZeroToAutopilotError(f"inventory file is unreadable: {relative}") from error
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or (before.st_dev, before.st_ino) != (info.st_dev, info.st_ino)
            or before.st_mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX)
        ):
            raise ZeroToAutopilotError(f"inventory file changed during scan: {relative}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            content = handle.read(limit + 1)
        after = os.fstat(descriptor)
        if (
            path.resolve(strict=True) != path
            or len(content) > limit
            or len(content) != before.st_size
            or (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            != (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        ):
            raise ZeroToAutopilotError(f"inventory file changed during scan: {relative}")
        return content
    finally:
        os.close(descriptor)


def _read_external_file(path: Path, limit: int, label: str) -> bytes:
    try:
        info = path.stat(follow_symlinks=False)
    except OSError as error:
        raise ZeroToAutopilotError(f"{label} is unreadable") from error
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise ZeroToAutopilotError(f"{label} must be a regular non-symbolic-link file")
    return _read_regular_file(path, info, label, limit)


def _risk_findings(relative: str, content: bytes) -> list[str]:
    name = PurePosixPath(relative).name.casefold()
    findings: list[str] = []
    if name in RISKY_NAMES or name.startswith(".env.") or name.startswith("secrets."):
        findings.append("credential-bearing-name")
    if name.endswith(RISKY_SUFFIXES):
        findings.append("credential-bearing-suffix")
    for marker, finding in RISKY_CONTENT:
        if marker in content:
            findings.append(finding)
    return sorted(set(findings))


def _scan_entries(
    root: Path,
    *,
    excluded: set[str],
    max_files: int,
    max_total_bytes: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    if max_files < 1 or max_total_bytes < 1:
        raise ZeroToAutopilotError("inventory bounds must be positive")
    entries: list[dict[str, Any]] = []
    empty_directories: list[str] = []
    seen_casefold: dict[str, str] = {}
    total_bytes = 0
    scanned_entries = 0

    def walk(folder: Path) -> bool:
        nonlocal scanned_entries, total_bytes
        if folder.is_symlink() or folder.resolve() != folder:
            raise ZeroToAutopilotError(f"inventory directory is unsafe: {folder}")
        non_git_children = 0
        try:
            children = sorted(os.scandir(folder), key=lambda item: item.name.encode("utf-8"))
        except (OSError, UnicodeError) as error:
            raise ZeroToAutopilotError(f"inventory directory is unreadable: {folder}") from error
        for item in children:
            path = Path(item.path)
            if item.name.casefold() == ".git":
                if path == root / ".git":
                    continue
                relative = path.relative_to(root).as_posix()
                raise ZeroToAutopilotError(
                    f"nested Git metadata is unsupported: {relative}"
                )
            relative = _safe_relative(path, root)
            non_git_children += 1
            scanned_entries += 1
            if scanned_entries > max_files:
                raise ZeroToAutopilotError("inventory exceeds configured entry bounds")
            key = relative.casefold()
            previous = seen_casefold.setdefault(key, relative)
            if previous != relative:
                raise ZeroToAutopilotError(
                    f"inventory contains a case-colliding path: {previous!r} and {relative!r}"
                )
            try:
                info = item.stat(follow_symlinks=False)
            except OSError as error:
                raise ZeroToAutopilotError(f"inventory entry is unreadable: {relative}") from error
            if item.is_symlink():
                raise ZeroToAutopilotError(f"inventory symbolic links are unsupported: {relative}")
            if item.is_dir(follow_symlinks=False):
                if not walk(path):
                    empty_directories.append(relative)
                continue
            if not item.is_file(follow_symlinks=False):
                raise ZeroToAutopilotError(f"inventory special files are unsupported: {relative}")
            if info.st_mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX):
                raise ZeroToAutopilotError(f"inventory file has unsafe mode bits: {relative}")
            content = _read_regular_file(
                path, info, relative, max_total_bytes - total_bytes
            )
            total_bytes += len(content)
            if total_bytes > max_total_bytes:
                raise ZeroToAutopilotError("inventory exceeds configured file or byte bounds")
            findings = _risk_findings(relative, content)
            disposition = "exclude" if relative in excluded or findings else "publish"
            entries.append(
                {
                    "path": relative,
                    "type": "regular",
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "size": len(content),
                    "mode": "100755" if info.st_mode & 0o111 else "100644",
                    "disposition": disposition,
                    "findings": findings,
                }
            )
        return non_git_children > 0

    walk(root)
    paths = {entry["path"] for entry in entries}
    unknown = sorted(excluded - paths)
    if unknown:
        raise ZeroToAutopilotError(
            f"excluded inventory paths are absent or not regular files: {', '.join(unknown)}"
        )
    return sorted(entries, key=lambda item: item["path"]), sorted(empty_directories)


def build_inventory_manifest(
    *,
    repository: str,
    target: str,
    visibility: str,
    base_branch: str,
    excludes: Sequence[str] = (),
    max_files: int = DEFAULT_MAX_FILES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> dict[str, Any]:
    root = _canonical_directory(repository)
    _validate_target_visibility_branch(target, visibility, base_branch)
    normalized_excludes = {_validate_relative(value) for value in excludes}
    git_path = root / ".git"
    if git_path.is_symlink():
        raise ZeroToAutopilotError("Git metadata must not be a symbolic link")
    initial_git_state = "absent" if not git_path.exists() else "existing"
    entries, empty_directories = _scan_entries(
        root,
        excluded=normalized_excludes,
        max_files=max_files,
        max_total_bytes=max_total_bytes,
    )
    return {
        "schema": MANIFEST_SCHEMA,
        "repository": root.as_posix(),
        "target": target.casefold(),
        "visibility": visibility,
        "base_branch": base_branch,
        "initial_git_state": initial_git_state,
        "entries": entries,
        "empty_directories": empty_directories,
        "limits": {"max_files": max_files, "max_total_bytes": max_total_bytes},
    }


def _validate_manifest_shape(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS or manifest.get("schema") != MANIFEST_SCHEMA:
        raise ZeroToAutopilotError("inventory manifest shape is invalid")
    if manifest.get("visibility") != "private" or manifest.get("initial_git_state") not in {"absent", "existing"}:
        raise ZeroToAutopilotError("inventory manifest policy is invalid")
    limits = manifest.get("limits")
    if not isinstance(limits, dict) or set(limits) != {"max_files", "max_total_bytes"} or any(
        not isinstance(limits[key], int) or limits[key] < 1 for key in limits
    ):
        raise ZeroToAutopilotError("inventory manifest bounds are invalid")
    entries = manifest.get("entries")
    empty = manifest.get("empty_directories")
    if not isinstance(entries, list) or not isinstance(empty, list):
        raise ZeroToAutopilotError("inventory manifest entries are invalid")
    previous: str | None = None
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise ZeroToAutopilotError("inventory manifest entry shape is invalid")
        path = entry.get("path")
        findings = entry.get("findings")
        if (
            not isinstance(path, str)
            or (previous is not None and path <= previous)
            or entry.get("type") != "regular"
            or not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", "")))
            or not isinstance(entry.get("size"), int)
            or entry["size"] < 0
            or entry.get("mode") not in {"100644", "100755"}
            or entry.get("disposition") not in {"publish", "exclude"}
            or not isinstance(findings, list)
            or findings != sorted(set(findings))
            or any(not isinstance(item, str) or not item for item in findings)
            or (findings and entry.get("disposition") != "exclude")
        ):
            raise ZeroToAutopilotError("inventory manifest entry is malformed")
        _validate_relative(path)
        previous = path
    if empty != sorted(set(empty)) or any(not isinstance(item, str) or not item for item in empty):
        raise ZeroToAutopilotError("inventory empty-directory list is malformed")
    for item in empty:
        _validate_relative(item)
    _validate_target_visibility_branch(
        str(manifest.get("target", "")),
        str(manifest.get("visibility", "")),
        str(manifest.get("base_branch", "")),
    )
    _canonical_directory(str(manifest.get("repository", "")))
    return manifest


def write_inventory_manifest(manifest: dict[str, Any], output: str | Path) -> dict[str, Any]:
    _validate_manifest_shape(manifest)
    root = Path(manifest["repository"])
    destination = _canonical_external_file(output, root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = _canonical_bytes(manifest) + b"\n"
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)
    return {
        "schema": 1,
        "status": "inventory-prepared",
        "inventory": destination.as_posix(),
        "inventory_sha256": hashlib.sha256(content).hexdigest(),
        "repository": manifest["repository"],
        "target": manifest["target"],
        "base_branch": manifest["base_branch"],
        "file_count": len(manifest["entries"]),
        "publish_count": sum(item["disposition"] == "publish" for item in manifest["entries"]),
        "exclude_count": sum(item["disposition"] == "exclude" for item in manifest["entries"]),
        "requires_exact_apply_authority": True,
    }


def prepare_inventory(
    *,
    repository: str,
    target: str,
    visibility: str,
    base_branch: str,
    output: str,
    excludes: Sequence[str] = (),
    max_files: int = DEFAULT_MAX_FILES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> dict[str, Any]:
    manifest = build_inventory_manifest(
        repository=repository,
        target=target,
        visibility=visibility,
        base_branch=base_branch,
        excludes=excludes,
        max_files=max_files,
        max_total_bytes=max_total_bytes,
    )
    return write_inventory_manifest(manifest, output)


def load_inventory(request: ZeroBootstrapRequest) -> dict[str, Any]:
    content = _read_external_file(
        request.inventory_path, MAX_MANIFEST_BYTES, "inventory artifact"
    )
    if hashlib.sha256(content).hexdigest() != request.inventory_sha256:
        raise ZeroToAutopilotError("inventory artifact SHA-256 contradicts authority")
    try:
        manifest = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ZeroToAutopilotError("inventory artifact is not valid UTF-8 JSON") from error
    manifest = _validate_manifest_shape(manifest)
    if content != _canonical_bytes(manifest) + b"\n":
        raise ZeroToAutopilotError("inventory artifact is not canonically serialized")
    expected = {
        "repository": request.repository.as_posix(),
        "target": request.target,
        "visibility": request.visibility,
        "base_branch": request.base_branch,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ZeroToAutopilotError("inventory artifact contradicts bootstrap request")
    return manifest


def assert_inventory_current(manifest: dict[str, Any]) -> None:
    excludes = {
        item["path"] for item in manifest["entries"] if item["disposition"] == "exclude"
    }
    observed, empty = _scan_entries(
        Path(manifest["repository"]),
        excluded=excludes,
        max_files=manifest["limits"]["max_files"],
        max_total_bytes=manifest["limits"]["max_total_bytes"],
    )
    expected_by_path = {item["path"]: item for item in manifest["entries"]}
    observed_by_path = {item["path"]: item for item in observed}
    for path, item in observed_by_path.items():
        expected = expected_by_path.get(path)
        if expected and expected["disposition"] == "publish" and item["findings"]:
            raise ZeroToAutopilotError(
                f"risky inventory path cannot be published: {path}; "
                f"findings={','.join(item['findings'])}"
            )
    if observed != manifest["entries"]:
        changed = next(
            path
            for path in sorted(set(expected_by_path) | set(observed_by_path))
            if expected_by_path.get(path) != observed_by_path.get(path)
        )
        raise ZeroToAutopilotError(
            f"filesystem inventory drifted after authority was prepared: {changed}"
        )
    if empty != manifest["empty_directories"]:
        changed = next(
            path
            for path in sorted(set(empty) | set(manifest["empty_directories"]))
            if (path in empty) != (path in manifest["empty_directories"])
        )
        raise ZeroToAutopilotError(
            f"empty-directory inventory drifted after authority was prepared: {changed}"
        )


def _event_hash(sequence: int, previous: str | None, kind: str, details: dict[str, Any]) -> str:
    return _digest({"sequence": sequence, "previous": previous, "kind": kind, "details": details})


def _append_event(state: dict[str, Any], kind: str, details: dict[str, Any]) -> bool:
    key = _digest({"kind": kind, "details": details})
    if any(event.get("event_key") == key for event in state["history"]):
        return False
    sequence = len(state["history"]) + 1
    previous = state["history"][-1]["hash"] if state["history"] else None
    state["history"].append(
        {
            "sequence": sequence,
            "previous": previous,
            "kind": kind,
            "details": details,
            "event_key": key,
            "hash": _event_hash(sequence, previous, kind, details),
        }
    )
    return True


def _validate_state(state: Any) -> dict[str, Any]:
    if (
        not isinstance(state, dict)
        or set(state) != STATE_KEYS
        or state.get("schema") != STATE_SCHEMA
        or not isinstance(state.get("intent"), dict)
        or set(state["intent"]) != INTENT_KEYS
        or state.get("intent_digest") != _digest(state["intent"])
        or not isinstance(state.get("history"), list)
    ):
        raise ZeroToAutopilotError("zero-bootstrap state payload is malformed")
    intent = state["intent"]
    try:
        repository = Path(intent["repository"])
        common = Path(intent["git_common_dir"])
        inventory = Path(intent["inventory_path"])
        _validate_target_visibility_branch(
            intent["target"], intent["visibility"], intent["base_branch"]
        )
    except (KeyError, TypeError, ValueError, ZeroToAutopilotError) as error:
        raise ZeroToAutopilotError("zero-bootstrap intent is malformed") from error
    if (
        not repository.is_absolute()
        or not common.is_absolute()
        or not inventory.is_absolute()
        or intent.get("authority_scope") != "one-private-zero-to-autopilot-bootstrap"
        or intent.get("local_mode") not in {"initialized", "existing"}
        or not re.fullmatch(r"[0-9a-f]{64}", str(intent.get("inventory_sha256", "")))
        or not isinstance(intent.get("actor"), str)
        or not intent["actor"]
        or intent["actor"] != intent["actor"].strip()
        or not isinstance(intent.get("evidence"), str)
        or not intent["evidence"]
        or intent["evidence"] != intent["evidence"].strip()
        or (intent["local_mode"] == "initialized") != (intent["requested_base_sha"] is None)
    ):
        raise ZeroToAutopilotError("zero-bootstrap intent is malformed")
    if intent["requested_base_sha"] is not None and not re.fullmatch(
        r"[0-9a-f]{40}|[0-9a-f]{64}", str(intent["requested_base_sha"])
    ):
        raise ZeroToAutopilotError("zero-bootstrap intent base is malformed")

    ranks = {
        "intent-persisted": 0,
        "git-initialized": 1,
        "tree-prepared": 2,
        "base-committed": 3,
        "repository-bootstrap-completed": 4,
        "zero-bootstrap-completed": 5,
    }
    previous = None
    seen_keys: set[str] = set()
    kinds: list[str] = []
    for sequence, event in enumerate(state["history"], 1):
        if (
            not isinstance(event, dict)
            or set(event)
            != {"sequence", "previous", "kind", "details", "event_key", "hash"}
            or event.get("sequence") != sequence
        ):
            raise ZeroToAutopilotError("zero-bootstrap history sequence is invalid")
        kind, details = event.get("kind"), event.get("details")
        if kind not in EVENT_KINDS or not isinstance(details, dict):
            raise ZeroToAutopilotError("zero-bootstrap history event is malformed")
        event_key = _digest({"kind": kind, "details": details})
        if (
            event.get("previous") != previous
            or event.get("event_key") != event_key
            or event_key in seen_keys
            or event.get("hash") != _event_hash(sequence, previous, kind, details)
            or (kinds and ranks[kind] <= ranks[kinds[-1]])
        ):
            raise ZeroToAutopilotError("zero-bootstrap history hash chain is invalid")
        seen_keys.add(event_key)
        kinds.append(kind)
        previous = event["hash"]
    if not kinds or kinds[0] != "intent-persisted" or state["history"][0]["details"] != {
        "intent_digest": state["intent_digest"]
    }:
        raise ZeroToAutopilotError("zero-bootstrap history lacks persisted intent")
    if "git-initialized" in kinds and intent["local_mode"] != "initialized":
        raise ZeroToAutopilotError("zero-bootstrap Git initialization history is inconsistent")
    if "git-initialized" in kinds:
        event = state["history"][kinds.index("git-initialized")]
        if event["details"] != {"base_branch": intent["base_branch"]}:
            raise ZeroToAutopilotError("zero-bootstrap Git initialization history is malformed")

    local = state.get("local_base")
    if local is not None and (
        not isinstance(local, dict)
        or set(local) != {"tree_oid", "base_sha"}
        or not all(
            isinstance(local[key], str)
            and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", local[key])
            for key in local
        )
    ):
        raise ZeroToAutopilotError("zero-bootstrap local base is malformed")
    if ("base-committed" in kinds) != (local is not None):
        raise ZeroToAutopilotError("zero-bootstrap local base history is inconsistent")
    if local is not None and intent["local_mode"] == "initialized" and "git-initialized" not in kinds:
        raise ZeroToAutopilotError("zero-bootstrap local base lacks initialization history")
    if local is not None:
        base_event = state["history"][kinds.index("base-committed")]
        if base_event["details"] != local:
            raise ZeroToAutopilotError("zero-bootstrap local base history is malformed")
        if intent["requested_base_sha"] is not None and local["base_sha"] != intent["requested_base_sha"]:
            raise ZeroToAutopilotError("zero-bootstrap local base contradicts authority")
        if "tree-prepared" not in kinds:
            raise ZeroToAutopilotError("zero-bootstrap local base lacks exact tree proof")
        tree_event = state["history"][kinds.index("tree-prepared")]
        if tree_event["details"] != {"tree_oid": local["tree_oid"]}:
            raise ZeroToAutopilotError("zero-bootstrap tree history is malformed")

    if "tree-prepared" in kinds:
        tree_details = state["history"][kinds.index("tree-prepared")]["details"]
        if set(tree_details) != {"tree_oid"} or not re.fullmatch(
            r"[0-9a-f]{40}|[0-9a-f]{64}", str(tree_details["tree_oid"])
        ):
            raise ZeroToAutopilotError("zero-bootstrap tree history is malformed")
    receipt = state.get("receipt")
    completions = [event for event in state["history"] if event["kind"] == "zero-bootstrap-completed"]
    nested = [event for event in state["history"] if event["kind"] == "repository-bootstrap-completed"]
    if len(nested) > 1 or (
        nested
        and (
            set(nested[0]["details"]) != {"receipt_digest"}
            or not re.fullmatch(
                r"[0-9a-f]{64}", str(nested[0]["details"]["receipt_digest"])
            )
        )
    ):
        raise ZeroToAutopilotError("repository-bootstrap completion history is malformed")
    if receipt is None:
        if completions:
            raise ZeroToAutopilotError("zero-bootstrap history completes without receipt")
    elif (
        local is None
        or not isinstance(receipt, dict)
        or set(receipt) != RECEIPT_KEYS
        or receipt.get("schema") != 1
        or receipt.get("status") != "repository-ready-for-ticket-autopilot"
        or receipt.get("repository") != intent["repository"]
        or receipt.get("target") != intent["target"]
        or receipt.get("visibility") != "private"
        or receipt.get("base_branch") != intent["base_branch"]
        or receipt.get("local_mode") != intent["local_mode"]
        or receipt.get("inventory_sha256") != intent["inventory_sha256"]
        or receipt.get("initial_tree_oid") != local["tree_oid"]
        or receipt.get("base_sha") != local["base_sha"]
        or receipt.get("normalized_remote")
        != normalized_github_remote(canonical_remote_url(intent["target"]))
        or receipt.get("observed_default_branch") != intent["base_branch"]
        or receipt.get("actor") != intent["actor"]
        or receipt.get("evidence") != intent["evidence"]
        or receipt.get("authority_scope")
        != "bootstrap-only-no-run-delivery-merge-source-wiki-pi-or-cleanup"
        or len(nested) != 1
        or nested[0]["details"]
        != {"receipt_digest": receipt.get("repository_bootstrap_receipt_digest")}
        or len(completions) != 1
        or completions[0] != state["history"][-1]
        or completions[0]["details"] != {"receipt_digest": _digest(receipt)}
    ):
        raise ZeroToAutopilotError("zero-bootstrap completion receipt is malformed")
    return state


class ZeroBootstrapStateStore:
    def __init__(self, common_git_dir: Path):
        self.path = common_git_dir / STATE_RELATIVE_PATH
        self.lock_path = self.path.with_suffix(".lock")

    @contextmanager
    def locked(self) -> Iterator[None]:
        if self.path.parent.is_symlink() or self.path.is_symlink() or self.lock_path.is_symlink():
            raise ZeroToAutopilotError("zero-bootstrap state paths must not be symbolic links")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.parent.is_dir() or self.path.parent.is_symlink():
            raise ZeroToAutopilotError("zero-bootstrap state directory is unsafe")
        with self.lock_path.open("a+", encoding="ascii") as handle:
            acquire_file_lock(handle, blocking=True)
            try:
                handle.seek(0)
                handle.truncate()
                handle.write(f"{os.getpid()}\n")
                handle.flush()
                os.fsync(handle.fileno())
                yield
            finally:
                release_file_lock(handle)

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        if self.path.parent.is_symlink() or self.path.is_symlink():
            raise ZeroToAutopilotError("zero-bootstrap state paths must not be symbolic links")
        try:
            content = _read_external_file(
                self.path, MAX_STATE_BYTES, "zero-bootstrap state"
            )
            envelope = json.loads(content.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ZeroToAutopilotError("zero-bootstrap state is not valid UTF-8 JSON") from error
        payload = envelope.get("payload") if isinstance(envelope, dict) else None
        if (
            not isinstance(envelope, dict)
            or envelope.get("envelope_schema") != 1
            or not isinstance(payload, dict)
            or envelope.get("integrity") != _digest(payload)
        ):
            raise ZeroToAutopilotError("zero-bootstrap state integrity check failed")
        return _validate_state(payload)

    def save(self, state: dict[str, Any]) -> None:
        _validate_state(state)
        envelope = {"envelope_schema": 1, "integrity": _digest(state), "payload": state}
        content = _canonical_bytes(envelope) + b"\n"
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
        )
        temporary_path = Path(temporary)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
            if os.name != "nt":
                directory = os.open(self.path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            temporary_path.unlink(missing_ok=True)


def _run(runner: CommandRunner, cwd: Path, command: list[str]) -> str:
    result = runner.run(command, cwd=cwd)
    if result.returncode:
        detail = result.stderr or result.stdout or "command failed"
        raise ZeroToAutopilotError(f"{' '.join(command)} failed: {detail}")
    return result.stdout


def _git_repository(runner: CommandRunner, root: Path) -> tuple[Path, Path] | None:
    result = runner.run(["git", "rev-parse", "--show-toplevel"], cwd=root)
    if result.returncode:
        return None
    observed = Path(result.stdout).resolve()
    if observed != root:
        raise ZeroToAutopilotError("Git repository root contradicts zero-bootstrap root")
    common_raw = _run(runner, root, ["git", "rev-parse", "--git-common-dir"])
    common = Path(common_raw)
    common = common.resolve() if common.is_absolute() else (root / common).resolve()
    return observed, common


def _object_oid(format_name: str, content: bytes) -> str:
    payload = f"blob {len(content)}\0".encode("ascii") + content
    if format_name == "sha1":
        return hashlib.sha1(payload).hexdigest()  # noqa: S324 - Git object identity
    if format_name == "sha256":
        return hashlib.sha256(payload).hexdigest()
    raise ZeroToAutopilotError(f"unsupported Git object format: {format_name}")


def _entry_content(root: Path, entry: dict[str, Any]) -> bytes:
    path = root / entry["path"]
    if path.is_symlink() or path.resolve() != path:
        raise ZeroToAutopilotError(
            f"authorized publish path became unsafe: {entry['path']}"
        )
    try:
        info = path.stat(follow_symlinks=False)
    except OSError as error:
        raise ZeroToAutopilotError(
            f"authorized publish path is unreadable: {entry['path']}"
        ) from error
    content = _read_regular_file(path, info, entry["path"], entry["size"])
    mode = "100755" if info.st_mode & 0o111 else "100644"
    if (
        len(content) != entry["size"]
        or hashlib.sha256(content).hexdigest() != entry["sha256"]
        or mode != entry["mode"]
    ):
        raise ZeroToAutopilotError(
            f"authorized publish path drifted: {entry['path']}"
        )
    return content


def _expected_tree_entries(manifest: dict[str, Any], object_format: str) -> dict[str, tuple[str, str]]:
    root = Path(manifest["repository"])
    return {
        entry["path"]: (
            entry["mode"],
            _object_oid(object_format, _entry_content(root, entry)),
        )
        for entry in manifest["entries"]
        if entry["disposition"] == "publish"
    }


def _tree_entries(runner: CommandRunner, root: Path, tree_oid: str) -> dict[str, tuple[str, str]]:
    output = _run(runner, root, ["git", "ls-tree", "-r", "-z", tree_oid])
    observed: dict[str, tuple[str, str]] = {}
    for record in output.split("\0"):
        if not record:
            continue
        metadata, path = record.split("\t", 1)
        mode, kind, oid = metadata.split(" ", 2)
        if kind != "blob" or path in observed:
            raise ZeroToAutopilotError("initial Git tree contains unsupported or duplicate entries")
        observed[path] = (mode, oid)
    return observed


def _assert_tree_matches(runner: CommandRunner, root: Path, tree_oid: str, manifest: dict[str, Any]) -> None:
    object_format = _run(runner, root, ["git", "rev-parse", "--show-object-format"])
    if _tree_entries(runner, root, tree_oid) != _expected_tree_entries(manifest, object_format):
        raise ZeroToAutopilotError("Git tree differs from authorized publish inventory")


def _index_fingerprint(runner: CommandRunner, root: Path) -> str:
    raw = Path(_run(runner, root, ["git", "rev-parse", "--git-path", "index"]))
    index = raw if raw.is_absolute() else root / raw
    if index.is_symlink():
        raise ZeroToAutopilotError("Git index must not be a symbolic link")
    return _file_sha256(index) if index.exists() else "absent"


def _local_origin_urls(runner: CommandRunner, root: Path) -> tuple[str, ...]:
    result = runner.run(
        ["git", "config", "--local", "--get-all", "remote.origin.url"],
        cwd=root,
    )
    if result.returncode == 1:
        return ()
    if result.returncode:
        raise ZeroToAutopilotError(
            f"local origin inspection failed: {result.stderr or result.stdout}"
        )
    return tuple(result.stdout.splitlines())


def _origin_identities(runner: CommandRunner, root: Path) -> tuple[str, ...]:
    listed = runner.run(["git", "remote"], cwd=root)
    if listed.returncode or "origin" not in listed.stdout.splitlines():
        return ()
    fetch = _run(runner, root, ["git", "remote", "get-url", "--all", "origin"])
    push = _run(runner, root, ["git", "remote", "get-url", "--all", "--push", "origin"])
    values = tuple(dict.fromkeys(line for line in (fetch + "\n" + push).splitlines() if line))
    try:
        return tuple(normalized_github_remote(value) for value in values)
    except RepositoryBootstrapError as error:
        raise ZeroToAutopilotError(str(error)) from error


def _assert_initialized_refs(
    runner: CommandRunner,
    root: Path,
    branch: str,
    base_sha: str | None,
) -> None:
    output = _run(
        runner,
        root,
        ["git", "for-each-ref", "--format=%(refname) %(objectname)"],
    )
    observed: dict[str, str] = {}
    for line in output.splitlines():
        name, sha = line.split(" ", 1)
        observed[name] = sha
    if base_sha is None:
        if observed:
            raise ZeroToAutopilotError(
                "initialized Git repository contains unexpected refs before the root commit"
            )
        return
    head = f"refs/heads/{branch}"
    remote = f"refs/remotes/origin/{branch}"
    if observed.get(head) != base_sha or any(
        name not in {head, remote} or sha != base_sha
        for name, sha in observed.items()
    ):
        raise ZeroToAutopilotError(
            "initialized Git repository contains unexpected or contradictory refs"
        )


class _BootstrapCommandRunner:
    """Suppress local push hooks/signing while retaining provider credential transport."""

    def __init__(self, delegate: CommandRunner):
        self.delegate = delegate

    def run(self, command: list[str], *, cwd: Path) -> Any:
        if command[:2] == ["git", "push"]:
            command = [
                "git",
                "-c",
                "push.gpgSign=false",
                "push",
                "--no-verify",
                *command[2:],
            ]
        return self.delegate.run(command, cwd=cwd)


class ZeroToAutopilotTransaction:
    def __init__(
        self,
        runner: CommandRunner | None = None,
        *,
        bootstrap: Callable[[BootstrapRequest], dict[str, Any]] | None = None,
        fault: Callable[[str], None] | None = None,
    ):
        self.runner = runner or SubprocessCommandRunner()
        bootstrap_runner = _BootstrapCommandRunner(self.runner)
        self.bootstrap = bootstrap or (
            lambda request: bootstrap_private_github_repository(
                request, runner=bootstrap_runner
            )
        )
        self.fault = fault or (lambda _stage: None)

    def _record(self, store: ZeroBootstrapStateStore, state: dict[str, Any], kind: str, details: dict[str, Any]) -> None:
        if _append_event(state, kind, details):
            store.save(state)

    def _initialized_base(
        self,
        request: ZeroBootstrapRequest,
        manifest: dict[str, Any],
        store: ZeroBootstrapStateStore,
        state: dict[str, Any],
    ) -> tuple[str, str]:
        root = request.repository
        repository = _git_repository(self.runner, root)
        if repository is None:
            self.fault("pre-init")
            _run(
                self.runner,
                root,
                [
                    "git",
                    "init",
                    "--template=",
                    "--object-format=sha1",
                    "-b",
                    request.base_branch,
                    str(root),
                ],
            )
            self.fault("post-init")
        repository = _git_repository(self.runner, root)
        if repository is None or repository[1] != store.path.parents[1]:
            raise ZeroToAutopilotError("initialized Git common directory contradicts persisted intent")
        if _run(self.runner, root, ["git", "symbolic-ref", "--short", "HEAD"]) != request.base_branch:
            raise ZeroToAutopilotError("initialized Git HEAD contradicts the authorized base branch")
        if _run(self.runner, root, ["git", "rev-parse", "--show-object-format"]) != "sha1":
            raise ZeroToAutopilotError("initialized Git object format must be sha1 for GitHub")
        self._record(store, state, "git-initialized", {"base_branch": request.base_branch})
        assert_inventory_current(manifest)
        existing = self.runner.run(
            ["git", "rev-parse", "--verify", f"refs/heads/{request.base_branch}^{{commit}}"],
            cwd=root,
        )
        if existing.returncode == 0:
            base_sha = existing.stdout
            _assert_initialized_refs(
                self.runner, root, request.base_branch, base_sha
            )
            parents = _run(self.runner, root, ["git", "rev-list", "--parents", "-n", "1", base_sha]).split()
            if parents != [base_sha]:
                raise ZeroToAutopilotError("initialized bootstrap branch is not one root commit")
            tree_oid = _run(self.runner, root, ["git", "rev-parse", f"{base_sha}^{{tree}}"])
            if _run(self.runner, root, ["git", "show", "-s", "--format=%B", base_sha]) != BOOTSTRAP_MESSAGE:
                raise ZeroToAutopilotError("initialized bootstrap commit message is contradictory")
            _assert_tree_matches(self.runner, root, tree_oid, manifest)
        else:
            _assert_initialized_refs(
                self.runner, root, request.base_branch, None
            )
            _run(self.runner, root, ["git", "read-tree", "--empty"])
            expected = _expected_tree_entries(manifest, "sha1")
            for path, (mode, expected_oid) in expected.items():
                oid = _run(
                    self.runner,
                    root,
                    ["git", "hash-object", "-w", "--no-filters", "--", path],
                )
                if oid != expected_oid:
                    raise ZeroToAutopilotError(
                        f"Git blob differs from authorized content: {path}"
                    )
                _run(
                    self.runner,
                    root,
                    ["git", "update-index", "--add", "--cacheinfo", f"{mode},{oid},{path}"],
                )
            tree_oid = _run(self.runner, root, ["git", "write-tree"])
            _assert_tree_matches(self.runner, root, tree_oid, manifest)
            self._record(store, state, "tree-prepared", {"tree_oid": tree_oid})
            self.fault("post-tree")
            command = [
                "git",
                "-c",
                "user.name=Ticket Autopilot",
                "-c",
                "user.email=ticket-autopilot@localhost",
                "-c",
                "commit.gpgSign=false",
                "-c",
                f"core.hooksPath={os.devnull}",
                "commit",
                "--no-verify",
                "--allow-empty",
                "-m",
                BOOTSTRAP_MESSAGE,
            ]
            _run(self.runner, root, command)
            self.fault("post-commit")
            base_sha = _run(self.runner, root, ["git", "rev-parse", f"refs/heads/{request.base_branch}^{{commit}}"])
            actual_tree = _run(self.runner, root, ["git", "rev-parse", f"{base_sha}^{{tree}}"])
            if actual_tree != tree_oid:
                raise ZeroToAutopilotError("created root commit tree contradicts prepared tree")
            _assert_initialized_refs(
                self.runner, root, request.base_branch, base_sha
            )
        if state["local_base"] is not None and state["local_base"] != {"tree_oid": tree_oid, "base_sha": base_sha}:
            raise ZeroToAutopilotError("persisted local base contradicts Git state")
        if state["local_base"] is None:
            state["local_base"] = {"tree_oid": tree_oid, "base_sha": base_sha}
            _append_event(state, "base-committed", state["local_base"])
            store.save(state)
        return tree_oid, base_sha

    def _existing_base(
        self,
        request: ZeroBootstrapRequest,
        manifest: dict[str, Any],
    ) -> tuple[str, str, str]:
        if request.base_sha is None:
            raise ZeroToAutopilotError("existing Git mode requires --base-sha")
        before = _index_fingerprint(self.runner, request.repository)
        observed = _run(
            self.runner,
            request.repository,
            ["git", "rev-parse", "--verify", f"refs/heads/{request.base_branch}^{{commit}}"],
        )
        if observed.casefold() != request.base_sha:
            raise ZeroToAutopilotError("existing Git base branch differs from authorized SHA")
        tree_oid = _run(self.runner, request.repository, ["git", "rev-parse", f"{observed}^{{tree}}"])
        _assert_tree_matches(self.runner, request.repository, tree_oid, manifest)
        assert_inventory_current(manifest)
        if _index_fingerprint(self.runner, request.repository) != before:
            raise ZeroToAutopilotError("existing Git index changed during local proof")
        return tree_oid, observed, before

    def apply(self, request: ZeroBootstrapRequest) -> dict[str, Any]:
        redirected = sorted(
            key for key in REDIRECTING_GIT_ENVIRONMENT if os.environ.get(key)
        )
        if redirected:
            raise ZeroToAutopilotError(
                "redirecting Git environment is unsupported: " + ", ".join(redirected)
            )
        manifest = load_inventory(request)
        if (request.repository / ".git").is_symlink():
            raise ZeroToAutopilotError("Git metadata must not be a symbolic link")
        candidate_state_parent = request.repository / ".git" / STATE_RELATIVE_PATH.parent
        if candidate_state_parent.is_symlink():
            raise ZeroToAutopilotError("zero-bootstrap state paths must not be symbolic links")
        assert_inventory_current(manifest)
        repository = _git_repository(self.runner, request.repository)
        precreated_state = request.repository / ".git" / STATE_RELATIVE_PATH
        if repository is None:
            if (request.repository / ".git").exists() and not precreated_state.is_file():
                raise ZeroToAutopilotError("malformed or unexpected .git state blocks initialization")
            mode = "initialized"
            common = request.repository / ".git"
            if request.base_sha is not None:
                raise ZeroToAutopilotError("new Git mode must not supply --base-sha")
            if manifest["initial_git_state"] != "absent":
                raise ZeroToAutopilotError("inventory did not authorize missing-Git initialization")
        else:
            _, common = repository
            mode = "existing"
            if manifest["initial_git_state"] != "existing":
                # Exact initialized replay retains an absent initial-state manifest.
                candidate_store = ZeroBootstrapStateStore(common)
                candidate_state = candidate_store.load()
                if not candidate_state or candidate_state["intent"].get("local_mode") != "initialized":
                    raise ZeroToAutopilotError("inventory Git-state classification contradicts repository")
                mode = "initialized"
        store = ZeroBootstrapStateStore(common)
        intent = {
            "repository": request.repository.as_posix(),
            "git_common_dir": common.resolve().as_posix(),
            "target": request.target,
            "visibility": request.visibility,
            "base_branch": request.base_branch,
            "requested_base_sha": request.base_sha,
            "local_mode": mode,
            "inventory_path": request.inventory_path.as_posix(),
            "inventory_sha256": request.inventory_sha256,
            "actor": request.actor,
            "evidence": request.evidence,
            "authority_scope": "one-private-zero-to-autopilot-bootstrap",
        }
        with store.locked():
            state = store.load()
            replayed = state is not None
            if state is None:
                state = {
                    "schema": STATE_SCHEMA,
                    "intent": intent,
                    "intent_digest": _digest(intent),
                    "history": [],
                    "local_base": None,
                    "receipt": None,
                }
                _append_event(state, "intent-persisted", {"intent_digest": state["intent_digest"]})
                store.save(state)
            elif state["intent"] != intent:
                raise ZeroToAutopilotError("zero-bootstrap intent is immutable")
            completed = state["receipt"] is not None
            if mode == "initialized":
                tree_oid, base_sha = self._initialized_base(request, manifest, store, state)
                index_before = None
            else:
                tree_oid, base_sha, index_before = self._existing_base(request, manifest)
                if state["local_base"] not in (None, {"tree_oid": tree_oid, "base_sha": base_sha}):
                    raise ZeroToAutopilotError("persisted local base contradicts existing Git")
                if state["local_base"] is None:
                    state["local_base"] = {"tree_oid": tree_oid, "base_sha": base_sha}
                    _append_event(state, "tree-prepared", {"tree_oid": tree_oid})
                    _append_event(state, "base-committed", state["local_base"])
                    store.save(state)
            self.fault("post-base")
            assert_inventory_current(manifest)
            if _origin_identities(self.runner, request.repository) and not _local_origin_urls(
                self.runner, request.repository
            ):
                raise ZeroToAutopilotError(
                    "effective origin must be persisted in local repository configuration"
                )
            self.fault("pre-bootstrap")
            bootstrap_request = BootstrapRequest.normalize(
                repository=request.repository.as_posix(),
                target=request.target,
                visibility="private",
                base_branch=request.base_branch,
                base_sha=base_sha,
                actor=request.actor,
                evidence=request.evidence,
            )
            nested = self.bootstrap(bootstrap_request)
            self.fault("post-bootstrap")
            nested_receipt = nested.get("receipt") if isinstance(nested, dict) else None
            if (
                not isinstance(nested_receipt, dict)
                or nested_receipt.get("status") != "completed"
                or nested_receipt.get("repository") != request.target
                or nested_receipt.get("visibility") != "private"
                or nested_receipt.get("base_branch") != request.base_branch
                or nested_receipt.get("local_sha") != base_sha
                or nested_receipt.get("remote_sha") != base_sha
                or nested_receipt.get("actor") != request.actor
                or nested_receipt.get("evidence") != request.evidence
                or nested_receipt.get("observed_default_branch") != request.base_branch
            ):
                raise ZeroToAutopilotError("repository-bootstrap receipt contradicts zero-bootstrap intent")
            expected_remote = normalized_github_remote(canonical_remote_url(request.target))
            identities = _origin_identities(self.runner, request.repository)
            local_urls = _local_origin_urls(self.runner, request.repository)
            try:
                local_identities = tuple(
                    normalized_github_remote(value) for value in local_urls
                )
            except RepositoryBootstrapError as error:
                raise ZeroToAutopilotError(str(error)) from error
            if (
                not identities
                or any(identity != expected_remote for identity in identities)
                or not local_identities
                or any(identity != expected_remote for identity in local_identities)
            ):
                raise ZeroToAutopilotError("final origin readback contradicts zero-bootstrap target")
            current_base = _run(
                self.runner,
                request.repository,
                ["git", "rev-parse", "--verify", f"refs/heads/{request.base_branch}^{{commit}}"],
            )
            current_tree = _run(self.runner, request.repository, ["git", "rev-parse", f"{current_base}^{{tree}}"])
            if current_base != base_sha or current_tree != tree_oid:
                raise ZeroToAutopilotError("final local base readback drifted")
            if mode == "initialized":
                _assert_initialized_refs(
                    self.runner, request.repository, request.base_branch, base_sha
                )
            _assert_tree_matches(self.runner, request.repository, current_tree, manifest)
            assert_inventory_current(manifest)
            if index_before is not None and _index_fingerprint(self.runner, request.repository) != index_before:
                raise ZeroToAutopilotError("existing Git index changed during bootstrap")
            self.fault("post-readback")
            nested_digest = _digest(nested_receipt)
            self._record(store, state, "repository-bootstrap-completed", {"receipt_digest": nested_digest})
            self.fault("post-nested-event")
            receipt = {
                "schema": 1,
                "status": "repository-ready-for-ticket-autopilot",
                "repository": request.repository.as_posix(),
                "target": request.target,
                "visibility": "private",
                "base_branch": request.base_branch,
                "local_mode": mode,
                "inventory_sha256": request.inventory_sha256,
                "initial_tree_oid": tree_oid,
                "base_sha": base_sha,
                "normalized_remote": expected_remote,
                "observed_default_branch": nested_receipt["observed_default_branch"],
                "actor": request.actor,
                "evidence": request.evidence,
                "repository_bootstrap_receipt_digest": nested_digest,
                "authority_scope": "bootstrap-only-no-run-delivery-merge-source-wiki-pi-or-cleanup",
            }
            if completed:
                if state["receipt"] != receipt:
                    raise ZeroToAutopilotError("completed zero-bootstrap receipt is immutable")
            else:
                state["receipt"] = receipt
                _append_event(state, "zero-bootstrap-completed", {"receipt_digest": _digest(receipt)})
                store.save(state)
            self.fault("post-completion")
            return {
                "state_path": store.path.as_posix(),
                "intent_digest": state["intent_digest"],
                "history_events": len(state["history"]),
                "replayed": replayed,
                "receipt": receipt,
            }


def apply_zero_to_autopilot(
    request: ZeroBootstrapRequest,
    *,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    return ZeroToAutopilotTransaction(runner).apply(request)


def inspect_zero_to_autopilot(repository: str | Path) -> dict[str, Any]:
    root = _canonical_directory(repository)
    if (root / ".git").is_symlink() or (
        root / ".git" / STATE_RELATIVE_PATH.parent
    ).is_symlink():
        raise ZeroToAutopilotError("zero-bootstrap state paths must not be symbolic links")
    runner = SubprocessCommandRunner()
    observed = _git_repository(runner, root)
    common = observed[1] if observed else root / ".git"
    store = ZeroBootstrapStateStore(common)
    state = store.load()
    if state is None:
        return {
            "schema": 1,
            "status": "absent",
            "repository": root.as_posix(),
            "state_path": store.path.as_posix(),
        }
    return {
        "schema": 1,
        "status": "completed" if state["receipt"] is not None else "in-progress",
        "repository": root.as_posix(),
        "state_path": store.path.as_posix(),
        "intent_digest": state["intent_digest"],
        "history_events": len(state["history"]),
        "receipt": state["receipt"],
    }
