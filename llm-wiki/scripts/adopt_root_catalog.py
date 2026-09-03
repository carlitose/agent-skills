#!/usr/bin/env python3
"""Explicitly add ownership boundaries to one exact legacy ``wiki/index.md``.

No heading or content inference is performed. The caller supplies the legacy SHA-256 and one
ordered byte span for each known owner. Validation and byte-perfect round-trip checks complete
before the regular file is atomically replaced.

Usage:
    python3 adopt_root_catalog.py <index.md> --expected-sha256 <digest> \
        --span project-sources:<start>:<end> \
        --span session-sources:<start>:<end> \
        --span timeline:<start>:<end> [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from root_catalog import (
    OWNERS,
    CatalogAdoptionSpan,
    CatalogOwnershipError,
    adopt_catalog_file,
)


def _span(value: str) -> CatalogAdoptionSpan:
    parts = value.split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("span must use OWNER:START:END")
    owner, raw_start, raw_end = parts
    try:
        start = int(raw_start)
        end = int(raw_end)
    except ValueError as error:
        raise argparse.ArgumentTypeError("span offsets must be decimal integers") from error
    return CatalogAdoptionSpan(owner, start, end)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument(
        "--span",
        action="append",
        type=_span,
        required=True,
        help="ordered OWNER:START:END byte span; required once per owner",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = adopt_catalog_file(args.catalog, args.expected_sha256, args.span)
    except (CatalogOwnershipError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{report['status']} {report['path']}")
        print(f"legacy sha256  {report['legacy_sha256']}")
        print(f"adopted sha256 {report['adopted_sha256']}")
        print("owners         " + ", ".join(OWNERS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
