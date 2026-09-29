"""Named semantic state: only exact content, no vague path-only question."""


def observed(receipt: dict, limit: int) -> dict:
    """The driver's own test run as one object: never the builder's word, never split apart."""
    output = receipt.get("stdout", "") + receipt.get("stderr", "")
    return {"argv": receipt.get("argv"), "exit_code": receipt.get("exit_code"), "output_tail": output[-limit:]}


def review(task: str, diff: str, prose: str, receipt: dict | None = None) -> dict:
    state = {"acceptance_text": task, "candidate_diff": diff, "review_prose": prose}
    if receipt is not None:
        state["driver_observed_test_receipt"] = observed(receipt, 4096)
    return state


def qa(argv: list[str], receipt: dict, paths: list[str], sources: list[dict] | None = None,
       limit: int = 4096) -> dict:
    """The end of each stream, as for red tests: a verbose suite's verdict comes last."""
    state = {"test_argv": argv, "exit_code": receipt.get("exit_code"),
             "observed_output": {"stdout_tail": receipt.get("stdout", "")[-limit:],
                                 "stderr_tail": receipt.get("stderr", "")[-limit:]},
             "changed_files": paths}
    if sources is not None:  # what the invocation ran: the class cannot be read from names alone
        state["test_sources"] = sources
    return state


def verify(claim: str, receipt: dict) -> dict:
    return {"claim": claim, "driver_observed_test_receipt": observed(receipt, 8192)}


def retry(output: str, finding: str) -> dict:
    return {"observed_failure_output": output[:8192], "review_finding": finding}


def red_tests(stdout: str, stderr: str, limit: int = 4096) -> dict:
    """A red test run: the end of each stream. A runner's verdict comes last, and one stream's
    build noise must not push the other stream's verdict out of the observation."""
    return {"observed_failure_output": {"stdout_tail": stdout[-limit:], "stderr_tail": stderr[-limit:]},
            "review_finding": "red tests"}
