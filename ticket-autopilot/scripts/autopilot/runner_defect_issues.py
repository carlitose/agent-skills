"""Audited, repository-bound publication of deterministic runner defects.

This lifecycle is deliberately orthogonal to the ticket-autopilot run ledger.  Its
only durable state is an independently locked authority registry and one integrity-
wrapped outbox document per stable defect fingerprint under the Git common directory.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Protocol
from urllib.parse import urlparse

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import common_git_dir, origin_url, run_directory
from .ledger import AtomicLedger
from .providers import (
    CREATE_RUNNER_DEFECT_ISSUE,
    GET_RUNNER_DEFECT_ISSUE,
    SEARCH_RUNNER_DEFECT_ISSUES,
    ProviderError,
    ProviderExecutor,
)

TARGET_REPOSITORY = "carlitose/agent-skills"
TARGET_PROVIDER = "github"
AUTHORITY_SCHEMA = 1
AUTHORITY_POLICY_VERSION = 1
OUTBOX_SCHEMA = 1
DEFECT_SCHEMA = 1
MARKER_PREFIX = "<!-- ticket-autopilot-runner-defect:v1:"
FINAL_STATES = frozenset({"published", "deduplicated"})

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"https?://[^/\s:@]+:[^/\s@]+@"),
    re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\\\Users\\\\)"),
)


class RunnerDefectError(RuntimeError):
    """The defect record, authority, provider evidence, or outbox is unsafe."""


class SimulatedIssueCrash(RuntimeError):
    """Test-only crash point after durable lifecycle state has been written."""


@dataclass(frozen=True)
class EscalationResult:
    fingerprint: str
    state: str
    disposition: str | None
    outbox_sha256: str | None
    receipt: dict[str, Any] | None


class IssueAdapter(Protocol):
    def search_exact(self, repository: str, fingerprint: str) -> dict[str, Any]: ...

    def create(
        self, repository: str, fingerprint: str, title: str, body: str
    ) -> dict[str, Any]: ...


class GitHubIssueAdapter:
    """Exact GitHub issue search/create seam backed by normalized provider operations."""

    def __init__(self, executor: ProviderExecutor):
        self.executor = executor

    def search_exact(self, repository: str, fingerprint: str) -> dict[str, Any]:
        return self.executor.execute(
            SEARCH_RUNNER_DEFECT_ISSUES,
            repository=repository,
            fingerprint=fingerprint,
        )

    def create(
        self, repository: str, fingerprint: str, title: str, body: str
    ) -> dict[str, Any]:
        return self.executor.execute(
            CREATE_RUNNER_DEFECT_ISSUE,
            repository=repository,
            fingerprint=fingerprint,
            title=title,
            body=body,
            label="bug",
        )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_tmp = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        tmp.unlink(missing_ok=True)


def _wrap(document: dict[str, Any]) -> bytes:
    envelope = {
        "envelope_schema": 1,
        "integrity": _digest(document),
        "payload": document,
    }
    return _canonical_bytes(envelope) + b"\n"


def _unwrap(raw: bytes, *, kind: str) -> dict[str, Any]:
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RunnerDefectError(f"{kind} is not valid JSON") from error
    if (
        not isinstance(envelope, dict)
        or set(envelope) != {"envelope_schema", "integrity", "payload"}
        or envelope.get("envelope_schema") != 1
        or not isinstance(envelope.get("payload"), dict)
        or envelope.get("integrity") != _digest(envelope["payload"])
    ):
        raise RunnerDefectError(f"{kind} integrity envelope is invalid")
    return envelope["payload"]


class _LockedDocument:
    def __init__(self, path: Path, *, kind: str):
        self.path = path
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        self.kind = kind
        self._lock_depth = 0

    @contextmanager
    def locked(self) -> Iterator[None]:
        if self._lock_depth:
            self._lock_depth += 1
            try:
                yield
            finally:
                self._lock_depth -= 1
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="ascii") as handle:
            try:
                acquire_file_lock(handle, blocking=False)
            except OSError as error:
                raise RunnerDefectError(f"{self.kind} is locked: {self.lock_path}") from error
            try:
                self._lock_depth = 1
                yield
            finally:
                self._lock_depth = 0
                release_file_lock(handle)

    def read_unlocked(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        return _unwrap(self.path.read_bytes(), kind=self.kind)

    def write_unlocked(self, document: dict[str, Any]) -> None:
        _atomic_write(self.path, _wrap(document))
        if self.read_unlocked() != document:
            raise RunnerDefectError(f"{self.kind} readback mismatch")


class PublicationAuthority:
    """Repository-scoped, explicitly revocable publication authority."""

    def __init__(self, repo: Path):
        self.store = _LockedDocument(
            common_git_dir(repo)
            / "ticket-autopilot"
            / "runner-defect-issue-publication-authority.json",
            kind="runner-defect publication authority",
        )

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "schema": AUTHORITY_SCHEMA,
            "policy_version": AUTHORITY_POLICY_VERSION,
            "repository": TARGET_REPOSITORY,
            "provider": TARGET_PROVIDER,
            "grants": [],
            "revocations": [],
        }

    @staticmethod
    def _validate(document: dict[str, Any]) -> None:
        if (
            set(document)
            != {
                "schema",
                "policy_version",
                "repository",
                "provider",
                "grants",
                "revocations",
            }
            or document.get("schema") != AUTHORITY_SCHEMA
            or document.get("policy_version") != AUTHORITY_POLICY_VERSION
            or document.get("repository") != TARGET_REPOSITORY
            or document.get("provider") != TARGET_PROVIDER
            or not isinstance(document.get("grants"), list)
            or not isinstance(document.get("revocations"), list)
        ):
            raise RunnerDefectError("publication authority schema is invalid")
        grant_ids: set[str] = set()
        for grant in document["grants"]:
            if (
                not isinstance(grant, dict)
                or set(grant)
                != {
                    "schema",
                    "policy_version",
                    "authority_id",
                    "repository",
                    "provider",
                    "actor",
                    "evidence",
                }
                or grant.get("schema") != 1
                or grant.get("policy_version") != AUTHORITY_POLICY_VERSION
                or grant.get("repository") != TARGET_REPOSITORY
                or grant.get("provider") != TARGET_PROVIDER
                or not _nonempty(grant.get("actor"))
                or not _nonempty(grant.get("evidence"))
            ):
                raise RunnerDefectError("publication grant is invalid")
            expected = "rdip-" + _digest(
                {
                    "repository": TARGET_REPOSITORY,
                    "provider": TARGET_PROVIDER,
                    "actor": grant["actor"],
                    "evidence": grant["evidence"],
                    "policy_version": AUTHORITY_POLICY_VERSION,
                }
            )[:24]
            if grant.get("authority_id") != expected or expected in grant_ids:
                raise RunnerDefectError("publication grant identity is invalid")
            grant_ids.add(expected)
        revoked: set[str] = set()
        for revocation in document["revocations"]:
            if (
                not isinstance(revocation, dict)
                or set(revocation)
                != {"schema", "authority_id", "actor", "evidence"}
                or revocation.get("schema") != 1
                or revocation.get("authority_id") not in grant_ids
                or revocation.get("authority_id") in revoked
                or not _nonempty(revocation.get("actor"))
                or not _nonempty(revocation.get("evidence"))
            ):
                raise RunnerDefectError("publication revocation is invalid")
            revoked.add(revocation["authority_id"])
        active = [grant for grant in document["grants"] if grant["authority_id"] not in revoked]
        if len(active) > 1:
            raise RunnerDefectError("publication authority has multiple active grants")

    def _read_unlocked(self) -> dict[str, Any]:
        document = self.store.read_unlocked() or self._empty()
        self._validate(document)
        return document

    @staticmethod
    def _active(document: dict[str, Any]) -> dict[str, Any] | None:
        revoked = {item["authority_id"] for item in document["revocations"]}
        active = [item for item in document["grants"] if item["authority_id"] not in revoked]
        return active[0] if active else None

    def inspect(self) -> dict[str, Any]:
        with self.store.locked():
            document = self._read_unlocked()
            return {
                "schema": 1,
                "repository": TARGET_REPOSITORY,
                "provider": TARGET_PROVIDER,
                "active_grant": self._active(document),
                "grant_count": len(document["grants"]),
                "revocation_count": len(document["revocations"]),
            }

    def grant(self, *, actor: str, evidence: str) -> dict[str, Any]:
        actor = _authority_text(actor, "actor")
        evidence = _authority_text(evidence, "evidence")
        authority_id = "rdip-" + _digest(
            {
                "repository": TARGET_REPOSITORY,
                "provider": TARGET_PROVIDER,
                "actor": actor,
                "evidence": evidence,
                "policy_version": AUTHORITY_POLICY_VERSION,
            }
        )[:24]
        grant = {
            "schema": 1,
            "policy_version": AUTHORITY_POLICY_VERSION,
            "authority_id": authority_id,
            "repository": TARGET_REPOSITORY,
            "provider": TARGET_PROVIDER,
            "actor": actor,
            "evidence": evidence,
        }
        with self.store.locked():
            document = self._read_unlocked()
            active = self._active(document)
            if active is not None:
                if active == grant:
                    return active
                raise RunnerDefectError("a distinct publication grant is already active")
            existing = next(
                (item for item in document["grants"] if item["authority_id"] == authority_id),
                None,
            )
            if existing is not None:
                raise RunnerDefectError("the identical publication grant was revoked")
            document["grants"].append(grant)
            self._validate(document)
            self.store.write_unlocked(document)
            return grant

    def revoke(
        self, *, authority_id: str, actor: str, evidence: str
    ) -> dict[str, Any]:
        actor = _authority_text(actor, "actor")
        evidence = _authority_text(evidence, "evidence")
        with self.store.locked():
            document = self._read_unlocked()
            active = self._active(document)
            if active is None or active["authority_id"] != authority_id:
                raise RunnerDefectError("revocation does not name the exact active grant")
            revocation = {
                "schema": 1,
                "authority_id": authority_id,
                "actor": actor,
                "evidence": evidence,
            }
            document["revocations"].append(revocation)
            self._validate(document)
            self.store.write_unlocked(document)
            return revocation

    def require_active(self, authority_id: str | None = None) -> dict[str, Any]:
        with self.store.locked():
            return self.require_active_unlocked(authority_id)

    def require_active_unlocked(
        self, authority_id: str | None = None
    ) -> dict[str, Any]:
        document = self._read_unlocked()
        active = self._active(document)
        if active is None:
            raise RunnerDefectError("runner-defect issue publication is not authorized")
        if authority_id is not None and active["authority_id"] != authority_id:
            raise RunnerDefectError("runner-defect publication grant is stale")
        return active


class IssueOutbox:
    def __init__(self, repo: Path):
        self.root = (
            common_git_dir(repo)
            / "ticket-autopilot"
            / "runner-defect-issue-publication"
            / "outbox"
        )

    def document(self, fingerprint: str) -> _LockedDocument:
        if not _HEX_64.fullmatch(fingerprint):
            raise RunnerDefectError("defect fingerprint is invalid")
        return _LockedDocument(
            self.root / f"{fingerprint}.json",
            kind=f"runner-defect outbox {fingerprint}",
        )


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _authority_text(value: Any, field: str) -> str:
    if (
        not _nonempty(value)
        or len(value) > 1000
        or "\n" in value
        or "\r" in value
        or _CONTROL.search(value)
    ):
        raise RunnerDefectError(f"publication {field} must be non-empty safe text")
    return value


def _safe_text(value: Any, path: str, *, maximum: int = 500) -> str:
    if (
        not _nonempty(value)
        or len(value) > maximum
        or "\n" in value
        or "\r" in value
        or _CONTROL.search(value)
        or any(character in value for character in "`<>[]")
    ):
        raise RunnerDefectError(
            f"{path} must be one non-empty sanitized plain-text line"
        )
    for pattern in _SECRET_PATTERNS:
        if pattern.search(value):
            raise RunnerDefectError(f"{path} contains secret or local-path material")
    return value


def _safe_token(value: Any, path: str) -> str:
    value = _safe_text(value, path, maximum=200)
    if not _SAFE_TOKEN.fullmatch(value):
        raise RunnerDefectError(f"{path} is not a safe diagnostic token")
    return value


def _sha(value: Any, path: str) -> str:
    if not isinstance(value, str) or not _HEX_64.fullmatch(value):
        raise RunnerDefectError(f"{path} must be a lowercase SHA-256 digest")
    return value


def target_repository_from_remote(remote: str) -> str:
    """Return a normalized owner/repository identity without accepting lookalikes."""

    value = remote.strip()
    if not value:
        raise RunnerDefectError("repository origin is absent")
    if value.startswith("git@github.com:"):
        path = value.split(":", 1)[1]
    else:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https", "ssh", "git"}:
            raise RunnerDefectError("repository origin is not a supported GitHub URL")
        if (parsed.hostname or "").casefold() != "github.com":
            raise RunnerDefectError("runner-defect publication requires github.com origin")
        path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if path != TARGET_REPOSITORY:
        raise RunnerDefectError(
            f"runner-defect publication target must be exactly {TARGET_REPOSITORY}"
        )
    return path


def assert_target_repository(repo: Path) -> str:
    return target_repository_from_remote(origin_url(repo) or "")


def validate_defect_record(
    value: Any,
    *,
    run_id: str,
    ledger_sha256: str,
    ledger: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "classification",
        "repository",
        "run_binding",
        "owner",
        "failure",
        "confidence",
        "feedback_loop",
        "evidence",
        "redaction",
    }:
        raise RunnerDefectError("runner-defect record schema is invalid")
    if (
        value.get("schema") != DEFECT_SCHEMA
        or value.get("classification") != "runner-defect"
        or value.get("repository") != TARGET_REPOSITORY
    ):
        raise RunnerDefectError("record is not an eligible target-bound runner defect")

    binding = value.get("run_binding")
    if not isinstance(binding, dict) or set(binding) != {
        "schema",
        "run_id",
        "ledger_sha256",
        "ticket_id",
        "ticket_digest",
    }:
        raise RunnerDefectError("runner-defect run binding schema is invalid")
    ticket_id = binding.get("ticket_id")
    ticket = ledger.get("tickets", {}).get(ticket_id)
    if (
        binding.get("schema") != 1
        or binding.get("run_id") != run_id
        or binding.get("ledger_sha256") != ledger_sha256
        or not isinstance(ticket, dict)
        or binding.get("ticket_digest") != ticket.get("ticket_digest")
    ):
        raise RunnerDefectError("runner-defect run binding is missing or stale")

    owner = value.get("owner")
    if not isinstance(owner, dict) or set(owner) != {"component", "module", "anchor"}:
        raise RunnerDefectError("runner-defect owner schema is invalid")
    normalized_owner = {
        "component": _safe_token(owner.get("component"), "owner.component"),
        "module": _safe_token(owner.get("module"), "owner.module"),
        "anchor": _safe_token(owner.get("anchor"), "owner.anchor"),
    }
    if normalized_owner["component"] != "ticket-autopilot":
        raise RunnerDefectError("defect ownership is outside ticket-autopilot")

    failure = value.get("failure")
    if not isinstance(failure, dict) or set(failure) != {
        "code",
        "phase",
        "invariant",
        "symptom",
        "exception_family",
    }:
        raise RunnerDefectError("runner-defect failure schema is invalid")
    normalized_failure = {
        "code": _safe_token(failure.get("code"), "failure.code"),
        "phase": _safe_token(failure.get("phase"), "failure.phase"),
        "invariant": _safe_text(failure.get("invariant"), "failure.invariant"),
        "symptom": _safe_text(failure.get("symptom"), "failure.symptom"),
        "exception_family": _safe_token(
            failure.get("exception_family"), "failure.exception_family"
        ),
    }

    confidence = value.get("confidence")
    if (
        not isinstance(confidence, dict)
        or set(confidence) != {"level", "basis"}
        or confidence.get("level") != "high"
        or not isinstance(confidence.get("basis"), list)
        or set(confidence["basis"])
        != {"deterministic-reproduction", "runner-source-trace"}
        or len(confidence["basis"]) != 2
    ):
        raise RunnerDefectError(
            "runner-defect confidence requires deterministic reproduction and source trace"
        )

    feedback = value.get("feedback_loop")
    if not isinstance(feedback, dict) or set(feedback) != {
        "kind",
        "anchor",
        "observed",
        "artifact_sha256",
    }:
        raise RunnerDefectError("runner-defect feedback-loop schema is invalid")
    normalized_feedback = {
        "kind": _safe_token(feedback.get("kind"), "feedback_loop.kind"),
        "anchor": _safe_token(feedback.get("anchor"), "feedback_loop.anchor"),
        "observed": _safe_text(feedback.get("observed"), "feedback_loop.observed"),
        "artifact_sha256": _sha(
            feedback.get("artifact_sha256"), "feedback_loop.artifact_sha256"
        ),
    }

    evidence = value.get("evidence")
    if not isinstance(evidence, list) or len(evidence) < 2:
        raise RunnerDefectError("runner-defect evidence requires at least two records")
    normalized_evidence: list[dict[str, str]] = []
    classes: set[str] = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict) or set(item) != {
            "class",
            "summary",
            "artifact_sha256",
        }:
            raise RunnerDefectError("runner-defect evidence schema is invalid")
        evidence_class = _safe_token(item.get("class"), f"evidence[{index}].class")
        if evidence_class not in {"local-deterministic", "static-source"}:
            raise RunnerDefectError("runner-defect evidence class is not eligible")
        classes.add(evidence_class)
        normalized_evidence.append(
            {
                "class": evidence_class,
                "summary": _safe_text(
                    item.get("summary"), f"evidence[{index}].summary"
                ),
                "artifact_sha256": _sha(
                    item.get("artifact_sha256"),
                    f"evidence[{index}].artifact_sha256",
                ),
            }
        )
    if classes != {"local-deterministic", "static-source"}:
        raise RunnerDefectError("runner-defect evidence does not prove both eligibility bases")

    redaction = value.get("redaction")
    if (
        not isinstance(redaction, dict)
        or set(redaction) != {"contract", "applied"}
        or redaction.get("contract") != "diagnose/references/secret-redaction.md"
        or redaction.get("applied") is not True
    ):
        raise RunnerDefectError("runner-defect redaction attestation is absent")

    return {
        "schema": DEFECT_SCHEMA,
        "classification": "runner-defect",
        "repository": TARGET_REPOSITORY,
        "run_binding": dict(binding),
        "owner": normalized_owner,
        "failure": normalized_failure,
        "confidence": {
            "level": "high",
            "basis": ["deterministic-reproduction", "runner-source-trace"],
        },
        "feedback_loop": normalized_feedback,
        "evidence": normalized_evidence,
        "redaction": {
            "contract": "diagnose/references/secret-redaction.md",
            "applied": True,
        },
    }


def defect_fingerprint(record: dict[str, Any]) -> str:
    projection = {
        "schema": 1,
        "repository": TARGET_REPOSITORY,
        "classification": "runner-defect",
        "owner": record["owner"],
        "failure": {
            key: record["failure"][key]
            for key in ("code", "phase", "invariant", "exception_family")
        },
        "feedback_loop": {
            key: record["feedback_loop"][key]
            for key in ("kind", "anchor", "artifact_sha256")
        },
    }
    return _digest(projection)


def marker_for(fingerprint: str) -> str:
    if not _HEX_64.fullmatch(fingerprint):
        raise RunnerDefectError("defect fingerprint is invalid")
    return f"{MARKER_PREFIX}{fingerprint} -->"


def render_issue(record: dict[str, Any], fingerprint: str) -> tuple[str, str]:
    failure = record["failure"]
    owner = record["owner"]
    feedback = record["feedback_loop"]
    evidence = sorted(record["evidence"], key=lambda item: item["class"])
    title = f"[Runner defect] {owner['module']}: {failure['code']}"
    if len(title) > 180:
        raise RunnerDefectError("rendered issue title exceeds the fixed limit")
    evidence_lines = "\n".join(
        f"- `{item['class']}`: {item['summary']} (artifact `{item['artifact_sha256']}`)"
        for item in evidence
    )
    body = (
        "## Runner defect\n\n"
        f"- Component: `{owner['component']}`\n"
        f"- Module: `{owner['module']}`\n"
        f"- Source anchor: `{owner['anchor']}`\n"
        f"- Failure code: `{failure['code']}`\n"
        f"- Phase: `{failure['phase']}`\n"
        f"- Exception family: `{failure['exception_family']}`\n\n"
        "## Sanitized diagnosis\n\n"
        f"**Invariant:** {failure['invariant']}\n\n"
        f"**Symptom:** {failure['symptom']}\n\n"
        "## Deterministic feedback loop\n\n"
        f"- Kind: `{feedback['kind']}`\n"
        f"- Anchor: `{feedback['anchor']}`\n"
        f"- Observation: {feedback['observed']}\n"
        f"- Artifact: `{feedback['artifact_sha256']}`\n\n"
        "## Sanitized evidence\n\n"
        f"{evidence_lines}\n\n"
        "This report was rendered under `diagnose/references/secret-redaction.md`.\n\n"
        f"{marker_for(fingerprint)}\n"
    )
    return title, body


@contextmanager
def protected_run_ledger(
    repo: Path, run_id: str, record: Any
) -> Iterator[tuple[dict[str, Any], dict[str, Any], str]]:
    """Lock a run and prove the escalation left its bytes exactly unchanged."""

    path = run_directory(repo, run_id) / "ledger.json"
    ledger_store = AtomicLedger(path)
    with ledger_store.run_locked():
        before = path.read_bytes() if path.exists() else b""
        if not before:
            raise RunnerDefectError(f"run ledger does not exist: {run_id}")
        ledger = ledger_store.load()
        ledger_sha256 = hashlib.sha256(before).hexdigest()
        normalized = validate_defect_record(
            record,
            run_id=run_id,
            ledger_sha256=ledger_sha256,
            ledger=ledger,
        )
        yield normalized, ledger, ledger_sha256
        after = path.read_bytes()
        if after != before:
            raise RunnerDefectError("runner-defect escalation changed protected run state")


def _provider_issue(receipt: dict[str, Any], fingerprint: str) -> dict[str, Any]:
    marker = marker_for(fingerprint)
    if (
        not isinstance(receipt, dict)
        or receipt.get("schema") != 1
        or receipt.get("provider") != TARGET_PROVIDER
        or receipt.get("evidence_class") != "live"
        or receipt.get("observed") is not True
        or receipt.get("repository") != TARGET_REPOSITORY
        or not isinstance(receipt.get("issue_number"), int)
        or receipt["issue_number"] <= 0
        or not _nonempty(receipt.get("url"))
        or receipt.get("state") not in {"open", "closed"}
        or not isinstance(receipt.get("body"), str)
        or marker not in receipt["body"]
        or receipt.get("fingerprint") != fingerprint
    ):
        raise RunnerDefectError("provider issue receipt is contradictory")
    return receipt


def _search_matches(receipt: dict[str, Any], fingerprint: str) -> list[dict[str, Any]]:
    if (
        not isinstance(receipt, dict)
        or receipt.get("schema") != 1
        or receipt.get("provider") != TARGET_PROVIDER
        or receipt.get("operation") != SEARCH_RUNNER_DEFECT_ISSUES
        or receipt.get("evidence_class") != "live"
        or receipt.get("observed") is not True
        or receipt.get("repository") != TARGET_REPOSITORY
        or receipt.get("fingerprint") != fingerprint
        or receipt.get("conclusive") is not True
        or not isinstance(receipt.get("matches"), list)
    ):
        raise RunnerDefectError("provider issue search receipt is inconclusive or invalid")
    return [_provider_issue(item, fingerprint) for item in receipt["matches"]]


class RunnerDefectEscalator:
    def __init__(
        self,
        authority: PublicationAuthority,
        outbox: IssueOutbox,
        adapter: IssueAdapter | None,
    ):
        self.authority = authority
        self.outbox = outbox
        self.adapter = adapter

    @staticmethod
    def _validate_outbox(
        document: dict[str, Any], fingerprint: str, title: str, body: str
    ) -> None:
        if (
            not isinstance(document, dict)
            or set(document)
            != {
                "schema",
                "repository",
                "provider",
                "fingerprint",
                "state",
                "phase",
                "authority",
                "attempts",
                "issue_payload",
                "provider_evidence",
                "receipt",
                "failure",
            }
            or document.get("schema") != OUTBOX_SCHEMA
            or document.get("repository") != TARGET_REPOSITORY
            or document.get("provider") != TARGET_PROVIDER
            or document.get("fingerprint") != fingerprint
            or document.get("state")
            not in {
                "reserved",
                "search-failed",
                "create-ready",
                "dispatch-ambiguous",
                "published",
                "deduplicated",
            }
            or not isinstance(document.get("phase"), str)
            or not document["phase"]
            or not isinstance(document.get("authority"), dict)
            or set(document["authority"]) != {"authority_id", "actor", "evidence"}
            or not _nonempty(document["authority"].get("authority_id"))
            or not _nonempty(document["authority"].get("actor"))
            or not _nonempty(document["authority"].get("evidence"))
            or document.get("issue_payload")
            != {
                "title": title,
                "body": body,
                "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "labels": ["bug"],
            }
            or not isinstance(document.get("attempts"), dict)
            or set(document["attempts"]) != {"search", "create"}
            or any(
                type(value) is not int or value < 0
                for value in document["attempts"].values()
            )
            or not isinstance(document.get("provider_evidence"), list)
            or any(
                not isinstance(item, dict)
                or set(item) != {"operation", "sha256"}
                or item.get("operation")
                not in {SEARCH_RUNNER_DEFECT_ISSUES, CREATE_RUNNER_DEFECT_ISSUE}
                or not isinstance(item.get("sha256"), str)
                or not _HEX_64.fullmatch(item["sha256"])
                for item in document["provider_evidence"]
            )
            or (
                document.get("failure") is not None
                and (
                    not isinstance(document["failure"], dict)
                    or set(document["failure"])
                    not in ({"code"}, {"code", "message_sha256"})
                    or not _nonempty(document["failure"].get("code"))
                    or (
                        "message_sha256" in document["failure"]
                        and (
                            not isinstance(document["failure"]["message_sha256"], str)
                            or not _HEX_64.fullmatch(
                                document["failure"]["message_sha256"]
                            )
                        )
                    )
                )
            )
        ):
            raise RunnerDefectError("runner-defect outbox is contradictory")
        final = document["state"] in FINAL_STATES
        receipt = document.get("receipt")
        if final != isinstance(receipt, dict):
            raise RunnerDefectError("runner-defect outbox final receipt is inconsistent")
        if not final:
            return
        provider = receipt.get("provider")
        if (
            set(receipt)
            != {
                "schema",
                "disposition",
                "repository",
                "issue_number",
                "url",
                "issue_state",
                "fingerprint",
                "sanitized_body_sha256",
                "actor",
                "authority_id",
                "provider",
            }
            or receipt.get("schema") != 1
            or receipt.get("disposition")
            != ("created" if document["state"] == "published" else "deduplicated")
            or receipt.get("repository") != TARGET_REPOSITORY
            or type(receipt.get("issue_number")) is not int
            or receipt["issue_number"] <= 0
            or not _nonempty(receipt.get("url"))
            or receipt.get("issue_state") not in {"open", "closed"}
            or receipt.get("fingerprint") != fingerprint
            or receipt.get("sanitized_body_sha256")
            != document["issue_payload"]["body_sha256"]
            or receipt.get("actor") != document["authority"]["actor"]
            or receipt.get("authority_id")
            != document["authority"]["authority_id"]
            or not isinstance(provider, dict)
            or set(provider)
            != {
                "name",
                "search_receipt_sha256",
                "create_receipt_sha256",
                "observed_body_sha256",
            }
            or provider.get("name") != TARGET_PROVIDER
            or not isinstance(provider.get("search_receipt_sha256"), str)
            or not _HEX_64.fullmatch(provider["search_receipt_sha256"])
            or (
                (provider.get("create_receipt_sha256") is not None)
                != (document["state"] == "published")
            )
            or (
                provider.get("create_receipt_sha256") is not None
                and (
                    not isinstance(provider["create_receipt_sha256"], str)
                    or not _HEX_64.fullmatch(provider["create_receipt_sha256"])
                )
            )
            or not isinstance(provider.get("observed_body_sha256"), str)
            or not _HEX_64.fullmatch(provider["observed_body_sha256"])
        ):
            raise RunnerDefectError("runner-defect outbox final receipt is invalid")

    @staticmethod
    def _new_document(
        fingerprint: str,
        title: str,
        body: str,
        grant: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema": OUTBOX_SCHEMA,
            "repository": TARGET_REPOSITORY,
            "provider": TARGET_PROVIDER,
            "fingerprint": fingerprint,
            "state": "reserved",
            "phase": "reserved",
            "authority": {
                "authority_id": grant["authority_id"],
                "actor": grant["actor"],
                "evidence": grant["evidence"],
            },
            "attempts": {"search": 0, "create": 0},
            "issue_payload": {
                "title": title,
                "body": body,
                "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "labels": ["bug"],
            },
            "provider_evidence": [],
            "receipt": None,
            "failure": None,
        }

    @staticmethod
    def _result(
        fingerprint: str,
        document: dict[str, Any] | None,
        raw: bytes | None,
    ) -> EscalationResult:
        receipt = document.get("receipt") if document else None
        return EscalationResult(
            fingerprint=fingerprint,
            state=document["state"] if document else "dry-run",
            disposition=receipt.get("disposition") if isinstance(receipt, dict) else None,
            outbox_sha256=hashlib.sha256(raw).hexdigest() if raw is not None else None,
            receipt=receipt,
        )

    def dry_run(self, record: dict[str, Any]) -> EscalationResult:
        grant = self.authority.require_active()
        fingerprint = defect_fingerprint(record)
        title, body = render_issue(record, fingerprint)
        # Exercise the complete deterministic payload contract without reserving or calling
        # the provider.  The authority is returned only as a validation dependency.
        self._new_document(fingerprint, title, body, grant)
        return self._result(fingerprint, None, None)

    def _finish(
        self,
        store: _LockedDocument,
        document: dict[str, Any],
        issue: dict[str, Any],
        fingerprint: str,
        *,
        disposition: str,
        search_evidence: dict[str, Any],
        create_evidence: dict[str, Any] | None,
    ) -> EscalationResult:
        authority = document["authority"]
        receipt = {
            "schema": 1,
            "disposition": disposition,
            "repository": TARGET_REPOSITORY,
            "issue_number": issue["issue_number"],
            "url": issue["url"],
            "issue_state": issue["state"],
            "fingerprint": fingerprint,
            "sanitized_body_sha256": document["issue_payload"]["body_sha256"],
            "actor": authority["actor"],
            "authority_id": authority["authority_id"],
            "provider": {
                "name": TARGET_PROVIDER,
                "search_receipt_sha256": _digest(search_evidence),
                "create_receipt_sha256": (
                    _digest(create_evidence) if create_evidence is not None else None
                ),
                "observed_body_sha256": hashlib.sha256(
                    issue["body"].encode("utf-8")
                ).hexdigest(),
            },
        }
        document["state"] = "published" if disposition == "created" else "deduplicated"
        document["phase"] = "receipt-saved"
        document["receipt"] = receipt
        document["failure"] = None
        store.write_unlocked(document)
        raw = store.path.read_bytes()
        return self._result(fingerprint, document, raw)

    def escalate(
        self,
        record: dict[str, Any],
        *,
        crash_at: str | None = None,
    ) -> EscalationResult:
        if self.adapter is None:
            raise RunnerDefectError("live escalation requires an issue provider adapter")
        fingerprint = defect_fingerprint(record)
        title, body = render_issue(record, fingerprint)
        store = self.outbox.document(fingerprint)
        with store.locked():
            document = store.read_unlocked()
            if document is None:
                grant = self.authority.require_active()
                document = self._new_document(fingerprint, title, body, grant)
                store.write_unlocked(document)
                if crash_at == "after-reservation":
                    raise SimulatedIssueCrash(crash_at)
            self._validate_outbox(document, fingerprint, title, body)
            if document["state"] in FINAL_STATES:
                return self._result(fingerprint, document, store.path.read_bytes())

            ambiguous_reconciliation = document["state"] == "dispatch-ambiguous"
            if not ambiguous_reconciliation:
                self.authority.require_active(document["authority"]["authority_id"])

            document["attempts"]["search"] += 1
            document["phase"] = (
                "ambiguous-read-only-reconciliation"
                if ambiguous_reconciliation
                else "exact-search"
            )
            document["failure"] = None
            store.write_unlocked(document)
            try:
                search = self.adapter.search_exact(TARGET_REPOSITORY, fingerprint)
                matches = _search_matches(search, fingerprint)
            except (ProviderError, RunnerDefectError) as error:
                document["phase"] = "search-failed"
                document["failure"] = {
                    "code": type(error).__name__,
                    "message_sha256": hashlib.sha256(str(error).encode("utf-8")).hexdigest(),
                }
                if not ambiguous_reconciliation:
                    document["state"] = "search-failed"
                store.write_unlocked(document)
                return self._result(fingerprint, document, store.path.read_bytes())

            document["provider_evidence"].append(
                {"operation": SEARCH_RUNNER_DEFECT_ISSUES, "sha256": _digest(search)}
            )
            if len(matches) > 1:
                document["state"] = (
                    "dispatch-ambiguous" if ambiguous_reconciliation else "search-failed"
                )
                document["phase"] = "multiple-exact-matches"
                document["failure"] = {"code": "ambiguous-exact-match"}
                store.write_unlocked(document)
                return self._result(fingerprint, document, store.path.read_bytes())
            if matches:
                return self._finish(
                    store,
                    document,
                    matches[0],
                    fingerprint,
                    disposition="deduplicated",
                    search_evidence=search,
                    create_evidence=None,
                )
            if ambiguous_reconciliation:
                document["state"] = "dispatch-ambiguous"
                document["phase"] = "human-reconciliation-required"
                document["failure"] = {"code": "ambiguous-dispatch-no-exact-match"}
                store.write_unlocked(document)
                return self._result(fingerprint, document, store.path.read_bytes())
            if crash_at == "after-search":
                raise SimulatedIssueCrash(crash_at)

            document["state"] = "create-ready"
            document["phase"] = "known-non-send"
            store.write_unlocked(document)
            if crash_at == "before-create":
                raise SimulatedIssueCrash(crash_at)

            # Linearize revocation against the only remote mutation.  A revocation that
            # acquires this lock first prevents dispatch; one that follows observes an
            # already-authorized intent/effect and blocks every later mutation.
            with self.authority.store.locked():
                self.authority.require_active_unlocked(
                    document["authority"]["authority_id"]
                )
                document["state"] = "dispatch-ambiguous"
                document["phase"] = "dispatch-intent-saved"
                document["attempts"]["create"] += 1
                store.write_unlocked(document)
                try:
                    created = self.adapter.create(
                        TARGET_REPOSITORY, fingerprint, title, body
                    )
                except (ProviderError, RunnerDefectError) as error:
                    document["phase"] = "dispatch-outcome-ambiguous"
                    document["failure"] = {
                        "code": type(error).__name__,
                        "message_sha256": hashlib.sha256(
                            str(error).encode("utf-8")
                        ).hexdigest(),
                    }
                    store.write_unlocked(document)
                    return self._result(
                        fingerprint, document, store.path.read_bytes()
                    )
            if crash_at == "after-create":
                raise SimulatedIssueCrash(crash_at)
            issue = _provider_issue(created, fingerprint)
            if created.get("operation") not in {
                CREATE_RUNNER_DEFECT_ISSUE,
                GET_RUNNER_DEFECT_ISSUE,
            }:
                raise RunnerDefectError("provider create readback operation is invalid")
            document["provider_evidence"].append(
                {"operation": CREATE_RUNNER_DEFECT_ISSUE, "sha256": _digest(created)}
            )
            return self._finish(
                store,
                document,
                issue,
                fingerprint,
                disposition="created",
                search_evidence=search,
                create_evidence=created,
            )
