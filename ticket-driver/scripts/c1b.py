"""Fresh review/QA leaf loop, independent of the builder session."""
from __future__ import annotations

import hashlib
import shutil
import sys
import time
from pathlib import Path

from autopilot.command_capture import CaptureFailure, capture_command
from autopilot.git_ops import run_git, semantic_candidate_ref
from findings import parse_findings, planned_commands
from leaf import invoke, render_prompt, usage


def _command(argv: list[str], worktree: Path, policy: dict) -> tuple:
    started = time.monotonic()
    try:
        stdout, stderr, code = capture_command(argv, cwd=worktree,
            timeout_seconds=policy["test_timeout_seconds"], max_output_bytes=policy["max_output_bytes"])
        return stdout, stderr, code, time.monotonic()-started, None
    except CaptureFailure as error:
        return b"", error.stderr, None, time.monotonic()-started, error.reason


def _product_fingerprint(worktree: Path) -> dict[str, str]:
    """Detect a reviewer modifying the candidate outside its one authored artifact directory."""
    result = {}
    for path in worktree.rglob("*"):
        relative = path.relative_to(worktree)
        if relative.parts[0] == ".ticket-driver" or not (path.is_file() or path.is_symlink()):
            continue
        result[str(relative)] = hashlib.sha256(path.read_bytes() if not path.is_symlink()
                                                  else str(path.readlink()).encode()).hexdigest()
    return result


def _leaf(run, summary: dict, state: dict, worktree: Path, policy: dict,
          leaf: str | None, role: str, attempt: int, prompt: str, template_sha: str) -> bool:
    name = f"{role}-{attempt}"
    session = run.path / "sessions" / name
    argv, out, err, code, duration, failure = invoke(leaf, policy, session, prompt, worktree)
    shown = argv[:-1] + ["<prompt:sha256:" + hashlib.sha256(prompt.encode()).hexdigest() + ">"]
    summary["receipts"][name] = run.receipt(name, shown, worktree, (out, err, code, duration, failure),
                                            max_bytes=policy["max_output_bytes"])
    summary["leaves"][name] = usage(session)
    summary.setdefault("prompt_hashes", {})[role] = template_sha
    if failure or code != 0:
        summary["failure"] = "leaf-timeout" if failure == "timeout" else f"{role}-leaf"
        return False
    return True


def cycle(run, summary: dict, state: dict, worktree: Path, policy: dict, leaf: str | None,
          builder_prompt: str, root: Path, *, typed_arbiter: bool = False) -> bool:
    """Two builder passes at most; each review and QA has a distinct fresh session."""
    products = worktree / ".ticket-driver"
    for attempt in (1, 2):
        if attempt == 2:
            builder_prompt += "\nRead .ticket-driver/retry.md before changing files; it contains observed blockers or test output.\n"
        if not _leaf(run, summary, state, worktree, policy, leaf, "builder", attempt,
                     builder_prompt, summary["prompt_sha256"]):
            return False
        semantic_candidate_ref(worktree, state["digest"])
        diff = run_git(worktree, "diff", "--cached", "--", ".", ":(exclude).ticket-driver/**")
        if len(diff.encode()) > 32768:
            summary["status"], summary["failure"] = "gated", "candidate diff exceeds review input bound"
            return False
        products.mkdir(exist_ok=True)
        for role in ("reviewer", "qa"):
            template = root / "prompts" / f"{role}.md"
            prompt, template_sha = render_prompt(template, kind=state["kind"],
                source_digest=state["digest"], task_text=state["text"])
            prompt = prompt.replace("{diff_text}", diff)
            before_review = _product_fingerprint(worktree) if role == "reviewer" else None
            if not _leaf(run, summary, state, worktree, policy, leaf, role, attempt,
                         prompt, template_sha):
                return False
            if before_review is not None and _product_fingerprint(worktree) != before_review:
                summary["status"], summary["failure"] = "gated", "reviewer modified candidate"
                return False
            artifact = products / ("review.md" if role == "reviewer" else "qa-plan.md")
            if not artifact.is_file():
                summary["status"], summary["failure"] = "gated", f"{role} artifact missing"
                return False
            name = f"{role}-artifact-{attempt}"
            summary["receipts"][name] = run.authored_receipt(name, artifact)
            text = artifact.read_text(encoding="utf-8")
            if role == "reviewer":
                findings = parse_findings(text)
                run.event("findings", attempt=attempt, **findings)
                if findings["state"] == "unparsed" and not typed_arbiter:
                    summary["status"], summary["failure"] = "gated", "findings: unparsed; no semantic arbiter in c1b"
                    return False
                if any(row["severity"] == "blocker" for row in findings["findings"]):
                    if attempt == 2:
                        summary["status"], summary["failure"] = "stopped", "review blocker on second pass"
                        return False
                    (products / "retry.md").write_text(text, encoding="utf-8", newline="\n")
                    break
            else:
                try:
                    commands = planned_commands(text)
                except ValueError as error:
                    summary["status"], summary["failure"] = "gated", str(error)
                    return False
                tree_before_tests = semantic_candidate_ref(worktree, state["digest"]).candidate_tree_oid
                for index, argv in enumerate([*commands, [sys.executable if arg == "python" else arg for arg in policy["test_command"]]], start=1):
                    name = f"tests-{attempt}-{index}"
                    result = _command(argv, worktree, policy)
                    summary["receipts"][name] = run.receipt(name, argv, worktree, result,
                                                               max_bytes=policy["max_output_bytes"])
                    if result[2] != 0:
                        if attempt == 2:
                            summary["status"], summary["failure"] = "stopped", "tests failed on second pass"
                            return False
                        tail = (result[1] + result[0])[-4096:].decode("utf-8", errors="replace")
                        (products / "retry.md").write_text(f"Observed test failure: {name}\n{tail}\n", encoding="utf-8", newline="\n")
                        break
                else:
                    run_git(worktree, "add", "-A")
                    if run_git(worktree, "write-tree") != tree_before_tests:
                        summary["status"], summary["failure"] = "gated", "tests-mutated-candidate"
                        return False
                    shutil.rmtree(products)
                    run_git(worktree, "add", "-A")
                    return True
                break  # a test failed; retry builder
    return False
