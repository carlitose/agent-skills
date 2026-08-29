from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "ticket-autopilot" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.cli import main
from autopilot.git_ops import CommandResult, SubprocessCommandRunner
from autopilot.providers import (
    GET_REPOSITORY,
    GET_REPOSITORY_BRANCH,
    GitHubProvider,
    ProviderError,
    ProviderExecutor,
)
from autopilot.repository_bootstrap import (
    BootstrapRequest,
    BootstrapStateStore,
    GitLocalBootstrap,
    LocalRepository,
    RepositoryBootstrapError,
    RepositoryBootstrapTransaction,
    _append_event,
    _digest,
    normalized_github_remote,
)


SHA = "a" * 40
TARGET = "owner/project"


def request(root: Path, *, branch: str = "main", actor: str = "alice", evidence: str = "artifact://bootstrap") -> BootstrapRequest:
    return BootstrapRequest.normalize(
        repository=str(root),
        target=TARGET,
        visibility="private",
        base_branch=branch,
        base_sha=SHA,
        actor=actor,
        evidence=evidence,
    )


def repository_receipt(*, default: str | None = "main", private: bool = True) -> dict[str, object]:
    return {
        "state": "present",
        "target": TARGET,
        "private": private,
        "visibility": "private" if private else "public",
        "default_branch": default,
        "clone_url": f"https://github.com/{TARGET}.git",
        "ssh_url": f"git@github.com:{TARGET}.git",
        "size": 0,
    }


class FakeLocal:
    def __init__(self, root: Path):
        self.repository = LocalRepository(root, root / ".git", "main", SHA)
        self.repository.common_git_dir.mkdir()
        self.origins: tuple[str, ...] = ()
        self.adds = 0
        self.pushes = 0
        self.on_push = None

    @property
    def state_path(self) -> Path:
        return BootstrapStateStore(self.repository.common_git_dir).path

    def _intent_exists(self) -> None:
        self.assertion = self.state_path.is_file()
        if not self.assertion:
            raise AssertionError("mutation occurred before intent persistence")

    def inspect(self, value: BootstrapRequest) -> LocalRepository:
        if value.repository != self.repository.root or value.base_sha != self.repository.base_sha:
            raise RepositoryBootstrapError("local repository contradiction")
        return LocalRepository(
            self.repository.root,
            self.repository.common_git_dir,
            value.base_branch,
            self.repository.base_sha,
        )

    def origin_urls(self, repository: LocalRepository) -> tuple[str, ...]:
        return self.origins

    def add_origin(self, repository: LocalRepository, url: str) -> None:
        self._intent_exists()
        self.adds += 1
        self.origins = (url,)

    def push_base(self, repository: LocalRepository, branch: str, sha: str) -> None:
        self._intent_exists()
        self.pushes += 1
        if self.on_push:
            self.on_push(branch, sha)


class FakeGitHub:
    def __init__(self, local: FakeLocal, *, present: bool = False, default: str | None = "main"):
        self.local = local
        self.repository = repository_receipt(default=default) if present else None
        self.branches: dict[str, str] = {}
        self.creates = 0
        self.default_updates = 0
        local.on_push = self._pushed

    def _intent_exists(self) -> None:
        if not self.local.state_path.is_file():
            raise AssertionError("provider mutation occurred before intent persistence")

    def _pushed(self, branch: str, sha: str) -> None:
        self.branches[branch] = sha
        if self.repository and not self.repository.get("default_branch"):
            self.repository["default_branch"] = branch

    def get_repository(self, target: str) -> dict[str, object]:
        return dict(self.repository) if self.repository else {"state": "absent", "target": target}

    def create_private_repository(self, target: str) -> dict[str, object]:
        self._intent_exists()
        self.creates += 1
        self.repository = repository_receipt(default="main")
        return dict(self.repository)

    def get_branch(self, target: str, branch: str) -> dict[str, object]:
        sha = self.branches.get(branch)
        if sha is None:
            return {"state": "absent", "target": target, "branch": branch}
        return {"state": "present", "target": target, "branch": branch, "sha": sha}

    def set_default_branch(self, target: str, branch: str) -> dict[str, object]:
        self._intent_exists()
        if branch not in self.branches:
            raise AssertionError("default branch set before publication")
        self.default_updates += 1
        assert self.repository is not None
        self.repository["default_branch"] = branch
        return dict(self.repository)


