#!/usr/bin/env python3
"""Skills-only access to the canonical ticket contract, without the runner.

    python -B <ticket-autopilot root>/scripts/ticket-contract.py parse <ticket.md>
    python -B <ticket-autopilot root>/scripts/ticket-contract.py emit <envelope.json> <body.md> --output <ticket.md>

The script finds its own package, so any shell may call it with any path form; nobody has to
put the skill root on `sys.path` (a Git Bash `/c/...` path there is invisible to Windows
Python). It imports only `autopilot.ticket_contract`: no CLI, kernel, ledger or run. Both
commands print the normalized envelope, the body and the canonical digest as JSON; a contract
violation exits 2 with the reason on stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autopilot.ticket_contract import (  # noqa: E402
    ContractError,
    parse_ticket_markdown,
    read_ticket_text,
    serialize_ticket_markdown,
    ticket_source_digest,
)


def _report(path: Path) -> dict:
    parsed = parse_ticket_markdown(read_ticket_text(path), source=str(path))
    return {"path": str(path), "envelope": parsed.envelope, "body": parsed.body,
            "digest": ticket_source_digest(path)}


def _write(path: Path, text: str) -> None:
    if not path.parent.is_dir():
        raise ContractError(f"destination folder does not exist: {path.parent}")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    parse = commands.add_parser("parse", help="validate one ticket and print its normalized form")
    parse.add_argument("ticket", type=Path)
    emit = commands.add_parser("emit", help="serialize, write and read back one ticket")
    emit.add_argument("envelope", type=Path)
    emit.add_argument("body", type=Path)
    emit.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "emit":
            envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
            body = args.body.read_text(encoding="utf-8")
            _write(args.output, serialize_ticket_markdown(envelope, body))
            path = args.output
        else:
            path = args.ticket
        report = _report(path)
    except (ContractError, OSError, ValueError) as error:
        print(f"ticket-contract: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
