from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "ticket-autopilot" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.cli import main
from autopilot.git_ops import CommandResult, SubprocessCommandRunner
from autopilot.repository_bootstrap import BootstrapRequest, RepositoryBootstrapError
from autopilot.zero_to_autopilot import (
    STATE_RELATIVE_PATH,
    ZeroBootstrapRequest,
    ZeroToAutopilotError,
    ZeroToAutopilotTransaction,
    assert_inventory_current,
    inspect_zero_to_autopilot,
    load_inventory,
    prepare_inventory,
)


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


class GuardedRunner:
    def __init__(self, root: Path):
        self.root = root
        self.delegate = SubprocessCommandRunner()
        self.commands: list[tuple[str, ...]] = []

    @property
    def state_path(self) -> Path:
        return self.root / ".git" / STATE_RELATIVE_PATH

    def run(self, command: list[str], *, cwd: Path) -> CommandResult:
        self.commands.append(tuple(command))
        mutating = (
            command[:2]
            in (
                ["git", "init"],
                ["git", "read-tree"],
                ["git", "add"],
                ["git", "hash-object"],
                ["git", "update-index"],
            )
            or "commit" in command
        )
        if mutating and not self.state_path.is_file():
            raise AssertionError(f"mutation preceded persisted intent: {command}")
        return self.delegate.run(command, cwd=cwd)


class FakePrivateBootstrap:
    def __init__(self, root: Path):
        self.root = root
        self.calls = 0
        self.completed = False
        self.request: BootstrapRequest | None = None

    def __call__(self, request: BootstrapRequest) -> dict[str, object]:
        common_raw = Path(git(self.root, "rev-parse", "--git-common-dir"))
        common = common_raw if common_raw.is_absolute() else self.root / common_raw
        state_path = common.resolve() / STATE_RELATIVE_PATH
        if not state_path.is_file():
            raise AssertionError("provider bootstrap preceded zero-bootstrap intent")
        self.calls += 1
        if self.request is not None and request != self.request:
            raise RepositoryBootstrapError("nested bootstrap request changed")
        self.request = request
        remotes = git(self.root, "remote").splitlines()
        if self.completed and "origin" not in remotes:
            raise RepositoryBootstrapError("completed bootstrap origin is now absent")
        if "origin" not in remotes:
            git(
                self.root,
                "remote",
                "add",
                "origin",
                f"https://github.com/{request.target}.git",
            )
        self.completed = True
        return {
            "receipt": {
                "schema": 1,
                "status": "completed",
                "repository": request.target,
                "visibility": "private",
                "local_repository": self.root.as_posix(),
                "git_common_dir": (self.root / ".git").as_posix(),
                "normalized_remote": f"github.com/{request.target}",
                "base_branch": request.base_branch,
                "local_sha": request.base_sha,
                "remote_sha": request.base_sha,
                "actor": request.actor,
                "evidence": request.evidence,
                "observed_default_branch": request.base_branch,
                "evidence_class": "live",
                "authority_scope": "bootstrap-only-no-delivery-merge-or-wiki-sync",
            }
        }


class CrashOnce:
    def __init__(self, stage: str):
        self.stage = stage
        self.fired = False

    def __call__(self, stage: str) -> None:
        if stage == self.stage and not self.fired:
            self.fired = True
            raise RuntimeError(f"crash at {stage}")


