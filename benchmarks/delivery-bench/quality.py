"""delivery-bench quality judging beyond the hidden tests (DBH-28..32).

    python -B quality.py units --lot DIR [--lot DIR ...]
    python -B quality.py materialize --lot DIR --unit ID [--dest DIR]
    python -B quality.py report --lot DIR [--lot DIR ...] [--out DIR]

Spec: docs/specs/delivery-bench-hard-quality-judge.md. A unit is one request of one cell. The
official verdict stays the hidden tests: this script only reads ``cells/*/cell.json``, the
per-request diffs and their object stores, and writes nothing outside ``<lot>/quality/``.
Robustness and compass are the judge's own axes, re-read here; the Markdown never names a
hidden check, only counts. Coverage, mutation and the blind review fill their columns once
their records exist under ``quality/<measure>/<unit>.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import statistics
import subprocess
import sys
import tarfile
import tempfile
from collections import defaultdict
from pathlib import Path

MEASURES = ("coverage", "mutation", "review")


def unit_id(lot: str, cell: str, request: int) -> str:
    """A neutral name: it says nothing about the arm, so a tree can be shown to a blind reviewer."""
    return hashlib.sha256(f"{lot}\0{cell}\0{request}".encode()).hexdigest()[:12]


def units(lot_dir: Path) -> list[dict]:
    """Every request of every cell, judged or not, with or without code."""
    lot_dir = Path(lot_dir)
    found = []
    for record in sorted((lot_dir / "cells").glob("*/cell.json")):
        cell = json.loads(record.read_text(encoding="utf-8"))
        lot = cell.get("lot") or lot_dir.name
        for request in cell.get("requests", []):
            diff, axes = request.get("diff") or {}, request.get("axes") or {}
            found.append({
                "unit": unit_id(lot, record.parent.name, request["request"]),
                "lot": lot, "cell": record.parent.name, "arm": cell["arm"], "scenario": cell["scenario"],
                "rep": cell.get("rep"), "request": request["request"], "status": request.get("status"),
                "base": diff.get("base"), "tree": diff.get("tree"), "diff": diff.get("path"),
                "diff_bytes": diff.get("bytes", 0), "files": diff.get("files", []),
                "code": bool(diff.get("tree") and diff.get("bytes")),
                "accepted": (axes.get("acceptance") or {}).get("accepted"),
                "robustness": axes.get("robustness"), "compass": axes.get("compass"),
            })
    return found


def object_dirs(lot_dir: Path, cell: str) -> list[Path]:
    """Where a unit's objects live. The runner now packs every object of both trees into the diff
    store; in lots run before that, the store kept only objects the arm's repository lacked and the
    cell snapshot predates the last request, so the arm's own repository (``lot.json`` ``arm_dir``)
    is still needed for work those arms committed in their last request."""
    lot_dir, cell_dir = Path(lot_dir), Path(lot_dir) / "cells" / cell
    candidates = [cell_dir / "diffs" / "objects", cell_dir / "snapshot" / "project" / ".git" / "objects",
                  cell_dir / "snapshot" / "origin.git" / "objects"]
    lot_record = lot_dir / "lot.json"
    if lot_record.is_file():
        arm_dir = (json.loads(lot_record.read_text(encoding="utf-8")).get("cells", {}).get(cell) or {}).get("arm_dir")
        if arm_dir:
            candidates.append(Path(arm_dir) / "project" / ".git" / "objects")
    return [path for path in candidates if path.is_dir()]


def _git(args: list[str], git_dir: Path, alternates: list[Path]) -> bytes:
    env = {**os.environ, "GIT_DIR": str(git_dir),
           "GIT_ALTERNATE_OBJECT_DIRECTORIES": os.pathsep.join(str(p.resolve()) for p in alternates)}
    # autocrlf off: the archive must carry the bytes the arm wrote, whatever the host default.
    return subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.quotepath=false", *args],
                          env=env, capture_output=True, check=True, timeout=600).stdout


def git_read(lot_dir: Path, cell: str, args: list[str]) -> bytes:
    """A read-only Git command over the cell's objects, from an empty repository of its own."""
    with tempfile.TemporaryDirectory(prefix="dbench-quality-") as scratch:
        bare = Path(scratch) / "objects.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], capture_output=True, check=True)
        return _git(args, bare, object_dirs(lot_dir, cell))


