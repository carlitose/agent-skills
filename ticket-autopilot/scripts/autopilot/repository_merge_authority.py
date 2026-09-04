"""Repository-wide autonomous merge authority and canonical run discovery."""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import common_git_dir
from .repository_authority import (
    AUTHORITY_SCOPE,
    AuthorityKind,
    RepositoryAuthorityStore,
    RepositoryBinding,
)


STATE_RELATIVE_PATH = Path("ticket-autopilot/repository-merge-authority.json")
SCHEDULER_LOCK_RELATIVE_PATH = Path("ticket-autopilot/repository-merge-all.lock")
ADOPTION_PREFIX = "repository-autonomous-merge:"
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_GRANT_ID = re.compile(r"^rma-[0-9a-f]{20}$")


class RepositoryMergeAuthorityError(RuntimeError):
    """Repository merge authority is absent, contradictory, corrupt, or unsafe."""


_MERGE_KIND = AuthorityKind(
    name="merge",
    grant_prefix="rma",
    state_relative_path=STATE_RELATIVE_PATH,
    grant_event="repository-autonomous-merge-granted",
    revoke_event="repository-autonomous-merge-revoked",
    error_type=RepositoryMergeAuthorityError,
)


class RepositoryMergeAuthorityStore(RepositoryAuthorityStore):
    """Worktree-stable merge authority serialized by one Git-common lock."""

    def __init__(self, repository: Path):
        super().__init__(repository, _MERGE_KIND)
        self.scheduler_lock_path = (
            Path(self.binding.git_common_dir) / SCHEDULER_LOCK_RELATIVE_PATH
        )

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
    def adoption_evidence(grant: dict[str, Any]) -> str:
        return f"{ADOPTION_PREFIX}{grant['grant_id']}:{grant['grant_digest']}"

    def _assert_run_grant_unlocked(
        self, run_grant: dict[str, Any]
    ) -> dict[str, Any]:
        record = self._load_unlocked()
        if record is None or record[0]["schema"] == 1 or record[0]["revocation"] is not None:
            raise RepositoryMergeAuthorityError(
                "repository-wide autonomous merge authority is not active"
            )
        grant = record[0]["grant"]
        expected_evidence = self.adoption_evidence(grant)
        if (
            not isinstance(run_grant, dict)
            or run_grant.get("repository_identity")
            != self.binding.observed_repository_root
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
        with self.locked():
            yield self._assert_run_grant_unlocked(run_grant)


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
