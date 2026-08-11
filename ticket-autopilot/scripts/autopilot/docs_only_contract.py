"""Pure versioned contracts for docs-only candidate adoption and receipts."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from .candidate_contract import CandidateRef, semantic_candidate
from .ticket_contract import (
    CONTRACT_VERSION as TICKET_CONTRACT_VERSION,
    ContractError,
    normalize_ticket_envelope,
)


DOCS_ONLY_CONTRACT_VERSION = 1
APPROVED_SCOPE = {
    "roots": ["docs"],
    "extensions": [".md"],
    "excluded_roots": ["docs/tickets"],
    "allow_runner_completion_artifacts": True,
}
CHECK_IDS = (
    "patch-integrity",
    "path-and-file-kind-policy",
    "markdown-utf8",
    "artifact-graph",
    "documentation-links",
)
CHECKPOINT_PHASES = (
    "context-loaded",
    "bundle-built",
    "bundle-validated",
    "bundle-reduced",
    "handoff-ready",
)
RECEIPT_LIMITATIONS = (
    "Docs-only evidence supports documentation implementation only.",
    "Runtime behavior, independent review, live hosts, and production readiness are not verified.",
)


class DocsOnlyError(ValueError):
    """A docs-only request, receipt, or frozen candidate is ineligible."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_document(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _string_array(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise DocsOnlyError(f"{field} must be an array of non-empty strings")
    if value != sorted(set(value)):
        raise DocsOnlyError(f"{field} must be sorted and unique")
    return list(value)


def normalize_docs_only_request(
    request: Any,
    *,
    ticket: Mapping[str, Any],
) -> tuple[dict[str, Any], CandidateRef, list[str]]:
    if not isinstance(request, Mapping):
        raise DocsOnlyError("docs-only adoption request must be an object")
    required = {
        "contract_version",
        "ticket_envelope",
        "ticket_digest",
        "source_relative_path",
        "candidate_ref",
        "expected_changed_paths",
        "approved_documentation_scope",
    }
    if set(request) != required:
        raise DocsOnlyError("docs-only adoption request fields are invalid")
    if request["contract_version"] != DOCS_ONLY_CONTRACT_VERSION:
        raise DocsOnlyError("unsupported docs-only adoption contract_version")
    try:
        envelope = normalize_ticket_envelope(
            request["ticket_envelope"], source="docs-only request"
        )
    except ContractError as error:
        raise DocsOnlyError(str(error)) from error
    expected_envelope = normalize_ticket_envelope(
        {
            "ticket_schema": TICKET_CONTRACT_VERSION,
            "ticket_id": ticket["ticket_id"],
            "execution_mode": ticket["execution_mode"],
            "blocked_by": list(ticket["blocked_by"]),
        },
        source="normalized run ticket",
    )
    if envelope != expected_envelope:
        raise DocsOnlyError("ticket_envelope differs from the normalized run ticket")
    if request["ticket_digest"] != ticket["ticket_digest"]:
        raise DocsOnlyError("ticket_digest differs from the normalized run ticket")
    if request["source_relative_path"] != ticket["source_relative_path"]:
        raise DocsOnlyError(
            "source_relative_path differs from the normalized run ticket"
        )
    try:
        candidate = semantic_candidate(request["candidate_ref"])
    except ValueError as error:
        raise DocsOnlyError(str(error)) from error
    if candidate.ticket_digest != ticket["ticket_digest"]:
        raise DocsOnlyError("candidate ticket_digest differs from the run ticket")
    try:
        active_candidate = semantic_candidate(ticket.get("candidate_ref"))
    except ValueError as error:
        raise DocsOnlyError(
            "runner-owned active ticket CandidateRef is invalid"
        ) from error
    if candidate.base_tree_oid != active_candidate.base_tree_oid:
        raise DocsOnlyError(
            "candidate base_tree_oid differs from the runner-owned active ticket CandidateRef"
        )
    if request["approved_documentation_scope"] != APPROVED_SCOPE:
        raise DocsOnlyError("approved_documentation_scope is not the canonical policy")
    expected_paths = _string_array(
        request["expected_changed_paths"], "expected_changed_paths"
    )
    if not expected_paths:
        raise DocsOnlyError("docs-only candidate must change at least one path")
    normalized = {
        "contract_version": DOCS_ONLY_CONTRACT_VERSION,
        "ticket_envelope": expected_envelope,
        "ticket_digest": ticket["ticket_digest"],
        "source_relative_path": ticket["source_relative_path"],
        "candidate_ref": asdict(candidate),
        "expected_changed_paths": expected_paths,
        "approved_documentation_scope": copy.deepcopy(APPROVED_SCOPE),
    }
    return normalized, candidate, expected_paths