def scenario(lot_dir: Path, name: str) -> dict:
    """The scenario as the lot bound it, with its image, limits and test command."""
    bound = json.loads((Path(lot_dir) / "lot.json").read_text(encoding="utf-8"))["scenarios"][name]
    found = json.loads((Path(bound["path"]) / "scenario.json").read_text(encoding="utf-8"))
    return {**found, **bound}


def blob_oid(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def materialize(lot_dir: Path, unit: dict, dest: Path) -> Path:
    """Write the unit's tree into ``dest`` and prove every blob matches the recorded tree."""
    if not unit.get("tree"):
        raise ValueError(f"unit {unit['unit']} has no tree")
    dest = Path(dest)
    if dest.exists():
        raise FileExistsError(dest)
    listing = git_read(lot_dir, unit["cell"], ["ls-tree", "-r", "-z", unit["tree"]])
    archive = git_read(lot_dir, unit["cell"], ["archive", "--format=tar", unit["tree"]])
    expected = {}
    for entry in filter(None, listing.split(b"\0")):
        meta, path = entry.split(b"\t", 1)
        _mode, kind, oid = meta.decode().split()
        if kind == "blob":
            expected[path.decode("utf-8")] = oid
    dest.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            if member.issym():  # stored as its target text, as Git does without symlink support
                target = dest / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(member.linkname.encode("utf-8"))
            elif member.isfile() or member.isdir():
                tar.extract(member, dest, filter="data")
    wrong = [path for path, oid in expected.items()
             if not (dest / path).is_file() or blob_oid((dest / path).read_bytes()) != oid]
    if wrong:
        raise RuntimeError(f"unit {unit['unit']}: {len(wrong)} files differ from tree {unit['tree']}: {wrong[:5]}")
    return dest


def measure_records(lot_dir: Path, measure: str) -> dict[str, dict]:
    folder = Path(lot_dir) / "quality" / measure
    return {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("*.json"))}


def spread(values: list[float]) -> dict | None:
    if not values:
        return None
    if len(values) == 1:
        return {"n": 1, "median": values[0], "q1": values[0], "q3": values[0]}
    q1, median, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return {"n": len(values), "median": median, "q1": q1, "q3": q3}


def summarize(group: list[dict], measures: dict[str, dict[str, dict]]) -> dict:
    judged = [u for u in group if u["accepted"] is not None]
    robust = [u["robustness"] for u in group if u["robustness"]]
    compass = [u["compass"] for u in group if u["compass"]]
    row = {
        "units": len(group), "with_code": sum(u["code"] for u in group),
        "accepted": sum(bool(u["accepted"]) for u in judged), "judged": len(judged),
        "latent_found": sum(r.get("latent_found", 0) for r in robust),
        "latent_total": sum(r.get("latent_total", 0) for r in robust),
        "latent_share": spread([r["latent_found"] / r["latent_total"] for r in robust if r.get("latent_total")]),
        "invariants_broken": sum(len((c.get("invariants") or {}).get("failed", [])) for c in compass),
        "traps_violated": sum(len(c.get("traps_violated", [])) for c in compass),
    }
    for measure in MEASURES:
        records = [measures[measure][u["unit"]] for u in group if u["unit"] in measures[measure]]
        row[measure] = {"units": len(records),
                        "score": spread([r["score"] for r in records if isinstance(r.get("score"), (int, float))])}
    return row


