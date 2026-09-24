"""One-ticket local driver. Git, subprocess results and receipts belong to this process."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path

from autopilot.candidate_contract import semantic_candidate
from autopilot.command_capture import CaptureFailure, capture_command
from autopilot.git_ops import GitError, common_git_dir, repository_root, run_git, semantic_candidate_ref, worktree_is_clean
from autopilot.ticket_contract import parse_ticket_markdown, ticket_source_digest
from leaf import invoke, pi_command, render_prompt, usage
from findings import parse_findings, planned_commands
from state import review as review_state, qa as qa_state, verify as verify_state, retry as retry_state

ROOT = Path(__file__).resolve().parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(path: Path, value: dict) -> None:
    path.write_bytes((json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8"))


class Run:
    def __init__(self, directory: Path):
        self.path = directory
        (directory / "receipts").mkdir(parents=True, exist_ok=True)
        self.ledger = directory / "ledger.jsonl"

    def event(self, event_type: str, **facts) -> None:
        with self.ledger.open("ab") as output:
            output.write((json.dumps({"event": event_type, **facts}, sort_keys=True) + "\n").encode("utf-8"))
            output.flush()
            os.fsync(output.fileno())

    def receipt(self, name: str, argv: list[str], cwd: Path, result: tuple,
                *, max_bytes: int) -> dict:
        stdout, stderr, code, duration, failure = result
        # The digest covers the exact bounded output persisted here, not a model's report.
        value = {"kind": "observed", "argv": argv, "cwd": str(cwd), "exit_code": code,
                 "duration_seconds": duration, "failure": failure,
                 "stdout": stdout[:max_bytes].decode("utf-8", errors="replace"),
                 "stderr": stderr[:max_bytes].decode("utf-8", errors="replace")}
        path = self.path / "receipts" / f"{name}.json"
        if path.exists():
            raise ValueError("receipt already exists")
        dump(path, value)
        record = {"path": str(path.relative_to(self.path)), "sha256": sha(path.read_bytes())}
        self.event("receipt", id=name, **record)
        return record

    def authored_receipt(self, name: str, path: Path) -> dict:
        """Copy authored Markdown without calling it executed evidence."""
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing {name} artifact")
        data = path.read_bytes()
        if len(data) > 65536:
            raise ValueError(f"{name} artifact exceeds 65536 bytes")
        artifact = self.path / "receipts" / f"{name}.md"
        if artifact.exists():
            raise ValueError("authored receipt already exists")
        artifact.write_bytes(data)
        record = {"kind": "authored-by-model", "path": str(artifact.relative_to(self.path)),
                  "sha256": sha(artifact.read_bytes())}
        self.event("artifact", id=name, **record)
        return record

    def finish(self, value: dict) -> dict:
        if (self.path / "summary.json").exists():
            raise ValueError("summary.json already exists")
        tmp = self.path / (".summary-" + uuid.uuid4().hex)
        dump(tmp, value)
        os.replace(tmp, self.path / "summary.json")
        return value


def preflight(args) -> dict:
    repo = Path(args.repo).resolve(strict=True)
    if repository_root(repo) != repo:
        raise ValueError("--repo must be a repository root")
    branch = run_git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not worktree_is_clean(repo):
        raise ValueError("target branch is dirty")
    target = run_git(repo, "rev-parse", "HEAD")
    base = run_git(repo, "rev-parse", "--verify", f"{args.base}^{{commit}}")
    if base != target:
        raise ValueError("base must equal target HEAD")
    policy_path = ROOT / "policy.json"
    raw_policy = policy_path.read_bytes()
    policy = json.loads(raw_policy)
    if policy.get("schema") != 1:
        raise ValueError("invalid policy schema")
    if args.candidate not in ("c1a", "c1b", "c2a", "c2b", "c3a", "c3b", "c4"):
        raise ValueError("candidate not implemented")
    if args.ticket:
        source = Path(args.ticket).resolve(strict=True)
        text = source.read_text(encoding="utf-8")
        envelope = parse_ticket_markdown(text, source=str(source)).envelope
        kind = f"ticket {envelope['ticket_id']}"
        digest = ticket_source_digest(source)
        if envelope["blocked_by"]:
            raise ValueError("ticket has unresolved dependencies; driver accepts only ready tickets")
    else:
        source = Path(args.task).resolve(strict=True)
        text = source.read_text(encoding="utf-8")
        kind, digest = "task", sha(source.read_bytes())
    if not args.leaf:
        authorize_live(args.live_authorization, repo, args.candidate)
        pi_command()  # Reject unsupported shims before a worktree or ledger exists.
    elif args.live_authorization:
        raise ValueError("--leaf fake runs must not use live authorization")
    run_id = args.run_id or f"tdr-{int(time.time())}-{uuid.uuid4().hex[:10]}"
    if not run_id.isascii() or not run_id.replace("-", "").isalnum() or len(run_id) > 80:
        raise ValueError("invalid run_id")
    directory = common_git_dir(repo) / "ticket-driver" / "runs" / run_id
    if (directory / "summary.json").exists():
        raise ValueError("summary.json already exists")
    if directory.exists():
        raise ValueError("run_id already exists")
    return dict(repo=repo, branch=branch, base=base, tree=run_git(repo, "rev-parse", "HEAD^{tree}"),
                policy=policy, policy_hash=sha(raw_policy), source=source, text=text, kind=kind,
                digest=digest, directory=directory, run_id=run_id)


def authorize_live(path: str | None, repo: Path, candidate: str) -> None:
    if not path:
        raise ValueError("live run requires separate --live-authorization for this batch")
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("repository") != str(repo) or candidate not in value.get("candidates", []) or not value.get("batch_id"):
        raise ValueError("live authorization does not cover repository and candidate")
    if candidate.startswith(("c2", "c3")) or candidate == "c4":
        if value.get("jev_spend_authorized") is not True:
            raise ValueError("live Jev candidate requires explicit Jev spend authorization")
    # A local file is only an input; the operator must verify its human provenance and batch scope.


def create_worktree(repo: Path, run_id: str, base: str) -> Path:
    """Separate parent from ticket-autopilot's GC-owned worktrees."""
    parent = repo.parent / f".{repo.name}-ticket-driver-worktrees"
    target = parent / run_id
    if target.exists():
        raise ValueError("driver worktree path already exists")
    parent.mkdir(exist_ok=True)
    run_git(repo, "worktree", "add", "--detach", str(target), base)
    return target.resolve()


