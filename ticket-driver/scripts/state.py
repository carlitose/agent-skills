"""Named semantic state: only exact content, no vague path-only question."""


def review(task: str, diff: str, prose: str) -> dict:
    return {"acceptance_text": task, "candidate_diff": diff, "review_prose": prose}


def qa(argv: list[str], receipt: dict, paths: list[str]) -> dict:
    return {"test_argv": argv, "exit_code": receipt.get("exit_code"),
            "observed_output": (receipt.get("stdout", "") + receipt.get("stderr", ""))[:8192],
            "changed_files": paths}


def verify(claim: str, receipt: dict) -> dict:
    return {"claim": claim, "observed_test_exit_code": receipt.get("exit_code"),
            "receipt_excerpt": (receipt.get("stdout", "") + receipt.get("stderr", ""))[:8192]}


def retry(output: str, finding: str) -> dict:
    return {"observed_failure_output": output[:8192], "review_finding": finding}
