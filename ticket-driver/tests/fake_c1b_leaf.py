"""Deterministic role-based leaf; no model or network access."""
import json
import sys
from pathlib import Path

args = sys.argv
session = Path(args[args.index("--session-dir") + 1])
prompt = args[-1]
role = next((name for name in ("reviewer", "qa") if f"ROLE={name}" in prompt), "builder")
products = Path(".ticket-driver")
if role == "builder":
    retry = (products / "retry.md").exists()
    value = 0 if "MODE=tests-red-first" in prompt and not retry else 42
    Path("calc.py").write_text(f"def answer():\n    return {value}\n", encoding="utf-8", newline="\n")
    Path("tests").mkdir(exist_ok=True)
    Path("tests/__init__.py").write_bytes(b"")
    Path("tests/test_calc.py").write_text("import unittest\nfrom calc import answer\nclass T(unittest.TestCase):\n    def test_answer(self): self.assertEqual(answer(), 42)\n", encoding="utf-8", newline="\n")
elif role == "reviewer":
    products.mkdir(exist_ok=True)
    if "MODE=reviewer-mutates" in prompt:
        Path("calc.py").write_text("def answer():\n    return 0\n", encoding="utf-8", newline="\n")
    if "MODE=unparsed" in prompt:
        text = "Looks good maybe, no explicit finding.\n"
    elif "MODE=block-twice" in prompt or ("MODE=block-once" in prompt and not (products / "retry.md").exists()):
        text = "[blocker] calc.py:2 - wrong boundary arithmetic\n"
    else:
        text = "No findings.\n"
    (products / "review.md").write_text(text, encoding="utf-8", newline="\n")
else:
    products.mkdir(exist_ok=True)
    (products / "qa-plan.md").write_text("# QA Plan\n\n## Automated Checks\n\n```bash\npython -B -m unittest discover -s tests -t .\n```\n", encoding="utf-8", newline="\n")
session.mkdir(parents=True, exist_ok=True)
(session / "fake.jsonl").write_text(json.dumps({"message": {"role": "assistant", "content": role,
    "usage": {"totalTokens": 11, "cost": {"total": 0.002}}}}) + "\n", encoding="utf-8", newline="\n")
print(role)
