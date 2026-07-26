from __future__ import annotations

import re
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .git_ops import CommandRunner, SubprocessCommandRunner


CREATE_OR_UPDATE_PR = "create-or-update-pr"
GET_PR_STATE = "get-pr-state"
RETARGET_PR = "retarget-pr"
GET_CHECKS_AND_POLICIES = "get-checks-and-policies"
GET_APPROVALS = "get-approvals"
MERGE_WITH_EXPECTED_HEAD = "merge-with-expected-head"
REQUIRED_CAPABILITIES = frozenset(
    {
        CREATE_OR_UPDATE_PR,
        GET_PR_STATE,
        GET_CHECKS_AND_POLICIES,
        GET_APPROVALS,
    }
)
# Compatibility name for the internal kernel import. The public normalized operation is
# MERGE_WITH_EXPECTED_HEAD.
MERGE_EXPECTED_HEAD = MERGE_WITH_EXPECTED_HEAD
AZURE_UPDATE_PR_DOCUMENTATION = (
    "https://learn.microsoft.com/en-us/rest/api/azure/devops/git/"
    "pull-requests/update"
)


class ProviderError(RuntimeError):
    """A remote provider is unknown, incapable, or unsafe for the requested action."""


@dataclass(frozen=True)
class MergeAuthorization:
    provider: str
    pr_id: str
    head_sha: str
    actor: str
    evidence: str


@dataclass(frozen=True)
class DeliveryPlan:
    ticket_id: str
    branch: str
    base_branch: str
    stacked_on: str | None
    local_commands: tuple[tuple[str, ...], ...]
    provider_operation: dict[str, str]


class RemoteProvider:
    name = "unknown"
    capabilities: frozenset[str] = frozenset()

    def negotiate(self, required: set[str] | frozenset[str]) -> dict[str, object]:
        missing = sorted(set(required) - self.capabilities)
        if missing:
            raise ProviderError(
                f"{self.name} provider lacks required capabilities: {', '.join(missing)}"
            )
        return {
            "provider": self.name,
            "capabilities": sorted(self.capabilities),
            "required": sorted(required),
        }

    def _validate_authorization(
        self,
        pr_id: str,
        current_head_sha: str,
        authorization: MergeAuthorization,
    ) -> None:
        if authorization.provider != self.name:
            raise ProviderError("merge authorization belongs to another provider")
        if authorization.pr_id != pr_id:
            raise ProviderError("merge authorization belongs to another PR")
        if authorization.head_sha != current_head_sha:
            raise ProviderError("merge authorization is stale for the current PR head")
        if not authorization.actor or not authorization.evidence:
            raise ProviderError("merge authorization requires actor and evidence")

    def merge_command(
        self,
        pr_id: str,
        current_head_sha: str,
        authorization: MergeAuthorization,
    ) -> list[str]:
        raise NotImplementedError

    def operation(self, operation: str, **parameters: str) -> dict[str, object]:
        if operation not in {
            CREATE_OR_UPDATE_PR,
            GET_PR_STATE,
            RETARGET_PR,
            GET_CHECKS_AND_POLICIES,
            GET_APPROVALS,
            MERGE_WITH_EXPECTED_HEAD,
        }:
            raise ProviderError(f"unknown normalized provider operation: {operation}")
        self.negotiate({operation})
        return {
            "schema": 1,
            "provider": self.name,
            "operation": operation,
            "parameters": dict(sorted(parameters.items())),
        }

    def retarget_command(self, pr_id: str, base_branch: str) -> list[str]:
        raise NotImplementedError

    def reconciliation_commands(
        self,
        *,
        branch: str,
        parent_branch: str,
        base_branch: str,
        expected_remote_sha: str,
    ) -> list[list[str]]:
        if not all(
            (branch, parent_branch, base_branch, expected_remote_sha)
        ):
            raise ProviderError("reconciliation inputs must be non-empty")
        return [
            ["git", "rebase", "--onto", base_branch, parent_branch, branch],
            [
                "git",
                "push",
                "origin",
                branch,
                f"--force-with-lease=refs/heads/{branch}:{expected_remote_sha}",
            ],
        ]


