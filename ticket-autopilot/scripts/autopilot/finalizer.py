from __future__ import annotations

import ctypes
import copy
import errno
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from .docs_only import DocsOnlyError, revalidate_docs_only_receipt
from .final_tree_projection import (
    FinalTreeProjectionError,
    NON_AUTHORITY,
    ProjectionExcluded,
    compare_projection,
    comparison_failure,
    excluded_observation,
    plan_tracked_completion,
    validate_manifest,
    validate_projection_config,
)
from .git_ops import (
    CommandRunner,
    GitError,
    SubprocessCommandRunner,
    candidate_ref,
    repository_root,
    run_git,
)
from .kernel import Kernel, TransitionError
from .link_repoint import repoint_moved_file
from .ledger import (
    AtomicLedger,
    completion_projection_destination,
    completion_projection_grant_matches_ticket,
)
from .pr_body_artifact import (
    CANONICAL_BODY_ENCODING,
    PrBodyArtifactError,
    canonical_markdown,
    persist_pr_body,
    read_pr_body,
)
from .providers import (
    CREATE_OR_UPDATE_PR,
    ProviderExecutor,
    build_delivery_plan,
)
from .ticket_contract import ticket_source_digest
from .verification_checkpoint import (
    VerificationCheckpointError,
    load_pr_body_validator,
)


class DeliveryBodyError(RuntimeError):
    """A rendered or observed PR body cannot support delivery progress."""

    def __init__(self, phase: str, detail: str):
        self.phase = phase
        super().__init__(detail)


class SourceDriftError(GitError):
    """An ignored caller-owned ticket no longer matches its snapshot."""


class CompletionProjectionError(GitError):
    """An explicit tracked completion projection is not exact and bounded."""


class SourceModeDriftError(SourceDriftError):
    """A frozen ticket source mode differs from the delivery checkout."""

    def __init__(self, details: dict[str, Any]):
        self.details = copy.deepcopy(details)
        super().__init__(
            "source-mode-drift "
            f"ticket={details['ticket_id']} "
            f"snapshot={details['snapshot_classification']} "
            f"observed={details['observed_classification']} "
            f"base={details['base_classification']} "
            f"boundary={details['boundary']} "
            f"path={details['source_path']}; "
            f"recovery={details['recovery']}"
        )


SOURCE_MODE_DRIFT_RECOVERY = (
    "publish the source tracking change separately, then start a new run "
    "from a base where the ticket folder is tracked"
)


def _git_path_listing(repo: Path, *arguments: str) -> set[str]:
    return {
        item
        for item in run_git(repo, *arguments).split("\0")
        if item
    }


def _git_path_is_ignored(repo: Path, path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", "--", path],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise GitError(
            "git check-ignore failed: "
            f"{result.stderr.strip() or 'unknown Git error'}"
        )
    return result.returncode == 0


def _ticket_git_paths(
    kernel: Kernel, ticket_id: str, worktree: Path
) -> tuple[str, tuple[str, ...]]:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if ticket is None:
        raise TransitionError(f"unknown ticket {ticket_id!r}")
    repo = Path(kernel.ledger["repo"]).resolve()
    folder = Path(kernel.ledger["ticket_folder"]).resolve()
    try:
        folder_relative = folder.relative_to(repo)
    except ValueError as error:
        raise GitError("ticket source folder is outside its bound repository") from error
    current = Path(ticket["current_source_relative_path"])
    original = Path(ticket["source_relative_path"])
    for relative in (current, original):
        if relative.is_absolute() or ".." in relative.parts:
            raise TransitionError("ticket source path escapes its accepted folder")
    destination = Path("done") / original.name
    paths = tuple(
        dict.fromkeys(
            (folder_relative / relative).as_posix()
            for relative in (current, original, destination)
        )
    )
    return (folder_relative / current).as_posix(), paths


def _classify_checkout_paths(
    worktree: Path,
    current_path: str,
    paths: tuple[str, ...],
    *,
    treeish: str | None,
) -> tuple[str, str]:
    tracked_paths = (
        _git_path_listing(worktree, "ls-files", "-z", "--", *paths)
        if treeish is None
        else _git_path_listing(
            worktree,
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            treeish,
            "--",
            *paths,
        )
    )
    for path in paths:
        if path in tracked_paths:
            return "tracked", path
    if _git_path_is_ignored(worktree, current_path):
        return "ignored", current_path
    return "untracked", current_path


def _index_entries(worktree: Path, paths: tuple[str, ...]) -> dict[str, tuple[str, str]]:
    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z", "--", *paths],
        cwd=worktree,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise CompletionProjectionError(
            "completion projection index inspection failed: "
            + result.stderr.decode("utf-8", errors="replace").strip()
        )
    entries: dict[str, tuple[str, str]] = {}
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, separator, raw_path = raw.partition(b"\t")
        fields = metadata.decode("ascii", errors="strict").split()
        if not separator or len(fields) != 3 or fields[2] != "0":
            raise CompletionProjectionError(
                "completion projection index entry is malformed or unmerged"
            )
        path = raw_path.decode("utf-8", errors="strict")
        if path in entries:
            raise CompletionProjectionError(
                "completion projection index contains duplicate paths"
            )
        entries[path] = (fields[0], fields[1])
    return entries


