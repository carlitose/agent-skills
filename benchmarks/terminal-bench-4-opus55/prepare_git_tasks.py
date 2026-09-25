"""Derive a local task with only its agent image changed to the common Git overlay.

This is packaging, not a trial launcher. It never reads or rewrites verifier tests
or solutions; Harbor still owns the separate original verifier. The caller must
verify that the derived image ID is in Docker and use one prepared task for all
four arms. Git bootstrap inside /app is a separate, still-open TBF-02 gate.
"""

from __future__ import annotations

import copy
import hashlib
import re
import shutil
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_task(source: Path, target: Path, frozen: dict, binding: dict) -> dict:
    source, target = Path(source), Path(target)
    if (not source.is_dir() or source.is_symlink() or target.exists()
            or target.resolve().is_relative_to(REPO)):
        raise ValueError("source/destination is unsafe or already exists")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("linked source task files are not supported")
    config_path, instruction = source / "task.toml", source / "instruction.md"
    if (digest(config_path) != frozen["task_toml_sha256"]
            or digest(instruction) != frozen["instruction_sha256"]
            or binding["task"] != frozen["name"]
            or not IMAGE_ID.fullmatch(binding["derived_agent_image_id"])):
        raise ValueError("task, image or source digest differs from frozen input")
    original_text = config_path.read_text(encoding="utf-8")
    original = tomllib.loads(original_text)
    if (original["task"]["name"] != f"terminal-bench/{frozen['name']}"
            or original["environment"]["docker_image"] != binding["base_agent_image_ref"]
            or original["verifier"]["environment_mode"] != "separate"
            or original["verifier"]["environment"]["docker_image"] != binding["original_verifier_image_ref"]):
        raise ValueError("agent or verifier binding differs from downloaded task")
    old_image = binding["base_agent_image_ref"]
    if original_text.count(old_image) != 1:
        raise ValueError("agent image must occur exactly once")
    modified_text = original_text.replace(old_image, binding["derived_agent_image_id"])
    expected = copy.deepcopy(original)
    expected["environment"]["docker_image"] = binding["derived_agent_image_id"]
    if tomllib.loads(modified_text) != expected:
        raise ValueError("unexpected task configuration change")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    (target / "task.toml").write_bytes(modified_text.encode("utf-8"))
    return {"task": frozen["name"], "source_task_ref": frozen["registry_ref"],
            "original_task_toml_sha256": frozen["task_toml_sha256"],
            "derived_task_toml_sha256": digest(target / "task.toml"),
            "derived_agent_image_id": binding["derived_agent_image_id"],
            "original_verifier_image_ref": binding["original_verifier_image_ref"]}
