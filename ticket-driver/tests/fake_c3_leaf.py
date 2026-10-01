"""Scripted builder/reviewer/QA/judge; never connects to model or Jev."""
import json
import sys
from pathlib import Path

from fake_judge import write_verdict

argv = sys.argv
session = Path(argv[argv.index("--session-dir") + 1])
prompt = argv[-1]
role = "directed-reviewer" if "ROLE=directed-reviewer" in prompt else "judge" if "You are a fresh independent judge" in prompt else next(
    (name for name in ("reviewer", "qa") if f"ROLE={name}" in prompt), "builder")
products = Path(".ticket-driver")
if role == "builder":
    if "MODE=directed-no-line-block-once" in prompt and (products / "retry.md").exists():
        session.mkdir(parents=True, exist_ok=True)
        (session / "retry-copy.txt").write_text((products / "retry.md").read_text(encoding="utf-8"), encoding="utf-8")
    if "MODE=scope-negative" in prompt and (products / "retry.md").exists():
        session.mkdir(parents=True, exist_ok=True)
        (session / "retry-copy.txt").write_text((products / "retry.md").read_text(encoding="utf-8"), encoding="utf-8")
        Path("FIXED.txt").write_text("fixed\n", encoding="utf-8", newline="\n")
    Path("calc.py").write_text("def answer():\n    return 42\ndef round_money(x):\n    return round(x * 100)\ndef boundary_tax(x):\n    return x >= 100\ndef helper(x):\n    return str(x)\n", encoding="utf-8", newline="\n")
    Path("tests").mkdir(exist_ok=True)
    Path("tests/__init__.py").write_bytes(b"")
    Path("tests/test_calc.py").write_text("import unittest\nfrom calc import answer\nclass T(unittest.TestCase):\n    def test_answer(self): self.assertEqual(answer(), 42)\n", encoding="utf-8", newline="\n")
elif role == "reviewer":
    products.mkdir(exist_ok=True)
    review = "Potentially okay, severity uncertain.\n" if "MODE=unparsed" in prompt else "No findings.\n"
    (products / "review.md").write_text(review, encoding="utf-8", newline="\n")
elif role == "directed-reviewer":
    products.mkdir(exist_ok=True)
    session.mkdir(parents=True, exist_ok=True)
    (session / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    blocker = "MODE=directed-always-block" in prompt or ("MODE=directed-block-once" in prompt and not session.name.endswith("-2"))
    no_line = "MODE=directed-no-line-block-once" in prompt and not session.name.endswith("-2")
    if "MODE=directed-tool-caches" in prompt or "MODE=directed-caches-and-notes" in prompt:
        # what running the tests from its cwd leaves behind (lot dbh-opus: pytest in the scratch)
        for cache in (".pytest_cache/v/cache/nodeids", ".pytest_cache/CACHEDIR.TAG", "__pycache__/calc.cpython-312.pyc"):
            Path(cache).parent.mkdir(parents=True, exist_ok=True)
            Path(cache).write_bytes(b"cache")
    if "MODE=directed-caches-and-notes" in prompt:
        Path("notes.txt").write_text("a reviewer's own file\n", encoding="utf-8")
    if "MODE=directed-mutate" in prompt:
        Path("calc.py").write_text("def answer():\n    return 0\n", encoding="utf-8")
    text = "[blocker] calc.py - money rounding edge\n" if no_line else "[blocker] calc.py:4 - money rounding edge\n" if blocker else "No findings.\n"
    (products / "review-directed.md").write_text(text, encoding="utf-8", newline="\n")
elif role == "qa":
    products.mkdir(exist_ok=True)
    (products / "qa-plan.md").write_text("# QA Plan\n\n## Automated Checks\n\n```bash\npython -B -m unittest discover -s tests -t .\n```\n", encoding="utf-8", newline="\n")
else:
    write_verdict(prompt, products, session)
session.mkdir(parents=True, exist_ok=True)
(session / "fake.jsonl").write_text(json.dumps({"message": {"role": "assistant", "content": role,
    "usage": {"totalTokens": 5, "cost": {"total": 0.001}}}}) + "\n", encoding="utf-8", newline="\n")
print(role)
