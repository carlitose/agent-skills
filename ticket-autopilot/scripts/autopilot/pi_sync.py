"""Exact-head synchronization of integrated agent-skills into a local Pi install."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Protocol

from .file_lock import acquire_file_lock, release_file_lock
from .git_ops import CommandResult


OID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
SKILL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
GIT_PACKAGE = re.compile(
    r"^git:github\.com/carlitose/agent-skills(?:@[0-9A-Za-z._/-]+)?$",
    re.IGNORECASE,
)
MANIFEST_NAME = ".agent-skills-install-manifest.json"
STATE_SCHEMA = 1
STATE_KEYS = frozenset(
    {
        "schema",
        "intent",
        "intent_digest",
        "phases",
        "owned_manifest_digest",
        "settings_before_digest",
        "settings_after_digest",
        "receipt",
        "error",
    }
)
PHASES = (
    "intent-persisted",
    "checkout-materialized",
    "skills-replaced",
    "pi-install-observed",
    "settings-reconciled",
    "pi-list-verified",
    "sync-completed",
)


class PiSyncError(RuntimeError):
    """A local Pi synchronization request is unsafe or contradictory."""


class PiRunner(Protocol):
    def run(self, command: list[str], *, cwd: Path) -> CommandResult: ...


class SubprocessPiRunner:
    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        return CommandResult(completed.stdout, completed.stderr, completed.returncode)


@dataclass(frozen=True)
class PiSyncRequest:
    source_repository: Path
    expected_head: str
    expected_tree: str
    checkout: Path
    agents_root: Path
    settings_path: Path
    actor: str
    evidence: str
    adopt_existing_owned: bool
    replace_package_source: bool

    @classmethod
    def normalize(
        cls,
        *,
        source_repository: str,
        expected_head: str,
        expected_tree: str,
        checkout: str,
        agents_root: str,
        settings_path: str,
        actor: str,
        evidence: str,
        adopt_existing_owned: bool,
        replace_package_source: bool,
    ) -> "PiSyncRequest":
        paths = {
            "source_repository": Path(source_repository),
            "checkout": Path(checkout),
            "agents_root": Path(agents_root),
            "settings_path": Path(settings_path),
        }
        if any(not value.is_absolute() for value in paths.values()):
            raise PiSyncError("Pi sync paths must be absolute")
        if not OID.fullmatch(expected_head) or not OID.fullmatch(expected_tree):
            raise PiSyncError("Pi sync head and tree must be exact Git object IDs")
        if any(not value or value != value.strip() for value in (actor, evidence)):
            raise PiSyncError("Pi sync actor and evidence must be non-empty and trimmed")
        source = paths["source_repository"].resolve()
        target = paths["checkout"].resolve()
        agents = paths["agents_root"].resolve()
        settings = paths["settings_path"].resolve()
        def overlaps(left: Path, right: Path) -> bool:
            return left == right or left in right.parents or right in left.parents

        if overlaps(target, source) or overlaps(target, agents):
            raise PiSyncError("Pi sync checkout must be a dedicated path")
        if overlaps(agents, source) or overlaps(agents, settings.parent):
            raise PiSyncError("Pi sync skill and settings roots must be separate")
        if overlaps(source, settings.parent):
            raise PiSyncError("Pi sync source and settings roots must be separate")
        if settings.name != "settings.json":
            raise PiSyncError("Pi sync settings path must end in settings.json")
        return cls(
            source_repository=source,
            expected_head=expected_head,
            expected_tree=expected_tree,
            checkout=target,
            agents_root=agents,
            settings_path=settings,
            actor=actor,
            evidence=evidence,
            adopt_existing_owned=adopt_existing_owned,
            replace_package_source=replace_package_source,
        )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_write(path: Path, content: bytes, *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary)
    try:
        if mode is not None:
            os.chmod(temporary_path, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        temporary_path.unlink(missing_ok=True)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.exists():
        shutil.rmtree(path)


def _run_git(cwd: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=cwd, text=True, capture_output=True, check=False
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip() or "Git failed"
        raise PiSyncError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout.strip()


def _ensure_safe_parent(path: Path, label: str) -> None:
    existing = path
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    if existing.is_symlink() or not existing.is_dir():
        raise PiSyncError(f"Pi sync {label} parent is unsafe")


def _tree_digest(root: Path) -> str:
    entries: list[dict[str, Any]] = []
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        directories.sort()
        files.sort()
        for name in list(directories):
            path = current_path / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise PiSyncError("Pi sync owned skill contains an unsafe directory")
            entries.append(
                {
                    "path": path.relative_to(root).as_posix() + "/",
                    "mode": stat.S_IMODE(mode),
                    "sha256": None,
                }
            )
        for name in files:
            path = current_path / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise PiSyncError("Pi sync owned skill contains a symlink or special file")
            relative = path.relative_to(root).as_posix()
            entries.append(
                {
                    "path": relative,
                    "mode": stat.S_IMODE(mode),
                    "sha256": _file_digest(path),
                }
            )
    return _digest(entries)


def _owned_skills(checkout: Path) -> dict[str, dict[str, Any]]:
    if any(
        line.startswith("160000 ")
        for line in _run_git(checkout, "ls-files", "--stage").splitlines()
    ):
        raise PiSyncError("Pi sync source contains a submodule")
    try:
        package = json.loads((checkout / "package.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeError, json.JSONDecodeError) as error:
        raise PiSyncError("Pi sync package.json is missing or malformed") from error
    manifest = package.get("pi") if isinstance(package, dict) else None
    skill_globs = manifest.get("skills") if isinstance(manifest, dict) else None
    if (
        package.get("name") != "carlitose-agent-skills-pi"
        or skill_globs != ["./*/SKILL.md"]
    ):
        raise PiSyncError("Pi sync requires the canonical agent-skills package manifest")
    result: dict[str, dict[str, Any]] = {}
    for skill_file in sorted(checkout.glob("*/SKILL.md")):
        root = skill_file.parent
        if root.is_symlink() or skill_file.is_symlink() or not skill_file.is_file():
            raise PiSyncError("Pi sync skill roots must be regular directories")
        name = root.name
        if not SKILL_NAME.fullmatch(name) or name in result:
            raise PiSyncError("Pi sync skill name is unsafe or duplicated")
        result[name] = {"digest": _tree_digest(root)}
    if not result:
        raise PiSyncError("Pi sync source contains no owned skills")
    return result


def _load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise PiSyncError("Pi sync owned-skill manifest is unsafe")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise PiSyncError("Pi sync owned-skill manifest is malformed") from error
    skills = document.get("skills") if isinstance(document, dict) else None
    if (
        set(document) != {"schema", "source_repository", "head", "tree", "skills"}
        or document.get("schema") != 1
        or not isinstance(document.get("source_repository"), str)
        or not Path(document["source_repository"]).is_absolute()
        or not isinstance(document.get("head"), str)
        or not OID.fullmatch(document["head"])
        or not isinstance(document.get("tree"), str)
        or not OID.fullmatch(document["tree"])
        or not isinstance(skills, dict)
        or any(
            not isinstance(name, str)
            or not SKILL_NAME.fullmatch(name)
            or not isinstance(value, dict)
            or set(value) != {"digest"}
            or not _is_sha256(value["digest"])
            for name, value in skills.items()
        )
    ):
        raise PiSyncError("Pi sync owned-skill manifest is invalid")
    return document


def _assert_owned_install(agents_root: Path, manifest: dict[str, Any]) -> None:
    for name, expected in manifest["skills"].items():
        destination = agents_root / name
        if (
            destination.is_symlink()
            or not destination.is_dir()
            or _tree_digest(destination) != expected["digest"]
        ):
            raise PiSyncError(f"Pi sync installed skill drifted: {name}")


def _pi_list_package_sources(output: str) -> list[str]:
    sources: list[str] = []
    for line in output.splitlines():
        if not line.startswith("  ") or line.startswith("    "):
            continue
        value = line[2:].strip()
        if value.endswith(" (filtered)"):
            value = value[: -len(" (filtered)")]
        if value:
            sources.append(value)
    return sources


def _source_for(entry: object) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict) and isinstance(entry.get("source"), str):
        return entry["source"]
    return None


def _preinstall_package_template(
    document: dict[str, Any], checkout: Path, *, replace_package_source: bool
) -> dict[str, Any]:
    packages = document.get("packages")
    if not isinstance(packages, list):
        raise PiSyncError("Pi settings packages must be a list")
    local = checkout.as_posix()
    local_entries = [entry for entry in packages if _source_for(entry) == local]
    git_entries = [
        entry
        for entry in packages
        if isinstance(_source_for(entry), str)
        and GIT_PACKAGE.fullmatch(_source_for(entry) or "")
    ]
    if len(local_entries) > 1 or len(git_entries) > 1:
        raise PiSyncError("Pi settings contain duplicate agent-skills packages")
    if local_entries and git_entries:
        raise PiSyncError("Pi settings contain contradictory agent-skills package sources")
    if git_entries:
        if not replace_package_source:
            raise PiSyncError("Pi package source replacement was not authorized")
        entry = git_entries[0]
    elif local_entries:
        if replace_package_source:
            raise PiSyncError("Pi package source replacement target is absent")
        entry = local_entries[0]
    else:
        if replace_package_source:
            raise PiSyncError("Pi package source replacement target is absent")
        return {}
    if not isinstance(entry, dict) or entry.get("skills") != []:
        raise PiSyncError("existing agent-skills package filter is contradictory")
    return {key: value for key, value in entry.items() if key != "source"}


def _reconcile_settings(
    document: dict[str, Any],
    checkout: Path,
    *,
    replace_package_source: bool,
    package_template: dict[str, Any] | None = None,
) -> dict[str, Any]:
    packages = document.get("packages")
    if not isinstance(packages, list):
        raise PiSyncError("Pi settings packages must be a list")
    local = checkout.as_posix()
    related: list[tuple[int, object, str]] = []
    for index, entry in enumerate(packages):
        source = _source_for(entry)
        if source == local or (isinstance(source, str) and GIT_PACKAGE.fullmatch(source)):
            related.append((index, entry, source))
    local_entries = [item for item in related if item[2] == local]
    git_entries = [item for item in related if item[2] != local]
    if len(local_entries) != 1:
        raise PiSyncError("pi install readback must create exactly one local package entry")
    if len(git_entries) > 1:
        raise PiSyncError("Pi settings contain duplicate agent-skills Git packages")
    if git_entries and not replace_package_source:
        raise PiSyncError("Pi package source replacement was not authorized")
    template = dict(package_template or {})
    if package_template is None:
        old = git_entries[0][1] if git_entries else local_entries[0][1]
        if isinstance(old, dict):
            template = {key: value for key, value in old.items() if key != "source"}
    template["skills"] = []
    replacement = {"source": local, **template}
    first = min(item[0] for item in related)
    unrelated = [
        entry
        for index, entry in enumerate(packages)
        if all(index != item[0] for item in related)
    ]
    unrelated.insert(first, replacement)
    result = dict(document)
    result["packages"] = unrelated
    return result


def integrated_pi_sync_binding(
    document: dict[str, Any], ticket_id: str
) -> tuple[str, str]:
    tickets = document.get("tickets")
    ticket = tickets.get(ticket_id) if isinstance(tickets, dict) else None
    lineage = ticket.get("delivery_lineage") if isinstance(ticket, dict) else None
    if (
        not isinstance(ticket, dict)
        or ticket.get("state") != "integrated"
        or ticket.get("disposition") != "completed"
        or not isinstance(lineage, dict)
        or not isinstance(lineage.get("head_sha"), str)
        or not OID.fullmatch(lineage["head_sha"])
    ):
        raise PiSyncError("Pi sync requires a durably integrated ticket")
    return lineage["head_sha"], ticket_id


def _validate_state(payload: dict[str, Any]) -> None:
    phases = payload.get("phases")
    intent = payload.get("intent")
    receipt = payload.get("receipt")
    error = payload.get("error")
    if (
        set(payload) != STATE_KEYS
        or payload.get("schema") != STATE_SCHEMA
        or not isinstance(intent, dict)
        or payload.get("intent_digest") != _digest(intent)
        or not isinstance(phases, list)
        or len(phases) != len(set(phases))
        or phases != list(PHASES[: len(phases)])
        or payload.get("owned_manifest_digest") is not None
        and not _is_sha256(payload.get("owned_manifest_digest"))
        or payload.get("settings_before_digest") not in {None, "absent"}
        and not _is_sha256(payload.get("settings_before_digest"))
        or payload.get("settings_after_digest") is not None
        and not _is_sha256(payload.get("settings_after_digest"))
        or error is not None
        and (
            not isinstance(error, dict)
            or set(error) != {"type", "message"}
            or not all(isinstance(value, str) for value in error.values())
        )
    ):
        raise PiSyncError("Pi sync state payload is invalid")
    if receipt is not None:
        required = {
            "schema",
            "status",
            "source_repository",
            "head",
            "tree",
            "checkout",
            "agents_root",
            "settings_path",
            "owned_manifest_digest",
            "settings_before_digest",
            "settings_after_digest",
            "actor",
            "evidence",
            "pi_install",
            "pi_list",
            "reload_required",
            "authority_scope",
            "limitations",
        }
        if (
            not isinstance(receipt, dict)
            or set(receipt) != required
            or receipt.get("schema") != 1
            or receipt.get("status") != "completed"
            or receipt.get("source_repository") != intent.get("source_repository")
            or receipt.get("head") != intent.get("expected_head")
            or receipt.get("tree") != intent.get("expected_tree")
            or receipt.get("checkout") != intent.get("checkout")
            or receipt.get("agents_root") != intent.get("agents_root")
            or receipt.get("settings_path") != intent.get("settings_path")
            or receipt.get("actor") != intent.get("actor")
            or receipt.get("evidence") != intent.get("evidence")
            or receipt.get("owned_manifest_digest")
            != payload.get("owned_manifest_digest")
            or receipt.get("settings_before_digest")
            != payload.get("settings_before_digest")
            or receipt.get("settings_after_digest")
            != payload.get("settings_after_digest")
            or receipt.get("pi_install") != "observed"
            or receipt.get("pi_list") != "verified"
            or receipt.get("reload_required") is not True
            or receipt.get("authority_scope")
            != "local-sync-only-no-pi-self-update-or-reload"
            or receipt.get("limitations")
            != ["Active Pi session was not reloaded; /reload is required."]
            or phases != list(PHASES)
        ):
            raise PiSyncError("Pi sync completion receipt is invalid")


class PiSyncStateStore:
    def __init__(self, path: Path, *, lock_path: Path | None = None):
        self.path = path
        self.lock_path = lock_path or path.with_suffix(".lock")

    @contextmanager
    def locked(self) -> Iterator[None]:
        _ensure_safe_parent(self.path.parent, "state")
        _ensure_safe_parent(self.lock_path.parent, "lock")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if (
            self.path.parent.is_symlink()
            or self.lock_path.parent.is_symlink()
            or self.path.is_symlink()
            or self.lock_path.is_symlink()
        ):
            raise PiSyncError("Pi sync state paths must not be symbolic links")
        with self.lock_path.open("a+", encoding="ascii") as handle:
            try:
                acquire_file_lock(handle, blocking=True)
            except OSError as error:
                raise PiSyncError("Pi sync state is locked") from error
            try:
                yield
            finally:
                release_file_lock(handle)

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise PiSyncError("Pi sync state is malformed") from error
        payload = envelope.get("payload") if isinstance(envelope, dict) else None
        if (
            envelope.get("envelope_schema") != 1
            or not isinstance(payload, dict)
            or envelope.get("integrity") != _digest(payload)
        ):
            raise PiSyncError("Pi sync state integrity check failed")
        _validate_state(payload)
        return payload

    def save(self, payload: dict[str, Any]) -> None:
        _validate_state(payload)
        envelope = {
            "envelope_schema": 1,
            "integrity": _digest(payload),
            "payload": payload,
        }
        _atomic_write(self.path, _canonical_bytes(envelope) + b"\n")


class PiSyncTransaction:
    def __init__(
        self,
        *,
        runner: PiRunner | None = None,
        fault: Callable[[str], None] | None = None,
    ):
        self.runner = runner or SubprocessPiRunner()
        self.fault = fault or (lambda _phase: None)

    @staticmethod
    def _intent(request: PiSyncRequest) -> dict[str, Any]:
        return {
            "schema": 1,
            "source_repository": request.source_repository.as_posix(),
            "expected_head": request.expected_head,
            "expected_tree": request.expected_tree,
            "checkout": request.checkout.as_posix(),
            "agents_root": request.agents_root.as_posix(),
            "settings_path": request.settings_path.as_posix(),
            "actor": request.actor,
            "evidence": request.evidence,
            "adopt_existing_owned": request.adopt_existing_owned,
            "replace_package_source": request.replace_package_source,
            "authority_scope": "exact-integrated-agent-skills-local-pi-sync",
        }

    @staticmethod
    def _record(store: PiSyncStateStore, state: dict[str, Any], phase: str) -> None:
        if phase not in state["phases"]:
            state["phases"].append(phase)
            store.save(state)

    @staticmethod
    def _materialize(request: PiSyncRequest) -> None:
        source = request.source_repository
        if _run_git(source, "rev-parse", "--show-toplevel") != source.as_posix():
            raise PiSyncError("Pi sync source must be a repository root")
        head = _run_git(source, "rev-parse", f"{request.expected_head}^{{commit}}")
        tree = _run_git(source, "rev-parse", f"{request.expected_head}^{{tree}}")
        if head != request.expected_head or tree != request.expected_tree:
            raise PiSyncError("Pi sync source commit or tree contradicts the request")
        _ensure_safe_parent(request.checkout, "checkout")
        created = not request.checkout.exists()
        if created:
            request.checkout.parent.mkdir(parents=True, exist_ok=True)
            completed = subprocess.run(
                [
                    "git",
                    "clone",
                    "--no-checkout",
                    "--shared",
                    source.as_posix(),
                    request.checkout.as_posix(),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode:
                shutil.rmtree(request.checkout, ignore_errors=True)
                raise PiSyncError(
                    "Pi sync checkout clone failed: "
                    + (completed.stderr.strip() or completed.stdout.strip())
                )
            try:
                _run_git(request.checkout, "config", "agentSkillsPiSync.owned", "true")
            except PiSyncError:
                shutil.rmtree(request.checkout, ignore_errors=True)
                raise
        if request.checkout.is_symlink() or not request.checkout.is_dir():
            raise PiSyncError("Pi sync checkout is unsafe")
        if _run_git(request.checkout, "rev-parse", "--show-toplevel") != request.checkout.as_posix():
            raise PiSyncError("Pi sync checkout must be a dedicated repository root")
        marker = subprocess.run(
            ["git", "config", "--get", "agentSkillsPiSync.owned"],
            cwd=request.checkout,
            text=True,
            capture_output=True,
            check=False,
        )
        if marker.returncode or marker.stdout.strip() != "true":
            raise PiSyncError("Pi sync checkout lacks the dedicated ownership marker")
        if not created and _run_git(
            request.checkout, "status", "--porcelain", "--ignored"
        ):
            raise PiSyncError("Pi sync checkout is dirty or contains ignored files")
        _run_git(request.checkout, "fetch", "--no-tags", source.as_posix(), request.expected_head)
        _run_git(request.checkout, "reset", "--hard", request.expected_head)
        if (
            _run_git(request.checkout, "rev-parse", "HEAD") != request.expected_head
            or _run_git(request.checkout, "rev-parse", "HEAD^{tree}")
            != request.expected_tree
            or _run_git(
                request.checkout, "status", "--porcelain", "--ignored"
            )
        ):
            raise PiSyncError("Pi sync checkout readback is contradictory")

    @staticmethod
    def _backup_settings(request: PiSyncRequest, backup: Path) -> str:
        marker = backup / "settings.absent"
        target = backup / "settings.json"
        if target.exists():
            return _file_digest(target)
        if marker.exists():
            return "absent"
        if request.settings_path.exists():
            if request.settings_path.is_symlink() or not request.settings_path.is_file():
                raise PiSyncError("Pi settings path is unsafe")
            shutil.copy2(request.settings_path, target)
            return _file_digest(target)
        marker.touch()
        return "absent"

    @staticmethod
    def _sync_skills(
        request: PiSyncRequest,
        state: dict[str, Any],
        state_root: Path,
        skills: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        agents = request.agents_root
        _ensure_safe_parent(agents, "agents root")
        agents.mkdir(parents=True, exist_ok=True)
        if agents.is_symlink() or not agents.is_dir():
            raise PiSyncError("Pi sync agents root is unsafe")
        manifest_path = agents / MANIFEST_NAME
        previous = _load_manifest(manifest_path)
        if (
            previous is not None
            and previous["source_repository"]
            != request.source_repository.as_posix()
        ):
            raise PiSyncError("Pi sync owned-skill manifest source drifted")
        previous_skills = previous["skills"] if previous else {}
        current_names = set(skills)
        previous_names = set(previous_skills)
        for name in current_names | previous_names:
            destination = agents / name
            exists = destination.exists() or destination.is_symlink()
            if (
                exists
                and name in current_names
                and name not in previous_names
                and not request.adopt_existing_owned
            ):
                raise PiSyncError(
                    f"Pi sync existing skill lacks ownership proof: {name}"
                )
            if exists and (destination.is_symlink() or not destination.is_dir()):
                raise PiSyncError("Pi sync destination skill is not a regular directory")
            if (
                exists
                and name in previous_names
                and _tree_digest(destination) != previous_skills[name]["digest"]
            ):
                raise PiSyncError(f"Pi sync previously owned skill drifted: {name}")
        stage = state_root / "staging"
        backup = state_root / "backup" / "skills"
        stage.mkdir(parents=True, exist_ok=True)
        backup.mkdir(parents=True, exist_ok=True)
        absent = backup / "absent"
        absent.mkdir(exist_ok=True)
        ownership_path = backup / "ownership.json"
        if not ownership_path.exists():
            _atomic_write(
                ownership_path,
                _canonical_bytes(sorted(current_names | previous_names)) + b"\n",
            )
        if not (backup / MANIFEST_NAME).exists() and manifest_path.exists():
            shutil.copy2(manifest_path, backup / MANIFEST_NAME)
        if previous is None:
            (backup / "manifest.absent").touch(exist_ok=True)
        for name in sorted(current_names):
            staged = stage / name
            if staged.exists():
                shutil.rmtree(staged)
            shutil.copytree(request.checkout / name, staged, symlinks=False)
            if _tree_digest(staged) != skills[name]["digest"]:
                raise PiSyncError("Pi sync staged skill digest changed")
        for name in sorted(current_names | previous_names):
            destination = agents / name
            saved = backup / name
            absent_marker = absent / name
            exists = destination.exists() or destination.is_symlink()
            if exists and not saved.exists() and not absent_marker.exists():
                os.replace(destination, saved)
            elif exists:
                _remove_path(destination)
            elif not saved.exists() and not absent_marker.exists():
                absent_marker.touch()
            if name in current_names:
                replacement = stage / name
                os.replace(replacement, destination)
        manifest = {
            "schema": 1,
            "source_repository": request.source_repository.as_posix(),
            "head": request.expected_head,
            "tree": request.expected_tree,
            "skills": skills,
        }
        _atomic_write(manifest_path, _canonical_bytes(manifest) + b"\n")
        state["owned_manifest_digest"] = _digest(manifest)
        return manifest

    @staticmethod
    def _rollback(request: PiSyncRequest, state_root: Path) -> None:
        backup = state_root / "backup"
        skill_backup = backup / "skills"
        manifest_path = request.agents_root / MANIFEST_NAME
        if skill_backup.exists():
            ownership_path = skill_backup / "ownership.json"
            try:
                names = json.loads(ownership_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, UnicodeError, json.JSONDecodeError) as error:
                raise PiSyncError("Pi sync rollback ownership is missing or malformed") from error
            if (
                not isinstance(names, list)
                or len(names) != len(set(names))
                or any(not isinstance(name, str) or not SKILL_NAME.fullmatch(name) for name in names)
            ):
                raise PiSyncError("Pi sync rollback ownership is invalid")
            for name in sorted(names):
                destination = request.agents_root / name
                _remove_path(destination)
                saved = skill_backup / name
                if saved.exists():
                    os.replace(saved, destination)
            saved_manifest = skill_backup / MANIFEST_NAME
            if saved_manifest.exists():
                os.replace(saved_manifest, manifest_path)
            elif (skill_backup / "manifest.absent").exists():
                manifest_path.unlink(missing_ok=True)
        settings_backup = backup / "settings.json"
        if settings_backup.exists():
            _atomic_write(
                request.settings_path,
                settings_backup.read_bytes(),
                mode=stat.S_IMODE(settings_backup.stat().st_mode),
            )
        elif (backup / "settings.absent").exists():
            request.settings_path.unlink(missing_ok=True)

    def _pi(self, request: PiSyncRequest, script: str, *arguments: str) -> CommandResult:
        command = ["zsh", "-lic", script, "agent-skills-pi-sync", *arguments]
        result = self.runner.run(command, cwd=request.checkout)
        if result.returncode:
            detail = result.stderr.strip() or result.stdout.strip() or "Pi command failed"
            raise PiSyncError(detail)
        return result

    def apply(self, request: PiSyncRequest, *, state_path: Path) -> dict[str, Any]:
        store = PiSyncStateStore(
            state_path,
            lock_path=request.settings_path.parent / ".agent-skills-pi-sync.lock",
        )
        with store.locked():
            intent = self._intent(request)
            state = store.load()
            if state is None:
                state = {
                    "schema": STATE_SCHEMA,
                    "intent": intent,
                    "intent_digest": _digest(intent),
                    "phases": ["intent-persisted"],
                    "owned_manifest_digest": None,
                    "settings_before_digest": None,
                    "settings_after_digest": None,
                    "receipt": None,
                    "error": None,
                }
                store.save(state)
            elif state.get("intent") != intent or state.get("intent_digest") != _digest(intent):
                raise PiSyncError("Pi sync intent is immutable")
            state_root = (
                request.agents_root
                / f".agent-skills-pi-sync-{state['intent_digest']}"
            )
            if state_root.is_symlink() or (
                state_root.exists() and not state_root.is_dir()
            ):
                state["error"] = {
                    "type": "PiSyncError",
                    "message": "Pi sync transaction root is unsafe",
                }
                store.save(state)
                raise PiSyncError("Pi sync transaction root is unsafe")
            if state.get("receipt") is not None:
                self._materialize(request)
                manifest = _load_manifest(request.agents_root / MANIFEST_NAME)
                if (
                    manifest is None
                    or _digest(manifest) != state.get("owned_manifest_digest")
                ):
                    raise PiSyncError("completed Pi sync owned manifest drifted")
                _assert_owned_install(request.agents_root, manifest)
                listed = self._pi(
                    request,
                    'PI_CODING_AGENT_DIR="$1" pi list',
                    request.settings_path.parent.as_posix(),
                )
                if _pi_list_package_sources(listed.stdout).count(request.checkout.as_posix()) != 1:
                    raise PiSyncError("completed Pi sync package readback drifted")
                shutil.rmtree(state_root, ignore_errors=True)
                return {
                    "schema": 1,
                    "status": "completed",
                    "replayed": True,
                    "receipt": state["receipt"],
                    "phases": list(state["phases"]),
                    "reload_required": True,
                }

            if state_root.exists():
                try:
                    self._rollback(request, state_root)
                except Exception as error:
                    state["error"] = {
                        "type": type(error).__name__,
                        "message": f"Pi sync recovery failed: {error}",
                    }
                    store.save(state)
                    raise PiSyncError("Pi sync recovery requires manual repair") from error
                shutil.rmtree(state_root)
            backup = state_root / "backup"
            try:
                self._materialize(request)
                self._record(store, state, "checkout-materialized")
                self.fault("checkout-materialized")

                skills = _owned_skills(request.checkout)
                manifest = self._sync_skills(request, state, state_root, skills)
                _assert_owned_install(request.agents_root, manifest)
                store.save(state)
                self._record(store, state, "skills-replaced")
                self.fault("skills-replaced")

                state["settings_before_digest"] = self._backup_settings(
                    request, backup
                )
                if state["settings_before_digest"] == "absent":
                    settings_before: dict[str, Any] = {"packages": []}
                else:
                    try:
                        settings_before = json.loads(
                            request.settings_path.read_text(encoding="utf-8")
                        )
                    except (UnicodeError, json.JSONDecodeError) as error:
                        raise PiSyncError(
                            "Pi settings before install are malformed"
                        ) from error
                package_template = _preinstall_package_template(
                    settings_before,
                    request.checkout,
                    replace_package_source=request.replace_package_source,
                )
                store.save(state)
                self._pi(
                    request,
                    'PI_CODING_AGENT_DIR="$1" pi install "$2"',
                    request.settings_path.parent.as_posix(),
                    request.checkout.as_posix(),
                )
                self._record(store, state, "pi-install-observed")
                self.fault("pi-install-observed")

                if (
                    request.settings_path.is_symlink()
                    or not request.settings_path.is_file()
                ):
                    raise PiSyncError("Pi settings readback is unsafe")
                settings_mode = stat.S_IMODE(request.settings_path.stat().st_mode)
                try:
                    settings = json.loads(request.settings_path.read_text(encoding="utf-8"))
                except (FileNotFoundError, UnicodeError, json.JSONDecodeError) as error:
                    raise PiSyncError("Pi settings readback is missing or malformed") from error
                reconciled = _reconcile_settings(
                    settings,
                    request.checkout,
                    replace_package_source=request.replace_package_source,
                    package_template=package_template,
                )
                _atomic_write(
                    request.settings_path,
                    _canonical_bytes(reconciled) + b"\n",
                    mode=settings_mode,
                )
                state["settings_after_digest"] = _file_digest(request.settings_path)
                store.save(state)
                self._record(store, state, "settings-reconciled")
                self.fault("settings-reconciled")

                listed = self._pi(
                    request,
                    'PI_CODING_AGENT_DIR="$1" pi list',
                    request.settings_path.parent.as_posix(),
                )
                if _pi_list_package_sources(listed.stdout).count(request.checkout.as_posix()) != 1:
                    raise PiSyncError("pi list did not prove exactly one local package")
                self._record(store, state, "pi-list-verified")
                self.fault("pi-list-verified")

                receipt = {
                    "schema": 1,
                    "status": "completed",
                    "source_repository": request.source_repository.as_posix(),
                    "head": request.expected_head,
                    "tree": request.expected_tree,
                    "checkout": request.checkout.as_posix(),
                    "agents_root": request.agents_root.as_posix(),
                    "settings_path": request.settings_path.as_posix(),
                    "owned_manifest_digest": state["owned_manifest_digest"],
                    "settings_before_digest": state["settings_before_digest"],
                    "settings_after_digest": state["settings_after_digest"],
                    "actor": request.actor,
                    "evidence": request.evidence,
                    "pi_install": "observed",
                    "pi_list": "verified",
                    "reload_required": True,
                    "authority_scope": "local-sync-only-no-pi-self-update-or-reload",
                    "limitations": [
                        "Active Pi session was not reloaded; /reload is required."
                    ],
                }
                state["receipt"] = receipt
                state["error"] = None
                self._record(store, state, "sync-completed")
                store.save(state)
                shutil.rmtree(state_root, ignore_errors=True)
                return {
                    "schema": 1,
                    "status": "completed",
                    "replayed": False,
                    "receipt": receipt,
                    "phases": list(state["phases"]),
                    "reload_required": True,
                }
            except Exception as error:
                try:
                    self._rollback(request, state_root)
                    shutil.rmtree(state_root, ignore_errors=True)
                except Exception as rollback_error:
                    state["error"] = {
                        "type": type(rollback_error).__name__,
                        "message": f"Pi sync rollback failed: {rollback_error}",
                    }
                    store.save(state)
                    raise PiSyncError(
                        "Pi sync rollback requires manual repair"
                    ) from error
                state["error"] = {"type": type(error).__name__, "message": str(error)}
                store.save(state)
                raise


def synchronize_local_pi(
    request: PiSyncRequest,
    *,
    state_path: Path,
    runner: PiRunner | None = None,
    fault: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    return PiSyncTransaction(runner=runner, fault=fault).apply(
        request, state_path=state_path
    )
