"""Offline contract checks for the external Pi/Harbor boundary (no model calls)."""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harbor.environments.base import ExecResult
from harbor.models.agent.context import AgentContext

from harbor_pi_agent import MAX_LINE, PiHarborAgent


class FakeEnvironment:
    def __init__(self):
        self.calls = []

    async def exec(self, command, *, cwd=None, timeout_sec=None):
        self.calls.append((command, cwd, timeout_sec))
        return ExecResult(stdout="sandbox-only", stderr="", return_code=0)


class PiHarborAgentTests(unittest.TestCase):
    def test_bridge_routes_only_through_harbor_and_excludes_judge_key(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake_bridge = root / "fake_bridge.py"
            fake_bridge.write_text(
                """import json, os, sys
start = json.loads(sys.stdin.readline())
print(json.dumps({'type': 'exec', 'id': 'one', 'command': 'pwd', 'cwd': '/app', 'timeout_sec': 7}), flush=True)
response = json.loads(sys.stdin.readline())
print(json.dumps({'type': 'final', 'instruction': start['instruction'],
    'arm': start['arm'], 'response': response,
    'judge_visible': 'TYPESAFE_API_KEY' in os.environ,
    'usage': {'input_tokens': 12, 'output_tokens': 3, 'cost_usd': 0.001}}), flush=True)
""", encoding="utf-8")
            agent = PiHarborAgent(logs_dir=root, model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            agent.bridge_command = (sys.executable, str(fake_bridge))
            env, context = FakeEnvironment(), AgentContext()
            with patch.dict(os.environ, {"TYPESAFE_API_KEY": "should-not-reach-child"}):
                asyncio.run(agent.run("Exact task text", env, context))
            self.assertEqual(env.calls, [("pwd", "/app", 7)])
            self.assertEqual(context.n_input_tokens, 12)
            self.assertEqual(context.n_output_tokens, 3)
            self.assertEqual(context.cost_usd, 0.001)
            trajectory = json.loads((root / "pi-harbor-trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(trajectory["instruction"], "Exact task text")
            self.assertEqual(trajectory["arm"], "pi-bare")
            self.assertFalse(trajectory["judge_visible"])
            self.assertEqual(trajectory["response"]["stdout"], "sandbox-only")

    def test_real_pi_tool_reaches_harbor_environment_without_model_call(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = PiHarborAgent(logs_dir=root, model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            agent.bridge_command = ("node", str(Path(__file__).with_name("pi_bridge.mjs")),
                                    "--offline-probe-tool")
            env, context = FakeEnvironment(), AgentContext()
            asyncio.run(agent.run("unmodified task", env, context))
            self.assertEqual(env.calls, [("printf sandbox-ok > /tmp/tbf-pi-probe && cat /tmp/tbf-pi-probe", None, 10)])
            self.assertEqual(context.cost_usd, 0)
            self.assertTrue(context.metadata["offline_probe"])
            transcript = json.loads((root / "pi-harbor-trajectory.json").read_text(encoding="utf-8"))
            self.assertEqual(transcript["response"]["stdout"], "sandbox-only")
            self.assertTrue(transcript["offline_probe"])

    def test_large_sandbox_output_is_explicitly_bounded_before_reply(self):
        class LargeEnvironment(FakeEnvironment):
            async def exec(self, command, *, cwd=None, timeout_sec=None):
                self.calls.append((command, cwd, timeout_sec))
                return ExecResult(stdout="\0" * 20000, stderr="\0" * 20000, return_code=7)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "large_bridge.py"
            fake.write_text("""import json, sys
start = json.loads(sys.stdin.readline())
print(json.dumps({'type':'exec','id':'1','command':'cat big','cwd':None,'timeout_sec':10}), flush=True)
line = sys.stdin.readline()
reply = json.loads(line)
print(json.dumps({'type':'final','frame_bytes':len(line.encode('utf-8')),
    'stdout':reply['stdout'], 'stderr':reply['stderr'], 'return_code':reply['return_code'],
    'usage':{'input_tokens':0,'output_tokens':0,'cost_usd':0}}), flush=True)
""", encoding="utf-8")
            agent = PiHarborAgent(logs_dir=root, model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            agent.bridge_command = (sys.executable, str(fake))
            env = LargeEnvironment()
            asyncio.run(agent.run("task", env, AgentContext()))
            frame = json.loads((root / "pi-harbor-trajectory.json").read_text(encoding="utf-8"))
            self.assertLess(frame["frame_bytes"], MAX_LINE)
            self.assertIn("[truncated]", frame["stdout"])
            self.assertIn("[truncated]", frame["stderr"])
            self.assertEqual(frame["return_code"], 7)
            self.assertEqual(env.calls, [("cat big", None, 10)])

    def test_invalid_command_never_reaches_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "bad_bridge.py"
            fake.write_text("import json, sys\nsys.stdin.readline()\nprint(json.dumps({'type':'exec','id':'x','command':'pwd','cwd':None,'timeout_sec':121}), flush=True)\n", encoding="utf-8")
            agent = PiHarborAgent(logs_dir=root, model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            agent.bridge_command = (sys.executable, str(fake))
            env = FakeEnvironment()
            with self.assertRaisesRegex(RuntimeError, "invalid sandbox command"):
                asyncio.run(agent.run("task", env, AgentContext()))
            self.assertEqual(env.calls, [])

    def test_unknown_cost_cannot_be_reported_as_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "unknown_cost.py"
            fake.write_text("import json, sys\nsys.stdin.readline()\nprint(json.dumps({'type':'final','usage':{'input_tokens':1,'output_tokens':1,'cost_usd':None}}), flush=True)\n", encoding="utf-8")
            agent = PiHarborAgent(logs_dir=root, model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            agent.bridge_command = (sys.executable, str(fake))
            with self.assertRaisesRegex(RuntimeError, "missing or invalid attributable model usage"):
                asyncio.run(agent.run("task", FakeEnvironment(), AgentContext()))
            self.assertFalse((root / "pi-harbor-trajectory.json").exists())

    def test_pi_sdk_preflight_has_only_sandbox_tool_without_model_call(self):
        root = Path(__file__).parent
        start = {"type": "start", "instruction": "offline", "arm": "pi-bare",
                 "model": "openai-codex/gpt-6-sol", "thinking": "high"}
        env = {key: os.environ[key] for key in
               ("PATH", "SYSTEMROOT", "COMSPEC", "TEMP", "TMP", "USERPROFILE", "APPDATA")
               if key in os.environ}
        result = subprocess.run(
            ["node", str(root / "pi_bridge.mjs"), "--offline-preflight"],
            input=json.dumps(start) + "\n", text=True, capture_output=True,
            cwd=root, env=env, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        preflight = json.loads(result.stdout)
        self.assertEqual(preflight["tools"], ["sandbox_exec"])
        self.assertEqual(preflight["model"], "gpt-6-sol")
        self.assertEqual(preflight["thinking"], "high")

    def test_driver_arms_fail_closed_until_faithful_bridge_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            for arm in ("ticket-driver-c1a", "ticket-driver-c3a"):
                with self.subTest(arm=arm):
                    agent = PiHarborAgent(logs_dir=Path(temp), model_name="openai-codex/gpt-6-sol", arm=arm)
                    with self.assertRaisesRegex(RuntimeError, "faithful"):
                        asyncio.run(agent.run("task", FakeEnvironment(), AgentContext()))

    def test_live_bridge_is_disabled_until_budget_and_skill_binding_exist(self):
        with tempfile.TemporaryDirectory() as temp:
            agent = PiHarborAgent(logs_dir=Path(temp), model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            with self.assertRaisesRegex(RuntimeError, "live pilot gate"):
                asyncio.run(agent.run("task", FakeEnvironment(), AgentContext()))

    def test_harbor_factory_imports_the_adapter_by_public_import_path(self):
        from harbor.agents.factory import AgentFactory
        with tempfile.TemporaryDirectory() as temp:
            agent = AgentFactory.create_agent_from_import_path(
                "harbor_pi_agent:PiHarborAgent", Path(temp),
                model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            self.assertIsInstance(agent, PiHarborAgent)
            self.assertEqual(agent.options.arm, "pi-bare")

    def test_gpt_model_is_accepted_for_each_arm_without_starting_a_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            for arm in ("pi-bare", "skills-only", "ticket-driver-c1a", "ticket-driver-c3a"):
                with self.subTest(arm=arm):
                    agent = PiHarborAgent(logs_dir=Path(temp), model_name="openai-codex/gpt-6-sol", arm=arm)
                    self.assertEqual(agent.to_agent_info().model_info.provider, "openai-codex")

    def test_model_and_arm_must_match_frozen_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            for arm, model in (("unknown", "openai-codex/gpt-6-sol"), ("pi-bare", "anthropic/claude-opus-5-5")):
                with self.subTest(arm=arm, model=model), self.assertRaises(ValueError):
                    PiHarborAgent(logs_dir=Path(temp), model_name=model, arm=arm)


if __name__ == "__main__":
    unittest.main()
