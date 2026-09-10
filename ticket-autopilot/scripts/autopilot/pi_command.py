"""Invoke installed Pi package commands without exposing shell syntax to callers."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Protocol

from .git_ops import CommandResult


class PiRunner(Protocol):
    def run(
        self, arguments: list[str], *, cwd: Path, settings_root: Path
    ) -> CommandResult: ...


_NPM_SHIM = r'''@ECHO off
GOTO start
:find_dp0
SET dp0=%~dp0
EXIT /b
:start
SETLOCAL
CALL :find_dp0

IF EXIST "%dp0%\node.exe" (
  SET "_prog=%dp0%\node.exe"
) ELSE (
  SET "_prog=node"
  SET PATHEXT=%PATHEXT:;.JS;=;%
)

endLocal & goto #_undefined_# 2>NUL || title %COMSPEC% & "%_prog%"  "%dp0%\{entry}" %*
'''


def _windows_pi() -> list[str]:
    selected = shutil.which("pi")
    if selected is None:
        raise ValueError("Windows Pi is not available on PATH")
    shim = Path(selected).resolve()
    if shim.suffix.lower() != ".cmd" or not shim.is_file():
        raise ValueError("Windows Pi requires a supported npm launcher")
    package = shim.parent / "node_modules" / "@earendil-works" / "pi-coding-agent"
    metadata = json.loads((package / "package.json").read_text(encoding="utf-8"))
    if not isinstance(metadata, dict) or metadata.get("name") != "@earendil-works/pi-coding-agent":
        raise ValueError("Windows Pi package identity is contradictory")
    bins = metadata.get("bin")
    entry_name = bins.get("pi") if isinstance(bins, dict) else None
    if not isinstance(entry_name, str) or not entry_name:
        raise ValueError("Windows Pi package has no declared bin.pi")
    entry = (package / entry_name).resolve()
    if not entry.is_relative_to(package.resolve()) or not entry.is_file():
        raise ValueError("Windows Pi entry point is missing or outside its package")
    relative_entry = entry.relative_to(shim.parent).as_posix().replace("/", "\\")
    if shim.read_text(encoding="utf-8-sig").strip() != _NPM_SHIM.format(entry=relative_entry).strip():
        raise ValueError("Windows Pi npm launcher and declared entry point disagree")
    adjacent = shim.parent / "node.exe"
    selected_node = str(adjacent) if adjacent.exists() else shutil.which("node.exe")
    if selected_node is None or not Path(selected_node).is_file():
        raise ValueError("Windows Pi requires an existing native node.exe")
    return [str(Path(selected_node).resolve()), str(entry)]


class SubprocessPiRunner:
    def run(
        self, arguments: list[str], *, cwd: Path, settings_root: Path
    ) -> CommandResult:
        if arguments == ["list"]:
            script = 'PI_CODING_AGENT_DIR="$1" pi list'
        elif len(arguments) == 2 and arguments[0] == "install":
            script = 'PI_CODING_AGENT_DIR="$1" pi install "$2"'
        else:
            raise ValueError("Pi sync supports only install <checkout> and list")
        if sys.platform == "win32":
            command = [*_windows_pi(), *arguments]
            env = {**os.environ, "PI_CODING_AGENT_DIR": str(settings_root)}
        else:
            command = ["zsh", "-lic", script, "agent-skills-pi-sync", settings_root.as_posix(), *arguments[1:]]
            env = None
        # Decode in this thread: Windows subprocess text reader failures can otherwise
        # yield None streams instead of raising to the transaction's recovery path.
        completed = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, check=False,
        )
        return CommandResult(
            completed.stdout.decode("utf-8"), completed.stderr.decode("utf-8"), completed.returncode
        )
