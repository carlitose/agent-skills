"""delivery-bench judge: run a scenario's hidden suite against a delivered repo, untouched.

    python -B judge.py --project P --scenario S --request N --out RESULT.json

The scenario directory lives in the private oracle repository, outside every checkout an arm
can read. It holds ``scenario.json`` and ``hidden/``. The delivered project is bind-mounted
read-only into a container without network; the judge takes a digest of the whole project
tree (``.git`` included) before and after, and a record whose digests differ is invalid.
The hidden suite writes ``/out/result.json``; the judge validates it and derives the axes the
suite can see (acceptance, robustness, compass). Cost and time are added by the runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

KINDS = ("feature", "latent", "invariant", "trap")
STATUSES = ("pass", "fail", "error")
TRAP_TYPES = ("deprecated", "architecture", "closed-bug", "contract", "convention")
DETAIL_LIMIT = 2000


class JudgeError(RuntimeError):
    """The judgement is unusable: bad scenario, container failure or tampering."""


def tree_digest(root: Path) -> dict:
    """Digest every file under root, symlinks by target; order and content both count."""
    root = Path(root)
    entries = []
    for directory, subdirs, files in os.walk(root, followlinks=False):
        subdirs.sort()
        base = Path(directory)
        for name in sorted(files) + sorted(d for d in subdirs if (base / d).is_symlink()):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                entries.append(f"L {relative} {os.readlink(path)}")
                continue
            digest = hashlib.sha256()
            with open(path, "rb") as handle:
                for block in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(block)
            entries.append(f"F {relative} {digest.hexdigest()}")
    body = "\n".join(entries).encode("utf-8")
    return {"sha256": hashlib.sha256(body).hexdigest(), "files": len(entries)}


def load_scenario(scenario: Path) -> dict:
    document = json.loads((scenario / "scenario.json").read_text(encoding="utf-8"))
    required = {"schema", "id", "image", "command", "requests", "timeout_seconds"}
    if not isinstance(document, dict) or not required <= set(document) or document["schema"] != 1:
        raise JudgeError("scenario.json lacks schema 1 fields")
    if (not isinstance(document["command"], list) or not document["command"]
            or type(document["requests"]) is not int or document["requests"] < 1):
        raise JudgeError("scenario command or request count is invalid")
    if not (scenario / "hidden").is_dir():
        raise JudgeError("scenario has no hidden suite")
    return document


def docker_argv(scenario_doc: dict, project: Path, hidden: Path, out_dir: Path,
                request: int, name: str) -> list[str]:
    def mount(source: Path, target: str, readonly: bool) -> list[str]:
        spec = f"type=bind,source={Path(source).resolve()},target={target}"
        return ["--mount", spec + (",readonly" if readonly else "")]
    return ["docker", "run", "--rm", "--name", name, "--network", "none",
            "--cpus", str(scenario_doc.get("cpus", 2)), "--memory", scenario_doc.get("memory", "2g"),
            "--pids-limit", "1024", "-e", f"DBENCH_REQUEST={request}",
            *mount(project, "/repo", True), *mount(hidden, "/hidden", True),
            *mount(out_dir, "/out", False),
            scenario_doc["image"], *scenario_doc["command"], "--request", str(request)]


def docker_runner(argv: list[str], timeout: int, name: str) -> dict:
    started = time.monotonic()
    try:
        done = subprocess.run(argv, capture_output=True, timeout=timeout, check=False)
        code, out, err = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as expiry:
        subprocess.run(["docker", "kill", name], capture_output=True, check=False, timeout=60)
        code, out, err = None, expiry.stdout or b"", b"judge timeout"
    return {"exit_code": code, "seconds": round(time.monotonic() - started, 3),
            "stdout_tail": out.decode("utf-8", "replace")[-DETAIL_LIMIT:],
            "stderr_tail": err.decode("utf-8", "replace")[-DETAIL_LIMIT:]}


def validate_result(document: object, scenario_id: str, request: int) -> list[dict]:
    if (not isinstance(document, dict) or document.get("schema") != 1
            or document.get("scenario") != scenario_id or document.get("request") != request
            or not isinstance(document.get("checks"), list)):
        raise JudgeError("hidden suite result is not schema 1 for this scenario and request")
    seen, checks = set(), []
    for check in document["checks"]:
        if (not isinstance(check, dict) or not isinstance(check.get("id"), str)
                or check.get("kind") not in KINDS or check.get("status") not in STATUSES
                or type(check.get("request")) is not int or not 1 <= check["request"] <= request
                or check["id"] in seen):
            raise JudgeError(f"invalid check record: {str(check)[:200]}")
        trap = check.get("trap")
        if check["kind"] == "trap" and (
                not isinstance(trap, dict) or trap.get("type") not in TRAP_TYPES
                or type(trap.get("rule")) is not int or type(trap.get("temptation")) is not int
                or not trap["rule"] < trap["temptation"] <= request
                or trap.get("distance") != trap["temptation"] - trap["rule"]):
            raise JudgeError(f"invalid trap metadata on {check['id']}")
        seen.add(check["id"])
        checks.append({**check, "detail": str(check.get("detail", ""))[:DETAIL_LIMIT]})
    if not any(c["kind"] == "feature" and c["request"] == request for c in checks):
        raise JudgeError("no acceptance check for the judged request")
    return checks


def axes(checks: list[dict], request: int) -> dict:
    def tally(selected: list[dict]) -> dict:
        passed = sum(1 for c in selected if c["status"] == "pass")
        return {"passed": passed, "total": len(selected),
                "failed": sorted(c["id"] for c in selected if c["status"] != "pass")}
    feature = tally([c for c in checks if c["kind"] == "feature" and c["request"] == request])
    latent = tally([c for c in checks if c["kind"] == "latent"])
    invariants = tally([c for c in checks if c["kind"] == "invariant"])
    traps = [c for c in checks if c["kind"] == "trap"]
    violated = [{"id": c["id"], **c["trap"]} for c in traps if c["status"] != "pass"]
    return {
        "acceptance": {**feature, "accepted": feature["passed"] == feature["total"]},
        "robustness": {"latent_found": latent["passed"], "latent_total": latent["total"],
                       "missed": latent["failed"]},
        "compass": {"invariants": invariants, "traps_total": len(traps),
                    "traps_violated": sorted(violated, key=lambda v: v["id"])},
    }


def judge(project: Path, scenario: Path, request: int, *, runner=docker_runner) -> dict:
    project, scenario = Path(project).resolve(), Path(scenario).resolve()
    doc = load_scenario(scenario)
    if not 1 <= request <= doc["requests"]:
        raise JudgeError("request outside the scenario chain")
    if project == scenario or project.is_relative_to(scenario) or scenario.is_relative_to(project):
        raise JudgeError("the hidden suite must live outside the delivered project")
    before = tree_digest(project)
    with tempfile.TemporaryDirectory(prefix="dbench-judge-") as scratch:
        out_dir = Path(scratch)
        name = f"dbench-judge-{uuid.uuid4().hex[:12]}"
        argv = docker_argv(doc, project, scenario / "hidden", out_dir, request, name)
        run = runner(argv, int(doc["timeout_seconds"]), name)
        result_path = out_dir / "result.json"
        raw = result_path.read_bytes() if result_path.is_file() else None
    after = tree_digest(project)
    record = {"schema": 1, "scenario": doc["id"], "request": request, "project": str(project),
              "image": doc["image"], "suite_sha256": tree_digest(scenario / "hidden")["sha256"],
              "tree_before": before, "tree_after": after,
              "identical": before["sha256"] == after["sha256"], "container": run}
    if not record["identical"]:
        raise JudgeError("delivered project changed during judgement")
    if raw is None:
        raise JudgeError(f"hidden suite wrote no result (exit {run['exit_code']})")
    checks = validate_result(json.loads(raw.decode("utf-8")), doc["id"], request)
    record.update(checks=checks, axes=axes(checks, request))
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--request", required=True, type=int)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    try:
        record = judge(Path(args.project), Path(args.scenario), args.request)
    except JudgeError as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({"ok": True, "out": str(out), "axes": record["axes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
