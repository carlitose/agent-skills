from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

if __package__:
    from .git_test_support import GitIsolatedTestCase, isolated_git_environment
else:
    from git_test_support import GitIsolatedTestCase, isolated_git_environment


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, check=True, timeout=15
    ).stdout


class GitEnvironmentTests(unittest.TestCase):
    def commit_fixture(self, repo: Path) -> None:
        repo.mkdir()
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "config", "user.email", "fixture@example.invalid")
        payload = b"canonical fixture\n"
        (repo / "ticket.md").write_bytes(payload)
        git(repo, "add", "ticket.md")
        git(repo, "commit", "-m", "fixture")
        self.assertEqual(payload, git(repo, "show", "HEAD:ticket.md"))
        self.assertTrue((repo / ".git").is_dir())

    def test_host_configuration_is_isolated_and_restored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            poison = root / "host.gitconfig"
            poison.write_bytes(
                b"[core]\n autocrlf = true\n[commit]\n gpgsign = true\n"
                b"[gpg]\n program = missing-fixture-signing-program\n"
            )
            before_bytes = poison.read_bytes()
            environment = {
                key: value for key, value in os.environ.items()
                if not key.startswith("GIT_")
            }
            environment.update({
                "GIT_CONFIG_GLOBAL": str(poison),
                "GIT_CONFIG_SYSTEM": str(poison),
                "GIT_CONFIG_COUNT": "2",
                "GIT_CONFIG_KEY_0": "core.autocrlf",
                "GIT_CONFIG_VALUE_0": "true",
                "GIT_CONFIG_KEY_1": "commit.gpgsign",
                "GIT_CONFIG_VALUE_1": "true",
            })
            with patch.dict(os.environ, environment, clear=True):
                before_environment = dict(os.environ)
                with isolated_git_environment():
                    repo = root / "repo"
                    self.commit_fixture(repo)
                    self.assertEqual(b"false\n", git(repo, "config", "core.autocrlf"))
                    self.assertEqual(b"false\n", git(repo, "config", "commit.gpgsign"))
                # Do not print the process environment, which can contain secrets.
                self.assertTrue(dict(os.environ) == before_environment)
            self.assertEqual(before_bytes, poison.read_bytes())

    def test_hooks_attributes_and_templates_do_not_leak_into_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hooks = root / "host hooks"
            hooks.mkdir()
            hook = hooks / "pre-commit"
            hook.write_bytes(b"#!/bin/sh\nexit 91\n")
            hook.chmod(0o755)
            attributes = root / "host attributes"
            attributes.write_bytes(b"* text eol=crlf\n")
            templates = root / "host templates"
            templates.mkdir()
            (templates / "host-marker").write_bytes(b"must not be copied")
            config = root / "host config"
            config.write_bytes((
                "[core]\n hooksPath = " + json.dumps(hooks.as_posix(), ensure_ascii=False)
                + "\n attributesFile = " + json.dumps(attributes.as_posix(), ensure_ascii=False)
                + "\n"
            ).encode("utf-8"))
            protected = {p: p.read_bytes() for p in (hook, attributes, config)}
            with patch.dict(os.environ, {
                "GIT_CONFIG_GLOBAL": str(config),
                "GIT_CONFIG_SYSTEM": str(config),
                "GIT_TEMPLATE_DIR": str(templates),
            }):
                with isolated_git_environment():
                    repo = root / "repo"
                    self.commit_fixture(repo)
                    self.assertFalse((repo / ".git/host-marker").exists())
                    # A checkout traverses smudge/EOL handling, not only git add.
                    (repo / "ticket.md").unlink()
                    git(repo, "checkout", "--", "ticket.md")
                    self.assertEqual(b"canonical fixture\n", (repo / "ticket.md").read_bytes())
            self.assertTrue(all(p.read_bytes() == data for p, data in protected.items()))

    def test_module_qualified_imports_work_in_a_fresh_isolated_process(self) -> None:
        root = Path(__file__).resolve().parents[2]
        modules = [
            "test_kernel", "test_repository_merge_authority",
            "test_final_tree_projection", "test_final_tree_transaction",
            "test_git_test_support",
        ]
        program = (
            "import importlib,json,sys; from pathlib import Path; "
            "root=Path(sys.argv[1]).resolve(); sys.path.insert(0,str(root)); "
            "modules=[importlib.import_module('ticket-autopilot.tests.'+name) "
            "for name in json.loads(sys.argv[2])]; "
            "assert all(Path(module.__file__).resolve().is_relative_to(root) for module in modules)"
        )
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", program, str(root), json.dumps(modules)],
            cwd=tempfile.gettempdir(), capture_output=True, timeout=15,
        )
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8", errors="replace"))

    def test_repository_environment_and_exception_cleanup_are_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            foreign = root / "foreign"
            variables = {
                "GIT_DIR": str(foreign / "git"),
                "GIT_WORK_TREE": str(foreign / "worktree"),
                "GIT_INDEX_FILE": str(foreign / "index"),
                "GIT_OBJECT_DIRECTORY": str(foreign / "objects"),
                "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(foreign / "alternate"),
                "GIT_CONFIG_PARAMETERS": "deliberately invalid fixture parameters",
            }
            with patch.dict(os.environ, variables):
                before = dict(os.environ)
                with self.assertRaisesRegex(RuntimeError, "fixture stop"):
                    with isolated_git_environment():
                        for name in variables:
                            self.assertNotIn(name, os.environ)
                        self.commit_fixture(root / "repo")
                        raise RuntimeError("fixture stop")
                self.assertTrue(dict(os.environ) == before)
            self.assertFalse(foreign.exists())