def _index_blob_digest(worktree: Path, oid: str) -> str:
    result = subprocess.run(
        ["git", "cat-file", "blob", oid],
        cwd=worktree,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise CompletionProjectionError(
            "completion projection blob inspection failed"
        )
    try:
        text = result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise CompletionProjectionError(
            "completion projection blob must be UTF-8 text"
        ) from error
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def inspect_completion_projection(
    kernel: Kernel,
    ticket_id: str,
    *,
    expected_tree_oid: str,
    base_ref: str,
) -> dict[str, str]:
    """Validate and describe one candidate-only exact ignored-source projection."""

    if kernel.ledger.get("ticket_source_mode") != "ignored":
        raise CompletionProjectionError(
            "completion projection requires an ignored ticket source"
        )
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if not isinstance(ticket, dict) or not isinstance(ticket.get("candidate_ref"), dict):
        raise CompletionProjectionError(
            "completion projection requires a frozen CandidateRef"
        )
    candidate = ticket["candidate_ref"]
    if candidate.get("candidate_tree_oid") != expected_tree_oid:
        raise CompletionProjectionError(
            "completion projection expected tree differs from CandidateRef"
        )
    worktree = Path(kernel.ledger["worktree"]).resolve()
    if repository_root(worktree) != worktree:
        raise CompletionProjectionError(
            "completion projection worktree is not an isolated Git root"
        )
    if run_git(worktree, "write-tree") != expected_tree_oid:
        raise CompletionProjectionError(
            "completion projection index differs from CandidateRef"
        )
    current_path, paths = _ticket_git_paths(kernel, ticket_id, worktree)
    destination = completion_projection_destination(kernel.ledger, ticket_id)
    if destination is None:
        raise CompletionProjectionError(
            "completion projection destination is outside its repository"
        )
    entries = _index_entries(worktree, paths)
    if set(entries) != {destination}:
        raise CompletionProjectionError(
            "completion projection must track only the canonical done destination"
        )
    mode, oid = entries[destination]
    if mode != "100644":
        raise CompletionProjectionError(
            "completion projection destination must be a regular non-executable file"
        )
    expected_digest = ticket["ticket_digest"]
    if candidate.get("ticket_digest") != expected_digest:
        raise CompletionProjectionError(
            "completion projection CandidateRef ticket digest is stale"
        )
    if _index_blob_digest(worktree, oid) != expected_digest:
        raise CompletionProjectionError(
            "completion projection destination digest differs from the managed snapshot"
        )
    base, _ = _classify_checkout_paths(
        worktree, current_path, paths, treeish=base_ref
    )
    if base != "ignored":
        raise CompletionProjectionError(
            "completion projection delivery base is not ignored"
        )
    _folder, source, final_destination, _summary = _ignored_ticket_paths(
        kernel, ticket_id
    )
    candidates = list(dict.fromkeys((source, final_destination)))
    existing = [path for path in candidates if path.exists()]
    if len(existing) != 1 or existing[0].is_symlink() or not existing[0].is_file():
        raise CompletionProjectionError(
            "completion projection caller-owned source is missing or contradictory"
        )
    if _file_digest(existing[0]) != expected_digest:
        raise CompletionProjectionError(
            "completion projection caller-owned source digest changed"
        )
    return {
        "destination_relative_path": destination,
        "candidate_tree_oid": expected_tree_oid,
        "base_tree_oid": candidate["base_tree_oid"],
        "ticket_digest": expected_digest,
    }


def _grant_allows_completion_projection(
    kernel: Kernel,
    ticket_id: str,
    *,
    base_ref: str,
) -> bool:
    ticket = kernel.ledger["tickets"][ticket_id]
    grant = ticket.get("completion_projection_grant")
    if not isinstance(grant, dict) or not completion_projection_grant_matches_ticket(
        kernel.ledger, ticket_id
    ):
        return False
    candidate = grant["candidate_ref"]
    projection_base = (
        candidate["base_tree_oid"] if base_ref == "HEAD" else base_ref
    )
    try:
        observed = inspect_completion_projection(
            kernel,
            ticket_id,
            expected_tree_oid=candidate["candidate_tree_oid"],
            base_ref=projection_base,
        )
    except (CompletionProjectionError, GitError, KeyError, TypeError, ValueError):
        return False
    return (
        ticket.get("candidate_ref") == candidate
        and observed["destination_relative_path"]
        == grant["destination_relative_path"]
    )


def assert_ticket_source_mode(
    kernel: Kernel,
    ticket_id: str,
    boundary: str,
    *,
    base_ref: str = "HEAD",
) -> None:
    """Fail closed when delivery ownership no longer matches the run snapshot."""

    worktree = Path(kernel.ledger["worktree"]).resolve()
    if repository_root(worktree) != worktree:
        raise GitError("ledger worktree is not an isolated Git root")
    expected = kernel.ledger["ticket_source_mode"]
    current_path, paths = _ticket_git_paths(kernel, ticket_id, worktree)
    observed, observed_path = _classify_checkout_paths(
        worktree, current_path, paths, treeish=None
    )
    base, base_path = _classify_checkout_paths(
        worktree, current_path, paths, treeish=base_ref
    )
    if observed == expected and base == expected:
        return
    if (
        expected == "ignored"
        and observed == "tracked"
        and _grant_allows_completion_projection(
            kernel, ticket_id, base_ref=base_ref
        )
    ):
        return
    if observed == expected:
        observed = base
        observed_path = base_path
    raise SourceModeDriftError(
        {
            "schema": 1,
            "ticket_id": ticket_id,
            "snapshot_classification": expected,
            "observed_classification": observed,
            "base_classification": base,
            "boundary": boundary,
            "source_path": observed_path,
            "recovery": SOURCE_MODE_DRIFT_RECOVERY,
        }
    )


def _completion_summary(kernel: Kernel, ticket_id: str) -> dict[str, Any]:
    ticket = kernel.ledger["tickets"][ticket_id]
    return {
        "schema": 1,
        "run_id": kernel.ledger["run_id"],
        "ticket_id": ticket_id,
        "implementation_status": "complete",
        "candidate_ref": ticket["candidate_ref"],
        "ticket_source_mode": kernel.ledger["ticket_source_mode"],
        "snapshot_manifest_digest": kernel.ledger["snapshot_manifest_digest"],
    }


def _summary_content(document: dict[str, Any]) -> str:
    return (
        json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    )


def _write_atomic_summary(path: Path, document: dict[str, Any]) -> None:
    content = _summary_content(document)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="utf-8") != content:
            raise SourceDriftError("completion summary content is contradictory")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_tmp = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_tmp)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            _rename_no_replace(temporary, path)
        except FileExistsError as error:
            raise SourceDriftError(
                "completion summary destination appeared concurrently"
            ) from error
    finally:
        temporary.unlink(missing_ok=True)


def _rename_no_replace(source: Path, destination: Path) -> None:
    if os.name == "nt":
        os.rename(source, destination)
        return
    library = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform == "darwin":
        rename = library.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(source_bytes, destination_bytes, 0x00000004)
    elif sys.platform.startswith("linux") and hasattr(library, "renameat2"):
        rename = library.renameat2
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename.restype = ctypes.c_int
        result = rename(-100, source_bytes, -100, destination_bytes, 1)
    else:
        raise OSError(
            errno.ENOTSUP,
            "atomic no-clobber rename is unavailable on this platform",
            str(destination),
        )
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(error_number, os.strerror(error_number), destination)
    raise OSError(error_number, os.strerror(error_number), destination)


def _move_ignored_source(source: Path, destination: Path) -> None:
    try:
        _rename_no_replace(source, destination)
    except FileExistsError as error:
        raise SourceDriftError(
            "ignored destination appeared concurrently"
        ) from error


