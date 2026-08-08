from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = (
    "ticket-autopilot",
    "execute-ticket",
    "code-review",
    "qa-test-plan",
    "verification-audit",
    "explain-pr",
    "code-simplification",
    "to-tickets",
    "wayfinder",
    "to-spec",
    "ask-skills",
)

ROLE_MARKERS = {
    "ticket-autopilot": "Owns: folder scheduling",
    "execute-ticket": "Owns: one-ticket quality loop",
    "code-review": "Owns: read-only review",
    "qa-test-plan": "Owns: QA plan",
    "verification-audit": "Owns: Verification Record",
    "explain-pr": "Owns: PR-body rendering",
    "code-simplification": "Owns: focused simplification",
    "to-tickets": "Owns: Ticket Envelope production",
    "wayfinder": "Owns: investigation map",
    "to-spec": "Owns: specification",
    "ask-skills": "Owns: routing",
}


def skill_text(name: str) -> str:
    return (REPO_ROOT / name / "SKILL.md").read_text(encoding="utf-8")


class SkillGraphTests(unittest.TestCase):
    def test_wayfinder_clear_destination_skips_ceremonial_grilling(self) -> None:
        wayfinder = skill_text("wayfinder")

        self.assertIn(
            "Clear destination: state assumptions and chart immediately.",
            wayfinder,
        )
        self.assertIn("Do not invoke `grilling` ceremonially.", wayfinder)

    def test_wayfinder_material_ambiguity_invokes_grilling_and_waits_before_artifacts(self) -> None:
        wayfinder = skill_text("wayfinder")

        self.assertIn("[grilling](../grilling/SKILL.md)", wayfinder)
        self.assertIn(
            "materially change the Destination, scope, or initial frontier",
            wayfinder,
        )
        self.assertIn("Ask one question at a time and wait", wayfinder)
        self.assertIn("Create zero durable artifacts before confirmation.", wayfinder)

    def test_wayfinder_maintenance_reuses_destination_until_scope_changes(self) -> None:
        wayfinder = skill_text("wayfinder")

        self.assertIn("Reuse the persisted Destination", wayfinder)
        self.assertIn(
            "Do not restart `grilling` unless the user explicitly changes it",
            wayfinder,
        )
        self.assertIn("return to the Destination gate before writing", wayfinder)

    def test_wayfinder_unresolved_decision_emits_hitl_grilling_ticket(self) -> None:
        wayfinder = skill_text("wayfinder")

        self.assertIn("Known Destination with an unresolved decision", wayfinder)
        self.assertIn("Do not run the interview inline", wayfinder)
        self.assertIn("`execution_mode: HITL`", wayfinder)
        self.assertIn("body must require [grilling](../grilling/SKILL.md)", wayfinder)
        self.assertIn("Keep that ticket on the frontier", wayfinder)
        self.assertIn("Do not add Ticket Envelope fields", wayfinder)

    def test_grilling_alias_graph_has_one_owner_and_no_cycle(self) -> None:
        paths = {
            name: REPO_ROOT / name / "SKILL.md"
            for name in ("grilling", "grill-me", "grill-with-docs")
        }
        texts = {name: skill_text(name) for name in paths}
        owner = "Owns: live decision interview and confirmation gate"

        self.assertEqual(
            [REPO_ROOT / "grilling" / "SKILL.md"],
            [
                path
                for path in REPO_ROOT.rglob("SKILL.md")
                if owner in path.read_text(encoding="utf-8")
            ],
        )
        self.assertIn("[grilling](../grilling/SKILL.md)", texts["grill-me"])
        self.assertNotIn("domain-modeling", texts["grill-me"])
        self.assertIn("[grilling](../grilling/SKILL.md)", texts["grill-with-docs"])
        self.assertIn(
            "[domain-modeling](../domain-modeling/SKILL.md)",
            texts["grill-with-docs"],
        )
        self.assertIn("Interview ownership remains with `grilling`", texts["grill-with-docs"])
        self.assertIn("Return control to the calling skill", texts["grilling"])
        for name, text in texts.items():
            with self.subTest(skill=name):
                self.assertNotIn("../wayfinder/SKILL.md", text)
                if name != "grill-me":
                    self.assertNotIn("../grill-me/SKILL.md", text)
                if name != "grill-with-docs":
                    self.assertNotIn("../grill-with-docs/SKILL.md", text)
    def test_autopilot_defaults_to_portable_inline_composition(self) -> None:
        scheduler = skill_text("ticket-autopilot")
        executor = skill_text("execute-ticket")

        vocabulary = (
            "invoke = execute one skill inline",
            "compose = run skills in serial sequence while preserving ownership",
            "delegate = use a distinct host worker",
            "independent = observed separate context",
            "parallel = concurrent delegations",
        )
        for definition in vocabulary:
            with self.subTest(definition=definition):
                self.assertIn(definition, scheduler)
        self.assertIn("Default ticket execution composes serially inline", scheduler)
        self.assertIn("requires zero AgentTool calls", scheduler)
        self.assertIn("Without delegation authority, invoke every stage inline", executor)

    def test_delegation_authority_and_isolation_claims_fail_closed(self) -> None:
        scheduler = skill_text("ticket-autopilot")
        review = skill_text("code-review")
        qa = skill_text("qa-test-plan")
        audit = skill_text("verification-audit")
        schema = (
            REPO_ROOT
            / "verification-audit"
            / "references"
            / "verification-contract-v2.json"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Delegate only with explicit user or applicable host authority",
            scheduler,
        )
        self.assertIn("schema-3 `execution`", review)
        self.assertRegex(
            review,
            r"shared-context or\s+unknown isolation is not independent",
        )
        self.assertIn("schema-3 `execution`", qa)
        self.assertIn("observed isolation", qa)
        self.assertIn("copy its isolation into existing stage limitations", audit)
        self.assertIn("`unsupported-independence` gate", audit)
        self.assertNotIn('"execution"', schema)

    def test_agenttool_optional_workflows_have_inline_fallback_or_gate(self) -> None:
        architecture = skill_text("improve-codebase-architecture")
        improver = skill_text("codebase-improver")
        quality_loop = (
            REPO_ROOT / "codebase-improver" / "references" / "quality-loop.md"
        ).read_text(encoding="utf-8")
        research = skill_text("research")
        triangulate = skill_text("triangulate-diagnosis")

        for name, text in (
            ("architecture", architecture),
            ("improver", improver),
            ("quality-loop", quality_loop),
        ):
            with self.subTest(skill=name):
                self.assertIn("Without delegation authority", text)
                self.assertIn("serially inline", text)
                self.assertRegex(text, r"(?i)(?:gate|do not claim).*(?:independent|parallel)")
        self.assertNotIn("Use the Agent tool with", architecture)
        self.assertNotIn("Spawn 3+ sub-agents in parallel", architecture)
        self.assertRegex(research, r"If\s+not, do the same workflow directly")
        self.assertIn("If the host cannot isolate context at all", triangulate)

    def test_codebase_improver_frontmatter_keeps_architecture_triggers(self) -> None:
        frontmatter = skill_text("codebase-improver").split("---", 2)[1]

        for trigger in (
            "make this more testable",
            "find refactoring opportunities",
            "deepen shallow modules",
            "consolidate tightly-coupled modules",
            "make codebase AI-navigable",
        ):
            with self.subTest(trigger=trigger):
                self.assertIn(trigger, frontmatter)
        self.assertIn("Worker delegation is optional", frontmatter)

    def test_independent_claims_require_observed_separate_context(self) -> None:
        scheduler = skill_text("ticket-autopilot")
        executor = skill_text("execute-ticket")
        scheduler_frontmatter = scheduler.split("---", 2)[1]
        executor_intro = executor.split("## Inputs", 1)[0]

        self.assertIn("evidence-backed quality gates", scheduler_frontmatter)
        self.assertNotIn("independent quality gates", scheduler_frontmatter)
        self.assertIn("review isolation gates", executor_intro)
        self.assertNotIn("independent review", executor_intro)
        self.assertRegex(
            executor,
            r"independent only when separate-context isolation was observed",
        )
    def test_ticket_contract_has_one_implementation_owner(self) -> None:
        definitions = {}
        for path in REPO_ROOT.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for symbol in (
                "normalize_ticket_envelope",
                "parse_ticket_markdown",
                "serialize_ticket_markdown",
            ):
                if re.search(rf"^def {symbol}\b", text, re.MULTILINE):
                    definitions.setdefault(symbol, []).append(path)

        owner = REPO_ROOT / "ticket-autopilot" / "scripts" / "autopilot" / "ticket_contract.py"
        self.assertEqual(
            {
                "normalize_ticket_envelope": [owner],
                "parse_ticket_markdown": [owner],
                "serialize_ticket_markdown": [owner],
            },
            definitions,
        )

    def test_verification_consumes_runner_identity_without_ticket_parser(self) -> None:
        path = REPO_ROOT / "verification-audit" / "scripts" / "verification_contract.py"
        text = path.read_text(encoding="utf-8")
        schema = (
            REPO_ROOT
            / "verification-audit"
            / "references"
            / "verification-contract-v2.json"
        ).read_text(encoding="utf-8")
        docs = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                REPO_ROOT / "verification-audit" / "SKILL.md",
                REPO_ROOT
                / "verification-audit"
                / "references"
                / "verification-record.md",
                REPO_ROOT
                / "ticket-autopilot"
                / "references"
                / "ticket-envelope-v1.md",
            )
        )

        self.assertNotIn("ticket-autopilot", text)
        self.assertNotIn("autopilot.ticket_contract", text)
        self.assertNotIn("parse_ticket_markdown", text)
        self.assertNotIn("validate-ticket", text)
        self.assertNotRegex(text, r"(?m)^def validate_ticket_envelope\b")
        self.assertNotRegex(text, r"(?m)^def parse_ticket_markdown\b")
        self.assertNotIn("def _front_matter_scalar", text)
        self.assertNotIn('"ticket_envelope"', schema)
        self.assertIn('"ticket_id"', schema)
        self.assertIn('"ticket_envelope_ref"', schema)
        self.assertNotIn("validate-ticket", docs)
        executor = (REPO_ROOT / "execute-ticket" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        scheduler = (REPO_ROOT / "ticket-autopilot" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Ticket Envelope artifact reference", executor)
        self.assertIn("source artifact reference", scheduler)

    def test_skill_roles_are_explicit_and_non_overlapping(self) -> None:
        for skill, marker in ROLE_MARKERS.items():
            with self.subTest(skill=skill):
                text = (REPO_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(marker, text)

        non_owners = (
            "ticket-autopilot",
            "execute-ticket",
            "code-review",
            "qa-test-plan",
            "explain-pr",
            "code-simplification",
            "to-tickets",
            "wayfinder",
            "to-spec",
            "ask-skills",
        )
        for skill in non_owners:
            with self.subTest(skill=skill):
                text = (REPO_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("## External Boundary Delta", text)
                self.assertNotIn("## Claim-to-Evidence Matrix", text)

    def test_leaf_workers_and_scheduler_do_not_cross_ownership_boundaries(self) -> None:
        scheduler = (REPO_ROOT / "ticket-autopilot" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        review = (REPO_ROOT / "code-review" / "SKILL.md").read_text(encoding="utf-8")
        qa = (REPO_ROOT / "qa-test-plan" / "SKILL.md").read_text(encoding="utf-8")
        executor = (REPO_ROOT / "execute-ticket" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        producer_docs = "\n".join(
            (REPO_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            for skill in ("to-tickets", "wayfinder")
        )

        self.assertNotRegex(
            scheduler,
            r"(?i)invoke\s+(?:`)?(?:code-review|qa-test-plan|verification-audit)",
        )
        self.assertNotRegex(review, r"(?i)invoke\s+`?verification-audit")
        self.assertNotRegex(qa, r"(?i)invoke\s+`?verification-audit")
        self.assertNotRegex(
            executor,
            r"(?i)\b(?:commit|push|open|edit|merge)\s+(?:the\s+)?PR\b",
        )
        self.assertNotIn("## Blocked By", producer_docs)

    def test_scheduler_uses_one_worktree_per_folder_run(self) -> None:
        scheduler = (REPO_ROOT / "ticket-autopilot" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(1, scheduler.count("one isolated worktree per folder run"))
        self.assertIn("serialized one-ticket mutation", scheduler)
        self.assertNotRegex(
            scheduler,
            r"(?i)(?:one|its|new|isolated)\s+(?:isolated\s+)?worktree\s+per\s+ticket",
        )
        self.assertNotIn("create its isolated worktree", scheduler)

    def test_review_and_qa_keep_authorized_standalone_routes(self) -> None:
        review = (REPO_ROOT / "code-review" / "SKILL.md").read_text(encoding="utf-8")
        qa = (REPO_ROOT / "qa-test-plan" / "SKILL.md").read_text(encoding="utf-8")
        router = (REPO_ROOT / "ask-skills" / "SKILL.md").read_text(encoding="utf-8")
        review_metadata = (
            REPO_ROOT / "code-review" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        qa_metadata = (
            REPO_ROOT / "qa-test-plan" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")

        for text in (review, qa):
            self.assertIn("Standalone acquisition", text)
            self.assertIn("PR, commit, local diff, or user-requested scope", text)
            self.assertIn("cannot claim ticket completion or release", text)
            self.assertNotRegex(text, r"(?i)invoke\s+`?verification-audit")
        self.assertIn("standalone PR, commit, local diff", router)
        self.assertIn("PR, commit, or local diff", review_metadata)
        self.assertIn("PR, commit, or local diff", qa_metadata)

    def test_router_parses_canonical_single_ticket_before_execute_ticket(self) -> None:
        router = (REPO_ROOT / "ask-skills" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        metadata = (
            REPO_ROOT / "ask-skills" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")

        self.assertRegex(router, r"absolute\s+skill root")
        self.assertIn(
            '"$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py" ticket-parse',
            router,
        )
        self.assertIn("normalized Ticket Envelope", router)
        self.assertIn("source artifact reference", router)
        self.assertIn("runner CandidateRef", router)
        self.assertIn("already-normalized", router)
        self.assertRegex(router, r"(?s)Legacy.*`migrate`")
        self.assertIn("canonical ticket Markdown", metadata)
        self.assertIn("ticket-parse", metadata)
        self.assertNotIn("nested orchestration", router)
        self.assertNotIn("run finalization", router)

    def test_verification_record_points_ticket_envelope_to_its_owner(self) -> None:
        reference = (
            REPO_ROOT
            / "verification-audit"
            / "references"
            / "verification-record.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "../../ticket-autopilot/references/ticket-envelope-v1.md",
            reference,
        )
        contract_paragraph = reference.split("Claim targets", 1)[0]
        self.assertNotRegex(
            contract_paragraph,
            r"verification-contract-v2\.json[\s\S]*canonical Ticket Envelope",
        )

    def test_cli_docs_are_complete_and_install_root_relative(self) -> None:
        scheduler = (REPO_ROOT / "ticket-autopilot" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for command in (
            "plan",
            "run",
            "resume",
            "status",
            "approve",
            "abort",
            "cleanup",
            "ticket-parse",
            "ticket-emit",
            "migrate",
        ):
            with self.subTest(command=command):
                self.assertIn(f"`{command}`", scheduler)
        self.assertIn("--help", scheduler)
        self.assertIn("absolute skill root", scheduler)

        docs = []
        for skill in (
            "ticket-autopilot",
            "verification-audit",
            "explain-pr",
            "to-tickets",
        ):
            docs.extend((REPO_ROOT / skill).rglob("*.md"))
        documented_commands = "\n".join(
            path.read_text(encoding="utf-8") for path in docs
        )
        self.assertNotRegex(
            documented_commands,
            r"python3 -B (?:ticket-autopilot|verification-audit)/",
        )
        self.assertNotIn("Run from the repository root", documented_commands)
        self.assertIn(
            'python3 -B "$TICKET_AUTOPILOT_ROOT/scripts/ticket-autopilot.py"',
            documented_commands,
        )
        self.assertIn(
            'python3 -B "$VERIFICATION_AUDIT_ROOT/scripts/verification_contract.py"',
            documented_commands,
        )

    def test_producers_and_consumers_reference_canonical_contracts(self) -> None:
        expected_links = {
            "to-tickets": "../ticket-autopilot/references/ticket-envelope-v1.md",
            "wayfinder": "../ticket-autopilot/references/ticket-envelope-v1.md",
            "execute-ticket": "../ticket-autopilot/references/ticket-envelope-v1.md",
            "ticket-autopilot": "references/ticket-envelope-v1.md",
            "code-review": "../verification-audit/references/verification-record.md",
            "qa-test-plan": "../verification-audit/references/verification-record.md",
            "explain-pr": "../verification-audit/references/verification-record.md",
        }
        for skill, link in expected_links.items():
            with self.subTest(skill=skill):
                text = (REPO_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(f"]({link})", text)

    def test_qa_evidence_classes_match_validator_and_ticket_mode_owner(self) -> None:
        qa = (REPO_ROOT / "qa-test-plan" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        verification_contract = json.loads(
            (
                REPO_ROOT
                / "verification-audit"
                / "references"
            / "verification-contract-v2.json"
            ).read_text(encoding="utf-8")
        )
        ticket_reference = (
            REPO_ROOT
            / "ticket-autopilot"
            / "references"
            / "ticket-envelope-v1.md"
        ).read_text(encoding="utf-8")

        canonical = ["static", "unit", "integration", "simulated", "live"]
        self.assertEqual(
            canonical,
            verification_contract["enums"]["evidence_class"],
        )
        self.assertIn(
            "static, unit, integration, simulated, or live",
            qa,
        )
        self.assertNotRegex(qa, r"(?i)\bsystem\b")
        self.assertNotIn("execution_mode", verification_contract["enums"])
        self.assertIn("execution_mode", ticket_reference)
        self.assertIn("AFK", ticket_reference)
        self.assertIn("HITL", ticket_reference)

    def test_skill_docs_are_concise(self) -> None:
        line_limits = {
            "ticket-autopilot": 130,
            "execute-ticket": 125,
            "code-review": 130,
            "qa-test-plan": 135,
            "verification-audit": 170,
            "explain-pr": 105,
            "code-simplification": 90,
            "to-tickets": 115,
            "wayfinder": 125,
            "to-spec": 150,
            "ask-skills": 70,
        }
        total = 0
        for skill, limit in line_limits.items():
            lines = (REPO_ROOT / skill / "SKILL.md").read_text(encoding="utf-8").splitlines()
            total += len(lines)
            with self.subTest(skill=skill):
                self.assertLessEqual(len(lines), limit)
        self.assertLessEqual(total, 1_300)

    def test_openai_metadata_matches_each_skill_role(self) -> None:
        for skill in SKILLS:
            with self.subTest(skill=skill):
                metadata = (REPO_ROOT / skill / "agents" / "openai.yaml").read_text(
                    encoding="utf-8"
                )
                self.assertIn("display_name:", metadata)
                self.assertIn("short_description:", metadata)
                self.assertIn("default_prompt:", metadata)
                self.assertIn(f"${skill}", metadata)
                self.assertNotIn("super-autopilot", metadata.lower())


if __name__ == "__main__":
    unittest.main()
