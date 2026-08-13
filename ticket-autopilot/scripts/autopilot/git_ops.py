from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .candidate_contract import CandidateRef
from .kernel import TransitionError


class GitError(RuntimeError):
    """A local Git precondition or guarded operation failed."""


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


def _run_captured(command: list[str], *, cwd: Path) -> tuple[bytes, str, int]:
    """Run `command`, returning raw stdout, decoded stderr, and the exit code.

    The two streams carry different kinds of thing and deserve different failure modes.

    `stdout` is data: SHAs, branch names, remote heads, config values. It feeds digests,
    equality checks, and `assert_cleanup_safe`, which decides whether a worktree may be
    deleted. An undecodable byte there must fail loudly rather than become U+FFFD inside a
    comparison that then quietly answers the wrong question, so callers decode it through
    `_decode_data` — the strict invariant `WD-02` chose.

    `stderr` only ever reaches a human or a log. On a non-English Windows it arrives in the
    console codepage, and a single `0xf3` byte decoded strictly raises `UnicodeDecodeError`
    and destroys the very message being reported, so it is decoded leniently here.

    `subprocess` applies one `errors=` to both streams, which is why this splits them. And
    stdout stays raw so that a *failing* command can still quote it back to a human without
    a strict decode raising in place of the error being explained.
    """

    result = subprocess.run(command, cwd=cwd, capture_output=True, check=False)
    return (
        result.stdout,
        result.stderr.decode("utf-8", errors="replace"),
        result.returncode,
    )


def _decode_data(raw: bytes) -> str:
    """Decode command output that will be compared, hashed, or acted on."""

    return raw.decode("utf-8")


def _decode_diagnostic(raw: bytes) -> str:
    """Decode command output that will only be shown."""

    return raw.decode("utf-8", errors="replace")


class SubprocessCommandRunner:
    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        # On Windows the provider CLI is a `.cmd` (`az.cmd`, `gh.cmd`) and `CreateProcess` does
        # not apply PATHEXT, so `subprocess.run(["az", ...])` fails with
        # `FileNotFoundError: [WinError 2]` even when `az` is on PATH. `shutil.which` resolves the
        # extension and returns the same path as before on POSIX.
        resolved = shutil.which(command[0]) if command else None
        if resolved:
            command = [resolved, *command[1:]]
        raw_stdout, stderr, returncode = _run_captured(command, cwd=cwd)
        return CommandResult(
            stdout=_decode_data(raw_stdout).strip(),
            stderr=stderr.strip(),
            returncode=returncode,
        )


def run_git(repo: Path, *args: str) -> str:
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
    return Path(run_git(repo.resolve(), "rev-parse", "--show-toplevel")).resolve()


def common_git_dir(repo: Path) -> Path:
    root = repository_root(repo)
    raw = run_git(root, "rev-parse", "--git-common-dir")
    path = Path(raw)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


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
    comparison = subprocess.run(
        ["git", "diff", "--quiet", base_ref, "--", str(relative)],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if comparison.returncode == 1:
        raise GitError(f"ticket folder differs from selected base {base_ref!r}")
    if comparison.returncode:
        raise GitError(
            comparison.stderr.decode("utf-8", errors="replace").strip()
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
        if head != ledger.get("base_sha"):
            raise GitError("detached worktree contains an unretained commit")
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
        raise GitError(f"branch {branch!r} has no retained upstream")
    ahead = int(run_git(worktree, "rev-list", "--count", "@{upstream}..HEAD"))
    if ahead:
        raise GitError(f"branch {branch!r} has unpublished commits")
    remote = run_git(
        worktree, "ls-remote", "--heads", "origin", f"refs/heads/{branch}"
    )
    remote_head = remote.split()[0] if remote else None
    if remote_head != head:
        raise GitError(f"branch {branch!r} is not retained at its current head")


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
