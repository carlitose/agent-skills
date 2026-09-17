"""What does containment cost per command, on the command shapes the runner actually issues?

`capture_command` contains every child in an owned job/session so a killed runner cannot leak
processes. That guarantee is not free. This measures the price on the real shapes observed by
`measure_commands.py`, not on `git --version`, and compares it against the same command run by
plain `subprocess.run` in the same repository.

Usage:
    python docs/prototypes/suite-cost-one-percent/measure_capture_overhead.py [repetitions]
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2].parent
sys.path.insert(0, str(ROOT / "ticket-autopilot" / "scripts"))

from autopilot.command_capture import capture_command  # noqa: E402

SHAPES = [
    ["git", "rev-parse", "--show-toplevel"],
    ["git", "rev-parse", "--git-common-dir"],
    ["git", "rev-parse", "HEAD"],
    ["git", "write-tree"],
    ["git", "add", "-A"],
    ["git", "ls-files", "-z", "--"],
    ["git", "ls-tree", "-r", "-z", "HEAD"],
    ["git", "diff", "--name-only", "-z"],
    ["git", "status", "--porcelain"],
]


def repository(directory: Path) -> Path:
    for command in (
        ["git", "init", "--quiet"],
        ["git", "config", "user.email", "probe@example.invalid"],
        ["git", "config", "user.name", "probe"],
    ):
        subprocess.run(command, cwd=directory, check=True, capture_output=True)
    for index in range(12):
        (directory / f"file-{index}.md").write_text(f"content {index}\n", encoding="utf-8", newline="\n")
    subprocess.run(["git", "add", "-A"], cwd=directory, check=True, capture_output=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "probe"], cwd=directory, check=True, capture_output=True)
    return directory


def timed(callable_) -> float:
    import time

    start = time.perf_counter()
    callable_()
    return (time.perf_counter() - start) * 1000


def main(argv: list[str]) -> int:
    repetitions = int(argv[0]) if argv else 15
    with tempfile.TemporaryDirectory() as raw:
        repo = repository(Path(raw))
        rows = []
        for shape in SHAPES:
            direct = [timed(lambda: subprocess.run(shape, cwd=repo, capture_output=True)) for _ in range(repetitions)]
            captured = [
                timed(lambda: capture_command(shape, cwd=repo, timeout_seconds=60, max_output_bytes=1 << 20))
                for _ in range(repetitions)
            ]
            direct_ms = statistics.median(direct)
            captured_ms = statistics.median(captured)
            rows.append({
                "argv": " ".join(shape),
                "direct_ms": round(direct_ms, 1),
                "captured_ms": round(captured_ms, 1),
                "overhead_ms": round(captured_ms - direct_ms, 1),
                "ratio": round(captured_ms / direct_ms, 2),
            })
    payload = {
        "repetitions": repetitions,
        "platform": sys.platform,
        "rows": rows,
        "median_overhead_ms": round(statistics.median(row["overhead_ms"] for row in rows), 1),
    }
    output = Path(__file__).resolve().parent / "measurements" / "capture-overhead.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=1), encoding="utf-8", newline="\n")
    for row in rows:
        print(f"  {row['direct_ms']:6.1f} -> {row['captured_ms']:6.1f} ms  (+{row['overhead_ms']:5.1f}, x{row['ratio']})  {row['argv']}")
    print(f"sobrecoste mediano: {payload['median_overhead_ms']} ms por comando")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
