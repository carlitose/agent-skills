"""Named semantic state: only exact content, no vague path-only question."""


def review(task: str, diff: str, prose: str, receipt: dict | None = None) -> dict:
    state = {"acceptance_text": task, "candidate_diff": diff, "review_prose": prose}
    if receipt is not None:  # the driver's own test run, never the builder's word
        output = receipt.get("stdout", "") + receipt.get("stderr", "")
        state["driver_observed_test_receipt"] = {"argv": receipt.get("argv"),
            "exit_code": receipt.get("exit_code"), "output_tail": output[-4096:]}
    return state


def qa(argv: list[str], receipt: dict, paths: list[str]) -> dict:
    return {"test_argv": argv, "exit_code": receipt.get("exit_code"),
            "observed_output": (receipt.get("stdout", "") + receipt.get("stderr", ""))[:8192],
            "changed_files": paths}


def verify(claim: str, receipt: dict) -> dict:
    return {"claim": claim, "observed_test_exit_code": receipt.get("exit_code"),
            "receipt_excerpt": (receipt.get("stdout", "") + receipt.get("stderr", ""))[:8192]}


def retry(output: str, finding: str) -> dict:
    return {"observed_failure_output": output[:8192], "review_finding": finding}