class RepositoryTemplateTests(GitIsolatedTestCase):
    """A copied repository must be the repository, not merely a similar one."""

    builds = 0

    @classmethod
    def build(cls, template: Path) -> None:
        cls.builds += 1
        git(template, "init", "-b", "main")
        git(template, "config", "user.name", "Fixture")
        git(template, "config", "user.email", "fixture@example.invalid")
        # Mixed newlines on purpose: a copy that rewrites bytes is a broken copy.
        (template / "unix.md").write_bytes(b"one\ntwo\n")
        (template / "dos.md").write_bytes(b"one\r\ntwo\r\n")
        git(template, "add", "unix.md", "dos.md")
        git(template, "commit", "-m", "baseline")
        (template / "staged.md").write_bytes(b"staged\n")
        git(template, "add", "staged.md")

    def fresh(self, name: str) -> Path:
        directory = tempfile.TemporaryDirectory(prefix="template-copy-")
        self.addCleanup(directory.cleanup)
        template = self.repository_template(self.build, name="baseline")
        return self.copy_of_template(template, Path(directory.name) / name)

    def test_a_copy_reproduces_the_initialised_repository_byte_for_byte(self) -> None:
        template = self.repository_template(self.build, name="baseline")
        copy = self.fresh("copy")
        self.assertEqual(
            git(template, "rev-parse", "HEAD"), git(copy, "rev-parse", "HEAD")
        )
        self.assertEqual(git(template, "write-tree"), git(copy, "write-tree"),
                         "a copied index must stage exactly what the original staged")
        self.assertEqual(git(template, "status", "--porcelain=v1"),
                         git(copy, "status", "--porcelain=v1"))
        for name in ("unix.md", "dos.md", "staged.md"):
            self.assertEqual((template / name).read_bytes(), (copy / name).read_bytes(),
                             f"{name} changed bytes while being copied")
        self.assertEqual(b"one\r\ntwo\r\n", (copy / "dos.md").read_bytes())

    def test_each_case_owns_its_copy_and_the_template_is_built_once(self) -> None:
        first, second = self.fresh("first"), self.fresh("second")
        (first / "unix.md").write_bytes(b"mutated\n")
        git(first, "add", "unix.md")
        git(first, "commit", "-m", "mutation")
        self.assertEqual(b"one\ntwo\n", (second / "unix.md").read_bytes())
        self.assertNotEqual(git(first, "rev-parse", "HEAD"), git(second, "rev-parse", "HEAD"))
        template = self.repository_template(self.build, name="baseline")
        self.assertEqual(b"one\ntwo\n", (template / "unix.md").read_bytes())
        self.assertEqual(1, type(self).builds, "the template is built once for the class")

    def test_template_can_be_rebuilt_after_class_cleanup(self) -> None:
        class Fixture(GitIsolatedTestCase):
            pass

        self.addCleanup(Fixture.doClassCleanups)
        builds = []

        def build(template: Path) -> None:
            builds.append(template)
            git(template, "init", "-b", "main")
            (template / "fixture.md").write_bytes(b"original\n")

        first = Fixture.repository_template(build, name="lifecycle")
        self.assertEqual(first, Fixture.repository_template(build, name="lifecycle"))
        self.assertEqual(1, len(builds), "a live template is reused")
        Fixture.doClassCleanups()
        self.assertFalse(first.exists(), "class cleanup releases the owned directory")

        second = Fixture.repository_template(build, name="lifecycle")
        with tempfile.TemporaryDirectory() as directory:
            copy = Fixture().copy_of_template(second, Path(directory) / "copy")
            self.assertEqual(b"original\n", (copy / "fixture.md").read_bytes())
        self.assertEqual(2, len(builds), "a later lifecycle builds a fresh template")
        Fixture.doClassCleanups()
        self.assertFalse(second.exists(), "the rebuilt template is also released")

    def test_an_incomplete_copy_fails_here_instead_of_inside_the_code_under_test(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="broken-copy-")
        self.addCleanup(directory.cleanup)
        hollow = Path(directory.name) / "hollow"
        (hollow / ".git").mkdir(parents=True)
        with self.assertRaisesRegex(AssertionError, "incomplete"):
            self.copy_of_template(hollow, Path(directory.name) / "copy")
        with self.assertRaisesRegex(AssertionError, "did not produce a Git repository"):
            self.repository_template(lambda path: None, name="never-initialised")


if __name__ == "__main__":
    unittest.main()