class CrashOnce:
    def __init__(self, stage: str):
        self.stage = stage
        self.fired = False

    def __call__(self, stage: str) -> None:
        if stage == self.stage and not self.fired:
            self.fired = True
            raise RuntimeError(f"crash at {stage}")


class RequestTests(unittest.TestCase):
    def test_request_requires_absolute_private_bound_inputs(self) -> None:
        with self.assertRaisesRegex(RepositoryBootstrapError, "absolute"):
            BootstrapRequest.normalize(
                repository=".", target=TARGET, visibility="private", base_branch="main",
                base_sha=SHA, actor="alice", evidence="artifact://bootstrap",
            )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for changed, message in (
                ({"target": "missing-slash"}, "OWNER/REPOSITORY"),
                ({"visibility": "public"}, "private visibility only"),
                ({"base_sha": "abc"}, "exact Git object ID"),
                ({"actor": ""}, "actor and evidence"),
            ):
                values = dict(repository=str(root), target=TARGET, visibility="private", base_branch="main", base_sha=SHA, actor="alice", evidence="artifact://bootstrap")
                values.update(changed)
                with self.subTest(changed=changed), self.assertRaisesRegex(RepositoryBootstrapError, message):
                    BootstrapRequest.normalize(**values)

    def test_local_origin_observation_includes_distinct_push_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            subprocess.run(["git", "init", "-b", "main", str(root)], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(root), "remote", "add", "origin", f"https://github.com/{TARGET}.git"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "remote", "set-url", "--add", "--push", "origin", "https://github.com/other/project.git"],
                check=True,
            )
            observed = GitLocalBootstrap().origin_urls(
                LocalRepository(root, root / ".git", "main", SHA)
            )

        self.assertEqual(
            {f"https://github.com/{TARGET}.git", "https://github.com/other/project.git"},
            set(observed),
        )

    def test_remote_equivalence_is_strict_to_one_github_identity(self) -> None:
        expected = "github.com/owner/project"
        for url in (
            "https://github.com/Owner/Project.git",
            "git@github.com:owner/project.git",
            "ssh://git@github.com/owner/project.git",
        ):
            with self.subTest(url=url):
                self.assertEqual(expected, normalized_github_remote(url))
        for url in (
            "https://example.com/owner/project.git",
            "https://token@github.com/owner/project.git",
            "https://github.com:8443/owner/project.git",
            "ssh://git@github.com:2222/owner/project.git",
            "https://[github.com/owner/project.git",
            "git@github.com:other/project.git?x=1",
        ):
            with self.subTest(url=url), self.assertRaises(RepositoryBootstrapError):
                normalized_github_remote(url)


