"""Standard Harbor Pi arm: original task environment, no Git overlay or model calls."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from harbor.agents.factory import AgentFactory
from harbor.environments.base import ExecResult
from harbor.models.agent.context import AgentContext
from harbor_pi_agent import StandardPiHarborAgent


class FakeEnvironment:
    def __init__(self, exit_code=0):
        self.exit_code = exit_code
        self.calls = []

    async def exec(self, command, *, cwd=None, timeout_sec=None):
        self.calls.append((command, cwd, timeout_sec))
        return ExecResult(stdout="", stderr="", return_code=self.exit_code)


class StandardPiAgentTests(unittest.TestCase):
    def test_factory_loads_bare_arm_and_setup_only_reads_original_app(self):
        with tempfile.TemporaryDirectory() as temp:
            agent = AgentFactory.create_agent_from_import_path(
                "harbor_pi_agent:StandardPiHarborAgent", Path(temp),
                model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            self.assertIsInstance(agent, StandardPiHarborAgent)
            env = FakeEnvironment()
            asyncio.run(agent.setup(env))
            self.assertEqual(len(env.calls), 1)
            command = env.calls[0][0]
            self.assertIn("test -d /app", command)
            self.assertIn("test ! -e /app/.git", command)
            self.assertNotIn("git init", command)
            self.assertNotIn("git commit", command)
            with self.assertRaisesRegex(RuntimeError, "ledger"):
                asyncio.run(agent.run("exact task instruction", env, AgentContext()))
            self.assertEqual(len(env.calls), 1)

    def test_bound_start_rejects_derived_image_before_setup(self):
        with tempfile.TemporaryDirectory() as temp:
            agent = StandardPiHarborAgent(Path(temp), model_name="openai-codex/gpt-6-sol",
                                         arm="pi-bare", task_name="html-js-filter",
                                         ledger_path=Path(temp) / "standard.jsonl")
            env = FakeEnvironment()
            env.task_env_config = SimpleNamespace(docker_image="sha256:" + "0" * 64)
            with self.assertRaisesRegex(RuntimeError, "original image"):
                asyncio.run(agent.setup(env))
            self.assertEqual(env.calls, [])

    def test_missing_app_fails_before_agent_run(self):
        with tempfile.TemporaryDirectory() as temp:
            agent = StandardPiHarborAgent(Path(temp), model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            env = FakeEnvironment(exit_code=1)
            with self.assertRaisesRegex(RuntimeError, "original task sandbox"):
                asyncio.run(agent.setup(env))
            self.assertEqual(len(env.calls), 1)

    def test_default_live_command_needs_an_external_reserved_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            agent = StandardPiHarborAgent(Path(temp), model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            env = FakeEnvironment()
            with self.assertRaisesRegex(RuntimeError, "ledger"):
                asyncio.run(agent.run("instruction", env, AgentContext()))
            self.assertEqual(env.calls, [])

    def test_standard_start_binds_a_fixed_model_request_reservation(self):
        with tempfile.TemporaryDirectory() as temp:
            agent = StandardPiHarborAgent(Path(temp), model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            frame = agent._start_payload("unaltered instruction", "pi-bare")
            self.assertEqual(frame["instruction"], "unaltered instruction")
            self.assertEqual(frame["method"], "standard")
            self.assertEqual(frame["budget"], {"limit_usd": "60", "max_requests": 16})
            with self.assertRaisesRegex(RuntimeError, "budget"):
                agent._validate_final({"offline_probe": False, "usage": {"cost_usd": 1}})
            agent.task_name = "html-js-filter"
            with self.assertRaisesRegex(RuntimeError, "budget receipt"):
                agent._validate_final({"task_name": agent.task_name, "method": "standard",
                    "budget": {"limitUsd": "60", "maxRequests": 16, "requests": 1,
                               "pendingRequests": 0, "maxPerRequestUsd": 8.2,
                               "reservedUsd": 0, "observedUsd": 0, "ambiguous": False},
                    "usage": {"cost_usd": 0}})

    def test_live_ledger_and_trajectory_paths_must_stay_outside_git(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "outside the repository"):
                StandardPiHarborAgent(Path(temp), model_name="openai-codex/gpt-6-sol",
                                      arm="pi-bare", task_name="html-js-filter",
                                      ledger_path=Path(__file__).parent / "pilot.jsonl")
            with self.assertRaisesRegex(ValueError, "outside the repository"):
                StandardPiHarborAgent(Path(__file__).parent, model_name="openai-codex/gpt-6-sol",
                                      arm="pi-bare", task_name="html-js-filter",
                                      ledger_path=Path(temp) / "pilot.jsonl")

    def test_standard_agent_rejects_modified_arms(self):
        with tempfile.TemporaryDirectory() as temp:
            for arm in ("skills-only", "ticket-driver-c1a", "ticket-driver-c3a"):
                with self.subTest(arm=arm), self.assertRaisesRegex(ValueError, "pi-bare"):
                    StandardPiHarborAgent(Path(temp), model_name="openai-codex/gpt-6-sol", arm=arm)

    def test_offline_pi_tool_reaches_harbor_without_git_bootstrap(self):
        with tempfile.TemporaryDirectory() as temp:
            agent = StandardPiHarborAgent(Path(temp), model_name="openai-codex/gpt-6-sol", arm="pi-bare")
            agent.bridge_command = ("node", str(Path(__file__).with_name("pi_bridge.mjs")), "--offline-probe-tool")
            env = FakeEnvironment()
            asyncio.run(agent.setup(env))
            context = AgentContext()
            asyncio.run(agent.run("unaltered instruction", env, context))
            self.assertTrue(context.metadata["offline_probe"])
            self.assertEqual(context.cost_usd, 0)
            self.assertEqual(len(env.calls), 2)
            self.assertIn("/tmp/tbf-pi-probe", env.calls[1][0])
            self.assertNotIn("git", env.calls[1][0])


if __name__ == "__main__":
    unittest.main()
