"""delivery-bench profile report: five axes side by side, no single number, no hidden check names.

    python -B profile_report.py --lot DIR [--base bare] [--through L] [--rep R ...] [--json]

Reads the cell records a lot wrote (``cells/*/cell.json``). Axes (contract §5, Decision 7):
acceptance (the judged request's features), robustness (latent defects found), compass
(invariants broken, traps violated with their distance), cost (Pi's token and USD estimates, Jev
apart) and time. Cells whose audit found hidden material are left out and listed. Acceptance is
also compared pairwise with the base arm per (scenario, repetition, request) by McNemar's exact
test with Holm correction; an arm is ``better``/``worse`` only when the difference exceeds 3 and
the adjusted p is below 0.05 (the TBA-03 rule). The Markdown never names a hidden check: only
counts, trap types and distances.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from math import comb
from pathlib import Path

ARMS = ("bare", "skills-only", "autopilot", "driver-c1a", "driver-c3a")
# Ties go to the simpler arm (TBA-03); Autopilot is the heaviest way of working.
SIMPLICITY = ("bare", "skills-only", "driver-c1a", "driver-c3a", "autopilot")
USAGE = ("input", "output", "cacheRead", "cacheWrite", "cost_usd")


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p on the discordant pairs (from TBA-03 arm_comparison.py)."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=lambda k: pvalues[k])
    adjusted, running = {}, 0.0
    for i, key in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - i) * pvalues[key]))
        adjusted[key] = round(running, 12)
    return adjusted


def load_cells(lot_dir: Path, *, through: int | None = None, reps: list[int] | None = None) -> list[dict]:
    """Cell records, optionally cut to a chain length and to some repetitions.

    A chain of length L is a cell brought to L requests (the rest are prefixes of it, contract §9);
    a cell that stopped earlier on the time cap, an error or the audit stays in, as it ended.
    """
    cells = []
    for path in sorted(Path(lot_dir).glob("cells/*/cell.json")):
        cell = json.loads(path.read_text(encoding="utf-8"))
        if reps and cell["rep"] not in reps:
            continue
        if through:
            stopped = cell.get("chain_cap_hit") or cell.get("invalid") or cell.get("error")
            if len(cell["requests"]) < through and not stopped:
                continue
            cell["requests"] = [r for r in cell["requests"] if r["request"] <= through]
        cells.append(cell)
    return cells


def _arm_order(name: str) -> int:
    return ARMS.index(name) if name in ARMS else len(ARMS)


def _empty() -> dict:
    return {"reps": 0, "judged": 0, "accepted": 0, "features_passed": 0, "features_total": 0,
            "latent_found": 0, "latent_total": 0, "invariants_broken": 0, "invariants_total": 0,
            "traps_total": 0, "traps_violated": 0, "trap_distance": Counter(), "trap_type": Counter(),
            **{key: 0 for key in USAGE}, "jev_calls": 0, "jev_usd": 0.0, "seconds": [],
            "timeouts": 0, "infra_retries": 0, "infra_usd": 0.0, "infra_exhausted": 0,
            "judge_errors": 0, "not_delivered": 0, "driver_status": Counter(),
            "gated_judged": 0, "gated_accepted": 0}


def _add(row: dict, request: dict) -> None:
    row["reps"] += 1
    status = request.get("status")
    row["not_delivered"] += status == "not-delivered"
    row["judge_errors"] += status == "judge-error"
    axes = request.get("axes") or {}
    acceptance = axes.get("acceptance") or {}
    if status == "judged":
        row["judged"] += 1
        row["accepted"] += bool(acceptance.get("accepted"))
        row["features_passed"] += acceptance.get("passed", 0)
        row["features_total"] += acceptance.get("total", 0)
        robustness, compass = axes.get("robustness") or {}, axes.get("compass") or {}
        row["latent_found"] += robustness.get("latent_found", 0)
        row["latent_total"] += robustness.get("latent_total", 0)
        invariants = compass.get("invariants") or {}
        row["invariants_total"] += invariants.get("total", 0)
        row["invariants_broken"] += invariants.get("total", 0) - invariants.get("passed", 0)
        row["traps_total"] += compass.get("traps_total", 0)
        for trap in compass.get("traps_violated", []):
            row["traps_violated"] += 1
            row["trap_distance"][trap["distance"]] += 1
            row["trap_type"][trap["type"]] += 1
    usage = request.get("usage") or {}
    for key in USAGE:
        row[key] += usage.get(key, 0) or 0
    jev = request.get("jev") or {}
    row["jev_calls"] += jev.get("calls", 0)
    row["jev_usd"] += jev.get("usd_estimate", 0.0)
    if request.get("seconds") is not None:
        row["seconds"].append(request["seconds"])
    row["timeouts"] += bool(request.get("timed_out"))
    infra = [a for a in request.get("attempts", []) if a.get("class", "").startswith("infra:")]
    row["infra_retries"] += len(infra) - (1 if request.get("infra_exhausted") else 0)
    row["infra_usd"] += (request.get("infra_usage") or {}).get("cost_usd", 0.0)
    row["infra_exhausted"] += bool(request.get("infra_exhausted"))
    row["driver_status"].update((request.get("driver") or {}).get("status", []))
    counterfactual = request.get("counterfactual") or {}
    if counterfactual.get("status") == "judged":
        row["gated_judged"] += 1
        row["gated_accepted"] += bool(counterfactual["axes"]["acceptance"]["accepted"])


END_OF_CHAIN = ("latent_found", "latent_total", "invariants_broken", "invariants_total",
                "traps_total", "traps_violated", "trap_distance", "trap_type")
OVER_CHAIN = (*USAGE, "jev_calls", "jev_usd", "timeouts", "infra_retries", "infra_usd",
              "not_delivered", "judge_errors", "driver_status", "gated_judged", "gated_accepted")


def _chain(cell: dict) -> dict:
    """One cell as a chain: robustness and compass of the final repo, acceptance, cost and time summed."""
    requests = [r for r in cell["requests"] if r.get("status") != "running"]
    over, end = _empty(), _empty()
    for request in requests:
        _add(over, request)
    final = next((r for r in reversed(requests) if r.get("status") == "judged"), None)
    if final:
        _add(end, final)
    return {"cells": 1, "requests": over["reps"], "accepted_requests": over["accepted"],
            **{key: end[key] for key in END_OF_CHAIN}, **{key: over[key] for key in OVER_CHAIN},
            "chain_seconds": [round(sum(over["seconds"]), 3)]}


def _merge(total: dict | None, chain: dict) -> dict:
    if total is None:
        return {key: (Counter(value) if isinstance(value, Counter) else list(value) if isinstance(value, list)
                      else value) for key, value in chain.items()}
    for key, value in chain.items():
        if isinstance(value, Counter):
            total[key].update(value)
        else:
            total[key] += value
    return total


def profile(cells: list[dict]) -> dict:
    rows: dict[tuple, dict] = {}
    chains: dict[tuple, dict] = {}
    totals: dict[str, dict] = {}
    invalid, errors, capped, infra_classes = [], [], [], Counter()
    for cell in cells:
        if cell.get("invalid"):
            invalid.append({"cell": cell["cell"], "patterns": sorted({h["pattern"] for h in cell["audit_hits"]})})
            continue
        if cell.get("error"):
            errors.append({"cell": cell["cell"], "error": cell["error"]})
        if cell.get("chain_cap_hit"):
            capped.append(cell["cell"])
        for request in cell["requests"]:
            if request.get("status") == "running":
                continue
            key = (cell["scenario"], cell["arm"], request["request"])
            _add(rows.setdefault(key, _empty()), request)
            infra_classes.update(a["class"] for a in request.get("attempts", [])
                                 if a.get("class", "").startswith("infra:"))
        if any(r.get("status") != "running" for r in cell["requests"]):
            chain = _chain(cell)
            chains[(cell["scenario"], cell["arm"])] = _merge(chains.get((cell["scenario"], cell["arm"])), chain)
            totals[cell["arm"]] = _merge(totals.get(cell["arm"]), chain)
    order = sorted(rows, key=lambda k: (k[0], _arm_order(k[1]), k[2]))
    return {"rows": [{"scenario": s, "arm": a, "request": n, **rows[(s, a, n)]} for s, a, n in order],
            "chains": [{"scenario": s, "arm": a, **chains[(s, a)]}
                       for s, a in sorted(chains, key=lambda k: (k[0], _arm_order(k[1])))],
            "totals": [{"arm": a, **totals[a]} for a in sorted(totals, key=_arm_order)],
            "invalid": invalid, "errors": errors, "chain_cap_hit": capped,
            "infra_classes": dict(infra_classes)}


def paired(cells: list[dict], base: str = "bare") -> dict:
    outcomes: dict[str, dict] = {}
    reps: dict[str, set] = {}
    for cell in cells:
        if cell.get("invalid"):
            continue
        for request in cell["requests"]:
            if request.get("status") not in ("judged", "not-delivered"):
                continue
            accepted = bool(((request.get("axes") or {}).get("acceptance") or {}).get("accepted"))
            outcomes.setdefault(cell["arm"], {})[(cell["scenario"], cell["rep"], request["request"])] = int(accepted)
            reps.setdefault(cell["arm"], set()).add(cell["rep"])
    if base not in outcomes:
        return {"base": base, "versus": {}, "note": "no judged base-arm requests"}
    raw, versus = {}, {}
    for arm in sorted(outcomes, key=_arm_order):
        if arm == base:
            continue
        keys = sorted(set(outcomes[arm]) & set(outcomes[base]))
        only_arm = sum(1 for k in keys if outcomes[arm][k] and not outcomes[base][k])
        only_base = sum(1 for k in keys if outcomes[base][k] and not outcomes[arm][k])
        raw[arm] = mcnemar_exact(only_arm, only_base)
        versus[arm] = {"pairs": len(keys), "arm_accepted": sum(outcomes[arm][k] for k in keys),
                       "base_accepted": sum(outcomes[base][k] for k in keys), "only_arm": only_arm,
                       "only_base": only_base, "difference": only_arm - only_base, "p": raw[arm],
                       "repetitions": min(len(reps[arm]), len(reps[base]))}
    adjusted = holm(raw) if raw else {}
    for arm, row in versus.items():
        row["p_holm"] = adjusted[arm]
        if abs(row["difference"]) > 3 and row["p_holm"] < 0.05:
            row["decision"] = "better" if row["difference"] > 0 else "worse"
        else:
            row["decision"] = "repeat" if row["repetitions"] < 2 else "indistinguishable"
    # Rates, not totals: extra repetitions go only to some arms, so coverage can differ.
    rate = {arm: sum(values.values()) / len(values) for arm, values in outcomes.items()}
    rank = lambda arm: (-rate[arm], SIMPLICITY.index(arm) if arm in SIMPLICITY else 99)
    provisional = min([base] + [a for a, r in versus.items() if r["decision"] == "better"], key=rank)
    blocking = [a for a, r in versus.items()
                if r["decision"] == "repeat" and rate[a] >= rate[provisional]]
    return {"base": base, "versus": versus, "acceptance_rate": rate,
            "winner": None if blocking else provisional, "repeat_needed": blocking}


def _histogram(counter: Counter, prefix: str = "") -> str:
    return ", ".join(f"{prefix}{key}×{counter[key]}" for key in sorted(counter)) or "—"


def _row(label: list[str], r: dict) -> str:
    seconds = f"{statistics.median(r['seconds']):.0f}" if r["seconds"] else "—"
    latent = f"{r['latent_found']}/{r['latent_total']}" if r["latent_total"] else "—"
    traps = f"{r['traps_violated']}/{r['traps_total']}" if r["traps_total"] else "—"
    return "| " + " | ".join(label + [
        f"{r['accepted']}/{r['reps']}", f"{r['features_passed']}/{r['features_total']}", latent,
        f"{r['invariants_broken']}/{r['invariants_total']}", traps, _histogram(r["trap_distance"], "d"),
        f"{r['input'] / 1000:.0f}k / {r['output'] / 1000:.0f}k / {r['cacheRead'] / 1000:.0f}k",
        f"{r['cost_usd']:.2f}", f"{r['jev_usd']:.4f}" if r["jev_calls"] else "—", seconds,
        str(r["timeouts"]), f"{r['infra_retries']} ({r['infra_usd']:.2f})"]) + " |"


HEADER = ("| Accepted | Features | Latent found | Invariants broken | Traps violated | Distances "
          "| Tokens in / out / cache read | USD (Pi) | USD (Jev) | Median s | Timeouts | Infra retries (USD) |")
CHAIN_HEADER = ("| Cells | Accepted requests | Latent found (end) | Invariants broken (end) "
                "| Traps violated (end) | Distances | USD (Pi) | USD (Jev) | Median chain s | Timeouts "
                "| Infra retries (USD) |")


def _chain_row(label: list[str], c: dict) -> str:
    latent = f"{c['latent_found']}/{c['latent_total']}" if c["latent_total"] else "—"
    traps = f"{c['traps_violated']}/{c['traps_total']}" if c["traps_total"] else "—"
    return "| " + " | ".join(label + [
        str(c["cells"]), f"{c['accepted_requests']}/{c['requests']}", latent,
        f"{c['invariants_broken']}/{c['invariants_total']}", traps, _histogram(c["trap_distance"], "d"),
        f"{c['cost_usd']:.2f}", f"{c['jev_usd']:.4f}" if c["jev_calls"] else "—",
        f"{statistics.median(c['chain_seconds']):.0f}", str(c["timeouts"]),
        f"{c['infra_retries']} ({c['infra_usd']:.2f})"]) + " |"


def render(prof: dict, comparison: dict) -> str:
    lines = ["## Profile per request", "",
             "| Scenario | Arm | Request " + HEADER, "|---|---|---:" + "|---:" * 12 + "|"]
    lines += [_row([r["scenario"], r["arm"], str(r["request"])], r) for r in prof["rows"]]
    lines += ["", "## Chains", "",
              ("Robustness and compass are read on the final repository of each chain (they are "
               "cumulative); acceptance counts accepted requests; cost and time are summed over the chain."),
              "", "| Scenario | Arm " + CHAIN_HEADER, "|---|---" + "|---:" * 11 + "|"]
    lines += [_chain_row([c["scenario"], c["arm"]], c) for c in prof["chains"]]
    lines += ["", "## Per arm, all scenarios", "", "| Arm " + CHAIN_HEADER, "|---" + "|---:" * 11 + "|"]
    lines += [_chain_row([r["arm"]], r) for r in prof["totals"]]
    lines += ["", "Violated trap types per arm: " + "; ".join(
        f"{r['arm']}: {_histogram(r['trap_type'])}" for r in prof["totals"]) + ".", "",
        f"## Acceptance paired with `{comparison['base']}`", ""]
    if comparison["versus"]:
        lines += [("| Arm | Pairs | Arm accepted | Base accepted | Only arm | Only base | Difference "
                   "| McNemar p | Holm p | Decision |"), "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
        for arm, v in comparison["versus"].items():
            lines.append(f"| {arm} | {v['pairs']} | {v['arm_accepted']} | {v['base_accepted']} | "
                         f"{v['only_arm']} | {v['only_base']} | {v['difference']:+d} | {v['p']:.4g} | "
                         f"{v['p_holm']:.4g} | {v['decision']} |")
        winner = comparison["winner"] or "undecided, repeat " + ", ".join(comparison["repeat_needed"])
        lines += ["", (f"Acceptance rule of TBA-03 (ties to the simpler arm): **{winner}**. It reads one "
                       "axis; the choice of an arm reads all five.")]
    else:
        lines.append(comparison.get("note", "no comparison"))
    drivers = [r for r in prof["rows"] if r["driver_status"]]
    if drivers:
        lines += ["", "## Driver outcomes", "",
                  ("A `gated` run stopped on an uncertain semantic gate and waits for a human; nothing is "
                   "integrated. Its candidate is judged apart (counterfactual, never counted as acceptance)."),
                  "", "| Scenario | Arm | Request | Runs by status | Gated candidates accepted |",
                  "|---|---|---:|---|---:|"]
        lines += [f"| {r['scenario']} | {r['arm']} | {r['request']} | {_histogram(r['driver_status'])} | "
                  + (f"{r['gated_accepted']}/{r['gated_judged']}" if r["gated_judged"] else "—") + " |"
                  for r in drivers]
    lines += ["", "## Harness and validity", "",
              f"- Infrastructure attempts by class: {json.dumps(prof['infra_classes'], sort_keys=True)}",
              f"- Cells invalidated by the audit: {prof['invalid'] or 'none'}",
              f"- Cells stopped by an error: {prof['errors'] or 'none'}",
              f"- Cells that hit the chain time cap: {prof['chain_cap_hit'] or 'none'}"]
    return "\n".join(lines) + "\n"


def report(lot_dir: Path, base: str = "bare", *, through: int | None = None,
           reps: list[int] | None = None) -> tuple[dict, dict, str]:
    cells = load_cells(lot_dir, through=through, reps=reps)
    prof, comparison = profile(cells), paired(cells, base)
    return prof, comparison, render(prof, comparison)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lot", required=True)
    parser.add_argument("--base", default="bare")
    parser.add_argument("--through", type=int, help="cut every chain to its first L requests")
    parser.add_argument("--rep", type=int, action="append", help="only these repetitions (repeatable)")
    parser.add_argument("--json", action="store_true", help="aggregates as JSON (still no check names)")
    args = parser.parse_args(argv)
    prof, comparison, text = report(Path(args.lot), args.base, through=args.through, reps=args.rep)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.json:
        print(json.dumps({"profile": prof, "paired": comparison}, indent=1, sort_keys=True, default=dict))
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
