"""Subprocess boundary tests; fake endpoint, real pipes, no model requests."""
import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path

from harbor.environments.base import ExecResult
from comparison_transport import ComparisonProcess, model_identity
from comparison_accounting import read_model_journal

INIT = {"type": "init", "method": "git-overlay-v1", "arm": "pi-bare",
        "task_name": "fixture", "trial_id": "fixture", "instruction": "task",
        "model": "openai-codex/gpt-6-sol", "thinking": "high"}
FAKE = '''import hashlib, json, sys
start = json.loads(sys.stdin.readline())
identity = dict(method=start['method'],task=start['task_name'],arm=start['arm'],trial=start['trial_id'],
                model=start['model'],thinking=start['thinking'],
                instruction_sha256=hashlib.sha256(start['instruction'].encode()).hexdigest())
print(json.dumps({'type':'ready','identity':identity}),flush=True)
phase=json.loads(sys.stdin.readline())
print(json.dumps({'type':'exec','id':'1','command':'sleep 50','cwd':'/app','timeout_sec':1}),flush=True)
reply=json.loads(sys.stdin.readline())
print(json.dumps({'type':'phase-result','phase':phase['name'],'status':'completed','reply':reply}),flush=True)
sys.stdin.readline()
print(json.dumps({'type':'final','status':'completed','identity':identity}),flush=True)
'''


class ComparisonTransportTests(unittest.TestCase):
    def test_real_endpoint_binds_identity_and_closes_without_model_request(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            init = {**INIT, "budget": {"limit_usd": "57", "max_requests": 48}}
            async def run():
                async with ComparisonProcess(directory, None, init) as proc:
                    final = await proc.finish("completed")
                    self.assertEqual(final["usage"]["cost_usd"], 0)
                    self.assertEqual(final["usage"]["budget"]["requests"], 0)
            asyncio.run(run())
            journal = [json.loads(row) for row in (directory / "model-usage.jsonl").read_text().splitlines()]
            self.assertEqual([row["event"] for row in journal], ["initial", "terminal"])
            receipt = read_model_journal(directory / "model-usage.jsonl", model_identity(init))
            self.assertTrue(receipt["known"])
            self.assertTrue(receipt["terminal"])
            self.assertEqual(receipt["cost_usd"], 0)

    def test_original_method_real_endpoint_handshake_without_model(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            init = {**INIT, "method": "original-harbor-full-pi-bare", "task_name": "nonpilot-task",
                    "budget": {"limit_usd": "57", "max_requests": 48}}
            async def run():
                async with ComparisonProcess(directory, None, init) as proc:
                    final = await proc.finish("completed")
                    self.assertEqual(final["identity"], model_identity(init))
                    self.assertEqual(final["usage"]["budget"]["requests"], 0)
            asyncio.run(run())
            model = read_model_journal(directory / "model-usage.jsonl", model_identity(init))
            self.assertTrue(model["known"])
            self.assertEqual(model["cost_usd"], 0)

    def test_real_endpoint_handshake_matches_python_identity_for_every_original_arm(self):
        # c1a/c3a lots failed live on "comparison endpoint identity mismatch": the bridge put
        # skills_sha256 in its identity only for skills-only. Exercise the real Node bridge.
        for arm in ("pi-bare", "skills-only", "ticket-driver-c1a", "ticket-driver-c3a"):
            with self.subTest(arm=arm), tempfile.TemporaryDirectory() as temp:
                init = {**INIT, "method": "original-harbor-full-pi-bare", "task_name": "nonpilot-task",
                        "arm": arm, "budget": {"limit_usd": "9000", "max_requests": 1000}}
                if arm != "pi-bare":
                    init["skills_sha256"] = "c" * 64
                async def run():
                    async with ComparisonProcess(Path(temp), None, init) as proc:
                        final = await proc.finish("completed")
                        self.assertEqual(final["identity"], model_identity(init))
                asyncio.run(run())

    def test_timeout_result_is_delivered_and_process_exits(self):
        class Environment:
            async def exec(self, command, *, cwd=None, timeout_sec=None):
                self.call = command, cwd, timeout_sec
                return ExecResult(stdout="partial", stderr="timeout", return_code=124)
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            script = directory / "endpoint.py"
            script.write_text(FAKE, encoding="utf8")
            env = Environment()
            async def run():
                async with ComparisonProcess(directory, env, INIT, command=(sys.executable, str(script))) as proc:
                    result = await proc.phase("builder", "task", "only sandbox", tools="sandbox")
                    self.assertEqual(result["reply"]["return_code"], 124)
                    await proc.finish("completed")
            asyncio.run(run())
            self.assertIn("timeout --signal=TERM", env.call[0])
            self.assertEqual(env.call[1:], ("/app", 16))
            self.assertEqual(json.loads((directory / "host-status.json").read_text())["status"], "completed")

    def test_transport_failure_kills_child_and_writes_host_failure(self):
        class Environment:
            async def exec(self, *args, **kwargs):
                raise RuntimeError("host timed out; remote termination unconfirmed")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            script = directory / "endpoint.py"
            script.write_text(FAKE, encoding="utf8")
            async def run():
                async with ComparisonProcess(directory, Environment(), INIT,
                                              command=(sys.executable, str(script))) as proc:
                    await proc.phase("builder", "task", "sandbox", tools="sandbox")
            with self.assertRaisesRegex(RuntimeError, "unconfirmed"):
                asyncio.run(run())
            state = json.loads((directory / "host-status.json").read_text())
            self.assertEqual(state["status"], "failed")
            self.assertTrue(state["process_stopped"])

    def test_wrong_trial_identity_is_rejected_before_a_phase(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            script = directory / "endpoint.py"
            script.write_text(FAKE.replace("trial=start['trial_id']", "trial='wrong'"), encoding="utf8")
            async def run():
                async with ComparisonProcess(directory, None, INIT,
                                              command=(sys.executable, str(script))):
                    self.fail("wrong identity was admitted")
            with self.assertRaisesRegex(RuntimeError, "identity"):
                asyncio.run(run())

    def test_read_only_phase_never_executes_a_command(self):
        class Environment:
            async def exec(self, *args, **kwargs):
                raise AssertionError("read-only phase called shell")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            script = directory / "endpoint.py"
            script.write_text(FAKE, encoding="utf8")
            async def run():
                async with ComparisonProcess(directory, Environment(), INIT,
                                              command=(sys.executable, str(script))) as proc:
                    await proc.phase("reviewer", "task", "review only", tools="none")
            with self.assertRaisesRegex(RuntimeError, "read-only"):
                asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