def semantic_gates(run: Run, summary: dict, state: dict, repo: Path, worktree: Path,
                   policy: dict, leaf: str | None) -> bool:
    """A process-owned suite is necessary; typed semantic checks are separate from it."""
    from cascade import Cascade, _append
    judge = Cascade(run, summary, repo, worktree, policy, ROOT, leaf)
    diff = run_git(worktree, "diff", "--cached", "HEAD")[:32768]
    reviews = [key for key in summary["receipts"] if key.startswith("reviewer-artifact-")]
    prose = (run.path / summary["receipts"][reviews[-1]]["path"]).read_text(encoding="utf-8") if reviews else "No independent reviewer in c2a; constructor prose is not gate evidence."
    result = judge.batch(review_state(state["text"], diff, prose),
                         ["review.findings_block", "review.scope_complete"])
    if summary["status"] == "gated":
        return False
    tests = [key for key in summary["receipts"] if key == "tests" or key.startswith("tests-")]
    if not tests:
        raise ValueError("no observed test receipt")
    receipt = json.loads((run.path / summary["receipts"][tests[-1]]["path"]).read_text(encoding="utf-8"))
    files = run_git(worktree, "diff", "--cached", "--name-only", "HEAD").splitlines()
    evidence = judge.batch(qa_state(receipt["argv"], receipt, files), ["qa.evidence_class"])
    supported = judge.batch(verify_state("The mandatory project test command returned exit code 0", receipt),
                            ["verify.claim_supported"])
    if summary["status"] == "gated":
        return False
    valid = (result["review.findings_block"] == "no" and result["review.scope_complete"] == "yes"
             and evidence["qa.evidence_class"] not in ("uncertain", "unknown")
             and supported["verify.claim_supported"] == "yes")
    if not valid:
        reason = f"semantic gate: review={result}, evidence={evidence}, verify={supported}"
        summary["status"], summary["failure"] = "gated", reason
        run.event("gate", reason=reason)
        _append(run.path / "gates.jsonl", {"status": "open", "reason": reason})
    return valid


def integrate_candidate(repo: Path, worktree: Path, base: str, tree: str,
                        policy: dict, run_id: str) -> str:
    """One local fast-forward integrator shared by run and human-approved continuation."""
    run_git(worktree, "-c", f"user.name={policy['commit_author']}", "-c",
            f"user.email={policy['commit_email']}", "commit", "-qm", f"ticket-driver {run_id}")
    commit = run_git(worktree, "rev-parse", "HEAD")
    if run_git(worktree, "rev-parse", "HEAD^{tree}") != tree:
        raise ValueError("commit tree differs from observed candidate")
    run_git(worktree, "merge-base", "--is-ancestor", base, commit)
    if run_git(repo, "rev-parse", "HEAD") != base or not worktree_is_clean(repo):
        raise ValueError("integration: target moved or is dirty")
    run_git(repo, "merge", "--ff-only", commit)
    if run_git(repo, "rev-parse", "HEAD") != commit or run_git(repo, "rev-parse", "HEAD^{tree}") != tree:
        raise ValueError("integrated head/tree mismatch")
    return commit


