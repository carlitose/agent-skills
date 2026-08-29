"""Disposable no-network logic model for RD-02. Not production code."""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import re
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping


TARGET_REPOSITORY = "carlitose/agent-skills"
MARKER_PREFIX = "runner-defect-fingerprint:"
FINAL_STATES = {"published", "deduplicated", "terminal-failure"}
ALLOWED_EVIDENCE_CLASSES = {
    "local-deterministic",
    "simulated-provider",
    "static-source",
}
TOP_LEVEL_KEYS = {
    "schema",
    "classification",
    "owner",
    "failure",
    "confidence",
    "feedback_loop",
    "evidence",
    "redaction",
}
OWNER_KEYS = {"component", "module", "anchor"}
FAILURE_KEYS = {
    "code",
    "phase",
    "invariant",
    "symptom",
    "exception_family",
}
CONFIDENCE_KEYS = {"level", "basis"}
FEEDBACK_KEYS = {"kind", "anchor", "observed", "artifact_sha256"}
EVIDENCE_KEYS = {"class", "summary", "artifact_sha256"}
REDACTION_KEYS = {"contract", "applied"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SYMBOL_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
FORBIDDEN_TEXT = (
    re.compile(r"(?i)\b(?:authorization|bearer|password|passwd|secret|token|cookie)\b"),
    re.compile(
        r"(?i)(?:gh[pousr]_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)"
    ),
    re.compile(r"(?:^|[\s(])/(?:Users|home|tmp|private|var)/"),
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"\brefs/heads/"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"),
    re.compile(r"\bline\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b[a-z0-9-]+-\d{8}\b"),
    re.compile(r"(?i)private[ -]content"),
)


class PrototypeError(RuntimeError):
    """Base class for deterministic prototype failures."""


class RecordRejected(PrototypeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class RunBindingRejected(PrototypeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class SimulatedCrash(PrototypeError):
    pass


class ProviderFailure(PrototypeError):
    def __init__(self, code: str, *, retryable: bool):
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class LostResponse(PrototypeError):
    pass


@dataclass(frozen=True)
class ProviderIssue:
    repository: str
    issue_id: int
    state: str
    fingerprint: str
    title: str
    body: str


@dataclass(frozen=True)
class SearchObservation:
    matches: tuple[ProviderIssue, ...]
    conclusive: bool


@dataclass(frozen=True)
class EscalationResult:
    fingerprint: str
    state: str
    document_bytes: bytes
    protected_state_sha256: str

    def as_dict(self) -> dict[str, Any]:
        document = json.loads(self.document_bytes)
        return {
            "fingerprint": self.fingerprint,
            "state": self.state,
            "phase": document["phase"],
            "attempts": document["attempts"],
            "failure": document.get("failure"),
            "receipt": document.get("receipt"),
            "protected_state_sha256": self.protected_state_sha256,
        }


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_exact_keys(value: Any, expected: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise RecordRejected(code)
    return value


def _plain_text(value: Any, *, code: str, maximum: int = 240) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise RecordRejected(code)
    if value != value.strip() or any(character in value for character in "\r\n\0`<>"):
        raise RecordRejected(code)
    for pattern in FORBIDDEN_TEXT:
        if pattern.search(value):
            raise RecordRejected("secret-or-volatile-text")
    return value


def _sentence(value: Any, *, code: str, maximum: int = 240) -> str:
    text = _plain_text(value, code=code, maximum=maximum)
    if (
        any(character in text for character in "*[]#!|")
        or re.search(r"(?i)https?://", text)
        or re.match(r"^(?:[-+] |\d+\. )", text)
    ):
        raise RecordRejected("markdown-passthrough")
    return text


def _symbol(value: Any, *, code: str, maximum: int = 160) -> str:
    text = _plain_text(value, code=code, maximum=maximum)
    if not SYMBOL_RE.fullmatch(text):
        raise RecordRejected(code)
    return text


def _digest(value: Any, *, code: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise RecordRejected(code)
    return value


def validate_record(record: Any) -> dict[str, Any]:
    """Accept only the RD-01 allowlisted record and return a deep copy."""

    root = _require_exact_keys(record, TOP_LEVEL_KEYS, "record-shape")
    if root["schema"] != 1:
        raise RecordRejected("record-schema")
    if root["classification"] != "runner-defect":
        raise RecordRejected("classification-not-runner-defect")

    owner = _require_exact_keys(root["owner"], OWNER_KEYS, "owner-shape")
    if _plain_text(owner["component"], code="owner-component", maximum=80) != "ticket-autopilot":
        raise RecordRejected("owner-not-runner")
    module = _symbol(owner["module"], code="owner-module")
    if not (module == "autopilot" or module.startswith("autopilot.")):
        raise RecordRejected("owner-not-runner")
    _symbol(owner["anchor"], code="owner-anchor")

    failure = _require_exact_keys(root["failure"], FAILURE_KEYS, "failure-shape")
    if not isinstance(failure["code"], str) or not KEBAB_RE.fullmatch(failure["code"]):
        raise RecordRejected("failure-code")
    if not isinstance(failure["phase"], str) or not KEBAB_RE.fullmatch(failure["phase"]):
        raise RecordRejected("failure-phase")
    _sentence(failure["invariant"], code="failure-invariant")
    _sentence(failure["symptom"], code="failure-symptom")
    _symbol(failure["exception_family"], code="exception-family", maximum=80)

    confidence = _require_exact_keys(
        root["confidence"], CONFIDENCE_KEYS, "confidence-shape"
    )
    if confidence["level"] not in {"high", "medium", "low"}:
        raise RecordRejected("confidence-level")
    if confidence["level"] != "high":
        raise RecordRejected("confidence-below-prototype-threshold")
    basis = confidence["basis"]
    if not isinstance(basis, list) or not basis or len(basis) != len(set(basis)):
        raise RecordRejected("confidence-basis")
    if set(basis) != {"deterministic-reproduction", "runner-source-trace"}:
        raise RecordRejected("confidence-basis")

    feedback = _require_exact_keys(
        root["feedback_loop"], FEEDBACK_KEYS, "feedback-shape"
    )
    if feedback["kind"] not in {"unit-test", "integration-test", "forward-test"}:
        raise RecordRejected("feedback-kind")
    _symbol(feedback["anchor"], code="feedback-anchor", maximum=200)
    _sentence(feedback["observed"], code="feedback-observed")
    _digest(feedback["artifact_sha256"], code="feedback-digest")

    evidence = root["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise RecordRejected("evidence-shape")
    classes: set[str] = set()
    for item in evidence:
        normalized = _require_exact_keys(item, EVIDENCE_KEYS, "evidence-item-shape")
        if normalized["class"] not in ALLOWED_EVIDENCE_CLASSES:
            raise RecordRejected("evidence-class")
        classes.add(normalized["class"])
        _sentence(normalized["summary"], code="evidence-summary")
        _digest(normalized["artifact_sha256"], code="evidence-digest")
    if "local-deterministic" not in classes:
        raise RecordRejected("local-deterministic-evidence-required")

    redaction = _require_exact_keys(
        root["redaction"], REDACTION_KEYS, "redaction-shape"
    )
    if redaction != {
        "contract": "diagnose/references/secret-redaction.md",
        "applied": True,
    }:
        raise RecordRejected("redaction-not-proven")

    return copy.deepcopy(root)


def fingerprint_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    """Project only stable fields; callers must validate before durable use.

    Tests may add excluded volatile fixture fields to prove that this pure projection ignores
    them. ``EscalationCoordinator`` always calls ``validate_record`` first, so unknown fields
    never cross the durable or provider boundary.
    """

    return {
        "classification": record["classification"],
        "failure": {
            "code": record["failure"]["code"],
            "invariant": record["failure"]["invariant"],
            "phase": record["failure"]["phase"],
        },
        "owner": {
            "anchor": record["owner"]["anchor"],
            "component": record["owner"]["component"],
            "module": record["owner"]["module"],
        },
        "schema": record["schema"],
    }


def fingerprint(record: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_bytes(fingerprint_projection(record)))


def marker_for(value: str) -> str:
    if not SHA256_RE.fullmatch(value):
        raise ValueError("fingerprint must be lowercase SHA-256")
    return f"<!-- {MARKER_PREFIX}{value} -->"


def render_issue(record: Mapping[str, Any], value: str) -> tuple[str, str]:
    title = f"[runner-defect] {record['failure']['code']} in {record['owner']['module']}"
    evidence = "\n".join(
        f"- {item['class']}: {item['summary']} (`{item['artifact_sha256']}`)"
        for item in sorted(record["evidence"], key=lambda item: (item["class"], item["artifact_sha256"]))
    )
    body = "\n".join(
        (
            marker_for(value),
            "",
            "## Diagnosed invariant",
            record["failure"]["invariant"],
            "",
            "## Sanitized symptom",
            record["failure"]["symptom"],
            "",
            "## Owner",
            f"- Component: `{record['owner']['component']}`",
            f"- Module: `{record['owner']['module']}`",
            f"- Anchor: `{record['owner']['anchor']}`",
            f"- Phase: `{record['failure']['phase']}`",
            "",
            "## Feedback loop",
            f"- {record['feedback_loop']['kind']}: `{record['feedback_loop']['anchor']}`",
            f"- Observation: {record['feedback_loop']['observed']}",
            f"- Artifact: `{record['feedback_loop']['artifact_sha256']}`",
            "",
            "## Sanitized evidence",
            evidence,
            "",
        )
    )
    return title, body


def validate_run_binding(binding: Any) -> dict[str, Any]:
    if not isinstance(binding, dict):
        raise RunBindingRejected("ledger-missing")
    expected = {"schema", "repository", "run_binding_sha256", "integrity", "bound"}
    if set(binding) != expected or binding.get("schema") != 1:
        raise RunBindingRejected("ledger-malformed")
    if binding.get("repository") != TARGET_REPOSITORY:
        raise RunBindingRejected("ledger-unbound")
    if binding.get("bound") is not True:
        raise RunBindingRejected("ledger-unbound")
    if binding.get("integrity") != "valid":
        raise RunBindingRejected("ledger-corrupt")
    value = binding.get("run_binding_sha256")
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise RunBindingRejected("ledger-malformed")
    return copy.deepcopy(binding)


class EscalationStore:
    """Atomic JSON sidecar with process-local plus OS per-fingerprint locking."""

    _locks_guard = threading.Lock()
    _process_locks: dict[str, threading.Lock] = {}

    def __init__(self, root: Path):
        self.root = root
        self.documents = root / "outbox"
        self.locks = root / "locks"
        self.documents.mkdir(parents=True, exist_ok=True)
        self.locks.mkdir(parents=True, exist_ok=True)

    def _document_path(self, value: str) -> Path:
        return self.documents / f"{value}.json"

    @classmethod
    def _process_lock(cls, path: Path) -> threading.Lock:
        key = str(path.resolve())
        with cls._locks_guard:
            return cls._process_locks.setdefault(key, threading.Lock())

    @contextmanager
    def locked(self, value: str) -> Iterator[None]:
        lock_path = self.locks / f"{value}.lock"
        process_lock = self._process_lock(lock_path)
        with process_lock:
            with lock_path.open("a+b") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def read_raw(self, value: str) -> bytes | None:
        path = self._document_path(value)
        return path.read_bytes() if path.exists() else None

    def read(self, value: str) -> dict[str, Any] | None:
        raw = self.read_raw(value)
        return json.loads(raw) if raw is not None else None

    def write(self, value: str, document: Mapping[str, Any]) -> bytes:
        raw = canonical_bytes(document)
        path = self._document_path(value)
        temporary = path.with_name(
            f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        with temporary.open("wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(self.documents, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return raw

    def list_documents(self) -> tuple[str, ...]:
        return tuple(path.name for path in sorted(self.documents.glob("*.json")))


class FakeIssueAdapter:
    """Stateful fake. It exposes only exact-marker search and one create operation."""

    def __init__(
        self,
        *,
        search_mode: str = "normal",
        create_mode: str = "success",
        issues: tuple[ProviderIssue, ...] = (),
    ):
        self.search_mode = search_mode
        self.create_mode = create_mode
        self.issues = list(issues)
        self.calls: list[tuple[str, str]] = []
        self._lock = threading.Lock()

    def search_exact(self, repository: str, value: str) -> SearchObservation:
        with self._lock:
            self.calls.append(("search", value))
            if self.search_mode == "offline":
                raise ProviderFailure("offline", retryable=True)
            if self.search_mode == "permission":
                raise ProviderFailure("permission-failure", retryable=False)
            matches = tuple(
                issue
                for issue in self.issues
                if issue.repository == repository and issue.fingerprint == value
            )
            if self.search_mode == "ambiguous":
                duplicate = ProviderIssue(
                    repository,
                    999,
                    "open",
                    value,
                    "synthetic ambiguous match",
                    marker_for(value),
                )
                return SearchObservation(matches + (duplicate,), True)
            if self.search_mode == "inconclusive-absent" and not matches:
                return SearchObservation((), False)
            return SearchObservation(matches, True)

    def create(
        self, repository: str, value: str, title: str, body: str
    ) -> ProviderIssue:
        with self._lock:
            self.calls.append(("create", value))
            if self.create_mode == "permission":
                raise ProviderFailure("permission-failure", retryable=False)
            issue = ProviderIssue(
                repository=repository,
                issue_id=max((item.issue_id for item in self.issues), default=0) + 1,
                state="open",
                fingerprint=value,
                title=title,
                body=body,
            )
            if self.create_mode == "contradictory":
                return ProviderIssue(
                    repository="other/repository",
                    issue_id=issue.issue_id,
                    state=issue.state,
                    fingerprint="0" * 64,
                    title=issue.title,
                    body=issue.body,
                )
            self.issues.append(issue)
            if self.create_mode == "lost-response":
                self.create_mode = "success"
                raise LostResponse("provider response was lost after synthetic dispatch")
            return issue

    def call_count(self, operation: str) -> int:
        return sum(1 for name, _value in self.calls if name == operation)


class EscalationCoordinator:
    """No-network coordinator that can mutate only ``EscalationStore``."""

    def __init__(self, store: EscalationStore, adapter: FakeIssueAdapter):
        self.store = store
        self.adapter = adapter

    def _result(
        self,
        value: str,
        document: Mapping[str, Any],
        protected_before: bytes,
        protected_state: Any,
    ) -> EscalationResult:
        protected_after = canonical_bytes(protected_state)
        if protected_after != protected_before:
            raise AssertionError("protected run state changed")
        raw = self.store.read_raw(value)
        if raw is None or json.loads(raw) != document:
            raise AssertionError("sidecar readback mismatch")
        return EscalationResult(
            fingerprint=value,
            state=document["state"],
            document_bytes=raw,
            protected_state_sha256=sha256_bytes(protected_after),
        )

    @staticmethod
    def _receipt(issue: ProviderIssue, value: str, *, disposition: str) -> dict[str, Any]:
        if (
            issue.repository != TARGET_REPOSITORY
            or issue.fingerprint != value
            or not isinstance(issue.issue_id, int)
            or issue.issue_id <= 0
            or issue.state not in {"open", "closed"}
            or marker_for(value) not in issue.body
        ):
            raise ProviderFailure("contradictory-provider-receipt", retryable=False)
        return {
            "disposition": disposition,
            "repository": issue.repository,
            "issue_id": issue.issue_id,
            "issue_state": issue.state,
            "fingerprint": value,
        }

    def _save_failure(
        self,
        value: str,
        document: dict[str, Any],
        failure: ProviderFailure,
        *,
        phase: str,
    ) -> dict[str, Any]:
        document["state"] = "retryable-failure" if failure.retryable else "terminal-failure"
        document["phase"] = phase
        document["failure"] = {"code": failure.code, "retryable": failure.retryable}
        document.pop("receipt", None)
        self.store.write(value, document)
        return document

    def escalate(
        self,
        record: Any,
        *,
        run_binding: Any,
        protected_state: Any,
        crash_at: str | None = None,
    ) -> EscalationResult:
        protected_before = canonical_bytes(protected_state)
        validate_run_binding(run_binding)
        normalized = validate_record(record)
        value = fingerprint(normalized)
        title, body = render_issue(normalized, value)

        if crash_at == "before-reservation":
            raise SimulatedCrash(crash_at)

        with self.store.locked(value):
            document = self.store.read(value)
            if document is None:
                document = {
                    "schema": 1,
                    "repository": TARGET_REPOSITORY,
                    "fingerprint": value,
                    "state": "reserved",
                    "phase": "reserved",
                    "attempts": {"search": 0, "create": 0},
                    "issue_payload": {"title": title, "body": body},
                }
                self.store.write(value, document)
                if crash_at == "after-reservation":
                    raise SimulatedCrash(crash_at)
            elif (
                document.get("schema") != 1
                or document.get("repository") != TARGET_REPOSITORY
                or document.get("fingerprint") != value
            ):
                raise PrototypeError("contradictory local reservation")

            if document["state"] in FINAL_STATES:
                return self._result(value, document, protected_before, protected_state)

            replaying_ambiguous_dispatch = document["state"] == "dispatch-ambiguous"
            document["attempts"]["search"] += 1
            document["phase"] = (
                "recovery-search" if replaying_ambiguous_dispatch else "search"
            )
            document.pop("failure", None)
            self.store.write(value, document)
            try:
                observation = self.adapter.search_exact(TARGET_REPOSITORY, value)
            except ProviderFailure as failure:
                if replaying_ambiguous_dispatch:
                    document["state"] = "dispatch-ambiguous"
                    document["phase"] = "recovery-search-failed"
                    document["failure"] = {
                        "code": failure.code,
                        "retryable": failure.retryable,
                    }
                    self.store.write(value, document)
                else:
                    self._save_failure(
                        value, document, failure, phase="search-failed"
                    )
                return self._result(value, document, protected_before, protected_state)

            if len(observation.matches) > 1:
                failure = ProviderFailure("ambiguous-match", retryable=True)
                if replaying_ambiguous_dispatch:
                    document["state"] = "dispatch-ambiguous"
                    document["phase"] = "recovery-search-ambiguous"
                    document["failure"] = {
                        "code": failure.code,
                        "retryable": True,
                    }
                    self.store.write(value, document)
                else:
                    self._save_failure(
                        value, document, failure, phase="search-ambiguous"
                    )
                return self._result(value, document, protected_before, protected_state)

            if observation.matches:
                try:
                    receipt = self._receipt(
                        observation.matches[0], value, disposition="deduplicated"
                    )
                except ProviderFailure as failure:
                    self._save_failure(
                        value, document, failure, phase="search-receipt-rejected"
                    )
                    return self._result(
                        value, document, protected_before, protected_state
                    )
                document["state"] = "deduplicated"
                document["phase"] = "receipt-saved"
                document["receipt"] = receipt
                document.pop("failure", None)
                self.store.write(value, document)
                return self._result(value, document, protected_before, protected_state)

            if not observation.conclusive:
                if replaying_ambiguous_dispatch:
                    document["state"] = "dispatch-ambiguous"
                    document["phase"] = "recovery-search-inconclusive"
                else:
                    document["state"] = "retryable-failure"
                    document["phase"] = "search-inconclusive"
                document["failure"] = {
                    "code": "inconclusive-absence",
                    "retryable": True,
                }
                self.store.write(value, document)
                return self._result(value, document, protected_before, protected_state)

            if crash_at == "after-search":
                raise SimulatedCrash(crash_at)

            document["state"] = "dispatch-ambiguous"
            document["phase"] = "dispatch-intent-saved"
            document["attempts"]["create"] += 1
            document.pop("failure", None)
            self.store.write(value, document)
            if crash_at == "before-create":
                raise SimulatedCrash(crash_at)

            payload = document["issue_payload"]
            try:
                issue = self.adapter.create(
                    TARGET_REPOSITORY, value, payload["title"], payload["body"]
                )
            except LostResponse:
                document["state"] = "dispatch-ambiguous"
                document["phase"] = "dispatch-response-lost"
                document["failure"] = {
                    "code": "lost-response",
                    "retryable": True,
                }
                self.store.write(value, document)
                return self._result(value, document, protected_before, protected_state)
            except ProviderFailure as failure:
                self._save_failure(
                    value, document, failure, phase="create-rejected"
                )
                return self._result(value, document, protected_before, protected_state)

            if crash_at == "after-create":
                raise SimulatedCrash(crash_at)
            try:
                receipt = self._receipt(issue, value, disposition="created")
            except ProviderFailure as failure:
                self._save_failure(
                    value, document, failure, phase="create-receipt-rejected"
                )
                return self._result(value, document, protected_before, protected_state)

            document["state"] = "published"
            document["phase"] = "receipt-saved"
            document["receipt"] = receipt
            document.pop("failure", None)
            self.store.write(value, document)
            return self._result(value, document, protected_before, protected_state)


def accepted_record() -> dict[str, Any]:
    return {
        "schema": 1,
        "classification": "runner-defect",
        "owner": {
            "component": "ticket-autopilot",
            "module": "autopilot.kernel",
            "anchor": "Kernel.preflight_mutation_boundary",
        },
        "failure": {
            "code": "mutation-boundary-regression",
            "phase": "pre-provider-mutation",
            "invariant": "A valid canonical ticket must pass the last safe mutation check.",
            "symptom": "The deterministic fixture rejects the unchanged canonical ticket.",
            "exception_family": "TransitionError",
        },
        "confidence": {
            "level": "high",
            "basis": ["deterministic-reproduction", "runner-source-trace"],
        },
        "feedback_loop": {
            "kind": "unit-test",
            "anchor": "ticket-autopilot.tests.test_kernel.Example.test_case",
            "observed": "The baseline fails with the sanitized invariant mismatch.",
            "artifact_sha256": "a" * 64,
        },
        "evidence": [
            {
                "class": "local-deterministic",
                "summary": "The valid fixture reaches the incorrect rejection branch.",
                "artifact_sha256": "b" * 64,
            },
            {
                "class": "static-source",
                "summary": "The source trace identifies the reversed boundary condition.",
                "artifact_sha256": "c" * 64,
            },
        ],
        "redaction": {
            "contract": "diagnose/references/secret-redaction.md",
            "applied": True,
        },
    }


def valid_run_binding() -> dict[str, Any]:
    return {
        "schema": 1,
        "repository": TARGET_REPOSITORY,
        "run_binding_sha256": "d" * 64,
        "integrity": "valid",
        "bound": True,
    }


def protected_run_state() -> dict[str, Any]:
    return {
        "tickets": {"RD-X": {"state": "gated"}},
        "gates": {"gate:RD-X:start:1": {"state": "open"}},
        "effects": {"RD-X": {"state": "none"}},
        "leaf_progress": {"RD-X": {"verify": {"complete": False}}},
        "delivery": {"RD-X": None},
        "pr": {"RD-X": None},
        "merge_policy": "manual",
        "autonomous_merge_grant": None,
        "history": [{"event": "run-created"}],
    }
