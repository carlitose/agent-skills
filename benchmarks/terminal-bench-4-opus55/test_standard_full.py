"""No provider: original-task admission, real journal reduction and fake Harbor IO."""
import asyncio
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harbor.environments.base import ExecResult
from harbor.models.agent.context import AgentContext
from harbor.models.task.config import TaskConfig
from comparison_accounting import AccountingError, read_model_journal
from harbor.agents.installed.base import NonZeroAgentExitCodeError
from comparison_transport import model_identity
from standard_full import FullStandardPiHarborAgent, METHOD, DATASET_REF, StandardLot, original_task

MODEL = "openai-codex/gpt-6-sol"
TOML = '''version = "1.0"
[task]
name = "terminal-bench/nonpilot-task"
[environment]
docker_image = "registry/original@sha256:AAAAAAAA"
[verifier.environment]
docker_image = "registry/verifier@sha256:BBBBBBBB"
'''.replace("AAAAAAAA", "a" * 64).replace("BBBBBBBB", "b" * 64)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rewrite_task(root, toml):
    task = root / "tasks/nonpilot-task/task.toml"
    task.write_text(toml, encoding="utf8")
    manifest = root / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf8"))
    data["tasks"][0]["task_toml_sha256"] = sha(task)
    manifest.write_text(json.dumps(data), encoding="utf8")
    lot = root / "lot.json"
    binding = json.loads(lot.read_text(encoding="utf8"))
    binding["manifest_sha256"] = sha(manifest)
    lot.write_text(json.dumps(binding), encoding="utf8")
    return TaskConfig.model_validate_toml(toml)


def fixture(root):
    task = root / "tasks/nonpilot-task"
    task.mkdir(parents=True)
    (task / "task.toml").write_text(TOML, encoding="utf8")
    (task / "instruction.md").write_text("<!-- canary fixture -->\n\nOriginal task\n", encoding="utf8")
    rows = [{"name": "nonpilot-task", "registry_ref": "terminal-bench/nonpilot-task@sha256:" + "c" * 64,
             "task_toml_sha256": sha(task / "task.toml"), "instruction_sha256": sha(task / "instruction.md")}]
    rows += [{**rows[0], "name": f"other-{n}"} for n in range(65)]
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"dataset_ref": DATASET_REF,
                                   "dataset_task_count": 66, "tasks": rows}), encoding="utf8")
    authority = root / "authority.txt"
    authority.write_text("Synthetic offline test authority; never usable for a live trial.", encoding="utf8")
    prior = root / "prior.jsonl"
    prior.write_text("synthetic previous evidence\n", encoding="utf8")
    second = root / "second.jsonl"
    second.write_text("synthetic second historical evidence\n", encoding="utf8")
    lot = root / "lot.json"
    lot.write_text(json.dumps({"schema": 1, "method": METHOD, "model": MODEL, "thinking": "high",
        "manifest_sha256": sha(manifest), "repetitions": 2, "cap_usd": "150",
        "prior_commitment_usd": "123.58286105200000007", "actor": "offline-test",
        "authority_sha256": sha(authority), "prior_evidence": [{"path": str(prior), "sha256": sha(prior)},
            {"path": str(second), "sha256": sha(second)}]}), encoding="utf8")
    return manifest, lot, authority


def agent_init(agent):
    return dict(type="init", method=METHOD, model=MODEL, thinking="high", arm="pi-bare",
                task_name=agent.task_name, instruction="Original task\n")


class Environment:
    def __init__(self, root):
        self.environment_dir = root / "tasks/nonpilot-task/environment"
        self.task_env_config = TaskConfig.model_validate_toml(TOML).environment
        self.commands = []

    async def exec(self, command, **kwargs):
        self.commands.append((command, kwargs))
        return ExecResult(return_code=0, stdout="")

    async def upload_file(self, *args):
        raise AssertionError("No public helper, Git or skill may be uploaded")


