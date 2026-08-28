"""Disposable logic model for WS-02. This is not production code."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath


class Outcome(str, Enum):
    ABSENT = "noop-absent"
    UNCHANGED = "unchanged"
    DIRECT_VALIDATED = "direct-write-validated"
    TRACKED_CANDIDATE = "tracked-candidate"
    AMBIGUOUS_ROOT = "error-ambiguous-root"
    BROKEN_BINDING = "error-broken-binding"
    PARTIAL_TRACKING = "error-partial-tracking"
    FORBIDDEN_SCOPE = "error-forbidden-scope"
    LINT_FAILED = "error-lint-failed"
    STALE_IDENTITY = "error-stale-identity"
    UNSAFE_POLICY = "error-unsafe-caller-policy"


class RequestDesign(str, Enum):
    VERSIONED_PROFILE = "docs-only-v2-profile"
    SEPARATE_REQUEST = "wiki-sync-v1-request"
    CALLER_ALLOWLIST = "caller-owned-allowlist"


class IdentityDesign(str, Enum):
    REUSE_ORIGIN = "reuse-origin-candidate"
    SYNTHETIC_TICKET = "fresh-synthetic-sync-ticket"
    COMPLETION_EFFECT = "fresh-completion-effect"


@dataclass(frozen=True)
class CandidateRef:
    base_tree_oid: str
    candidate_tree_oid: str
    ticket_digest: str
    contract_version: int = 2


@dataclass(frozen=True)
class FileChange:
    path: str
    kind: str = "regular"
    executable: bool = False


@dataclass(frozen=True)
class Probe:
    roots: tuple[str, ...]
    changes: tuple[FileChange, ...] = ()
    tracked_paths: frozenset[str] = frozenset()
    binding_ok: bool = True
    lint_ok: bool = True
    before_tree_oid: str = "tree-before"
    after_tree_oid: str = "tree-after"


@dataclass(frozen=True)
class SyncResult:
    outcome: Outcome
    protected_tree_oid: str
    detail: str
    candidate_ref: CandidateRef | None = None


@dataclass(frozen=True)
class DesignAssessment:
    design: RequestDesign
    viable: bool
    policy_owner: str
    counterexample: str | None


def _rejected(probe: Probe, outcome: Outcome, detail: str) -> SyncResult:
    return SyncResult(outcome, probe.before_tree_oid, detail)


def _generated_markdown(change: FileChange) -> bool:
    path = PurePosixPath(change.path)
    return (
        change.kind == "regular"
        and not change.executable
        and not path.is_absolute()
        and ".." not in path.parts
        and len(path.parts) >= 2
        and path.parts[0] == "wiki"
        and path.suffix == ".md"
    )


def _fresh_candidate(
    probe: Probe,
    root: str,
    origin: CandidateRef,
    identity: IdentityDesign,
) -> CandidateRef | None:
    if identity is IdentityDesign.REUSE_ORIGIN:
        return None
    identity_material = f"{identity.value}:{root}:{origin.ticket_digest}"
    return CandidateRef(
        base_tree_oid=probe.before_tree_oid,
        candidate_tree_oid=probe.after_tree_oid,
        ticket_digest=hashlib.sha256(identity_material.encode()).hexdigest(),
    )


def classify(
    probe: Probe,
    origin: CandidateRef,
    *,
    request_design: RequestDesign = RequestDesign.SEPARATE_REQUEST,
    identity_design: IdentityDesign = IdentityDesign.COMPLETION_EFFECT,
) -> SyncResult:
    """Classify one proposed sync while keeping rejected protected trees unchanged."""

    if not probe.roots:
        return _rejected(probe, Outcome.ABSENT, "No compatible wiki root was found.")
    if len(probe.roots) != 1:
        return _rejected(
            probe,
            Outcome.AMBIGUOUS_ROOT,
            "Discovery must resolve exactly one compatible wiki root.",
        )
    if not probe.binding_ok:
        return _rejected(
            probe,
            Outcome.BROKEN_BINDING,
            "The selected wiki binding does not resolve to this project.",
        )
    if request_design is RequestDesign.CALLER_ALLOWLIST:
        return _rejected(
            probe,
            Outcome.UNSAFE_POLICY,
            "A caller-owned allowlist cannot prove one canonical docs-only scope.",
        )
    if not probe.changes:
        return SyncResult(
            Outcome.UNCHANGED,
            probe.before_tree_oid,
            "The compiler produced no file changes.",
        )
    invalid = [change.path for change in probe.changes if not _generated_markdown(change)]
    if invalid:
        return _rejected(
            probe,
            Outcome.FORBIDDEN_SCOPE,
            "Forbidden candidate paths: " + ", ".join(sorted(invalid)),
        )
    if not probe.lint_ok:
        return _rejected(
            probe,
            Outcome.LINT_FAILED,
            "Generated Markdown did not pass the wiki lint boundary.",
        )

    changed_paths = {change.path for change in probe.changes}
    tracked = changed_paths & set(probe.tracked_paths)
    if tracked and tracked != changed_paths:
        return _rejected(
            probe,
            Outcome.PARTIAL_TRACKING,
            "Generated output is only partially tracked.",
        )
    if not tracked:
        return SyncResult(
            Outcome.DIRECT_VALIDATED,
            probe.after_tree_oid,
            "Untracked generated Markdown may be written directly after validation.",
        )

    candidate = _fresh_candidate(probe, probe.roots[0], origin, identity_design)
    if candidate is None:
        return _rejected(
            probe,
            Outcome.STALE_IDENTITY,
            "An integrated origin CandidateRef cannot own a later wiki candidate.",
        )
    return SyncResult(
        Outcome.TRACKED_CANDIDATE,
        probe.before_tree_oid,
        "Tracked output is isolated as a fresh docs-only candidate.",
        candidate,
    )


def assess_designs() -> tuple[DesignAssessment, ...]:
    return (
        DesignAssessment(
            RequestDesign.VERSIONED_PROFILE,
            True,
            "docs-only contract",
            None,
        ),
        DesignAssessment(
            RequestDesign.SEPARATE_REQUEST,
            True,
            "wiki-sync contract using shared static validators",
            None,
        ),
        DesignAssessment(
            RequestDesign.CALLER_ALLOWLIST,
            False,
            "caller",
            "The caller can add llm-wiki-project.json or raw/sources/* to its allowlist.",
        ),
    )


def scenario_matrix() -> dict[str, Probe]:
    generated = (
        FileChange("wiki/index.md"),
        FileChange("wiki/concepts/docs-only-sync.md"),
        FileChange("wiki/log.md"),
    )
    all_tracked = frozenset(change.path for change in generated)
    return {
        "absent": Probe(()),
        "unchanged": Probe(("knowledge",)),
        "untracked": Probe(("knowledge",), generated),
        "tracked": Probe(("knowledge",), generated, all_tracked),
        "partial": Probe(
            ("knowledge",), generated, frozenset({"wiki/index.md"})
        ),
        "multiple": Probe(("wiki-a", "wiki-b"), generated),
        "broken": Probe(("knowledge",), generated, binding_ok=False),
        "mixed-code": Probe(
            ("knowledge",), generated + (FileChange("src/app.py"),)
        ),
        "configuration-wiki": Probe(
            ("knowledge",),
            generated + (FileChange("llm-wiki-project.json"),),
        ),
        "ticket-source": Probe(
            ("knowledge",),
            generated + (FileChange("docs/tickets/01.md"),),
        ),
        "raw-binary": Probe(
            ("knowledge",),
            generated + (FileChange("raw/sources/paper.pdf"),),
        ),
        "lint-failed": Probe(("knowledge",), generated, lint_ok=False),
    }
