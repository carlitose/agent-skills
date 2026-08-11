from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.docs_only import (
    APPROVED_SCOPE,
    DocsOnlyError,
    docs_only_verification_bundle,
    revalidate_docs_only_receipt,
    validate_docs_only_candidate,
)
from autopilot.docs_only_contract import CHECKPOINT_PHASES
from autopilot.git_ops import candidate_ref


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


class DocsOnlyValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "tests@example.invalid")
        git(self.repo, "config", "user.name", "Docs Tests")
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "index.md").write_text("# Index\n", encoding="utf-8")
        git(self.repo, "add", "docs/index.md")
        git(self.repo, "commit", "-m", "baseline")
        self.base_tree = git(self.repo, "rev-parse", "HEAD^{tree}")
        self.ticket = {
            "ticket_id": "D-01",
            "ticket_digest": "d" * 64,
            "execution_mode": "AFK",
            "blocked_by": [],
            "source_relative_path": "D-01.md",
            "candidate_ref": {
                "contract_version": 2,
                "base_tree_oid": self.base_tree,
                "candidate_tree_oid": self.base_tree,
                "ticket_digest": "d" * 64,
            },
        }
        self.evidence = Path(self.directory.name) / "evidence"

    def request(
        self,
        paths: list[str],
        *,
        candidate_tree: str | None = None,
    ) -> dict[str, object]:
        if candidate_tree is None:
            candidate = candidate_ref(
                self.repo,
                self.ticket["ticket_digest"],
                base_ref=self.base_tree,
            )
            candidate_document = {
                "contract_version": candidate.contract_version,
                "base_tree_oid": candidate.base_tree_oid,
                "candidate_tree_oid": candidate.candidate_tree_oid,
                "ticket_digest": candidate.ticket_digest,
            }
        else:
            candidate_document = {
                "contract_version": 2,
                "base_tree_oid": self.base_tree,
                "candidate_tree_oid": candidate_tree,
                "ticket_digest": self.ticket["ticket_digest"],
            }
        return {
            "contract_version": 1,
            "ticket_envelope": {
                "ticket_schema": 1,
                "ticket_id": self.ticket["ticket_id"],
                "execution_mode": self.ticket["execution_mode"],
                "blocked_by": list(self.ticket["blocked_by"]),
            },
            "ticket_digest": self.ticket["ticket_digest"],
            "source_relative_path": self.ticket["source_relative_path"],
            "candidate_ref": candidate_document,
            "expected_changed_paths": paths,
            "approved_documentation_scope": APPROVED_SCOPE,
        }

    def test_request_requires_the_canonical_ticket_envelope(self) -> None:
        self.stage_doc()
        request = self.request(["docs/guide.md"])
        del request["ticket_envelope"]["ticket_schema"]
        with self.assertRaisesRegex(DocsOnlyError, "missing required field"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                request,
                evidence_dir=self.evidence,
            )

    def test_request_base_tree_must_match_the_runner_owned_candidate(self) -> None:
        (self.repo / "script.py").write_text("print('hidden')\n", encoding="utf-8")
        git(self.repo, "add", "script.py")
        alternate_base = git(self.repo, "write-tree")
        self.stage_doc()
        request = self.request(["docs/guide.md"])
        request["candidate_ref"]["base_tree_oid"] = alternate_base

        with self.assertRaisesRegex(DocsOnlyError, "base_tree_oid differs"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                request,
                evidence_dir=self.evidence,
            )

    def stage_doc(self, path: str = "docs/guide.md", text: str = "# Guide\n") -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        git(self.repo, "add", "--", path)

    @staticmethod
    def persisted_receipt(validation: object) -> dict[str, object]:
        receipt = validation.receipt()
        receipt["checkpoint"] = {
            "input_hash": "c" * 64,
            "artifact_hashes": {phase: "d" * 64 for phase in CHECKPOINT_PHASES},
            "phases_complete": list(CHECKPOINT_PHASES),
        }
        return receipt

    def test_valid_candidate_emits_content_addressed_evidence_and_static_ceiling(self) -> None:
        self.stage_doc(text="# Guide\n\n[Index](index.md)\n")
        validation = validate_docs_only_candidate(
            self.repo,
            self.ticket,
            self.request(["docs/guide.md"]),
            evidence_dir=self.evidence,
        )

        artifact = Path(validation.evidence_path)
        self.assertTrue(artifact.is_file())
        self.assertEqual(
            validation.evidence_sha256,
            hashlib.sha256(artifact.read_bytes()).hexdigest(),
        )
        self.assertEqual(4, validation.receipt()["leaf_interactions_avoided"])
        bundle = docs_only_verification_bundle(self.ticket, validation)
        self.assertEqual("implementation-complete", bundle["verification"]["max_claim"])
        self.assertIn("behavior-verified", bundle["verification"]["forbidden_claims"])

    def test_mixed_doc_and_non_doc_candidate_is_rejected(self) -> None:
        self.stage_doc()
        (self.repo / "script.py").write_text("print('no')\n", encoding="utf-8")
        git(self.repo, "add", "script.py")
        with self.assertRaisesRegex(DocsOnlyError, "outside approved"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                self.request(["docs/guide.md", "script.py"]),
                evidence_dir=self.evidence,
            )

    def test_agent_instructions_and_ticket_sources_are_rejected(self) -> None:
        for path, message in (
            ("docs/AGENTS.md", "agent-executable"),
            ("docs/SKILL.md", "agent-executable"),
            ("docs/manifest.md", "agent-executable"),
            ("docs/config/settings.md", "agent-executable"),
            ("docs/generated/report.md", "agent-executable"),
            ("docs/scripts/example.md", "agent-executable"),
            ("docs/tickets/01.md", "runner-owned"),
            ("docs/Tickets/02.md", "runner-owned"),
        ):
            with self.subTest(path=path):
                git(self.repo, "reset", "--hard", "HEAD")
                target = self.repo / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("# No\n", encoding="utf-8")
                git(self.repo, "add", "--", path)
                with self.assertRaisesRegex(DocsOnlyError, message):
                    validate_docs_only_candidate(
                        self.repo,
                        self.ticket,
                        self.request([path]),
                        evidence_dir=self.evidence,
                    )

    def test_symlink_is_rejected(self) -> None:
        (self.repo / "docs" / "link.md").symlink_to("index.md")
        git(self.repo, "add", "docs/link.md")
        with self.assertRaisesRegex(DocsOnlyError, "regular non-executable blob"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                self.request(["docs/link.md"]),
                evidence_dir=self.evidence,
            )

    def test_submodule_entry_is_rejected(self) -> None:
        commit = git(self.repo, "rev-parse", "HEAD")
        git(
            self.repo,
            "clone",
            "--quiet",
            str(self.repo),
            "docs/submodule.md",
        )
        git(
            self.repo,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{commit},docs/submodule.md",
        )
        tree = git(self.repo, "write-tree")
        with self.assertRaisesRegex(DocsOnlyError, "regular non-executable blob"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                self.request(["docs/submodule.md"], candidate_tree=tree),
                evidence_dir=self.evidence,
            )

    def test_unstaged_or_untracked_changes_fail_closed(self) -> None:
        self.stage_doc()
        request = self.request(["docs/guide.md"])
        (self.repo / "docs" / "index.md").write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(DocsOnlyError, "unstaged"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                request,
                evidence_dir=self.evidence,
            )

    def test_candidate_and_path_drift_are_rejected(self) -> None:
        self.stage_doc()
        request = self.request(["docs/guide.md"])
        request["candidate_ref"]["candidate_tree_oid"] = "0" * 40
        with self.assertRaisesRegex(DocsOnlyError, "staged tree differs"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                request,
                evidence_dir=self.evidence,
            )

    def test_missing_link_and_corrupt_receipt_evidence_fail_closed(self) -> None:
        self.stage_doc(text="# Guide\n\n[Missing](missing.md)\n")
        with self.assertRaisesRegex(DocsOnlyError, "link target is missing"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                self.request(["docs/guide.md"]),
                evidence_dir=self.evidence,
            )
        git(self.repo, "reset", "--hard", "HEAD")
        self.stage_doc()
        request = self.request(["docs/guide.md"])
        validation = validate_docs_only_candidate(
            self.repo, self.ticket, request, evidence_dir=self.evidence
        )
        receipt = self.persisted_receipt(validation)
        Path(validation.evidence_path).write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(DocsOnlyError, "missing or corrupt"):
            revalidate_docs_only_receipt(
                self.repo,
                self.ticket,
                receipt,
                evidence_dir=self.evidence,
            )

    def test_applicable_artifact_graph_metadata_is_required(self) -> None:
        self.stage_doc(
            "docs/specs/guide.md",
            "# Guide\n\n## Artifact Graph\n\n- Role: spec\n",
        )
        with self.assertRaisesRegex(DocsOnlyError, "canonical artifact audit"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                self.request(["docs/specs/guide.md"]),
                evidence_dir=self.evidence,
            )

    def test_canonical_artifact_audit_ignores_unrelated_preexisting_errors(self) -> None:
        specs = self.repo / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "legacy-broken.md").write_text(
            """# Legacy broken

## Artifact Graph

- Artifact ID: `artifact:legacy-broken`
- Role: `invalid`
- Standalone: true
""",
            encoding="utf-8",
        )
        git(self.repo, "add", "docs/specs/legacy-broken.md")
        git(self.repo, "commit", "-m", "pre-existing unrelated audit error")
        self.base_tree = git(self.repo, "rev-parse", "HEAD^{tree}")
        self.ticket["candidate_ref"]["base_tree_oid"] = self.base_tree
        self.ticket["candidate_ref"]["candidate_tree_oid"] = self.base_tree
        self.stage_doc(
            "docs/specs/guide.md",
            """# Guide

## Artifact Graph

- Artifact ID: `artifact:guide`
- Role: `spec`
- Standalone: true
""",
        )

        validation = validate_docs_only_candidate(
            self.repo,
            self.ticket,
            self.request(["docs/specs/guide.md"]),
            evidence_dir=self.evidence,
        )

        artifact_check = next(
            check for check in validation.checks if check["id"] == "artifact-graph"
        )
        self.assertEqual(1, artifact_check["managed_paths"])

    def test_canonical_artifact_audit_rejects_multi_path_diagnostic(self) -> None:
        specs = self.repo / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "owner.md").write_text(
            """# Owner

## Artifact Graph

- Artifact ID: `artifact:duplicate`
- Role: `spec`
- Standalone: true

### Children
- [Duplicate](./duplicate.md)
""",
            encoding="utf-8",
        )
        git(self.repo, "add", "docs/specs/owner.md")
        git(self.repo, "commit", "-m", "add artifact owner")
        self.base_tree = git(self.repo, "rev-parse", "HEAD^{tree}")
        self.ticket["candidate_ref"]["base_tree_oid"] = self.base_tree
        self.ticket["candidate_ref"]["candidate_tree_oid"] = self.base_tree
        self.stage_doc(
            "docs/specs/duplicate.md",
            """# Duplicate

## Artifact Graph

- Artifact ID: `artifact:duplicate`
- Role: `spec`
- Parent: [Owner](./owner.md)
""",
        )

        with self.assertRaisesRegex(DocsOnlyError, "duplicate-artifact-id"):
            validate_docs_only_candidate(
                self.repo,
                self.ticket,
                self.request(["docs/specs/duplicate.md"]),
                evidence_dir=self.evidence,
            )

    def test_delivery_revalidation_rejects_candidate_drift(self) -> None:
        self.stage_doc()
        request = self.request(["docs/guide.md"])
        validation = validate_docs_only_candidate(
            self.repo, self.ticket, request, evidence_dir=self.evidence
        )
        receipt = self.persisted_receipt(validation)
        (self.repo / "docs" / "guide.md").write_text(
            "# Changed after adoption\n", encoding="utf-8"
        )
        git(self.repo, "add", "docs/guide.md")
        with self.assertRaisesRegex(DocsOnlyError, "staged tree differs"):
            revalidate_docs_only_receipt(
                self.repo,
                self.ticket,
                receipt,
                evidence_dir=self.evidence,
            )


if __name__ == "__main__":
    unittest.main()