def risk_phase(run: Run, summary: dict, state: dict, repo: Path, worktree: Path,
               policy: dict, leaf: str | None, candidate, builder_prompt: str):
    """Directed findings reenter the one-retry builder loop, not a self-signed gate."""
    from c1b import _product_fingerprint, cycle, _leaf, _command
    from risk import assess, directed_review
    mode = summary["candidate"]
    for attempt in (1, 2):
        selected = assess(run, summary, repo, worktree, policy, ROOT, candidate)
        before_review = _product_fingerprint(worktree)
        findings = directed_review(run, summary, state, worktree, policy, ROOT, leaf, selected, attempt=attempt)
        if summary["status"] == "gated":
            return None
        if _product_fingerprint(worktree) != before_review:
            summary["status"], summary["failure"] = "gated", "directed reviewer modified candidate"
            return None
        if findings["state"] == "unparsed" and mode != "c4":
            summary["status"], summary["failure"] = "gated", "directed findings: unparsed"
            return None
        blockers = [item for item in findings["findings"] if item["severity"] == "blocker"]
        if mode == "c4" or not blockers:
            run_git(worktree, "add", "-A")
            if run_git(worktree, "write-tree") != candidate.candidate_tree_oid:
                summary["status"], summary["failure"] = "gated", "directed review changed candidate"
                return None
            return candidate
        used_retry = "builder-2" in summary["leaves"]
        if attempt == 2 or used_retry:
            summary["status"], summary["failure"] = "stopped", "directed review blocker after retry"
            return None
        products = worktree / ".ticket-driver"
        products.mkdir(exist_ok=True)
        (products / "retry.md").write_text("Directed review blocker:\n" + "\n".join(
            f"[{row['severity']}] {row['path']}{':' + str(row['line']) if row['line'] is not None else ''} - {row['text']}"
            for row in blockers) + "\n",
            encoding="utf-8", newline="\n")
        if mode == "c3b":
            if not cycle(run, summary, state, worktree, policy, leaf, builder_prompt, ROOT,
                         typed_arbiter=True, start_at=2):
                return None
        else:
            retry_prompt = builder_prompt + "\nRead .ticket-driver/retry.md and correct the directed blocker before stopping.\n"
            if not _leaf(run, summary, state, worktree, policy, leaf, "builder", 2,
                         retry_prompt, summary["prompt_sha256"]):
                return None
            original = semantic_candidate_ref(worktree, state["digest"])
            argv = [sys.executable if arg == "python" else arg for arg in policy["test_command"]]
            result = _command(argv, worktree, policy)
            summary["receipts"]["tests-risk-retry"] = run.receipt("tests-risk-retry", argv, worktree,
                result, max_bytes=policy["max_output_bytes"])
            if result[2] != 0:
                summary["status"], summary["failure"] = "stopped", "tests failed after directed retry"
                return None
            run_git(worktree, "add", "-A")
            if run_git(worktree, "write-tree") != original.candidate_tree_oid:
                summary["status"], summary["failure"] = "gated", "tests-mutated-candidate"
                return None
            import shutil
            shutil.rmtree(products)
            run_git(worktree, "add", "-A")
        candidate = semantic_candidate_ref(worktree, state["digest"])
        summary["candidate_tree_oid"] = candidate.candidate_tree_oid
        summary["candidate_ref"] = semantic_candidate(candidate.as_dict()).as_dict()
        run.event("candidate-retry", candidate_ref=summary["candidate_ref"])
        if not semantic_gates(run, summary, state, repo, worktree, policy, leaf):
            return None
    return None


