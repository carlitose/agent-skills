"""Deterministic file writer for driver tests. Never imports or invokes Pi."""
import json
import subprocess
import sys
import time
from pathlib import Path

args = sys.argv
session = Path(args[args.index("--session-dir") + 1])
prompt = args[-1]
if "MODE=timeout" in prompt:
    time.sleep(3)
    raise SystemExit(0)
Path("calc.py").write_text("def answer():\n    return 42\n", encoding="utf-8", newline="\n")
Path("tests").mkdir(exist_ok=True)
Path("tests/__init__.py").write_bytes(b"")
value = 7 if "MODE=red" in prompt else 42
Path("tests/test_calc.py").write_text(
    f"import unittest\nfrom calc import answer\nclass CalcTests(unittest.TestCase):\n    def test_value(self): self.assertEqual(answer(), {value})\n",
    encoding="utf-8", newline="\n")
if "MODE=move" in prompt:
    target = prompt.split("TARGET=", 1)[1].split()[0]
    subprocess.run(["git", "-C", target, "-c", "user.name=test", "-c", "user.email=test@example.org",
                    "commit", "--allow-empty", "-qm", "race"], check=True)
session.mkdir(parents=True, exist_ok=True)
(session / "fake.jsonl").write_text(json.dumps({"message": {"usage": {"totalTokens": 11, "cost": {"total": 0.002}}}}) + "\n",
    encoding="utf-8", newline="\n")
print("fake leaf completed")