class ZeroBootstrapFixture(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temporary = tempfile.TemporaryDirectory()
        parent = Path(temporary.name).resolve()
        root = parent / "project"
        root.mkdir()
        manifest = parent / "inventory.json"
        return temporary, root, manifest

    def prepare(
        self,
        root: Path,
        manifest: Path,
        *,
        excludes: tuple[str, ...] = (),
    ) -> dict[str, object]:
        return prepare_inventory(
            repository=root.as_posix(),
            target="owner/project",
            visibility="private",
            base_branch="main",
            output=manifest.as_posix(),
            excludes=excludes,
        )

    def request(
        self,
        root: Path,
        manifest: Path,
        prepared: dict[str, object],
        *,
        actor: str = "alice",
        evidence: str = "decision://exact-inventory",
        base_sha: str | None = None,
    ) -> ZeroBootstrapRequest:
        return ZeroBootstrapRequest.normalize(
            repository=root.as_posix(),
            target="owner/project",
            visibility="private",
            base_branch="main",
            inventory_path=manifest.as_posix(),
            inventory_sha256=str(prepared["inventory_sha256"]),
            actor=actor,
            evidence=evidence,
            base_sha=base_sha,
        )


class InventoryTests(ZeroBootstrapFixture):
    def test_prepare_is_canonical_complete_and_risky_files_are_excluded(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "README.md").write_text("safe\n", encoding="utf-8")
            script = root / "run.sh"
            script.write_text("#!/bin/sh\n", encoding="utf-8")
            script.chmod(0o755)
            (root / ".env").write_text("TOKEN=fixture\n", encoding="utf-8")
            (root / "notes.txt").write_text("private\n", encoding="utf-8")
            result = self.prepare(root, manifest, excludes=("notes.txt",))
            request = self.request(root, manifest, result)
            value = load_inventory(request)

            self.assertEqual("inventory-prepared", result["status"])
            self.assertEqual(4, result["file_count"])
            dispositions = {item["path"]: item["disposition"] for item in value["entries"]}
            self.assertEqual(
                {".env": "exclude", "README.md": "publish", "notes.txt": "exclude", "run.sh": "publish"},
                dispositions,
            )
            modes = {item["path"]: item["mode"] for item in value["entries"]}
            self.assertEqual("100755", modes["run.sh"])
            self.assertEqual("100644", modes["README.md"])
            self.assertTrue(value["entries"][0]["findings"])
            self.assertEqual(
                result["inventory_sha256"],
                hashlib.sha256(manifest.read_bytes()).hexdigest(),
            )

    def test_inventory_drift_digest_and_output_inside_root_fail_closed(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            prepared = self.prepare(root, manifest)
            request = self.request(root, manifest, prepared)
            (root / "a.txt").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ZeroToAutopilotError, "drifted"):
                assert_inventory_current(load_inventory(request))
            with self.assertRaisesRegex(ZeroToAutopilotError, "outside"):
                prepare_inventory(
                    repository=root.as_posix(),
                    target="owner/project",
                    visibility="private",
                    base_branch="main",
                    output=(root / "inventory.json").as_posix(),
                )
            with self.assertRaisesRegex(ZeroToAutopilotError, "SHA-256"):
                load_inventory(
                    ZeroBootstrapRequest.normalize(
                        repository=root.as_posix(), target="owner/project", visibility="private",
                        base_branch="main", inventory_path=manifest.as_posix(),
                        inventory_sha256="0" * 64, actor="alice", evidence="decision://x",
                    )
                )

    def test_forged_risky_publish_reports_exact_path_and_finding(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / ".env").write_text("TOKEN=fixture\n", encoding="utf-8")
            self.prepare(root, manifest)
            document = json.loads(manifest.read_text(encoding="utf-8"))
            entry = next(item for item in document["entries"] if item["path"] == ".env")
            entry["disposition"] = "publish"
            entry["findings"] = []
            content = json.dumps(
                document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8") + b"\n"
            manifest.write_bytes(content)
            request = ZeroBootstrapRequest.normalize(
                repository=root.as_posix(),
                target="owner/project",
                visibility="private",
                base_branch="main",
                inventory_path=manifest.as_posix(),
                inventory_sha256=hashlib.sha256(content).hexdigest(),
                actor="alice",
                evidence="decision://forged-risk",
            )
            with self.assertRaisesRegex(
                ZeroToAutopilotError,
                r"\.env; findings=credential-bearing-name",
            ):
                ZeroToAutopilotTransaction(
                    bootstrap=FakePrivateBootstrap(root)
                ).apply(request)
            self.assertFalse((root / ".git").exists())

    def test_symlink_nested_git_special_file_and_unknown_exclude_are_rejected(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            target = root / "target.txt"
            target.write_text("x", encoding="utf-8")
            (root / "link.txt").symlink_to(target)
            with self.assertRaisesRegex(ZeroToAutopilotError, "symbolic links"):
                self.prepare(root, manifest)
            (root / "link.txt").unlink()
            nested = root / "nested" / ".git"
            nested.mkdir(parents=True)
            with self.assertRaisesRegex(ZeroToAutopilotError, "nested Git"):
                self.prepare(root, manifest)
            (root / "nested" / ".git").rmdir()
            if hasattr(os, "mkfifo"):
                fifo = root / "pipe"
                os.mkfifo(fifo)
                with self.assertRaisesRegex(ZeroToAutopilotError, "special files"):
                    self.prepare(root, manifest)
                fifo.unlink()
            with self.assertRaisesRegex(ZeroToAutopilotError, "absent"):
                self.prepare(root, manifest, excludes=("missing.txt",))
            reserved = root / "CON.txt"
            reserved.write_text("unsafe\n", encoding="utf-8")
            with self.assertRaisesRegex(ZeroToAutopilotError, "unsafe"):
                self.prepare(root, manifest)
            reserved.unlink()
            external_git = root.parent / "external-git"
            external_git.mkdir()
            (root / ".git").symlink_to(external_git, target_is_directory=True)
            with self.assertRaisesRegex(ZeroToAutopilotError, "symbolic link"):
                self.prepare(root, manifest)


class TransactionTests(ZeroBootstrapFixture):
    def test_non_git_directory_persists_intent_builds_exact_tree_and_replays(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "README.md").write_text("hello\n", encoding="utf-8")
            (root / ".env").write_text("TOKEN=fixture\n", encoding="utf-8")
            prepared = self.prepare(root, manifest)
            request = self.request(root, manifest, prepared)
            runner = GuardedRunner(root)
            bootstrap = FakePrivateBootstrap(root)
            transaction = ZeroToAutopilotTransaction(runner, bootstrap=bootstrap)

            first = transaction.apply(request)
            head = git(root, "rev-parse", "HEAD")
            tree_paths = git(root, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
            commit_line = git(root, "rev-list", "--parents", "-n", "1", "HEAD").split()
            command_count = len(runner.commands)
            second = transaction.apply(request)

            self.assertEqual("repository-ready-for-ticket-autopilot", first["receipt"]["status"])
            self.assertEqual("initialized", first["receipt"]["local_mode"])
            self.assertEqual(["README.md"], tree_paths)
            self.assertEqual([head], commit_line)
            self.assertEqual(head, first["receipt"]["base_sha"])
            self.assertTrue(second["replayed"])
            self.assertEqual(first["receipt"], second["receipt"])
            self.assertEqual(2, bootstrap.calls)
            self.assertFalse(any(command[:3] == ("git", "add", "-A") for command in runner.commands))
            self.assertEqual(1, sum(command[:2] == ("git", "init") for command in runner.commands))
            self.assertGreater(len(runner.commands), command_count)

    def test_initial_tree_ignores_ambient_filters_hooks_and_object_format(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            parent = root.parent
            home = parent / "home"
            hooks = parent / "hooks"
            home.mkdir()
            hooks.mkdir()
            marker = parent / "hook-fired"
            hook = hooks / "post-commit"
            hook.write_text(f"#!/bin/sh\ntouch {marker}\n", encoding="utf-8")
            hook.chmod(0o755)
            (home / ".gitconfig").write_text(
                "[core]\n\tautocrlf = true\n\thooksPath = "
                + hooks.as_posix()
                + "\n[init]\n\tdefaultObjectFormat = sha256\n",
                encoding="utf-8",
            )
            content = b"line-one\r\nline-two\r\n"
            (root / "raw.txt").write_bytes(content)
            prepared = self.prepare(root, manifest)
            request = self.request(root, manifest, prepared)
            environment = {
                "HOME": home.as_posix(),
                "XDG_CONFIG_HOME": (parent / "xdg").as_posix(),
            }

            with patch.dict(os.environ, environment):
                result = ZeroToAutopilotTransaction(
                    bootstrap=FakePrivateBootstrap(root)
                ).apply(request)
                observed = subprocess.run(
                    ["git", "show", "HEAD:raw.txt"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                ).stdout
                object_format = git(root, "rev-parse", "--show-object-format")

            self.assertEqual(content, observed)
            self.assertEqual("sha1", object_format)
            self.assertFalse(marker.exists())
            self.assertEqual(result["receipt"]["base_sha"], git(root, "rev-parse", "HEAD"))

    def test_redirecting_git_environment_fails_before_initialization(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            prepared = self.prepare(root, manifest)
            with patch.dict(
                os.environ,
                {"GIT_INDEX_FILE": (root.parent / "redirected-index").as_posix()},
            ):
                with self.assertRaisesRegex(ZeroToAutopilotError, "redirecting Git environment"):
                    ZeroToAutopilotTransaction(
                        bootstrap=FakePrivateBootstrap(root)
                    ).apply(self.request(root, manifest, prepared))
            self.assertFalse((root / ".git").exists())

    def test_existing_linked_worktree_preserves_its_specific_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary).resolve()
            primary = parent / "primary"
            linked = parent / "linked"
            manifest = parent / "inventory.json"
            primary.mkdir()
            git(primary, "init", "--template=", "-b", "main")
            (primary / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            git(primary, "add", "--", "tracked.txt")
            git(
                primary,
                "-c", "user.name=Fixture",
                "-c", "user.email=fixture@example.test",
                "commit", "-m", "base",
            )
            base_sha = git(primary, "rev-parse", "main")
            git(primary, "worktree", "add", "-b", "feature", linked.as_posix())
            prepared = self.prepare(linked, manifest)
            request = self.request(linked, manifest, prepared, base_sha=base_sha)
            index_raw = Path(git(linked, "rev-parse", "--git-path", "index"))
            index = index_raw if index_raw.is_absolute() else linked / index_raw
            index_before = index.read_bytes()

            result = ZeroToAutopilotTransaction(
                bootstrap=FakePrivateBootstrap(linked)
            ).apply(request)

            self.assertEqual("existing", result["receipt"]["local_mode"])
            self.assertEqual("feature", git(linked, "branch", "--show-current"))
            self.assertEqual(index_before, index.read_bytes())
            self.assertEqual(base_sha, git(linked, "rev-parse", "main"))

    def test_initialized_replay_rejects_unrelated_refs_before_provider_mutation(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            prepared = self.prepare(root, manifest)
            request = self.request(root, manifest, prepared)
            bootstrap = FakePrivateBootstrap(root)
            with self.assertRaisesRegex(RuntimeError, "crash at post-base"):
                ZeroToAutopilotTransaction(
                    bootstrap=bootstrap, fault=CrashOnce("post-base")
                ).apply(request)
            git(root, "branch", "unrelated", "HEAD")

            with self.assertRaisesRegex(ZeroToAutopilotError, "unexpected"):
                ZeroToAutopilotTransaction(bootstrap=bootstrap).apply(request)

            self.assertEqual(0, bootstrap.calls)
            self.assertEqual([], git(root, "remote").splitlines())

    def test_every_local_crash_boundary_recovers_without_duplicate_init_or_commit(self) -> None:
        for stage in (
            "pre-init",
            "post-init",
            "post-tree",
            "post-commit",
            "post-base",
            "pre-bootstrap",
            "post-bootstrap",
            "post-readback",
            "post-nested-event",
            "post-completion",
        ):
            temporary, root, manifest = self.fixture()
            with temporary, self.subTest(stage=stage):
                (root / "value.txt").write_text("value\n", encoding="utf-8")
                prepared = self.prepare(root, manifest)
                request = self.request(root, manifest, prepared)
                runner = GuardedRunner(root)
                bootstrap = FakePrivateBootstrap(root)
                crashing = ZeroToAutopilotTransaction(
                    runner, bootstrap=bootstrap, fault=CrashOnce(stage)
                )
                with self.assertRaisesRegex(RuntimeError, "crash at"):
                    crashing.apply(request)
                recovered = ZeroToAutopilotTransaction(
                    runner, bootstrap=bootstrap
                ).apply(request)

                self.assertEqual("repository-ready-for-ticket-autopilot", recovered["receipt"]["status"])
                self.assertEqual(1, sum(command[:2] == ("git", "init") for command in runner.commands))
                self.assertEqual(1, sum("commit" in command for command in runner.commands))

    def test_existing_git_mode_preserves_history_and_index(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            git(root, "init", "--template=", "-b", "main")
            (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            git(root, "add", "--", "tracked.txt")
            git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-m", "base")
            (root / ".env").write_text("TOKEN=fixture\n", encoding="utf-8")
            base_sha = git(root, "rev-parse", "HEAD")
            index = root / ".git" / "index"
            index_before = index.read_bytes()
            refs_before = git(root, "show-ref")
            prepared = self.prepare(root, manifest)
            request = self.request(root, manifest, prepared, base_sha=base_sha)
            bootstrap = FakePrivateBootstrap(root)

            result = ZeroToAutopilotTransaction(bootstrap=bootstrap).apply(request)

            self.assertEqual("existing", result["receipt"]["local_mode"])
            self.assertEqual(base_sha, git(root, "rev-parse", "HEAD"))
            self.assertEqual(refs_before, git(root, "show-ref"))
            self.assertEqual(index_before, index.read_bytes())
            self.assertEqual(["tracked.txt"], git(root, "ls-tree", "-r", "--name-only", "HEAD").splitlines())

    def test_mode_authority_replay_contradiction_and_completed_drift_fail(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            prepared = self.prepare(root, manifest)
            with self.assertRaisesRegex(ZeroToAutopilotError, "must not supply"):
                ZeroToAutopilotTransaction(bootstrap=FakePrivateBootstrap(root)).apply(
                    self.request(root, manifest, prepared, base_sha="a" * 40)
                )
            request = self.request(root, manifest, prepared)
            bootstrap = FakePrivateBootstrap(root)
            transaction = ZeroToAutopilotTransaction(bootstrap=bootstrap)
            transaction.apply(request)
            with self.assertRaisesRegex(ZeroToAutopilotError, "immutable"):
                transaction.apply(
                    self.request(root, manifest, prepared, actor="bob")
                )
            git(root, "remote", "remove", "origin")
            with self.assertRaises(RepositoryBootstrapError):
                transaction.apply(request)

    def test_corrupt_or_symlinked_state_fails_before_replay(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            prepared = self.prepare(root, manifest)
            request = self.request(root, manifest, prepared)
            bootstrap = FakePrivateBootstrap(root)
            ZeroToAutopilotTransaction(bootstrap=bootstrap).apply(request)
            state = root / ".git" / STATE_RELATIVE_PATH
            document = json.loads(state.read_text())
            document["payload"]["intent"]["actor"] = "mallory"
            state.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ZeroToAutopilotError, "integrity"):
                ZeroToAutopilotTransaction(bootstrap=bootstrap).apply(request)

        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            prepared = self.prepare(root, manifest)
            state_parent = root / ".git" / "ticket-autopilot"
            outside = root / "outside"
            outside.mkdir()
            (root / ".git").mkdir()
            state_parent.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ZeroToAutopilotError, "symbolic links"):
                ZeroToAutopilotTransaction(bootstrap=FakePrivateBootstrap(root)).apply(
                    self.request(root, manifest, prepared)
                )


class CliTests(ZeroBootstrapFixture):
    def invoke(self, args: list[str]) -> tuple[int, dict[str, object]]:
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(args)
        return code, json.loads(output.getvalue())

    def test_prepare_and_absent_status_are_provider_free(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "README.md").write_text("hello\n", encoding="utf-8")
            code, prepared = self.invoke(
                [
                    "prepare-zero-to-autopilot",
                    "--repo", root.as_posix(),
                    "--target", "owner/project",
                    "--visibility", "private",
                    "--base", "main",
                    "--output", manifest.as_posix(),
                ]
            )
            status_code, status = self.invoke(
                ["zero-to-autopilot-status", "--repo", root.as_posix()]
            )

            self.assertEqual(0, code)
            self.assertEqual("inventory-prepared", prepared["data"]["status"])
            self.assertEqual(0, status_code)
            self.assertEqual("absent", status["data"]["status"])
            self.assertFalse((root / ".git").exists())

    def test_cli_rejects_public_visibility_and_missing_exact_authority(self) -> None:
        temporary, root, manifest = self.fixture()
        with temporary:
            (root / "README.md").write_text("hello\n", encoding="utf-8")
            prepared = self.prepare(root, manifest)
            code, result = self.invoke(
                [
                    "zero-to-autopilot",
                    "--repo", root.as_posix(),
                    "--target", "owner/project",
                    "--visibility", "private",
                    "--base", "main",
                    "--inventory", manifest.as_posix(),
                    "--inventory-sha256", str(prepared["inventory_sha256"]),
                    "--actor", "",
                    "--evidence", "decision://x",
                ]
            )
            self.assertEqual(2, code)
            self.assertEqual("ZeroToAutopilotError", result["error"]["type"])


if __name__ == "__main__":
    unittest.main()
