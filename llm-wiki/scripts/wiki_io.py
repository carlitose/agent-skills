"""Native I/O spelling for the frozen wiki store, never a serialized identity."""
from __future__ import annotations

import os
from pathlib import Path


def _windows_io_spelling(absolute: str) -> str:
    if absolute.startswith("\\\\?\\"):
        return absolute
    if absolute.startswith("\\\\"):
        return "\\\\?\\UNC\\" + absolute[2:]
    return "\\\\?\\" + absolute


def native_path(path: Path) -> Path:
    """Adapt an I/O operand only; callers still own canonicality and containment.

    Keep the original Path for Git arguments, logical relatives and persisted records.
    No resolve, case folding, separator rewrite or filesystem validity inference occurs.
    """
    if os.name != "nt":
        return path
    return Path(_windows_io_spelling(str(path.absolute())))
