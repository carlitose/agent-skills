"""One typed score request for all modified functions; uncertainty widens review."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from findings import parse_findings
from leaf import invoke, render_prompt, usage
from arbiter import Unavailable, allowed, ask, classify, questions
from cascade import _append
from function_diff import changed_functions


def assess(run, summary: dict, repo: Path, worktree: Path, policy: dict, root: Path, candidate,
           *, transport=None, sleep=None) -> list[dict]:
    functions, unsupported = changed_functions(worktree, candidate)
    summary["risk"] = {"functions": [{"path": f["path"], "function": f["function"], "change": f["change"]}
                                     for f in functions], "unsupported": unsupported, "directed": []}
    run.event("risk-inventory", functions=len(functions), unsupported=unsupported)
    if not functions:
        return []
    template, hashes = questions(root)
    summary.setdefault("question_hashes", {}).update(hashes)
    config = policy["arbiter"]
    summary.setdefault("jev_usage", {"calls": 0, "input_tokens": 0, "output_tokens": 0})
    eligible = [f for f in functions if len(f["hunk"].encode()) <= 8192]
    oversized = [f for f in functions if f not in eligible]
    if len(eligible) > 32:
        oversized.extend(eligible)
        eligible = []
    answers, unavailable = None, None
    if eligible and allowed(repo, config):
        state = {"functions": eligible}
        selected = {}
        for index in range(len(eligible)):
            question = dict(template["risk.semantic_change"])
            question["instructions"] += f" Evaluate only `functions[{index}]` in the state."
            selected[f"risk_{index}"] = question
        try:
            kwargs = {"transport": transport}
            if sleep is not None:
                kwargs["sleep"] = sleep
            answers, usage = ask(state, selected, config, **kwargs)
            summary["jev_usage"]["calls"] += 1
            summary["jev_usage"]["input_tokens"] += usage["input_tokens"]
            summary["jev_usage"]["output_tokens"] += usage["output_tokens"]
        except Unavailable as error:
            unavailable = str(error)
    elif not allowed(repo, config):
        unavailable = "repository not in external_judgment_allowed"
    selected_high = []
    digest = hashlib.sha256(json.dumps({"functions": eligible}, sort_keys=True).encode()).hexdigest()
    for index, function in enumerate(eligible):
        answer = answers.get(f"risk_{index}") if answers else None
        try:
            decision = classify(answer, config) if answer else {"outcome": "uncertain", "confidence": None}
        except Unavailable:
            decision = {"outcome": "uncertain", "confidence": None}
        outcome = decision["outcome"]
        high = outcome == "uncertain" or outcome >= config["risk_score_high"]
        record = {"question": "risk.semantic_change", "question_sha256": hashes["risk.semantic_change"],
                  "state_sha256": digest, "function": function["function"], "path": function["path"],
                  "hunk_sha256": hashlib.sha256(function["hunk"].encode()).hexdigest(),
                  "answer": answer, "decision": decision, "threshold": config["risk_score_high"],
                  "directed": high, "arbiter": "unavailable" if unavailable else "observed",
                  "unavailability": unavailable}
        _append(run.path / "judgments.jsonl", record)
        if high:
            selected_high.append(function)
    selected_high.extend(oversized)
    summary["risk"]["directed"] = [{"path": f["path"], "function": f["function"]} for f in selected_high]
    if oversized:
        summary["risk"]["unsupported"].extend({"path": f["path"], "reason": "function hunk exceeds risk input bound"} for f in oversized)
    run.event("risk-directed", functions=summary["risk"]["directed"], unavailability=unavailable)
    return selected_high


def directed_review(run, summary: dict, state: dict, worktree: Path, policy: dict,
                    root: Path, leaf: str | None, functions: list[dict], *, attempt: int = 1) -> dict:
    if not functions:
        return {"state": "clean", "findings": []}
    name = f"directed-reviewer-{attempt}"
    template = root / "prompts" / "reviewer-directed.md"
    prompt, prompt_hash = render_prompt(template, kind=state["kind"], source_digest=state["digest"],
                                        task_text=state["text"])
    hunks = "\n\n".join(f"{f['path']}:{f['function']} ({f['change']})\n{f['hunk']}" for f in functions)
    prompt = prompt.replace("{risk_hunks}", hunks)
    directory = worktree / ".ticket-driver"
    directory.mkdir(exist_ok=True)
    session = run.path / "sessions" / name
    argv, out, err, code, duration, failure = invoke(leaf, policy, session, prompt, worktree)
    visible = argv[:-1] + ["<prompt:sha256:" + hashlib.sha256(prompt.encode()).hexdigest() + ">"]
    summary["receipts"][name] = run.receipt(name, visible, worktree,
        (out, err, code, duration, failure), max_bytes=policy["max_output_bytes"])
    summary["leaves"][name] = usage(session)
    summary.setdefault("prompt_hashes", {})["reviewer-directed"] = prompt_hash
    artifact = directory / "review-directed.md"
    if code != 0 or failure or not artifact.is_file():
        summary["status"], summary["failure"] = "gated", "directed reviewer unavailable"
        return {"state": "unparsed", "findings": []}
    summary["receipts"][name+"-artifact"] = run.authored_receipt(name+"-artifact", artifact)
    text = artifact.read_text(encoding="utf-8")
    artifact.unlink()
    findings = parse_findings(text)
    run.event("directed-findings", attempt=attempt, **findings)
    return findings
