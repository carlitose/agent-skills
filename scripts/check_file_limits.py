"""Read-only file/aggregate line limits; Ruff's line-length is not a file limit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def positive_integer(value: object) -> bool:
    return type(value) is int and value > 0


def check_limits(root: Path, policy: object) -> dict:
    if not isinstance(policy, dict) or set(policy) != {
        "schema", "files", "total_line_limit"
    }:
        raise ValueError("policy must contain schema, files and total_line_limit")
    if type(policy["schema"]) is not int or policy["schema"] != 1:
        raise ValueError("unsupported policy schema")
    limits = policy["files"]
    if not isinstance(limits, dict) or not limits:
        raise ValueError("files must be a nonempty map")
    if not positive_integer(policy["total_line_limit"]):
        raise ValueError("total_line_limit must be a positive integer")

    root = root.resolve()
    files = {}
    violations = []
    total = 0
    for relative, limit in sorted(limits.items()):
        if not isinstance(relative, str) or not positive_integer(limit):
            raise ValueError("file paths need positive integer limits")
        path = (root / relative).resolve()
        if Path(relative).is_absolute() or not path.is_relative_to(root):
            raise ValueError(f"file path is outside the root: {relative}")
        lines = len(path.read_text(encoding="utf-8").splitlines())
        files[relative] = {"lines": lines, "limit": limit}
        total += lines
        if lines > limit:
            violations.append({"path": relative, "lines": lines, "limit": limit})
    if total > policy["total_line_limit"]:
        violations.append({
            "path": "<total>", "lines": total, "limit": policy["total_line_limit"]
        })
    return {
        "schema": 1,
        "files": files,
        "total_lines": total,
        "total_line_limit": policy["total_line_limit"],
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    args = parser.parse_args()
    try:
        policy = json.loads((args.root / "scripts/file-limits.json").read_text(encoding="utf-8"))
        report = check_limits(args.root, policy)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"file-limit error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=True))
    else:
        for path, count in report["files"].items():
            print(f"{path}: {count['lines']}/{count['limit']} lines")
        print(f"Total: {report['total_lines']}/{report['total_line_limit']} lines")
        for failure in report["violations"]:
            print(f"LIMIT EXCEEDED: {failure['path']}", file=sys.stderr)
    return 1 if report["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
