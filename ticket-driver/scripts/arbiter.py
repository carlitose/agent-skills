"""Typed Jev questions over a single exact state; secret stays in request headers only."""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


class Unavailable(RuntimeError):
    pass


def questions(root: Path) -> tuple[dict, dict]:
    result, hashes = {}, {}
    for path in sorted((root / "questions").glob("*.json")):
        raw = path.read_bytes()
        question = json.loads(raw)
        if question.get("id") != path.stem or question.get("type") not in ("noul", "choice", "score"):
            raise ValueError(f"invalid question: {path.name}")
        hashes[question["id"]] = hashlib.sha256(raw).hexdigest()
        result[question["id"]] = {k: v for k, v in question.items() if k != "id"}
    return result, hashes


def allowed(repo: Path, policy: dict) -> bool:
    """Exact agent-skills root or canonical seeded benchmark project; not a generic remote slug."""
    repo = repo.resolve()
    rule = policy["external_judgment_allowed"]
    if any(repo == Path(folder).expanduser().resolve() for folder in rule["repository_roots"]):
        return True
    bench = Path(rule["benchmark_root"]).expanduser().resolve()
    return (repo.parent.parent == bench and repo.name == "project"
            and repo.parent.name.startswith("driver-") and (repo / "billing" / "money.py").is_file()
            and (repo / "TASK.md").is_file())


def ask(state: dict, selected: dict, policy: dict, *, transport=None, sleep=time.sleep) -> tuple[dict, dict]:
    """One request for all selected questions on one state; never return raw HTTP diagnostics."""
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise Unavailable("key absent")
    endpoint = policy["endpoint"]
    if endpoint != "https://api.typesafe.ai/v1/systemone" and not endpoint.startswith("http://127.0.0.1:"):
        raise Unavailable("untrusted arbiter endpoint")
    payload = json.dumps({"state": state, "model": policy["model"], "questions": selected}, ensure_ascii=False).encode()
    req = urllib.request.Request(endpoint, data=payload, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    opener = transport or urllib.request.urlopen
    for attempt in range(policy["max_attempts"]):
        try:
            with opener(req, timeout=policy["timeout_seconds"]) as response:
                result = json.load(response)
            answers = result.get("answers", {})
            if set(answers) != set(selected) or not isinstance(result.get("usage"), dict):
                raise Unavailable("malformed answer map")
            if any(type(result["usage"].get(key)) is not int or result["usage"][key] < 0
                   for key in ("input_tokens", "output_tokens")):
                raise Unavailable("invalid usage")
            for ident, question in selected.items():
                answer = answers[ident]
                if answer.get("type") != question["type"]:
                    raise Unavailable("answer type mismatch")
                if question["type"] == "choice" and set(answer.get("probabilities", {})) != set(question["criteria"]):
                    raise Unavailable("choice probabilities do not cover criteria")
                if question["type"] == "score" and set(answer.get("probabilities", {})) != {str(i) for i in range(len(question["criteria"]))}:
                    raise Unavailable("score probabilities do not cover criteria")
            return answers, result["usage"]
        except urllib.error.HTTPError as error:
            if error.code not in (429, 529) or attempt + 1 >= policy["max_attempts"]:
                raise Unavailable(f"HTTP {error.code}") from None
            sleep(min(0.25 * 2**attempt, 1.0))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError) as error:
            raise Unavailable("network or invalid response") from None
    raise Unavailable("retry budget exhausted")


def classify(answer: dict, policy: dict) -> dict:
    """Policy bands are initial guesses, never calibrated probabilities."""
    kind = answer["type"]
    if kind == "noul":
        probability = answer.get("noul")
        if type(probability) not in (float, int) or not 0 <= probability <= 1:
            raise Unavailable("invalid noul probability")
        outcome = "yes" if probability >= policy["noul_high"] else "no" if probability <= policy["noul_low"] else "uncertain"
        return {"outcome": outcome, "probability": probability, "confidence": max(probability, 1-probability),
                "threshold": [policy["noul_low"], policy["noul_high"]]}
    probabilities = answer.get("probabilities")
    confidence = answer.get("confidence")
    if (not isinstance(probabilities, dict) or not probabilities
            or any(type(value) not in (float, int) or not 0 <= value <= 1 for value in probabilities.values())
            or abs(sum(probabilities.values()) - 1) > 0.05
            or type(confidence) not in (float, int) or not 0 <= confidence <= 1):
        raise Unavailable("invalid distribution")
    choice = answer.get("choice") if kind == "choice" else answer.get("score")
    if kind == "choice" and (choice not in probabilities or probabilities[choice] < max(probabilities.values()) - 1e-6):
        raise Unavailable("choice missing or inconsistent with distribution")
    if kind == "score" and not isinstance(choice, (float, int)):
        raise Unavailable("score missing")
    return {"outcome": choice if confidence >= policy["choice_min_confidence"] else "uncertain",
            "probabilities": probabilities, "confidence": confidence,
            "threshold": policy["choice_min_confidence"]}
