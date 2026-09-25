"""Host-only Jev file binding; never start a driver, agent or network request here.

The ticket-driver arbiter's isolated_key context removes the key from the child
process environment while keeping it available to the host judge. A caller must
supply that context manager; this module does not relax its repository allowlist.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[2]


class JevKeyError(ValueError):
    """The external key cannot be safely bound to this host process."""


def read_jev_key(path: Path) -> str:
    """Read one raw token or one TYPESAFE_API_KEY assignment outside Git."""
    file = Path(path)
    try:
        if (file.is_symlink() or not file.is_file() or
                file.resolve().is_relative_to(REPO) or not 0 < file.stat().st_size <= 16384):
            raise JevKeyError("external Jev file is unavailable or unsafe")
        lines = [row.strip() for row in file.read_text(encoding="utf-8-sig").splitlines()
                 if row.strip() and not row.lstrip().startswith("#")]
    except (OSError, UnicodeError) as exc:
        raise JevKeyError("external Jev file cannot be read") from exc
    if len(lines) != 1:
        raise JevKeyError("external Jev file requires exactly one credential")
    if lines[0].startswith("TYPESAFE_API_KEY="):
        value = lines[0].split("=", 1)[1].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
    elif "=" not in lines[0]:
        value = lines[0]
    else:
        raise JevKeyError("external Jev file has an unsupported assignment")
    if not (16 <= len(value) <= 2048 and value.isascii() and value.isprintable()
            and not any(char.isspace() or char in (chr(92), "/", ":", "<", ">") for char in value)):
        raise JevKeyError("external Jev credential has an invalid shape")
    return value


@contextmanager
def jev_key_scope(path: Path, isolated_key: Callable):
    """Give the host arbiter its key, never a child; only valid in a serial process."""
    if "TYPESAFE_API_KEY" in os.environ:
        raise JevKeyError("a preexisting Jev credential must not be overwritten")
    key = read_jev_key(path)
    try:
        os.environ["TYPESAFE_API_KEY"] = key
        with isolated_key(require=True):
            if "TYPESAFE_API_KEY" in os.environ:
                raise JevKeyError("arbiter did not isolate the key from child processes")
            yield
    finally:
        os.environ.pop("TYPESAFE_API_KEY", None)
