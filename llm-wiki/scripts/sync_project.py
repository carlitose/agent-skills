#!/usr/bin/env python3
"""Compile one existing project wiki through the versioned ``wiki-sync-v1`` boundary.

The protected wiki is never used as a work area.  Project-document ingest, timeline rebuild,
scope validation, and the full lint run happen in a disposable staging copy.  A successful
internal-untracked or external result is applied only after a generated-tree compare-and-swap;
an internal-tracked result is frozen in Git metadata for a separate delivery owner.

Usage:
    python3 sync_project.py <project-root> [--wiki-root <path>]... [--json]
        [--origin-kind <kind>] [--origin-id <id>] [--trigger <name>]...
        [--autopilot-root <path>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterator, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_timeline import build as build_timeline  # noqa: E402
from ingest_docs import (  # noqa: E402
    TicketParserError,
    default_autopilot_root,
    ingest as ingest_docs,
)
from lint_wiki import ERROR, run_passes  # noqa: E402
from project_binding import BindingError, config_path, read_binding  # noqa: E402

CONTRACT_VERSION = "wiki-sync-v1"
CLAIM_CEILING = "implementation-complete"
REQUIRED_WIKI_FILES = ("purpose.md", "schema.md", "wiki/index.md", "wiki/log.md")
MANAGED_ROOT_FILES = {"purpose.md", "schema.md", "llm-wiki-project.json"}
MANAGED_ROOT_DIRECTORIES = {"audit", "raw", "wiki"}
RETRYABLE_REASONS = {"concurrent-operation", "stale-tree"}


class SyncFailure(RuntimeError):
    """A fail-closed outcome whose reason is part of the public result contract."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Entry:
    kind: str
    mode: int
    digest: str


Observer = Callable[[str], None]


def _observe(observer: Observer | None, event: str) -> None:
    if observer is not None:
        observer(event)


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _entry(root: Path, path: Path) -> tuple[str, Entry] | None:
    relative = path.relative_to(root).as_posix()
    details = path.lstat()
    mode = stat.S_IMODE(details.st_mode)
    if path.is_symlink():
        target = os.readlink(path)
        return relative, Entry(
            "symlink", mode, hashlib.sha256(target.encode("utf-8")).hexdigest()
        )
    if path.is_file():
        return relative, Entry("file", mode, _file_digest(path))
    return None


def _subtree_inventory(root: Path, relative_root: str) -> dict[str, Entry]:
    start = root / relative_root
    if not start.exists() and not start.is_symlink():
        return {}
    paths = [start] if start.is_symlink() or start.is_file() else sorted(start.rglob("*"))
    inventory: dict[str, Entry] = {}
    for path in paths:
        item = _entry(root, path)
        if item is not None:
            inventory[item[0]] = item[1]
    return inventory


def _generated_inventory(root: Path) -> dict[str, Entry]:
    return {
        path: entry
        for path, entry in _subtree_inventory(root, "wiki").items()
        if PurePosixPath(path).suffix.lower() == ".md"
    }


def _managed_inventory(root: Path) -> dict[str, Entry]:
    inventory: dict[str, Entry] = {}
    for name in MANAGED_ROOT_FILES:
        path = root / name
        if path.exists() or path.is_symlink():
            item = _entry(root, path)
            if item is not None:
                inventory[item[0]] = item[1]
    for name in MANAGED_ROOT_DIRECTORIES:
        inventory.update(_subtree_inventory(root, name))
    return inventory


def _stage_copy(root: Path, destination: Path) -> None:
    destination.mkdir()
    for name in sorted(MANAGED_ROOT_FILES):
        source = root / name
        if source.exists() or source.is_symlink():
            shutil.copy2(source, destination / name, follow_symlinks=False)
    for name in sorted(MANAGED_ROOT_DIRECTORIES):
        source = root / name
        if source.exists() or source.is_symlink():
            shutil.copytree(
                source,
                destination / name,
                symlinks=True,
                copy_function=shutil.copy2,
            )


def _tree_digest(inventory: Mapping[str, Entry]) -> str:
    return _sha256(
        [
            {"path": path, "kind": item.kind, "mode": item.mode, "sha256": item.digest}
            for path, item in sorted(inventory.items())
        ]
    )


