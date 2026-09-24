"""Freeze public registry metadata without exposing benchmark tests or solutions.

Usage: python -B freeze_manifest.py REGISTRY_SHOW_JSON DOWNLOADED_TASKS
Prints one deterministic JSON object. No network or model requests occur here.
"""

import hashlib
import json
import pathlib
import re
import sys

import tomllib

DATASET = "terminal-bench/terminal-bench"
PILOT = ("html-js-filter", "interleaved-vigenere", "wal-recovery-ordering")
DIGEST = re.compile(r"(?:sha256:)?[a-f0-9]{64}\Z")


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(registry_path: pathlib.Path, downloaded: pathlib.Path) -> dict:
    raw = registry_path.read_bytes()
    registry = json.loads(raw)
    if registry["package"] != DATASET or registry["type"] != "dataset":
        raise ValueError("wrong registry package")
    digest = registry["content_hash"]
    if not DIGEST.fullmatch(digest) or registry.get("yanked_at"):
        raise ValueError("invalid or yanked dataset digest")
    rows = registry["tasks"]
    if not rows or len(rows) != len({r["task_version_id"] for r in rows}):
        raise ValueError("missing or duplicate registry task versions")
    tasks = []
    for row in rows:
        if not row["available"] or not row["task_version"]:
            raise ValueError("unavailable task in registry version")
        version = row["task_version"]
        name = version["package"]["name"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            raise ValueError("unsafe task name")
        if version["package"]["org"]["name"] != "terminal-bench":
            raise ValueError("foreign task organization")
        task_hash = version["content_hash"]
        if not DIGEST.fullmatch(task_hash):
            raise ValueError("invalid task content digest")
        directory = downloaded / name
        toml_file = directory / "task.toml"
        instruction = directory / "instruction.md"
        if directory.is_symlink() or toml_file.is_symlink() or instruction.is_symlink():
            raise ValueError(f"linked task metadata: {name}")
        if not toml_file.is_file() or not instruction.is_file():
            raise ValueError(f"missing downloaded task metadata: {name}")
        task = tomllib.loads(toml_file.read_text(encoding="utf-8"))
        if task["task"]["name"] != f"terminal-bench/{name}":
            raise ValueError(f"task name mismatch: {name}")
        env = task.get("environment", {})
        verifier = task.get("verifier", {}).get("environment", {})
        agent_gpu = int(env.get("gpus", 0))
        verifier_gpu = int(verifier.get("gpus", 0))
        if agent_gpu < 0 or verifier_gpu < 0:
            raise ValueError(f"negative GPU request: {name}")
        tasks.append({
            "name": name,
            "registry_ref": f"terminal-bench/{name}@sha256:{task_hash.removeprefix('sha256:')}",
            "task_toml_sha256": sha256(toml_file),
            "instruction_sha256": sha256(instruction),
            "agent_gpus": agent_gpu,
            "verifier_gpus": verifier_gpu,
        })
    tasks.sort(key=lambda item: item["name"])
    if len(tasks) != len({t["name"] for t in tasks}):
        raise ValueError("duplicate task names")
    by_name = {t["name"]: t for t in tasks}
    if any(by_name[name]["agent_gpus"] or by_name[name]["verifier_gpus"] for name in PILOT):
        raise ValueError("pilot requires unavailable GPU")
    return {
        "schema": 1,
        "source": "Harbor Hub version show --tasks --json; local Harbor dataset download",
        "source_registry_json_sha256": hashlib.sha256(raw).hexdigest(),
        "registry_version_id": registry["id"],
        "registry_revision": registry["revision"],
        "registry_tags_observed": registry["tags"],
        "dataset_ref": f"{DATASET}@{digest}",
        "dataset_task_count": len(tasks),
        "gpu_exclusions": [t["name"] for t in tasks if t["agent_gpus"] or t["verifier_gpus"]],
        "pilot_tasks": list(PILOT),
        "tasks": tasks,
    }


if __name__ == "__main__":
    print(json.dumps(build(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])), sort_keys=True, indent=2))
