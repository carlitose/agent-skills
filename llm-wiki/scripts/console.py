#!/usr/bin/env python3
"""UTF-8 on the way out, matching the repository convention.

`ticket-autopilot/scripts/autopilot/cli.py` reconfigures its streams the same way. Without
it an em-dash or an emoji in a script's own output is unencodable on a legacy Windows
console code page, and the script dies on a print rather than on anything real.
"""

from __future__ import annotations

import sys


def utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="strict")