class GitHubProvider(RemoteProvider):
    name = "github"
    capabilities = REQUIRED_CAPABILITIES | {
        RETARGET_PR,
        MERGE_WITH_EXPECTED_HEAD,
    }

    def merge_command(
        self,
        pr_id: str,
        current_head_sha: str,
        authorization: MergeAuthorization,
    ) -> list[str]:
        self._validate_authorization(pr_id, current_head_sha, authorization)
        return [
            "gh",
            "pr",
            "merge",
            pr_id,
            "--match-head-commit",
            current_head_sha,
        ]

    def retarget_command(self, pr_id: str, base_branch: str) -> list[str]:
        return ["gh", "pr", "edit", pr_id, "--base", base_branch]

class AzureDevOpsProvider(RemoteProvider):
    name = "azure-devops"
    capabilities = REQUIRED_CAPABILITIES

    def merge_command(
        self,
        pr_id: str,
        current_head_sha: str,
        authorization: MergeAuthorization,
    ) -> list[str]:
        self._validate_authorization(pr_id, current_head_sha, authorization)
        raise ProviderError(
            "Azure DevOps does not document an atomic expected-head completion "
            "precondition; merge-expected-head is unsupported "
            f"({AZURE_UPDATE_PR_DOCUMENTATION})"
        )

    def retarget_command(self, pr_id: str, base_branch: str) -> list[str]:
        raise ProviderError(
            "Azure DevOps PR retarget is unsupported by this runner; "
            "complete it externally and resume through an explicit HITL gate"
        )