def _changed_paths(before: Mapping[str, Entry], after: Mapping[str, Entry]) -> list[str]:
    return sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
    )


def _path_value(value: object, *, label: str) -> Path:
    if not isinstance(value, (str, os.PathLike)):
        raise SyncFailure("broken-binding", f"{label} must be a filesystem path")
    return Path(value)


def _canonical_directory(path: object, *, label: str) -> Path:
    raw = _path_value(path, label=label)
    try:
        resolved = raw.expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise SyncFailure("broken-binding", f"{label} does not resolve: {raw}: {error}") from error
    if not resolved.is_dir():
        raise SyncFailure("broken-binding", f"{label} is not a directory: {resolved}")
    return resolved


def normalize_request(
    project_root: Path,
    wiki_roots: Sequence[Path] = (),
    *,
    origin_kind: str = "manual",
    origin_id: str = "manual",
    triggers: Sequence[str] = ("manual",),
    attempt: int = 1,
) -> dict[str, Any]:
    """Return the strict, deterministic request document used to mint operation identity."""

    project = _canonical_directory(project_root, label="project_root")
    if not isinstance(origin_kind, str) or not origin_kind:
        raise SyncFailure("broken-binding", "origin kind must be a non-empty string")
    if not isinstance(origin_id, str) or not origin_id:
        raise SyncFailure("broken-binding", "origin identifier must be a non-empty string")
    if isinstance(triggers, (str, bytes)) or not all(
        isinstance(trigger, str) and trigger for trigger in triggers
    ):
        raise SyncFailure("broken-binding", "triggers must be non-empty strings")
    normalized_triggers = sorted(set(triggers))
    if not normalized_triggers:
        raise SyncFailure("broken-binding", "at least one trigger is required")
    if isinstance(wiki_roots, (str, bytes, os.PathLike)):
        raise SyncFailure("broken-binding", "wiki_roots must be a sequence of paths")
    normalized_roots: set[str] = set()
    for path in wiki_roots:
        raw = _path_value(path, label="wiki_root")
        try:
            normalized_roots.add(str(raw.expanduser().resolve()))
        except (OSError, RuntimeError) as error:
            raise SyncFailure(
                "broken-binding", f"wiki_root does not resolve: {raw}: {error}"
            ) from error
    if type(attempt) is not int or attempt < 1:
        raise SyncFailure("broken-binding", "attempt must be a positive integer")
    return {
        "contract_version": CONTRACT_VERSION,
        "project_root": str(project),
        "wiki_roots": sorted(normalized_roots),
        "origin": {"kind": origin_kind, "id": origin_id},
        "triggers": normalized_triggers,
        "attempt": attempt,
    }


def _wiki_sync_ref(
    request: Mapping[str, Any], *, wiki_identity: str | None, pre_sync_tree: str
) -> dict[str, Any]:
    identity = {
        "contract_version": CONTRACT_VERSION,
        "project_root": request["project_root"],
        "wiki_identity": wiki_identity,
        "origin": request["origin"],
        "pre_sync_tree_sha256": pre_sync_tree,
        "triggers": request["triggers"],
    }
    return {**identity, "digest": _sha256(identity)}


def _candidate_ref(
    wiki_sync_ref: Mapping[str, Any], *, before: str, after: str
) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "profile": CONTRACT_VERSION,
        "base_tree_sha256": before,
        "candidate_tree_sha256": after,
        "wiki_sync_ref": wiki_sync_ref["digest"],
    }


