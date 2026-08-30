from __future__ import annotations

import re
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .git_ops import CommandRunner, SubprocessCommandRunner


CREATE_OR_UPDATE_PR = "create-or-update-pr"
GET_PR_STATE = "get-pr-state"
RETARGET_PR = "retarget-pr"
GET_CHECKS_AND_POLICIES = "get-checks-and-policies"
GET_APPROVALS = "get-approvals"
MERGE_WITH_EXPECTED_HEAD = "merge-with-expected-head"
GET_REPOSITORY = "get-repository"
CREATE_PRIVATE_REPOSITORY = "create-private-repository"
GET_REPOSITORY_BRANCH = "get-repository-branch"
SET_DEFAULT_BRANCH = "set-default-branch"
REPOSITORY_BOOTSTRAP_CAPABILITIES = frozenset(
    {
        GET_REPOSITORY,
        CREATE_PRIVATE_REPOSITORY,
        GET_REPOSITORY_BRANCH,
        SET_DEFAULT_BRANCH,
    }
)
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
GITHUB_QUEUE_READBACK_QUERY = (
    "query($pullRequestId:ID!){node(id:$pullRequestId){... on PullRequest{"
    "headRefOid mergeQueueEntry{id position state enqueuedAt}}}}"
)
GITHUB_QUEUE_MUTATION = (
    "mutation($pullRequestId:ID!,$expectedHeadOid:GitObjectID!,"
    "$clientMutationId:String!){enqueuePullRequest(input:{"
    "pullRequestId:$pullRequestId,expectedHeadOid:$expectedHeadOid,"
    "clientMutationId:$clientMutationId}){clientMutationId "
    "mergeQueueEntry{id position state enqueuedAt}}}"
)
GITHUB_RULES_PLAN_LIMIT_MESSAGE = (
    "Upgrade to GitHub Pro or make this repository public to enable this feature."
)
GITHUB_RULES_DOCUMENTATION_URL = (
    "https://docs.github.com/rest/repos/rules#get-rules-for-a-branch"
)


class ProviderError(RuntimeError):
    """A remote provider is unknown, incapable, or unsafe for the requested action."""


_NEGATIVE_NUMBER = re.compile(r"^-\d+$|^-\d*\.\d+$")

# The option that always follows `--description` in the argument vector below. The test
# double reads the description back to this sentinel, so the two stay in step.
AZURE_DESCRIPTION_TERMINATOR = "--output"


def _azure_description_arguments(body: str) -> list[str]:
    """Expand a PR body into the argument vector `az ... --description` rejoins.

    `--description` is `nargs='+'` and Azure DevOps documents it as "Each value sent to
    this arg will be a new line", so the stored description is `"\\n".join(values)`.
    `split("\\n")` is that join's exact inverse; `splitlines()` is not, because it drops a
    trailing newline and also collapses CRLF, `\\v`, `\\f`, `\\x1c`-`\\x1e`, `\\x85`,
    U+2028 and U+2029 into `\\n`. Any of those makes the readback differ from the
    validated body and opens the `delivery-pr-body` gate on a body that is in fact correct.

    A line that `argparse` reads as an option cannot be delivered through this argument at
    all: `az` answers `unrecognized arguments` and never reaches the service. Fail here
    instead, naming the line, so the cause is visible rather than opaque.
    """

    values = body.split("\n")
    for index, line in enumerate(values):
        if _parses_as_option(line):
            raise ProviderError(
                "Azure DevOps cannot receive PR body line "
                f"{index + 1} verbatim through --description: {line!r} is parsed as a "
                "command-line option"
            )
    return values


