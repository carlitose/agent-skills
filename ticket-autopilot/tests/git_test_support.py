"""Process-scoped Git isolation for disposable repository fixtures."""

import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


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
        with patch.dict(os.environ, environment, clear=True):
            yield


class GitIsolatedTestCase(unittest.TestCase):
    """Keep nested runtime subprocesses isolated throughout a fixture class."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        environment = isolated_git_environment()
        environment.__enter__()
        cls.addClassCleanup(environment.__exit__, None, None, None)