def report(lot_dirs: list[Path], out: Path) -> dict:
    every, measures = [], {m: {} for m in MEASURES}
    for lot_dir in lot_dirs:
        every += units(lot_dir)
        for measure in MEASURES:
            measures[measure].update(measure_records(lot_dir, measure))
    groups = defaultdict(list)
    for unit in every:
        groups[(unit["arm"], unit["scenario"])].append(unit)
        groups[(unit["arm"], "*")].append(unit)
    rows = [{"arm": arm, "scenario": scenario, **summarize(group, measures)}
            for (arm, scenario), group in sorted(groups.items())]
    result = {"schema": 1, "lots": [Path(d).name for d in lot_dirs], "rows": rows}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_bytes((json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    (out / "report.md").write_bytes(markdown(result).encode("utf-8"))
    return result


def _cell(value: dict | None, percent: bool = False) -> str:
    if not value or not value.get("score"):
        return "—"
    s = value["score"]
    f = (lambda x: f"{100 * x:.0f}%") if percent else (lambda x: f"{x:.2g}")
    return f"{f(s['median'])} [{f(s['q1'])}–{f(s['q3'])}] n={s['n']}"


def markdown(result: dict) -> str:
    lines = [f"# Quality beyond the hidden tests: {', '.join(result['lots'])}", "",
             "Official verdict: accepted requests. Every other column is reported apart and changes nothing.",
             "Median [q1–q3] over units; `—` until that measure has run. Invariants and traps are the judge's",
             "raw counts per request; profile_report.py counts only regressions along the chain.", "",
             ("| Arm | Scenario | Units | With code | Accepted | Latent found | Invariants broken | Traps violated "
              "| Coverage | Mutation | Review |"),
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in result["rows"]:
        lines.append(f"| {r['arm']} | {r['scenario']} | {r['units']} | {r['with_code']} | {r['accepted']}/{r['judged']} "
                     f"| {r['latent_found']}/{r['latent_total']} | {r['invariants_broken']} | {r['traps_violated']} "
                     f"| {_cell(r['coverage'], True)} | {_cell(r['mutation'], True)} | {_cell(r['review'])} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("units", help="list every unit into <lot>/quality/units.json")
    listing.add_argument("--lot", type=Path, action="append", required=True)
    tree = sub.add_parser("materialize", help="write one unit's tree under <lot>/quality/trees/<unit>")
    tree.add_argument("--lot", type=Path, required=True)
    tree.add_argument("--unit", required=True)
    tree.add_argument("--dest", type=Path)
    cover = sub.add_parser("coverage", help="coverage of each unit's own tests over its added lines (DBH-29)")
    cover.add_argument("--lot", type=Path, required=True)
    cover.add_argument("--unit", action="append", help="only these units (repeatable)")
    cover.add_argument("--force", action="store_true", help="measure again units already measured")
    review = sub.add_parser("review", help="blind Opus 5.5 review of each unit's change (DBH-31)")
    review.add_argument("--lot", type=Path, required=True)
    review.add_argument("--unit", action="append", help="only these units (repeatable)")
    review.add_argument("--reviews", type=int, default=1, help="independent reviews per unit")
    review.add_argument("--force", action="store_true", help="review again units already reviewed")
    mutate = sub.add_parser("mutation", help="mutation of each unit's added lines, after coverage (DBH-30)")
    mutate.add_argument("--lot", type=Path, required=True)
    mutate.add_argument("--unit", action="append", help="only these units (repeatable)")
    mutate.add_argument("--limit", type=int, default=8, help="at most this many mutants per unit")
    mutate.add_argument("--jobs", type=int, default=4, help="mutants run at once")
    mutate.add_argument("--force", action="store_true", help="measure again units already measured")
    summary = sub.add_parser("report", help="write report.md and report.json")
    summary.add_argument("--lot", type=Path, action="append", required=True)
    summary.add_argument("--out", type=Path, help="default: <first lot>/quality")
    args = parser.parse_args(argv)
    if args.command == "units":
        for lot_dir in args.lot:
            found = units(lot_dir)
            folder = lot_dir / "quality"
            folder.mkdir(exist_ok=True)
            (folder / "units.json").write_bytes((json.dumps(found, indent=2) + "\n").encode("utf-8"))
            print(f"{lot_dir.name}: {len(found)} units, {sum(u['code'] for u in found)} with code")
    elif args.command == "materialize":
        unit = next((u for u in units(args.lot) if u["unit"] == args.unit), None)
        if unit is None:
            parser.error(f"no unit {args.unit} in {args.lot}")
        print(materialize(args.lot, unit, args.dest or args.lot / "quality" / "trees" / unit["unit"]))
    elif args.command in ("coverage", "mutation", "review"):
        import quality_coverage
        import quality_mutation
        import quality_review
        folder = args.lot / "quality" / args.command
        folder.mkdir(parents=True, exist_ok=True)
        for unit in units(args.lot):
            target = folder / f"{unit['unit']}.json"
            if (args.unit and unit["unit"] not in args.unit) or (target.exists() and not args.force):
                continue
            if args.command == "coverage":
                record = quality_coverage.measure(args.lot, unit, scenario(args.lot, unit["scenario"]))
            elif args.command == "mutation":
                record = quality_mutation.measure(args.lot, unit, scenario(args.lot, unit["scenario"]),
                                                  quality_mutation.coverage_record(args.lot, unit["unit"]),
                                                  args.limit, args.jobs)
            else:
                record = quality_review.measure(args.lot, unit, args.reviews)
            target.write_bytes((json.dumps(record, indent=1) + "\n").encode("utf-8"))
            print(unit["unit"], unit["cell"], unit["request"], record["status"], record.get("score"), flush=True)
    else:
        result = report(args.lot, args.out or args.lot[0] / "quality")
        print(markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