class TransactionTests(unittest.TestCase):
    def fixture(self, *, present: bool = False, default: str | None = "main"):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name).resolve()
        local = FakeLocal(root)
        provider = FakeGitHub(local, present=present, default=default)
        return temporary, local, provider

    def test_create_publish_complete_and_exact_replay_emit_no_second_mutation(self) -> None:
        temporary, local, provider = self.fixture()
        with temporary:
            transaction = RepositoryBootstrapTransaction(local, provider)
            first = transaction.apply(request(local.repository.root))
            counts = (provider.creates, local.adds, local.pushes, provider.default_updates)
            state_bytes = local.state_path.read_bytes()
            second = transaction.apply(request(local.repository.root))

            self.assertEqual((1, 1, 1, 0), counts)
            self.assertEqual(counts, (provider.creates, local.adds, local.pushes, provider.default_updates))
            self.assertFalse(first["replayed"])
            self.assertTrue(second["replayed"])
            self.assertEqual(first["receipt"], second["receipt"])
            self.assertEqual(
                {
                    "repository": TARGET,
                    "visibility": "private",
                    "base_branch": "main",
                    "local_sha": SHA,
                    "remote_sha": SHA,
                    "actor": "alice",
                    "evidence": "artifact://bootstrap",
                    "observed_default_branch": "main",
                },
                {key: first["receipt"][key] for key in (
                    "repository", "visibility", "base_branch", "local_sha",
                    "remote_sha", "actor", "evidence", "observed_default_branch",
                )},
            )
            self.assertEqual(state_bytes, local.state_path.read_bytes())
            self.assertEqual(first["history_events"], second["history_events"])
            self.assertEqual("bootstrap-only-no-delivery-merge-or-wiki-sync", first["receipt"]["authority_scope"])

    def test_completed_receipt_never_authorizes_repairing_later_drift(self) -> None:
        for drift in ("origin", "repository", "branch", "default"):
            temporary, local, provider = self.fixture()
            with temporary, self.subTest(drift=drift):
                value = request(local.repository.root)
                transaction = RepositoryBootstrapTransaction(local, provider)
                transaction.apply(value)
                before = (provider.creates, local.adds, local.pushes, provider.default_updates)
                if drift == "origin":
                    local.origins = ()
                elif drift == "repository":
                    provider.repository = None
                elif drift == "branch":
                    provider.branches.clear()
                else:
                    assert provider.repository is not None
                    provider.repository["default_branch"] = "release"
                with self.assertRaises(RepositoryBootstrapError):
                    transaction.apply(value)
                self.assertEqual(
                    before,
                    (provider.creates, local.adds, local.pushes, provider.default_updates),
                )

    def test_matching_existing_empty_or_exact_repository_is_adopted(self) -> None:
        for exact in (False, True):
            temporary, local, provider = self.fixture(present=True)
            with temporary, self.subTest(exact=exact):
                local.origins = (f"git@github.com:{TARGET}.git",)
                if exact:
                    provider.branches["main"] = SHA
                result = RepositoryBootstrapTransaction(local, provider).apply(request(local.repository.root))

                self.assertEqual(0, provider.creates)
                self.assertEqual(0, local.adds)
                self.assertEqual(0 if exact else 1, local.pushes)
                self.assertEqual(SHA, result["receipt"]["remote_sha"])

    def test_conflicts_fail_without_mutation(self) -> None:
        cases = ("origin", "visibility", "url", "base", "nonempty", "default")
        for case in cases:
            temporary, local, provider = self.fixture(present=True)
            with temporary, self.subTest(case=case):
                if case == "origin":
                    local.origins = ("https://github.com/other/project.git",)
                elif case == "visibility":
                    provider.repository = repository_receipt(private=False)
                elif case == "url":
                    assert provider.repository is not None
                    provider.repository["clone_url"] = "https://github.com/other/project.git"
                elif case == "base":
                    provider.branches["main"] = "b" * 40
                elif case == "nonempty":
                    assert provider.repository is not None
                    provider.repository["size"] = 1
                else:
                    assert provider.repository is not None
                    provider.repository["default_branch"] = "release"
                    provider.branches["release"] = "b" * 40
                with self.assertRaises(RepositoryBootstrapError):
                    RepositoryBootstrapTransaction(local, provider).apply(request(local.repository.root))
                self.assertEqual((0, 0, 0, 0), (provider.creates, local.adds, local.pushes, provider.default_updates))

    def test_intent_identity_visibility_branch_actor_and_evidence_are_immutable(self) -> None:
        temporary, local, provider = self.fixture()
        with temporary:
            original = request(local.repository.root)
            RepositoryBootstrapTransaction(local, provider).apply(original)
            for changed in (
                replace(original, target="other/project"),
                replace(original, visibility="public"),
                replace(original, base_branch="trunk"),
                replace(original, actor="bob"),
                replace(original, evidence="artifact://other"),
            ):
                with self.assertRaisesRegex(RepositoryBootstrapError, "immutable"):
                    RepositoryBootstrapTransaction(local, provider).apply(changed)

    def test_every_crash_boundary_recovers_without_duplicate_mutation(self) -> None:
        for stage in (
            "pre-create",
            "post-create",
            "post-origin",
            "post-push",
            "post-default-branch",
            "post-readback",
        ):
            temporary, local, provider = self.fixture()
            with temporary, self.subTest(stage=stage):
                value = request(local.repository.root, branch="trunk")
                crashing = RepositoryBootstrapTransaction(local, provider, fault=CrashOnce(stage))
                with self.assertRaisesRegex(RuntimeError, "crash at"):
                    crashing.apply(value)
                after_crash = (provider.creates, local.adds, local.pushes, provider.default_updates)
                result = RepositoryBootstrapTransaction(local, provider).apply(value)
                after_replay = (provider.creates, local.adds, local.pushes, provider.default_updates)

                self.assertEqual("completed", result["receipt"]["status"])
                self.assertEqual((1, 1, 1, 1), after_replay)
                self.assertTrue(all(after_replay[i] >= after_crash[i] for i in range(4)))

    def test_symlinked_state_directory_is_rejected_before_mutation(self) -> None:
        temporary, local, provider = self.fixture()
        with temporary:
            outside = local.repository.root / "outside"
            outside.mkdir()
            local.state_path.parent.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RepositoryBootstrapError, "symbolic links"):
                RepositoryBootstrapTransaction(local, provider).apply(request(local.repository.root))
            self.assertEqual(0, provider.creates)

    def test_integrity_and_completion_history_corruption_are_rejected(self) -> None:
        temporary, local, provider = self.fixture()
        with temporary:
            value = request(local.repository.root)
            RepositoryBootstrapTransaction(local, provider).apply(value)
            original = local.state_path.read_text()
            document = json.loads(original)
            document["payload"]["intent"]["actor"] = "mallory"
            local.state_path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(RepositoryBootstrapError, "integrity"):
                RepositoryBootstrapTransaction(local, provider).apply(value)

            document = json.loads(original)
            _append_event(document["payload"], "origin-observed", {"state": "late"})
            document["integrity"] = _digest(document["payload"])
            local.state_path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(RepositoryBootstrapError, "receipt"):
                RepositoryBootstrapTransaction(local, provider).apply(value)


