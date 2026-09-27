"""Scripted fresh judge shared by the fake leaves: it reads the question id and ends with one verdict."""
from pathlib import Path

QUESTIONS = ("review.findings_block", "review.scope_complete", "qa.evidence_class",
             "verify.claim_supported", "retry.recoverable")


def write_verdict(prompt: str, products: Path, session: Path) -> None:
    session.mkdir(parents=True, exist_ok=True)
    (session / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    state_file = products / "judge-state.json"
    state = state_file.read_text(encoding="utf-8") if state_file.is_file() else ""
    (session / "state.json").write_text(state, encoding="utf-8", newline="\n")
    prompt = prompt + "\n" + state  # the judge decides from the file the prompt names
    question = next((name for name in QUESTIONS if f"Question `{name}`" in prompt), None)
    if "MODE=gate" in prompt:
        text = "I cannot determine this from the evidence.\nAnswer: undetermined\n"
    elif question == "review.findings_block":
        # Quoting a clean review must not be read as this judge's verdict.
        text = ('The review says "No findings." but the change drops a required branch.\nAnswer: yes\n'
                if "MODE=quoted-clean" in prompt else "Nothing blocks integration.\nAnswer: no\n")
    elif question == "review.scope_complete":
        negative = "MODE=scope-negative-always" in prompt or (
            "MODE=scope-negative-once" in prompt and "FIXED.txt" not in prompt)
        text = ("The retry criterion has no implementation path in this diff.\nAnswer: no\n" if negative
                else "Every criterion has an implementation path.\nAnswer: yes\n")
    elif question == "verify.claim_supported":
        text = "The receipt shows exit code 0.\nAnswer: yes\n"
    elif question == "qa.evidence_class":
        text = "The command runs a unit binary and a CLI script together.\nAnswer: integration\n"
    else:
        text = "One bounded pass can correct this.\nAnswer: fix-in-place\n"
    products.mkdir(exist_ok=True)
    (products / "judge.md").write_text(text, encoding="utf-8", newline="\n")
