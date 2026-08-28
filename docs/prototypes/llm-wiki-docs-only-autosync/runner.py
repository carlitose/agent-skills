from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from model import (
    CandidateRef,
    IdentityDesign,
    RequestDesign,
    assess_designs,
    classify,
    scenario_matrix,
)


HERE = Path(__file__).resolve().parent
ORIGIN = CandidateRef("origin-base", "origin-integrated", "origin-ticket")


def main() -> int:
    print("WS-02 state matrix")
    for name, probe in scenario_matrix().items():
        result = classify(probe, ORIGIN)
        identity = (
            "-" if result.candidate_ref is None else result.candidate_ref.ticket_digest[:12]
        )
        print(
            f"{name:20} {result.outcome.value:28} "
            f"protected={result.protected_tree_oid:11} identity={identity}"
        )

    print("\nRequest design comparison")
    for assessment in assess_designs():
        print(
            f"{assessment.design.value:24} viable={str(assessment.viable).lower():5} "
            f"owner={assessment.policy_owner}"
        )
        if assessment.counterexample:
            print(f"  counterexample: {assessment.counterexample}")

    print("\nTracked identity comparison")
    tracked = scenario_matrix()["tracked"]
    for design in IdentityDesign:
        result = classify(tracked, ORIGIN, identity_design=design)
        digest = result.candidate_ref.ticket_digest if result.candidate_ref else "-"
        print(f"{design.value:30} {result.outcome.value:24} {digest[:16]}")

    print("\nRunning executable assertions and real llm-wiki lint fixture...")
    completed = subprocess.run(
        [sys.executable, "-B", str(HERE / "test_model.py")],
        cwd=HERE,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