def normalize_docs_only_receipt(
    receipt: Any,
    *,
    ticket: Mapping[str, Any],
    candidate: Any,
) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise DocsOnlyError("docs-only receipt must be an object")
    required = {
        "contract_version",
        "status",
        "request",
        "request_sha256",
        "candidate_ref",
        "changed_paths",
        "checks",
        "evidence",
        "leaf_interactions_avoided",
        "limitations",
        "checkpoint",
    }
    if set(receipt) != required:
        raise DocsOnlyError("docs-only receipt fields are invalid")
    if (
        receipt["contract_version"] != DOCS_ONLY_CONTRACT_VERSION
        or receipt["status"] != "eligible"
    ):
        raise DocsOnlyError("docs-only receipt is not eligible")
    normalized_request, request_candidate, expected_paths = normalize_docs_only_request(
        receipt["request"], ticket=ticket
    )
    try:
        candidate_document = asdict(semantic_candidate(candidate))
    except ValueError as error:
        raise DocsOnlyError(str(error)) from error
    if (
        receipt["request"] != normalized_request
        or asdict(request_candidate) != candidate_document
        or receipt["candidate_ref"] != candidate_document
        or receipt["request_sha256"] != sha256_document(normalized_request)
        or receipt["changed_paths"] != expected_paths
    ):
        raise DocsOnlyError("docs-only receipt candidate binding is invalid")
    checks = receipt["checks"]
    if (
        not isinstance(checks, list)
        or len(checks) != len(CHECK_IDS)
        or tuple(
            item.get("id") for item in checks if isinstance(item, Mapping)
        )
        != CHECK_IDS
        or any(
            not isinstance(item, Mapping) or item.get("result") != "pass"
            for item in checks
        )
    ):
        raise DocsOnlyError("docs-only receipt checks are invalid")
    evidence = receipt["evidence"]
    if (
        not isinstance(evidence, Mapping)
        or set(evidence) != {"artifact", "sha256"}
        or not isinstance(evidence["artifact"], str)
        or not evidence["artifact"]
        or not Path(evidence["artifact"]).is_absolute()
        or not _is_sha256(evidence["sha256"])
    ):
        raise DocsOnlyError("docs-only receipt evidence is invalid")
    if (
        receipt["leaf_interactions_avoided"] != 4
        or receipt["limitations"] != list(RECEIPT_LIMITATIONS)
    ):
        raise DocsOnlyError("docs-only receipt accounting or limitations are invalid")
    checkpoint = receipt["checkpoint"]
    if (
        not isinstance(checkpoint, Mapping)
        or set(checkpoint) != {"input_hash", "artifact_hashes", "phases_complete"}
        or not _is_sha256(checkpoint["input_hash"])
        or not isinstance(checkpoint["artifact_hashes"], Mapping)
        or set(checkpoint["artifact_hashes"]) != set(CHECKPOINT_PHASES)
        or any(
            not _is_sha256(value) for value in checkpoint["artifact_hashes"].values()
        )
        or checkpoint["phases_complete"] != list(CHECKPOINT_PHASES)
    ):
        raise DocsOnlyError("docs-only receipt checkpoint is invalid")
    return copy.deepcopy(dict(receipt))
