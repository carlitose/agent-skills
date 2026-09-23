"""Resume only a frozen semantic gate after an explicit operator approval input."""
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path

from autopilot.command_capture import CaptureFailure, capture_command
from autopilot.git_ops import repository_root, run_git, semantic_candidate_ref
from arbiter import questions
from driver import ROOT, Run, dump, integrate_candidate, sha


def approve(repo: Path, run_id: str, actor: str, reason: str) -> dict:
    if not actor.strip() or not reason.strip():
        raise ValueError("approve needs non-empty actor and reason")
    repo = repo.resolve(strict=True)
    if repository_root(repo) != repo:
        raise ValueError("--repo must be a repository root")
    from autopilot.git_ops import common_git_dir
    directory = common_git_dir(repo) / "ticket-driver" / "runs" / run_id
    original = directory / "summary.json"
    result_path = directory / "approval-result.json"
    if not original.is_file() or result_path.exists():
        raise ValueError("gate summary missing or already resolved")
    summary = json.loads(original.read_text(encoding="utf-8"))
    if summary.get("run_id") != run_id or summary.get("status") != "gated" or summary.get("candidate") not in ("c2a", "c2b"):
        raise ValueError("no resumable c2 semantic gate")
    worktree = Path(summary["worktree"])
    if not worktree.exists() or run_git(worktree, "rev-parse", "HEAD") != summary["base_commit"]:
        raise ValueError("gated worktree drift")
    policy_bytes = (ROOT / "policy.json").read_bytes()
    if sha(policy_bytes) != summary["policy_sha256"]:
        raise ValueError("policy changed since gate")
    policy = json.loads(policy_bytes)
    if questions(ROOT)[1] != summary["question_hashes"]:
        raise ValueError("question contracts changed since gate")
    candidate = semantic_candidate_ref(worktree, summary["source_digest"])
    if candidate.candidate_tree_oid != summary["candidate_tree_oid"]:
        raise ValueError("gated candidate tree drift")
    run = Run(directory)
    argv = [sys.executable if arg == "python" else arg for arg in policy["test_command"]]
    started = time.monotonic()
    try:
        stdout, stderr, code = capture_command(argv, cwd=worktree,
            timeout_seconds=policy["test_timeout_seconds"], max_output_bytes=policy["max_output_bytes"])
        test = (stdout, stderr, code, time.monotonic()-started, None)
    except CaptureFailure as error:
        test = (b"", error.stderr, None, time.monotonic()-started, error.reason)
    receipt = run.receipt("approval-tests", argv, worktree, test, max_bytes=policy["max_output_bytes"])
    if test[2] != 0:
        raise ValueError("approved candidate failed re-executed tests; no integration")
    run_git(worktree, "add", "-A")
    if run_git(worktree, "write-tree") != candidate.candidate_tree_oid:
        raise ValueError("approved candidate changed during tests")
    commit = integrate_candidate(repo, worktree, summary["base_commit"], candidate.candidate_tree_oid, policy, run_id)
    result = {"run_id": run_id, "status": "integrated", "candidate_commit": commit,
              "candidate_tree_oid": candidate.candidate_tree_oid, "actor": actor, "reason": reason,
              "observed_test_receipt": receipt, "original_summary_sha256": sha(original.read_bytes())}
    tmp = directory / (".approval-" + uuid.uuid4().hex)
    dump(tmp, result)
    if result_path.exists():
        raise ValueError("approval result already exists")
    os.replace(tmp, result_path)
    run.event("human-approval", actor=actor, reason=reason, commit=commit)
    return result
