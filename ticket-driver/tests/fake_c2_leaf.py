"""Scripted builder/reviewer/QA/judge; never connects to model or Jev."""
import json
import sys
from pathlib import Path

argv = sys.argv
session = Path(argv[argv.index("--session-dir") + 1])
prompt = argv[-1]
role = "judge" if "You are a fresh independent judge" in prompt else next(
    (name for name in ("reviewer", "qa") if f"ROLE={name}" in prompt), "builder")
products = Path(".ticket-driver")
if role == "builder":
    Path("calc.py").write_text("def answer():\n    return 42\n", encoding="utf-8", newline="\n")
    Path("tests").mkdir(exist_ok=True)
    Path("tests/__init__.py").write_bytes(b"")
    Path("tests/test_calc.py").write_text("import unittest\nfrom calc import answer\nclass T(unittest.TestCase):\n    def test_answer(self): self.assertEqual(answer(), 42)\n", encoding="utf-8", newline="\n")
elif role == "reviewer":
    products.mkdir(exist_ok=True)
    review = "Potentially okay, severity uncertain.\n" if "MODE=unparsed" in prompt else "No findings.\n"
    (products / "review.md").write_text(review, encoding="utf-8", newline="\n")
elif role == "qa":
    products.mkdir(exist_ok=True)
    (products / "qa-plan.md").write_text("# QA Plan\n\n## Automated Checks\n\n```bash\npython -B -m unittest discover -s tests -t .\n```\n", encoding="utf-8", newline="\n")
else:
    products.mkdir(exist_ok=True)
    if "MODE=gate" in prompt:
        text = "I cannot determine this from the evidence.\n"
    elif "Does the review" in prompt:
        text = "No findings.\n"
    elif "cover each acceptance" in prompt:
        text = "All acceptance criteria are covered.\n"
    elif "supported by" in prompt:
        text = "This claim is supported.\n"
    else:
        text = "This is a simulated test.\n"
    (products / "judge.md").write_text(text, encoding="utf-8", newline="\n")
session.mkdir(parents=True, exist_ok=True)
(session / "fake.jsonl").write_text(json.dumps({"message": {"role": "assistant", "content": role,
    "usage": {"totalTokens": 5, "cost": {"total": 0.001}}}}) + "\n", encoding="utf-8", newline="\n")
print(role)
