"""The simulated user of a vague-request lot (DBH-38): it answers the arm's `ask_user` questions.

    python -B simulator.py ask    # the question as JSON on stdin, the answer as JSON on stdout

The `ask_user` extension runs this with ``DBENCH_ASK_USER`` naming the attempt's config file,
which the runner writes into the lot folder. The simulated user is another model in a session of
its own: it sees the precise requests of the chain (its brief) and the question, never the arm,
the arm's code or the lot. A question asked before about the same request, in any arm or
repetition, gets the stored answer without a new call; an answer that names a hidden test file or
the canary is replaced and recorded. Spec: docs/specs/delivery-bench-hard-vague-requests.md.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import secrets
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

ENV = "DBENCH_ASK_USER"
LIMIT = 10
UNKNOWN = "No lo sé, decide tú."
LIMIT_TEXT = ("Ya no puedes hacer más preguntas sobre este encargo: sigue con lo que sabes y decide tú "
              "lo que falte.")
SYSTEM = (
    "Eres la persona que ha encargado un trabajo a un desarrollador. Abajo tienes lo que quieres, "
    "con todo detalle: el encargo actual y los anteriores de la misma serie, que recuerdas. El "
    "desarrollador solo ha recibido una versión corta del encargo actual y te hace una pregunta.\n"
    "Reglas:\n"
    "- Responde como esa persona, en español, breve y directo, solo a lo que se pregunta, con los datos "
    "de tus encargos (nombres, mensajes de error y comportamientos exactos cuando te los piden).\n"
    "- No escribas código, no propongas soluciones ni cómo implementarlo, no añadas requisitos que no "
    "te han preguntado y no inventes nada que no esté en tus encargos.\n"
    "- Si tus encargos no dicen nada de lo que se pregunta, responde exactamente: " + UNKNOWN + "\n"
    "- No sabes quién te pregunta y respondes igual a cualquiera.")
RETRY_SECONDS = (5.0, 30.0, 120.0)
LOCK_STALE_SECONDS = 900.0
CALL_SECONDS = 600.0
pause = time.sleep  # the one wait the tests record instead of sleeping


class SimulatorError(RuntimeError):
    """The simulated user could not answer: the provider failed after every retry."""


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def normalize(question: str) -> str:
    return re.sub(r"\s+", " ", question).strip().lower()


def brief(paths: list) -> str:
    parts = []
    for number, path in enumerate(paths, 1):
        label = "Encargo actual" if number == len(paths) else f"Encargo anterior {number}"
        parts.append(f"## {label}\n\n{Path(path).read_text(encoding='utf-8').strip()}")
    return "\n\n".join(parts)


def leaks(answer: str, forbidden: list) -> list:
    low = answer.lower()
    return sorted({item for item in forbidden if item and item.lower() in low})


@contextmanager
def file_lock(target: Path):
    """One writer per cache file across the lot's parallel cells; a lock older than 15 min is stale."""
    lock = Path(str(target) + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(handle, str(os.getpid()).encode())
            os.close(handle)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > LOCK_STALE_SECONDS:
                    lock.unlink()
                    continue
            except FileNotFoundError:
                continue
            time.sleep(0.2)
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def call_model(config: dict, text: str) -> dict:
    """One Pi call in its own session folder, no tools, no extensions, no skills."""
    import runner  # its session reader; imported late, runner imports this module

    if len(text) + len(SYSTEM) > 30000:  # Windows caps a command line at 32767 characters
        raise SimulatorError("the brief is too long for one command line")

    sessions = Path(config["sessions"]) / f"{time.strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(3)}"
    sessions.mkdir(parents=True)
    argv = [*config["pi_command"], "-p", "--provider", config["provider"], "--model", config["model"],
            "--thinking", config["thinking"], "--no-tools", "--no-extensions", "--no-skills",
            "--no-context-files", "--no-prompt-templates", "--system-prompt", SYSTEM,
            "--session-dir", str(sessions), "--", text]
    env = {key: value for key, value in os.environ.items() if key != ENV and not key.startswith("PI_CODING_AGENT")}
    done = subprocess.run(argv, cwd=sessions, env=env, capture_output=True, timeout=CALL_SECONDS,
                          stdin=subprocess.DEVNULL, check=False)
    summary = runner.summarize(runner.new_events([sessions], {}))
    answer = done.stdout.decode("utf-8", "replace").strip()
    if done.returncode != 0 or not answer or summary["last_stop"] == "error":
        raise SimulatorError(f"exit {done.returncode}: {summary['last_error'] or done.stderr[-300:]!r}")
    return {"answer": answer, "usage": summary["usage"], "session": sessions.name}


def ask(config: dict, question: str, *, model=call_model) -> dict:
    """Answer one question and append it to the attempt's log; the limit is per attempt."""
    log = Path(config["log"])
    log.parent.mkdir(parents=True, exist_ok=True)
    asked = len(log.read_text(encoding="utf-8").splitlines()) if log.is_file() else 0
    entry = {"at": now(), "question": question, "normalized": normalize(question), "cached": False,
             "rejected": [], "limited": False, "cost_usd": 0.0, "usage": None, "error": None}
    started = time.monotonic()
    if not entry["normalized"]:
        entry.update(answer="La pregunta está vacía.", limited=False)
    elif asked >= config.get("limit", LIMIT):
        entry.update(answer=LIMIT_TEXT, limited=True)
    else:
        cache_path = Path(config["cache"])
        with file_lock(cache_path):
            cache = _read_json(cache_path, {})
            if entry["normalized"] in cache:
                entry.update(answer=cache[entry["normalized"]]["answer"], cached=True,
                             rejected=cache[entry["normalized"]].get("rejected", []))
            else:
                text = (brief(config["brief"]) + "\n\n## Pregunta del desarrollador\n\n" + question.strip())
                result = None
                for wait in (*config.get("retry_seconds", RETRY_SECONDS), None):
                    try:
                        result = model(config, text)
                        break
                    except (SimulatorError, subprocess.SubprocessError, OSError) as error:
                        entry["error"] = f"{type(error).__name__}: {error}"[:500]
                        if wait is None:
                            break
                        pause(wait)
                if result is None:
                    entry.update(answer=None, seconds=round(time.monotonic() - started, 3))
                    _append(log, entry)
                    raise SimulatorError(entry["error"])
                entry["error"] = None
                answer, rejected = result["answer"], leaks(result["answer"], config.get("forbidden", []))
                entry.update(usage=result["usage"], cost_usd=result["usage"].get("cost_usd", 0.0),
                             session=result.get("session"), rejected=rejected)
                if rejected:
                    entry["rejected_answer"] = answer
                    answer = UNKNOWN
                entry["answer"] = answer
                cache[entry["normalized"]] = {"question": question, "answer": answer, "rejected": rejected,
                                              "at": entry["at"]}
                tmp = cache_path.with_suffix(".tmp")
                tmp.write_text(json.dumps(cache, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
                os.replace(tmp, cache_path)
    entry["seconds"] = round(time.monotonic() - started, 3)
    _append(log, entry)
    return entry


def _append(log: Path, entry: dict) -> None:
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def summarize_log(path: Path) -> dict:
    """What an attempt asked, for its record: counts and the simulated user's own spend."""
    entries = []
    if Path(path).is_file():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
    cost = sum(e.get("cost_usd") or 0.0 for e in entries)
    tokens = sum(((e.get("usage") or {}).get("totalTokens") or 0) for e in entries)
    return {"questions": len(entries), "cached": sum(bool(e.get("cached")) for e in entries),
            "rejected": sum(bool(e.get("rejected")) for e in entries),
            "limited": sum(bool(e.get("limited")) for e in entries),
            "errors": sum(bool(e.get("error")) for e in entries),
            "cost_usd": round(cost, 6), "total_tokens": tokens}


def main() -> int:
    if sys.argv[1:] != ["ask"]:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        config = json.loads(Path(json.loads(os.environ[ENV])["config"]).read_text(encoding="utf-8"))
        question = json.loads(sys.stdin.buffer.read().decode("utf-8"))["question"]
        entry = ask(config, str(question))
    except (KeyError, ValueError, OSError, SimulatorError) as error:
        print(json.dumps({"error": f"{type(error).__name__}: {error}"[:500]}))
        return 1
    sys.stdout.buffer.write(json.dumps({"answer": entry["answer"]}, ensure_ascii=False).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
