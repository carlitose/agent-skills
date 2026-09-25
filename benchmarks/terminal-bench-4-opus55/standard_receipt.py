"""Reconcile one completed original Harbor trial; never launches or retries a trial.

A refusal leaves the ledger's started cell unresolved. Both input files must be
kept outside Git; their combined SHA-256 binds the settled event to its sources.
"""

from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

from harbor.models.task.id import LocalTaskId
from harbor.models.task.task import Task
from harbor.models.trial.result import TrialResult
from pilot_ledger import MODEL, GateError, PilotLedger, frozen_bytes

AGENT_IMPORT = "harbor_pi_agent:StandardPiHarborAgent"


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def attributable_result(result: TrialResult, trajectory: dict, *, name: str,
                        task_dir: Path, ledger_path: Path, binding: dict,
                        original_checksum: str) -> dict:
    """Validate identity, verifier and Pi receipt; return only observed metrics."""
    row = next((item for item in binding["tasks"] if item["name"] == name), None)
    if row is None or not isinstance(result.task_id, LocalTaskId):
        raise GateError("trial is not a frozen local task")
    agent = result.config.agent
    verifier = result.config.verifier
    if (result.task_name != f"terminal-bench/{name}"
        or result.task_id.path.expanduser().resolve() != task_dir.resolve()
        or result.config.task.path is None
        or Path(result.config.task.path).expanduser().resolve() != task_dir.resolve()
        or result.task_checksum != original_checksum
        or result.config.timeout_multiplier != 1
        or result.config.agent_timeout_multiplier is not None
        or result.config.verifier_timeout_multiplier is not None
        or result.config.extra_instruction_paths or result.config.extra_instructions
        or result.config.environment.type.value != "docker"
        or result.config.environment.import_path is not None
        or result.config.environment.force_build or result.config.environment.kwargs
        or result.config.environment.mounts or result.config.environment.extra_docker_compose
        or any(getattr(result.config.environment, field) is not None for field in
               ("override_cpus", "override_memory_mb", "override_storage_mb", "override_gpus", "override_tpu"))
        or agent.import_path != AGENT_IMPORT or agent.model_name != MODEL
        or agent.skills or agent.override_timeout_sec is not None
        or agent.max_timeout_sec is not None
        or agent.load_trajectory is not None or agent.resume_trajectory
        or agent.kwargs.get("task_name") != name
        or Path(agent.kwargs.get("ledger_path", "")).expanduser().resolve() != ledger_path.resolve()
        or agent.kwargs.get("arm", "pi-bare") != "pi-bare"
        or verifier.disable or verifier.import_path is not None
        or verifier.override_timeout_sec is not None or verifier.max_timeout_sec is not None
        or result.verifier_environment_mode is None
        or result.verifier_environment_mode.value != "separate"
        or result.agent_info.name != "pi-harbor-standard"
        or result.agent_info.version != "0.2.0-standard"
        or result.agent_info.model_info is None
        or result.agent_info.model_info.provider != "openai-codex"
        or result.agent_info.model_info.name != "gpt-6-sol"):
        raise GateError("Harbor trial identity or original verifier differs")
    context = result.agent_result
    usage = trajectory.get("usage")
    receipt = trajectory.get("budget")
    if (result.exception_info is not None or result.step_results is not None
        or context is None or context.metadata is None
        or context.metadata.get("method") != "original-harbor-pi-bare"
        or context.metadata.get("task_name") != name
        or context.metadata.get("offline_probe") is not False
        or trajectory.get("method") != "standard"
        or trajectory.get("arm") != "pi-bare" or trajectory.get("task_name") != name
        or not isinstance(usage, dict) or not isinstance(receipt, dict)
        or receipt.get("ambiguous") is not False
        or receipt.get("limitUsd") != "60" or receipt.get("maxRequests") != 16
        or type(receipt.get("requests")) is not int or not 1 <= receipt["requests"] <= 16
        or type(receipt.get("pendingRequests")) is not int or receipt["pendingRequests"] != 0
        or type(receipt.get("maxPerRequestUsd")) not in (int, float)
        or not 0 < receipt["maxPerRequestUsd"] < float("inf")
        or abs(receipt["maxPerRequestUsd"] - 8.2) > 0.000001
        or not isinstance(trajectory.get("instruction"), str)
        or _digest(trajectory["instruction"].encode("utf-8")) != row["harbor_instruction_sha256"]
        or type(context.n_input_tokens) is not int or context.n_input_tokens < 0
        or type(context.n_output_tokens) is not int or context.n_output_tokens < 0
        or type(context.cost_usd) not in (int, float) or not 0 < context.cost_usd < float("inf")
        or usage.get("input_tokens") != context.n_input_tokens
        or usage.get("output_tokens") != context.n_output_tokens
        or type(usage.get("cost_usd")) not in (int, float)
        or abs(usage["cost_usd"] - context.cost_usd) > 0.000001
        or type(receipt.get("reservedUsd")) not in (int, float)
        or type(receipt.get("observedUsd")) not in (int, float)
        or not 0 < receipt["observedUsd"] <= receipt["reservedUsd"] <= 60
        or abs(receipt["reservedUsd"] - receipt["observedUsd"]) > 0.000001
        or abs(receipt["observedUsd"] - context.cost_usd) > 0.000001):
        raise GateError("missing or mismatched Pi cost and task receipt")
    reward = (result.verifier_result.rewards or {}).get("reward") if result.verifier_result else None
    timing = result.agent_execution
    if (type(reward) not in (int, float) or reward not in (0, 1)
        or timing is None or timing.started_at is None or timing.finished_at is None
        or timing.finished_at < timing.started_at):
        raise GateError("missing verifier decision or agent execution duration")
    elapsed = (timing.finished_at - timing.started_at).total_seconds()
    return {"status": "valid", "cost_usd": str(context.cost_usd),
            "input_tokens": context.n_input_tokens, "output_tokens": context.n_output_tokens,
            "elapsed_seconds": str(elapsed), "verifier_pass": bool(reward)}


