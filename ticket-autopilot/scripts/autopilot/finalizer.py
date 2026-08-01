from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .git_ops import (
    CommandRunner,
    GitError,
    SubprocessCommandRunner,
    candidate_ref,
    repository_root,
    run_git,
)
from .kernel import Kernel, TransitionError
from .ledger import AtomicLedger
from .providers import (
    CREATE_OR_UPDATE_PR,
    ProviderExecutor,
    build_delivery_plan,
)
from .verification_checkpoint import (
    VerificationCheckpointError,
    load_pr_body_validator,
)


class DeliveryBodyError(RuntimeError):
    """A rendered or observed PR body cannot support delivery progress."""

    def __init__(self, phase: str, detail: str):
        self.phase = phase
        super().__init__(detail)


def _ticket_paths(kernel: Kernel, ticket_id: str, worktree: Path) -> tuple[Path, Path]:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if ticket is None:
        raise TransitionError(f"unknown ticket {ticket_id!r}")
    repo_value = kernel.ledger.get("repo")
    if not repo_value:
        raise TransitionError("ledger has no repository binding")
    original_repo = Path(repo_value).resolve()
    original_ticket = Path(ticket["path"]).resolve()
    try:
        relative = original_ticket.relative_to(original_repo)
    except ValueError as error:
        raise TransitionError("ticket path is outside the bound repository") from error
    source = worktree.resolve() / relative
    destination = source.parent / "done" / source.name
    return source, destination


def finalize_done(
    store: AtomicLedger, kernel: Kernel, ticket_id: str
) -> bool:
    ticket = kernel.ledger["tickets"].get(ticket_id)
    if ticket is None or ticket["state"] not in {"verified", "pr-open", "integrated"}:
        raise TransitionError("done/ finalization requires a validated terminal result")
    worktree = Path(kernel.ledger["worktree"]).resolve()
    if repository_root(worktree) != worktree:
        raise GitError("ledger worktree is not an isolated Git root")
    source, destination = _ticket_paths(kernel, ticket_id, worktree)
    effect = "move-done-and-stage"

    already_recorded = any(
        item["ticket_id"] == ticket_id and item["effect"] == effect
        for item in kernel.ledger["effects"].values()
    )
    if already_recorded:
        if source.exists() or not destination.exists():
            raise TransitionError("finalization ledger and worktree disagree")
        return False

    if source.exists() and destination.exists():
        raise TransitionError("both pending and done ticket paths exist")
    if not source.exists() and not destination.exists():
        raise TransitionError("ticket is absent from pending and done paths")
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, destination)

    relative_source = source.relative_to(worktree)
    relative_destination = destination.relative_to(worktree)
    run_git(
        worktree,
        "add",
        "-A",
        "--",
        str(relative_source),
        str(relative_destination),
    )
    changed = kernel.record_finalization_effect(ticket_id, effect)
    store.save(kernel.ledger)
    return changed


