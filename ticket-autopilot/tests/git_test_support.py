"""Process-scoped Git isolation for disposable repository fixtures."""

import os
import shutil
import subprocess
import tempfile
import unittest
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


_REAL_WRITE_TEXT = Path.write_text


def _write_text_without_platform_newlines(
    self, data, encoding=None, errors=None, newline=None
):
    """Write the text the fixture declared, not the platform's idea of it.

    `Path.write_text` translates "\\n" to os.linesep, so on Windows a fixture that
    writes "# Guide\\n" puts CRLF on disk. Neither Git policy then behaves: with
    core.autocrlf=true the working tree stops matching the index and ticket sources
    read as drifted, and with core.autocrlf=false the CR enters the blob and the
    docs-only patch check reports trailing whitespace. Both are artefacts of the
    fixture, not of the code under test, and they make an outcome depend on the
    operator's machine. An explicit `newline=` still wins, so a fixture that wants
    CRLF asks for it and gets it.
    """
    return _REAL_WRITE_TEXT(
        self, data, encoding=encoding, errors=errors,
        newline="\n" if newline is None else newline,
    )


@contextmanager
def isolated_git_environment():
    """Use disposable config, not the operator's config, for all nested Git calls.

    Local repository settings and explicit command options remain available for
    intentional conversion tests. No user/system configuration file is written.
    """
    with tempfile.TemporaryDirectory(prefix="git-test-config-") as temporary:
        root = Path(temporary)
        empty = root / "empty"
        empty.mkdir()
        attributes = root / "attributes"
        attributes.write_bytes(b"")
        config = root / "config"
        environment = {
            key: value for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        environment.update({
            "GIT_CONFIG_GLOBAL": str(config),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_TEMPLATE_DIR": str(empty),
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_DEFAULT_HASH": "sha1",
        })
        settings = {
            "core.autocrlf": "false",
            "core.eol": "lf",
            "core.hooksPath": str(empty),
            "core.attributesFile": str(attributes),
            "commit.gpgSign": "false",
            "tag.gpgSign": "false",
        }
        for key, value in settings.items():
            subprocess.run(
                ["git", "config", "--file", str(config), key, value],
                cwd=root, env=environment, check=True, capture_output=True,
                timeout=15,
            )
        with patch.dict(os.environ, environment, clear=True), \
                patch.object(Path, "write_text", _write_text_without_platform_newlines):
            yield


class GitIsolatedTestCase(unittest.TestCase):
    """Keep nested runtime subprocesses isolated throughout a fixture class."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        environment = isolated_git_environment()
        environment.__enter__()
        cls.addClassCleanup(environment.__exit__, None, None, None)

    @classmethod
    def repository_template(cls, build: Callable[[Path], None], *, name: str) -> Path:
        """Build one disposable repository per class and keep it for copying.

        `build` runs once. Its result is never handed to a test: each case receives
        its own copy, so a case that mutates its repository cannot reach another.
        """
        # Per class, never inherited: a subclass builds its own rather than reusing a
        # parent's template and quietly sharing state across fixtures.
        if "_repository_templates" not in vars(cls):
            cls._repository_templates = {}
        cache = cls._repository_templates
        if name not in cache:
            owner = tempfile.TemporaryDirectory(prefix=f"git-template-{name}-")
            cls.addClassCleanup(owner.cleanup)
            template = Path(owner.name) / "template"
            template.mkdir()
            build(template)
            if not (template / ".git").is_dir():
                raise AssertionError(
                    f"repository template {name!r} did not produce a Git repository"
                )
            cache[name] = template
        return cache[name]

    def copy_of_template(self, template: Path, destination: Path) -> Path:
        """Give this case its own repository, byte for byte.

        Copying preserves the exact stored bytes and the index, which re-running
        `git init`/`add`/`commit` under a different newline or attribute policy would
        not. A partial copy fails here rather than inside the code under test.
        """
        shutil.copytree(template, destination, symlinks=True)
        if not (destination / ".git" / "HEAD").is_file():
            raise AssertionError(f"repository copy at {destination} is incomplete")
        return destination