def _result(
    request: Mapping[str, Any],
    *,
    status: str,
    reason: str,
    wiki_ref: Mapping[str, Any],
    wiki_identity: str | None = None,
    changed_paths: Sequence[str] = (),
    candidate_ref: Mapping[str, Any] | None = None,
    validation_receipt: Mapping[str, Any] | None = None,
    candidate_path: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    retryable = reason in RETRYABLE_REASONS
    return {
        "contract_version": CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "wiki_sync_ref": dict(wiki_ref),
        "wiki_identity": wiki_identity,
        "origin": request["origin"],
        "triggers": request["triggers"],
        "attempt": request["attempt"],
        "changed_paths": list(changed_paths),
        "candidate_ref": dict(candidate_ref) if candidate_ref else None,
        "candidate_path": candidate_path,
        "validation_receipt": dict(validation_receipt) if validation_receipt else None,
        "retry": {
            "disposition": "retryable" if retryable else "terminal",
            "max_attempts": 3 if retryable else 1,
        },
        "detail": detail,
    }


def _bounded_candidates(project_root: Path) -> list[Path]:
    candidates: list[Path] = []
    if config_path(project_root).is_file():
        candidates.append(project_root)
    for child in sorted(project_root.iterdir()):
        if child.is_dir() and config_path(child).is_file():
            candidates.append(child)
    return candidates


def _assert_compatible(root: Path, project_root: Path) -> dict[str, object]:
    try:
        document = read_binding(root)
        bound = Path(str(document["project_root"])).expanduser().resolve(strict=True)
    except (BindingError, OSError) as error:
        raise SyncFailure("broken-binding", str(error)) from error
    if bound != project_root:
        raise SyncFailure(
            "broken-binding",
            f"{config_path(root)} binds {bound}, expected {project_root}",
        )
    for relative in REQUIRED_WIKI_FILES:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise SyncFailure("broken-binding", f"compatible wiki file is missing: {path}")
        try:
            path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError) as error:
            raise SyncFailure(
                "broken-binding", f"wiki file is unreadable UTF-8: {path}"
            ) from error
    return document


def discover_wiki(
    request: Mapping[str, Any], *, observer: Observer | None = None
) -> tuple[Path | None, dict[str, object] | None]:
    """Resolve exactly zero or one compatible root without any unbounded search."""

    _observe(observer, "discover")
    project = Path(str(request["project_root"]))
    explicit = [Path(item) for item in request["wiki_roots"]]  # type: ignore[index]
    roots: dict[str, Path] = {}
    for raw in [*explicit, *_bounded_candidates(project)]:
        root = _canonical_directory(raw, label="wiki_root")
        roots[str(root)] = root
    compatible: list[tuple[Path, dict[str, object]]] = []
    for root in roots.values():
        compatible.append((root, _assert_compatible(root, project)))
    if not compatible:
        return None, None
    if len(compatible) > 1:
        names = ", ".join(str(item[0]) for item in compatible)
        raise SyncFailure("ambiguous-root", f"multiple compatible wiki roots: {names}")
    return compatible[0]


def _assert_generated_scope(root: Path, inventory: Mapping[str, Entry]) -> None:
    if (root / "wiki").is_symlink():
        raise SyncFailure("forbidden-scope", "generated wiki directory must not be a symlink")
    if not inventory:
        raise SyncFailure("forbidden-scope", "generated wiki corpus is empty")
    for relative, item in inventory.items():
        pure = PurePosixPath(relative)
        if (
            pure.is_absolute()
            or ".." in pure.parts
            or pure.parts[:1] != ("wiki",)
            or pure.suffix.lower() != ".md"
        ):
            raise SyncFailure("forbidden-scope", f"path is outside wiki-sync-v1: {relative}")
        path = root / pure
        if item.kind != "file" or path.is_symlink() or not path.is_file():
            raise SyncFailure("forbidden-scope", f"generated path is not regular: {relative}")
        if item.mode & 0o111:
            raise SyncFailure("forbidden-scope", f"generated path is executable: {relative}")
        try:
            path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError) as error:
            raise SyncFailure(
                "forbidden-scope", f"generated path is not UTF-8: {relative}"
            ) from error


def _assert_complete_diff(
    before_root: Path,
    after_root: Path,
    before_all: Mapping[str, Entry],
    after_all: Mapping[str, Entry],
) -> list[str]:
    changed = _changed_paths(before_all, after_all)
    for relative in changed:
        pure = PurePosixPath(relative)
        if pure.parts[:1] != ("wiki",) or pure.suffix.lower() != ".md":
            raise SyncFailure(
                "forbidden-scope", f"staged diff contains a forbidden path: {relative}"
            )
    _assert_generated_scope(before_root, _generated_inventory(before_root))
    _assert_generated_scope(after_root, _generated_inventory(after_root))
    return changed


