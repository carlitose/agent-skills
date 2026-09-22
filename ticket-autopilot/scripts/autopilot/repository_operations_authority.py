"""Durable, revocable authority for the repeatable delivery operations of one repository.

Merge and reconciliation already have their own repository-wide authority, each with its own
grant, provenance and revocation. Everything else an operator repeatedly consents to during
delivery — publishing a pull request, moving the owned local install to an integrated head,
asking the host for a reload — has lived only in conversation: nothing durable to point at,
nothing to revoke, nothing that survives a compaction.

This module gives those operations the same treatment, with one difference that matters: the
covered operations are a closed list pinned to a policy version. An authority whose scope
cannot be enumerated afterwards is indistinguishable from no authority at all, so widening the
list requires a new policy version and a fresh human decision rather than a silent upgrade.

What this authority never covers, in any version: another repository, anything outside the
repository, destructive or rewriting operations, and anything about proof. It answers "may
I", never "is it proven".
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .repository_authority import AuthorityKind, RepositoryAuthorityStore
from .repository_merge_authority import RepositoryMergeAuthorityStore
from .repository_reconciliation_authority import RepositoryReconciliationAuthorityStore

STATE_RELATIVE_PATH = Path("ticket-autopilot/repository-operations-authority.json")
ADOPTION_PREFIX = "repository-autonomous-operations:"
OPERATIONS_POLICY_VERSION = 1

# Closed list for policy version 1. Each entry names an operation an operator would otherwise
# authorize again in every session.
OPERATIONS_CAPABILITIES: tuple[str, ...] = (
    "publish-pr",
    "sync-local-install",
    "request-runtime-reload",
)

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_GRANT_ID = re.compile(r"^roa-[0-9a-f]{20}$")


class RepositoryOperationsAuthorityError(RuntimeError):
    """Operational authority is absent, revoked, contradictory, corrupt, or too narrow."""


_OPERATIONS_KIND = AuthorityKind(
    name="operations",
    grant_prefix="roa",
    state_relative_path=STATE_RELATIVE_PATH,
    grant_event="repository-autonomous-operations-granted",
    revoke_event="repository-autonomous-operations-revoked",
    error_type=RepositoryOperationsAuthorityError,
    policy_version=OPERATIONS_POLICY_VERSION,
)


class RepositoryOperationsAuthorityStore(RepositoryAuthorityStore):
    """Worktree-stable operational authority over a closed list of capabilities."""

    def __init__(self, repository: Path):
        super().__init__(repository, _OPERATIONS_KIND)

    @staticmethod
    def adoption_evidence(grant: dict[str, Any]) -> str:
        return f"{ADOPTION_PREFIX}{grant['grant_id']}:{grant['grant_digest']}"

    def inspect(self) -> dict[str, Any]:
        """Report the authority and the list it is pinned to, so scope is never implicit."""

        return {
            **super().inspect(),
            "policy_version": OPERATIONS_POLICY_VERSION,
            "capabilities": list(OPERATIONS_CAPABILITIES),
        }

    def _assert_capability_unlocked(
        self, run_grant: dict[str, Any], capability: str
    ) -> dict[str, Any]:
        if capability not in OPERATIONS_CAPABILITIES:
            raise RepositoryOperationsAuthorityError(
                f"{capability!r} is not covered by repository operational authority "
                f"policy version {OPERATIONS_POLICY_VERSION}: "
                f"{', '.join(OPERATIONS_CAPABILITIES)}"
            )
        record = self._load_unlocked()
        if record is None or record[0]["schema"] == 1 or record[0]["revocation"] is not None:
            raise RepositoryOperationsAuthorityError(
                "repository-wide operational authority is not active"
            )
        grant = record[0]["grant"]
        if (
            not isinstance(run_grant, dict)
            or run_grant.get("repository_identity")
            != self.binding.observed_repository_root
            or run_grant.get("provider") != self.binding.provider
            or run_grant.get("actor") != grant["actor"]
            or run_grant.get("evidence") != self.adoption_evidence(grant)
        ):
            raise RepositoryOperationsAuthorityError(
                "run operational grant does not match active repository authority"
            )
        return grant

    def assert_capability(
        self, run_grant: dict[str, Any], capability: str
    ) -> dict[str, Any]:
        with self.locked():
            return self._assert_capability_unlocked(run_grant, capability)

    @contextmanager
    def guard_capability(
        self, run_grant: dict[str, Any], capability: str
    ) -> Iterator[dict[str, Any]]:
        with self.locked():
            yield self._assert_capability_unlocked(run_grant, capability)


def is_repository_adoption_evidence(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith(ADOPTION_PREFIX):
        return False
    parts = value[len(ADOPTION_PREFIX) :].split(":")
    return (
        len(parts) == 2
        and _GRANT_ID.fullmatch(parts[0]) is not None
        and _HEX_64.fullmatch(parts[1]) is not None
    )


def repository_authority_status(repository: Path) -> dict[str, Any]:
    """Report every repository-wide authority in one read, granting nothing.

    "Authorize everything" is answered by three separate transactions, so the operator needs
    one place that says what is actually active and what each part covers.
    """

    return {
        "merge": RepositoryMergeAuthorityStore(repository).inspect(),
        "reconciliation": RepositoryReconciliationAuthorityStore(repository).inspect(),
        "operations": RepositoryOperationsAuthorityStore(repository).inspect(),
    }