def execute(args) -> dict:
    state = preflight(args)  # no worktree or ledger before all input checks
    directory = state["directory"]
    directory.mkdir(parents=True, exist_ok=False)
    run = Run(directory)
    repo, base, branch = state["repo"], state["base"], state["branch"]
    policy = state["policy"]
    prompt, prompt_hash = render_prompt(ROOT / "prompts" / "builder.md", kind=state["kind"],
                                         source_digest=state["digest"], task_text=state["text"])
    summary = {"run_id": state["run_id"], "candidate": args.candidate, "status": "failed",
               "failure": None, "base_commit": base, "base_tree_oid": state["tree"],
               "target_branch": branch, "source_digest": state["digest"],
               "policy_sha256": state["policy_hash"], "prompt_sha256": prompt_hash,
               "worktree": None, "candidate_tree_oid": None, "candidate_commit": None,
               "receipts": {}, "leaves": {}}
    run.event("started", base=base, branch=branch, source_digest=state["digest"])
    try:
        worktree = repo if args.candidate == "c4" else create_worktree(repo, state["run_id"], base)
        summary["worktree"] = str(worktree)
        if args.candidate in ("c1b", "c2b", "c3b"):
            from c1b import cycle
            if not cycle(run, summary, state, worktree, policy, args.leaf, prompt, ROOT,
                         typed_arbiter=args.candidate in ("c2b", "c3b")):
                if args.candidate in ("c2b", "c3b") and summary.get("status") == "stopped":
                    from cascade import Cascade
                    judge = Cascade(run, summary, repo, worktree, policy, ROOT, args.leaf)
                    judge.batch(retry_state(summary["failure"], summary["failure"]), ["retry.recoverable"])
                return run.finish(summary)
        else:
            session = directory / "sessions" / "builder"
            argv, stdout, stderr, code, duration, failure = invoke(args.leaf, policy, session, prompt, worktree)
            # Prompt content is never repeated in receipts; the prompt template and source are hashed.
            visible_argv = argv[:-1] + [f"<prompt:sha256:{sha(prompt.encode('utf-8'))}>"]
            summary["receipts"]["leaf"] = run.receipt("leaf", visible_argv, worktree,
                (stdout, stderr, code, duration, failure), max_bytes=policy["max_output_bytes"])
            summary["leaves"]["builder"] = usage(session)
            if failure or code != 0:
                summary["failure"] = "leaf-timeout" if failure == "timeout" else "leaf"
                return run.finish(summary)
        candidate = semantic_candidate_ref(worktree, state["digest"])
        summary["candidate_tree_oid"] = candidate.candidate_tree_oid
        summary["candidate_ref"] = semantic_candidate(candidate.as_dict()).as_dict()
        run.event("candidate", candidate_ref=summary["candidate_ref"])
        # A no-op is not an integrated candidate.
        if candidate.candidate_tree_oid == state["tree"]:
            summary["failure"] = "empty-candidate"
            return run.finish(summary)
        if args.candidate in ("c1a", "c2a", "c3a"):
            test_argv = [sys.executable if arg == "python" else arg for arg in policy["test_command"]]
            started = time.monotonic()
            try:
                out, err, exit_code = capture_command(test_argv, cwd=worktree,
                    timeout_seconds=policy["test_timeout_seconds"], max_output_bytes=policy["max_output_bytes"])
                test_result = (out, err, exit_code, time.monotonic() - started, None)
            except CaptureFailure as error:
                test_result = (b"", error.stderr, None, time.monotonic() - started, error.reason)
            summary["receipts"]["tests"] = run.receipt("tests", test_argv, worktree, test_result,
                max_bytes=policy["max_output_bytes"])
            if test_result[2] != 0:
                summary["failure"] = "tests"
                if args.candidate in ("c2a", "c3a"):
                    from cascade import Cascade
                    judge = Cascade(run, summary, repo, worktree, policy, ROOT, args.leaf)
                    judge.batch(retry_state((test_result[1] + test_result[0]).decode('utf-8', 'replace'), 'red tests'),
                                ["retry.recoverable"])
                return run.finish(summary)
            run_git(worktree, "add", "-A")
            if run_git(worktree, "write-tree") != candidate.candidate_tree_oid:
                # Tests may write files; only the byte-identical observed candidate is integrated.
                summary["failure"] = "tests-mutated-candidate"
                return run.finish(summary)
        if args.candidate in ("c2a", "c2b", "c3a", "c3b"):
            if not semantic_gates(run, summary, state, repo, worktree, policy, args.leaf):
                return run.finish(summary)
        if args.candidate in ("c3a", "c3b", "c4"):
            candidate = risk_phase(run, summary, state, repo, worktree, policy, args.leaf, candidate, prompt)
            if candidate is None:
                return run.finish(summary)
            if args.candidate == "c4":
                summary["status"] = "completed-local"
                run.event("completed-local", tree=candidate.candidate_tree_oid)
                return run.finish(summary)
        commit = integrate_candidate(repo, worktree, base, candidate.candidate_tree_oid, policy, state["run_id"])
        summary["candidate_commit"] = commit
        summary["status"] = "integrated"
        run.event("integrated", commit=commit, tree=candidate.candidate_tree_oid)
    except (GitError, ValueError, OSError) as error:
        if summary["worktree"]:
            try:
                head = run_git(Path(summary["worktree"]), "rev-parse", "HEAD")
                if head != base:
                    summary["candidate_commit"] = head
            except GitError:
                pass
        summary["failure"] = "integration" if summary["candidate_commit"] else "driver"
        run.event("failure", reason=summary["failure"], detail=str(error))
    return run.finish(summary)