class Process:
    pending = False
    failure = False
    phases = []

    def __init__(self, directory, environment, init):
        self.directory, self.init = directory, init
        self.identity = model_identity(init)

    async def __aenter__(self):
        return self

    async def phase(self, name, prompt, system, *, tools):
        self.phases.append((name, prompt, system, tools))
        if self.failure:
            raise RuntimeError("fake transport loss")
        return {"status": "completed"}

    async def finish(self, status):
        return {"status": status, "usage": {"cost_usd": 0.01, "input_tokens": 12, "output_tokens": 3}}

    async def __aexit__(self, *_):
        policy = self.init["budget"]
        budget = dict(requests=0, pendingRequests=0, maxPerRequestUsd=8.2, reservedUsd=0,
                      observedUsd=0, ambiguous=False, maxRequests=policy["max_requests"],
                      limitUsd=policy["limit_usd"])
        initial = dict(schema=1, seq=0, event="initial", phase="initial", identity=self.identity,
                       budget=budget, known=True, cost_usd=0, input_tokens=0, output_tokens=0)
        request = {**initial, "seq": 1, "event": "request", "known": False, "cost_usd": None,
                   "budget": {**budget, "requests": 1, "pendingRequests": 1, "reservedUsd": 8.2}}
        usage = {**initial, "seq": 2, "event": "usage", "cost_usd": 0.01,
                 "input_tokens": 12, "output_tokens": 3,
                 "budget": {**budget, "requests": 1, "observedUsd": 0.01, "reservedUsd": 0.01}}
        rows = [initial, request] if self.pending else [initial, request, usage]
        rows.append({**rows[-1], "seq": len(rows), "event": "terminal",
                     "status": "failed" if self.failure else "completed"})
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "model-usage.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf8")
        (self.directory / "host-status.json").write_text(json.dumps({"process_stopped": True,
            "trial_id": self.init["trial_id"]}), encoding="utf8")


