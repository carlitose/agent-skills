"""Summarize one Pi session log (JSONL) for a retrospective, read-only and redacted.

Usage: python -B session_digest.py [SESSION.jsonl]   (default: $PI_SESSION_FILE)
Prints one JSON object: turn and call counts, cost, tool errors, costliest turns,
repeated identical calls, and the largest tool results.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

TOP = 10
SNIPPET = 160
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)\b([\w-]*(?:api[_-]?key|token|secret|password|passwd|pwd))(\s*[:=]\s*)\S+"),
    re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[\w-]+\.[\w-]+\.[\w-]+"),
)


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        if pattern.groups == 2:
            text = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}<REDACTED>", text)
        elif pattern.groups == 1:
            text = pattern.sub(lambda m: f"{m.group(1)} <REDACTED>", text)
        else:
            text = pattern.sub("<REDACTED>", text)
    return text


def snippet(value: object) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = redact(" ".join(text.split()))
    return text if len(text) <= SNIPPET else text[: SNIPPET - 1] + "…"


def result_text(message: dict) -> str:
    return "".join(
        block.get("text", "") for block in message.get("content") or [] if isinstance(block, dict)
    )


def digest(path: Path) -> dict:
    turns = calls = single = 0
    total = 0.0
    by_tool: Counter[str] = Counter()
    seen: Counter[tuple[str, str]] = Counter()
    costly: list[dict] = []
    errors: list[dict] = []
    largest: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            event = json.loads(line)
            message = event.get("message") if event.get("type") == "message" else None
            if not isinstance(message, dict):
                continue
            if message.get("role") == "assistant":
                turns += 1
                tool_calls = [b for b in message.get("content") or [] if b.get("type") == "toolCall"]
                cost = float(((message.get("usage") or {}).get("cost") or {}).get("total") or 0)
                total += cost
                calls += len(tool_calls)
                single += len(tool_calls) == 1
                for call in tool_calls:
                    by_tool[call.get("name", "?")] += 1
                    seen[(call.get("name", "?"), snippet(call.get("arguments")))] += 1
                costly.append(
                    {
                        "line": line_number,
                        "cost": round(cost, 6),
                        "calls": [f"{c.get('name')}: {snippet(c.get('arguments'))}" for c in tool_calls],
                    }
                )
            elif message.get("role") == "toolResult":
                text = result_text(message)
                tool = message.get("toolName", "?")
                largest.append({"line": line_number, "tool": tool, "chars": len(text)})
                if message.get("isError"):
                    errors.append({"line": line_number, "tool": tool, "text": snippet(text)})
    return {
        "session": path.name,
        "assistant_turns": turns,
        "tool_calls": calls,
        "single_call_turns": single,
        "total_cost": round(total, 6),
        "calls_by_tool": dict(sorted(by_tool.items())),
        "errors": errors[:TOP],
        "error_count": len(errors),
        "costliest_turns": sorted(costly, key=lambda t: -t["cost"])[:TOP],
        "repeated_calls": [
            {"tool": tool, "arguments": args, "count": count}
            for (tool, args), count in seen.most_common(TOP)
            if count > 1
        ],
        "largest_results": sorted(largest, key=lambda r: -r["chars"])[:TOP],
    }


def main(argv: list[str]) -> int:
    target = argv[1] if len(argv) > 1 else os.environ.get("PI_SESSION_FILE", "")
    path = Path(target) if target else None
    if path is None or not path.is_file():
        print(f"session log not found: {target or '(no argument and no PI_SESSION_FILE)'}", file=sys.stderr)
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(digest(path), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