def _append_log(root: Path, changed_count: int, *, now: datetime | None = None) -> None:
    log = root / "wiki" / "log.md"
    lines = log.read_text(encoding="utf-8").splitlines()
    if now is None:
        first_date = next(
            (line[3:] for line in lines if line.startswith("## ")),
            "1970-01-01",
        )
        first_clock = next(
            (
                line[2:7]
                for line in lines
                if line.startswith("- ") and len(line) >= 7
            ),
            "00:00",
        )
        try:
            now = datetime.combine(
                datetime.fromisoformat(first_date).date(),
                time.fromisoformat(first_clock),
            ) + timedelta(minutes=1)
        except ValueError:
            now = datetime(1970, 1, 1)
    stamp = now
    date_heading = f"## {stamp.date().isoformat()}"
    entry = (
        f"- {stamp.strftime('%H:%M')} sync-project — "
        f"compiled {changed_count} generated path(s)"
    )
    try:
        heading = lines.index(date_heading)
    except ValueError:
        first_date = next(
            (i for i, line in enumerate(lines) if line.startswith("## ")), len(lines)
        )
        lines[first_date:first_date] = [date_heading, "", entry, ""]
    else:
        insertion = heading + 1
        while insertion < len(lines) and not lines[insertion].startswith("- "):
            if lines[insertion].startswith("## "):
                break
            insertion += 1
        lines.insert(insertion, entry)
    log.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _lint_receipt(
    stage: Path,
    *,
    candidate: Mapping[str, Any],
    changed_paths: Sequence[str],
) -> dict[str, Any]:
    results = run_passes(stage)
    lint = [
        {
            "pass": result.name,
            "severity": result.severity,
            "issues": len(result.issues),
        }
        for result in results
    ]
    errors = sum(
        len(result.issues) for result in results if result.severity == ERROR
    )
    if errors:
        failing = ", ".join(
            f"{result.name}={len(result.issues)}"
            for result in results
            if result.severity == ERROR and result.issues
        )
        raise SyncFailure("lint", f"full wiki lint found {errors} error(s): {failing}")
    evidence = {
        "schema": 1,
        "contract_version": CONTRACT_VERSION,
        "candidate_ref": dict(candidate),
        "changed_paths": list(changed_paths),
        "checks": [
            {"id": "complete-staged-diff", "result": "pass", "paths": len(changed_paths)},
            {"id": "path-file-kind-utf8", "result": "pass", "paths": len(changed_paths)},
            {"id": "llm-wiki-lint", "result": "pass", "passes": lint},
            {"id": "compare-and-swap", "result": "pending"},
        ],
        "claim_ceiling": CLAIM_CEILING,
        "limitations": [
            "Deterministic wiki checks do not establish provider or production behavior.",
            "Tracked-candidate delivery and merge are owned by a separate caller.",
        ],
    }
    return {**evidence, "sha256": _sha256(evidence)}