class StandardFullTests(unittest.TestCase):
    def setUp(self):
        prior = hashlib.sha256(("synthetic previous evidence" + os.linesep).encode()).hexdigest()
        second = hashlib.sha256(("synthetic second historical evidence" + os.linesep).encode()).hexdigest()
        gate = patch("standard_full.PRIOR_DIGESTS", frozenset((prior, second)))
        gate.start()
        self.addCleanup(gate.stop)

    def agent(self, root, repetition=1):
        return FullStandardPiHarborAgent(root / f"logs-{repetition}", model_name=MODEL,
            repetition=repetition,
            lot_path=str(root / "lot.json"), authority_path=str(root / "authority.txt"),
            ledger_path=str(root / "ledger.jsonl"))

    def test_nonpilot_original_task_runs_without_git_helpers_or_rewritten_instruction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, _, _ = fixture(root)
            Process.phases = []
            with patch("standard_full.MANIFEST", manifest), patch("standard_full.ComparisonProcess", Process):
                agent = self.agent(root)
                env, context = Environment(root), AgentContext()
                async def run():
                    await agent.setup(env)
                    await agent.run("Original task\n", env, context)
                asyncio.run(run())
                self.assertEqual(agent.ledger.state()["starts"], 1)
                self.assertEqual(agent.ledger.state()["spent_usd"], "0.01")
            self.assertEqual(context.cost_usd, 0.01)
            self.assertEqual(Process.phases[0][1], "Original task\n")
            self.assertEqual(Process.phases[0][3], "sandbox")
            self.assertEqual(len(Process.phases), 1)
            self.assertEqual(Process.phases[0][2], "Work only through sandbox_exec in the task environment. Complete the user task.")
            self.assertTrue(all("git" not in c and "/app" not in c for c, _ in env.commands))
            receipt = json.loads((root / "logs-1/standard-receipt.json").read_text())
            self.assertTrue(receipt["model"]["known"])
            self.assertEqual(receipt["method"], METHOD)

    def test_native_harbor_environment_identifies_task_without_per_task_agent_config(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            env = Environment(root)
            env.environment_dir = root / "tasks/nonpilot-task/environment"
            with patch("standard_full.MANIFEST", manifest):
                agent = FullStandardPiHarborAgent(root / "native", model_name=MODEL,
                    lot_path=str(lot), authority_path=str(authority), ledger_path=str(root / "ledger.jsonl"))
                asyncio.run(agent.setup(env))
                self.assertEqual(agent.task_name, "nonpilot-task")
                self.assertEqual(agent.cell, "nonpilot-task#1")
                self.assertEqual(agent.ledger.state()["starts"], 0)

    def test_task_native_skills_dir_is_not_agent_injection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            config = rewrite_task(root, TOML.replace("[verifier.environment]",
                'skills_dir = "/original-task-skills"\n[verifier.environment]'))
            env = Environment(root)
            env.task_env_config = config.environment
            with patch("standard_full.MANIFEST", manifest):
                agent = FullStandardPiHarborAgent(root / "native", model_name=MODEL,
                    skills_dir="/original-task-skills", lot_path=str(lot),
                    authority_path=str(authority), ledger_path=str(root / "ledger.jsonl"))
                asyncio.run(agent.setup(env))
                self.assertEqual(agent.ledger.state()["starts"], 0)
                self.assertEqual(len(env.commands), 1)  # capability probe, never upload skills
                with self.assertRaisesRegex(ValueError, "injected"):
                    other = FullStandardPiHarborAgent(root / "wrong", model_name=MODEL,
                        skills_dir="/different-skills", lot_path=str(lot),
                        authority_path=str(authority), ledger_path=str(root / "ledger.jsonl"))
                    asyncio.run(other.setup(env))

    def test_task_native_mcp_is_not_agent_injection_or_pi_tool(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            toml = TOML.replace("[verifier.environment]",
                '[[environment.mcp_servers]]\nname = "playwright"\n'
                'transport = "sse"\nurl = "http://playwright-mcp:3080/sse"\n'
                '[verifier.environment]')
            config = rewrite_task(root, toml)
            env = Environment(root)
            env.task_env_config = config.environment
            with patch("standard_full.MANIFEST", manifest):
                agent = FullStandardPiHarborAgent(root / "native", model_name=MODEL,
                    mcp_servers=config.environment.mcp_servers,
                    lot_path=str(lot), authority_path=str(authority),
                    ledger_path=str(root / "ledger.jsonl"))
                asyncio.run(agent.setup(env))
                self.assertEqual(agent.ledger.state()["starts"], 0)
                self.assertEqual(len(env.commands), 1)
                with self.assertRaisesRegex(ValueError, "injected"):
                    other = FullStandardPiHarborAgent(root / "wrong", model_name=MODEL,
                        mcp_servers=[], lot_path=str(lot), authority_path=str(authority),
                        ledger_path=str(root / "ledger.jsonl"))
                    asyncio.run(other.setup(env))

    def test_unsupported_timeout_does_not_start_or_modify_image(self):
        class Unsupported(Environment):
            async def exec(self, *args, **kwargs):
                return ExecResult(return_code=127, stderr="timeout unavailable")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, _, _ = fixture(root)
            with patch("standard_full.MANIFEST", manifest):
                agent = self.agent(root)
                with self.assertRaisesRegex(RuntimeError, "no overlay"):
                    asyncio.run(agent.setup(Unsupported(root)))
                self.assertEqual(agent.ledger.state()["starts"], 0)

    def test_lot_cannot_replace_old_ledger_or_exceed_project_cap(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            with patch("standard_full.MANIFEST", manifest):
                old = root / "old-ledger.jsonl"
                old.write_text('{"event":"comparison"}\n', encoding="utf8")
                with self.assertRaises(AccountingError):
                    StandardLot(old, lot, authority)
                config = json.loads(lot.read_text())
                config["cap_usd"] = "1000"
                lot.write_text(json.dumps(config), encoding="utf8")
                with self.assertRaises(AccountingError):
                    StandardLot(root / "new-ledger.jsonl", lot, authority)

    def test_non_ascii_instruction_matches_installed_harbor_loader(self):
        from harbor.models.task.task import Task
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, _, _ = fixture(root)
            task = root / "tasks/nonpilot-task"
            (task / "instruction.md").write_text("<!-- canary fixture -->\n\nCaffè\n", encoding="utf8")
            data = json.loads(manifest.read_text())
            data["tasks"][0]["instruction_sha256"] = sha(task / "instruction.md")
            manifest.write_text(json.dumps(data), encoding="utf8")
            with patch("standard_full.MANIFEST", manifest):
                _, instruction = original_task(root / "tasks", "nonpilot-task")
            self.assertEqual(instruction, Task(task, disable_verification=True).instruction)

    def test_known_failure_cost_is_retained_in_context_and_ledger(self):
        class Failed(Process):
            failure = True
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, _, _ = fixture(root)
            with patch("standard_full.MANIFEST", manifest), patch("standard_full.ComparisonProcess", Failed):
                agent, context = self.agent(root), AgentContext()
                async def run():
                    env = Environment(root)
                    await agent.setup(env)
                    await agent.run("Original task\n", env, context)
                with self.assertRaisesRegex(RuntimeError, "fake transport loss"):
                    asyncio.run(run())
                self.assertEqual(context.cost_usd, 0.01)
                self.assertFalse(agent.ledger.state()["blocked"])
                self.assertEqual(agent.ledger.state()["spent_usd"], "0.01")

    def test_pending_model_request_blocks_even_another_predeclared_repetition(self):
        class Lost(Process):
            failure = pending = True
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, _, _ = fixture(root)
            with patch("standard_full.MANIFEST", manifest), patch("standard_full.ComparisonProcess", Lost):
                agent = self.agent(root)
                async def run():
                    env = Environment(root)
                    await agent.setup(env)
                    await agent.run("Original task\n", env, AgentContext())
                with self.assertRaisesRegex(RuntimeError, "fake transport loss"):
                    asyncio.run(run())
                self.assertTrue(agent.ledger.state()["blocked"])
                self.assertEqual(agent.ledger.state()["spent_usd"], "unknown")
                with self.assertRaises(AccountingError):
                    agent.ledger.reserve("nonpilot-task#2", "pi-bare")

    def test_original_metadata_instruction_image_and_resources_must_match(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, _, _ = fixture(root)
            with patch("standard_full.MANIFEST", manifest):
                env = Environment(root)
                env.task_env_config.cpus = 99
                agent = self.agent(root)
                with self.assertRaisesRegex(ValueError, "environment"):
                    asyncio.run(agent.setup(env))
                self.assertEqual(agent.ledger.state()["starts"], 0)
                (root / "tasks/nonpilot-task/instruction.md").write_text("changed", encoding="utf8")
                with self.assertRaisesRegex(ValueError, "metadata"):
                    original_task(root / "tasks", "nonpilot-task")

    def test_duplicate_cell_and_historical_ledger_or_authority_drift_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            with patch("standard_full.MANIFEST", manifest):
                ledger = StandardLot(root / "ledger.jsonl", lot, authority)
                self.assertEqual(len(ledger.tasks), 132)
                ledger.reserve("nonpilot-task#1", "pi-bare")
                ledger.start("nonpilot-task#1", "pi-bare")
                ledger.settle("nonpilot-task#1", "pi-bare", "0.01", "e" * 64)
                with self.assertRaises(AccountingError):
                    ledger.reserve("nonpilot-task#1", "pi-bare")
                authority.write_text("changed", encoding="utf8")
                with self.assertRaises(ValueError):
                    StandardLot(root / "ledger.jsonl", lot, authority)

    def test_lot_refuses_ledger_alias_and_prior_evidence_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            data = json.loads(lot.read_text())
            with patch("standard_full.MANIFEST", manifest):
                with self.assertRaises(ValueError):
                    StandardLot(authority, lot, authority)
                data["prior_evidence"] = [{"path": str(root / "ledger.jsonl"),
                                            "sha256": "d" * 64}]
                lot.write_text(json.dumps(data), encoding="utf8")
                with self.assertRaises(ValueError):
                    StandardLot(root / "ledger.jsonl", lot, authority)

    def test_declared_exclusion_removes_cells_and_blocks_setup_before_start(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            data = json.loads(lot.read_text())
            data["excluded_tasks"] = ["nonpilot-task", "other-0"]
            lot.write_text(json.dumps(data), encoding="utf8")
            with patch("standard_full.MANIFEST", manifest):
                ledger = StandardLot(root / "ledger.jsonl", lot, authority)
                self.assertEqual(len(ledger.tasks), 128)
                self.assertNotIn("nonpilot-task#1", ledger.tasks)
                self.assertEqual(ledger.excluded_tasks, ("nonpilot-task", "other-0"))
                with self.assertRaises(AccountingError):
                    ledger.reserve("nonpilot-task#1", "pi-bare")
                agent = self.agent(root)
                with self.assertRaisesRegex(ValueError, "outside the authorized"):
                    asyncio.run(agent.setup(Environment(root)))
                self.assertEqual(agent.ledger.state()["starts"], 0)

    def test_exclusions_must_be_unique_manifest_tasks_and_leave_a_cell(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            names = ["nonpilot-task"] + [f"other-{n}" for n in range(65)]
            with patch("standard_full.MANIFEST", manifest):
                for bad in (["not-in-manifest"], ["other-1", "other-1"], "other-1", [3], names):
                    data = json.loads(lot.read_text())
                    data["excluded_tasks"] = bad
                    lot.write_text(json.dumps(data), encoding="utf8")
                    with self.assertRaisesRegex(ValueError, "exclusion"):
                        StandardLot(root / f"ledger-{len(str(bad))}.jsonl", lot, authority)

    def flat_lot(self, root, **extra):
        lot = root / "lot.json"
        data = json.loads(lot.read_text())
        data.update({"agent_policy": {"max_requests": 1000, "limit_usd": "9000"},
                     "cap_usd": "100000", "project_ceiling_usd": "1000000",
                     "unknown_cost_blocks": False, "max_in_flight": 4, **extra})
        lot.write_text(json.dumps(data), encoding="utf8")
        return lot

    def test_agent_failure_after_settlement_lets_harbor_run_the_verifier(self):
        class Failed(Process):
            failure = True
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, _, _ = fixture(root)
            with patch("standard_full.MANIFEST", manifest), patch("standard_full.ComparisonProcess", Failed):
                agent, context = self.agent(root), AgentContext()
                async def run():
                    env = Environment(root)
                    await agent.setup(env)
                    await agent.run("Original task\n", env, context)
                with self.assertRaisesRegex(NonZeroAgentExitCodeError, "fake transport loss"):
                    asyncio.run(run())
                self.assertEqual(agent.ledger.state()["spent_usd"], "0.01")

    def test_flat_rate_lot_uses_declared_agent_policy_and_does_not_block_on_unknown(self):
        class Lost(Process):
            failure = pending = True
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            self.flat_lot(root)
            Lost.phases = []
            with patch("standard_full.MANIFEST", manifest), patch("standard_full.ComparisonProcess", Lost):
                agent = self.agent(root)
                env = Environment(root)
                async def run():
                    await agent.setup(env)
                    await agent.run("Original task\n", env, AgentContext())
                with self.assertRaises(NonZeroAgentExitCodeError):
                    asyncio.run(run())
                state = agent.ledger.state()
                self.assertEqual(state["spent_usd"], "unknown")
                self.assertFalse(state["blocked"])
                journal = read_model_journal(root / "logs-1/model-usage.jsonl",
                    model_identity({**agent_init(agent), "trial_id": "nonpilot-task#1"}),
                    max_requests=1000, limit_usd="9000")
                self.assertFalse(journal["known"])
                ledger = StandardLot(root / "ledger.jsonl", lot, authority)
                self.assertEqual(ledger.per_start_usd, "9000")
                self.assertEqual(ledger.header["agent_policy"], {"max_requests": 1000, "limit_usd": "9000"})
                self.assertFalse(ledger.header["unknown_cost_blocks"])
                for name in ("other-0", "other-1", "other-2", "other-3"):
                    ledger.reserve(f"{name}#1", "pi-bare")
                with self.assertRaises(AccountingError):
                    ledger.reserve("other-4#1", "pi-bare")

    def test_flat_rate_policy_values_are_validated(self):
        bad = [{"agent_policy": {"max_requests": 0, "limit_usd": "9000"}},
               {"agent_policy": {"max_requests": 5001, "limit_usd": "9000"}},
               {"agent_policy": {"max_requests": 10, "limit_usd": "lots"}},
               {"agent_policy": {"max_requests": 10}},
               {"max_in_flight": 0}, {"max_in_flight": 17},
               {"unknown_cost_blocks": "no"},
               {"project_ceiling_usd": "100"}]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            with patch("standard_full.MANIFEST", manifest):
                for n, extra in enumerate(bad):
                    self.flat_lot(root, **extra)
                    with self.assertRaises((ValueError, AccountingError), msg=str(extra)):
                        StandardLot(root / f"ledger-{n}.jsonl", lot, authority)

    def test_default_lot_keeps_frozen_policy_serial_and_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            with patch("standard_full.MANIFEST", manifest):
                ledger = StandardLot(root / "ledger.jsonl", lot, authority)
                self.assertEqual(ledger.per_start_usd, "57")
                self.assertNotIn("agent_policy", ledger.header)
                ledger.reserve("other-0#1", "pi-bare")
                with self.assertRaises(AccountingError):
                    ledger.reserve("other-1#1", "pi-bare")

    def test_concurrent_admission_waits_for_a_briefly_held_lock(self):
        import threading
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            self.flat_lot(root)
            with patch("standard_full.MANIFEST", manifest):
                ledger = StandardLot(root / "ledger.jsonl", lot, authority)
                ledger.lock.mkdir()
                threading.Timer(0.3, ledger.lock.rmdir).start()
                ledger.reserve("other-0#1", "pi-bare")
                self.assertEqual(ledger.state()["pending"], 1)

    SKILLS_SHA = "cfda572172516a40b188f31ac5e8eb77c41ae2672458b0fb9e5039b235173c42"

    def skills_lot(self, root, **extra):
        lot = root / "lot.json"
        data = json.loads(lot.read_text())
        data.update({"arm": "skills-only",
                     "skills_snapshot": {"path": "comparison-skills.md", "sha256": self.SKILLS_SHA}, **extra})
        lot.write_text(json.dumps(data), encoding="utf8")
        return lot

    def test_skills_only_arm_appends_the_frozen_snapshot_and_records_the_arm(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            self.skills_lot(root)
            Process.phases = []
            with patch("standard_full.MANIFEST", manifest), patch("standard_full.ComparisonProcess", Process):
                agent, context = self.agent(root), AgentContext()
                env = Environment(root)
                async def run():
                    await agent.setup(env)
                    await agent.run("Original task\n", env, context)
                asyncio.run(run())
                ledger = StandardLot(root / "ledger.jsonl", lot, authority)
                self.assertEqual(ledger.arm, "skills-only")
                self.assertEqual(ledger.header["arms"], ["skills-only"])
                self.assertEqual(ledger.header["skills_sha256"], self.SKILLS_SHA)
                self.assertEqual(ledger.state()["starts"], 1)
            system = Process.phases[0][2]
            base = "Work only through sandbox_exec in the task environment. Complete the user task."
            snapshot = (Path(__file__).with_name("comparison-skills.md")).read_text(encoding="utf8")
            self.assertEqual(system, base + "\n\nFrozen local workflow skills:\n" + snapshot)
            self.assertEqual(Process.phases[0][1], "Original task\n")
            receipt = json.loads((root / "logs-1/standard-receipt.json").read_text())
            self.assertEqual(receipt["arm"], "skills-only")
            self.assertEqual(context.metadata["arm"], "skills-only")

    def test_skills_snapshot_binding_rejects_drift_escape_and_unknown_arms(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, lot, authority = fixture(root)
            bad = [{"skills_snapshot": {"path": "comparison-skills.md", "sha256": "0" * 64}},
                   {"skills_snapshot": {"path": "../README.md", "sha256": self.SKILLS_SHA}},
                   {"skills_snapshot": {"path": "missing-skills.md", "sha256": self.SKILLS_SHA}},
                   {"skills_snapshot": None},
                   {"arm": "ticket-driver-c1a"}]
            with patch("standard_full.MANIFEST", manifest):
                for n, extra in enumerate(bad):
                    self.skills_lot(root, **extra)
                    with self.assertRaises(ValueError, msg=str(extra)):
                        StandardLot(root / f"ledger-{n}.jsonl", lot, authority)
                data = json.loads(lot.read_text())
                data.update({"arm": "pi-bare", "skills_snapshot": {"path": "comparison-skills.md", "sha256": self.SKILLS_SHA}})
                lot.write_text(json.dumps(data), encoding="utf8")
                with self.assertRaises(ValueError):
                    StandardLot(root / "ledger-bare.jsonl", lot, authority)

    def test_setup_failure_or_instruction_drift_never_starts_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, _, _ = fixture(root)
            with patch("standard_full.MANIFEST", manifest), patch("standard_full.ComparisonProcess") as process:
                agent = self.agent(root)
                async def run():
                    env = Environment(root)
                    await agent.setup(env)
                    await agent.run("changed instruction", env, AgentContext())
                with self.assertRaisesRegex(ValueError, "instruction"):
                    asyncio.run(run())
                process.assert_not_called()
                self.assertEqual(agent.ledger.state()["starts"], 0)


if __name__ == "__main__":
    unittest.main()