class DeliveryFinalizer:
    def __init__(
        self,
        store: AtomicLedger,
        kernel: Kernel,
        executor: ProviderExecutor,
        runner: CommandRunner | None = None,
    ):
        self.store = store
        self.kernel = kernel
        self.executor = executor
        self.provider = executor.provider
        self.runner = runner or SubprocessCommandRunner()
        self.worktree = Path(kernel.ledger["worktree"]).resolve()

    def _run(self, *command: str, allow_failure: bool = False) -> str:
        result = self.runner.run(list(command), cwd=self.worktree)
        if result.returncode and not allow_failure:
            raise GitError(
                f"{' '.join(command)} failed: {result.stderr or result.stdout}"
            )
        return result.stdout

    def _effect_applied(self, ticket_id: str, effect: str) -> bool:
        return any(
            item["ticket_id"] == ticket_id and item["effect"] == effect
            for item in self.kernel.ledger["effects"].values()
        )

    def _record_effect(self, ticket_id: str, effect: str) -> None:
        self.kernel.record_finalization_effect(ticket_id, effect)
        self.store.save(self.kernel.ledger)

    @staticmethod
    def _atomic_summary(path: Path, document: dict[str, Any]) -> None:
        content = (
            json.dumps(
                document,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
        )
        if path.exists():
            if path.read_text(encoding="utf-8") != content:
                raise TransitionError("completion summary content is contradictory")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, raw_tmp = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(raw_tmp)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _atomic_text(path: Path, content: str) -> None:
        if path.exists():
            if path.read_text(encoding="utf-8") != content:
                raise DeliveryBodyError(
                    "render-persistence",
                    "content-addressed PR-body artifact is contradictory",
                )
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, raw_tmp = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(raw_tmp)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _canonical_digest(value: Any) -> str:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _render_request(
        self,
        ticket_id: str,
        *,
        branch: str,
        base_branch: str,
        head: str,
    ) -> dict[str, Any]:
        ticket = self.kernel.ledger["tickets"][ticket_id]
        _bundle, bundle_ref = self._verification_bundle_from_handoff(
            ticket_id, phase="render-request"
        )
        changed_paths = [
            item
            for item in self._run(
                "git",
                "diff",
                "--name-only",
                f"{ticket['candidate_ref']['base_sha']}..{head}",
            ).splitlines()
            if item
        ]
        payload = {
            "schema": 1,
            "ticket_id": ticket_id,
            "ticket": {
                "ticket_id": ticket_id,
                "ticket_digest": ticket["ticket_digest"],
                "execution_mode": ticket["execution_mode"],
                "blocked_by": list(ticket["blocked_by"]),
            },
            "candidate_ref": ticket["candidate_ref"],
            "artifact_generation": ticket["artifact_generation"],
            "expected_head_sha": head,
            "branch": branch,
            "base": base_branch,
            "diff_facts": {"changed_paths": changed_paths},
            "verification_bundle": bundle_ref,
        }
        request = {**payload, "request_hash": self._canonical_digest(payload)}
        existing = ticket["delivery"].get("pr-body-request")
        if existing is not None and existing != request:
            raise DeliveryBodyError(
                "render-request",
                "persisted PR-body render request contradicts delivery head",
            )
        if existing is None:
            self.kernel.record_delivery_metadata(
                ticket_id, "pr-body-request", request
            )
            self.store.save(self.kernel.ledger)
        return request

    def _verification_bundle_from_handoff(
        self,
        ticket_id: str,
        *,
        phase: str,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        ticket = self.kernel.ledger["tickets"][ticket_id]
        evidence = (
            ticket.get("leaf_results", {})
            .get("verify", {})
            .get("quality", {})
            .get("evidence", [])
        )
        by_id = {item.get("id"): item for item in evidence}
        bundle_reference = by_id.get("verification-checkpoint:bundle-validated")
        handoff_reference = by_id.get("verification-checkpoint:handoff-ready")
        if not isinstance(bundle_reference, dict) or not isinstance(
            handoff_reference, dict
        ):
            raise DeliveryBodyError(
                phase,
                "verify handoff requires bundle-validated and handoff-ready artifacts",
            )

        def load_artifact(reference: dict[str, Any], expected_phase: str) -> tuple[Path, dict[str, Any], str]:
            path = Path(reference["artifact"]).resolve()
            path.relative_to(self.store.path.parent.resolve())
            document = json.loads(path.read_text(encoding="utf-8"))
            recorded_hash = document["artifact_hash"]
            payload = {
                key: value
                for key, value in document.items()
                if key != "artifact_hash"
            }
            if (
                recorded_hash != reference["sha256"]
                or self._canonical_digest(payload) != recorded_hash
                or document.get("phase") != expected_phase
                or document.get("candidate_ref") != ticket["candidate_ref"]
                or not isinstance(document.get("value"), dict)
            ):
                raise DeliveryBodyError(
                    phase, f"verification {expected_phase} artifact is invalid"
                )
            return path, document, recorded_hash

        try:
            bundle_path, bundle_document, bundle_hash = load_artifact(
                bundle_reference, "bundle-validated"
            )
            _handoff_path, _handoff_document, handoff_hash = load_artifact(
                handoff_reference, "handoff-ready"
            )
        except DeliveryBodyError:
            raise
        except (KeyError, OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            raise DeliveryBodyError(
                phase, f"verification handoff bundle is unreadable: {error}"
            ) from error
        return bundle_document["value"], {
            "artifact": str(bundle_path),
            "sha256": bundle_hash,
            "handoff_sha256": handoff_hash,
        }

    def _accept_render_payload(
        self,
        ticket_id: str,
        request: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        body = payload.get("rendered_body")
        bundle = payload.get("verification_bundle")
        root_value = payload.get("verification_audit_root")
        if (
            not isinstance(body, str)
            or not body
            or not isinstance(bundle, dict)
            or not isinstance(root_value, str)
            or not root_value
        ):
            raise DeliveryBodyError(
                "render-validation",
                "rendered body, verification bundle, and verification root are required",
            )
        if payload.get("render_request_hash") != request["request_hash"]:
            raise DeliveryBodyError(
                "render-validation", "rendered body belongs to another request"
            )
        if payload.get("expected_head_sha") != request["expected_head_sha"]:
            raise DeliveryBodyError(
                "render-validation", "rendered body is stale for the delivery head"
            )
        ticket = self.kernel.ledger["tickets"][ticket_id]
        expected_bundle, _bundle_ref = self._verification_bundle_from_handoff(
            ticket_id, phase="render-validation"
        )
        if bundle != expected_bundle:
            raise DeliveryBodyError(
                "render-validation",
                "rendered body bundle differs from the verified handoff bundle",
            )
        verification_root = Path(root_value)
        try:
            validator = load_pr_body_validator(
                verification_root,
                current_candidate=ticket["candidate_ref"],
            )
            normalized_bundle = validator(
                body, bundle, request["expected_head_sha"]
            )
        except VerificationCheckpointError as error:
            raise DeliveryBodyError(
                "render-validation", str(error)
            ) from error

        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        bundle_hash = self._canonical_digest(normalized_bundle)
        artifact_root = (
            self.store.path.parent / "pr-body-artifacts" / ticket_id
        )
        body_path = artifact_root / f"{body_hash}.md"
        bundle_path = artifact_root / f"{bundle_hash}.json"
        self._atomic_text(body_path, body)
        self._atomic_summary(bundle_path, normalized_bundle)
        self.kernel.record_delivery_metadata(
            ticket_id,
            "pr-body",
            {
                "schema": 1,
                "request_hash": request["request_hash"],
                "expected_head_sha": request["expected_head_sha"],
                "body_sha256": body_hash,
                "body_path": str(body_path),
                "bundle_sha256": bundle_hash,
                "bundle_path": str(bundle_path),
                "verification_audit_root": str(verification_root),
            },
        )
        self.store.save(self.kernel.ledger)

    def _load_rendered_body(
        self,
        ticket_id: str,
        request: dict[str, Any],
    ) -> tuple[str, dict[str, Any], Any]:
        ticket = self.kernel.ledger["tickets"][ticket_id]
        record = ticket["delivery"].get("pr-body")
        if not isinstance(record, dict):
            raise DeliveryBodyError(
                "render-validation", "validated PR-body artifact is absent"
            )
        try:
            if (
                record["request_hash"] != request["request_hash"]
                or record["expected_head_sha"] != request["expected_head_sha"]
            ):
                raise DeliveryBodyError(
                    "render-validation", "persisted PR-body artifact is stale"
                )
            artifact_root = (
                self.store.path.parent / "pr-body-artifacts" / ticket_id
            ).resolve()
            body_path = Path(record["body_path"]).resolve()
            bundle_path = Path(record["bundle_path"]).resolve()
            body_path.relative_to(artifact_root)
            bundle_path.relative_to(artifact_root)
            body = body_path.read_text(encoding="utf-8")
            bundle = json.loads(
                bundle_path.read_text(encoding="utf-8")
            )
            if hashlib.sha256(body.encode("utf-8")).hexdigest() != record[
                "body_sha256"
            ]:
                raise DeliveryBodyError(
                    "render-validation", "persisted PR-body hash is invalid"
                )
            if self._canonical_digest(bundle) != record["bundle_sha256"]:
                raise DeliveryBodyError(
                    "render-validation", "persisted verification bundle hash is invalid"
                )
            expected_bundle, _bundle_ref = self._verification_bundle_from_handoff(
                ticket_id, phase="render-validation"
            )
            if bundle != expected_bundle:
                raise DeliveryBodyError(
                    "render-validation",
                    "persisted bundle differs from the verified handoff bundle",
                )
            validator = load_pr_body_validator(
                Path(record["verification_audit_root"]),
                current_candidate=ticket["candidate_ref"],
            )
            validator(body, bundle, request["expected_head_sha"])
        except DeliveryBodyError:
            raise
        except (
            OSError,
            UnicodeError,
            ValueError,
            json.JSONDecodeError,
            VerificationCheckpointError,
        ) as error:
            raise DeliveryBodyError(
                "render-validation", f"persisted PR-body artifact is unreadable: {error}"
            ) from error
        except VerificationCheckpointError as error:
            raise DeliveryBodyError(
                "render-validation", f"persisted PR-body validation failed: {error}"
            ) from error
        return body, bundle, validator

    def _ensure_branch(
        self, ticket_id: str, branch: str, base_branch: str
    ) -> None:
        effect = "delivery-branch"
        current = self._run(
            "git", "symbolic-ref", "--quiet", "--short", "HEAD", allow_failure=True
        )
        if current != branch:
            exists = (
                self.runner.run(
                    ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
                    cwd=self.worktree,
                ).returncode
                == 0
            )
            if exists:
                self._run("git", "switch", branch)
            else:
                self._run("git", "switch", "-c", branch, base_branch)
        self.kernel.record_delivery_metadata(
            ticket_id, "branch", {"branch": branch, "base": base_branch}
        )
        self._record_effect(ticket_id, effect)

    def _ensure_summary(self, ticket_id: str) -> Path:
        _, done_path = _ticket_paths(
            self.kernel, ticket_id, Path(self.kernel.ledger["worktree"])
        )
        summary_path = done_path.with_suffix(".completion.json")
        ticket = self.kernel.ledger["tickets"][ticket_id]
        self._atomic_summary(
            summary_path,
            {
                "schema": 1,
                "run_id": self.kernel.ledger["run_id"],
                "ticket_id": ticket_id,
                "implementation_status": "complete",
                "candidate_ref": ticket["candidate_ref"],
            },
        )
        relative = summary_path.relative_to(self.worktree)
        self._run("git", "add", "--", str(relative))
        self.kernel.record_delivery_metadata(
            ticket_id, "summary", {"path": str(relative)}
        )
        self._record_effect(ticket_id, "completion-summary")
        return summary_path

    def _ensure_commit(
        self, ticket_id: str, branch: str, expected_tree_oid: str
    ) -> str:
        marker = (
            f"Ticket-Autopilot-Run: {self.kernel.ledger['run_id']}/{ticket_id}"
        )
        message = self._run("git", "log", "-1", "--format=%B")
        committed_tree = self._run("git", "rev-parse", "HEAD^{tree}")
        if marker not in message or committed_tree != expected_tree_oid:
            staged_tree = self._run("git", "write-tree")
            if staged_tree != expected_tree_oid:
                raise GitError(
                    "staged delivery tree differs from the revalidated CandidateRef"
                )
            staged = self.runner.run(
                ["git", "diff", "--cached", "--quiet"], cwd=self.worktree
            )
            if staged.returncode == 0:
                raise GitError("delivery commit has no staged changes")
            if staged.returncode != 1:
                raise GitError(staged.stderr or "Git could not inspect staged changes")
            self._run(
                "git",
                "commit",
                "-m",
                (
                    f"ticket {ticket_id}: complete"
                    if marker not in message
                    else f"ticket {ticket_id}: revalidate delivery candidate"
                ),
                "-m",
                marker,
            )
        current_branch = self._run(
            "git", "symbolic-ref", "--quiet", "--short", "HEAD"
        )
        head = self._run("git", "rev-parse", "HEAD")
        committed_tree = self._run("git", "rev-parse", "HEAD^{tree}")
        if current_branch != branch or committed_tree != expected_tree_oid:
            raise GitError(
                "recovered commit marker does not match branch and CandidateRef tree"
            )
        self.kernel.record_delivery_metadata(
            ticket_id, "commit", {"branch": branch, "head_sha": head}
        )
        self._record_effect(ticket_id, "delivery-commit")
        return head

    def _ensure_push(self, ticket_id: str, branch: str, head: str) -> None:
        remote = self._run(
            "git",
            "ls-remote",
            "--heads",
            "origin",
            f"refs/heads/{branch}",
        )
        remote_head = remote.split()[0] if remote else None
        recorded_head = (
            self.kernel.ledger["tickets"][ticket_id]
            .get("delivery", {})
            .get("push", {})
            .get("head_sha")
        )
        if remote_head not in {None, head, recorded_head}:
            raise GitError("remote branch diverged from the idempotent delivery head")
        if remote_head is None:
            self._run("git", "push", "-u", "origin", branch)
        elif remote_head != head:
            self._run("git", "merge-base", "--is-ancestor", remote_head, head)
            self._run("git", "push", "origin", branch)
        self.kernel.record_delivery_metadata(
            ticket_id, "push", {"branch": branch, "head_sha": head}
        )
        self._record_effect(ticket_id, "delivery-push")

    def _validate_pr_receipt(
        self,
        receipt: dict[str, Any],
        *,
        branch: str,
        base_branch: str,
        head: str,
        body: str,
    ) -> None:
        expected = {
            "provider": self.provider.name,
            "operation": "create-or-update-pr",
            "branch": branch,
            "base": base_branch,
            "head_sha": head,
        }
        for key, value in expected.items():
            if receipt.get(key) != value:
                raise TransitionError(
                    f"provider receipt {key} contradicts delivery state"
                )
        if receipt.get("body") != body:
            raise DeliveryBodyError(
                "readback-validation",
                "provider receipt body contradicts validated delivery body",
            )
        if not isinstance(receipt.get("pr_id"), str) or not receipt["pr_id"]:
            raise TransitionError("provider receipt requires pr_id")

    def apply(
        self,
        ticket_id: str,
        *,
        render_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ticket = self.kernel.ledger["tickets"].get(ticket_id)
        open_provider_gates = [
            (gate_id, gate)
            for gate_id, gate in self.kernel.ledger["gates"].items()
            if gate["ticket_id"] == ticket_id
            and gate["category"]
            in {"provider-environment", "provider-pr", "delivery-pr-body"}
            and gate["state"] == "open"
            and gate["resume_state"] in {"verified", "pr-open"}
        ]
        resumable_provider_gate = (
            ticket is not None
            and ticket["state"] == "gated"
            and bool(open_provider_gates)
            and not any(
                gate["ticket_id"] == ticket_id
                and gate["state"] == "open"
                and gate["category"]
                not in {
                    "provider-environment",
                    "provider-pr",
                    "delivery-pr-body",
                }
                for gate in self.kernel.ledger["gates"].values()
            )
        )
        if ticket is None or (
            ticket["state"] not in {"active", "verified", "pr-open"}
            and not resumable_provider_gate
        ):
            raise TransitionError(
                "delivery requires active revalidation, verified, or pr-open state"
            )
        if ticket["state"] == "pr-open":
            return {
                "result": "pr-open",
                "head_sha": ticket["pr"]["head_sha"],
                "branch": ticket["pr"]["branch"],
                "pr_id": ticket["pr"]["pr_id"],
            }
        if ticket["state"] == "active":
            branch_record = ticket["delivery"].get("branch", {})
            return {
                "result": "revalidation-required",
                "tree_oid": ticket["candidate_ref"]["tree_oid"],
                "branch": branch_record.get("branch"),
            }
        plan = build_delivery_plan(
            self.provider,
            self.kernel.ledger,
            ticket_id,
            default_base="main",
            title=f"Ticket {ticket_id}",
            body_artifact=f"render-pending://{self.kernel.ledger['run_id']}/{ticket_id}",
        )
        self._ensure_branch(ticket_id, plan.branch, plan.base_branch)
        prepared = ticket["delivery"].get("prepared")
        if prepared is None:
            finalize_done(self.store, self.kernel, ticket_id)
            self._ensure_summary(ticket_id)
            fixed = candidate_ref(self.worktree, ticket["ticket_digest"])
            self.kernel.record_delivery_candidate(ticket_id, fixed)
            self.kernel.record_delivery_metadata(
                ticket_id,
                "prepared",
                {"candidate_ref": asdict(fixed)},
            )
            self.store.save(self.kernel.ledger)
            prepared = ticket["delivery"]["prepared"]
        fixed = candidate_ref(self.worktree, ticket["ticket_digest"])
        prepared_ref = prepared.get("candidate_ref", {})
        if any(
            prepared_ref.get(field) != getattr(fixed, field)
            for field in ("contract_version", "ticket_digest", "tree_oid")
        ):
            raise GitError(
                "prepared delivery tree differs from the recorded delivery CandidateRef"
            )
        head = self._ensure_commit(ticket_id, plan.branch, fixed.tree_oid)
        self._ensure_push(ticket_id, plan.branch, head)
        request = self._render_request(
            ticket_id,
            branch=plan.branch,
            base_branch=plan.base_branch,
            head=head,
        )
        if render_payload is not None:
            self._accept_render_payload(ticket_id, request, render_payload)
        if not ticket["delivery"].get("pr-body"):
            self.kernel.record_delivery_metadata(
                ticket_id,
                "result",
                {"phase": "render", "result": "render-required"},
            )
            self.store.save(self.kernel.ledger)
            return {
                "result": "render-required",
                "head_sha": head,
                "branch": plan.branch,
                "render_request_hash": request["request_hash"],
                "render_request": request,
            }
        body, bundle, body_validator = self._load_rendered_body(
            ticket_id, request
        )
        pr_receipt = self.executor.execute(
            CREATE_OR_UPDATE_PR,
            branch=plan.branch,
            base=plan.base_branch,
            head_sha=head,
            title=f"Ticket {ticket_id}",
            body_artifact=body,
        )
        if pr_receipt.get("evidence_class") != "live":
            self.kernel.record_delivery_metadata(
                ticket_id, "provider-simulation", pr_receipt
            )
            self.kernel.record_delivery_metadata(
                ticket_id,
                "result",
                {
                    "phase": "provider",
                    "result": "waiting-provider",
                    "gate": "provider-pr",
                },
            )
            if not open_provider_gates:
                self.kernel.open_gate(
                    ticket_id,
                    "provider-pr",
                    scope="ticket",
                    reason=(
                        "simulated provider evidence cannot authorize PR state; "
                        "resume this run in live provider mode"
                    ),
                )
                self.store.save(self.kernel.ledger)
            return {
                "result": "waiting-provider",
                "head_sha": head,
                "branch": plan.branch,
                "provider_receipt": pr_receipt,
            }
        self._validate_pr_receipt(
            pr_receipt,
            branch=plan.branch,
            base_branch=plan.base_branch,
            head=head,
            body=body,
        )
        try:
            body_validator(
                pr_receipt["body"], bundle, pr_receipt["head_sha"]
            )
        except VerificationCheckpointError as error:
            raise DeliveryBodyError(
                "readback-validation",
                f"provider PR-body readback validation failed: {error}",
            ) from error
        for gate_id, _gate in open_provider_gates:
            self.kernel.approve_gate(
                gate_id,
                actor=f"provider:{self.provider.name}",
                evidence=f"live-readback:{pr_receipt['pr_id']}:{head}",
            )
        self.store.save(self.kernel.ledger)
        self.kernel.record_delivery_metadata(ticket_id, "pr", pr_receipt)
        self.kernel.record_delivery_metadata(
            ticket_id,
            "result",
            {"phase": "readback", "result": "pr-open"},
        )
        self.kernel.record_pr(
            ticket_id,
            provider=self.provider.name,
            pr_id=pr_receipt["pr_id"],
            head_sha=head,
            branch=plan.branch,
        )
        self._record_effect(ticket_id, "delivery-pr")
        return {
            "result": "pr-open",
            "head_sha": head,
            "branch": plan.branch,
            "pr_id": pr_receipt["pr_id"],
        }