class StaticRunner:
    def __init__(self, result: CommandResult):
        self.result = result

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        return self.result


class ProviderOperationTests(unittest.TestCase):
    def test_exact_404_is_absent_but_generic_provider_failure_remains_fatal(self) -> None:
        executor = ProviderExecutor(
            GitHubProvider(), cwd=Path.cwd(), runner=StaticRunner(
                CommandResult("", "gh: Not Found (HTTP 404)", 1)
            )
        )
        self.assertEqual(
            "absent", executor.execute(GET_REPOSITORY, target=TARGET)["state"]
        )

        generic = ProviderExecutor(
            GitHubProvider(), cwd=Path.cwd(), runner=StaticRunner(
                CommandResult("", "gh: forbidden (HTTP 403)", 1)
            )
        )
        with self.assertRaises(ProviderError):
            generic.execute(GET_REPOSITORY, target=TARGET)

    def test_exact_empty_repository_409_is_an_absent_branch_only(self) -> None:
        result = CommandResult("", "gh: Git Repository is empty. (HTTP 409)", 1)
        branch = ProviderExecutor(
            GitHubProvider(), cwd=Path.cwd(), runner=StaticRunner(result)
        )
        self.assertEqual(
            "absent",
            branch.execute(
                GET_REPOSITORY_BRANCH, target=TARGET, branch="main"
            )["state"],
        )

        repository = ProviderExecutor(
            GitHubProvider(), cwd=Path.cwd(), runner=StaticRunner(result)
        )
        with self.assertRaises(ProviderError):
            repository.execute(GET_REPOSITORY, target=TARGET)


