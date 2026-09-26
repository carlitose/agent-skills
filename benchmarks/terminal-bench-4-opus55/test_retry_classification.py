"""Offline: classify a finished Harbor cell as agent outcome or infrastructure failure."""
import json
import tempfile
import unittest
from pathlib import Path

from retry_classification import MAX_INFRA_RETRIES, classify_trial, retry_plan


def trial(root, *, reward=0.0, exc=None, agent_status="completed", stop=None, error=None, stages=True,
          error_type=None):
    d = Path(root)
    (d / "agent").mkdir(parents=True, exist_ok=True)
    stamp = {"started_at": "2026-09-25T10:00:00Z", "finished_at": "2026-09-25T10:10:00Z"}
    result = {"verifier_result": None if reward is None else {"rewards": {"reward": reward}},
              "exception_info": None if exc is None else {"exception_type": exc, "exception_message": "m"},
              "agent_execution": stamp if stages else None, "verifier": stamp if reward is not None else None}
    (d / "result.json").write_text(json.dumps(result), encoding="utf8")
    (d / "agent/standard-receipt.json").write_text(json.dumps({"status": agent_status, "error_type": error_type}),
                                                   encoding="utf8")
    message = {"role": "assistant", "content": [], "stopReason": stop or "stop"}
    if error:
        message["errorMessage"] = error
    (d / "agent/pi-builder.jsonl").write_text(json.dumps({"type": "message", "message": message}) + "\n", encoding="utf8")
    return d


class RetryClassificationTests(unittest.TestCase):
    def check(self, expected, **kwargs):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(classify_trial(trial(temp, **kwargs))["class"], expected, kwargs)

    def test_verified_outcomes_of_a_normally_ended_agent_count(self):
        self.check("agent", reward=0.0)
        self.check("agent", reward=1.0)
        self.check("agent", reward=0.0, exc="AgentTimeoutError")

    def test_verifier_not_run_by_the_harness_is_infrastructure(self):
        self.check("infra:verifier", reward=None, exc="ValueError")

    def test_provider_disconnect_that_stopped_the_agent_is_infrastructure(self):
        self.check("infra:provider", reward=0.0, exc="NonZeroAgentExitCodeError", agent_status="failed",
                   stop="error", error="WebSocket closed 1012")
        self.check("infra:provider", reward=0.0, exc="NonZeroAgentExitCodeError", agent_status="failed",
                   stop="error", error="503 Service Unavailable")

    def test_a_pass_is_never_repeated_even_after_a_provider_error(self):
        self.check("agent", reward=1.0, exc="NonZeroAgentExitCodeError", agent_status="failed",
                   stop="error", error="WebSocket closed 1012")

    def test_agent_own_failures_count_and_unknown_cases_need_review(self):
        self.check("agent", reward=0.0, exc="NonZeroAgentExitCodeError", agent_status="failed",
                   stop="error", error="request limit reached")
        self.check("review", reward=None, exc="NonZeroAgentExitCodeError", agent_status="failed")
        self.check("infra:environment", reward=None, exc="RuntimeError", stages=False)

    def test_host_side_exception_in_our_harness_is_infrastructure(self):
        # e.g. Windows CreateProcess "embedded null character" killed the agent run.
        self.check("infra:harness", reward=0.0, exc="NonZeroAgentExitCodeError", agent_status="failed",
                   error_type="ValueError")
        self.check("infra:harness", reward=0.0, exc="NonZeroAgentExitCodeError", agent_status="failed",
                   error_type="OSError")
        self.check("agent", reward=1.0, exc="NonZeroAgentExitCodeError", agent_status="failed",
                   error_type="ValueError")
        self.check("agent", reward=0.0, exc="NonZeroAgentExitCodeError", agent_status="failed",
                   error_type="RuntimeError")

    def test_missing_result_is_infrastructure(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(classify_trial(Path(temp))["class"], "infra:no-result")

    def test_retry_plan_caps_infra_retries_and_keeps_the_first_non_infra_attempt(self):
        cells = {"a": ["agent"], "b": ["infra:provider"], "c": ["infra:verifier", "agent"],
                 "d": ["infra:verifier"] * (1 + MAX_INFRA_RETRIES), "e": ["review"]}
        plan = retry_plan(cells)
        self.assertEqual(plan["retry"], ["b"])
        self.assertEqual(plan["final"], {"a": 0, "c": 1})
        self.assertEqual(plan["exhausted"], ["d"])
        self.assertEqual(plan["review"], ["e"])


if __name__ == "__main__":
    unittest.main()
