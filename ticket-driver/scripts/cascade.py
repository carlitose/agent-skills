"""Typed arbitration, one fresh judge on uncertainty, then a literal human gate."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from arbiter import Unavailable, allowed, ask, classify, questions
from leaf import invoke, usage


def _append(path: Path, event: dict) -> None:
    with path.open("ab") as output:
        output.write((json.dumps(event, sort_keys=True) + "\n").encode())
        output.flush()
        os.fsync(output.fileno())


ANSWER_LINE = re.compile(r"answer\s*:\s*(.*)", re.IGNORECASE)
UNDETERMINED = "undetermined"


def verdicts(question: dict) -> dict[str, str]:
    """A judge's allowed final answers, named like the arbiter's outcomes for the same question."""
    if question["type"] == "noul":
        return {"yes": "yes", "no": "no"}
    if question["type"] == "choice":
        return {name: name for name in question["criteria"]}
    return {}


def render_verdicts(question: dict) -> str:
    criteria = question["criteria"]
    rows = ([("yes", criteria["true"]), ("no", criteria["false"])] if question["type"] == "noul"
            else list(criteria.items()) if question["type"] == "choice" else [])
    rows.append((UNDETERMINED, "The exact state does not decide the question; the driver opens a human gate."))
    return "\n".join(f"- `Answer: {value}`: {meaning}" for value, meaning in rows)


def _plain(line: str) -> str:
    return line.replace("*", "").replace("`", "").strip()


def _judge_answer(question: dict, text: str) -> str:
    """Only one final `Answer:` line decides; every other ending fails closed to `uncertain`."""
    lines = [line for line in map(_plain, text.splitlines()) if line]
    answers = [index for index, line in enumerate(lines) if ANSWER_LINE.fullmatch(line)]
    if answers != [len(lines) - 1]:
        return "uncertain"
    value = ANSWER_LINE.fullmatch(lines[-1]).group(1).strip().rstrip(".").strip().lower()
    return verdicts(question).get(value, "uncertain")


class Cascade:
    def __init__(self, run, summary: dict, repo: Path, worktree: Path, policy: dict,
                 root: Path, leaf: str | None, *, transport=None, sleep=None):
        self.run, self.summary, self.repo, self.worktree = run, summary, repo, worktree
        self.policy, self.root, self.leaf = policy, root, leaf
        self.transport, self.sleep = transport, sleep
        self.registry, hashes = questions(root)
        summary["question_hashes"] = hashes
        summary.setdefault("jev_usage", {"calls": 0, "input_tokens": 0, "output_tokens": 0})
        self.counter = 0
        self.prose = {}  # judge prose per question, handed to a builder retry as the finding

    def batch(self, state: dict, ids: list[str]) -> dict[str, str]:
        """All ids sharing this state travel in one request; no builder self-attestation."""
        selected = {ident: self.registry[ident] for ident in ids}
        digest = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        config = self.policy["arbiter"]
        results = {}
        if not allowed(self.repo, config):
            failure = "repository not in external_judgment_allowed"
            answers = None
        else:
            try:
                kwargs = {"transport": self.transport}
                if self.sleep is not None:
                    kwargs["sleep"] = self.sleep
                answers, usage_data = ask(state, selected, config, **kwargs)
                totals = self.summary["jev_usage"]
                totals["calls"] += 1
                totals["input_tokens"] += usage_data.get("input_tokens", 0)
                totals["output_tokens"] += usage_data.get("output_tokens", 0)
                failure = None
            except Unavailable as error:
                answers, failure = None, str(error)
        for ident in ids:
            answer = answers[ident] if answers else None
            try:
                decision = classify(answer, config) if answer else {"outcome": "uncertain", "confidence": None, "threshold": None}
            except Unavailable as error:
                decision, failure = {"outcome": "uncertain", "confidence": None, "threshold": None}, str(error)
            record = {"question": ident, "state_sha256": digest, "question_sha256": self.summary["question_hashes"][ident],
                      "answer": answer, "decision": decision, "arbiter": "unavailable" if failure else "observed",
                      "unavailability": failure}
            _append(self.run.path / "judgments.jsonl", record)
            self.run.event("judgment", question=ident, state_sha256=digest, outcome=decision["outcome"])
            outcome = decision["outcome"]
            if outcome == "uncertain" and self.summary["status"] != "gated":
                outcome = self.judge(ident, state, decision, failure)
            results[ident] = outcome
        return results

    def judge(self, ident: str, state: dict, prior: dict, failure: str | None) -> str:
        # semantic_gates may create a new Cascade after a directed builder retry.
        # Allocate against this run's on-disk sessions and receipts, not just this
        # instance's counter; never overwrite a partial or completed judge.
        while True:
            self.counter += 1
            name = f"judge-{self.counter}"
            if (name not in self.summary["receipts"]
                    and f"{name}-prose" not in self.summary["receipts"]
                    and not (self.run.path / "sessions" / name).exists()
                    and not (self.run.path / "receipts" / f"{name}.json").exists()
                    and not (self.run.path / "receipts" / f"{name}-prose.md").exists()):
                break
        template = (self.root / "prompts" / "judge.md").read_text(encoding="utf-8")
        question = self.registry[ident]
        directory = self.worktree / ".ticket-driver"
        directory.mkdir(exist_ok=True)
        # The state is a file, not argv: a diff plus a receipt can pass Windows' command-line limit.
        state_bytes = json.dumps(state, sort_keys=True, ensure_ascii=False, indent=1).encode("utf-8")
        state_digest = hashlib.sha256(state_bytes).hexdigest()
        state_file = directory / "judge-state.json"
        prompt = (template.replace("{question_id}", ident).replace("{question}", question["instructions"])
                  .replace("{verdicts}", render_verdicts(question))
                  .replace("{state_file}", ".ticket-driver/judge-state.json").replace("{state_sha256}", state_digest))
        session = self.run.path / "sessions" / name
        state_file.write_bytes(state_bytes)
        try:
            argv, out, err, code, duration, problem = invoke(self.leaf, self.policy, session, prompt, self.worktree)
        finally:
            state_file.unlink(missing_ok=True)
        visible = argv[:-1] + ["<prompt:sha256:" + hashlib.sha256(prompt.encode()).hexdigest() + ">"]
        self.summary["receipts"][name] = self.run.receipt(name, visible, self.worktree,
            (out, err, code, duration, problem), max_bytes=self.policy["max_output_bytes"])
        self.summary["leaves"][name] = usage(session)
        artifact = directory / "judge.md"
        prose = artifact.read_text(encoding="utf-8") if code == 0 and artifact.is_file() else "judge unavailable"
        if artifact.is_file():
            self.summary["receipts"][f"{name}-prose"] = self.run.authored_receipt(f"{name}-prose", artifact)
            artifact.unlink()
        outcome = _judge_answer(question, prose)
        self.prose[ident] = prose[:4096]
        _append(self.run.path / "escalations.jsonl", {"question": ident, "prior": prior,
            "judge_state_sha256": state_digest,
            "arbiter_unavailability": failure, "judge_prose": prose[:4096], "outcome": outcome})
        if outcome == "uncertain":
            reason = f"{ident}: probability/confidence={prior}; judge={prose[:512]}"
            self.summary["status"], self.summary["failure"] = "gated", reason
            self.run.event("gate", question=ident, reason=reason)
            _append(self.run.path / "gates.jsonl", {"question": ident, "reason": reason, "status": "open"})
        return outcome
