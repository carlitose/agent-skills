"""Fail-closed adoption and validation for prebuilt project-documentation candidates."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping
from urllib.parse import unquote

from .artifact_audit import audit_artifacts
from .candidate_contract import CandidateRef
from .docs_only_contract import (
    APPROVED_SCOPE,
    DOCS_ONLY_CONTRACT_VERSION,
    RECEIPT_LIMITATIONS,
    DocsOnlyError,
    canonical_bytes,
    normalize_docs_only_receipt,
    normalize_docs_only_request,
    sha256_document,
)
from .git_ops import GitError, run_git
FORBIDDEN_BASENAMES = {
    "agents.md",
    "claude.md",
    "instructions.md",
    "manifest.md",
    "prompt.md",
    "skill.md",
}
FORBIDDEN_PARTS = {
    ".git",
    ".github",
    ".openai",
    "agents",
    "build",
    "config",
    "configs",
    "dist",
    "generated",
    "manifests",
    "node_modules",
    "prompts",
    "scripts",
    "skills",
}
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
MANAGED_ARTIFACT_PREFIXES = (
    "docs/tickets/",
    "docs/specs/",
    "docs/research/",
)


@dataclass(frozen=True)
class DocsOnlyValidation:
    request: dict[str, Any]
    candidate: CandidateRef
    changed_paths: tuple[str, ...]
    checks: tuple[dict[str, Any], ...]
    evidence_path: str
    evidence_sha256: str
    request_sha256: str

    def receipt(self) -> dict[str, Any]:
        return {
            "contract_version": DOCS_ONLY_CONTRACT_VERSION,
            "status": "eligible",
            "request": self.request,
            "request_sha256": self.request_sha256,
            "candidate_ref": asdict(self.candidate),
            "changed_paths": list(self.changed_paths),
            "checks": [dict(item) for item in self.checks],
            "evidence": {
                "artifact": self.evidence_path,
                "sha256": self.evidence_sha256,
            },
            "leaf_interactions_avoided": 4,
            "limitations": list(RECEIPT_LIMITATIONS),
        }


def _git_result(worktree: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=worktree,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        check=False,
    )


def _assert_index_is_frozen(worktree: Path) -> None:
    unstaged = _git_result(worktree, "diff", "--quiet", "--ignore-submodules", "--")
    if unstaged.returncode == 1:
        raise DocsOnlyError("docs-only candidate has unstaged changes")
    if unstaged.returncode != 0:
        raise DocsOnlyError(unstaged.stderr.strip() or "Git could not inspect unstaged changes")
    status = run_git(
        worktree, "status", "--porcelain=v1", "--untracked-files=all"
    )
    for line in status.splitlines():
        if line.startswith("??") or len(line) < 3 or line[1] != " ":
            raise DocsOnlyError("docs-only candidate contains untracked or unstaged paths")


def _candidate_paths(worktree: Path, candidate: CandidateRef) -> list[str]:
    actual_tree = run_git(worktree, "write-tree")
    if actual_tree != candidate.candidate_tree_oid:
        raise DocsOnlyError("staged tree differs from candidate_tree_oid")
    encoded = run_git(
        worktree,
        "diff",
        "--name-only",
        "-z",
        candidate.base_tree_oid,
        candidate.candidate_tree_oid,
    )
    return sorted(path for path in encoded.split("\0") if path)


def _assert_path_policy(worktree: Path, candidate: CandidateRef, path: str) -> None:
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise DocsOnlyError(f"docs-only path escapes the repository: {path}")
    if pure.parts[0] != "docs" or pure.suffix.lower() != ".md":
        raise DocsOnlyError(f"path is outside approved documentation scope: {path}")
    lowered_parts = {part.lower() for part in pure.parts}
    if (
        pure.name.lower() in FORBIDDEN_BASENAMES
        or FORBIDDEN_PARTS.intersection(lowered_parts)
    ):
        raise DocsOnlyError(f"agent-executable or generated documentation is ineligible: {path}")
    if len(pure.parts) > 1 and pure.parts[1].lower() == "tickets":
        raise DocsOnlyError(f"ticket lifecycle artifacts are runner-owned, not adoptable: {path}")
    entry = run_git(worktree, "ls-tree", candidate.candidate_tree_oid, "--", path)
    match = re.fullmatch(r"(\d{6}) (\w+) ([0-9a-f]+)\t(.+)", entry)
    if match is None or match.group(1) != "100644" or match.group(2) != "blob":
        raise DocsOnlyError(f"docs-only path must be a regular non-executable blob: {path}")
    local = worktree / pure
    if local.is_symlink() or not local.is_file():
        raise DocsOnlyError(f"docs-only path is missing or not a regular file: {path}")
    try:
        local.resolve().relative_to((worktree / "docs").resolve())
    except ValueError as error:
        raise DocsOnlyError(f"docs-only path resolves outside docs: {path}") from error


def _read_candidate_text(worktree: Path, candidate: CandidateRef, path: str) -> str:
    try:
        return run_git(worktree, "show", f"{candidate.candidate_tree_oid}:{path}")
    except (GitError, UnicodeError) as error:
        raise DocsOnlyError(f"documentation is not readable UTF-8 Markdown: {path}") from error


def _check_links(
    worktree: Path,
    candidate: CandidateRef,
    path: str,
    text: str,
) -> int:
    checked = 0
    parent = PurePosixPath(path).parent
    for raw_target in LINK_PATTERN.findall(text):
        target = raw_target.strip().strip("<>").split(maxsplit=1)[0]
        if not target or target.startswith("#") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
            continue
        target = unquote(target.split("#", 1)[0])
        if not target:
            continue
        resolved = PurePosixPath(target) if target.startswith("/") else parent / target
        parts: list[str] = []
        for part in resolved.parts:
            if part in {"", ".", "/"}:
                continue
            if part == "..":
                if not parts:
                    raise DocsOnlyError(f"documentation link escapes repository: {path} -> {target}")
                parts.pop()
            else:
                parts.append(part)
        repo_target = PurePosixPath(*parts).as_posix()
        probe = _git_result(
            worktree,
            "cat-file",
            "-e",
            f"{candidate.candidate_tree_oid}:{repo_target}",
        )
        if probe.returncode != 0:
            raise DocsOnlyError(f"documentation link target is missing: {path} -> {target}")
        checked += 1
    return checked


def _diagnostic_paths(diagnostic: Mapping[str, Any]) -> set[str]:
    paths = set()
    path = diagnostic.get("path")
    if isinstance(path, str):
        paths.add(path)
    related = diagnostic.get("paths")
    if isinstance(related, list):
        paths.update(item for item in related if isinstance(item, str))
    return paths


def _audit_changed_managed_artifacts(
    worktree: Path, changed_paths: list[str]
) -> int:
    managed_paths = {
        path
        for path in changed_paths
        if path.startswith(MANAGED_ARTIFACT_PREFIXES)
    }
    if not managed_paths:
        return 0
    audit = audit_artifacts(worktree)
    relevant = [
        diagnostic
        for category in ("errors", "warnings")
        for diagnostic in audit[category]
        if managed_paths.intersection(_diagnostic_paths(diagnostic))
    ]
    if relevant:
        details = "; ".join(
            f"{item['code']} ({', '.join(sorted(_diagnostic_paths(item)))})"
            for item in relevant
        )
        raise DocsOnlyError(
            f"canonical artifact audit failed for changed managed artifacts: {details}"
        )
    return len(managed_paths)


def validate_docs_only_candidate(
    worktree: Path,
    ticket: Mapping[str, Any],
    request: Any,
    *,
    evidence_dir: Path,
    persist: bool = True,
) -> DocsOnlyValidation:
    normalized, candidate, expected_paths = normalize_docs_only_request(
        request, ticket=ticket
    )
    _assert_index_is_frozen(worktree)
    actual_paths = _candidate_paths(worktree, candidate)
    if actual_paths != expected_paths:
        raise DocsOnlyError("complete frozen diff differs from expected_changed_paths")
    patch_check = _git_result(
        worktree,
        "diff",
        "--check",
        candidate.base_tree_oid,
        candidate.candidate_tree_oid,
        "--",
    )
    if patch_check.returncode != 0:
        raise DocsOnlyError(patch_check.stderr.strip() or patch_check.stdout.strip() or "documentation patch integrity failed")
    links_checked = 0
    for path in actual_paths:
        _assert_path_policy(worktree, candidate, path)
        text = _read_candidate_text(worktree, candidate, path)
        links_checked += _check_links(worktree, candidate, path, text)
    managed_artifacts_checked = _audit_changed_managed_artifacts(
        worktree, actual_paths
    )
    checks = (
        {"id": "patch-integrity", "result": "pass", "paths": len(actual_paths)},
        {"id": "path-and-file-kind-policy", "result": "pass", "paths": len(actual_paths)},
        {"id": "markdown-utf8", "result": "pass", "paths": len(actual_paths)},
        {
            "id": "artifact-graph",
            "result": "pass",
            "managed_paths": managed_artifacts_checked,
        },
        {"id": "documentation-links", "result": "pass", "links_checked": links_checked},
    )
    evidence = {
        "schema": 1,
        "contract_version": DOCS_ONLY_CONTRACT_VERSION,
        "ticket_id": ticket["ticket_id"],
        "candidate_ref": asdict(candidate),
        "request_sha256": sha256_document(normalized),
        "changed_paths": actual_paths,
        "checks": list(checks),
        "claim_ceiling": "implementation-complete",
        "limitations": [
            "Deterministic documentation checks do not execute runtime behavior.",
            "No independent review, live-host, provider, deployment, or production claim is supported.",
        ],
    }
    evidence_bytes = canonical_bytes(evidence)
    evidence_sha = hashlib.sha256(evidence_bytes).hexdigest()
    evidence_path = evidence_dir / f"docs-only-{ticket['ticket_id']}-{evidence_sha}.json"
    if persist:
        evidence_dir.mkdir(parents=True, exist_ok=True)
        if evidence_path.exists() and evidence_path.read_bytes() != evidence_bytes:
            raise DocsOnlyError("content-addressed docs-only evidence is contradictory")
        if not evidence_path.exists():
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{evidence_path.name}.",
                dir=evidence_dir,
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(evidence_bytes)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_name, evidence_path)
            finally:
                try:
                    os.unlink(temporary_name)
                except FileNotFoundError:
                    pass
    return DocsOnlyValidation(
        request=normalized,
        candidate=candidate,
        changed_paths=tuple(actual_paths),
        checks=checks,
        evidence_path=str(evidence_path.resolve()),
        evidence_sha256=evidence_sha,
        request_sha256=evidence["request_sha256"],
    )


def revalidate_docs_only_receipt(
    worktree: Path,
    ticket: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    evidence_dir: Path,
) -> DocsOnlyValidation:
    normalize_docs_only_receipt(
        receipt,
        ticket=ticket,
        candidate=receipt.get("candidate_ref"),
    )
    validation = validate_docs_only_candidate(
        worktree,
        ticket,
        receipt["request"],
        evidence_dir=evidence_dir,
        persist=False,
    )
    if (
        receipt.get("request_sha256") != validation.request_sha256
        or receipt.get("candidate_ref") != asdict(validation.candidate)
        or receipt.get("changed_paths") != list(validation.changed_paths)
        or receipt.get("checks") != [dict(item) for item in validation.checks]
        or receipt.get("evidence", {}).get("sha256") != validation.evidence_sha256
        or receipt.get("evidence", {}).get("artifact") != validation.evidence_path
    ):
        raise DocsOnlyError("persisted docs-only receipt differs from current Git evidence")
    artifact = Path(validation.evidence_path)
    if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != validation.evidence_sha256:
        raise DocsOnlyError("persisted docs-only evidence is missing or corrupt")
    return validation


def docs_only_verification_bundle(
    ticket: Mapping[str, Any], validation: DocsOnlyValidation
) -> dict[str, Any]:
    candidate = asdict(validation.candidate)
    evidence_id = f"e-{ticket['ticket_id']}-docs-only"
    invariant_id = f"inv-{ticket['ticket_id']}-docs-scope"
    claim_id = f"claim-{ticket['ticket_id']}-docs-implementation"
    return {
        "contract_version": 2,
        "artifact_type": "verification-bundle",
        "ticket_id": ticket["ticket_id"],
        "ticket_envelope_ref": f"run://docs-only/{ticket['ticket_id']}",
        "candidate_ref": candidate,
        "stage_results": [
            {
                "id": f"stage-{ticket['ticket_id']}-implement",
                "stage": "implement",
                "result": "pass",
                "candidate_ref": candidate,
                "artifact": validation.evidence_path,
                "evidence_ids": [evidence_id],
                "invariant_ids": [invariant_id],
                "boundary_delta_ids": [],
                "gate_ids": [],
                "provider_record_ids": [],
                "limitations": ["Only the prebuilt project-documentation candidate was validated."],
            }
        ],
        "evidence": [
            {
                "id": evidence_id,
                "candidate_ref": candidate,
                "class": "static",
                "environment": "local-git-docs-only",
                "environment_scope": "local",
                "boundary_scope": "internal",
                "result": "pass",
                "critical": True,
                "supports_claim": "implementation-complete",
                "causal_coverage": "none",
                "injection_point": "frozen documentation diff",
                "observed_segment": "path policy, file kinds, patch integrity, Markdown readability, artifact metadata, and links",
                "artifact": validation.evidence_path,
                "limitations": ["Static documentation validation does not execute runtime behavior."],
            }
        ],
        "invariants": [
            {
                "id": invariant_id,
                "candidate_ref": candidate,
                "description": "The complete adopted diff remains inside the approved project-documentation scope and contains only regular Markdown blobs.",
                "status": "preserved",
                "impact": "high",
                "evidence_ids": [evidence_id],
                "authorization_ref": None,
            }
        ],
        "external_boundary_delta": [],
        "gates": [],
        "provider_records": [],
        "claims": [
            {
                "id": claim_id,
                "candidate_ref": candidate,
                "text": "The frozen project-documentation candidate satisfies the explicit docs-only adoption contract and deterministic documentation checks.",
                "kind": "implementation",
                "criticality": "high",
                "environment_scope": "local",
                "boundary_scope": "internal",
                "causal_chain": [
                    {"step": "freeze and stage the complete documentation diff", "controller": "codebase", "observed": True},
                    {"step": "validate exact paths, file kinds, patch integrity, metadata, and links", "controller": "codebase", "observed": True},
                ],
                "uncovered_segments": ["runtime behavior", "live hosts", "production deployment"],
                "status": "supported",
                "requested_claim": "implementation-complete",
                "evidence_ids": [evidence_id],
                "gate_ids": [],
            }
        ],
        "verification": {
            "candidate_ref": candidate,
            "implementation_status": "complete",
            "max_claim": "implementation-complete",
            "release_status": "eligible",
            "final_disposition": "implementation-complete",
            "evidence_ids": [evidence_id],
            "invariant_ids": [invariant_id],
            "boundary_delta_ids": [],
            "gate_ids": [],
            "provider_record_ids": [],
            "claim_ids": [claim_id],
            "blocking_gaps": [],
            "forbidden_claims": [
                "behavior-verified",
                "production-ready",
                "independent review performed",
                "live host behavior verified",
            ],
            "requested_operation": "report",
        },
    }