def _parses_as_option(line: str) -> bool:
    """Whether `argparse` would treat `line` as an option rather than a value.

    Mirrors `argparse._parse_optional`: a leading prefix character, more than one
    character, no embedded space, and not a negative number. Markdown bullets (`- item`)
    contain a space and are therefore safe; a horizontal rule (`---`) is not.
    """

    if len(line) < 2 or not line.startswith("-") or " " in line:
        return False
    return not _NEGATIVE_NUMBER.match(line)


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
            GET_REPOSITORY,
            CREATE_PRIVATE_REPOSITORY,
            GET_REPOSITORY_BRANCH,
            SET_DEFAULT_BRANCH,
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
    capabilities = REQUIRED_CAPABILITIES | REPOSITORY_BOOTSTRAP_CAPABILITIES | {
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
            "--merge",
        ]

    def retarget_command(self, pr_id: str, base_branch: str) -> list[str]:
        return [
            "gh",
            "api",
            f"repos/{{owner}}/{{repo}}/pulls/{pr_id}",
            "--method",
            "PATCH",
            "--raw-field",
            f"base={base_branch}",
        ]

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

    def _json(
        self,
        command: list[str],
        *,
        accepted_returncodes: frozenset[int] = frozenset({0}),
    ) -> Any:
        result = self.runner.run(command, cwd=self.cwd)
        if result.returncode not in accepted_returncodes:
            detail = result.stderr or result.stdout or "provider command failed"
            raise ProviderError(f"{' '.join(command)} failed: {detail}")
        try:
            return json.loads(result.stdout)
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
    def _github_check_bucket(state: str) -> str:
        normalized = state.casefold()
        if normalized in {"success", "successful", "neutral", "skipped"}:
            return "pass"
        if normalized in {
            "pending",
            "queued",
            "in_progress",
            "requested",
            "waiting",
            "expected",
        }:
            return "pending"
        if normalized in {
            "failure",
            "failed",
            "error",
            "cancelled",
            "canceled",
            "timed_out",
            "action_required",
            "stale",
            "startup_failure",
        }:
            return "fail"
        return "unknown"

    @classmethod
    def _github_check_item(cls, item: Any) -> dict[str, str]:
        if not isinstance(item, dict):
            raise ProviderError("GitHub status check rollup item must be an object")
        name = item.get("name") or item.get("context")
        state = (
            item.get("conclusion")
            or item.get("state")
            or item.get("status")
        )
        workflow_value = item.get("workflowName") or item.get("workflow") or ""
        workflow = (
            workflow_value.get("name", "")
            if isinstance(workflow_value, dict)
            else workflow_value
        )
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(state, str)
            or not state
            or not isinstance(workflow, str)
        ):
            raise ProviderError("GitHub status check rollup item is malformed")
        return {
            "bucket": cls._github_check_bucket(state),
            "name": name,
            "state": state,
            "workflow": workflow,
        }

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
                "number,url,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName,"
                "body,reviewDecision,reviews,mergeable,mergeStateStatus",
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
        body = document.get("body")
        if not isinstance(body, str):
            raise ProviderError("GitHub readback omitted PR body")
        merge_commit_document = document.get("mergeCommit")
        merge_commit_sha = (
            merge_commit_document.get("oid")
            if isinstance(merge_commit_document, dict)
            else None
        )
        if merge_commit_sha is not None and (
            not isinstance(merge_commit_sha, str) or not merge_commit_sha
        ):
            raise ProviderError("GitHub readback returned a malformed merge commit")
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
            "merge_commit_sha": merge_commit_sha,
            "body": body,
            "state": self._github_state(document),
            "url": document.get("url"),
            "mergeable": document.get("mergeable"),
            "merge_state_status": document.get("mergeStateStatus"),
        }

    def _github_active_rules(
        self, base: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        command = [
            "gh",
            "api",
            f"repos/{{owner}}/{{repo}}/rules/branches/{quote(base, safe='')}",
        ]
        result = self.runner.run(command, cwd=self.cwd)
        try:
            document = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            if result.returncode:
                detail = result.stderr or result.stdout or "provider command failed"
                raise ProviderError(f"{' '.join(command)} failed: {detail}") from error
            raise ProviderError(
                f"{' '.join(command)} returned invalid JSON"
            ) from error
        if result.returncode:
            if (
                isinstance(document, dict)
                and document.get("status") == "403"
                and document.get("message") == GITHUB_RULES_PLAN_LIMIT_MESSAGE
                and document.get("documentation_url")
                == GITHUB_RULES_DOCUMENTATION_URL
            ):
                return [], {
                    "schema": 1,
                    "source": "github-active-rules-api",
                    "status": "feature-unavailable",
                    "reason": "private-repository-plan-limit",
                    "http_status": 403,
                    "documentation_url": GITHUB_RULES_DOCUMENTATION_URL,
                }
            detail = result.stderr or result.stdout or "provider command failed"
            raise ProviderError(f"{' '.join(command)} failed: {detail}")
        rules = document
        if not isinstance(rules, list) or any(
            not isinstance(rule, dict)
            or not isinstance(rule.get("type"), str)
            or not rule["type"]
            for rule in rules
        ):
            raise ProviderError("GitHub active branch rules readback is malformed")
        return rules, {
            "schema": 1,
            "source": "github-active-rules-api",
            "status": "observed",
        }

    @staticmethod
    def _github_queue_entry(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if (
            not isinstance(value, dict)
            or not isinstance(value.get("id"), str)
            or not value["id"]
            or not isinstance(value.get("position"), int)
            or not isinstance(value.get("state"), str)
            or not value["state"]
            or not isinstance(value.get("enqueuedAt"), str)
            or not value["enqueuedAt"]
        ):
            raise ProviderError("GitHub merge-queue entry readback is malformed")
        return {
            "id": value["id"],
            "position": value["position"],
            "state": value["state"],
            "enqueuedAt": value["enqueuedAt"],
        }

    def _github_queue_readback(
        self, pull_request_id: str, expected_head: str
    ) -> dict[str, Any] | None:
        document = self._json(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                f"query={GITHUB_QUEUE_READBACK_QUERY}",
                "-f",
                f"pullRequestId={pull_request_id}",
            ]
        )
        node = (
            document.get("data", {}).get("node")
            if isinstance(document, dict)
            and isinstance(document.get("data"), dict)
            else None
        )
        if not isinstance(node, dict):
            raise ProviderError("GitHub merge-queue PR readback is malformed")
        if node.get("headRefOid") != expected_head:
            raise ProviderError(
                "GitHub merge-queue readback belongs to a different PR head"
            )
        return self._github_queue_entry(node.get("mergeQueueEntry"))

    def _github_merge_context(
        self, pr_id: str, expected_head: str
    ) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
        document = self._json(
            [
                "gh",
                "pr",
                "view",
                pr_id,
                "--json",
                "id,headRefOid,baseRefName",
            ]
        )
        if not isinstance(document, dict):
            raise ProviderError("GitHub merge context readback must be an object")
        if document.get("headRefOid") != expected_head:
            raise ProviderError("GitHub merge context belongs to a different PR head")
        pull_request_id = document.get("id")
        base = document.get("baseRefName")
        if not isinstance(pull_request_id, str) or not pull_request_id:
            raise ProviderError("GitHub merge context omitted PR node ID")
        if not isinstance(base, str) or not base:
            raise ProviderError("GitHub merge context omitted base branch")
        rules, observation = self._github_active_rules(base)
        return pull_request_id, rules, observation

    @staticmethod
    def _github_not_found(stdout: str, stderr: str) -> bool:
        for raw in (stdout, stderr):
            try:
                document = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            if (
                isinstance(document, dict)
                and document.get("message") == "Not Found"
                and str(document.get("status")) == "404"
            ):
                return True
        detail = (stderr or stdout).strip()
        return detail == "gh: Not Found (HTTP 404)"

    @staticmethod
    def _github_empty_repository(stdout: str, stderr: str) -> bool:
        for raw in (stdout, stderr):
            try:
                document = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            if (
                isinstance(document, dict)
                and document.get("message") == "Git Repository is empty."
                and str(document.get("status")) == "409"
            ):
                return True
        detail = (stderr or stdout).strip()
        return detail == "gh: Git Repository is empty. (HTTP 409)"

    def _github_json_or_absent(
        self, command: list[str], *, empty_repository_is_absent: bool = False
    ) -> Any | None:
        result = self.runner.run(command, cwd=self.cwd)
        if result.returncode:
            if self._github_not_found(result.stdout, result.stderr) or (
                empty_repository_is_absent
                and self._github_empty_repository(result.stdout, result.stderr)
            ):
                return None
            detail = result.stderr or result.stdout or "provider command failed"
            raise ProviderError(f"{' '.join(command)} failed: {detail}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise ProviderError(
                f"{' '.join(command)} returned invalid JSON"
            ) from error

    def _github_repository(self, target: str, operation: str) -> dict[str, Any]:
        document = self._github_json_or_absent(
            ["gh", "api", "--hostname", "github.com", f"repos/{target}"]
        )
        if document is None:
            return {
                "schema": 1,
                "provider": "github",
                "operation": operation,
                "evidence_class": "live",
                "observed": True,
                "state": "absent",
                "target": target.casefold(),
            }
        if not isinstance(document, dict):
            raise ProviderError("GitHub repository readback must be an object")
        full_name = document.get("full_name")
        private = document.get("private")
        visibility = document.get("visibility")
        default_branch = document.get("default_branch")
        clone_url = document.get("clone_url")
        ssh_url = document.get("ssh_url")
        size = document.get("size")
        if (
            not isinstance(full_name, str)
            or not full_name
            or not isinstance(private, bool)
            or not isinstance(visibility, str)
            or (default_branch is not None and not isinstance(default_branch, str))
            or not isinstance(clone_url, str)
            or not clone_url
            or not isinstance(ssh_url, str)
            or not ssh_url
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
        ):
            raise ProviderError("GitHub repository readback is malformed")
        return {
            "schema": 1,
            "provider": "github",
            "operation": operation,
            "evidence_class": "live",
            "observed": True,
            "state": "present",
            "target": full_name.casefold(),
            "private": private,
            "visibility": visibility,
            "default_branch": default_branch or None,
            "clone_url": clone_url,
            "ssh_url": ssh_url,
            "size": size,
        }

    def _github_repository_branch(
        self, target: str, branch: str, operation: str
    ) -> dict[str, Any]:
        encoded = quote(branch, safe="")
        document = self._github_json_or_absent(
            [
                "gh",
                "api",
                "--hostname",
                "github.com",
                f"repos/{target}/git/ref/heads/{encoded}",
            ],
            empty_repository_is_absent=True,
        )
        if document is None:
            return {
                "schema": 1,
                "provider": "github",
                "operation": operation,
                "evidence_class": "live",
                "observed": True,
                "state": "absent",
                "target": target.casefold(),
                "branch": branch,
            }
        value = document.get("object") if isinstance(document, dict) else None
        sha = value.get("sha") if isinstance(value, dict) else None
        ref = document.get("ref") if isinstance(document, dict) else None
        if not isinstance(sha, str) or not sha or ref != f"refs/heads/{branch}":
            raise ProviderError("GitHub repository branch readback is malformed")
        return {
            "schema": 1,
            "provider": "github",
            "operation": operation,
            "evidence_class": "live",
            "observed": True,
            "state": "present",
            "target": target.casefold(),
            "branch": branch,
            "sha": sha,
        }

    def _execute_github(
        self, operation: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        target = str(parameters.get("target", ""))
        if operation == GET_REPOSITORY:
            if not target:
                raise ProviderError("get-repository requires target")
            return self._github_repository(target, operation)
        if operation == CREATE_PRIVATE_REPOSITORY:
            if not target:
                raise ProviderError("create-private-repository requires target")
            owner, name = target.split("/", 1)
            account = self._json(
                ["gh", "api", "--hostname", "github.com", "user"]
            )
            login = account.get("login") if isinstance(account, dict) else None
            if not isinstance(login, str) or not login:
                raise ProviderError("GitHub account readback omitted login")
            endpoint = "user/repos" if login.casefold() == owner.casefold() else f"orgs/{owner}/repos"
            self._run(
                [
                    "gh",
                    "api",
                    "--hostname",
                    "github.com",
                    "--method",
                    "POST",
                    endpoint,
                    "--raw-field",
                    f"name={name}",
                    "--field",
                    "private=true",
                ]
            )
            receipt = self._github_repository(target, operation)
            if receipt["state"] != "present":
                raise ProviderError("GitHub repository creation readback is absent")
            return receipt
        if operation == GET_REPOSITORY_BRANCH:
            branch = str(parameters.get("branch", ""))
            if not target or not branch:
                raise ProviderError("get-repository-branch requires target and branch")
            return self._github_repository_branch(target, branch, operation)
        if operation == SET_DEFAULT_BRANCH:
            branch = str(parameters.get("branch", ""))
            if not target or not branch:
                raise ProviderError("set-default-branch requires target and branch")
            self._run(
                [
                    "gh",
                    "api",
                    "--hostname",
                    "github.com",
                    f"repos/{target}",
                    "--method",
                    "PATCH",
                    "--raw-field",
                    f"default_branch={branch}",
                ]
            )
            receipt = self._github_repository(target, operation)
            if receipt.get("default_branch") != branch:
                raise ProviderError(
                    "GitHub default-branch readback contradicts requested branch"
                )
            return receipt

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
                        "api",
                        f"repos/{{owner}}/{{repo}}/pulls/{pr_id}",
                        "--method",
                        "PATCH",
                        "--raw-field",
                        f"base={base}",
                        "--raw-field",
                        f"title={title}",
                        "--raw-field",
                        f"body={body}",
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
            command = self.provider.retarget_command(pr_id, base)
            body = parameters.get("body_artifact")
            if body is not None:
                if not isinstance(body, str) or not body:
                    raise ProviderError("retarget-pr body must be non-empty text")
                command.extend(["--raw-field", f"body={body}"])
            self._run(command)
            receipt = self._github_state_receipt(
                operation, self._github_view(pr_id)
            )
            if receipt["base"] != base:
                raise ProviderError("GitHub retarget readback contradicts requested base")
            if body is not None and receipt["body"] != body:
                raise ProviderError("GitHub retarget readback contradicts requested body")
            return receipt
        if operation == GET_CHECKS_AND_POLICIES:
            expected_head = str(parameters.get("expected_head", ""))
            if not pr_id or not expected_head:
                raise ProviderError(
                    "get-checks-and-policies requires PR and expected head"
                )
            document = self._json(
                [
                    "gh",
                    "pr",
                    "view",
                    pr_id,
                    "--json",
                    "number,headRefOid,baseRefName,mergeStateStatus,"
                    "statusCheckRollup",
                ]
            )
            if not isinstance(document, dict):
                raise ProviderError("GitHub checks readback must be an object")
            observed_head = document.get("headRefOid")
            base = document.get("baseRefName")
            rollup = document.get("statusCheckRollup")
            if observed_head != expected_head:
                raise ProviderError(
                    "GitHub checks readback belongs to a different PR head"
                )
            if not isinstance(base, str) or not base:
                raise ProviderError("GitHub checks readback omitted base branch")
            if not isinstance(rollup, list):
                raise ProviderError("GitHub checks readback omitted status rollup")
            rules, rules_observation = self._github_active_rules(base)
            checks = [self._github_check_item(item) for item in rollup]
            observed_names = {item["name"] for item in checks}
            for rule in rules:
                if rule["type"] != "required_status_checks":
                    continue
                rule_parameters = rule.get("parameters", {})
                required = (
                    rule_parameters.get("required_status_checks", [])
                    if isinstance(rule_parameters, dict)
                    else []
                )
                if not isinstance(required, list):
                    raise ProviderError(
                        "GitHub required status-check policy is malformed"
                    )
                for required_check in required:
                    context = (
                        required_check.get("context")
                        if isinstance(required_check, dict)
                        else None
                    )
                    if not isinstance(context, str) or not context:
                        raise ProviderError(
                            "GitHub required status-check context is malformed"
                        )
                    if context not in observed_names:
                        checks.append(
                            {
                                "bucket": "pending",
                                "name": context,
                                "state": "EXPECTED",
                                "workflow": "",
                            }
                        )
            active_rules = [
                {
                    "type": rule["type"],
                    "ruleset_id": rule.get("ruleset_id"),
                    "source_type": rule.get("ruleset_source_type"),
                    "source": rule.get("ruleset_source"),
                }
                for rule in rules
            ]
            return {
                "schema": 1,
                "provider": "github",
                "operation": operation,
                "evidence_class": "live",
                "observed": True,
                "pr_id": pr_id,
                "head_sha": observed_head,
                "base": base,
                "merge_state_status": document.get("mergeStateStatus"),
                "checks_and_policies": checks,
                "active_rules": active_rules,
                "rules_observation": rules_observation,
                "merge_mode": (
                    "queue"
                    if any(rule["type"] == "merge_queue" for rule in rules)
                    else "direct"
                ),
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
        if operation == MERGE_WITH_EXPECTED_HEAD:
            expected_head = str(parameters.get("expected_head", ""))
            intent_key = str(parameters.get("intent_key", ""))
            previous_attempt_mode = parameters.get("previous_attempt_mode")
            if previous_attempt_mode not in {None, "direct", "queue"}:
                raise ProviderError("previous merge attempt mode is invalid")
            mutation_previously_applied = (
                parameters.get("mutation_previously_applied") is True
            )
            queue_dispatch_ambiguous = (
                parameters.get("queue_dispatch_ambiguous") is True
            )
            authorization = parameters.get("authorization")
            if (
                not pr_id
                or not expected_head
                or not intent_key
                or not isinstance(authorization, MergeAuthorization)
            ):
                raise ProviderError(
                    "merge-with-expected-head requires PR, head, intent, and authorization"
                )
            self.provider._validate_authorization(
                pr_id, expected_head, authorization
            )
            pull_request_id, rules, rules_observation = self._github_merge_context(
                pr_id, expected_head
            )
            current_merge_mode = (
                "queue"
                if any(rule["type"] == "merge_queue" for rule in rules)
                else "direct"
            )
            if (
                previous_attempt_mode is not None
                and previous_attempt_mode != current_merge_mode
            ):
                raise ProviderError(
                    f"previously attempted {previous_attempt_mode} merge policy changed "
                    f"to {current_merge_mode}; refusing provider fallback"
                )
            if current_merge_mode == "queue":
                queue_entry = self._github_queue_readback(
                    pull_request_id, expected_head
                )
                replayed = queue_entry is not None
                recovered_after_error = False
                if queue_entry is None and mutation_previously_applied:
                    raise ProviderError(
                        "previously applied queue entry is no longer observable; "
                        "refusing a second provider mutation"
                    )
                if queue_entry is None and queue_dispatch_ambiguous:
                    raise ProviderError(
                        "persisted queue attempt has no durable mutation receipt or "
                        "observable queue entry; refusing a second provider mutation"
                    )
                if queue_entry is None:
                    command = [
                        "gh",
                        "api",
                        "graphql",
                        "-f",
                        f"query={GITHUB_QUEUE_MUTATION}",
                        "-f",
                        f"pullRequestId={pull_request_id}",
                        "-f",
                        f"expectedHeadOid={expected_head}",
                        "-f",
                        f"clientMutationId={intent_key}",
                    ]
                    result = self.runner.run(command, cwd=self.cwd)
                    applied_entry: dict[str, Any] | None = None
                    response_intent: Any = None
                    if not result.returncode:
                        try:
                            document = json.loads(result.stdout)
                        except json.JSONDecodeError:
                            document = None
                        payload = (
                            document.get("data", {}).get("enqueuePullRequest")
                            if isinstance(document, dict)
                            and isinstance(document.get("data"), dict)
                            else None
                        )
                        if isinstance(payload, dict):
                            response_intent = payload.get("clientMutationId")
                            if response_intent == intent_key:
                                applied_entry = self._github_queue_entry(
                                    payload.get("mergeQueueEntry")
                                )
                    queue_entry = self._github_queue_readback(
                        pull_request_id, expected_head
                    )
                    if queue_entry is None:
                        detail = (
                            result.stderr
                            or result.stdout
                            or "provider command failed"
                        )
                        if result.returncode:
                            raise ProviderError(
                                f"{' '.join(command)} failed: {detail}"
                            )
                        raise ProviderError(
                            "GitHub merge-queue readback did not confirm the mutation"
                        )
                    if (
                        isinstance(response_intent, str)
                        and response_intent
                        and response_intent != intent_key
                    ):
                        raise ProviderError(
                            "GitHub merge-queue mutation lost its intent binding"
                        )
                    if (
                        applied_entry is not None
                        and applied_entry["id"] != queue_entry["id"]
                    ):
                        raise ProviderError(
                            "GitHub merge-queue readback did not confirm the mutation"
                        )
                    recovered_after_error = (
                        result.returncode != 0 or applied_entry is None
                    )
                return {
                    "schema": 1,
                    "provider": "github",
                    "operation": operation,
                    "evidence_class": "live",
                    "observed": True,
                    "pr_id": pr_id,
                    "head_sha": expected_head,
                    "intent_key": intent_key,
                    "merge_mode": "queue",
                    "rules_observation": rules_observation,
                    "queue_entry": queue_entry,
                    "replayed": replayed,
                    "recovered_after_error": recovered_after_error,
                    "state": "queue-entry-observed",
                }
            self._run(
                self.provider.merge_command(
                    pr_id, expected_head, authorization
                )
            )
            return {
                "schema": 1,
                "provider": "github",
                "operation": operation,
                "evidence_class": "live",
                "observed": True,
                "pr_id": pr_id,
                "head_sha": expected_head,
                "intent_key": intent_key,
                "merge_mode": "direct",
                "rules_observation": rules_observation,
                "replayed": False,
                "state": "merge-command-accepted",
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
        body = document.get("description")
        if not isinstance(body, str):
            raise ProviderError("Azure DevOps readback omitted PR body")
        merge_commit_document = document.get("lastMergeCommit")
        merge_commit_sha = (
            merge_commit_document.get("commitId")
            if isinstance(merge_commit_document, dict)
            else None
        )
        if merge_commit_sha is not None and (
            not isinstance(merge_commit_sha, str) or not merge_commit_sha
        ):
            raise ProviderError(
                "Azure DevOps readback returned a malformed merge commit"
            )
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
            "merge_commit_sha": merge_commit_sha,
            "body": body,
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
                        *_azure_description_arguments(body),
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
                        *_azure_description_arguments(body),
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
        elif (
            parent["state"] == "pr-open"
            or (
                parent["state"] == "gated"
                and any(
                    gate.get("ticket_id") == parent_id
                    and gate.get("category") == "provider-merge"
                    and gate.get("state") == "open"
                    for gate in ledger["gates"].values()
                )
            )
        ) and parent.get("pr", {}).get("branch"):
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
