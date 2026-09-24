"""Typed arbitration, one fresh judge on uncertainty, then a literal human gate."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from arbiter import Unavailable, allowed, ask, classify, questions
from leaf import invoke, usage


def _append(path: Path, event: dict) -> None:
    with path.open("ab") as output:
        output.write((json.dumps(event, sort_keys=True) + "\n").encode())
        output.flush()
        os.fsync(output.fileno())


def _judge_answer(question: str, text: str) -> str:
    lower = text.lower().strip()
    if question == "review.findings_block":
        return "no" if "no findings" in lower else "yes" if "blocks integration" in lower else "uncertain"
    if question == "review.scope_complete":
        return "yes" if "all acceptance criteria are covered" in lower else "no" if "criterion is missing" in lower else "uncertain"
    if question == "verify.claim_supported":
        return "yes" if "claim is supported" in lower else "no" if "claim is unsupported" in lower else "uncertain"
    if question == "retry.recoverable":
        return "fix-in-place" if "fix in place" in lower else "needs-redesign" if "redesign" in lower else "uncertain"
    if question == "qa.evidence_class":
        return next((name for name in ("integration", "simulated", "unit", "live") if f"{name} test" in lower), "uncertain")
    return "uncertain"


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
        prompt = template.replace("{question}", self.registry[ident]["instructions"]).replace(
            "{state}", json.dumps(state, sort_keys=True, ensure_ascii=False))
        directory = self.worktree / ".ticket-driver"
        directory.mkdir(exist_ok=True)
        session = self.run.path / "sessions" / name
        argv, out, err, code, duration, problem = invoke(self.leaf, self.policy, session, prompt, self.worktree)
        visible = argv[:-1] + ["<prompt:sha256:" + hashlib.sha256(prompt.encode()).hexdigest() + ">"]
        self.summary["receipts"][name] = self.run.receipt(name, visible, self.worktree,
            (out, err, code, duration, problem), max_bytes=self.policy["max_output_bytes"])
        self.summary["leaves"][name] = usage(session)
        artifact = directory / "judge.md"
        prose = artifact.read_text(encoding="utf-8") if code == 0 and artifact.is_file() else "judge unavailable"
        if artifact.is_file():
            self.summary["receipts"][f"{name}-prose"] = self.run.authored_receipt(f"{name}-prose", artifact)
            artifact.unlink()
        outcome = _judge_answer(ident, prose)
        _append(self.run.path / "escalations.jsonl", {"question": ident, "prior": prior,
            "arbiter_unavailability": failure, "judge_prose": prose[:4096], "outcome": outcome})
        if outcome == "uncertain":
            reason = f"{ident}: probability/confidence={prior}; judge={prose[:512]}"
            self.summary["status"], self.summary["failure"] = "gated", reason
            self.run.event("gate", question=ident, reason=reason)
            _append(self.run.path / "gates.jsonl", {"question": ident, "reason": reason, "status": "open"})
        return outcome
