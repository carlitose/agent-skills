"""One modified Harbor trial. The caller selects exactly one pre-reserved cell.

No benchmark scheduler, retry loop or original ticket-driver invocation. Adapted
c1a/c3a phases operate inside Harbor's task sandbox; Jev remains host-only.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

from harbor.models.agent.context import ModelUsage
from harbor_pi_agent import GIT_SETUP, GIT_CLEANUP, MODEL, PiHarborAgent
from comparison_accounting import ComparisonLedger, AccountingError, read_model_journal
from comparison_jev import ComparisonJev, JevFailure, arbiter, read_jev_journal
from comparison_transport import ComparisonProcess, model_identity
from jev_host import jev_key_scope

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
ARMS = ("pi-bare", "skills-only", "ticket-driver-c1a", "ticket-driver-c3a")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound(path, name):
    file = Path(path)
    if not file.is_file() or file.is_symlink() or file.resolve().is_relative_to(ROOT):
        raise ValueError(f"{name} must be a real external file")
    return file


def parse_json_result(result, label):
    if result.return_code != 0:
        raise RuntimeError(f"{label} command failed ({result.return_code})")
    try:
        return json.loads(result.stdout)
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"invalid {label} receipt") from error


class ComparisonPiHarborAgent(PiHarborAgent):
    def __init__(self, logs_dir: Path, model_name: str | None = None, *,
                 task_name: str, binding_path: str, ledger_path: str,
                 authority_path: str, prior_ledger_path: str, jev_key_path: str | None = None, **kwargs):
        super().__init__(logs_dir, model_name=model_name, **kwargs)
        if self.options.arm not in ARMS:
            raise ValueError("unrecognized comparison arm")
        self.task_name = task_name
        self.binding_path = bound(binding_path, "comparison binding")
        self.authority_path = bound(authority_path, "human authorization")
        self.prior_path = bound(prior_ledger_path, "original pilot ledger")
        self.ledger_path = Path(ledger_path)
        if self.ledger_path.resolve().is_relative_to(ROOT) or self.logs_dir.resolve().is_relative_to(ROOT):
            raise ValueError("comparison receipts must remain outside Git")
        self.jev_key = bound(jev_key_path, "Jev key") if jev_key_path is not None else None
        if self.options.arm == "ticket-driver-c3a" and self.jev_key is None:
            raise ValueError("c3a needs a separate host Jev credential")
        self.binding = json.loads(self.binding_path.read_text(encoding="utf8"))
        self.rows = [row for row in self.binding.get("tasks", []) if row.get("task") == task_name]
        if (self.binding.get("method") != "git-overlay-v1" or self.binding.get("model") != MODEL
                or self.binding.get("thinking") != "high" or len(self.rows) != 1
                or self.binding.get("max_starts") != 12 or self.binding.get("cap_usd") != "720"):
            raise ValueError("comparison task binding is not frozen")
        self.task_binding = self.rows[0]
        self.ledger = ComparisonLedger(self.ledger_path, binding_sha256=sha(self.binding_path),
            authority_sha256=sha(self.authority_path), prior_ledger_sha256=sha(self.prior_path),
            prior_commitment_usd="120.17657720000000002")
        self.base = None

    @staticmethod
    def name():
        return "pi-harbor-comparison"

    def version(self):
        return "0.1.0-git-overlay"

    async def setup(self, environment):
        image = getattr(getattr(environment, "task_env_config", None), "docker_image", None)
        if image != self.task_binding["derived_agent_image_id"]:
            raise RuntimeError("task uses an unbound Git overlay image")
        await super().setup(environment)
        result = await environment.exec("git -C /app rev-parse HEAD", timeout_sec=30)
        self.base = (result.stdout or "").strip()
        if result.return_code != 0 or not re.fullmatch(r"[a-f0-9]{40}", self.base):
            raise RuntimeError("task Git baseline unavailable")
        if self.options.arm != "pi-bare":
            self._skills()  # reject drift before the cell starts or calls a provider
        if sha(ROOT / "ticket-driver/policy.json") != self.binding["arbiter_policy_sha256"]:
            raise RuntimeError("frozen semantic policy changed")
        for name, expected in self.binding["questions_sha256"].items():
            if (name not in ("review.findings_block.json", "review.scope_complete.json",
                             "qa.evidence_class.json", "verify.claim_supported.json",
                             "risk.semantic_change.json") or
                    sha(ROOT / "ticket-driver/questions" / name) != expected):
                raise RuntimeError("frozen Jev question changed")
        if len(self.binding["questions_sha256"]) != 5:
            raise RuntimeError("incomplete semantic question snapshot")
        if self.jev_key is not None:
            from jev_host import read_jev_key
            read_jev_key(self.jev_key)  # shape only; never print or pass to Pi
        for name in ("public_checks.py", "comparison_sandbox.py"):
            path = HERE / name
            if sha(path) != self.binding["helpers_sha256"][name]:
                raise RuntimeError("frozen public check/helper changed")
            await environment.upload_file(path, "/tmp/tbf-" + name)
            await self._verify_helper(environment, name)

    async def _verify_helper(self, environment, name):
        from comparison_exec import sandbox_exec
        result = await sandbox_exec(environment, "sha256sum /tmp/tbf-" + name,
                                    cwd="/app", timeout_sec=30)
        if (result.return_code != 0 or not (result.stdout or "").startswith(self.binding["helpers_sha256"][name] + " ")
                or sha(HERE / name) != self.binding["helpers_sha256"][name]):
            raise RuntimeError("sandbox helper integrity changed")

    async def _observe(self, environment, action, *args):
        from comparison_exec import sandbox_exec
        await self._verify_helper(environment, "comparison_sandbox.py")
        command = "python3 -B /tmp/tbf-comparison_sandbox.py " + action + " " + self.base
        if args:
            import shlex
            command += " " + shlex.quote(json.dumps(args[0]))
        result = await sandbox_exec(environment, command, cwd="/app", timeout_sec=60)
        await self._verify_helper(environment, "comparison_sandbox.py")
        return parse_json_result(result, action)

    async def _smoke(self, environment):
        from comparison_exec import sandbox_exec
        await self._verify_helper(environment, "public_checks.py")
        command = "python3 -B /tmp/tbf-public_checks.py " + self.task_name
        result = await sandbox_exec(environment, command, cwd="/app", timeout_sec=120)
        await self._verify_helper(environment, "public_checks.py")
        try:
            receipt = json.loads((result.stdout or "").strip())
        except ValueError as error:
            raise RuntimeError("public smoke missing structured receipt") from error
        if (receipt.get("task") != self.task_name or receipt.get("schema") != 1
                or receipt.get("kind") != "public-functional-smoke-not-official-verifier"
                or type(receipt.get("tests")) is not int or receipt["tests"] <= 0
                or type(receipt.get("passed")) is not bool or
                receipt["passed"] != (result.return_code == 0)):
            raise RuntimeError("invalid public smoke receipt")
        return receipt

    async def run(self, instruction, environment, context):
        if (hashlib.sha256(instruction.encode()).hexdigest() != self.task_binding["harbor_instruction_sha256"]
                or self.base is None or self.options.arm not in ARMS):
            raise RuntimeError("trial instruction, setup or arm differs from bound cell")
        arm = self.options.arm
        trial = f"{self.task_name}-{arm}-1"
        self.ledger.start(self.task_name, arm)  # The caller reserved this exact cell.
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        identity = {"method": "git-overlay-v1", "task": self.task_name, "arm": arm, "trial": trial}
        init = {"type": "init", "method": "git-overlay-v1", "model": MODEL,
                "thinking": "high", "arm": arm, "task_name": self.task_name,
                "trial_id": trial, "instruction": instruction,
                "budget": {"limit_usd": "57", "max_requests": 48}}
        metadata = {"arm": arm, "method": "git-overlay-v1", "task_name": self.task_name,
                    "local_gate": "not-started", "smoke": None}
        endpoint_final = None
        jev = None
        failed = None
        try:
            before = await self._observe(environment, "fingerprint")
            async with ComparisonProcess(self.logs_dir, environment, init) as process:
                skills = self._skills() if arm != "pi-bare" else ""
                prompt = (instruction + "\n\nPublic smoke command (not official verifier): "
                          f"python3 -B /tmp/tbf-public_checks.py {self.task_name}\n"
                          "Use sandbox_exec only; all work stays in /app. No hidden verifier is available.")
                system = "Work only inside the Harbor container. Use sandbox_exec for shell and file operations."
                if skills:
                    system += "\n\nFrozen local workflow skills:\n" + skills
                builder = await process.phase("builder", prompt, system, tools="sandbox")
                if builder["status"] != "completed":
                    raise RuntimeError("builder phase unavailable")
                after = await self._observe(environment, "fingerprint")
                if arm in ("ticket-driver-c1a", "ticket-driver-c3a"):
                    gate = await self._validate_candidate(environment, before, after)
                    metadata.update(gate)
                    if not gate["local_gate"] == "passed":
                        metadata["candidate_discarded"] = True
                        await self._observe(environment, "rollback", before["directories"])
                else:
                    metadata["local_gate"] = "not-applicable"
                if arm == "ticket-driver-c3a" and metadata["local_gate"] == "passed":
                    jev = ComparisonJev(self.logs_dir / "jev.jsonl", identity,
                        admit=lambda: self._jev_admission())
                    with jev_key_scope(self.jev_key, arbiter.isolated_key):
                        await self._semantic_gate(process, environment, instruction, jev, metadata, before)
                    if metadata["local_gate"] == "passed":
                        after_review = await self._observe(environment, "fingerprint")
                        if (after_review["tree"] != after["tree"] or
                                after_review["source_sha256"] != after["source_sha256"]):
                            metadata.update(local_gate="failed", reason="semantic phase mutated candidate")
                            await self._observe(environment, "rollback", before["directories"])
                            metadata["candidate_discarded"] = True
                expected_status = "failed" if metadata["local_gate"] == "failed" else "completed"
                endpoint_final = await process.finish(expected_status)
                if endpoint_final["status"] != expected_status:
                    raise RuntimeError("comparison phase status differs from terminal receipt")
            model = read_model_journal(self.logs_dir / "model-usage.jsonl", model_identity(init))
            if (not model["known"] or not model["terminal"]
                    or endpoint_final.get("usage", {}).get("cost_usd") != model["cost_usd"]
                    or endpoint_final["usage"].get("input_tokens") != model["input_tokens"]
                    or endpoint_final["usage"].get("output_tokens") != model["output_tokens"]):
                raise RuntimeError("model use not attributable after comparison")
            jev_receipt = read_jev_journal(self.logs_dir / "jev.jsonl", identity) if jev is not None else None
            if jev_receipt is not None and not jev_receipt["known"]:
                raise RuntimeError("Jev use not attributable")
            total = Decimal(str(model["cost_usd"])) + Decimal(jev_receipt["cost_usd"] if jev_receipt else "0")
            if total > 60:
                raise RuntimeError("trial exceeded reservation")
            context.n_input_tokens = model["input_tokens"]
            context.n_output_tokens = model["output_tokens"]
            context.cost_usd = float(total)
            context.model_usage = {MODEL: ModelUsage(n_input_tokens=model["input_tokens"],
                n_output_tokens=model["output_tokens"], cost_usd=float(model["cost_usd"]))}
            metadata["model_journal_sha256"] = model["sha256"]
            metadata["jev_cost_usd"] = jev_receipt["cost_usd"] if jev_receipt else "0"
            context.metadata = metadata
            self._write_receipt(metadata, model, jev_receipt, total)
        except BaseException as error:
            failed = error
        finally:
            # Git must be absent before Harbor exports artifacts for its verifier.
            try:
                if self._git_initialized:
                    result = await environment.exec(GIT_CLEANUP, timeout_sec=30)
                    if result.return_code != 0:
                        raise RuntimeError("Git cleanup unconfirmed")
                    self._git_initialized = False
            except BaseException as error:
                failed = error
            try:
                if failed is None:
                    evidence = sha(self.logs_dir / "pi-harbor-trajectory.json")
                    self.ledger.settle(self.task_name, arm, str(total), evidence)
                else:
                    # Missing journal or outstanding request is unknown, not $0.
                    self._settle_failure(init, identity)
            except BaseException as error:
                failed = error
        if failed is not None:
            raise failed

    def _jev_admission(self):
        if self.ledger.state()["blocked"]:
            raise JevFailure("comparison ledger blocked before host judgment")

    def _skills(self):
        snapshot = self.binding["skills"]
        chunks = []
        if len(snapshot) != 1 or snapshot[0].get("path") != "comparison-skills.md":
            raise RuntimeError("unbound skill inventory")
        for row in snapshot:
            path = HERE / row["path"]
            if path.is_symlink() or sha(path) != row["sha256"]:
                raise RuntimeError("frozen skill snapshot changed")
            chunks.append(path.read_text(encoding="utf8"))
        return "\n\n".join(chunks)

    async def _validate_candidate(self, environment, before, after):
        if before["source_sha256"] == after["source_sha256"]:
            return {"local_gate": "failed", "reason": "no task source changed"}
        smoke = await self._smoke(environment)
        observed = await self._observe(environment, "fingerprint")
        if observed["source_sha256"] != after["source_sha256"] or observed["tree"] != after["tree"]:
            return {"local_gate": "failed", "reason": "smoke mutated candidate", "smoke": smoke}
        return {"local_gate": "passed" if smoke["passed"] else "failed",
                "reason": "public smoke passed" if smoke["passed"] else "public smoke failed",
                "smoke": smoke, "candidate_tree": after["tree"],
                "candidate_source_sha256": after["source_sha256"]}

    async def _semantic_gate(self, process, environment, instruction, jev, metadata, before):
        changes = await self._observe(environment, "changes")
        question_root = ROOT / "ticket-driver/questions"
        questions = {}
        for name in ("review.findings_block", "review.scope_complete", "qa.evidence_class",
                     "verify.claim_supported", "risk.semantic_change"):
            question = json.loads((question_root / f"{name}.json").read_text(encoding="utf8"))
            questions[name] = {k: v for k, v in question.items() if k != "id"}
        policy = json.loads((ROOT / "ticket-driver/policy.json").read_text(encoding="utf8"))["arbiter"]
        risk = []
        for item in changes["functions"]:
            risk.append({"path": item["path"], "function": item["function"], "hunk": item["hunk"]})
        if risk:
            selected = {}
            for n in range(len(risk)):
                selected[f"risk_{n}"] = {**questions["risk.semantic_change"],
                    "instructions": questions["risk.semantic_change"]["instructions"] + f" Evaluate only functions[{n}]."}
            answers = jev.ask({"functions": risk}, selected)
            directed = [risk[n] for n in range(len(risk)) if self._risk_high(answers[f"risk_{n}"], policy)]
        else:
            directed = []
        if changes["unsupported"]:
            # Whole-file diff is always supplied; unsupported changes must be reviewed.
            directed.extend(risk)
        prompt = ("Fresh reviewer; no builder history. Read the public task and full candidate diff. "
                  "Do not edit files; report concrete [blocker], [should-fix], [nit] findings with paths, "
                  "or an exact line `No findings.` if none.\nTASK:\n" + instruction + "\nDIFF:\n" + changes["diff"])
        review = await process.phase("reviewer", prompt, "Review read-only with no tools; use only the supplied evidence.", tools="none")
        if review["status"] != "completed":
            raise RuntimeError("fresh review unavailable")
        state = {"acceptance_text": instruction, "candidate_diff": changes["diff"],
                 "review_prose": review["response"]}
        answers = jev.ask(state, {k: questions[k] for k in ("review.findings_block", "review.scope_complete")})
        decisions = {k: arbiter.classify(value, policy)["outcome"] for k, value in answers.items()}
        if (decisions["review.findings_block"] != "no" or decisions["review.scope_complete"] != "yes"
                or "[blocker]" in review["response"].lower()):
            metadata.update(local_gate="failed", reason="semantic review did not approve")
        if directed:
            hunks = "\n".join(f'{r["path"]}:{r["function"]}\n{r["hunk"]}' for r in directed)
            specific = await process.phase("directed-reviewer", "Review high-risk functions without editing; "
                "list each [blocker] path - explanation or say No findings.\n" + hunks,
                "Fresh directed reviewer; no tools.", tools="none")
            if specific["status"] != "completed" or "[blocker]" in specific["response"].lower():
                metadata.update(local_gate="failed", reason="directed review unresolved")
        receipt = metadata["smoke"]
        qa = {"test_argv": ["python3", "-B", "/tmp/tbf-public_checks.py", self.task_name],
              "exit_code": 0 if receipt["passed"] else 1, "observed_output": json.dumps(receipt),
              "changed_files": [r["path"] for r in changes["unsupported"]]}
        claim = {"claim": "Only this public smoke passed, not hidden verifier", "observed_test_exit_code": qa["exit_code"],
                 "receipt_excerpt": qa["observed_output"]}
        classification = jev.ask(qa, {"qa.evidence_class": questions["qa.evidence_class"]})
        supported = jev.ask(claim, {"verify.claim_supported": questions["verify.claim_supported"]})
        if (arbiter.classify(classification["qa.evidence_class"], policy)["outcome"] in ("uncertain", "unknown")
                or arbiter.classify(supported["verify.claim_supported"], policy)["outcome"] != "yes"):
            metadata.update(local_gate="failed", reason="QA or claim judgment unresolved")
        metadata["semantic_decisions"] = decisions
        metadata["risk_functions"] = len(directed)
        if metadata["local_gate"] != "passed":
            await self._observe(environment, "rollback", before["directories"])
            metadata["candidate_discarded"] = True

    @staticmethod
    def _risk_high(answer, policy):
        outcome = arbiter.classify(answer, policy)["outcome"]
        return outcome == "uncertain" or outcome >= policy["risk_score_high"]

    def _write_receipt(self, metadata, model, jev, total):
        receipt = {"method": "git-overlay-v1", "task": self.task_name, "arm": self.options.arm,
                   "estimated_cost_usd": str(total), "model": model, "jev": jev,
                   "metadata": metadata, "verifier_result": "owned by Harbor, not this agent"}
        path = self.logs_dir / "pi-harbor-trajectory.json"
        with path.open("x", encoding="utf8") as file:
            json.dump(receipt, file, sort_keys=True)
            file.write("\n")
            file.flush()
            import os
            os.fsync(file.fileno())

    def _settle_failure(self, init, identity):
        try:
            host_status = json.loads((self.logs_dir / "host-status.json").read_text(encoding="utf8"))
            if (host_status.get("process_stopped") is not True
                    or host_status.get("trial_id") != identity["trial"]):
                raise AccountingError("endpoint not confirmed stopped")
            model = read_model_journal(self.logs_dir / "model-usage.jsonl", model_identity(init))
            jev = read_jev_journal(self.logs_dir / "jev.jsonl", identity) if (self.logs_dir / "jev.jsonl").exists() else None
            cost = (Decimal(str(model["cost_usd"])) + Decimal(jev["cost_usd"] if jev else "0")
                    if model["known"] and (jev is None or jev["known"]) else None)
        except (AccountingError, OSError, ValueError):
            cost = None
        evidence = hashlib.sha256((self.logs_dir / "model-usage.jsonl").read_bytes()).hexdigest() if (self.logs_dir / "model-usage.jsonl").exists() else "0" * 64
        self.ledger.settle(self.task_name, self.options.arm, str(cost) if cost is not None else None, evidence)
