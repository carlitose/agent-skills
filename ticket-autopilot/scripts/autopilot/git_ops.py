from __future__ import annotations

import codecs
import os
import re
import shutil
import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .candidate_contract import CandidateRef
from .command_capture import CaptureFailure, capture_command
from .kernel import TransitionError


class GitError(RuntimeError):
    """A local Git precondition or guarded operation failed.

    ``detail`` names what to change, in the shape every named rejection uses.
    ``str(error)`` stays the invariant, so existing callers and tests keep their text.
    """

    def __init__(self, message: str, *, detail: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.detail = dict(detail) if detail is not None else None


def assert_remote_head(
    observed_head: str | None,
    allowed_heads: set[str | None],
    *,
    phase: str,
) -> str | None:
    """Return an allowed remote head or fail closed on divergence."""

    if observed_head not in allowed_heads:
        raise GitError(f"remote branch diverged {phase}")
    return observed_head


@dataclass(frozen=True)
class CommandResult:
    """Command output with surrounding whitespace removed.

    The trimming is load-bearing, not incidental. Every consumer treats these as scalars:
    `git rev-parse` answers `"bba712e...\\n"` and is compared against a tree OID,
    `ls-remote` output is split, `--format=%B` is substring-searched for a run marker, and
    the provider paths parse JSON. Returning the raw text would make each of those
    comparisons fail on the trailing newline instead.

    The consequence is a boundary worth stating: **this type cannot carry a
    whitespace-sensitive payload**. A PR body, a file's contents, a diff — anything whose
    trailing newline is part of its identity — must not be read back through here. Bodies
    reach the delivery readback as a JSON field precisely because of that, and
    `finalizer` compares them literally, so a trimmed value would gate every delivery whose
    body ends in a newline.
    """

    stdout: str
    stderr: str
    returncode: int


class CommandRunner(Protocol):
    def run(self, command: list[str], *, cwd: Path) -> CommandResult: ...

    # Whether this runner would launch `program` through a Windows batch wrapper, which
    # reparses the command line. A runner that does not launch real processes has no such
    # hazard, so callers read it through `runner_uses_batch_wrapper` and a missing method
    # means no.
    def uses_batch_wrapper(self, program: str) -> bool: ...


def runner_uses_batch_wrapper(runner: object, program: str) -> bool:
    """Ask `runner` whether it would reach `program` through a batch wrapper."""

    answer = getattr(runner, "uses_batch_wrapper", None)
    return bool(answer(program)) if callable(answer) else False


def _run_captured(
    command: list[str], *, cwd: Path, cancel_event: threading.Event | None = None,
) -> tuple[bytes, str, int]:
    """Run `command`, returning raw stdout, decoded stderr, and the exit code.

    The two streams carry different kinds of thing and deserve different failure modes.

    `stdout` is data: SHAs, branch names, remote heads, config values. It feeds digests,
    equality checks, and `assert_cleanup_safe`, which decides whether a worktree may be
    deleted. An undecodable byte there must fail loudly rather than become U+FFFD inside a
    comparison that then quietly answers the wrong question. Git/scalar callers use
    `_decode_data`; Azure stdout has an explicitly selected strict producer codec.

    `stderr` remains diagnostic text, including producer warnings that can invalidate
    stdout. It may arrive in a local code page; a single `0xf3` decoded strictly can
    destroy the reported message, so diagnostic decoding stays lenient here.

    `subprocess` applies one `errors=` to both streams, which is why this splits them. And
    stdout stays raw so that a *failing* command can still quote it back to a human without
    a strict decode raising in place of the error being explained.
    """

    setting = "TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS"
    try:
        timeout = float(os.environ.get(setting, "300"))
    except ValueError as error:
        raise GitError(f"{setting} must be a finite number from 0.1 to 3600 seconds") from error
    if not 0.1 <= timeout <= 3600:
        raise GitError(f"{setting} must be a finite number from 0.1 to 3600 seconds")
    output_setting = "TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES"
    try:
        max_output = int(os.environ.get(output_setting, str(16 * 1024 * 1024)))
    except ValueError as error:
        raise GitError(f"{output_setting} must be an integer from 1 to 67108864 bytes") from error
    if not 1 <= max_output <= 64 * 1024 * 1024:
        raise GitError(f"{output_setting} must be an integer from 1 to 67108864 bytes")
    try:
        raw_stdout, raw_stderr, returncode = capture_command(
            command, cwd=cwd, timeout_seconds=timeout, max_output_bytes=max_output,
            cancel_event=cancel_event,
        )
    except CaptureFailure as error:
        diagnostic = _decode_diagnostic(error.stderr[:8192]).strip() or "(empty)"
        outcome = (
            "outcome is uncertain. A mutating command may already have taken effect; "
            "reobserve state before repeating it"
            if error.started else "this command was not executed"
        )
        cleanup = (
            "; cleanup unconfirmed: " + "; ".join(error.cleanup_issues)
            if error.cleanup_issues else ""
        )
        executable = repr(command[0]) if command else "(empty argv)"
        raise GitError(
            f"command {error.reason} ({executable}): {error}; {outcome}. "
            f"stderr (bounded diagnostic): {diagnostic}{cleanup}"
        ) from error
    return raw_stdout, _decode_diagnostic(raw_stderr), returncode


def _decode_data(raw: bytes) -> str:
    """Decode command output that will be compared, hashed, or acted on."""

    return raw.decode("utf-8")


def _decode_diagnostic(raw: bytes) -> str:
    """Decode command output that will only be shown."""

    return raw.decode("utf-8", errors="replace")


AZURE_STDOUT_ENCODING_ENV = "TICKET_AUTOPILOT_AZURE_STDOUT_ENCODING"


class AzureCliOutputError(RuntimeError):
    """An explicit Azure producer profile is missing or cannot yield exact data."""

    def __init__(self, detail: str, *, returncode: int | None = None, stderr: str = ""):
        self.returncode = returncode
        self.stderr = stderr
        if returncode is None:
            context = "this command was not executed"
        else:
            context = (
                f"exit {returncode}; stderr: {stderr.strip() or '(empty)'}. "
                "A mutating command may already have taken effect; "
                "reobserve provider state before repeating it"
            )
        super().__init__(f"Azure CLI stdout: {detail}; {context}")


def _azure_codec(setting: str | None) -> str:
    if not setting:
        raise AzureCliOutputError(
            f"explicit producer encoding required; set {AZURE_STDOUT_ENCODING_ENV} "
            "to established utf-8 or cpNNN; decoder selection does not configure the CLI"
        )
    try:
        codec = codecs.lookup(setting).name
    except LookupError as error:
        raise AzureCliOutputError(
            f"unsupported encoding {setting!r}; use established utf-8 or cpNNN"
        ) from error
    if codec != "utf-8" and not re.fullmatch(r"cp[0-9]+", codec):
        raise AzureCliOutputError(
            f"unsupported encoding {setting!r}; use established utf-8 or cpNNN"
        )
    return codec


def _decode_azure_stdout(raw: bytes, stderr: str, returncode: int, codec: str) -> str:
    # Knack 0.14 can return exit zero and valid ASCII JSON after dropping Unicode.
    # This observed producer signal invalidates data; stderr decoding is unchanged.
    if re.search(
        r"Unable to encode the output with [^\r\n]+ encoding\. "
        r"Unsupported characters are discarded\.", stderr
    ):
        raise AzureCliOutputError(
            "producer reported discarded characters; exact JSON text is unavailable",
            returncode=returncode, stderr=stderr,
        )
    try:
        return raw.decode(codec, errors="strict")
    except UnicodeDecodeError as error:
        raise AzureCliOutputError(
            f"data does not match selected encoding {codec!r} at byte {error.start}; "
            "no replacement or fallback was applied",
            returncode=returncode, stderr=stderr,
        ) from error


# CreateProcess runs a `.cmd` or `.bat` through `cmd.exe`, which reparses the command line
# that `subprocess.list2cmdline` built. That function quotes an element only when it holds a
# space or a tab, so an element without spaces reaches the shell bare: `|---|---|` is read as
# a pipe and `a>b` as a redirection that writes a file into the working directory. A caller
# that must pass arbitrary text asks this first and keeps that text off the command line.
_BATCH_WRAPPER_SUFFIXES = frozenset({".cmd", ".bat"})


def resolves_to_batch_wrapper(program: str) -> bool:
    """Whether `program` resolves to a Windows batch wrapper on this host."""

    if os.name != "nt" or not program:
        return False
    resolved = shutil.which(program)
    if not resolved:
        return False
    return Path(resolved).suffix.casefold() in _BATCH_WRAPPER_SUFFIXES


class SubprocessCommandRunner:
    def __init__(
        self, *, azure_stdout_encoding: str | None = None,
        cancel_event: threading.Event | None = None,
    ):
        self._cancel_event = cancel_event
        # Snapshot one setting per runner. No environment or launcher is rewritten.
        self._azure_stdout_encoding = (
            azure_stdout_encoding if azure_stdout_encoding is not None
            else os.environ.get(AZURE_STDOUT_ENCODING_ENV)
        )

    def uses_batch_wrapper(self, program: str) -> bool:
        return resolves_to_batch_wrapper(program)

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        is_azure = bool(command) and Path(command[0]).name.casefold() in {
            "az", "az.cmd", "az.exe"
        }
        codec = _azure_codec(self._azure_stdout_encoding) if is_azure else None
        # Resolve PATHEXT on Windows without changing the logical producer identity.
        resolved = shutil.which(command[0]) if command else None
        if resolved:
            command = [resolved, *command[1:]]
        raw_stdout, stderr, returncode = _run_captured(
            command, cwd=cwd, cancel_event=self._cancel_event
        )
        stdout = (
            _decode_azure_stdout(raw_stdout, stderr, returncode, codec)
            if codec is not None else _decode_data(raw_stdout)
        )
        return CommandResult(
            stdout=stdout.strip(),
            stderr=stderr.strip(),
            returncode=returncode,
        )


# Commands that can move a path from one repository to another, or into a repository at all.
# Anything outside this set may change content, never the structure question below.
_STRUCTURE_COMMANDS = frozenset({"init", "clone", "worktree", "submodule"})

# `None` means "no scope": every question reaches Git. A scope is entered per CLI invocation,
# so a cached answer cannot outlive the command that asked it, and nothing a test or another
# process does between invocations can be answered from a stale entry.
_STRUCTURE_CACHE: dict[tuple[str, Path], Path] | None = None


@contextmanager
def repository_scope() -> Iterator[None]:
    """Answer a repository's *structure* questions once per invocation instead of per call.

    Measured on one lifecycle case: `rev-parse --show-toplevel` ran 116 times and
    `--git-common-dir` 52, for the same unchanged answer, at ~95 ms each including
    containment. Only the two structure facts are reused, and only inside this scope; a
    structure-changing Git command clears them, and a failure is never remembered.
    """
    global _STRUCTURE_CACHE
    previous = _STRUCTURE_CACHE
    _STRUCTURE_CACHE = {}
    try:
        yield
    finally:
        _STRUCTURE_CACHE = previous


def _remembered(kind: str, key: Path, compute: Callable[[], Path]) -> Path:
    cache = _STRUCTURE_CACHE
    if cache is None:
        return compute()
    entry = (kind, key)
    if entry not in cache:
        cache[entry] = compute()  # A raising call stores nothing.
    return cache[entry]


def run_git(repo: Path, *args: str) -> str:
    if args and args[0] in _STRUCTURE_COMMANDS and _STRUCTURE_CACHE is not None:
        _STRUCTURE_CACHE.clear()
    raw_stdout, stderr, returncode = _run_captured(["git", *args], cwd=repo)
    if returncode:
        detail = (
            stderr.strip()
            or _decode_diagnostic(raw_stdout).strip()
            or "unknown Git error"
        )
        raise GitError(f"git {' '.join(args)} failed: {detail}")
    return _decode_data(raw_stdout).strip()


def repository_root(repo: Path) -> Path:
    resolved = repo.resolve()
    return _remembered(
        "toplevel", resolved,
        lambda: Path(run_git(resolved, "rev-parse", "--show-toplevel")).resolve(),
    )


def common_git_dir(repo: Path) -> Path:
    root = repository_root(repo)

    def compute() -> Path:
        path = Path(run_git(root, "rev-parse", "--git-common-dir"))
        return path.resolve() if path.is_absolute() else (root / path).resolve()

    return _remembered("common-dir", root, compute)


def origin_url(repo: Path) -> str | None:
    raw_stdout, _stderr, _returncode = _run_captured(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=repository_root(repo),
    )
    return _decode_data(raw_stdout).strip() or None


def validate_run_id(run_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", run_id):
        raise GitError("run ID must be 1-80 safe filename characters")


def assert_ticket_folder_at_ref(
    repo: Path, folder: Path, *, base_ref: str
) -> Path:
    root = repository_root(repo)
    resolved = folder.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise GitError("ticket folder must be inside the repository") from error
    if not relative.parts:
        raise GitError("repository root cannot be used as the ticket folder")
    uncommitted = run_git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        str(relative),
    )
    if uncommitted:
        raise GitError("ticket folder differs from committed Git state")
    run_git(root, "cat-file", "-e", f"{base_ref}:{relative.as_posix()}")
    _comparison_stdout, comparison_stderr, comparison_code = _run_captured(
        ["git", "diff", "--quiet", base_ref, "--", str(relative)], cwd=root,
    )
    if comparison_code == 1:
        raise GitError(f"ticket folder differs from selected base {base_ref!r}")
    if comparison_code:
        raise GitError(
            comparison_stderr.strip()
            or "Git could not compare the ticket folder to the selected base"
        )
    return relative


def run_directory(repo: Path, run_id: str) -> Path:
    validate_run_id(run_id)
    return common_git_dir(repo) / "ticket-autopilot" / "runs" / run_id


def create_isolated_worktree(
    repo: Path, run_id: str, *, base_ref: str = "HEAD"
) -> Path:
    root = repository_root(repo)
    validate_run_id(run_id)
    parent = root.parent / f".{root.name}-ticket-autopilot-worktrees"
    worktree = parent / run_id
    if worktree.exists():
        raise GitError(f"isolated worktree path already exists: {worktree}")
    parent.mkdir(parents=True, exist_ok=True)
    run_git(root, "worktree", "add", "--detach", str(worktree), base_ref)
    if repository_root(worktree) != worktree.resolve():
        raise GitError("Git created an unexpected worktree root")
    return worktree.resolve()


def worktree_is_clean(worktree: Path) -> bool:
    return (
        run_git(worktree, "status", "--porcelain=v1", "--untracked-files=all") == ""
    )


def remove_isolated_worktree(repo: Path, worktree: Path) -> None:
    root = repository_root(repo)
    resolved = worktree.resolve()
    expected_parent = root.parent / f".{root.name}-ticket-autopilot-worktrees"
    if resolved.parent != expected_parent.resolve():
        raise GitError(f"refusing to remove unmanaged worktree: {resolved}")
    if not resolved.exists():
        return
    if not worktree_is_clean(resolved):
        raise GitError(f"isolated worktree has unpublished local state: {resolved}")
    run_git(root, "worktree", "remove", str(resolved))


def _remote_default_branch(worktree: Path) -> tuple[str, str] | None:
    """Name the remote's default branch and its current head, or nothing.

    Read-only: `ls-remote` asks the remote what it already has and writes nothing,
    locally or remotely.
    """

    raw, _stderr, returncode = _run_captured(
        ["git", "ls-remote", "--symref", "origin", "HEAD"], cwd=worktree
    )
    if returncode:
        return None
    branch: str | None = None
    for line in _decode_data(raw).splitlines():
        if line.startswith("ref:"):
            target = line.split()[1]
            branch = target.removeprefix("refs/heads/")
            break
    if not branch:
        return None
    listed = run_git(worktree, "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    if not listed:
        return None
    return branch, listed.split()[0]


def head_retained_by_integration(worktree: Path, head: str) -> dict[str, object]:
    """Answer whether this head is already contained in the remote default branch.

    A provider that deletes the source branch when it merges leaves the commit in the
    default branch and nowhere else. Asking only whether the run's branch still exists
    answers the wrong question and calls integrated work unretained. Ancestry is proven
    locally, so a default branch this repository has never fetched yields no proof
    rather than a guess; nothing is fetched, pushed or written here.
    """

    observed = _remote_default_branch(worktree)
    if observed is None:
        return {
            "retained": False,
            "reason": "default-branch-unobservable",
            "default_branch": None,
            "default_sha": None,
        }
    branch, default_sha = observed
    details: dict[str, object] = {
        "retained": False,
        "reason": "",
        "default_branch": branch,
        "default_sha": default_sha,
    }
    _present_stdout, _present_stderr, present_code = _run_captured(
        ["git", "cat-file", "-e", f"{default_sha}^{{commit}}"], cwd=worktree
    )
    if present_code:
        details["reason"] = "default-branch-object-missing"
        return details
    _ancestor_stdout, _ancestor_stderr, ancestor_code = _run_captured(
        ["git", "merge-base", "--is-ancestor", head, default_sha], cwd=worktree
    )
    details["retained"] = ancestor_code == 0
    details["reason"] = (
        "contained-in-default-branch"
        if ancestor_code == 0
        else "outside-default-branch"
    )
    return details


def _retention_refusal(worktree: Path, head: str, situation: str) -> GitError:
    """Explain a refusal in terms of what was checked, not of a missing branch."""

    proof = head_retained_by_integration(worktree, head)
    branch = proof["default_branch"]
    default_sha = proof["default_sha"]
    if proof["reason"] == "default-branch-unobservable":
        return GitError(
            f"{situation} and the remote default branch could not be observed, "
            "so retention is unproven"
        )
    if proof["reason"] == "default-branch-object-missing":
        return GitError(
            f"{situation}; the default branch {branch!r} is at {default_sha}, which "
            f"this repository does not have, so retention is unproven: run "
            f"`git fetch origin {branch}` and try again"
        )
    return GitError(
        f"{situation} and the head is not contained in the default branch {branch!r} "
        f"at {default_sha}"
    )


def assert_cleanup_safe(worktree: Path, ledger: dict[str, object]) -> None:
    if not worktree.exists():
        return
    if not worktree_is_clean(worktree):
        raise GitError(f"isolated worktree has unpublished local state: {worktree}")
    head = run_git(worktree, "rev-parse", "HEAD")
    raw_branch, _branch_stderr, branch_returncode = _run_captured(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=worktree,
    )
    if branch_returncode:
        detached_elsewhere = head != ledger.get("base_sha")
        if detached_elsewhere and not head_retained_by_integration(worktree, head)[
            "retained"
        ]:
            raise _retention_refusal(
                worktree, head, "detached worktree contains an unretained commit"
            )
        return
    # Strict: this branch name selects the remote ref compared below, and the comparison
    # authorizes deleting the worktree.
    branch = _decode_data(raw_branch).strip()
    # Only the exit code is consulted here, so neither stream is decoded as data.
    _upstream_stdout, _upstream_stderr, upstream_returncode = _run_captured(
        ["git", "rev-parse", "--verify", "@{upstream}"],
        cwd=worktree,
    )
    if upstream_returncode:
        if head_retained_by_integration(worktree, head)["retained"]:
            return
        raise _retention_refusal(
            worktree, head, f"branch {branch!r} has no retained upstream"
        )
    ahead = int(run_git(worktree, "rev-list", "--count", "@{upstream}..HEAD"))
    if ahead:
        if head_retained_by_integration(worktree, head)["retained"]:
            return
        raise _retention_refusal(
            worktree, head, f"branch {branch!r} has unpublished commits"
        )
    remote = run_git(
        worktree, "ls-remote", "--heads", "origin", f"refs/heads/{branch}"
    )
    remote_head = remote.split()[0] if remote else None
    if remote_head != head:
        if head_retained_by_integration(worktree, head)["retained"]:
            return
        raise _retention_refusal(
            worktree, head, f"branch {branch!r} is not retained at its current head"
        )


def semantic_candidate_ref(
    worktree: Path,
    ticket_digest: str,
    *,
    base_ref: str = "HEAD",
) -> CandidateRef:
    run_git(worktree, "add", "-A")
    base_tree_oid = run_git(worktree, "rev-parse", f"{base_ref}^{{tree}}")
    candidate_tree_oid = run_git(worktree, "write-tree")
    return CandidateRef(
        base_tree_oid=base_tree_oid,
        candidate_tree_oid=candidate_tree_oid,
        ticket_digest=ticket_digest,
        contract_version=2,
    )


candidate_ref = semantic_candidate_ref


def candidate_files(worktree: Path, candidate: CandidateRef) -> list[str]:
    candidate.validate()
    encoded = run_git(
        worktree,
        "diff",
        "--name-only",
        "-z",
        candidate.base_tree_oid,
        candidate.candidate_tree_oid,
    )
    return [path for path in encoded.split("\0") if path]


def assert_candidate(worktree: Path, expected: CandidateRef) -> None:
    expected.validate()
    run_git(worktree, "add", "-A")
    current = CandidateRef(
        base_tree_oid=run_git(worktree, "rev-parse", "HEAD^{tree}"),
        candidate_tree_oid=run_git(worktree, "write-tree"),
        ticket_digest=expected.ticket_digest,
        contract_version=expected.contract_version,
    )
    if current != expected:
        raise TransitionError("worktree drift: CandidateRef does not match")