class GitHubCommandRunner:
    """Use real local Git and an in-memory GitHub command boundary."""

    def __init__(self):
        self.git = SubprocessCommandRunner()
        self.repository = None
        self.branches: dict[str, str] = {}
        self.commands: list[tuple[str, ...]] = []

    def _result(self, value: object) -> CommandResult:
        return CommandResult(json.dumps(value), "", 0)

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(tuple(command))
        if command[:2] == ["git", "push"]:
            sha, ref = command[-1].split(":", 1)
            self.branches[ref.removeprefix("refs/heads/")] = sha
            return CommandResult("", "", 0)
        if command[:2] == ["gh", "api"]:
            endpoints = [
                value for value in command[2:]
                if value == "user" or value == "user/repos"
                or value.startswith("repos/") or value.startswith("orgs/")
            ]
            endpoint = endpoints[0]
            if endpoint == "user":
                return self._result({"login": "owner"})
            if "--method" in command and command[command.index("--method") + 1] == "POST":
                self.repository = {
                    "full_name": TARGET,
                    "private": True,
                    "visibility": "private",
                    "default_branch": "main",
                    "clone_url": f"https://github.com/{TARGET}.git",
                    "ssh_url": f"git@github.com:{TARGET}.git",
                    "size": 0,
                }
                return self._result(self.repository)
            if "/git/ref/heads/" in endpoint:
                branch = endpoint.rsplit("/", 1)[-1]
                if branch not in self.branches:
                    return CommandResult("", "gh: Not Found (HTTP 404)", 1)
                return self._result({"ref": f"refs/heads/{branch}", "object": {"sha": self.branches[branch]}})
            if "--method" in command:
                branch = next(value.split("=", 1)[1] for value in command if value.startswith("default_branch="))
                assert self.repository is not None
                self.repository["default_branch"] = branch
                return self._result(self.repository)
            if self.repository is None:
                return CommandResult("", "gh: Not Found (HTTP 404)", 1)
            return self._result(self.repository)
        return self.git.run(command, cwd=cwd)


class CliIntegrationTests(unittest.TestCase):
    def test_cli_creates_private_repository_adds_origin_and_pushes_exact_sha(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            subprocess.run(["git", "init", "-b", "main", str(root)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            (root / "README.md").write_text("# Test\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-m", "initial"], check=True, capture_output=True)
            sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
            runner = GitHubCommandRunner()
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(
                    [
                        "bootstrap-private-github", "--repo", str(root), "--target", TARGET,
                        "--visibility", "private", "--base", "main", "--base-sha", sha,
                        "--actor", "alice", "--evidence", "artifact://bootstrap",
                    ],
                    command_runner=runner,
                )
            response = json.loads(output.getvalue())

            self.assertEqual(0, code, response)
            self.assertTrue(response["ok"])
            self.assertEqual(sha, response["data"]["receipt"]["remote_sha"])
            origin = subprocess.check_output(["git", "-C", str(root), "remote", "get-url", "origin"], text=True).strip()
            self.assertEqual(f"https://github.com/{TARGET}.git", origin)
            creates = [
                command for command in runner.commands
                if command[:2] == ("gh", "api")
                and "POST" in command
                and "private=true" in command
            ]
            self.assertEqual(1, len(creates))
            self.assertIn("--hostname", creates[0])
            self.assertIn("github.com", creates[0])
            pushes = [command for command in runner.commands if command[:2] == ("git", "push")]
            self.assertEqual([("git", "push", "origin", f"{sha}:refs/heads/main")], pushes)
            self.assertFalse(any("--force" in argument for command in pushes for argument in command))
            for command in runner.commands:
                if command[:2] == ("gh", "api"):
                    self.assertIn("--hostname", command)
                    self.assertIn("github.com", command)
            command_text = "\n".join(" ".join(command) for command in runner.commands).casefold()
            for forbidden in ("gh pr", "gh repo delete", "visibility=", "wiki-sync"):
                self.assertNotIn(forbidden, command_text)


if __name__ == "__main__":
    unittest.main()
