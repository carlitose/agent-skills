"""Audited, replayable bootstrap of one private GitHub repository and base branch."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Protocol
from urllib.parse import urlparse

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import CommandRunner, SubprocessCommandRunner
from .providers import (
    CREATE_PRIVATE_REPOSITORY,
    GET_REPOSITORY,
    GET_REPOSITORY_BRANCH,
    SET_DEFAULT_BRANCH,
    GitHubProvider,
    ProviderExecutor,
)


TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9_.-]+$")
STATE_RELATIVE_PATH = Path("ticket-autopilot/repository-bootstrap.json")
STATE_KEYS = frozenset({"schema", "intent", "intent_digest", "history", "receipt"})
INTENT_KEYS = frozenset(
    {
        "local_repository",
        "git_common_dir",
        "target",
        "visibility",
        "base_branch",
        "base_sha",
        "normalized_remote",
        "actor",
        "evidence",
        "authority_scope",
    }
)
RECEIPT_KEYS = frozenset(
    {
        "schema",
        "status",
        "repository",
        "visibility",
        "local_repository",
        "git_common_dir",
        "normalized_remote",
        "base_branch",
        "local_sha",
        "remote_sha",
        "actor",
        "evidence",
        "observed_default_branch",
        "evidence_class",
        "authority_scope",
    }
)
EVENT_KINDS = frozenset(
    {
        "intent-persisted",
        "origin-observed",
        "repository-observed",
        "repository-created",
        "base-observed",
        "default-branch-placeholder-observed",
        "origin-configured",
        "base-published",
        "bootstrap-completed",
    }
)


class RepositoryBootstrapError(RuntimeError):
    """The requested bootstrap is ambiguous, contradictory, or unsafe."""


@dataclass(frozen=True)
class BootstrapRequest:
    repository: Path
    target: str
    visibility: str
    base_branch: str
    base_sha: str
    actor: str
    evidence: str

    @classmethod
    def normalize(
        cls,
        *,
        repository: str,
        target: str,
        visibility: str,
        base_branch: str,
        base_sha: str,
        actor: str,
        evidence: str,
    ) -> "BootstrapRequest":
        raw_repository = Path(repository)
        if not raw_repository.is_absolute():
            raise RepositoryBootstrapError("bootstrap repository path must be absolute")
        if not TARGET.fullmatch(target) or target.casefold().endswith(".git"):
            raise RepositoryBootstrapError("bootstrap target must be OWNER/REPOSITORY")
        if visibility != "private":
            raise RepositoryBootstrapError("repository bootstrap supports private visibility only")
        if not base_branch or base_branch != base_branch.strip():
            raise RepositoryBootstrapError("bootstrap base branch must be non-empty and trimmed")
        if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", base_sha):
            raise RepositoryBootstrapError("bootstrap base SHA must be an exact Git object ID")
        if not actor or actor != actor.strip() or not evidence or evidence != evidence.strip():
            raise RepositoryBootstrapError("bootstrap actor and evidence must be non-empty and trimmed")
        return cls(
            repository=raw_repository.resolve(),
            target=target.casefold(),
            visibility=visibility,
            base_branch=base_branch,
            base_sha=base_sha.casefold(),
            actor=actor,
            evidence=evidence,
        )


@dataclass(frozen=True)
class LocalRepository:
    root: Path
    common_git_dir: Path
    base_branch: str
    base_sha: str


class LocalBootstrap(Protocol):
    def inspect(self, request: BootstrapRequest) -> LocalRepository: ...
    def origin_urls(self, repository: LocalRepository) -> tuple[str, ...]: ...
    def add_origin(self, repository: LocalRepository, url: str) -> None: ...
    def push_base(self, repository: LocalRepository, branch: str, sha: str) -> None: ...


class GitHubBootstrap(Protocol):
    def get_repository(self, target: str) -> dict[str, Any]: ...
    def create_private_repository(self, target: str) -> dict[str, Any]: ...
    def get_branch(self, target: str, branch: str) -> dict[str, Any]: ...
    def set_default_branch(self, target: str, branch: str) -> dict[str, Any]: ...


def normalized_github_remote(value: str) -> str:
    """Normalize an uncredentialed GitHub HTTPS/SSH remote to one identity."""

    raw = value.strip()
    scp = re.fullmatch(r"git@github\.com:([^/]+)/(.+)", raw, re.IGNORECASE)
    if scp:
        owner, name = scp.groups()
    else:
        try:
            parsed = urlparse(raw)
            port = parsed.port
        except ValueError as error:
            raise RepositoryBootstrapError("origin URL contains an invalid port") from error
        if (
            parsed.scheme not in {"https", "ssh"}
            or parsed.hostname != "github.com"
            or port is not None
        ):
            raise RepositoryBootstrapError("origin must be a canonical HTTPS or SSH GitHub URL")
        if parsed.query or parsed.fragment or parsed.password:
            raise RepositoryBootstrapError("origin URL must not contain credentials or parameters")
        if parsed.scheme == "https" and parsed.username:
            raise RepositoryBootstrapError("HTTPS origin URL must not contain a username")
        if parsed.scheme == "ssh" and parsed.username not in {None, "git"}:
            raise RepositoryBootstrapError("SSH origin URL has an unexpected username")
        pieces = [piece for piece in parsed.path.split("/") if piece]
        if len(pieces) != 2:
            raise RepositoryBootstrapError("origin URL must identify one GitHub repository")
        owner, name = pieces
    name = name[:-4] if name.casefold().endswith(".git") else name
    target = f"{owner}/{name}"
    if not TARGET.fullmatch(target):
        raise RepositoryBootstrapError("origin URL contains an invalid repository identity")
    return f"github.com/{target.casefold()}"


def canonical_remote_url(target: str) -> str:
    return f"https://github.com/{target}.git"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


class BootstrapStateStore:
    """Integrity-wrapped, fsync-safe state serialized by one Git-common lock."""

    def __init__(self, common_git_dir: Path):
        self.path = common_git_dir / STATE_RELATIVE_PATH
        self.lock_path = self.path.with_suffix(".lock")

    @contextmanager
    def locked(self) -> Iterator[None]:
        if self.path.parent.is_symlink() or self.path.is_symlink() or self.lock_path.is_symlink():
            raise RepositoryBootstrapError("bootstrap state paths must not be symbolic links")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.parent.is_dir() or self.path.parent.is_symlink():
            raise RepositoryBootstrapError("bootstrap state directory is unsafe")
        with self.lock_path.open("a+", encoding="ascii") as handle:
            try:
                acquire_file_lock(handle, blocking=True)
            except OSError as error:
                raise RepositoryBootstrapError(f"bootstrap state is locked: {self.lock_path}") from error
            try:
                handle.seek(0)
                handle.truncate()
                handle.write(f"{os.getpid()}\n")
                handle.flush()
                os.fsync(handle.fileno())
                yield
            finally:
                release_file_lock(handle)

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeError) as error:
            raise RepositoryBootstrapError("bootstrap state is not valid UTF-8 JSON") from error
        if not isinstance(envelope, dict) or envelope.get("envelope_schema") != 1:
            raise RepositoryBootstrapError("bootstrap state envelope is malformed")
        payload = envelope.get("payload")
        if not isinstance(payload, dict) or envelope.get("integrity") != _digest(payload):
            raise RepositoryBootstrapError("bootstrap state integrity check failed")
        _validate_state(payload)
        return payload

    def save(self, state: dict[str, Any]) -> None:
        _validate_state(state)
        envelope = {"envelope_schema": 1, "integrity": _digest(state), "payload": state}
        content = _canonical_bytes(envelope) + b"\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        temp_path = Path(temporary)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
            if os.name != "nt":
                directory = os.open(self.path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            temp_path.unlink(missing_ok=True)


def _event_hash(sequence: int, previous: str | None, kind: str, details: dict[str, Any]) -> str:
    return _digest({"sequence": sequence, "previous": previous, "kind": kind, "details": details})


def _validate_state(state: dict[str, Any]) -> None:
    if (
        set(state) != STATE_KEYS
        or state.get("schema") != 1
        or not isinstance(state.get("intent"), dict)
        or set(state["intent"]) != INTENT_KEYS
        or state["intent"].get("authority_scope") != "one-private-repository-bootstrap"
    ):
        raise RepositoryBootstrapError("bootstrap state payload is malformed")
    if state.get("intent_digest") != _digest(state["intent"]):
        raise RepositoryBootstrapError("bootstrap intent digest is invalid")
    history = state.get("history")
    if not isinstance(history, list):
        raise RepositoryBootstrapError("bootstrap history is malformed")
    previous = None
    for sequence, event in enumerate(history, 1):
        if not isinstance(event, dict) or event.get("sequence") != sequence:
            raise RepositoryBootstrapError("bootstrap history sequence is invalid")
        details = event.get("details")
        kind = event.get("kind")
        if not isinstance(details, dict) or kind not in EVENT_KINDS:
            raise RepositoryBootstrapError("bootstrap history event is malformed")
        expected = _event_hash(sequence, previous, kind, details)
        event_key = _digest({"kind": kind, "details": details})
        if (
            event.get("previous") != previous
            or event.get("event_key") != event_key
            or event.get("hash") != expected
        ):
            raise RepositoryBootstrapError("bootstrap history hash chain is invalid")
        previous = expected
    if (
        not history
        or history[0]["kind"] != "intent-persisted"
        or history[0]["details"] != {"intent_digest": state["intent_digest"]}
    ):
        raise RepositoryBootstrapError("bootstrap history does not begin with its intent")
    receipt = state.get("receipt")
    completions = [event for event in history if event["kind"] == "bootstrap-completed"]
    if receipt is None:
        if completions:
            raise RepositoryBootstrapError("bootstrap history completes without a receipt")
    elif (
        not isinstance(receipt, dict)
        or set(receipt) != RECEIPT_KEYS
        or receipt.get("schema") != 1
        or receipt.get("status") != "completed"
        or receipt.get("repository") != state["intent"]["target"]
        or receipt.get("visibility") != "private"
        or receipt.get("local_repository") != state["intent"]["local_repository"]
        or receipt.get("git_common_dir") != state["intent"]["git_common_dir"]
        or receipt.get("normalized_remote") != state["intent"]["normalized_remote"]
        or receipt.get("base_branch") != state["intent"]["base_branch"]
        or receipt.get("local_sha") != state["intent"]["base_sha"]
        or receipt.get("remote_sha") != state["intent"]["base_sha"]
        or receipt.get("actor") != state["intent"]["actor"]
        or receipt.get("evidence") != state["intent"]["evidence"]
        or receipt.get("observed_default_branch") != state["intent"]["base_branch"]
        or receipt.get("evidence_class") != "live"
        or receipt.get("authority_scope") != "bootstrap-only-no-delivery-merge-or-wiki-sync"
        or len(completions) != 1
        or completions[0] != history[-1]
        or completions[0]["details"] != {"receipt_digest": _digest(receipt)}
    ):
        raise RepositoryBootstrapError("bootstrap completion receipt is malformed")


def _append_event(state: dict[str, Any], kind: str, details: dict[str, Any]) -> bool:
    event_key = _digest({"kind": kind, "details": details})
    if any(event.get("event_key") == event_key for event in state["history"]):
        return False
    sequence = len(state["history"]) + 1
    previous = state["history"][-1]["hash"] if state["history"] else None
    state["history"].append(
        {
            "sequence": sequence,
            "previous": previous,
            "kind": kind,
            "details": details,
            "event_key": event_key,
            "hash": _event_hash(sequence, previous, kind, details),
        }
    )
    return True


class GitLocalBootstrap:
    def __init__(self, runner: CommandRunner | None = None):
        self.runner = runner or SubprocessCommandRunner()

    def _run(self, repository: Path, command: list[str]) -> str:
        result = self.runner.run(command, cwd=repository)
        if result.returncode:
            detail = result.stderr or result.stdout or "Git command failed"
            raise RepositoryBootstrapError(f"{' '.join(command)} failed: {detail}")
        return result.stdout

    def inspect(self, request: BootstrapRequest) -> LocalRepository:
        root_value = self._run(request.repository, ["git", "rev-parse", "--show-toplevel"])
        root = Path(root_value).resolve()
        if root != request.repository:
            raise RepositoryBootstrapError("bootstrap path must be the local repository root")
        common_value = self._run(root, ["git", "rev-parse", "--git-common-dir"])
        common = Path(common_value)
        common = (root / common).resolve() if not common.is_absolute() else common.resolve()
        branch_check = self.runner.run(["git", "check-ref-format", "--branch", request.base_branch], cwd=root)
        if branch_check.returncode:
            raise RepositoryBootstrapError("bootstrap base branch is not a valid Git branch")
        sha = self._run(root, ["git", "rev-parse", "--verify", f"refs/heads/{request.base_branch}^{{commit}}"])
        if sha.casefold() != request.base_sha:
            raise RepositoryBootstrapError("local base branch does not match the authorized SHA")
        return LocalRepository(root=root, common_git_dir=common, base_branch=request.base_branch, base_sha=sha.casefold())

    def origin_urls(self, repository: LocalRepository) -> tuple[str, ...]:
        remotes = self._run(repository.root, ["git", "remote"])
        if "origin" not in remotes.splitlines():
            return ()
        fetch = self._run(repository.root, ["git", "remote", "get-url", "--all", "origin"])
        push = self._run(
            repository.root,
            ["git", "remote", "get-url", "--all", "--push", "origin"],
        )
        values = tuple(dict.fromkeys(line for line in (fetch + "\n" + push).splitlines() if line))
        if not values:
            raise RepositoryBootstrapError("origin exists without a usable URL")
        return values

    def add_origin(self, repository: LocalRepository, url: str) -> None:
        self._run(repository.root, ["git", "remote", "add", "origin", url])

    def push_base(self, repository: LocalRepository, branch: str, sha: str) -> None:
        self._run(repository.root, ["git", "push", "origin", f"{sha}:refs/heads/{branch}"])


class GitHubBootstrapClient:
    def __init__(self, repository: Path, runner: CommandRunner | None = None):
        self.executor = ProviderExecutor(GitHubProvider(), cwd=repository, mode="live", runner=runner)

    def get_repository(self, target: str) -> dict[str, Any]:
        return self.executor.execute(GET_REPOSITORY, target=target)

    def create_private_repository(self, target: str) -> dict[str, Any]:
        return self.executor.execute(CREATE_PRIVATE_REPOSITORY, target=target)

    def get_branch(self, target: str, branch: str) -> dict[str, Any]:
        return self.executor.execute(GET_REPOSITORY_BRANCH, target=target, branch=branch)

    def set_default_branch(self, target: str, branch: str) -> dict[str, Any]:
        return self.executor.execute(SET_DEFAULT_BRANCH, target=target, branch=branch)


class RepositoryBootstrapTransaction:
    def __init__(
        self,
        local: LocalBootstrap,
        provider: GitHubBootstrap,
        *,
        fault: Callable[[str], None] | None = None,
    ):
        self.local = local
        self.provider = provider
        self.fault = fault or (lambda _stage: None)

    @staticmethod
    def _intent(request: BootstrapRequest, repository: LocalRepository) -> dict[str, Any]:
        return {
            "local_repository": repository.root.as_posix(),
            "git_common_dir": repository.common_git_dir.as_posix(),
            "target": request.target,
            "visibility": request.visibility,
            "base_branch": request.base_branch,
            "base_sha": request.base_sha,
            "normalized_remote": normalized_github_remote(canonical_remote_url(request.target)),
            "actor": request.actor,
            "evidence": request.evidence,
            "authority_scope": "one-private-repository-bootstrap",
        }

    @staticmethod
    def _validate_repository(receipt: dict[str, Any], intent: dict[str, Any]) -> None:
        if receipt.get("state") != "present" or receipt.get("target") != intent["target"]:
            raise RepositoryBootstrapError("provider repository identity contradicts bootstrap intent")
        if receipt.get("private") is not True or receipt.get("visibility") != "private":
            raise RepositoryBootstrapError("provider repository visibility contradicts bootstrap intent")
        for key in ("clone_url", "ssh_url"):
            if normalized_github_remote(str(receipt.get(key, ""))) != intent["normalized_remote"]:
                raise RepositoryBootstrapError("provider repository URL contradicts bootstrap intent")

    @staticmethod
    def _validate_branch(receipt: dict[str, Any], intent: dict[str, Any]) -> None:
        if receipt.get("state") != "present" or receipt.get("branch") != intent["base_branch"]:
            raise RepositoryBootstrapError("provider base branch readback is absent or contradictory")
        if str(receipt.get("sha", "")).casefold() != intent["base_sha"]:
            raise RepositoryBootstrapError("remote base branch differs from the authorized SHA")

    @staticmethod
    def _check_origin(urls: tuple[str, ...], intent: dict[str, Any]) -> None:
        if any(normalized_github_remote(url) != intent["normalized_remote"] for url in urls):
            raise RepositoryBootstrapError("origin points to a different repository")

    @staticmethod
    def _record(store: BootstrapStateStore, state: dict[str, Any], kind: str, details: dict[str, Any]) -> None:
        if _append_event(state, kind, details):
            store.save(state)

    def apply(self, request: BootstrapRequest) -> dict[str, Any]:
        initial = self.local.inspect(request)
        store = BootstrapStateStore(initial.common_git_dir)
        with store.locked():
            repository = self.local.inspect(request)
            intent = self._intent(request, repository)
            state = store.load()
            replayed = state is not None
            if state is None:
                state = {"schema": 1, "intent": intent, "intent_digest": _digest(intent), "history": [], "receipt": None}
                _append_event(state, "intent-persisted", {"intent_digest": state["intent_digest"]})
                store.save(state)
            elif state["intent"] != intent:
                raise RepositoryBootstrapError("repository bootstrap intent is immutable")
            completed_replay = state["receipt"] is not None

            def record(kind: str, details: dict[str, Any]) -> None:
                if not completed_replay:
                    self._record(store, state, kind, details)

            origin_urls = self.local.origin_urls(repository)
            self._check_origin(origin_urls, intent)
            if completed_replay and not origin_urls:
                raise RepositoryBootstrapError(
                    "completed bootstrap origin is now absent"
                )
            record("origin-observed", {"state": "present" if origin_urls else "absent", "normalized_remote": intent["normalized_remote"] if origin_urls else None})

            remote = self.provider.get_repository(request.target)
            record("repository-observed", {"state": remote.get("state"), "target": request.target})
            if remote.get("state") == "absent":
                if completed_replay:
                    raise RepositoryBootstrapError(
                        "completed bootstrap repository is now absent"
                    )
                self.fault("pre-create")
                remote = self.provider.create_private_repository(request.target)
                self.fault("post-create")
                self._validate_repository(remote, intent)
                record("repository-created", {"target": request.target, "visibility": "private"})
            else:
                self._validate_repository(remote, intent)

            branch = self.provider.get_branch(request.target, request.base_branch)
            record("base-observed", {"state": branch.get("state"), "branch": request.base_branch, "sha": branch.get("sha")})
            if branch.get("state") == "present":
                self._validate_branch(branch, intent)
            elif completed_replay:
                raise RepositoryBootstrapError(
                    "completed bootstrap base branch is now absent"
                )
            elif remote.get("size") != 0:
                raise RepositoryBootstrapError(
                    "existing repository is not empty and lacks the authorized base"
                )

            default_branch = remote.get("default_branch")
            if default_branch and default_branch != request.base_branch:
                previous_default = self.provider.get_branch(request.target, str(default_branch))
                if previous_default.get("state") == "present":
                    raise RepositoryBootstrapError("provider default branch conflicts with bootstrap intent")
                record("default-branch-placeholder-observed", {"branch": default_branch, "state": "absent"})

            if not origin_urls:
                self.local.add_origin(repository, canonical_remote_url(request.target))
                self.fault("post-origin")
                origin_urls = self.local.origin_urls(repository)
                self._check_origin(origin_urls, intent)
                record("origin-configured", {"normalized_remote": intent["normalized_remote"]})

            if branch.get("state") == "absent":
                self.local.push_base(repository, request.base_branch, request.base_sha)
                self.fault("post-push")
                branch = self.provider.get_branch(request.target, request.base_branch)
                self._validate_branch(branch, intent)
                record("base-published", {"branch": request.base_branch, "sha": request.base_sha})

            remote = self.provider.get_repository(request.target)
            self._validate_repository(remote, intent)
            if remote.get("default_branch") != request.base_branch:
                if completed_replay:
                    raise RepositoryBootstrapError(
                        "completed bootstrap default branch is now contradictory"
                    )
                previous = remote.get("default_branch")
                if previous:
                    previous_receipt = self.provider.get_branch(request.target, str(previous))
                    if previous_receipt.get("state") == "present":
                        raise RepositoryBootstrapError("provider default branch conflicts with bootstrap intent")
                remote = self.provider.set_default_branch(request.target, request.base_branch)
                self.fault("post-default-branch")
                self._validate_repository(remote, intent)
            if remote.get("default_branch") != request.base_branch:
                raise RepositoryBootstrapError("provider default branch was not established")

            current_local = self.local.inspect(request)
            current_origins = self.local.origin_urls(current_local)
            self._check_origin(current_origins, intent)
            final_branch = self.provider.get_branch(request.target, request.base_branch)
            self._validate_branch(final_branch, intent)
            final_remote = self.provider.get_repository(request.target)
            self._validate_repository(final_remote, intent)
            if final_remote.get("default_branch") != request.base_branch:
                raise RepositoryBootstrapError("final default-branch readback is contradictory")
            self.fault("post-readback")

            receipt = {
                "schema": 1,
                "status": "completed",
                "repository": request.target,
                "visibility": "private",
                "local_repository": current_local.root.as_posix(),
                "git_common_dir": current_local.common_git_dir.as_posix(),
                "normalized_remote": intent["normalized_remote"],
                "base_branch": request.base_branch,
                "local_sha": request.base_sha,
                "remote_sha": final_branch["sha"].casefold(),
                "actor": request.actor,
                "evidence": request.evidence,
                "observed_default_branch": final_remote["default_branch"],
                "evidence_class": "live",
                "authority_scope": "bootstrap-only-no-delivery-merge-or-wiki-sync",
            }
            if state["receipt"] is not None:
                if state["receipt"] != receipt:
                    raise RepositoryBootstrapError("bootstrap completion receipt is immutable")
            else:
                state["receipt"] = receipt
                _append_event(state, "bootstrap-completed", {"receipt_digest": _digest(receipt)})
                store.save(state)
            return {
                "state_path": store.path.as_posix(),
                "intent_digest": state["intent_digest"],
                "history_events": len(state["history"]),
                "replayed": replayed,
                "receipt": receipt,
            }


def bootstrap_private_github_repository(
    request: BootstrapRequest,
    *,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    command_runner = runner or SubprocessCommandRunner()
    return RepositoryBootstrapTransaction(
        GitLocalBootstrap(command_runner),
        GitHubBootstrapClient(request.repository, command_runner),
    ).apply(request)
