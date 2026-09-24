"""Task-bound one-cell agent behavior, fakes only; no Harbor trial or model."""
import asyncio
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harbor.environments.base import ExecResult
from harbor.models.agent.context import AgentContext
from comparison_agent import ComparisonPiHarborAgent, HERE, ROOT
from comparison_accounting import ComparisonLedger


class Environment:
    class Config:
        docker_image = "sha256:" + "a" * 64
    task_env_config = Config()
    def __init__(self):
        self.commands = []
    async def exec(self, command, *, timeout_sec=None, cwd=None):
        self.commands.append(command)
        if "git init" in command or "rev-parse HEAD" in command:
            return ExecResult(return_code=0, stdout="b" * 40 + "\n")
        if "sha256sum" in command:
            match = re.search(r"tbf-(public_checks\.py|comparison_sandbox\.py)", command)
            target = HERE / match.group(1)
            return ExecResult(return_code=0, stdout=hashlib.sha256(target.read_bytes()).hexdigest() + "  file\n")
        return ExecResult(return_code=0, stdout="")
    async def upload_file(self, source, dest):
        self.commands.append((str(source), dest))


class Process:
    def __init__(self, *args, **kwargs):
        self.names = []
        self.arm = args[2]["arm"]
    async def __aenter__(self): return self
    async def __aexit__(self, *_): return False
    async def phase(self, name, *args, **kwargs):
        self.names.append(name)
        return {"status": "completed", "response": "No findings."}
    async def finish(self, status):
        return {"status": status, "usage": {"cost_usd": 0.01 if self.arm == "pi-bare" else 0.02,
                "input_tokens": 1 if self.arm == "pi-bare" else 4,
                "output_tokens": 2 if self.arm == "pi-bare" else 5}}


class AgentTests(unittest.TestCase):
    def prepare(self, temp, arm):
        root = Path(temp)
        bind = root / "comparison-binding.json"
        auth, prior = root / "authority.txt", root / "pilot.jsonl"
        auth.write_text("synthetic authorization for offline tests", encoding="utf8")
        prior.write_text("synthetic prior ledger for offline tests", encoding="utf8")
        instruction = "public fixture"
        binding = {"method": "git-overlay-v1", "model": "openai-codex/gpt-6-sol", "thinking": "high",
                   "max_starts": 12, "cap_usd": "720", "skills": [{"path": "comparison-skills.md",
                    "sha256": hashlib.sha256((HERE / "comparison-skills.md").read_bytes()).hexdigest()}],
                   "helpers_sha256": {file: hashlib.sha256((HERE / file).read_bytes()).hexdigest()
                                      for file in ("public_checks.py", "comparison_sandbox.py")},
                   "arbiter_policy_sha256": hashlib.sha256((ROOT / "ticket-driver/policy.json").read_bytes()).hexdigest(),
                   "questions_sha256": {name: hashlib.sha256((ROOT / "ticket-driver/questions" / name).read_bytes()).hexdigest()
                       for name in ("review.findings_block.json", "review.scope_complete.json",
                                    "qa.evidence_class.json", "verify.claim_supported.json", "risk.semantic_change.json")},
                   "tasks": [{"task": "html-js-filter", "derived_agent_image_id": Environment.Config.docker_image,
                              "harbor_instruction_sha256": hashlib.sha256(instruction.encode()).hexdigest()}]}
        bind.write_text(json.dumps(binding), encoding="utf8")
        ledger_path = root / "comparison-ledger.jsonl"
        agent = ComparisonPiHarborAgent(root / "trial", model_name="openai-codex/gpt-6-sol",
            arm=arm, task_name="html-js-filter", binding_path=str(bind), ledger_path=str(ledger_path),
            authority_path=str(auth), prior_ledger_path=str(prior))
        agent.ledger.reserve("html-js-filter", arm)
        return agent, instruction

    def test_pi_bare_success_settles_one_cell_and_removes_git(self):
        with tempfile.TemporaryDirectory() as temp:
            agent, instruction = self.prepare(temp, "pi-bare")
            env, context = Environment(), AgentContext()
            async def observe(_environment, action, *args):
                return {"source_sha256": "1" * 64, "tree": "2" * 40, "directories": []}
            model = {"known": True, "terminal": True, "cost_usd": 0.01,
                     "input_tokens": 1, "output_tokens": 2, "sha256": "0" * 64}
            with patch("comparison_agent.ComparisonProcess", Process), \
                 patch("comparison_agent.read_model_journal", return_value=model), \
                 patch.object(agent, "_observe", side_effect=observe):
                async def run():
                    await agent.setup(env)
                    await agent.run(instruction, env, context)
                asyncio.run(run())
            self.assertEqual(agent.ledger.state()["starts"], 1)
            self.assertEqual(agent.ledger.state()["spent_usd"], "0.01")
            self.assertEqual(context.cost_usd, 0.01)
            self.assertEqual(context.metadata["local_gate"], "not-applicable")
            self.assertTrue(any("rm -rf" in command for command in env.commands if isinstance(command, str)))

    def test_c1a_missing_source_change_rolls_back_and_has_no_claim_of_local_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            agent, instruction = self.prepare(temp, "ticket-driver-c1a")
            env, context = Environment(), AgentContext()
            observed = []
            async def observe(_environment, action, *args):
                observed.append(action)
                return {"source_sha256": "1" * 64, "tree": "2" * 40, "directories": []}
            model = {"known": True, "terminal": True, "cost_usd": 0.02,
                     "input_tokens": 4, "output_tokens": 5, "sha256": "0" * 64}
            with patch("comparison_agent.ComparisonProcess", Process), \
                 patch("comparison_agent.read_model_journal", return_value=model), \
                 patch.object(agent, "_observe", side_effect=observe):
                async def run():
                    await agent.setup(env)
                    await agent.run(instruction, env, context)
                asyncio.run(run())
            self.assertEqual(context.metadata["local_gate"], "failed")
            self.assertTrue(context.metadata["candidate_discarded"])
            self.assertIn("rollback", observed)
            self.assertEqual(agent.ledger.state()["spent_usd"], "0.02")

    def test_synthetic_bridge_failure_with_no_receipt_blocks_next_cell(self):
        class Disconnect(Process):
            async def phase(self, *args, **kwargs):
                raise RuntimeError("synthetic endpoint failed")
        with tempfile.TemporaryDirectory() as temp:
            agent, instruction = self.prepare(temp, "pi-bare")
            env, context = Environment(), AgentContext()
            async def observe(_environment, action, *args):
                return {"source_sha256": "1" * 64, "tree": "2" * 40, "directories": []}
            with patch("comparison_agent.ComparisonProcess", Disconnect), \
                 patch.object(agent, "_observe", side_effect=observe):
                async def run():
                    await agent.setup(env)
                    await agent.run(instruction, env, context)
                with self.assertRaisesRegex(RuntimeError, "synthetic endpoint failed"):
                    asyncio.run(run())
            self.assertEqual(agent.ledger.state()["spent_usd"], "unknown")
            self.assertTrue(agent.ledger.state()["blocked"])


if __name__ == "__main__":
    unittest.main()