def settle_completed_trial(*, ledger_path: Path, result_path: Path,
                           trajectory_path: Path, task_dir: Path) -> dict:
    """Settle one *completed* trial after checking its original task and files.

    Failures or missing files need manual cost adjudication; never convert absent
    cost/verifier evidence to a zero-cost or passing result.
    """
    root = Path(__file__).parent
    binding = json.loads((root / "standard-pilot.json").read_text(encoding="utf-8"))
    manifest_path = root / "manifest.json"
    if (binding.get("source_manifest_sha256") != _digest(frozen_bytes(manifest_path))
        or binding.get("method") != "original-harbor-pi-bare"):
        raise GateError("standard binding changed")
    task = Task(Path(task_dir))
    name = Path(task_dir).name
    row = next((item for item in binding["tasks"] if item["name"] == name), None)
    if (row is None or task.name != f"terminal-bench/{name}" or task.has_steps
        or _digest((task.task_dir / "task.toml").read_bytes()) != row["task_toml_sha256"]
        or _digest((task.task_dir / "instruction.md").read_bytes()) != row["raw_instruction_sha256"]
        or _digest(task.instruction.encode("utf-8")) != row["harbor_instruction_sha256"]
        or task.config.environment.docker_image != row["original_agent_image_ref"]
        or task.config.verifier.environment.docker_image != row["original_verifier_image_ref"]
        or task.config.verifier.environment_mode.value != "separate"
        or task.config.agent.timeout_sec != row["agent_timeout_sec"]):
        raise GateError("original task binding changed")
    raw_result = Path(result_path).read_bytes()
    raw_trajectory = Path(trajectory_path).read_bytes()
    result = TrialResult.model_validate_json(raw_result)
    trajectory = json.loads(raw_trajectory)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        original_checksum = task.checksum
    metrics = attributable_result(result, trajectory, name=name, task_dir=task.task_dir,
                                  ledger_path=Path(ledger_path), binding=binding,
                                  original_checksum=original_checksum)
    # The delimiter makes concatenations unambiguous. Both files remain outside Git.
    receipt_sha256 = _digest(raw_result + b"\0" + raw_trajectory)
    PilotLedger(ledger_path, manifest_path, standard=True).settle(
        name, "pi-bare", **metrics, receipt_sha256=receipt_sha256)
    return {"task": name, "receipt_sha256": receipt_sha256,
            "verifier_pass": metrics["verifier_pass"], "cost_usd": metrics["cost_usd"]}