class ProviderExecutor:
    """Execute normalized provider operations and return observed receipts.

    The executor is the only boundary allowed to mint a live provider receipt. In
    simulated mode it never invokes a command and labels the result so the kernel can
    keep it below integration/completion claim gates.
    """

    def __init__(
        self,
        provider: RemoteProvider,
        *,
        cwd: Path,
        mode: str = "live",
        runner: CommandRunner | None = None,
    ):
        if mode not in {"live", "simulated"}:
            raise ProviderError("provider mode must be live or simulated")
        self.provider = provider
        self.cwd = cwd
        self.mode = mode
        self.runner = runner or SubprocessCommandRunner()

    def _run(self, command: list[str]) -> str:
        result = self.runner.run(command, cwd=self.cwd)
        if result.returncode:
            detail = result.stderr or result.stdout or "provider command failed"
            raise ProviderError(f"{' '.join(command)} failed: {detail}")
        return result.stdout

    def _json(self, command: list[str]) -> Any:
        raw = self._run(command)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise ProviderError(
                f"{' '.join(command)} returned invalid JSON"
            ) from error

    @staticmethod
    def _branch(value: Any) -> str | None:
        if not isinstance(value, str) or not value:
            return None
        prefix = "refs/heads/"
        return value[len(prefix) :] if value.startswith(prefix) else value

    @staticmethod
    def _pr_id(value: Any) -> str:
        if isinstance(value, (str, int)) and str(value):
            return str(value)
        raise ProviderError("provider readback omitted PR ID")

    @staticmethod
    def _github_state(document: dict[str, Any]) -> str:
        if document.get("mergedAt"):
            return "merged"
        state = str(document.get("state", "")).casefold()
        if state == "open":
            return "open"
        if state in {"closed", "merged"}:
            return state
        raise ProviderError("GitHub readback returned an unknown PR state")

    @staticmethod
    def _azure_state(document: dict[str, Any]) -> str:
        state = str(document.get("status", "")).casefold()
        normalized = {
            "active": "open",
            "completed": "merged",
            "abandoned": "closed",
        }.get(state)
        if normalized is None:
            raise ProviderError("Azure DevOps readback returned an unknown PR state")
        return normalized

    def _simulated(
        self, operation: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "schema": 1,
            "provider": self.provider.name,
            "operation": operation,
            "evidence_class": "simulated",
            "observed": False,
            "parameters": {
                key: value
                for key, value in sorted(parameters.items())
                if isinstance(value, (str, int, bool)) or value is None
            },
        }

    def execute(self, operation: str, **parameters: Any) -> dict[str, Any]:
        string_parameters = {
            key: str(value)
            for key, value in parameters.items()
            if value is not None
        }
        self.provider.operation(operation, **string_parameters)
        if self.mode == "simulated":
            return self._simulated(operation, parameters)
        if self.provider.name == "github":
            return self._execute_github(operation, parameters)
        if self.provider.name == "azure-devops":
            return self._execute_azure(operation, parameters)
        raise ProviderError(f"no live executor for provider {self.provider.name}")

    def _github_view(self, pr_id: str) -> dict[str, Any]:
        document = self._json(
            [
                "gh",
                "pr",
                "view",
                pr_id,
                "--json",
                "number,url,state,mergedAt,headRefName,headRefOid,baseRefName,"
                "reviewDecision,reviews",
            ]
        )
        if not isinstance(document, dict):
            raise ProviderError("GitHub PR readback must be an object")
        return document

    def _github_state_receipt(
        self, operation: str, document: dict[str, Any]
    ) -> dict[str, Any]:
        head_sha = document.get("headRefOid")
        base = document.get("baseRefName")
        if not isinstance(head_sha, str) or not head_sha:
            raise ProviderError("GitHub readback omitted head SHA")
        if not isinstance(base, str) or not base:
            raise ProviderError("GitHub readback omitted base branch")
        return {
            "schema": 1,
            "provider": "github",
            "operation": operation,
            "evidence_class": "live",
            "observed": True,
            "pr_id": self._pr_id(document.get("number")),
            "branch": self._branch(document.get("headRefName")),
            "base": base,
            "head_sha": head_sha,
            "state": self._github_state(document),
            "url": document.get("url"),
        }

    def _execute_github(
        self, operation: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        pr_id = str(parameters.get("pr_id", ""))
        if operation == CREATE_OR_UPDATE_PR:
            branch = str(parameters.get("branch", ""))
            base = str(parameters.get("base", ""))
            head_sha = str(parameters.get("head_sha", ""))
            title = str(parameters.get("title", ""))
            body = str(parameters.get("body_artifact", ""))
            if not all((branch, base, head_sha, title, body)):
                raise ProviderError("create-or-update-pr parameters must be non-empty")
            listed = self._json(
                [
                    "gh",
                    "pr",
                    "list",
                    "--head",
                    branch,
                    "--state",
                    "all",
                    "--json",
                    "number",
                    "--limit",
                    "1",
                ]
            )
            if not isinstance(listed, list):
                raise ProviderError("GitHub PR list readback must be an array")
            if listed:
                item = listed[0]
                if not isinstance(item, dict):
                    raise ProviderError("GitHub PR list item must be an object")
                pr_id = self._pr_id(item.get("number"))
                self._run(
                    [
                        "gh",
                        "pr",
                        "edit",
                        pr_id,
                        "--base",
                        base,
                        "--title",
                        title,
                        "--body",
                        body,
                    ]
                )
            else:
                self._run(
                    [
                        "gh",
                        "pr",
                        "create",
                        "--head",
                        branch,
                        "--base",
                        base,
                        "--title",
                        title,
                        "--body",
                        body,
                    ]
                )
                listed = self._json(
                    [
                        "gh",
                        "pr",
                        "list",
                        "--head",
                        branch,
                        "--state",
                        "open",
                        "--json",
                        "number",
                        "--limit",
                        "1",
                    ]
                )
                if not isinstance(listed, list) or len(listed) != 1:
                    raise ProviderError("GitHub PR creation readback was not unique")
                pr_id = self._pr_id(listed[0].get("number"))
            receipt = self._github_state_receipt(
                operation, self._github_view(pr_id)
            )
            expected = {
                "branch": branch,
                "base": base,
                "head_sha": head_sha,
            }
            if any(receipt.get(key) != value for key, value in expected.items()):
                raise ProviderError(
                    "GitHub PR readback contradicts requested branch, base, or head"
                )
            return receipt
        if operation == GET_PR_STATE:
            if not pr_id:
                raise ProviderError("get-pr-state requires pr_id")
            return self._github_state_receipt(
                operation, self._github_view(pr_id)
            )
        if operation == RETARGET_PR:
            base = str(parameters.get("base", ""))
            if not pr_id or not base:
                raise ProviderError("retarget-pr requires pr_id and base")
            self._run(["gh", "pr", "edit", pr_id, "--base", base])
            receipt = self._github_state_receipt(
                operation, self._github_view(pr_id)
            )
            if receipt["base"] != base:
                raise ProviderError("GitHub retarget readback contradicts requested base")
            return receipt
        if operation == GET_CHECKS_AND_POLICIES:
            if not pr_id:
                raise ProviderError("get-checks-and-policies requires pr_id")
            checks = self._json(
                [
                    "gh",
                    "pr",
                    "checks",
                    pr_id,
                    "--json",
                    "bucket,name,state,workflow",
                ]
            )
            if not isinstance(checks, list):
                raise ProviderError("GitHub checks readback must be an array")
            return {
                "schema": 1,
                "provider": "github",
                "operation": operation,
                "evidence_class": "live",
                "observed": True,
                "pr_id": pr_id,
                "checks_and_policies": checks,
            }
        if operation == GET_APPROVALS:
            if not pr_id:
                raise ProviderError("get-approvals requires pr_id")
            document = self._github_view(pr_id)
            return {
                "schema": 1,
                "provider": "github",
                "operation": operation,
                "evidence_class": "live",
                "observed": True,
                "pr_id": self._pr_id(document.get("number")),
                "review_decision": document.get("reviewDecision"),
                "reviews": document.get("reviews", []),
            }
        raise ProviderError(
            f"live execution of {operation} is not exposed by this workflow"
        )

    def _azure_view(self, pr_id: str) -> dict[str, Any]:
        document = self._json(
            ["az", "repos", "pr", "show", "--id", pr_id, "--output", "json"]
        )
        if not isinstance(document, dict):
            raise ProviderError("Azure DevOps PR readback must be an object")
        return document

    def _azure_state_receipt(
        self, operation: str, document: dict[str, Any]
    ) -> dict[str, Any]:
        source_commit = document.get("lastMergeSourceCommit")
        head_sha = (
            source_commit.get("commitId")
            if isinstance(source_commit, dict)
            else None
        )
        base = self._branch(document.get("targetRefName"))
        if not isinstance(head_sha, str) or not head_sha:
            raise ProviderError("Azure DevOps readback omitted head SHA")
        if not base:
            raise ProviderError("Azure DevOps readback omitted target branch")
        return {
            "schema": 1,
            "provider": "azure-devops",
            "operation": operation,
            "evidence_class": "live",
            "observed": True,
            "pr_id": self._pr_id(document.get("pullRequestId")),
            "branch": self._branch(document.get("sourceRefName")),
            "base": base,
            "head_sha": head_sha,
            "state": self._azure_state(document),
            "url": document.get("url"),
        }

    def _execute_azure(
        self, operation: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        pr_id = str(parameters.get("pr_id", ""))
        if operation == CREATE_OR_UPDATE_PR:
            branch = str(parameters.get("branch", ""))
            base = str(parameters.get("base", ""))
            head_sha = str(parameters.get("head_sha", ""))
            title = str(parameters.get("title", ""))
            body = str(parameters.get("body_artifact", ""))
            if not all((branch, base, head_sha, title, body)):
                raise ProviderError("create-or-update-pr parameters must be non-empty")
            listed = self._json(
                [
                    "az",
                    "repos",
                    "pr",
                    "list",
                    "--source-branch",
                    branch,
                    "--status",
                    "all",
                    "--output",
                    "json",
                ]
            )
            if not isinstance(listed, list):
                raise ProviderError("Azure DevOps PR list readback must be an array")
            if listed:
                item = listed[0]
                if not isinstance(item, dict):
                    raise ProviderError("Azure DevOps PR list item must be an object")
                pr_id = self._pr_id(item.get("pullRequestId"))
                current_base = self._branch(item.get("targetRefName"))
                if current_base != base:
                    raise ProviderError(
                        "existing Azure DevOps PR requires unsupported retarget"
                    )
                self._run(
                    [
                        "az",
                        "repos",
                        "pr",
                        "update",
                        "--id",
                        pr_id,
                        "--title",
                        title,
                        "--description",
                        body,
                        "--output",
                        "json",
                    ]
                )
            else:
                created = self._json(
                    [
                        "az",
                        "repos",
                        "pr",
                        "create",
                        "--source-branch",
                        branch,
                        "--target-branch",
                        base,
                        "--title",
                        title,
                        "--description",
                        body,
                        "--output",
                        "json",
                    ]
                )
                if not isinstance(created, dict):
                    raise ProviderError("Azure DevOps PR creation must return an object")
                pr_id = self._pr_id(created.get("pullRequestId"))
            receipt = self._azure_state_receipt(
                operation, self._azure_view(pr_id)
            )
            expected = {
                "branch": branch,
                "base": base,
                "head_sha": head_sha,
            }
            if any(receipt.get(key) != value for key, value in expected.items()):
                raise ProviderError(
                    "Azure DevOps PR readback contradicts requested branch, base, or head"
                )
            return receipt
        if operation == GET_PR_STATE:
            if not pr_id:
                raise ProviderError("get-pr-state requires pr_id")
            return self._azure_state_receipt(
                operation, self._azure_view(pr_id)
            )
        if operation == GET_CHECKS_AND_POLICIES:
            if not pr_id:
                raise ProviderError("get-checks-and-policies requires pr_id")
            policies = self._json(
                [
                    "az",
                    "repos",
                    "pr",
                    "policy",
                    "list",
                    "--id",
                    pr_id,
                    "--output",
                    "json",
                ]
            )
            if not isinstance(policies, list):
                raise ProviderError("Azure DevOps policies readback must be an array")
            return {
                "schema": 1,
                "provider": "azure-devops",
                "operation": operation,
                "evidence_class": "live",
                "observed": True,
                "pr_id": pr_id,
                "checks_and_policies": policies,
            }
        if operation == GET_APPROVALS:
            if not pr_id:
                raise ProviderError("get-approvals requires pr_id")
            document = self._azure_view(pr_id)
            return {
                "schema": 1,
                "provider": "azure-devops",
                "operation": operation,
                "evidence_class": "live",
                "observed": True,
                "pr_id": self._pr_id(document.get("pullRequestId")),
                "reviews": document.get("reviewers", []),
            }
        raise ProviderError(
            f"live execution of {operation} is unsupported for Azure DevOps"
        )


def detect_provider(remote_url: str, override: str | None = None) -> RemoteProvider:
    selected = override.casefold() if override else None
    if selected in {"github", "gh"}:
        return GitHubProvider()
    if selected in {"azure", "azure-devops", "ado"}:
        return AzureDevOpsProvider()
    if selected:
        raise ProviderError(f"unsupported provider override: {override}")

    normalized = remote_url.casefold()
    if re.search(r"(?:^|[.@/])github\.com(?::|/)", normalized):
        return GitHubProvider()
    if "dev.azure.com/" in normalized or "visualstudio.com/" in normalized:
        return AzureDevOpsProvider()
    raise ProviderError(
        "remote provider cannot be detected; pass an explicit supported override"
    )


def build_delivery_plan(
    provider: RemoteProvider,
    ledger: dict[str, Any],
    ticket_id: str,
    *,
    default_base: str,
    title: str,
    body_artifact: str,
) -> DeliveryPlan:
    provider.negotiate(REQUIRED_CAPABILITIES)
    try:
        ticket = ledger["tickets"][ticket_id]
    except KeyError as error:
        raise ProviderError(f"unknown ticket {ticket_id!r}") from error
    blockers = ticket["blocked_by"]
    stacked_on: str | None = None
    if not blockers:
        base_branch = default_base
    elif len(blockers) == 1:
        parent_id = blockers[0]
        parent = ledger["tickets"][parent_id]
        if parent["state"] == "integrated":
            base_branch = default_base
        elif parent["state"] == "pr-open" and parent.get("pr", {}).get("branch"):
            base_branch = parent["pr"]["branch"]
            stacked_on = parent_id
        else:
            raise ProviderError("single-parent delivery is not stackable yet")
    else:
        if not all(ledger["tickets"][item]["state"] == "integrated" for item in blockers):
            raise ProviderError("multi-blocker join must wait for integration")
        base_branch = default_base
    branch = f"ticket-autopilot/{ledger['run_id']}/{ticket_id}"
    return DeliveryPlan(
        ticket_id=ticket_id,
        branch=branch,
        base_branch=base_branch,
        stacked_on=stacked_on,
        local_commands=(("git", "switch", "-c", branch, base_branch),),
        provider_operation={
            "operation": "create-or-update-pr",
            "provider": provider.name,
            "head": branch,
            "base": base_branch,
            "title": title,
            "body_artifact": body_artifact,
        },
    )
