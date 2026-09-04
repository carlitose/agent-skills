from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import shutil
import stat
import sys
import tempfile
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence

from .git_ops import CommandRunner, GitError, repository_root, run_git
from .kernel import Kernel, TransitionError
from .ledger import AtomicLedger
from .repository_authority import RepositoryBinding
from .providers import (
    CREATE_OR_UPDATE_PR,
    GET_APPROVALS,
    GET_CHECKS_AND_POLICIES,
    GET_PR_STATE,
    MERGE_EXPECTED_HEAD,
    MergeAuthorization,
    ProviderError,
    ProviderExecutor,
    detect_provider,
)


CONTRACT_VERSION = "ticket-post-integration-wiki-sync-v1"
SYNC_STEP = "wiki-sync"
TERMINAL_SYNC_STATUSES = {
    "skipped",
    "unchanged",
    "updated-directly",
    "merged-automatically",
}
SyncOperation = Callable[..., Mapping[str, Any]]
DeliveryOperation = Callable[..., Mapping[str, Any]]
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_TARGET_CONTRACT = "wiki-delivery-target-v1"
_RETRY_CONTRACT = "wiki-delivery-retry-v1"
_RETRY_AUTHORITY_EXCLUSIONS = [
    "provider",
    "push",
    "publication",
    "merge",
    "reconciliation",
    "cleanup",
    "pi-sync",
    "reload",
]
_RETRY_REQUEST_FIELDS = {
    "schema",
    "contract_version",
    "run_id",
    "ticket_id",
    "expected_record_sha256",
    "actor",
    "evidence",
    "target_receipt_sha256",
}
_TARGET_RECEIPT_FIELDS = {
    "schema",
    "contract_version",
    "run_repository_root",
    "project_root",
    "git_common_dir",
    "provider",
    "normalized_remote",
    "wiki_relative",
    "wiki_sync_ref",
    "candidate_tree_sha256",
    "manifest_sha256",
    "validation_receipt_sha256",
    "receipt_sha256",
}
_TERMINAL_DELIVERY_MARKERS = (
    "already merged without",
    "changed",
    "contradict",
    "differs",
    "diverged",
    "invalid",
    "missing",
    "non-regular",
    "outside",
    "simulated",
    "stale",
    "unsupported",
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _origin_id(kernel: Kernel, ticket_id: str, head_sha: str) -> str:
    return _digest(
        {
            "contract_version": CONTRACT_VERSION,
            "run_id": kernel.ledger["run_id"],
            "ticket_id": ticket_id,
            "integrated_head_sha": head_sha,
        }
    )


@lru_cache(maxsize=1)
def _load_sync_operation() -> SyncOperation:
    scripts = Path(__file__).resolve().parents[3] / "llm-wiki" / "scripts"
    module_path = scripts / "sync_project.py"
    if not module_path.is_file():
        raise TransitionError(
            f"llm-wiki sync-project is unavailable beside ticket-autopilot: {scripts}"
        )
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(
        "_ticket_autopilot_llm_wiki_sync_project", module_path
    )
    if spec is None or spec.loader is None:
        raise TransitionError(f"cannot load llm-wiki sync-project: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.sync_project


def _record(
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    value: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = copy.deepcopy(dict(value))
    kernel.record_delivery_metadata(ticket_id, SYNC_STEP, normalized)
    store.save(kernel.ledger)
    return normalized


@contextmanager
def _source_checkout(repo: Path, head_sha: str) -> Iterator[Path]:
    temporary = Path(tempfile.mkdtemp(prefix="ticket-wiki-source-"))
    registered = False
    try:
        run_git(repo, "cat-file", "-e", f"{head_sha}^{{commit}}")
        run_git(repo, "worktree", "add", "--detach", str(temporary), head_sha)
        registered = True
        observed = run_git(temporary, "rev-parse", "HEAD")
        if observed != head_sha:
            raise GitError("wiki source checkout differs from integrated head")
        yield temporary
    finally:
        if registered:
            try:
                run_git(repo, "worktree", "remove", "--force", str(temporary))
            except GitError:
                pass
        shutil.rmtree(temporary, ignore_errors=True)


def _wiki_relative(repo: Path, wiki_identity: str) -> Path:
    untrusted = Path(wiki_identity).expanduser()
    if not untrusted.is_absolute():
        raise TransitionError("tracked wiki identity is not absolute")
    root = repo.resolve()
    try:
        relative = untrusted.relative_to(root)
    except ValueError as error:
        raise TransitionError(
            "tracked wiki candidate is outside the project repository"
        ) from error
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise TransitionError("tracked wiki identity contains a symbolic link")
    if untrusted.resolve() != root / relative:
        raise TransitionError("tracked wiki identity is not canonical")
    return relative if relative.parts else Path(".")


def _wiki_contract_digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value) + b"\n").hexdigest()


def _frozen_files(
    candidate_path: Path, result: Mapping[str, Any]
) -> dict[str, Path]:
    candidate_ref = result.get("candidate_ref")
    if not isinstance(candidate_ref, Mapping):
        raise TransitionError("tracked wiki result lacks a candidate reference")
    manifest = candidate_path / "manifest.json"
    if manifest.is_symlink() or not manifest.is_file():
        raise TransitionError("tracked wiki candidate manifest is missing or unsafe")
    try:
        manifest_document = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise TransitionError("tracked wiki candidate manifest is unreadable") from error
    if (
        not isinstance(manifest_document, dict)
        or set(manifest_document) != {"candidate_ref", "validation_receipt"}
        or manifest_document.get("candidate_ref") != result.get("candidate_ref")
        or manifest_document.get("validation_receipt")
        != result.get("validation_receipt")
    ):
        raise TransitionError("tracked wiki candidate manifest contradicts sync result")
    receipt = manifest_document["validation_receipt"]
    if not isinstance(receipt, dict) or receipt.get("sha256") != _wiki_contract_digest(
        {key: value for key, value in receipt.items() if key != "sha256"}
    ):
        raise TransitionError("tracked wiki validation receipt hash is invalid")
    files: dict[str, Path] = {}
    for path in sorted(candidate_path.rglob("*")):
        if path.is_dir() and not path.is_symlink():
            continue
        relative = path.relative_to(candidate_path).as_posix()
        if relative == "manifest.json":
            continue
        if (
            path.is_symlink()
            or not path.is_file()
            or not relative.startswith("wiki/")
            or path.suffix.lower() != ".md"
            or stat.S_IMODE(path.stat().st_mode) & 0o111
        ):
            raise TransitionError("tracked wiki candidate contains a non-regular path")
        try:
            path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError) as error:
            raise TransitionError("tracked wiki candidate is not UTF-8") from error
        files[relative] = path
    if not files:
        raise TransitionError("tracked wiki candidate corpus is empty")
    tree = _wiki_contract_digest(
        [
            {
                "path": relative,
                "kind": "file",
                "mode": stat.S_IMODE(path.stat().st_mode),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for relative, path in sorted(files.items())
        ]
    )
    if tree != candidate_ref.get("candidate_tree_sha256"):
        raise TransitionError("tracked wiki candidate tree hash is invalid")
    return files


def _repository_binding(repository: Path, *, label: str) -> RepositoryBinding:
    try:
        return RepositoryBinding.inspect(repository)
    except Exception as error:
        raise TransitionError(f"{label} repository identity is invalid: {error}") from error


def _target_repository(
    run_repo: Path,
    raw_project_root: str,
    *,
    provider_name: str,
) -> tuple[Path, RepositoryBinding, RepositoryBinding]:
    if not raw_project_root or raw_project_root != raw_project_root.strip():
        raise TransitionError("wiki delivery target project root is invalid")
    untrusted = Path(raw_project_root).expanduser()
    if not untrusted.is_absolute() or untrusted.is_symlink():
        raise TransitionError("wiki delivery target project root is unsafe")
    try:
        target = untrusted.resolve(strict=True)
    except OSError as error:
        raise TransitionError("wiki delivery target project root is missing") from error
    if target != untrusted:
        raise TransitionError("wiki delivery target must be a canonical Git worktree root")
    run_binding = _repository_binding(run_repo, label="run")
    target_binding = _repository_binding(target, label="wiki delivery target")
    if Path(target_binding.observed_repository_root) != target:
        raise TransitionError("wiki delivery target must be a Git worktree root")
    if (
        run_binding.provider != provider_name
        or target_binding.provider != provider_name
        or run_binding.normalized_remote != target_binding.normalized_remote
    ):
        raise TransitionError(
            "wiki delivery target has cross-repository identity"
        )
    return target, run_binding, target_binding


def _delivery_target(
    run_repo: Path,
    result: Mapping[str, Any],
    *,
    provider_name: str,
) -> tuple[Path, dict[str, Any]]:
    wiki_ref = result.get("wiki_sync_ref")
    if not isinstance(wiki_ref, Mapping):
        raise TransitionError("tracked wiki result lacks a WikiSyncRef")
    raw_project_root = wiki_ref.get("project_root")
    if not isinstance(raw_project_root, str):
        raise TransitionError("tracked wiki result lacks target project_root")
    target, run_binding, target_binding = _target_repository(
        run_repo, raw_project_root, provider_name=provider_name
    )
    wiki_identity = result.get("wiki_identity")
    candidate_ref = result.get("candidate_ref")
    candidate_path_raw = result.get("candidate_path")
    receipt = result.get("validation_receipt")
    if (
        not isinstance(wiki_identity, str)
        or not isinstance(candidate_ref, Mapping)
        or not isinstance(candidate_path_raw, str)
        or not isinstance(receipt, Mapping)
    ):
        raise TransitionError("tracked wiki result lacks delivery target identity")
    if wiki_ref.get("wiki_identity") != wiki_identity:
        raise TransitionError("tracked wiki result has contradictory logical wiki identity")
    wiki_relative = _wiki_relative(target, wiki_identity)
    if not wiki_relative.parts or wiki_relative == Path("."):
        raise TransitionError("tracked wiki identity cannot equal the project root")
    untrusted_candidate = Path(candidate_path_raw).expanduser()
    if not untrusted_candidate.is_absolute() or untrusted_candidate.is_symlink():
        raise TransitionError("tracked wiki candidate path is unsafe")
    try:
        candidate_path = untrusted_candidate.resolve(strict=True)
    except OSError as error:
        raise TransitionError("tracked wiki candidate path is missing") from error
    if candidate_path != untrusted_candidate:
        raise TransitionError("tracked wiki candidate path is not canonical")
    sync_digest = wiki_ref.get("digest")
    candidate_tree = candidate_ref.get("candidate_tree_sha256")
    if (
        not isinstance(sync_digest, str)
        or not _HEX_64.fullmatch(sync_digest)
        or not isinstance(candidate_tree, str)
        or not _HEX_64.fullmatch(candidate_tree)
        or candidate_ref.get("wiki_sync_ref") != sync_digest
        or candidate_ref.get("contract_version") != "wiki-sync-v1"
        or candidate_ref.get("profile") != "wiki-sync-v1"
        or wiki_ref.get("contract_version") != "wiki-sync-v1"
        or _wiki_contract_digest(
            {key: value for key, value in wiki_ref.items() if key != "digest"}
        )
        != sync_digest
    ):
        raise TransitionError("tracked wiki candidate target digest is invalid")
    candidate_store = Path(target_binding.git_common_dir) / "llm-wiki" / "candidates"
    expected_candidate_raw = candidate_store / sync_digest / candidate_tree
    for component in (
        candidate_store,
        candidate_store / sync_digest,
        expected_candidate_raw,
    ):
        if component.is_symlink():
            raise TransitionError("tracked wiki candidate store contains a symbolic link")
    expected_candidate = expected_candidate_raw.resolve()
    if candidate_path != expected_candidate:
        raise TransitionError(
            "tracked wiki candidate is outside the canonical target store"
        )
    _frozen_files(candidate_path, result)
    manifest = candidate_path / "manifest.json"
    validation_sha = receipt.get("sha256")
    if not isinstance(validation_sha, str) or not _HEX_64.fullmatch(validation_sha):
        raise TransitionError("tracked wiki validation receipt identity is invalid")
    unsigned = {
        "schema": 1,
        "contract_version": _TARGET_CONTRACT,
        "run_repository_root": run_binding.observed_repository_root,
        "project_root": str(target),
        "git_common_dir": target_binding.git_common_dir,
        "provider": target_binding.provider,
        "normalized_remote": target_binding.normalized_remote,
        "wiki_relative": wiki_relative.as_posix(),
        "wiki_sync_ref": sync_digest,
        "candidate_tree_sha256": candidate_tree,
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "validation_receipt_sha256": validation_sha,
    }
    return target, {**unsigned, "receipt_sha256": _digest(unsigned)}


def _bound_project_target(
    run_repo: Path,
    source: Path,
    *,
    provider_name: str,
) -> Path:
    configs = []
    candidates = [source]
    for path in sorted(source.iterdir()):
        if path.is_symlink():
            if (path / "llm-wiki-project.json").exists():
                raise TransitionError(
                    "exact source wiki project directory is a symbolic link"
                )
            continue
        if path.is_dir():
            candidates.append(path)
    for candidate in candidates:
        config = candidate / "llm-wiki-project.json"
        if config.is_symlink():
            raise TransitionError("exact source wiki binding is a symbolic link")
        if config.is_file():
            configs.append(config)
    if not configs:
        return repository_root(run_repo)
    if len(configs) != 1:
        raise TransitionError("exact source contains ambiguous wiki delivery targets")
    try:
        document = json.loads(configs[0].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise TransitionError("exact source wiki binding is unreadable") from error
    raw_project_root = document.get("project_root") if isinstance(document, dict) else None
    if not isinstance(raw_project_root, str):
        raise TransitionError("exact source wiki binding lacks project_root")
    target, _run_binding, _target_binding = _target_repository(
        run_repo, raw_project_root, provider_name=provider_name
    )
    return target


def _ensure_source_head(repo: Path, head_sha: str, base_branch: str) -> None:
    try:
        run_git(repo, "cat-file", "-e", f"{head_sha}^{{commit}}")
        return
    except GitError:
        run_git(repo, "fetch", "origin", base_branch)
    run_git(repo, "cat-file", "-e", f"{head_sha}^{{commit}}")


def _sync_from_canonical_target(
    run_repo: Path,
    head_sha: str,
    base_branch: str,
    operation: SyncOperation,
    *,
    origin_id: str,
    attempt: int,
    provider_name: str,
) -> dict[str, Any]:
    def invoke(target: Path, source: Path) -> dict[str, Any]:
        return dict(
            operation(
                target,
                (),
                origin_kind="integrated-ticket",
                origin_id=origin_id,
                triggers=("post-integration",),
                attempt=attempt,
                autopilot_root=Path(__file__).resolve().parents[2],
                source_root=source,
                expected_source_head=head_sha,
            )
        )

    with _source_checkout(run_repo, head_sha) as discovery_source:
        target = _bound_project_target(
            run_repo, discovery_source, provider_name=provider_name
        )
        if target == repository_root(run_repo):
            return invoke(target, discovery_source)
        _ensure_source_head(target, head_sha, base_branch)
        with _source_checkout(target, head_sha) as canonical_source:
            return invoke(target, canonical_source)


def _head_matches_frozen(
    repo: Path,
    head_sha: str,
    base_sha: str,
    wiki_relative: Path,
    frozen: Mapping[str, Path],
    changed_paths: Sequence[str],
) -> bool:
    lineage = run_git(repo, "rev-list", "--parents", "-n", "1", head_sha).split()
    if lineage != [head_sha, base_sha]:
        return False
    observed_changes = set(
        run_git(repo, "diff", "--name-only", base_sha, head_sha).splitlines()
    )
    expected_changes = {
        (wiki_relative / relative).as_posix() for relative in changed_paths
    }
    if observed_changes != expected_changes:
        return False
    prefix = (wiki_relative / "wiki").as_posix()
    tracked = {
        item
        for item in run_git(
            repo, "ls-tree", "-r", "--name-only", head_sha, "--", prefix
        ).splitlines()
        if item.endswith(".md")
    }
    expected = {(wiki_relative / relative).as_posix() for relative in frozen}
    if tracked != expected:
        return False
    for relative, source in frozen.items():
        try:
            observed_blob = run_git(
                repo,
                "rev-parse",
                f"{head_sha}:{(wiki_relative / relative).as_posix()}",
            )
            expected_blob = run_git(repo, "hash-object", str(source))
        except GitError:
            return False
        if observed_blob != expected_blob:
            return False
    return True


def _candidate_branch(wiki_sync_ref: str) -> str:
    return f"ticket-autopilot/wiki-sync-{wiki_sync_ref[:16]}"


def _render_body(result: Mapping[str, Any], head_sha: str) -> str:
    receipt = result.get("validation_receipt")
    receipt_hash = receipt.get("sha256") if isinstance(receipt, Mapping) else None
    changed = result.get("changed_paths") or []
    lines = [
        "## Wiki synchronization",
        "",
        "Docs-only projection generated by `wiki-sync-v1` after durable ticket integration.",
        "",
        f"- WikiSyncRef: `{result['wiki_sync_ref']['digest']}`",
        f"- Candidate tree: `{result['candidate_ref']['candidate_tree_sha256']}`",
        f"- Delivery head: `{head_sha}`",
        f"- Validation receipt: `{receipt_hash}`",
        "- Claim ceiling: `implementation-complete`",
        "",
        "### Changed generated paths",
        "",
        *[f"- `{path}`" for path in changed],
        "",
    ]
    return "\n".join(lines)


def _autonomous_reasons(
    observation: Mapping[str, Any],
    policies: Mapping[str, Any],
    approvals: Mapping[str, Any],
    *,
    provider: str,
    pr_id: str,
    head_sha: str,
) -> list[str]:
    reasons: list[str] = []
    if any(
        observation.get(key) != value
        for key, value in {
            "provider": provider,
            "operation": GET_PR_STATE,
            "evidence_class": "live",
            "observed": True,
            "pr_id": pr_id,
            "head_sha": head_sha,
            "state": "open",
        }.items()
    ):
        reasons.append("provider PR observation is incomplete or stale")
    if observation.get("mergeable") != "MERGEABLE":
        reasons.append("provider mergeability is not proven")
    if observation.get("merge_state_status") not in {"CLEAN", "HAS_HOOKS"}:
        reasons.append("provider merge state is not clean")
    if (
        policies.get("provider") != provider
        or policies.get("operation") != GET_CHECKS_AND_POLICIES
        or policies.get("evidence_class") != "live"
        or policies.get("observed") is not True
        or policies.get("pr_id") != pr_id
        or policies.get("head_sha") != head_sha
        or policies.get("base") != observation.get("base")
        or policies.get("merge_mode") not in {"direct", "queue"}
        or not isinstance(policies.get("active_rules"), list)
        or not isinstance(policies.get("checks_and_policies"), list)
    ):
        reasons.append("provider checks and policies receipt is incomplete")
    else:
        allowed = {
            "pass",
            "passed",
            "success",
            "successful",
            "skipping",
            "skipped",
        }
        for item in policies["checks_and_policies"]:
            if (
                not isinstance(item, Mapping)
                or set(item) != {"bucket", "name", "state", "workflow"}
                or not all(
                    isinstance(item.get(field), str) and item[field]
                    for field in ("bucket", "name", "state")
                )
                or not isinstance(item.get("workflow"), str)
                or str(item["bucket"]).casefold() not in allowed
            ):
                reasons.append("required checks are pending, failed, or malformed")
                break
    if (
        approvals.get("provider") != provider
        or approvals.get("operation") != GET_APPROVALS
        or approvals.get("evidence_class") != "live"
        or approvals.get("observed") is not True
        or approvals.get("pr_id") != pr_id
    ):
        reasons.append("provider approvals receipt is incomplete")
    elif approvals.get("review_decision") not in {None, "", "APPROVED"}:
        reasons.append(
            f"provider review decision is {approvals.get('review_decision')}"
        )
    return reasons


def deliver_tracked_candidate(
    repo: Path,
    result: Mapping[str, Any],
    *,
    base_branch: str,
    provider_name: str,
    provider_mode: str,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Materialize one frozen wiki candidate without touching the protected worktree."""

    candidate_path = Path(str(result.get("candidate_path", ""))).resolve()
    wiki_identity = result.get("wiki_identity")
    wiki_ref = result.get("wiki_sync_ref")
    changed_paths = result.get("changed_paths")
    if (
        not candidate_path.is_dir()
        or not isinstance(wiki_identity, str)
        or not isinstance(wiki_ref, Mapping)
        or not isinstance(wiki_ref.get("digest"), str)
        or not isinstance(changed_paths, list)
        or not changed_paths
        or not all(isinstance(item, str) and item for item in changed_paths)
    ):
        raise TransitionError("tracked wiki result lacks frozen candidate identity")
    frozen = _frozen_files(candidate_path, result)
    relative = _wiki_relative(repo, wiki_identity)
    branch = _candidate_branch(str(wiki_ref["digest"]))
    remote = run_git(
        repo, "ls-remote", "--heads", "origin", f"refs/heads/{base_branch}"
    )
    base_sha = remote.split()[0] if remote else None
    if not base_sha:
        raise GitError(f"remote base branch is missing: {base_branch}")
    try:
        run_git(repo, "cat-file", "-e", f"{base_sha}^{{commit}}")
    except GitError:
        run_git(repo, "fetch", "origin", base_branch)

    remote_candidate = run_git(
        repo, "ls-remote", "--heads", "origin", f"refs/heads/{branch}"
    )
    remote_head = remote_candidate.split()[0] if remote_candidate else None
    if remote_head:
        try:
            run_git(repo, "cat-file", "-e", f"{remote_head}^{{commit}}")
        except GitError:
            run_git(repo, "fetch", "origin", branch)
        if not _head_matches_frozen(
            repo,
            remote_head,
            base_sha,
            relative,
            frozen,
            changed_paths,
        ):
            raise GitError("remote wiki-sync branch diverged from its frozen candidate")
        head_sha = remote_head
    else:
        temporary = Path(tempfile.mkdtemp(prefix="ticket-wiki-delivery-"))
        registered = False
        try:
            run_git(repo, "worktree", "add", "--detach", str(temporary), base_sha)
            registered = True
            generated = temporary / relative / "wiki"
            if generated.exists():
                for path in sorted(generated.rglob("*.md"), reverse=True):
                    if path.is_symlink() or not path.is_file():
                        raise TransitionError(
                            "protected tracked wiki contains a non-regular generated path"
                        )
                    path.unlink()
            for relative_path, source in frozen.items():
                target = temporary / relative / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            run_git(temporary, "add", "-A", "--", (relative / "wiki").as_posix())
            if not run_git(temporary, "status", "--porcelain", "--", relative.as_posix()):
                raise TransitionError("tracked wiki candidate unexpectedly has no Git diff")
            run_git(
                temporary,
                "commit",
                "-m",
                f"docs: synchronize wiki {str(wiki_ref['digest'])[:12]}",
            )
            head_sha = run_git(temporary, "rev-parse", "HEAD")
            run_git(temporary, "branch", "-f", branch, head_sha)
            if not _head_matches_frozen(
                repo,
                head_sha,
                base_sha,
                relative,
                frozen,
                changed_paths,
            ):
                raise GitError(
                    "materialized wiki branch differs from the frozen docs-only candidate"
                )
            run_git(temporary, "push", "-u", "origin", f"{head_sha}:refs/heads/{branch}")
        finally:
            if registered:
                try:
                    run_git(repo, "worktree", "remove", "--force", str(temporary))
                except GitError:
                    pass
            shutil.rmtree(temporary, ignore_errors=True)

    provider = detect_provider("", override=provider_name)
    executor = ProviderExecutor(
        provider, cwd=repo, mode=provider_mode, runner=runner
    )
    body = _render_body(result, head_sha)
    receipt = executor.execute(
        CREATE_OR_UPDATE_PR,
        branch=branch,
        base=base_branch,
        head_sha=head_sha,
        title="Docs: synchronize project wiki",
        body_artifact=body,
    )
    if provider_mode != "live" or receipt.get("evidence_class") != "live":
        raise ProviderError("simulated provider evidence cannot deliver a wiki candidate")
    expected = {
        "provider": provider_name,
        "operation": CREATE_OR_UPDATE_PR,
        "branch": branch,
        "base": base_branch,
        "head_sha": head_sha,
        "body": body,
        "state": "open",
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise ProviderError("wiki PR readback contradicts the frozen delivery candidate")
    return {
        "schema": 1,
        "status": "pr-open",
        "branch": branch,
        "base": base_branch,
        "head_sha": head_sha,
        "pr_id": receipt["pr_id"],
        "url": receipt.get("url"),
        "provider_receipt": receipt,
    }


def _initial_record(kernel: Kernel, ticket_id: str, head_sha: str) -> dict[str, Any]:
    return {
        "schema": 1,
        "contract_version": CONTRACT_VERSION,
        "state": "running",
        "origin": {
            "kind": "integrated-ticket",
            "id": _origin_id(kernel, ticket_id, head_sha),
            "run_id": kernel.ledger["run_id"],
            "ticket_id": ticket_id,
            "integrated_head_sha": head_sha,
        },
        "attempt": 1,
        "result": None,
        "delivery": None,
        "authorization": None,
    }


def _retry_record(record: Mapping[str, Any]) -> dict[str, Any]:
    retried = copy.deepcopy(dict(record))
    retried["state"] = "running"
    retried["attempt"] = int(record.get("attempt", 0)) + 1
    return retried


def _delivery_failure(error: Exception) -> tuple[str, str, dict[str, Any]]:
    detail = str(error)
    terminal = isinstance(error, TransitionError) or any(
        marker in detail.casefold() for marker in _TERMINAL_DELIVERY_MARKERS
    )
    return (
        "terminal" if terminal else "retryable",
        "delivery-invalid" if terminal else "provider",
        {
            "disposition": "terminal" if terminal else "retryable",
            "max_attempts": 1 if terminal else 3,
        },
    )


def _should_retry(record: Mapping[str, Any]) -> bool:
    if record.get("state") == "running":
        return int(record.get("attempt", 0)) < 3
    result = record.get("result")
    return bool(
        record.get("state") == "retryable"
        and isinstance(result, Mapping)
        and result.get("retry", {}).get("disposition") == "retryable"
        and int(record.get("attempt", 0))
        < int(result.get("retry", {}).get("max_attempts", 1))
    )


def _retry_text(value: str, field: str) -> str:
    if not value or value != value.strip():
        raise TransitionError(f"wiki delivery retry {field} must be non-empty and trimmed")
    return value


def _retry_candidate_record(ticket: Mapping[str, Any]) -> Mapping[str, Any]:
    record = ticket.get("delivery", {}).get(SYNC_STEP)
    delivery = record.get("delivery") if isinstance(record, Mapping) else None
    result = record.get("result") if isinstance(record, Mapping) else None
    expected_failure = {
        "schema": 1,
        "status": "failed",
        "reason": "delivery-invalid",
        "detail": "tracked wiki candidate is outside the project repository",
        "retry": {"disposition": "terminal", "max_attempts": 1},
    }
    if (
        ticket.get("state") != "integrated"
        or not isinstance(record, Mapping)
        or record.get("state") != "terminal"
        or record.get("authorization") is not None
        or record.get("publication_authorization") is not None
        or record.get("delivery_target") is not None
        or record.get("delivery_retry") is not None
        or not isinstance(result, Mapping)
        or result.get("status") != "candidate-created"
        or not isinstance(delivery, Mapping)
        or delivery != expected_failure
    ):
        raise TransitionError(
            "wiki delivery retry requires one exact terminal pre-provider destination failure"
        )
    return record


def _retry_request(
    kernel: Kernel,
    ticket_id: str,
    expected_record_sha256: str,
    actor: str,
    evidence: str,
    target_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": 1,
        "contract_version": _RETRY_CONTRACT,
        "run_id": kernel.ledger["run_id"],
        "ticket_id": ticket_id,
        "expected_record_sha256": expected_record_sha256,
        "actor": actor,
        "evidence": evidence,
        "target_receipt_sha256": target_receipt["receipt_sha256"],
    }


def _validated_target_receipt(value: Any) -> dict[str, Any]:
    if (
        not isinstance(value, Mapping)
        or set(value) != _TARGET_RECEIPT_FIELDS
        or value.get("schema") != 1
        or value.get("contract_version") != _TARGET_CONTRACT
        or not isinstance(value.get("receipt_sha256"), str)
        or not _HEX_64.fullmatch(value["receipt_sha256"])
    ):
        raise TransitionError("wiki delivery retry target receipt is invalid")
    document = dict(value)
    observed = document.pop("receipt_sha256")
    if _digest(document) != observed:
        raise TransitionError("wiki delivery retry target receipt digest is invalid")
    return dict(value)


def _validated_retry_request(
    value: Any, kernel: Kernel, ticket_id: str
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _RETRY_REQUEST_FIELDS:
        raise TransitionError("wiki delivery retry request shape is invalid")
    expected = value.get("expected_record_sha256")
    target = value.get("target_receipt_sha256")
    actor = value.get("actor")
    evidence = value.get("evidence")
    if (
        value.get("schema") != 1
        or value.get("contract_version") != _RETRY_CONTRACT
        or value.get("run_id") != kernel.ledger["run_id"]
        or value.get("ticket_id") != ticket_id
        or not isinstance(expected, str)
        or not _HEX_64.fullmatch(expected)
        or not isinstance(target, str)
        or not _HEX_64.fullmatch(target)
        or not isinstance(actor, str)
        or not isinstance(evidence, str)
    ):
        raise TransitionError("wiki delivery retry request identity is invalid")
    _retry_text(actor, "actor")
    _retry_text(evidence, "evidence")
    return dict(value)


def _validated_retry_marker(
    record: Mapping[str, Any],
    state: str,
    kernel: Kernel,
    ticket_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Mapping[str, Any]]:
    marker = record.get("delivery_retry")
    fields = {
        "schema",
        "contract_version",
        "state",
        "request",
        "target_receipt",
        "previous_record",
    }
    if state == "applied":
        fields.add("receipt")
    if (
        not isinstance(marker, Mapping)
        or set(marker) != fields
        or marker.get("schema") != 1
        or marker.get("contract_version") != _RETRY_CONTRACT
        or marker.get("state") != state
    ):
        raise TransitionError(f"wiki delivery retry {state} marker is invalid")
    request = _validated_retry_request(marker.get("request"), kernel, ticket_id)
    target = _validated_target_receipt(marker.get("target_receipt"))
    previous = marker.get("previous_record")
    if (
        not isinstance(previous, Mapping)
        or _digest(previous) != request["expected_record_sha256"]
        or target["receipt_sha256"] != request["target_receipt_sha256"]
    ):
        raise TransitionError(f"wiki delivery retry {state} provenance is contradictory")
    if state == "intent-persisted":
        expected_record = copy.deepcopy(dict(previous))
        expected_record["delivery_retry"] = dict(marker)
        if dict(record) != expected_record:
            raise TransitionError("wiki delivery retry intent record is contradictory")
    if state == "applied":
        receipt = marker.get("receipt")
        receipt_fields = {
            "schema",
            "contract_version",
            "result",
            "request",
            "predecessor_record_sha256",
            "target_receipt_sha256",
            "authority_exclusions",
            "receipt_sha256",
        }
        if not isinstance(receipt, Mapping) or set(receipt) != receipt_fields:
            raise TransitionError("wiki delivery retry applied receipt shape is invalid")
        unsigned = dict(receipt)
        receipt_sha = unsigned.pop("receipt_sha256")
        if (
            receipt.get("schema") != 1
            or receipt.get("contract_version") != _RETRY_CONTRACT
            or receipt.get("result") != "prepared"
            or receipt.get("request") != request
            or receipt.get("predecessor_record_sha256")
            != request["expected_record_sha256"]
            or receipt.get("target_receipt_sha256")
            != target["receipt_sha256"]
            or receipt.get("authority_exclusions") != _RETRY_AUTHORITY_EXCLUSIONS
            or not isinstance(receipt_sha, str)
            or not _HEX_64.fullmatch(receipt_sha)
            or _digest(unsigned) != receipt_sha
        ):
            raise TransitionError("wiki delivery retry applied receipt is contradictory")
    return dict(marker), request, target, previous


def _validated_retry_predecessor(
    ticket: Mapping[str, Any], previous: Mapping[str, Any]
) -> Mapping[str, Any]:
    predecessor_ticket = copy.deepcopy(dict(ticket))
    predecessor_ticket.setdefault("delivery", {})[SYNC_STEP] = previous
    return _retry_candidate_record(predecessor_ticket)


def wiki_delivery_retry_status(
    repo: Path, kernel: Kernel, ticket_id: str
) -> dict[str, Any]:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if not isinstance(ticket, Mapping):
        raise TransitionError(f"unknown ticket: {ticket_id}")
    record = ticket.get("delivery", {}).get(SYNC_STEP)
    if not isinstance(record, Mapping):
        return {
            "schema": 1,
            "contract_version": _RETRY_CONTRACT,
            "ticket_id": ticket_id,
            "status": "absent",
            "eligible": False,
            "record_sha256": None,
            "reason": "wiki-sync record is absent",
        }
    marker = record.get("delivery_retry")
    record_sha256 = _digest(record)
    if isinstance(marker, Mapping) and marker.get("state") == "applied":
        try:
            validated, _request, _target, previous = _validated_retry_marker(
                record, "applied", kernel, ticket_id
            )
            _validated_retry_predecessor(ticket, previous)
        except TransitionError as error:
            return {
                "schema": 1,
                "contract_version": _RETRY_CONTRACT,
                "ticket_id": ticket_id,
                "status": "ineligible",
                "eligible": False,
                "record_sha256": record_sha256,
                "reason": str(error),
            }
        return {
            "schema": 1,
            "contract_version": _RETRY_CONTRACT,
            "ticket_id": ticket_id,
            "status": "applied",
            "eligible": False,
            "record_sha256": record_sha256,
            "reason": None,
            "receipt": copy.deepcopy(validated["receipt"]),
        }
    try:
        status = "eligible"
        retry_request = None
        candidate_record = record
        persisted_target = None
        if isinstance(marker, Mapping) and marker.get("state") == "intent-persisted":
            status = "intent-persisted"
            _validated, retry_request, persisted_target, candidate_record = (
                _validated_retry_marker(record, status, kernel, ticket_id)
            )
            record_sha256 = retry_request["expected_record_sha256"]
            _validated_retry_predecessor(ticket, candidate_record)
        else:
            _retry_candidate_record(ticket)
        _target, target_receipt = _delivery_target(
            repo,
            candidate_record["result"],
            provider_name=str(kernel.ledger["provider"]),
        )
        if persisted_target is not None and persisted_target != target_receipt:
            raise TransitionError("wiki delivery retry intent target is contradictory")
    except TransitionError as error:
        return {
            "schema": 1,
            "contract_version": _RETRY_CONTRACT,
            "ticket_id": ticket_id,
            "status": "ineligible",
            "eligible": False,
            "record_sha256": record_sha256,
            "reason": str(error),
        }
    return {
        "schema": 1,
        "contract_version": _RETRY_CONTRACT,
        "ticket_id": ticket_id,
        "status": status,
        "eligible": True,
        "record_sha256": record_sha256,
        "reason": None,
        "delivery_target": target_receipt,
        "retry_request": copy.deepcopy(retry_request),
    }


def retry_wiki_delivery(
    repo: Path,
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    *,
    expected_record_sha256: str,
    actor: str,
    evidence: str,
) -> dict[str, Any]:
    if not _HEX_64.fullmatch(expected_record_sha256):
        raise TransitionError(
            "wiki delivery retry expected record SHA-256 must be lowercase hexadecimal"
        )
    actor = _retry_text(actor, "actor")
    evidence = _retry_text(evidence, "evidence")
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if not isinstance(ticket, Mapping):
        raise TransitionError(f"unknown ticket: {ticket_id}")
    current = ticket.get("delivery", {}).get(SYNC_STEP)
    if not isinstance(current, Mapping):
        raise TransitionError("wiki delivery retry requires a wiki-sync record")

    marker = current.get("delivery_retry")
    if isinstance(marker, Mapping) and marker.get("state") == "applied":
        validated, request, target_receipt, previous = _validated_retry_marker(
            current, "applied", kernel, ticket_id
        )
        _validated_retry_predecessor(ticket, previous)
        if any(
            request[field] != value
            for field, value in {
                "expected_record_sha256": expected_record_sha256,
                "actor": actor,
                "evidence": evidence,
            }.items()
        ):
            raise TransitionError("wiki delivery retry replay authority is contradictory")
        return {
            "schema": 1,
            "contract_version": _RETRY_CONTRACT,
            "ticket_id": ticket_id,
            "result": "prepared",
            "replayed": True,
            "record_sha256_before": expected_record_sha256,
            "record_sha256_after": _digest(current),
            "delivery_target": target_receipt,
            "receipt": copy.deepcopy(validated["receipt"]),
        }

    previous: Mapping[str, Any]
    persisted_request = None
    persisted_target = None
    if isinstance(marker, Mapping) and marker.get("state") == "intent-persisted":
        _validated, persisted_request, persisted_target, previous = (
            _validated_retry_marker(current, "intent-persisted", kernel, ticket_id)
        )
        _validated_retry_predecessor(ticket, previous)
        if persisted_request["expected_record_sha256"] != expected_record_sha256:
            raise TransitionError("wiki delivery retry intent has stale predecessor bytes")
    else:
        previous = _retry_candidate_record(ticket)
        if _digest(previous) != expected_record_sha256:
            raise TransitionError("wiki delivery retry record SHA-256 changed")

    _target, target_receipt = _delivery_target(
        repo,
        previous["result"],
        provider_name=str(kernel.ledger["provider"]),
    )
    request = _retry_request(
        kernel,
        ticket_id,
        expected_record_sha256,
        actor,
        evidence,
        target_receipt,
    )

    if isinstance(marker, Mapping) and marker.get("state") == "intent-persisted":
        if persisted_request != request or persisted_target != target_receipt:
            raise TransitionError("wiki delivery retry intent is contradictory")
    else:
        intent_record = copy.deepcopy(dict(previous))
        intent_record["delivery_retry"] = {
            "schema": 1,
            "contract_version": _RETRY_CONTRACT,
            "state": "intent-persisted",
            "request": request,
            "target_receipt": target_receipt,
            "previous_record": copy.deepcopy(dict(previous)),
        }
        _record(store, kernel, ticket_id, intent_record)

    receipt_unsigned = {
        "schema": 1,
        "contract_version": _RETRY_CONTRACT,
        "result": "prepared",
        "request": request,
        "predecessor_record_sha256": expected_record_sha256,
        "target_receipt_sha256": target_receipt["receipt_sha256"],
        "authority_exclusions": _RETRY_AUTHORITY_EXCLUSIONS,
    }
    receipt = {**receipt_unsigned, "receipt_sha256": _digest(receipt_unsigned)}
    recovered = copy.deepcopy(dict(previous))
    recovered["state"] = "delivery-pending"
    recovered["delivery"] = None
    recovered["authorization"] = None
    recovered["delivery_target"] = target_receipt
    recovered["delivery_retry"] = {
        "schema": 1,
        "contract_version": _RETRY_CONTRACT,
        "state": "applied",
        "request": request,
        "target_receipt": target_receipt,
        "previous_record": copy.deepcopy(dict(previous)),
        "receipt": receipt,
    }
    _record(store, kernel, ticket_id, recovered)
    readback = store.load()["tickets"][ticket_id]["delivery"][SYNC_STEP]
    if readback != recovered:
        raise TransitionError("wiki delivery retry readback is contradictory")
    return {
        "schema": 1,
        "contract_version": _RETRY_CONTRACT,
        "ticket_id": ticket_id,
        "result": "prepared",
        "replayed": False,
        "record_sha256_before": expected_record_sha256,
        "record_sha256_after": _digest(recovered),
        "delivery_target": target_receipt,
        "receipt": receipt,
    }


def drive_post_integration_sync(
    repo: Path,
    store: AtomicLedger,
    kernel: Kernel,
    *,
    runner: CommandRunner | None = None,
    sync_operation: SyncOperation | None = None,
    delivery_operation: DeliveryOperation = deliver_tracked_candidate,
    boundary_guard: Callable[[str, str], None] | None = None,
) -> list[dict[str, Any]]:
    """Drive durable post-integration effects; origin ticket state is never changed."""

    sync = sync_operation
    processed: list[dict[str, Any]] = []
    policy = kernel.ledger.get("wiki_sync_policy") or {
        "schema": 1,
        "merge_policy": "manual",
        "autonomous_grant": None,
    }
    autonomous = policy.get("merge_policy") == "autonomous"
    for ticket_id in kernel.ledger["ticket_order"]:
        ticket = kernel.ledger["tickets"][ticket_id]
        if ticket["state"] != "integrated" or ticket.get("preexisting_integrated"):
            continue
        head_sha = ticket.get("pr", {}).get("head_sha")
        if not isinstance(head_sha, str) or not head_sha:
            continue
        existing = ticket.get("delivery", {}).get(SYNC_STEP)
        if isinstance(existing, Mapping):
            result = existing.get("result")
            if (
                isinstance(result, Mapping)
                and result.get("status") in TERMINAL_SYNC_STATUSES
            ) or existing.get("state") == "merged" or (
                existing.get("state") == "awaiting-authorization"
                and not autonomous
                and existing.get("authorization") is None
            ) or existing.get("state") == "terminal":
                continue
        if boundary_guard is not None:
            boundary_guard(ticket_id, "wiki:post-integration-sync")
        if isinstance(existing, Mapping):
            result = existing.get("result")
            if isinstance(result, Mapping) and result.get("status") == "candidate-created":
                record = copy.deepcopy(dict(existing))
                delivery = record.get("delivery")
                if (
                    isinstance(delivery, Mapping)
                    and delivery.get("status") == "failed"
                    and int(record.get("attempt", 0)) < int(
                        delivery.get("retry", {}).get("max_attempts", 1)
                    )
                ):
                    record["attempt"] = int(record.get("attempt", 0)) + 1
                    record["delivery"] = None
                    record["state"] = "delivery-pending"
                    _record(store, kernel, ticket_id, record)
                elif (
                    isinstance(delivery, Mapping)
                    and (
                        delivery.get("status") == "failed"
                        or record.get("state") in {"retryable", "awaiting-provider"}
                    )
                    and int(record.get("attempt", 0))
                    >= int(delivery.get("retry", {}).get("max_attempts", 3))
                ):
                    record["state"] = "terminal"
                    record["delivery"] = {
                        **dict(delivery),
                        "status": "failed",
                        "reason": "transient-exhausted",
                        "retry": {"disposition": "terminal", "max_attempts": 3},
                    }
                    _record(store, kernel, ticket_id, record)
            elif not _should_retry(existing):
                if existing.get("state") in {"running", "retryable"}:
                    exhausted = copy.deepcopy(dict(existing))
                    previous_result = exhausted.get("result")
                    exhausted["state"] = "terminal"
                    exhausted["result"] = {
                        **(
                            dict(previous_result)
                            if isinstance(previous_result, Mapping)
                            else {
                                "contract_version": "wiki-sync-v1",
                                "status": "failed",
                                "origin": exhausted.get("origin"),
                                "attempt": exhausted.get("attempt"),
                            }
                        ),
                        "status": "failed",
                        "reason": "transient-exhausted",
                        "retry": {"disposition": "terminal", "max_attempts": 3},
                    }
                    _record(store, kernel, ticket_id, exhausted)
                continue
            else:
                record = _retry_record(existing)
                _record(store, kernel, ticket_id, record)
        else:
            record = _initial_record(kernel, ticket_id, head_sha)
            _record(store, kernel, ticket_id, record)

        result = record.get("result")
        if not isinstance(result, Mapping) or result.get("status") != "candidate-created":
            try:
                operation = sync or _load_sync_operation()
                result = _sync_from_canonical_target(
                    repo,
                    head_sha,
                    str(ticket.get("pr", {}).get("base") or "main"),
                    operation,
                    origin_id=record["origin"]["id"],
                    attempt=record["attempt"],
                    provider_name=str(kernel.ledger["provider"]),
                )
            except (GitError, TransitionError) as error:
                terminal = isinstance(error, TransitionError)
                result = {
                    "contract_version": "wiki-sync-v1",
                    "status": "failed",
                    "reason": "broken-binding" if terminal else "stale-tree",
                    "origin": {
                        "kind": "integrated-ticket",
                        "id": record["origin"]["id"],
                    },
                    "attempt": record["attempt"],
                    "retry": {
                        "disposition": "terminal" if terminal else "retryable",
                        "max_attempts": 1 if terminal else 3,
                    },
                    "detail": str(error),
                }
            record["result"] = result
            record["state"] = (
                "retryable"
                if result.get("status") == "failed"
                and result.get("retry", {}).get("disposition") == "retryable"
                else "terminal"
                if result.get("status") == "failed"
                else "delivery-pending"
                if result.get("status") == "candidate-created"
                else "complete"
            )
            _record(store, kernel, ticket_id, record)

        if result.get("status") == "candidate-created" and not record.get("delivery"):
            try:
                delivery_repo, target_receipt = _delivery_target(
                    repo,
                    result,
                    provider_name=str(kernel.ledger["provider"]),
                )
                existing_target = record.get("delivery_target")
                if existing_target is not None and existing_target != target_receipt:
                    raise TransitionError(
                        "persisted wiki delivery target is contradictory"
                    )
                if existing_target is None:
                    record["delivery_target"] = target_receipt
                    _record(store, kernel, ticket_id, record)
                delivery = dict(
                    delivery_operation(
                        delivery_repo,
                        result,
                        base_branch=str(ticket.get("pr", {}).get("base") or "main"),
                        provider_name=str(kernel.ledger["provider"]),
                        provider_mode=str(
                            kernel.ledger.get("provider_mode", "live")
                        ),
                        runner=runner,
                    )
                )
            except (GitError, ProviderError, TransitionError, OSError) as error:
                state, reason, retry = _delivery_failure(error)
                record["delivery"] = {
                    "schema": 1,
                    "status": "failed",
                    "reason": reason,
                    "detail": str(error),
                    "retry": retry,
                }
                record["state"] = state
            else:
                record["delivery"] = delivery
                record["state"] = "awaiting-authorization"
            _record(store, kernel, ticket_id, record)

        delivery = record.get("delivery")
        if (
            autonomous
            and isinstance(delivery, Mapping)
            and delivery.get("status")
            in {"pr-open", "queued", "waiting-provider"}
            and record.get("state") != "merged"
            and int(record.get("attempt", 0)) < 3
        ):
            grant = policy.get("autonomous_grant")
            if not isinstance(grant, Mapping):
                raise TransitionError("autonomous wiki-sync grant is missing")
            if record.get("state") in {"retryable", "awaiting-provider"}:
                record["attempt"] = int(record.get("attempt", 0)) + 1
                _record(store, kernel, ticket_id, record)
            try:
                record = approve_wiki_sync(
                    repo,
                    store,
                    kernel,
                    ticket_id,
                    actor=str(grant["actor"]),
                    evidence=str(grant["evidence"]),
                    head_sha=str(delivery["head_sha"]),
                    runner=runner,
                    mode="autonomous",
                )
            except (ProviderError, TransitionError) as error:
                current = kernel.ledger["tickets"][ticket_id]["delivery"][SYNC_STEP]
                record = copy.deepcopy(current)
                state, reason, retry = _delivery_failure(error)
                record["state"] = state
                failed_delivery = {
                    **dict(record["delivery"]),
                    "merge_error": str(error),
                    "retry": retry,
                }
                if state == "terminal":
                    failed_delivery.update(status="failed", reason=reason)
                record["delivery"] = failed_delivery
                _record(store, kernel, ticket_id, record)

        delivery = record.get("delivery")
        authorization = record.get("authorization")
        if (
            not autonomous
            and isinstance(authorization, Mapping)
            and isinstance(delivery, Mapping)
            and delivery.get("status") in {"pr-open", "queued", "waiting-provider"}
            and record.get("state") != "merged"
            and int(record.get("attempt", 0)) < 3
        ):
            record["attempt"] = int(record.get("attempt", 0)) + 1
            _record(store, kernel, ticket_id, record)
            try:
                record = approve_wiki_sync(
                    repo,
                    store,
                    kernel,
                    ticket_id,
                    actor=str(authorization["actor"]),
                    evidence=str(authorization["evidence"]),
                    head_sha=str(delivery["head_sha"]),
                    runner=runner,
                    mode=str(authorization["mode"]),
                )
            except (ProviderError, TransitionError) as error:
                current = kernel.ledger["tickets"][ticket_id]["delivery"][SYNC_STEP]
                record = copy.deepcopy(current)
                state, reason, retry = _delivery_failure(error)
                record["state"] = state
                failed_delivery = {
                    **dict(record["delivery"]),
                    "merge_error": str(error),
                    "retry": retry,
                }
                if state == "terminal":
                    failed_delivery.update(status="failed", reason=reason)
                record["delivery"] = failed_delivery
                _record(store, kernel, ticket_id, record)

        processed.append(
            {
                "operation": "post-integration-wiki-sync",
                "ticket_id": ticket_id,
                "result": record.get("state"),
                "wiki_sync": copy.deepcopy(record.get("result")),
                "delivery": copy.deepcopy(record.get("delivery")),
            }
        )
    return processed


def approve_wiki_sync(
    repo: Path,
    store: AtomicLedger,
    kernel: Kernel,
    ticket_id: str,
    *,
    actor: str,
    evidence: str,
    head_sha: str,
    runner: CommandRunner | None = None,
    mode: str = "runner",
) -> dict[str, Any]:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    record = ticket.get("delivery", {}).get(SYNC_STEP) if ticket else None
    delivery = record.get("delivery") if isinstance(record, Mapping) else None
    if (
        not isinstance(record, Mapping)
        or not isinstance(delivery, Mapping)
        or delivery.get("status") not in {"pr-open", "queued", "waiting-provider"}
    ):
        raise TransitionError("wiki-sync approval requires its separate open PR")
    if delivery.get("head_sha") != head_sha:
        raise TransitionError("wiki-sync authorization is stale for the current PR head")
    if not actor or not evidence:
        raise TransitionError("wiki-sync authorization requires actor and evidence")
    if mode not in {"runner", "autonomous"}:
        raise TransitionError("wiki-sync authorization mode is invalid")
    provider = detect_provider("", override=kernel.ledger["provider"])
    delivery_repo, target_receipt = _delivery_target(
        repo, record.get("result", {}), provider_name=provider.name
    )
    persisted_target = record.get("delivery_target")
    if persisted_target != target_receipt:
        raise TransitionError("wiki-sync approval has no matching delivery target receipt")
    executor = ProviderExecutor(
        provider,
        cwd=delivery_repo,
        mode=str(kernel.ledger.get("provider_mode", "live")),
        runner=runner,
    )
    pr_id = str(delivery["pr_id"])
    observation = executor.execute(GET_PR_STATE, pr_id=pr_id)
    if observation.get("head_sha") != head_sha:
        raise ProviderError("provider wiki PR head changed before authorization")
    authorization = {
        "schema": 1,
        "scope": "wiki-sync-v1",
        "actor": actor,
        "evidence": evidence,
        "head_sha": head_sha,
        "mode": mode,
    }
    updated = copy.deepcopy(dict(record))
    existing = updated.get("authorization")
    if existing is not None and existing != authorization:
        raise TransitionError("persisted wiki-sync authorization is contradictory")
    if observation.get("state") == "merged" and mode == "autonomous":
        previous_attempt = delivery.get("merge_attempt")
        if (
            existing is None
            or not isinstance(previous_attempt, Mapping)
            or previous_attempt.get("head_sha") != head_sha
        ):
            raise ProviderError(
                "wiki PR is already merged without a replay-safe autonomous attempt"
            )
    updated["authorization"] = authorization
    _record(store, kernel, ticket_id, updated)
    if observation.get("state") == "merged":
        updated["state"] = "merged"
        updated["result"] = {
            **dict(updated["result"]),
            "status": (
                "merged-automatically"
                if mode == "autonomous"
                else "candidate-created"
            ),
            "reason": (
                "autonomous-grant"
                if mode == "autonomous"
                else "manual-authorization"
            ),
        }
        updated["delivery"] = {
            **dict(updated["delivery"]),
            "status": "merged",
            "readback": observation,
        }
        _record(store, kernel, ticket_id, updated)
        return copy.deepcopy(updated)
    if observation.get("state") != "open":
        raise ProviderError("wiki PR is neither open nor merged")

    policies = executor.execute(
        GET_CHECKS_AND_POLICIES, pr_id=pr_id, expected_head=head_sha
    )
    if policies.get("head_sha") != head_sha:
        raise ProviderError("wiki merge policy belongs to another head")
    if mode == "autonomous":
        approvals = executor.execute(GET_APPROVALS, pr_id=pr_id)
        reasons = _autonomous_reasons(
            observation,
            policies,
            approvals,
            provider=provider.name,
            pr_id=pr_id,
            head_sha=head_sha,
        )
        if reasons:
            updated["state"] = "awaiting-provider"
            updated["delivery"] = {
                **dict(delivery),
                "status": "waiting-provider",
                "policies": policies,
                "approvals": approvals,
                "reasons": reasons,
            }
            _record(store, kernel, ticket_id, updated)
            return copy.deepcopy(updated)

    intent_key = _digest(
        {
            "provider": provider.name,
            "pr_id": pr_id,
            "head_sha": head_sha,
            "actor": actor,
            "evidence": evidence,
            "scope": "wiki-sync-v1",
        }
    )
    merge_attempt = {
        "schema": 1,
        "intent_key": intent_key,
        "provider": provider.name,
        "pr_id": pr_id,
        "head_sha": head_sha,
        "merge_mode": policies.get("merge_mode"),
    }
    existing_attempt = delivery.get("merge_attempt")
    if existing_attempt is not None and existing_attempt != merge_attempt:
        raise TransitionError("persisted wiki merge attempt is contradictory")
    updated["delivery"] = {
        **dict(delivery),
        "policies": policies,
        "merge_attempt": merge_attempt,
    }
    _record(store, kernel, ticket_id, updated)
    mutation = executor.execute(
        MERGE_EXPECTED_HEAD,
        pr_id=pr_id,
        expected_head=head_sha,
        intent_key=intent_key,
        previous_attempt_mode=policies.get("merge_mode"),
        mutation_previously_applied=False,
        queue_dispatch_ambiguous=False,
        authorization=MergeAuthorization(
            provider=provider.name,
            pr_id=pr_id,
            head_sha=head_sha,
            actor=actor,
            evidence=evidence,
        ),
    )
    readback = executor.execute(GET_PR_STATE, pr_id=pr_id)
    if readback.get("head_sha") != head_sha:
        raise ProviderError("wiki merge readback belongs to another head")
    if readback.get("state") == "merged":
        updated["state"] = "merged"
        updated["result"] = {
            **dict(updated["result"]),
            "status": (
                "merged-automatically"
                if mode == "autonomous"
                else "candidate-created"
            ),
            "reason": (
                "autonomous-grant"
                if mode == "autonomous"
                else "manual-authorization"
            ),
        }
        updated["delivery"] = {
            **dict(updated["delivery"]),
            "status": "merged",
            "policies": policies,
            "mutation": mutation,
            "readback": readback,
        }
    elif mutation.get("merge_mode") == "queue" and readback.get("state") == "open":
        updated["state"] = "awaiting-authorization"
        updated["delivery"] = {
            **dict(updated["delivery"]),
            "status": "queued",
            "policies": policies,
            "mutation": mutation,
            "readback": readback,
        }
    else:
        raise ProviderError("wiki merge readback did not confirm merged or queued state")
    _record(store, kernel, ticket_id, updated)
    return copy.deepcopy(updated)
