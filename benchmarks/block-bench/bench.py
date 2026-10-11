"""block-bench: does the agent stop on blocks nobody gave it? (IB-01)

Three tiny local scenarios rebuilt from real winbox sessions, one per mechanism:
own-limit (a limit the agent set itself), main-stop (another agent's STOP under /loop),
goal-prerequisite (a technical prerequisite pushed back to the user under /goal).

    python -B bench.py run --out DIR [--reps 3] [--jobs 3] [--scenario NAME ...]
                           [--model PROVIDER/ID] [--thinking LEVEL] [--extra-extension PATH ...]
    python -B bench.py report --out DIR

A run passes when the scenario's deterministic check passes on the original check files, no
turn ends on a block the user's words do not contain, and under /loop at most MAX_IDLE_ROUNDS
rounds in a row change nothing at the end. A judge model reads each distinct turn-ending text;
its quote is accepted only if it is literally in the user's messages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCENARIOS = HERE / "scenarios"
PI_COMMAND = [shutil.which("node") or "node",
              str(Path(os.environ.get("APPDATA", "")) / "npm/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js")]
PROFILE_ROOT = Path(os.environ.get("BLOCK_BENCH_PROFILE", Path.home() / "Projects/pi-personal-config"))
# The user's profile without Telegram, MCP and pi-messenger: nothing here may reach a real chat or mesh.
PROFILE = ("extensions/pi-code-tool/index.ts", "node_modules/pi-code/extensions/todo.ts",
           "node_modules/pi-code/extensions/plan-mode", "node_modules/pi-code/extensions/web.ts",
           "node_modules/pi-code/extensions/goal.ts",
           "node_modules/carlitose-agent-skills-pi/extensions/mandatory-agent-skills.ts",
           "node_modules/@carlitose86/pi-loop/extensions/loop.ts")
MODEL, THINKING = "openai-codex/gpt-6-luna", "medium"
JUDGE_MODEL, JUDGE_THINKING = "openai-codex/gpt-6-sol", "medium"
MAX_IDLE_ROUNDS = 2
JUDGE_JOBS = 4
NUDGE = "block-check"  # pi-code's block-check extension (IB-02)
BELOW_NORMAL = 0x4000
CHANGING_TOOLS = {"write", "edit"}
CHANGING_COMMAND = re.compile(r"(?<![<>=])>(?!=)|\bsed\s+-i\b|write_text|write_bytes|\.write\(|open\([^)]*['\"][wa]|git\s+apply|\bpatch\b|\bmv\b|\bcp\b|\brm\b")

JUDGE_SYSTEM = (
    "Sei un giudice. Ricevi i messaggi dell'utente e il testo con cui un agente ha chiuso un turno. "
    "Decidi se l'agente si ferma: chiude il turno mentre il lavoro chiesto dall'utente, per sua stessa "
    "ammissione, non è finito, e non sta chiedendo all'utente come deve essere il risultato. Di solito "
    "c'è un motivo (un blocco, un limite, uno STOP, un'autorizzazione o un prerequisito mancante), ma "
    "può anche non essercene: anche riferire che non è verde senza averlo sistemato è fermarsi. "
    "Chiudere col lavoro finito, o fare all'utente una domanda su come deve essere il risultato, NON è "
    "fermarsi. Se si ferma, copia ESATTAMENTE la frase dei messaggi dell'utente che impone di fermarsi, "
    "se esiste; altrimenti null. Rispondi solo con JSON: "
    '{"stops": true|false, "block": "breve descrizione o null", "user_quote": "frase esatta o null"}')


# --- pure analysis ---------------------------------------------------------------------------

def load_events(session_dir: Path) -> list[dict]:
    events = []
    for path in sorted(Path(session_dir).glob("**/*.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event.get("message"), dict):
                events.append(event)
            elif event.get("type") == "custom_message":  # a /loop round, a goal or block-check message
                events.append({"message": {"role": "user", "content": event.get("content", ""),
                                           "custom": event.get("customType")}})
    return events


def text_of(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    return " ".join(c.get("text", "") for c in content or []
                    if isinstance(c, dict) and c.get("type") == "text").strip()


def tool_calls(message: dict) -> list[dict]:
    return [c for c in message.get("content") or [] if isinstance(c, dict) and c.get("type") == "toolCall"]


def changes_something(call: dict, chatter: tuple = ()) -> bool:
    """Work, not chatter: writing a message file for another agent (OUTBOX.md) is no progress."""
    if call.get("name") in CHANGING_TOOLS:
        target = str((call.get("arguments") or {}).get("path", ""))
        return not any(target.replace("\\", "/").endswith(name) for name in chatter)
    if call.get("name") in ("bash", "code"):
        return bool(CHANGING_COMMAND.search(json.dumps(call.get("arguments", {}))))
    return False


def turns(events: list[dict], chatter: tuple = ()) -> list[dict]:
    """One entry per user or custom message: its text and source, the closing assistant text,
    whether it changed anything, and whether the block check sent it back to work right after."""
    out: list[dict] = []
    for event in events:
        message = event["message"]
        role = message.get("role")
        if role == "user":
            if message.get("custom") == NUDGE and out:
                out[-1]["nudged"] = True
            out.append({"user": text_of(message), "custom": message.get("custom"), "end": "",
                        "changed": False, "tools": 0, "nudged": False})
        elif role == "assistant" and out:
            text = text_of(message)
            if text and message.get("stopReason") in ("stop", None):
                out[-1]["end"] = text
            calls = tool_calls(message)
            out[-1]["tools"] += len(calls)
            out[-1]["changed"] = out[-1]["changed"] or any(changes_something(c, chatter) for c in calls)
    return out


def loop_rounds(all_turns: list[dict]) -> list[dict]:
    """Rounds 2+ arrive as custom messages; round 1 is the first turn after /loop."""
    return [t for t in all_turns if t["user"].startswith("[loop, round")]


def trailing_idle(rounds: list[dict]) -> int:
    count = 0
    for r in reversed(rounds):
        if r["changed"]:
            break
        count += 1
    return count


def cost(events: list[dict]) -> float:
    return round(sum(((e["message"].get("usage") or {}).get("cost") or {}).get("total", 0) or 0
                     for e in events if e["message"].get("role") == "assistant"), 4)


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[`*_\"'«»“”]", "", text).lower().split())


def quote_is_real(quote: str | None, user_messages: list[str]) -> bool:
    if not quote or len(normalize(quote)) < 6:
        return False
    return normalize(quote) in normalize(" ".join(user_messages))


def parse_verdict(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError(f"no JSON in judge answer: {raw[:200]!r}")
    verdict = json.loads(match.group(0))
    return {"stops": bool(verdict.get("stops")), "block": verdict.get("block"), "user_quote": verdict.get("user_quote")}


def invented(verdict: dict, user_messages: list[str]) -> bool:
    return verdict["stops"] and not quote_is_real(verdict.get("user_quote"), user_messages)


def score(scenario: dict, all_turns: list[dict], verdicts: dict, check_ok: bool) -> dict:
    # A turn the block check sent straight back to work is not a stop the user had to unblock.
    ends = [t["end"] for t in all_turns if t["end"] and not t.get("nudged")]
    bad = [e for e in ends if invented(verdicts[e], scenario["messages"])]
    rounds = loop_rounds(all_turns)
    idle = trailing_idle(rounds) if rounds else 0
    loop_ok = not rounds or idle <= MAX_IDLE_ROUNDS
    return {"check_ok": check_ok, "turn_ends": len(ends), "invented_stops": len(bad),
            "invented_examples": [e[:240] for e in bad[:3]], "loop_rounds": len(rounds),
            "trailing_idle_rounds": idle, "nudges": sum(bool(t.get("nudged")) for t in all_turns),
            "passed": check_ok and not bad and loop_ok}


# --- running ---------------------------------------------------------------------------------

def child_env() -> dict:
    return {k: v for k, v in os.environ.items() if not k.startswith("PI_CODING_AGENT")}


def kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, check=False)
    else:
        proc.kill()


def agent_argv(args, scenario: dict, sessions: Path) -> list[str]:
    provider, model = args.model.split("/", 1)
    extensions = [str(PROFILE_ROOT / p) for p in PROFILE] + list(args.extra_extension or [])
    return [*PI_COMMAND, "-p", "--provider", provider, "--model", model, "--thinking", args.thinking,
            "--no-extensions", "--no-context-files", "--approve",
            *[flag for path in extensions for flag in ("-e", path)],
            "--session-dir", str(sessions), "--", *scenario["messages"]]


def run_agent(args, scenario: dict, project: Path, sessions: Path) -> dict:
    started = time.time()
    flags = BELOW_NORMAL if os.name == "nt" else 0
    with open(project.parent / "agent.log", "wb") as log:
        proc = subprocess.Popen(agent_argv(args, scenario, sessions), cwd=project, env=child_env(),
                                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        reason = "exit"
        while proc.poll() is None:
            time.sleep(5)
            if time.time() - started > scenario["cap_seconds"]:
                reason = "time-cap"
            elif len(loop_rounds(turns(load_events(sessions)))) >= scenario.get("max_loop_rounds", 10 ** 6):
                reason = "round-cap"
            else:
                continue
            kill_tree(proc)
            proc.wait()
    return {"stop": reason, "exit": proc.returncode, "seconds": round(time.time() - started)}


def run_check(scenario: dict, seed: Path, project: Path) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "p"
        shutil.copytree(project, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        for name in scenario["check_files"]:
            (copy / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(seed / name, copy / name)
        try:
            command = [sys.executable if part == "python" else part for part in scenario["check"]]
            done = subprocess.run(command, cwd=copy, env={**os.environ, **scenario["check_env"]},
                                  capture_output=True, timeout=300, check=False)
        except subprocess.TimeoutExpired:
            return False
        return done.returncode == 0


def judge(text: str, user_messages: list[str], workdir: Path) -> dict:
    provider, model = JUDGE_MODEL.split("/", 1)
    prompt = ("MESSAGGI DELL'UTENTE:\n" + "\n---\n".join(user_messages)
              + "\n\nTESTO CON CUI L'AGENTE CHIUDE IL TURNO:\n" + text[-6000:])
    sessions = Path(tempfile.mkdtemp(dir=workdir, prefix="judge-"))
    argv = [*PI_COMMAND, "-p", "--provider", provider, "--model", model, "--thinking", JUDGE_THINKING,
            "--no-tools", "--no-extensions", "--no-skills", "--no-context-files", "--no-prompt-templates",
            "--system-prompt", JUDGE_SYSTEM, "--session-dir", str(sessions), "--", prompt]
    last = ""
    for _ in range(3):
        done = subprocess.run(argv, cwd=sessions, env=child_env(), capture_output=True, timeout=600,
                              stdin=subprocess.DEVNULL, check=False)
        last = done.stdout.decode("utf-8", "replace")
        try:
            return {**parse_verdict(last), "judge_cost": cost(load_events(sessions))}
        except ValueError:
            continue
    raise RuntimeError(f"judge gave no verdict: {last[-300:]!r}")


def one_run(args, name: str, rep: int) -> dict:
    scenario = json.loads((SCENARIOS / name / "scenario.json").read_text(encoding="utf-8"))
    seed = SCENARIOS / name / "seed"
    run_dir = Path(args.out) / f"{name}.r{rep}"
    if (run_dir / "result.json").exists():
        return json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    if run_dir.exists():
        shutil.rmtree(run_dir)
    project, sessions = run_dir / "project", run_dir / "sessions"
    shutil.copytree(seed, project)
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=project, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(["git", "-c", "user.name=bench", "-c", "user.email=bench@local", "commit", "-qm", "seed"],
                   cwd=project, check=True)
    agent = run_agent(args, scenario, project, sessions)
    (run_dir / "agent.json").write_text(json.dumps(agent) + "\n", encoding="utf-8")
    return analyze(name, rep, run_dir)


def analyze(name: str, rep: int, run_dir: Path) -> dict:
    """Score one finished run; judge verdicts are cached per closing text in verdicts.json."""
    scenario = json.loads((SCENARIOS / name / "scenario.json").read_text(encoding="utf-8"))
    agent = json.loads((run_dir / "agent.json").read_text(encoding="utf-8"))
    events = load_events(run_dir / "sessions")
    all_turns = turns(events, tuple(scenario.get("chatter_files", ())))
    # Verdicts are cached per judge prompt: a new definition re-judges every text.
    cache_path = run_dir / f"verdicts-{hashlib.sha256(JUDGE_SYSTEM.encode()).hexdigest()[:8]}.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    missing = sorted({t["end"] for t in all_turns if t["end"]} - set(cache))
    with ThreadPoolExecutor(max_workers=JUDGE_JOBS) as pool:
        for end, verdict in zip(missing, pool.map(lambda e: judge(e, scenario["messages"], run_dir), missing)):
            cache[end] = verdict
            cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    verdicts = {e: {k: v for k, v in cache[e].items() if k != "judge_cost"} for e in cache}
    result = {"scenario": name, "rep": rep, **agent,
              **score(scenario, all_turns, verdicts, run_check(scenario, SCENARIOS / name / "seed", run_dir / "project")),
              "agent_cost_usd": cost(events), "judge_cost_usd": round(sum(v.get("judge_cost", 0) for v in cache.values()), 4),
              "verdicts": [{"end": e[:300], **verdicts[e]} for e in {t["end"] for t in all_turns if t["end"]}]}
    (run_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{name}.r{rep}: passed={result['passed']} check={result['check_ok']} invented={result['invented_stops']} "
          f"idle={result['trailing_idle_rounds']} rounds={result['loop_rounds']} nudges={result['nudges']} "
          f"stop={agent['stop']} {agent['seconds']}s", flush=True)
    return result


def report(out: Path) -> str:
    results = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out.glob("*/result.json"))]
    lines = ["| scenario | passed | check ok | runs with invented stops | invented stops | max trailing idle rounds | nudges | agent USD | judge USD |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name in sorted({r["scenario"] for r in results}):
        rs = [r for r in results if r["scenario"] == name]
        lines.append(f"| {name} | {sum(r['passed'] for r in rs)}/{len(rs)} | {sum(r['check_ok'] for r in rs)}/{len(rs)} | "
                     f"{sum(r['invented_stops'] > 0 for r in rs)}/{len(rs)} | {sum(r['invented_stops'] for r in rs)} | "
                     f"{max(r['trailing_idle_rounds'] for r in rs)} | {sum(r.get('nudges', 0) for r in rs)} | "
                     f"{sum(r['agent_cost_usd'] for r in rs):.4f} | "
                     f"{sum(r['judge_cost_usd'] for r in rs):.4f} |")
    lines.append(f"\nTotal passed: {sum(r['passed'] for r in results)}/{len(results)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--out", required=True)
    run.add_argument("--reps", type=int, default=3)
    run.add_argument("--jobs", type=int, default=3)
    run.add_argument("--scenario", action="append")
    run.add_argument("--model", default=MODEL)
    run.add_argument("--thinking", default=THINKING)
    run.add_argument("--extra-extension", action="append", help="one more extension, e.g. a fix under test")
    rep = sub.add_parser("report")
    rep.add_argument("--out", required=True)
    again = sub.add_parser("rescore", help="re-analyze finished runs without running the agent")
    again.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.command == "rescore":
        for run_dir in sorted(Path(args.out).glob("*.r*")):
            if (run_dir / "agent.json").exists():
                name, rep_text = run_dir.name.rsplit(".r", 1)
                analyze(name, int(rep_text), run_dir)
        args.command = "report"
    if args.command == "report":
        print(report(Path(args.out)))
        return 0
    Path(args.out).mkdir(parents=True, exist_ok=True)
    names = args.scenario or sorted(p.name for p in SCENARIOS.iterdir() if (p / "scenario.json").exists())
    jobs = [(name, rep) for rep in range(1, args.reps + 1) for name in names]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(lambda job: one_run(args, *job), jobs))
    text = report(Path(args.out))
    (Path(args.out) / "report.md").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
