"""Canonical semantic-candidate and delivery-lineage contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping


CANDIDATE_CONTRACT_VERSION = 2
DELIVERY_LINEAGE_CONTRACT_VERSION = 1


class CandidateContractError(ValueError):
    """A candidate or delivery-lineage record violates its versioned contract."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CandidateContractError(f"{field} must be a non-empty string")
    return value


@dataclass(frozen=True)
class SemanticCandidateRef:
    base_tree_oid: str
    candidate_tree_oid: str
    ticket_digest: str
    contract_version: int = CANDIDATE_CONTRACT_VERSION

    def validate(self) -> None:
        if type(self.contract_version) is not int or (
            self.contract_version != CANDIDATE_CONTRACT_VERSION
        ):
            raise CandidateContractError(
                "unsupported semantic candidate contract_version; "
                "start a new run with CandidateRef v2"
            )
        _text(self.base_tree_oid, "base_tree_oid")
        _text(self.candidate_tree_oid, "candidate_tree_oid")
        _text(self.ticket_digest, "ticket_digest")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @property
    def digest(self) -> str:
        encoded = json.dumps(
            self.as_dict(), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DeliveryLineage:
    provider: str
    pr_id: str
    branch: str
    base_branch: str
    base_sha: str
    head_sha: str
    contract_version: int = DELIVERY_LINEAGE_CONTRACT_VERSION

    def validate(self) -> None:
        if type(self.contract_version) is not int or (
            self.contract_version != DELIVERY_LINEAGE_CONTRACT_VERSION
        ):
            raise CandidateContractError(
                "unsupported delivery lineage contract_version"
            )
        for field in (
            "provider",
            "pr_id",
            "branch",
            "base_branch",
            "base_sha",
            "head_sha",
        ):
            _text(getattr(self, field), field)

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def semantic_candidate(value: Any) -> SemanticCandidateRef:
    if isinstance(value, SemanticCandidateRef):
        value.validate()
        return value
    if not isinstance(value, Mapping):
        raise CandidateContractError("semantic candidate must be an object")
    required = {
        "base_tree_oid",
        "candidate_tree_oid",
        "ticket_digest",
        "contract_version",
    }
    if set(value) != required:
        raise CandidateContractError(
            "semantic candidate fields are invalid; CandidateRef v1 is incompatible"
        )
    candidate = SemanticCandidateRef(
        base_tree_oid=value["base_tree_oid"],
        candidate_tree_oid=value["candidate_tree_oid"],
        ticket_digest=value["ticket_digest"],
        contract_version=value["contract_version"],
    )
    candidate.validate()
    return candidate


def delivery_lineage(value: Any) -> DeliveryLineage:
    if isinstance(value, DeliveryLineage):
        value.validate()
        return value
    if not isinstance(value, Mapping):
        raise CandidateContractError("delivery lineage must be an object")
    required = {
        "provider",
        "pr_id",
        "branch",
        "base_branch",
        "base_sha",
        "head_sha",
        "contract_version",
    }
    if set(value) != required:
        raise CandidateContractError("delivery lineage fields are invalid")
    lineage = DeliveryLineage(
        provider=value["provider"],
        pr_id=value["pr_id"],
        branch=value["branch"],
        base_branch=value["base_branch"],
        base_sha=value["base_sha"],
        head_sha=value["head_sha"],
        contract_version=value["contract_version"],
    )
    lineage.validate()
    return lineage


CandidateRef = SemanticCandidateRef
