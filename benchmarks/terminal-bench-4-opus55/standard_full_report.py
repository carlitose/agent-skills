"""Reduce original-harness Harbor lots, including infrastructure retries, into one report.

Each lot is a Harbor job directory with at most one trial per task, given in attempt
order (the main lot first, then retry lots). Every attempt is classified by
``retry_classification``; the reported result for a task is its first non-infrastructure
attempt. Costs are summed over every attempt, including repeated ones, and remain
estimates. Nothing here opens hidden tests or rewrites receipts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from retry_classification import classify_trial, retry_plan


def _receipt(trial_dir: Path) -> dict:
    try:
        return json.loads((trial_dir / "agent/standard-receipt.json").read_text(encoding="utf8"))
    except (OSError, ValueError):
        return {}


def _trials(jobs: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for d in sorted(Path(jobs).glob("*__*")):
        if d.is_dir():
            task = d.name.split("__")[0]
            if task in found:
                raise ValueError(f"lot {jobs} has two trials for {task}")
            found[task] = d
    return found


def reduce_lots(lots: list[tuple[str, Path]], tasks: list[str]) -> dict:
    per_lot = [(name, _trials(jobs)) for name, jobs in lots]
    rows, classes, known_usd, unknown, attempts_total = [], {}, 0.0, 0, 0
    for task in tasks:
        attempts = []
        for name, trials in per_lot:
            if task in trials:
                info = classify_trial(trials[task])
                model = _receipt(trials[task]).get("model") or {}
                attempts.append({"lot": name, "class": info["class"], "reward": info["reward"],
                                 "cost": model.get("cost_usd") if model.get("known") else None,
                                 "requests": (model.get("budget") or {}).get("requests")})
                attempts_total += 1
                if model.get("known"):
                    known_usd += float(model.get("cost_usd") or 0)
                else:
                    unknown += 1
        if attempts:
            classes[task] = [a["class"] for a in attempts]
        rows.append({"task": task, "attempts": [a["class"] for a in attempts], "detail": attempts})
    plan = retry_plan(classes)
    for row in rows:
        task = row["task"]
        if not row["detail"]:
            row.update(status="not-run", final_lot=None, reward=None)
        elif task in plan["final"]:
            final = row["detail"][plan["final"][task]]
            row.update(status="scored", final_lot=final["lot"], reward=final["reward"],
                       requests=final["requests"], cost=final["cost"])
        else:
            status = ("exhausted" if task in plan["exhausted"] else
                      "review" if task in plan["review"] else "retry-pending")
            row.update(status=status, final_lot=None, reward=None)
    scored = [r for r in rows if r["status"] == "scored"]
    return {"rows": rows, "planned": len(tasks), "scored": len(scored),
            "passed": sum(1 for r in scored if r["reward"] == 1), "known_usd": known_usd,
            "unknown_cost_attempts": unknown, "attempts": attempts_total,
            "retry": plan["retry"], "exhausted": plan["exhausted"], "review": plan["review"],
            "lots": [name for name, _ in lots]}


def _fmt(value):
    if value is None:
        return "—"
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


def render_markdown(summary: dict, *, excluded: list[str], dataset_total: int) -> str:
    lines = ["| Task | Final lot | Attempts | Reward | Requests | Est. USD (final) |",
             "|---|---|---|---:|---:|---:|"]
    for row in summary["rows"]:
        cost = row.get("cost")
        lines.append(f"| {row['task']} | {row['final_lot'] or row['status']} | "
                     f"{', '.join(row['attempts']) or '—'} | {_fmt(row['reward'])} | "
                     f"{_fmt(row.get('requests'))} | {'—' if cost is None else f'{cost:.4f}'} |")
    head = (f"**Coverage:** {summary['passed']}/{summary['scored']} scored tasks passed; "
            f"{summary['scored']} of {summary['planned']} planned tasks scored, {dataset_total} in the dataset. "
            f"Excluded (lost coverage): {', '.join(excluded) or 'none'}. This is a **partial** run, not a full score.\n\n"
            f"**Attempts:** {summary['attempts']} across lots {', '.join(summary['lots'])}; "
            f"estimated known USD {summary['known_usd']:.4f} (estimates, not invoices); "
            f"{summary['unknown_cost_attempts']} attempt(s) with unknown cost. "
            f"Retry pending: {', '.join(summary['retry']) or 'none'}; exhausted: {', '.join(summary['exhausted']) or 'none'}; "
            f"manual review: {', '.join(summary['review']) or 'none'}.\n")
    return head + "\n" + "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lot", action="append", required=True, help="NAME=JOB_DIR, in attempt order")
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    manifest = json.loads((Path(__file__).with_name("manifest.json")).read_text(encoding="utf8"))
    tasks = [t["name"] for t in manifest["tasks"] if t["name"] not in args.exclude]
    lots = [(spec.split("=", 1)[0], Path(spec.split("=", 1)[1])) for spec in args.lot]
    summary = reduce_lots(lots, tasks)
    if args.json:
        print(json.dumps(summary, indent=1, sort_keys=True))
    else:
        print(render_markdown(summary, excluded=args.exclude, dataset_total=manifest["dataset_task_count"]))


if __name__ == "__main__":
    main()
