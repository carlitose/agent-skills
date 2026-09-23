#!/usr/bin/env python3
"""One-ticket driver CLI; no Autopilot CLI or kernel imports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Resolve the pure-function package relative to this installed skill, not the caller's cwd.
CATALOG = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CATALOG / "ticket-autopilot" / "scripts"))
from autopilot.git_ops import common_git_dir, repository_root  # noqa: E402
from driver import execute, preflight  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run")
    run.add_argument("--candidate", required=True)
    source = run.add_mutually_exclusive_group(required=True)
    source.add_argument("--ticket")
    source.add_argument("--task")
    run.add_argument("--repo", required=True)
    run.add_argument("--base", default="HEAD")
    run.add_argument("--run-id")
    run.add_argument("--leaf")
    run.add_argument("--live-authorization")
    for name in ("status", "report", "approve"):
        query = sub.add_parser(name)
        query.add_argument("--repo", required=True)
        query.add_argument("run_id")
        if name == "approve":
            query.add_argument("--actor", required=True)
            query.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "run":
            result = execute(args)
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "integrated" else 1
        repo = Path(args.repo).resolve(strict=True)
        if repository_root(repo) != repo or not args.run_id.isascii() or not args.run_id.replace("-", "").isalnum():
            raise ValueError("invalid repo or run_id")
        if args.action == "approve":
            from approval import approve
            print(json.dumps(approve(repo, args.run_id, args.actor, args.reason), sort_keys=True))
            return 0
        directory = common_git_dir(repo) / "ticket-driver" / "runs" / args.run_id
        summary = directory / "summary.json"
        if summary.exists():
            value = json.loads(summary.read_text(encoding="utf-8"))
            resolved = directory / "approval-result.json"
            if resolved.exists():
                value.update(json.loads(resolved.read_text(encoding="utf-8")))
        elif (directory / "ledger.jsonl").exists():
            value = {"run_id": args.run_id, "status": "running", "ledger": str(directory / "ledger.jsonl")}
        else:
            raise ValueError("run not found")
        print(json.dumps(value, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ticket-driver: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
