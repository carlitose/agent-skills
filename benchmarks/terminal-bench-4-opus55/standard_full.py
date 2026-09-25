"""Native Harbor/Pi adapter for one original task/repetition, never a scheduler.

The outside-Git lot must be supplied by an authorized caller. Its evidence hashes
bind that decision; they do not create consent. No lot or paid start is created by
importing this module or by preparation. Harbor owns artifacts and verification.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from decimal import Decimal

from harbor.agents.base import BaseAgent
from harbor.agents.installed.base import NonZeroAgentExitCodeError
from harbor.agents.options import AgentOptions
from harbor.models.agent.context import ModelUsage
from harbor.models.task.config import TaskConfig
from harbor.models.task.task import strip_canary
from comparison_accounting import ComparisonLedger, AccountingError, _append, _sha, read_model_journal
from comparison_transport import ComparisonProcess, model_identity
from harbor_pi_agent import MODEL
from pilot_ledger import amount, frozen_bytes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MANIFEST = HERE / "manifest.json"
METHOD = "original-harbor-full-pi-bare"
DATASET_REF = "terminal-bench/terminal-bench@sha256:39d9f44b40420cde8fdcc087579c0d72a7e14fa3656d603c3f0d22fb35e27732"
SYSTEM = "Work only through sandbox_exec in the task environment. Complete the user task."
SKILLS_PREFIX = "\n\nFrozen local workflow skills:\n"
ORIGINAL_ARMS = ("pi-bare", "skills-only")
# Closed historical ledgers. Their $60 assumptions are admission, not known billed costs.
PRIOR_DIGESTS = frozenset({
    "ce4b46c78577f7c80511aa0b612380ca6fb5051a1228441a5b26c0d470d82688",
    "6ae0764ffc7978f6427e5b23d315bfa3d9085036370e4fc75269008ad7ea13a8",
})
PRIOR_COMMITMENT_USD = "123.58286105200000007"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest():
    raw = frozen_bytes(MANIFEST)
    data = json.loads(raw)
    rows = data["tasks"]
    if (data.get("dataset_ref") != DATASET_REF or
            data.get("dataset_task_count") != 66 or len(rows) != 66 or
            len({r["name"] for r in rows}) != 66 or
            any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", r["name"]) for r in rows)):
        raise ValueError("full dataset manifest must contain all 66 unique original tasks")
    return data, hashlib.sha256(raw).hexdigest()


def original_task(task_root, name, *, directory=None):
    data, _ = manifest()
    row = next((r for r in data["tasks"] if r["name"] == name), None)
    if row is None:
        raise ValueError("task is outside frozen original dataset")
    directory = Path(directory) if directory is not None else Path(task_root) / name
    files = (directory / "task.toml", directory / "instruction.md")
    if (directory.is_symlink() or any(p.is_symlink() for p in files) or
            sha(files[0]) != row["task_toml_sha256"] or sha(files[1]) != row["instruction_sha256"]):
        raise ValueError("original task metadata changed")
    config = TaskConfig.model_validate_toml(files[0].read_text(encoding="utf8"))
    if (config.task is None or config.task.name != "terminal-bench/" + name or config.steps or
            config.environment.os.value != "linux"):
        raise ValueError("unsupported original task features; do not silently omit them")
    image = config.environment.docker_image
    if not image or not re.search(r"@sha256:[a-f0-9]{64}$", image):
        raise ValueError("original task needs its digest-pinned image")
    # Use the installed Harbor loader's decoding/newline semantics exactly.
    # Run Harbor with PYTHONUTF8=1 on Windows, as documented for the full lot.
    instruction = strip_canary(files[1].read_text())
    return config, instruction


class StandardLot(ComparisonLedger):
    """Passive, serial, fail-closed usage account; no launch or retry methods."""
    method = METHOD
    header_event = "standard-full"
    arms = ("pi-bare",)
    per_start_usd = "57"

    def __init__(self, path, lot_path, authority_path):
        path, lot_path, authority_path = Path(path), Path(lot_path), Path(authority_path)
        if (path.resolve() in {lot_path.resolve(), authority_path.resolve()} or
                any(p.resolve().is_relative_to(ROOT) or p.is_symlink() for p in (lot_path, authority_path))):
            raise ValueError("lot and authority must remain outside Git")
        data, manifest_sha = manifest()
        lot = json.loads(lot_path.read_text(encoding="utf8"))
        if (lot.get("schema") != 1 or lot.get("method") != METHOD or lot.get("model") != MODEL or
                lot.get("thinking") != "high" or lot.get("manifest_sha256") != manifest_sha or
                lot.get("prior_commitment_usd") != PRIOR_COMMITMENT_USD or
                type(lot.get("repetitions")) is not int or not 1 <= lot["repetitions"] <= 5 or
                not isinstance(lot.get("actor"), str) or not lot["actor"].strip() or
                sha(authority_path) != lot.get("authority_sha256")):
            raise ValueError("standard lot or human authority binding changed")
        prior = lot.get("prior_evidence")
        if (not isinstance(prior, list) or len(prior) != len(PRIOR_DIGESTS) or
                {row.get("sha256") for row in prior if isinstance(row, dict)} != PRIOR_DIGESTS):
            raise ValueError("both immutable historical ledgers must be bound")
        for row in prior:
            p = Path(row["path"])
            if (not p.is_absolute() or p.resolve() in {path.resolve(), lot_path.resolve(), authority_path.resolve()}
                    or p.is_symlink() or sha(p) != _sha(row["sha256"])):
                raise ValueError("prior consumption evidence changed")
        names = [r["name"] for r in data["tasks"]]
        excluded = lot.get("excluded_tasks", [])
        # A declared exclusion is lost coverage recorded in the ledger header, never a substitute.
        if (not isinstance(excluded, list) or any(not isinstance(n, str) or n not in names for n in excluded)
                or len(set(excluded)) != len(excluded) or len(excluded) >= len(names)):
            raise ValueError("exclusion must list unique manifest tasks and leave at least one")
        self.excluded_tasks = tuple(excluded)
        self.repetitions = lot["repetitions"]
        self.tasks = tuple(f'{name}#{n}' for name in names if name not in excluded
                           for n in range(1, self.repetitions + 1))
        self.max_starts = len(self.tasks)
        self.cap_usd = str(amount(lot["cap_usd"]))
        self._bind_policy(lot)
        self._bind_arm(lot)
        if amount(self.cap_usd) < amount(self.per_start_usd):
            raise ValueError("lot cannot admit even one full request budget")
        prior_sha = hashlib.sha256(json.dumps(prior, sort_keys=True).encode()).hexdigest()
        super().__init__(path, binding_sha256=sha(lot_path), authority_sha256=sha(authority_path),
                         prior_ledger_sha256=prior_sha, prior_commitment_usd=PRIOR_COMMITMENT_USD)

    POLICY_KEYS = ("agent_policy", "project_ceiling_usd", "unknown_cost_blocks", "max_in_flight")

    def _bind_policy(self, lot):
        """Optional human-declared policy (e.g. flat-rate tokens); absent keys keep the frozen defaults."""
        self.agent_policy = {"max_requests": 48, "limit_usd": "57"}
        self.declared_policy = any(key in lot for key in self.POLICY_KEYS)
        policy = lot.get("agent_policy", self.agent_policy)
        if (not isinstance(policy, dict) or set(policy) != {"max_requests", "limit_usd"} or
                type(policy["max_requests"]) is not int or not 1 <= policy["max_requests"] <= 5000 or
                not isinstance(policy["limit_usd"], str) or
                not re.fullmatch(r"\d+(?:\.\d{1,2})?", policy["limit_usd"]) or
                Decimal(policy["limit_usd"]) < Decimal("9")):
            raise ValueError("agent policy must declare 1-5000 requests and a decimal limit of at least $9")
        self.agent_policy = dict(policy)
        self.per_start_usd = policy["limit_usd"]
        blocks = lot.get("unknown_cost_blocks", True)
        in_flight = lot.get("max_in_flight", 1)
        if type(blocks) is not bool or type(in_flight) is not int or not 1 <= in_flight <= 16:
            raise ValueError("unknown-cost policy must be boolean and max_in_flight 1-16")
        self.unknown_cost_blocks, self.max_in_flight = blocks, in_flight
        self.lock_wait_seconds = 120 if in_flight > 1 else 0
        self.project_ceiling_usd = str(amount(lot.get("project_ceiling_usd", "1000")))

    def _bind_arm(self, lot):
        """Pi bare by default; skills-only appends one frozen snapshot bound by SHA-256."""
        self.arm = lot.get("arm", "pi-bare")
        snapshot = lot.get("skills_snapshot")
        self.skills_text = self.skills_sha256 = None
        if self.arm not in ORIGINAL_ARMS or ((self.arm == "skills-only") != ("skills_snapshot" in lot)):
            raise ValueError("original arm must be pi-bare, or skills-only with a skills snapshot")
        if self.arm == "skills-only":
            path = HERE / str((snapshot or {}).get("path", ""))
            if (not isinstance(snapshot, dict) or set(snapshot) != {"path", "sha256"} or
                    not path.resolve().is_relative_to(HERE) or path.is_symlink() or not path.is_file() or
                    sha(path) != _sha(snapshot["sha256"])):
                raise ValueError("skills snapshot must be an unchanged file in the benchmark directory")
            self.skills_text = path.read_text(encoding="utf8")
            self.skills_sha256 = hashlib.sha256(self.skills_text.encode("utf8")).hexdigest()
            if not self.skills_text:
                raise ValueError("skills snapshot must not be empty")
        self.arms = (self.arm,)

    def system_prompt(self):
        return SYSTEM if self.arm == "pi-bare" else SYSTEM + SKILLS_PREFIX + self.skills_text

    def _header_extra(self):
        extra = {"skills_sha256": self.skills_sha256} if self.arm == "skills-only" else {}
        if not self.declared_policy:
            return extra
        return {**extra, "agent_policy": self.agent_policy, "project_ceiling_usd": self.project_ceiling_usd,
                "unknown_cost_blocks": self.unknown_cost_blocks, "max_in_flight": self.max_in_flight}


class FullOptions(AgentOptions):
    repetition: int = 1
    lot_path: str
    authority_path: str
    ledger_path: str


class FullStandardPiHarborAgent(BaseAgent):
    options_model = FullOptions

    def __init__(self, logs_dir, model_name=None, **kwargs):
        super().__init__(logs_dir, model_name=model_name, **kwargs)
        if self.model_name != MODEL or self.logs_dir.resolve().is_relative_to(ROOT):
            raise ValueError("original Pi requires frozen model and external receipts")
        if self.load_trajectory or self.extra_env:
            raise ValueError("original Pi does not inject trajectory or provider environment")
        self.ledger = StandardLot(self.options.ledger_path, self.options.lot_path, self.options.authority_path)
        if not 1 <= self.options.repetition <= self.ledger.repetitions:
            raise ValueError("repetition is outside the authorized original lot")
        self.config = self.instruction = self.cell = self.task_name = None
        self.ready = False

    @staticmethod
    def name():
        return "pi-harbor-original-full"

    def version(self):
        return "0.1.0"

    def _validate_environment(self, environment):
        directory = environment.environment_dir.parent
        public = TaskConfig.model_validate_toml((directory / "task.toml").read_text(encoding="utf8"))
        if public.task is None:
            raise ValueError("original task has no package identity")
        config, instruction = original_task(directory.parent, public.task.short_name, directory=directory)
        # Harbor forwards task-declared skills/MCP alongside agent options. Accept only
        # the exact original declarations, never an added host skill or MCP server.
        if (self.skills_dir != config.environment.skills_dir or
                self.mcp_servers != config.environment.mcp_servers):
            raise ValueError("agent-injected skills or MCP differ from the original task")
        if (environment.task_env_config != config.environment or
                (self.config is not None and (config != self.config or instruction != self.instruction))):
            raise ValueError("original environment or metadata changed")
        self.config, self.instruction = config, instruction
        self.task_name = config.task.short_name
        self.cell = f"{self.task_name}#{self.options.repetition}"
        if self.cell not in self.ledger.tasks:
            raise ValueError("task/repetition is outside the authorized original lot")

    async def setup(self, environment):
        self._validate_environment(environment)
        # Capability probe only: no installation, Git assumptions, uploads or /app assumption.
        result = await environment.exec(
            "timeout --signal=TERM --kill-after=1s 1s /bin/sh -c 'exit 0'", timeout_sec=15)
        if result.return_code != 0:
            raise RuntimeError("original image lacks the timeout/shell capability; no overlay permitted")
        self.ready = True

    async def run(self, instruction, environment, context):
        self._validate_environment(environment)
        if not self.ready or instruction != self.instruction:
            raise ValueError("setup or original Harbor instruction differs")
        # Re-read authority/prior bindings before admission, including setup-to-run drift.
        self.ledger = StandardLot(self.options.ledger_path, self.options.lot_path, self.options.authority_path)
        arm = self.ledger.arm
        self.ledger.reserve(self.cell, arm)
        self.ledger.start(self.cell, arm)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        init = dict(type="init", method=METHOD, model=MODEL, thinking="high", arm=arm,
                    task_name=self.task_name, trial_id=self.cell, instruction=instruction,
                    budget={"limit_usd": self.ledger.agent_policy["limit_usd"],
                            "max_requests": self.ledger.agent_policy["max_requests"]})
        if arm == "skills-only":
            init["skills_sha256"] = self.ledger.skills_sha256
        failure = final = None
        try:
            async with ComparisonProcess(self.logs_dir, environment, init) as process:
                result = await process.phase("builder", instruction, self.ledger.system_prompt(), tools="sandbox")
                final = await process.finish(result["status"])
                if result["status"] != "completed" or final["status"] != "completed":
                    raise RuntimeError("Pi task phase did not complete")
        except BaseException as error:
            failure = error
        # An interrupted settlement remains pending and blocks later starts.
        model = self._usage(init)
        if failure is None and (not model["known"] or not model["terminal"] or
                model["budget"]["requests"] == 0 or
                any(final["usage"].get(k) != model[k] for k in ("cost_usd", "input_tokens", "output_tokens"))):
            failure = RuntimeError("original Pi terminal usage is not attributable")
        metadata = {"method": METHOD, "arm": arm, "task": self.task_name, "repetition": self.options.repetition,
                    "model_journal_sha256": model.get("sha256"),
                    "status": "failed" if failure else "completed"}
        if model["known"]:
            context.n_input_tokens = model["input_tokens"]
            context.n_output_tokens = model["output_tokens"]
            context.cost_usd = model["cost_usd"]
            context.model_usage = {MODEL: ModelUsage(n_input_tokens=model["input_tokens"],
                n_output_tokens=model["output_tokens"], cost_usd=model["cost_usd"])}
        context.metadata = metadata
        receipt = self.logs_dir / "standard-receipt.json"
        _append(receipt, {**metadata, "model": model,
            "error_type": type(failure).__name__ if failure else None,
            "verifier": "owned by Harbor; no score inferred by adapter"}, "x")
        self.ledger.settle(self.cell, arm, str(model["cost_usd"]) if model["known"] else None, sha(receipt))
        if isinstance(failure, Exception):
            # Like an installed agent's non-zero exit: Harbor records it and still runs the verifier.
            raise NonZeroAgentExitCodeError(f"original Pi agent failed: {failure}") from failure
        if failure is not None:
            raise failure

    def _usage(self, init):
        try:
            status = json.loads((self.logs_dir / "host-status.json").read_text(encoding="utf8"))
            if status.get("process_stopped") is not True or status.get("trial_id") != self.cell:
                raise AccountingError("model endpoint termination is unconfirmed")
            return read_model_journal(self.logs_dir / "model-usage.jsonl", model_identity(init),
                                      max_requests=init["budget"]["max_requests"],
                                      limit_usd=init["budget"]["limit_usd"])
        except (AccountingError, OSError, ValueError):
            return {"known": False, "cost_usd": None, "terminal": False}