def _project_worktree_root(project_root: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def _source_state(
    project_root: Path, binding: Mapping[str, object]
) -> str:
    artefacts: list[dict[str, object]] = []
    found: set[Path] = set()
    for pattern in binding["docs_globs"]:  # type: ignore[union-attr]
        found.update(path for path in project_root.glob(str(pattern)) if path.is_file())
    for path in sorted(found):
        details = path.stat()
        artefacts.append(
            {
                "path": path.relative_to(project_root).as_posix(),
                "mode": stat.S_IMODE(details.st_mode),
                "sha256": _file_digest(path),
            }
        )
    head = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return _sha256(
        {
            "artefacts": artefacts,
            "git_head": head.stdout.strip() if head.returncode == 0 else None,
        }
    )


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _classify(root: Path, project_root: Path, binding: Mapping[str, object]) -> str:
    worktree = _project_worktree_root(project_root)
    internal_parent = worktree or project_root
    if not _is_within(root, internal_parent):
        return "external"
    if worktree is None or binding.get("git_mode") == "off":
        return "internal-untracked"
    generated = sorted(_generated_inventory(root))
    relative = [str((root / path).relative_to(worktree).as_posix()) for path in generated]
    wiki_subtree = (root / "wiki").relative_to(worktree).as_posix()
    result = subprocess.run(
        ["git", "-C", str(worktree), "ls-files", "-z", "--", wiki_subtree],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SyncFailure("broken-binding", "Git could not classify the internal wiki")
    tracked = {item.decode("utf-8", "strict") for item in result.stdout.split(b"\0") if item}
    count = sum(1 for item in relative if item in tracked)
    if count == 0:
        return "internal-untracked"
    if count == len(relative):
        return "internal-tracked"
    raise SyncFailure(
        "partial-tracking",
        f"internal generated corpus is partially tracked ({count}/{len(relative)})",
    )


@contextmanager
def _wiki_lock(root: Path) -> Iterator[None]:
    lock_root = Path(tempfile.gettempdir()) / "llm-wiki-sync-locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    lock = lock_root / f"{hashlib.sha256(str(root).encode('utf-8')).hexdigest()}.lock"
    handle = lock.open("a+b")
    acquired = False
    try:
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except (BlockingIOError, OSError) as error:
            raise SyncFailure(
                "concurrent-operation", f"wiki sync is already active: {root}"
            ) from error
        yield
    finally:
        if acquired:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _apply_generated(
    stage: Path,
    protected: Path,
    changed_paths: Sequence[str],
    *,
    expected_tree: str,
) -> None:
    backups: dict[str, tuple[bytes, int] | None] = {}
    try:
        for relative in changed_paths:
            target = protected / PurePosixPath(relative)
            source = stage / PurePosixPath(relative)
            backups[relative] = (
                (target.read_bytes(), stat.S_IMODE(target.stat().st_mode))
                if target.is_file() and not target.is_symlink()
                else None
            )
            if not source.exists():
                target.unlink(missing_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.", dir=target.parent
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(source.read_bytes())
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(temporary_name, stat.S_IMODE(source.stat().st_mode))
                os.replace(temporary_name, target)
            finally:
                try:
                    os.unlink(temporary_name)
                except FileNotFoundError:
                    pass
        if _tree_digest(_generated_inventory(protected)) != expected_tree:
            raise SyncFailure(
                "stale-tree", "published generated tree differs from the frozen candidate"
            )
    except Exception:
        for relative, backup in reversed(list(backups.items())):
            target = protected / PurePosixPath(relative)
            if backup is None:
                target.unlink(missing_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(backup[0])
                target.chmod(backup[1])
        raise


def _git_common_dir(project_root: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise SyncFailure("broken-binding", "tracked wiki has no Git common directory")
    common = Path(result.stdout.strip())
    return (project_root / common).resolve() if not common.is_absolute() else common.resolve()


def _freeze_candidate(
    stage: Path,
    project_root: Path,
    candidate: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> Path:
    destination = (
        _git_common_dir(project_root)
        / "llm-wiki"
        / "candidates"
        / str(candidate["wiki_sync_ref"])
        / str(candidate["candidate_tree_sha256"])
    )
    manifest = {"candidate_ref": dict(candidate), "validation_receipt": dict(receipt)}
    if destination.exists():
        existing = destination / "manifest.json"
        if not existing.is_file() or existing.read_bytes() != _canonical_bytes(manifest):
            raise SyncFailure("stale-tree", "content-addressed candidate storage is contradictory")
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".wiki-sync-", dir=destination.parent))
    try:
        for relative, entry in _generated_inventory(stage).items():
            if entry.kind != "file":
                raise SyncFailure("forbidden-scope", f"cannot freeze non-file {relative}")
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(stage / relative, target)
            target.chmod(entry.mode)
        (temporary / "manifest.json").write_bytes(_canonical_bytes(manifest))
        if _tree_digest(_generated_inventory(temporary)) != candidate["candidate_tree_sha256"]:
            raise SyncFailure(
                "stale-tree", "frozen files differ from the validated candidate tree"
            )
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return destination


def sync_project(
    project_root: Path,
    wiki_roots: Sequence[Path] = (),
    *,
    origin_kind: str = "manual",
    origin_id: str = "manual",
    triggers: Sequence[str] = ("manual",),
    attempt: int = 1,
    autopilot_root: Path | None = None,
    observer: Observer | None = None,
    before_publish: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Run one normalized sync operation; policy failures are returned, never raised."""

    try:
        request = normalize_request(
            project_root,
            wiki_roots,
            origin_kind=origin_kind,
            origin_id=origin_id,
            triggers=triggers,
            attempt=attempt,
        )
    except SyncFailure as failure:
        safe_roots = (
            [str(path) for path in wiki_roots]
            if isinstance(wiki_roots, Sequence)
            and not isinstance(wiki_roots, (str, bytes))
            else []
        )
        safe_triggers = (
            sorted(
                {
                    trigger
                    for trigger in triggers
                    if isinstance(trigger, str) and trigger
                }
            )
            if isinstance(triggers, Sequence)
            and not isinstance(triggers, (str, bytes))
            else []
        )
        fallback = {
            "contract_version": CONTRACT_VERSION,
            "project_root": str(project_root),
            "wiki_roots": safe_roots,
            "origin": {
                "kind": origin_kind if isinstance(origin_kind, str) and origin_kind else "invalid",
                "id": origin_id if isinstance(origin_id, str) and origin_id else "invalid",
            },
            "triggers": safe_triggers or ["manual"],
            "attempt": attempt if type(attempt) is int and attempt > 0 else 1,
        }
        ref = _wiki_sync_ref(fallback, wiki_identity=None, pre_sync_tree="unknown")
        return _result(
            fallback,
            status="failed",
            reason=failure.reason,
            wiki_ref=ref,
            detail=failure.detail,
        )

    wiki_identity: str | None = None
    pre_digest = "absent"
    wiki_ref = _wiki_sync_ref(request, wiki_identity=None, pre_sync_tree=pre_digest)
    known_changed: list[str] = []
    known_candidate: dict[str, Any] | None = None
    known_receipt: dict[str, Any] | None = None
    try:
        root, binding = discover_wiki(request, observer=observer)
        if root is None or binding is None:
            return _result(
                request,
                status="skipped",
                reason="absent",
                wiki_ref=wiki_ref,
            )
        wiki_identity = str(root)
        before_generated = _generated_inventory(root)
        pre_digest = _tree_digest(before_generated)
        wiki_ref = _wiki_sync_ref(
            request, wiki_identity=wiki_identity, pre_sync_tree=pre_digest
        )
        with _wiki_lock(root):
            project = Path(str(request["project_root"]))
            binding = _assert_compatible(root, project)
            before_generated = _generated_inventory(root)
            _assert_generated_scope(root, before_generated)
            pre_digest = _tree_digest(before_generated)
            wiki_ref = _wiki_sync_ref(
                request, wiki_identity=wiki_identity, pre_sync_tree=pre_digest
            )
            if binding["auto_sync"] == "disabled":
                return _result(
                    request,
                    status="skipped",
                    reason="disabled",
                    wiki_ref=wiki_ref,
                    wiki_identity=wiki_identity,
                )
            classification = _classify(root, project, binding)
            pre_managed_digest = _tree_digest(_managed_inventory(root))
            source_state = _source_state(project, binding)
            with tempfile.TemporaryDirectory(prefix="llm-wiki-sync-") as temporary:
                stage = Path(temporary) / "wiki-root"
                _stage_copy(root, stage)
                _observe(observer, "stage")
                before_all = _managed_inventory(stage)
                _observe(observer, "ingest")
                ingest_report = ingest_docs(
                    stage, autopilot_root or default_autopilot_root()
                )
                _observe(observer, "timeline")
                timeline_report = build_timeline(stage)
                compiled_all = _managed_inventory(stage)
                initial_changes = _changed_paths(before_all, compiled_all)
                if initial_changes:
                    _append_log(stage, len(initial_changes))
                after_all = _managed_inventory(stage)
                _observe(observer, "scope")
                known_changed = _changed_paths(_managed_inventory(root), after_all)
                changed = _assert_complete_diff(
                    root, stage, _managed_inventory(root), after_all
                )
                after_generated = _generated_inventory(stage)
                post_digest = _tree_digest(after_generated)
                candidate = _candidate_ref(
                    wiki_ref, before=pre_digest, after=post_digest
                )
                known_candidate = candidate
                _observe(observer, "lint")
                receipt = _lint_receipt(
                    stage, candidate=candidate, changed_paths=changed
                )
                receipt["compile"] = {
                    "ingest": ingest_report,
                    "timeline": timeline_report,
                }
                receipt_without_hash = {
                    key: value for key, value in receipt.items() if key != "sha256"
                }
                receipt["sha256"] = _sha256(receipt_without_hash)
                known_receipt = receipt
                if before_publish is not None:
                    before_publish()
                _observe(observer, "compare-and-swap")
                try:
                    publish_classification = _classify(root, project, binding)
                except SyncFailure as failure:
                    raise SyncFailure(
                        "stale-tree",
                        f"wiki tracking changed during sync: {failure.detail}",
                    ) from failure
                if (
                    _tree_digest(_managed_inventory(root)) != pre_managed_digest
                    or _source_state(project, binding) != source_state
                    or publish_classification != classification
                ):
                    raise SyncFailure(
                        "stale-tree", "protected wiki or project corpus changed during sync"
                    )
                receipt["checks"][-1]["result"] = "pass"  # type: ignore[index]
                receipt_without_hash = {
                    key: value for key, value in receipt.items() if key != "sha256"
                }
                receipt["sha256"] = _sha256(receipt_without_hash)
                if not changed:
                    return _result(
                        request,
                        status="unchanged",
                        reason="no-diff",
                        wiki_ref=wiki_ref,
                        wiki_identity=wiki_identity,
                        candidate_ref=candidate,
                        validation_receipt=receipt,
                    )
                _observe(observer, "publish")
                if classification == "internal-tracked":
                    frozen = _freeze_candidate(
                        stage,
                        Path(str(request["project_root"])),
                        candidate,
                        receipt,
                    )
                    return _result(
                        request,
                        status="candidate-created",
                        reason="manual-authorization",
                        wiki_ref=wiki_ref,
                        wiki_identity=wiki_identity,
                        changed_paths=changed,
                        candidate_ref=candidate,
                        validation_receipt=receipt,
                        candidate_path=str(frozen),
                    )
                _apply_generated(
                    stage,
                    root,
                    changed,
                    expected_tree=post_digest,
                )
                return _result(
                    request,
                    status="updated-directly",
                    reason=("external" if classification == "external" else "internal-untracked"),
                    wiki_ref=wiki_ref,
                    wiki_identity=wiki_identity,
                    changed_paths=changed,
                    candidate_ref=candidate,
                    validation_receipt=receipt,
                )
    except SyncFailure as failure:
        return _result(
            request,
            status="failed",
            reason=failure.reason,
            wiki_ref=wiki_ref,
            wiki_identity=wiki_identity,
            changed_paths=known_changed,
            candidate_ref=known_candidate,
            validation_receipt=known_receipt,
            detail=failure.detail,
        )
    except (BindingError, TicketParserError, OSError, UnicodeError, ValueError) as error:
        return _result(
            request,
            status="failed",
            reason="compile",
            wiki_ref=wiki_ref,
            wiki_identity=wiki_identity,
            changed_paths=known_changed,
            candidate_ref=known_candidate,
            validation_receipt=known_receipt,
            detail=str(error),
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--wiki-root", action="append", type=Path, default=[])
    parser.add_argument("--origin-kind", default="manual")
    parser.add_argument("--origin-id", default="manual")
    parser.add_argument("--trigger", action="append", default=[])
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--autopilot-root", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    report = sync_project(
        arguments.project_root,
        arguments.wiki_root,
        origin_kind=arguments.origin_kind,
        origin_id=arguments.origin_id,
        triggers=arguments.trigger or ["manual"],
        attempt=arguments.attempt,
        autopilot_root=arguments.autopilot_root,
    )
    if arguments.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"status  {report['status']}")
        print(f"reason  {report['reason']}")
        if report["wiki_identity"]:
            print(f"wiki    {report['wiki_identity']}")
        print(f"changed {len(report['changed_paths'])}")
        if report["detail"]:
            print(f"detail  {report['detail']}")
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
