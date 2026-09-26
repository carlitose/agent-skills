"""Classify a finished Harbor cell: the agent's own outcome, or an infrastructure failure.

User rule (2026-09-25): an agent mistake counts; a failure caused by the evaluation
harness or any factor other than the agent's work is repeated. Classification reads only
Harbor's result, the adapter receipt and the Pi session's final stop reason; it never
opens hidden tests. A verified pass is never repeated. Unrecognised cases go to review
rather than being guessed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

MAX_INFRA_RETRIES = 2
# Model provider or transport stopped the agent, not the agent's own decision.
PROVIDER_ERROR = re.compile(
    r"websocket closed|econnreset|socket hang up|connection (reset|closed|refused)|"
    r"\b5\d\d\b|service unavailable|overloaded|bad gateway|gateway timeout|rate limit",
    re.IGNORECASE)


def _json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf8"))
    except (OSError, ValueError):
        return None


def _last_assistant(path: Path) -> dict:
    last = {}
    try:
        for line in path.read_text(encoding="utf8").splitlines():
            try:
                message = json.loads(line).get("message") or {}
            except ValueError:
                continue
            if message.get("role") == "assistant":
                last = message
    except OSError:
        pass
    return last


def classify_trial(trial_dir: Path) -> dict:
    trial_dir = Path(trial_dir)
    result = _json(trial_dir / "result.json")
    if not isinstance(result, dict):
        return {"class": "infra:no-result", "reward": None, "evidence": "no Harbor result.json"}
    verifier = result.get("verifier_result") or {}
    reward = (verifier.get("rewards") or {}).get("reward") if verifier else None
    exception = (result.get("exception_info") or {}).get("exception_type")
    receipt = _json(trial_dir / "agent/standard-receipt.json") or {}
    last = _last_assistant(trial_dir / "agent/pi-builder.jsonl")
    provider = last.get("stopReason") == "error" and bool(PROVIDER_ERROR.search(last.get("errorMessage") or ""))
    evidence = {"reward": reward, "exception": exception, "agent_status": receipt.get("status"),
                "stop_reason": last.get("stopReason"), "error": last.get("errorMessage")}
    host_error = receipt.get("error_type") not in (None, "RuntimeError")
    # A failed agent that never sent one model request did no work: the harness failed it
    # (e.g. the c1a/c3a endpoint identity mismatch). Its verifier score is not the agent's.
    host = _json(trial_dir / "agent/host-status.json") or {}
    never_started = (((receipt.get("model") or {}).get("budget") or {}).get("requests") == 0
                     or (host.get("phases") == [] and host.get("commands") == 0))
    evidence["error_type"] = receipt.get("error_type")
    if reward == 1:
        kind = "agent"
    elif provider and receipt.get("status") == "failed":
        kind = "infra:provider"
    elif (host_error or never_started) and receipt.get("status") == "failed":
        # A host-side exception in our adapter/transport (not the agent's own stop), e.g.
        # ValueError from Windows CreateProcess on a NUL byte, ended the agent run.
        kind = "infra:harness"
    elif result.get("agent_execution") is None and reward is None:
        kind = "infra:environment"
    elif reward is None and exception not in ("NonZeroAgentExitCodeError", "AgentTimeoutError"):
        kind = "infra:verifier"
    elif reward is not None:
        kind = "agent"
    else:
        kind = "review"
    return {"class": kind, "reward": reward, "evidence": evidence}


def retry_plan(cells: dict[str, list[str]]) -> dict:
    """Given each cell's classifications in attempt order, decide what to repeat."""
    plan = {"retry": [], "final": {}, "exhausted": [], "review": []}
    for cell, attempts in sorted(cells.items()):
        first = next((i for i, kind in enumerate(attempts) if not kind.startswith("infra:")), None)
        if first is not None:
            if attempts[first] == "review":
                plan["review"].append(cell)
            else:
                plan["final"][cell] = first
        elif len(attempts) > MAX_INFRA_RETRIES:
            plan["exhausted"].append(cell)
        else:
            plan["retry"].append(cell)
    return plan


if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:]:
        print(json.dumps({"trial": arg, **classify_trial(Path(arg))}, sort_keys=True))