def _ticket_paths(kernel: Kernel, ticket_id: str, worktree: Path) -> tuple[Path, Path]:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if ticket is None:
        raise TransitionError(f"unknown ticket {ticket_id!r}")
    repo_value = kernel.ledger.get("repo")
    if not repo_value:
        raise TransitionError("ledger has no repository binding")
    original_repo = Path(repo_value).resolve()
    original_folder = Path(kernel.ledger["ticket_folder"]).resolve()
    try:
        folder_relative = original_folder.relative_to(original_repo)
    except ValueError as error:
        raise TransitionError("ticket folder is outside the bound repository") from error
    relative = Path(ticket["current_source_relative_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise TransitionError("current ticket path escapes its folder")
    folder = worktree.resolve() / folder_relative
    source = folder / relative
    destination = folder / "done" / relative.name
    return source, destination


def _ignored_ticket_paths(
    kernel: Kernel, ticket_id: str
) -> tuple[Path, Path, Path, Path]:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if ticket is None:
        raise TransitionError(f"unknown ticket {ticket_id!r}")
    repo = Path(kernel.ledger["repo"]).resolve()
    folder = Path(kernel.ledger["ticket_folder"])
    if not folder.is_absolute():
        raise SourceDriftError("ignored ticket folder must be absolute")
    try:
        folder_relative = folder.relative_to(repo)
    except ValueError as error:
        raise SourceDriftError("ignored ticket folder is outside the repository") from error
    current = repo
    for part in folder_relative.parts:
        current = current / part
        if current.is_symlink():
            raise SourceDriftError(
                f"ignored ticket folder path contains a symlink: {current}"
            )
    try:
        folder_stat = folder.stat(follow_symlinks=False)
    except OSError as error:
        raise SourceDriftError("ignored ticket folder is missing") from error
    observed_identity = {
        "device": folder_stat.st_dev,
        "inode": folder_stat.st_ino,
    }
    if observed_identity != kernel.ledger["ticket_source_folder_identity"]:
        raise SourceDriftError("ignored ticket folder identity changed after snapshot")
    relative = Path(ticket["current_source_relative_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise SourceDriftError("ignored ticket path is outside the accepted folder")
    source = folder / relative
    destination = folder / "done" / relative.name
    summary = destination.with_suffix(".completion.json")
    for path in (source, destination, summary):
        try:
            path.resolve(strict=False).relative_to(folder)
        except ValueError as error:
            raise SourceDriftError("ignored finalization path escapes its folder") from error
    if source.is_symlink() or destination.is_symlink() or summary.is_symlink():
        raise SourceDriftError("ignored finalization rejects symlink paths")
    if destination.parent.exists() and destination.parent.is_symlink():
        raise SourceDriftError("ignored done folder cannot be a symlink")
    return folder, source, destination, summary


def _file_digest(path: Path) -> str:
    return ticket_source_digest(path)


def _finalize_ignored(
    store: AtomicLedger, kernel: Kernel, ticket_id: str
) -> bool:
    ticket = kernel.ledger["tickets"][ticket_id]
    folder, source, destination, summary = _ignored_ticket_paths(kernel, ticket_id)
    expected_digest = ticket["ticket_digest"]
    summary_document = _completion_summary(kernel, ticket_id)
    summary_digest = hashlib.sha256(
        _summary_content(summary_document).encode("utf-8")
    ).hexdigest()
    intent = {
        "source_relative_path": source.relative_to(folder).as_posix(),
        "destination_relative_path": destination.relative_to(folder).as_posix(),
        "summary_relative_path": summary.relative_to(folder).as_posix(),
        "ticket_digest": expected_digest,
        "summary_digest": summary_digest,
    }
    recorded_intent = ticket["delivery"].get("ignored-finalization-intent")
    if recorded_intent is None:
        kernel.record_delivery_metadata(
            ticket_id, "ignored-finalization-intent", intent
        )
        store.save(kernel.ledger)
    elif recorded_intent != intent:
        raise SourceDriftError("ignored finalization intent is contradictory")

    source_exists = source.exists()
    destination_exists = destination.exists()
    if source_exists and destination_exists:
        raise SourceDriftError(
            "both source and destination exist during ignored finalization"
        )
    if not source_exists and not destination_exists:
        raise SourceDriftError(
            "ignored ticket is missing from both source and destination"
        )
    if not source_exists and destination_exists and recorded_intent is None:
        raise SourceDriftError(
            "ignored source is missing and destination predates finalization intent"
        )
    observed = source if source_exists else destination
    if not observed.is_file() or _file_digest(observed) != expected_digest:
        raise SourceDriftError("ignored ticket content digest changed after snapshot")
    if source_exists:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.parent.is_symlink():
            raise SourceDriftError("ignored done folder cannot be a symlink")
        _move_ignored_source(source, destination)
    if not destination.is_file() or _file_digest(destination) != expected_digest:
        raise SourceDriftError("ignored destination digest differs from snapshot")
    _write_atomic_summary(summary, summary_document)
    applied = {
        **intent,
        "state": "applied",
    }
    existing_applied = ticket["delivery"].get("ignored-finalization-applied")
    if existing_applied is not None and existing_applied != applied:
        raise SourceDriftError("ignored finalization applied receipt is contradictory")
    if existing_applied is None:
        kernel.record_delivery_metadata(
            ticket_id, "ignored-finalization-applied", applied
        )
        store.save(kernel.ledger)
    changed = kernel.record_finalization_effect(
        ticket_id, "move-done-and-summarize-external"
    )
    store.save(kernel.ledger)
    return changed


def finalize_done(
    store: AtomicLedger, kernel: Kernel, ticket_id: str
) -> bool:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if ticket is None or ticket["state"] not in {"verified", "pr-open", "integrated"}:
        raise TransitionError("done/ finalization requires a validated terminal result")
    assert_ticket_source_mode(kernel, ticket_id, "source-finalization")
    if kernel.ledger["ticket_source_mode"] == "ignored":
        return _finalize_ignored(store, kernel, ticket_id)
    worktree = Path(kernel.ledger["worktree"]).resolve()
    if repository_root(worktree) != worktree:
        raise GitError("ledger worktree is not an isolated Git root")
    source, destination = _ticket_paths(kernel, ticket_id, worktree)
    effect = "move-done-and-stage"

    already_recorded = any(
        item["ticket_id"] == ticket_id and item["effect"] == effect
        for item in kernel.ledger["effects"].values()
    )
    if already_recorded:
        if (source != destination and source.exists()) or not destination.exists():
            raise TransitionError("finalization ledger and worktree disagree")
        return False

    if source.exists() and destination.exists():
        raise TransitionError("both pending and done ticket paths exist")
    if not source.exists() and not destination.exists():
        raise TransitionError("ticket is absent from pending and done paths")
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, destination)

    relative_source = source.relative_to(worktree)
    relative_destination = destination.relative_to(worktree)
    # The documents linking the old path go stale in the same instant the file moves, and the
    # delivery candidate is recomputed after this function mutates the tree — so the repoint
    # rides the same commit as the move. The ticket itself is digest-frozen and untouched.
    repointed = repoint_moved_file(
        worktree,
        relative_source.as_posix(),
        relative_destination.as_posix(),
    )
    run_git(
        worktree,
        "add",
        "-A",
        "--",
        str(relative_source),
        str(relative_destination),
        *repointed,
    )
    changed = kernel.record_finalization_effect(ticket_id, effect)
    store.save(kernel.ledger)
    return changed


class DeliveryFinalizer:
    def __init__(
        self,
        store: AtomicLedger,
        kernel: Kernel,
        executor: ProviderExecutor,
        runner: CommandRunner | None = None,
        boundary_guard: Callable[[str, str], None] | None = None,
    ):
        self.store = store
        self.kernel = kernel
        self.executor = executor
        self.provider = executor.provider
        self.runner = runner or SubprocessCommandRunner()
        self.boundary_guard = boundary_guard
        self._active_ticket_id: str | None = None
        self.worktree = Path(kernel.ledger["worktree"]).resolve()

    def _provider_execute(
        self, ticket_id: str, operation: str, **parameters: Any
    ) -> dict[str, Any]:
        if self.boundary_guard is None:
            return self.executor.execute(operation, **parameters)
        delegate = self.executor.runner
        boundary_guard = self.boundary_guard

        class GuardedRunner:
            def run(self, command: list[str], *, cwd: Path):
                boundary_guard(ticket_id, f"provider-command:{operation}")
                return delegate.run(command, cwd=cwd)

        self.executor.runner = GuardedRunner()
        try:
            boundary_guard(ticket_id, f"provider:{operation}")
            return self.executor.execute(operation, **parameters)
        finally:
            self.executor.runner = delegate

    def _run(self, *command: str, allow_failure: bool = False) -> str:
        if self.boundary_guard is not None and self._active_ticket_id is not None:
            operation = command[1] if len(command) > 1 else command[0]
            self.boundary_guard(self._active_ticket_id, f"git:{operation}")
        result = self.runner.run(list(command), cwd=self.worktree)
        if result.returncode and not allow_failure:
            raise GitError(
                f"{' '.join(command)} failed: {result.stderr or result.stdout}"
            )
        return result.stdout

    def _effect_applied(self, ticket_id: str, effect: str) -> bool:
        return any(
            item["ticket_id"] == ticket_id and item["effect"] == effect
            for item in self.kernel.ledger["effects"].values()
        )

    def _record_effect(self, ticket_id: str, effect: str) -> None:
        self.kernel.record_finalization_effect(ticket_id, effect)
        self.store.save(self.kernel.ledger)

    @staticmethod
    def _atomic_summary(path: Path, document: dict[str, Any]) -> None:
        _write_atomic_summary(path, document)

    @staticmethod
    def _atomic_text(path: Path, content: bytes) -> None:
        try:
            persist_pr_body(path, content)
        except PrBodyArtifactError as error:
            raise DeliveryBodyError("render-persistence", str(error)) from error

    @staticmethod
    def _canonical_digest(value: Any) -> str:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _render_request(
        self,
        ticket_id: str,
        *,
        branch: str,
        base_branch: str,
        head: str,
        metadata_step: str = "pr-body-request",
        reconciled_from_head: str | None = None,
    ) -> dict[str, Any]:
        ticket = self.kernel.ledger["tickets"][ticket_id]
        bundle, bundle_ref = self._verification_bundle_from_handoff(
            ticket_id, phase="render-request"
        )
        changed_paths = [
            item
            for item in self._run(
                "git",
                "diff",
                "--name-only",
                ticket["candidate_ref"]["base_tree_oid"],
                ticket["candidate_ref"]["candidate_tree_oid"],
            ).splitlines()
            if item
        ]
        payload = {
            "schema": 1,
            "ticket_id": ticket_id,
            "ticket": {
                "ticket_id": ticket_id,
                "ticket_digest": ticket["ticket_digest"],
                "execution_mode": ticket["execution_mode"],
                "blocked_by": list(ticket["blocked_by"]),
            },
            "candidate_ref": ticket["candidate_ref"],
            "artifact_generation": ticket["artifact_generation"],
            "expected_head_sha": head,
            "branch": branch,
            "base": base_branch,
            "diff_facts": {"changed_paths": changed_paths},
            "verification_bundle": bundle_ref,
        }
        if reconciled_from_head is not None:
            payload["bundle_sha256"] = self._canonical_digest(bundle)
            payload["reconciled_from_head"] = reconciled_from_head
            payload["required_head_literal"] = head
        request = {**payload, "request_hash": self._canonical_digest(payload)}
        existing = ticket["delivery"].get(metadata_step)
        if existing is None:
            self.kernel.record_delivery_metadata(
                ticket_id, metadata_step, request
            )
            self.store.save(self.kernel.ledger)
        elif existing != request:
            legacy_payload = {
                key: value
                for key, value in payload.items()
                if key != "bundle_sha256"
            }
            legacy_request = {
                **legacy_payload,
                "request_hash": self._canonical_digest(legacy_payload),
            }
            if existing != legacy_request:
                raise DeliveryBodyError(
                    "render-request",
                    "persisted PR-body render request contradicts delivery head",
                )
            self.kernel.record_delivery_metadata(
                ticket_id, metadata_step, request
            )
            self.store.save(self.kernel.ledger)
        return request

    def _verification_bundle_from_handoff(
        self,
        ticket_id: str,
        *,
        phase: str,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        ticket = self.kernel.ledger["tickets"][ticket_id]
        evidence = (
            ticket.get("leaf_results", {})
            .get("verify", {})
            .get("quality", {})
            .get("evidence", [])
        )
        by_id = {item.get("id"): item for item in evidence}
        bundle_reference = by_id.get("verification-checkpoint:bundle-validated")
        handoff_reference = by_id.get("verification-checkpoint:handoff-ready")
        if not isinstance(bundle_reference, dict) or not isinstance(
            handoff_reference, dict
        ):
            raise DeliveryBodyError(
                phase,
                "verify handoff requires bundle-validated and handoff-ready artifacts",
            )

        def load_artifact(reference: dict[str, Any], expected_phase: str) -> tuple[Path, dict[str, Any], str]:
            path = Path(reference["artifact"]).resolve()
            path.relative_to(self.store.path.parent.resolve())
            document = json.loads(path.read_text(encoding="utf-8"))
            recorded_hash = document["artifact_hash"]
            payload = {
                key: value
                for key, value in document.items()
                if key != "artifact_hash"
            }
            if (
                recorded_hash != reference["sha256"]
                or self._canonical_digest(payload) != recorded_hash
                or document.get("phase") != expected_phase
                or document.get("candidate_ref") != ticket["candidate_ref"]
                or not isinstance(document.get("value"), dict)
            ):
                raise DeliveryBodyError(
                    phase, f"verification {expected_phase} artifact is invalid"
                )
            return path, document, recorded_hash

        try:
            bundle_path, bundle_document, bundle_hash = load_artifact(
                bundle_reference, "bundle-validated"
            )
            _handoff_path, _handoff_document, handoff_hash = load_artifact(
                handoff_reference, "handoff-ready"
            )
        except DeliveryBodyError:
            raise
        except (KeyError, OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            raise DeliveryBodyError(
                phase, f"verification handoff bundle is unreadable: {error}"
            ) from error
        return bundle_document["value"], {
            "artifact": str(bundle_path),
            "sha256": bundle_hash,
            "handoff_sha256": handoff_hash,
        }

    def _accept_render_payload(
        self,
        ticket_id: str,
        request: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        record = self._validated_render_record(ticket_id, request, payload)
        self.kernel.record_delivery_metadata(ticket_id, "pr-body", record)
        self.store.save(self.kernel.ledger)

    def _validated_render_record(
        self,
        ticket_id: str,
        request: dict[str, Any],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate and materialize immutable artifacts without mutating the ledger."""

        body = payload.get("rendered_body")
        bundle = payload.get("verification_bundle")
        root_value = payload.get("verification_audit_root")
        if (
            not isinstance(body, str)
            or not body
            or not isinstance(bundle, dict)
            or not isinstance(root_value, str)
            or not root_value
        ):
            raise DeliveryBodyError(
                "render-validation",
                "rendered body, verification bundle, and verification root are required",
            )
        if payload.get("render_request_hash") != request["request_hash"]:
            raise DeliveryBodyError(
                "render-validation", "rendered body belongs to another request"
            )
        if payload.get("expected_head_sha") != request["expected_head_sha"]:
            raise DeliveryBodyError(
                "render-validation", "rendered body is stale for the delivery head"
            )
        try:
            body, body_bytes = canonical_markdown(body)
        except PrBodyArtifactError as error:
            raise DeliveryBodyError("render-validation", str(error)) from error
        ticket = self.kernel.ledger["tickets"][ticket_id]
        expected_bundle, _bundle_ref = self._verification_bundle_from_handoff(
            ticket_id, phase="render-validation"
        )
        if bundle != expected_bundle:
            raise DeliveryBodyError(
                "render-validation",
                "rendered body bundle differs from the verified handoff bundle",
            )
        verification_root = Path(root_value)
        try:
            validator = load_pr_body_validator(
                verification_root,
                current_candidate=ticket["candidate_ref"],
            )
            normalized_bundle = validator(
                body, bundle, request["expected_head_sha"]
            )
        except VerificationCheckpointError as error:
            raise DeliveryBodyError(
                "render-validation", str(error)
            ) from error

        body_hash = hashlib.sha256(body_bytes).hexdigest()
        bundle_hash = self._canonical_digest(normalized_bundle)
        artifact_root = (
            self.store.path.parent / "pr-body-artifacts" / ticket_id
        )
        body_path = artifact_root / f"{body_hash}.md"
        bundle_path = artifact_root / f"{bundle_hash}.json"
        self._atomic_text(body_path, body_bytes)
        self._atomic_summary(bundle_path, normalized_bundle)
        return {
            "schema": 1,
            "request_hash": request["request_hash"],
            "expected_head_sha": request["expected_head_sha"],
            "body_sha256": body_hash,
            "body_encoding": CANONICAL_BODY_ENCODING,
            "body_path": str(body_path),
            "bundle_sha256": bundle_hash,
            "bundle_path": str(bundle_path),
            "verification_audit_root": str(verification_root),
        }

    def _load_rendered_body(
        self,
        ticket_id: str,
        request: dict[str, Any],
    ) -> tuple[str, dict[str, Any], Any]:
        ticket = self.kernel.ledger["tickets"][ticket_id]
        record = ticket["delivery"].get("pr-body")
        if not isinstance(record, dict):
            raise DeliveryBodyError(
                "render-validation", "validated PR-body artifact is absent"
            )
        try:
            if (
                record["request_hash"] != request["request_hash"]
                or record["expected_head_sha"] != request["expected_head_sha"]
            ):
                raise DeliveryBodyError(
                    "render-validation", "persisted PR-body artifact is stale"
                )
            artifact_root = (
                self.store.path.parent / "pr-body-artifacts" / ticket_id
            ).resolve()
            body_path = Path(record["body_path"]).resolve()
            bundle_path = Path(record["bundle_path"]).resolve()
            body_path.relative_to(artifact_root)
            bundle_path.relative_to(artifact_root)
            if body_path.name != f"{record['body_sha256']}.md":
                raise DeliveryBodyError(
                    "render-validation", "persisted PR-body path is invalid"
                )
            body = read_pr_body(
                body_path,
                recorded_sha256=record["body_sha256"],
                encoding=record.get("body_encoding"),
            )
            bundle = json.loads(
                bundle_path.read_text(encoding="utf-8")
            )
            if self._canonical_digest(bundle) != record["bundle_sha256"]:
                raise DeliveryBodyError(
                    "render-validation", "persisted verification bundle hash is invalid"
                )
            expected_bundle, _bundle_ref = self._verification_bundle_from_handoff(
                ticket_id, phase="render-validation"
            )
            if bundle != expected_bundle:
                raise DeliveryBodyError(
                    "render-validation",
                    "persisted bundle differs from the verified handoff bundle",
                )
            validator = load_pr_body_validator(
                Path(record["verification_audit_root"]),
                current_candidate=ticket["candidate_ref"],
            )
            validator(body, bundle, request["expected_head_sha"])
        except DeliveryBodyError:
            raise
        except PrBodyArtifactError as error:
            raise DeliveryBodyError("render-validation", str(error)) from error
        except (
            OSError,
            UnicodeError,
            ValueError,
            json.JSONDecodeError,
            VerificationCheckpointError,
        ) as error:
            raise DeliveryBodyError(
                "render-validation", f"persisted PR-body artifact is unreadable: {error}"
            ) from error
        except VerificationCheckpointError as error:
            raise DeliveryBodyError(
                "render-validation", f"persisted PR-body validation failed: {error}"
            ) from error
        return body, bundle, validator

    def reconcile_render_request(
        self,
        ticket_id: str,
        *,
        branch: str,
        base_branch: str,
        old_head: str,
        new_head: str,
    ) -> dict[str, Any]:
        return self._render_request(
            ticket_id,
            branch=branch,
            base_branch=base_branch,
            head=new_head,
            metadata_step="reconcile-pr-body-request",
            reconciled_from_head=old_head,
        )

    def accept_reconcile_render_payload(
        self,
        ticket_id: str,
        *,
        request: dict[str, Any],
        payload: dict[str, Any],
    ) -> tuple[str, dict[str, Any], Any]:
        """Persist a freshly rendered body bound to a reconciled delivery head."""

        ticket = self.kernel.ledger["tickets"][ticket_id]
        previous = copy.deepcopy(ticket["delivery"].get("pr-body"))
        if not isinstance(previous, dict):
            raise DeliveryBodyError(
                "reconcile-body-render",
                "stack reconciliation requires the previously validated PR body",
            )
        body = payload.get("rendered_body")
        if not isinstance(body, str):
            raise DeliveryBodyError(
                "reconcile-body-render",
                "reconciled PR body must contain the exact new head SHA",
            )
        try:
            body, _body_bytes = canonical_markdown(body)
        except PrBodyArtifactError as error:
            raise DeliveryBodyError("reconcile-body-render", str(error)) from error
        if request["expected_head_sha"] not in body:
            raise DeliveryBodyError(
                "reconcile-body-render",
                "reconciled PR body must contain the exact new head SHA",
            )
        record = self._validated_render_record(
            ticket_id, request, {**payload, "rendered_body": body}
        )
        rebinds = copy.deepcopy(previous.get("lineage_rebinds", []))
        rebinds.append(
            {
                "schema": 2,
                "old_head": request["reconciled_from_head"],
                "new_head": request["expected_head_sha"],
                "old_body_sha256": previous["body_sha256"],
                "new_body_sha256": record["body_sha256"],
                "old_bundle_sha256": previous["bundle_sha256"],
                "new_bundle_sha256": record["bundle_sha256"],
                "old_bundle_path": previous["bundle_path"],
                "new_bundle_path": record["bundle_path"],
                "old_verification_audit_root": previous[
                    "verification_audit_root"
                ],
                "new_verification_audit_root": record[
                    "verification_audit_root"
                ],
                "render_request_hash": request["request_hash"],
                "old_receipt": previous,
            }
        )
        rebound = {
            **record,
            "schema": 2,
            "lineage_rebinds": rebinds,
        }
        self.kernel.record_delivery_metadata(ticket_id, "pr-body", rebound)
        self.store.save(self.kernel.ledger)
        return self._load_rendered_body(ticket_id, request)

    def load_reconcile_rendered_body(
        self,
        ticket_id: str,
        request: dict[str, Any],
    ) -> tuple[str, dict[str, Any], Any] | None:
        record = self.kernel.ledger["tickets"][ticket_id]["delivery"].get(
            "pr-body"
        )
        if (
            not isinstance(record, dict)
            or record.get("schema") != 2
            or record.get("request_hash") != request["request_hash"]
            or record.get("expected_head_sha") != request["expected_head_sha"]
        ):
            return None
        return self._load_rendered_body(ticket_id, request)

    def _branch_base_sha(
        self,
        ticket_id: str,
        branch: str,
        expected_base_tree_oid: str,
    ) -> str:
        """Recover a verified base from a branch created by this ticket."""

        commit = self._run("git", "rev-parse", branch)
        if self._run("git", "rev-parse", f"{commit}^{{tree}}") == (
            expected_base_tree_oid
        ):
            return commit
        marker = f"Ticket-Autopilot-Run: {self.kernel.ledger['run_id']}/{ticket_id}"
        while marker in self._run("git", "log", "-1", "--format=%B", commit):
            parent = self._run(
                "git", "rev-parse", f"{commit}^", allow_failure=True
            )
            if not parent:
                break
            if self._run("git", "rev-parse", f"{parent}^{{tree}}") == (
                expected_base_tree_oid
            ):
                return parent
            commit = parent
        raise GitError(
            "delivery branch has no commit matching the verified CandidateRef "
            "base tree; reconciliation required"
        )

    def _ensure_branch(
        self,
        ticket_id: str,
        branch: str,
        base_branch: str,
        expected_base_tree_oid: str,
    ) -> str:
        effect = "delivery-branch"
        ticket = self.kernel.ledger["tickets"][ticket_id]
        recorded = ticket["delivery"].get("branch", {})
        current = self._run(
            "git", "symbolic-ref", "--quiet", "--short", "HEAD", allow_failure=True
        )
        branch_base_sha = (
            recorded.get("base_sha") if isinstance(recorded, dict) else None
        )
        if branch_base_sha and self._run(
            "git", "rev-parse", f"{branch_base_sha}^{{tree}}"
        ) != expected_base_tree_oid:
            raise GitError(
                "recorded delivery branch base differs from the verified "
                "CandidateRef base tree; reconciliation required"
            )
        if current != branch:
            exists = (
                self.runner.run(
                    ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
                    cwd=self.worktree,
                ).returncode
                == 0
            )
            if exists:
                if not branch_base_sha:
                    branch_base_sha = self._branch_base_sha(
                        ticket_id,
                        branch,
                        expected_base_tree_oid,
                    )
                self._run("git", "switch", branch)
            else:
                branch_base_sha = self._run("git", "rev-parse", "HEAD")
                observed_tree = self._run("git", "rev-parse", "HEAD^{tree}")
                if observed_tree != expected_base_tree_oid:
                    raise GitError(
                        "delivery checkout does not match the verified CandidateRef "
                        "base tree; reconciliation required"
                    )
                self._run("git", "switch", "-c", branch, branch_base_sha)
        if not branch_base_sha:
            branch_base_sha = self._branch_base_sha(
                ticket_id,
                branch,
                expected_base_tree_oid,
            )
        if self._run(
            "git", "rev-parse", f"{branch_base_sha}^{{tree}}"
        ) != expected_base_tree_oid:
            raise GitError(
                "recorded delivery branch base differs from the verified "
                "CandidateRef base tree; reconciliation required"
            )
        self.kernel.record_delivery_metadata(
            ticket_id,
            "branch",
            {
                "branch": branch,
                "base": base_branch,
                "base_sha": branch_base_sha,
                "base_tree_oid": expected_base_tree_oid,
            },
        )
        self._record_effect(ticket_id, effect)
        return branch_base_sha

    def _revalidate_docs_only_delivery(
        self, ticket: dict[str, Any]
    ) -> None:
        receipt = ticket.get("docs_only")
        if not isinstance(receipt, dict) or receipt.get("status") != "eligible":
            return
        try:
            revalidate_docs_only_receipt(
                self.worktree,
                ticket,
                receipt,
                evidence_dir=self.store.path.parent / "evidence",
            )
        except DocsOnlyError as error:
            raise GitError(
                f"docs-only delivery revalidation failed: {error}"
            ) from error

    def _ensure_summary(self, ticket_id: str) -> Path:
        ignored = self.kernel.ledger["ticket_source_mode"] == "ignored"
        if ignored:
            summary_root, _source, _destination, summary_path = _ignored_ticket_paths(
                self.kernel, ticket_id
            )
        else:
            summary_root = self.worktree
            _, done_path = _ticket_paths(
                self.kernel, ticket_id, Path(self.kernel.ledger["worktree"])
            )
            summary_path = done_path.with_suffix(".completion.json")
        self._atomic_summary(
            summary_path,
            _completion_summary(self.kernel, ticket_id),
        )
        relative = summary_path.relative_to(summary_root)
        if not ignored:
            self._run("git", "add", "--", str(relative))
        self.kernel.record_delivery_metadata(
            ticket_id,
            "summary",
            {"path": str(relative), "source_mode": self.kernel.ledger["ticket_source_mode"]},
        )
        self._record_effect(ticket_id, "completion-summary")
        return summary_path

    def _ensure_commit(
        self, ticket_id: str, branch: str, expected_tree_oid: str
    ) -> str:
        marker = (
            f"Ticket-Autopilot-Run: {self.kernel.ledger['run_id']}/{ticket_id}"
        )
        message = self._run("git", "log", "-1", "--format=%B")
        committed_tree = self._run("git", "rev-parse", "HEAD^{tree}")
        if marker not in message or committed_tree != expected_tree_oid:
            staged_tree = self._run("git", "write-tree")
            if staged_tree != expected_tree_oid:
                raise GitError(
                    "staged delivery tree differs from the revalidated CandidateRef"
                )
            staged = self.runner.run(
                ["git", "diff", "--cached", "--quiet"], cwd=self.worktree
            )
            if staged.returncode == 0:
                raise GitError("delivery commit has no staged changes")
            if staged.returncode != 1:
                raise GitError(staged.stderr or "Git could not inspect staged changes")
            self._run(
                "git",
                "commit",
                "-m",
                (
                    f"ticket {ticket_id}: complete"
                    if marker not in message
                    else f"ticket {ticket_id}: revalidate delivery candidate"
                ),
                "-m",
                marker,
            )
        current_branch = self._run(
            "git", "symbolic-ref", "--quiet", "--short", "HEAD"
        )
        head = self._run("git", "rev-parse", "HEAD")
        committed_tree = self._run("git", "rev-parse", "HEAD^{tree}")
        if current_branch != branch or committed_tree != expected_tree_oid:
            raise GitError(
                "recovered commit marker does not match branch and CandidateRef tree"
            )
        self.kernel.record_delivery_metadata(
            ticket_id, "commit", {"branch": branch, "head_sha": head}
        )
        self._record_effect(ticket_id, "delivery-commit")
        return head

    def _ensure_push(self, ticket_id: str, branch: str, head: str) -> None:
        remote = self._run(
            "git",
            "ls-remote",
            "--heads",
            "origin",
            f"refs/heads/{branch}",
        )
        remote_head = remote.split()[0] if remote else None
        recorded_head = (
            self.kernel.ledger["tickets"][ticket_id]
            .get("delivery", {})
            .get("push", {})
            .get("head_sha")
        )
        if remote_head not in {None, head, recorded_head}:
            raise GitError("remote branch diverged from the idempotent delivery head")
        if remote_head is None:
            self._run("git", "push", "-u", "origin", branch)
        elif remote_head != head:
            self._run("git", "merge-base", "--is-ancestor", remote_head, head)
            self._run("git", "push", "origin", branch)
        self.kernel.record_delivery_metadata(
            ticket_id, "push", {"branch": branch, "head_sha": head}
        )
        self._record_effect(ticket_id, "delivery-push")

    def _validate_pr_receipt(
        self,
        receipt: dict[str, Any],
        *,
        branch: str,
        base_branch: str,
        head: str,
        body: str,
    ) -> None:
        expected = {
            "provider": self.provider.name,
            "operation": "create-or-update-pr",
            "branch": branch,
            "base": base_branch,
            "head_sha": head,
        }
        for key, value in expected.items():
            if receipt.get(key) != value:
                raise TransitionError(
                    f"provider receipt {key} contradicts delivery state"
                )
        if receipt.get("body") != body:
            raise DeliveryBodyError(
                "readback-validation",
                "provider receipt body contradicts validated delivery body",
            )
        if not isinstance(receipt.get("pr_id"), str) or not receipt["pr_id"]:
            raise TransitionError("provider receipt requires pr_id")

    def _final_tree_projection_config(self) -> dict[str, Any] | None:
        value = self.kernel.ledger.get("final_tree_projection")
        if value is None:
            return None
        try:
            config = validate_projection_config(value)
        except FinalTreeProjectionError as error:
            raise CompletionProjectionError(str(error)) from error
        if config["mode"] == "enabled":
            raise CompletionProjectionError(
                "enabled final-tree projection is unavailable until its durable "
                "transaction and recovery contract is installed"
            )
        return config

    def _projection_artifact(
        self,
        ticket_id: str,
        document: dict[str, Any],
        payload: bytes,
    ) -> dict[str, Any]:
        digest = hashlib.sha256(payload).hexdigest()
        path = (
            self.store.path.parent
            / "artifacts"
            / "final-tree-projection"
            / ticket_id
            / f"{digest}.json"
        )
        if path.exists():
            if path.read_bytes() != payload:
                raise CompletionProjectionError(
                    "content-addressed final-tree projection artifact drifted"
                )
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(
                prefix=path.name + ".", dir=path.parent
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return {
            "schema": 1,
            "artifact": str(path),
            "sha256": digest,
            "status": document.get("status", "eligible"),
            "authority": dict(NON_AUTHORITY),
        }

    @staticmethod
    def _read_projection_artifact(reference: dict[str, Any]) -> dict[str, Any]:
        path = Path(str(reference.get("artifact", "")))
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise CompletionProjectionError(
                "final-tree projection artifact is unavailable"
            ) from error
        if hashlib.sha256(payload).hexdigest() != reference.get("sha256"):
            raise CompletionProjectionError(
                "final-tree projection artifact digest is invalid"
            )
        try:
            document = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CompletionProjectionError(
                "final-tree projection artifact is malformed"
            ) from error
        if not isinstance(document, dict):
            raise CompletionProjectionError(
                "final-tree projection artifact is malformed"
            )
        return document

    def _projection_excluded_reasons(
        self, ticket_id: str, ticket: dict[str, Any]
    ) -> list[str]:
        reasons: list[str] = []
        if ticket.get("completion_projection_grant") is not None:
            reasons.append("completion-projection-recovery")
        if ticket.get("docs_only") is not None:
            reasons.append("docs-only-special-lane")
        if ticket.get("current_source_relative_path") != ticket.get(
            "source_relative_path"
        ):
            reasons.append("non-original-source")
        for gate in self.kernel.ledger.get("gates", {}).values():
            if (
                gate.get("ticket_id") == ticket_id
                and gate.get("state") == "open"
            ):
                reasons.append(f"open-gate:{gate.get('category')}")
        return reasons

    def _prepare_projection_observation(
        self,
        ticket_id: str,
        summary: dict[str, Any],
        source: Path,
        destination: Path,
    ) -> dict[str, Any] | None:
        config = self._final_tree_projection_config()
        if config is None or config["mode"] == "off":
            return None
        ticket = self.kernel.ledger["tickets"][ticket_id]
        existing = ticket.get("delivery", {}).get(
            "final-tree-projection-plan"
        )
        if isinstance(existing, dict):
            document = self._read_projection_artifact(existing)
            if existing.get("status") == "eligible":
                try:
                    manifest = validate_manifest(document)
                except FinalTreeProjectionError as error:
                    raise CompletionProjectionError(str(error)) from error
                if (
                    manifest["implementation_candidate_ref"]
                    != ticket["candidate_ref"]
                    or manifest["artifact_generation"]
                    != ticket["artifact_generation"]
                ):
                    raise CompletionProjectionError(
                        "persisted final-tree projection plan is stale"
                    )
                return manifest
            return None
        try:
            planned = plan_tracked_completion(
                self.worktree,
                run_id=self.kernel.ledger["run_id"],
                ticket_id=ticket_id,
                artifact_generation=ticket["artifact_generation"],
                configuration=config,
                candidate_ref=ticket["candidate_ref"],
                source_relative_path=source.relative_to(
                    self.worktree
                ).as_posix(),
                destination_relative_path=destination.relative_to(
                    self.worktree
                ).as_posix(),
                receipt_document=summary,
                source_mode=self.kernel.ledger["ticket_source_mode"],
                delivery_metadata=ticket.get("delivery", {}),
                pr=ticket.get("pr"),
                excluded_reasons=self._projection_excluded_reasons(
                    ticket_id, ticket
                ),
            )
            reference = {
                **self._projection_artifact(
                    ticket_id, planned.manifest, planned.bytes
                ),
                "mode": config["mode"],
                "contract_version": planned.manifest["contract_version"],
                "manifest_digest": planned.manifest["manifest_digest"],
                "implementation_candidate_ref": planned.manifest[
                    "implementation_candidate_ref"
                ],
                "planned_delivery_candidate_ref": planned.manifest[
                    "planned_delivery_candidate_ref"
                ],
            }
            self.kernel.record_final_tree_projection(
                ticket_id, kind="plan", reference=reference
            )
            self.store.save(self.kernel.ledger)
            return planned.manifest
        except ProjectionExcluded as error:
            observation = excluded_observation(
                run_id=self.kernel.ledger["run_id"],
                ticket_id=ticket_id,
                artifact_generation=ticket["artifact_generation"],
                configuration=config,
                code=error.code,
                detail=error.detail,
            )
        except FinalTreeProjectionError as error:
            observation = excluded_observation(
                run_id=self.kernel.ledger["run_id"],
                ticket_id=ticket_id,
                artifact_generation=ticket["artifact_generation"],
                configuration=config,
                code="observer-error",
                detail=str(error),
            )
        reference = {
            **self._projection_artifact(
                ticket_id, observation.document, observation.bytes
            ),
            "mode": config["mode"],
            "contract_version": observation.document["contract_version"],
            "reason": observation.document["reason"],
        }
        self.kernel.record_final_tree_projection(
            ticket_id, kind="plan", reference=reference
        )
        self.store.save(self.kernel.ledger)
        return None

    def _record_projection_observation(
        self,
        ticket_id: str,
        manifest: dict[str, Any] | None,
        actual_candidate: dict[str, Any],
    ) -> None:
        if manifest is None:
            return
        try:
            observation = compare_projection(
                self.worktree, manifest, actual_candidate
            )
        except FinalTreeProjectionError as error:
            observation = comparison_failure(
                manifest, actual_candidate, str(error)
            )
        reference = {
            **self._projection_artifact(
                ticket_id, observation.document, observation.bytes
            ),
            "mode": manifest["configuration"]["mode"],
            "contract_version": observation.document["contract_version"],
            "manifest_digest": manifest["manifest_digest"],
            "observation_digest": observation.document[
                "observation_digest"
            ],
            "actual_delivery_candidate_ref": actual_candidate,
            "discrepancies": observation.document["discrepancies"],
        }
        self.kernel.record_final_tree_projection(
            ticket_id, kind="observation", reference=reference
        )
        self.store.save(self.kernel.ledger)

    def apply(
        self,
        ticket_id: str,
        *,
        render_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._active_ticket_id = ticket_id
        ticket = self.kernel.ledger["tickets"].get(ticket_id)
        open_provider_gates = [
            (gate_id, gate)
            for gate_id, gate in self.kernel.ledger["gates"].items()
            if gate["ticket_id"] == ticket_id
            and gate["category"]
            in {"provider-environment", "provider-pr", "delivery-pr-body"}
            and gate["state"] == "open"
            and gate["resume_state"] in {"verified", "pr-open"}
        ]
        resumable_provider_gate = (
            ticket is not None
            and ticket["state"] == "gated"
            and bool(open_provider_gates)
            and not any(
                gate["ticket_id"] == ticket_id
                and gate["state"] == "open"
                and gate["category"]
                not in {
                    "provider-environment",
                    "provider-pr",
                    "delivery-pr-body",
                }
                for gate in self.kernel.ledger["gates"].values()
            )
        )
        if ticket is None or (
            ticket["state"] not in {"active", "verified", "pr-open"}
            and not resumable_provider_gate
        ):
            raise TransitionError(
                "delivery requires active revalidation, verified, or pr-open state"
            )
        if ticket["state"] == "pr-open":
            return {
                "result": "pr-open",
                "head_sha": ticket["pr"]["head_sha"],
                "branch": ticket["pr"]["branch"],
                "pr_id": ticket["pr"]["pr_id"],
            }
        if ticket["state"] == "active":
            branch_record = ticket["delivery"].get("branch", {})
            return {
                "result": "revalidation-required",
                "tree_oid": ticket["candidate_ref"]["candidate_tree_oid"],
                "branch": branch_record.get("branch"),
            }
        self._final_tree_projection_config()
        boundary_candidate = candidate_ref(
            self.worktree,
            ticket["ticket_digest"],
            base_ref=ticket["candidate_ref"]["base_tree_oid"],
        )
        if (
            ticket.get("pr") is None
            and self.kernel.reset_stale_delivery_preparation(
                ticket_id, boundary_candidate
            )
        ):
            self.store.save(self.kernel.ledger)
            ticket = self.kernel.ledger["tickets"][ticket_id]
        plan = build_delivery_plan(
            self.provider,
            self.kernel.ledger,
            ticket_id,
            default_base="main",
            title=f"Ticket {ticket_id}",
            body_artifact=f"render-pending://{self.kernel.ledger['run_id']}/{ticket_id}",
        )
        if ticket["delivery"].get("prepared") is None:
            self._revalidate_docs_only_delivery(ticket)
        delivery_base_sha = self._ensure_branch(
            ticket_id,
            plan.branch,
            plan.base_branch,
            ticket["candidate_ref"]["base_tree_oid"],
        )
        prepared = ticket["delivery"].get("prepared")
        if prepared is None:
            self._revalidate_docs_only_delivery(ticket)
            source, destination = _ticket_paths(
                self.kernel, ticket_id, self.worktree
            )
            projection_manifest = self._prepare_projection_observation(
                ticket_id,
                _completion_summary(self.kernel, ticket_id),
                source,
                destination,
            )
            finalize_done(self.store, self.kernel, ticket_id)
            self._ensure_summary(ticket_id)
            fixed = candidate_ref(
                self.worktree,
                ticket["ticket_digest"],
                base_ref=ticket["candidate_ref"]["base_tree_oid"],
            )
            self._record_projection_observation(
                ticket_id, projection_manifest, asdict(fixed)
            )
            self.kernel.record_delivery_candidate(ticket_id, fixed)
            self.kernel.record_delivery_metadata(
                ticket_id,
                "prepared",
                {"candidate_ref": asdict(fixed)},
            )
            self.store.save(self.kernel.ledger)
            prepared = ticket["delivery"]["prepared"]
        fixed = candidate_ref(
            self.worktree,
            ticket["ticket_digest"],
            base_ref=ticket["candidate_ref"]["base_tree_oid"],
        )
        prepared_ref = prepared.get("candidate_ref", {})
        if any(
            prepared_ref.get(field) != getattr(fixed, field)
            for field in (
                "contract_version",
                "ticket_digest",
                "base_tree_oid",
                "candidate_tree_oid",
            )
        ):
            raise GitError(
                "prepared delivery tree differs from the recorded delivery CandidateRef"
            )
        head = self._ensure_commit(
            ticket_id, plan.branch, fixed.candidate_tree_oid
        )
        self._ensure_push(ticket_id, plan.branch, head)
        request = self._render_request(
            ticket_id,
            branch=plan.branch,
            base_branch=plan.base_branch,
            head=head,
        )
        if render_payload is not None:
            self._accept_render_payload(ticket_id, request, render_payload)
        if not ticket["delivery"].get("pr-body"):
            self.kernel.record_delivery_metadata(
                ticket_id,
                "result",
                {"phase": "render", "result": "render-required"},
            )
            self.store.save(self.kernel.ledger)
            return {
                "result": "render-required",
                "head_sha": head,
                "branch": plan.branch,
                "render_request_hash": request["request_hash"],
                "render_request": request,
            }
        body, bundle, body_validator = self._load_rendered_body(
            ticket_id, request
        )
        pr_receipt = self._provider_execute(
            ticket_id,
            CREATE_OR_UPDATE_PR,
            branch=plan.branch,
            base=plan.base_branch,
            head_sha=head,
            title=f"Ticket {ticket_id}",
            body_artifact=body,
        )
        if pr_receipt.get("evidence_class") != "live":
            self.kernel.record_delivery_metadata(
                ticket_id, "provider-simulation", pr_receipt
            )
            self.kernel.record_delivery_metadata(
                ticket_id,
                "result",
                {
                    "phase": "provider",
                    "result": "waiting-provider",
                    "gate": "provider-pr",
                },
            )
            if not open_provider_gates:
                self.kernel.open_gate(
                    ticket_id,
                    "provider-pr",
                    scope="ticket",
                    reason=(
                        "simulated provider evidence cannot authorize PR state; "
                        "resume this run in live provider mode"
                    ),
                )
                self.store.save(self.kernel.ledger)
            return {
                "result": "waiting-provider",
                "head_sha": head,
                "branch": plan.branch,
                "provider_receipt": pr_receipt,
            }
        self._validate_pr_receipt(
            pr_receipt,
            branch=plan.branch,
            base_branch=plan.base_branch,
            head=head,
            body=body,
        )
        try:
            body_validator(
                pr_receipt["body"], bundle, pr_receipt["head_sha"]
            )
        except VerificationCheckpointError as error:
            raise DeliveryBodyError(
                "readback-validation",
                f"provider PR-body readback validation failed: {error}",
            ) from error
        for gate_id, _gate in open_provider_gates:
            self.kernel.approve_gate(
                gate_id,
                actor=f"provider:{self.provider.name}",
                evidence=f"live-readback:{pr_receipt['pr_id']}:{head}",
            )
        self.store.save(self.kernel.ledger)
        self.kernel.record_delivery_metadata(ticket_id, "pr", pr_receipt)
        self.kernel.record_delivery_metadata(
            ticket_id,
            "result",
            {"phase": "readback", "result": "pr-open"},
        )
        self.kernel.record_pr(
            ticket_id,
            provider=self.provider.name,
            pr_id=pr_receipt["pr_id"],
            head_sha=head,
            branch=plan.branch,
            base_branch=plan.base_branch,
            base_sha=delivery_base_sha,
        )
        self._record_effect(ticket_id, "delivery-pr")
        return {
            "result": "pr-open",
            "head_sha": head,
            "branch": plan.branch,
            "pr_id": pr_receipt["pr_id"],
        }
