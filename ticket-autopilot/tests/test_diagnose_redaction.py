from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DIAGNOSE = REPO_ROOT / "diagnose" / "SKILL.md"
REFERENCE = REPO_ROOT / "diagnose" / "references" / "secret-redaction.md"
TRIANGULATE = REPO_ROOT / "triangulate-diagnosis" / "SKILL.md"


class DiagnoseRedactionContractTests(unittest.TestCase):
    def test_redaction_precedes_every_evidence_surface(self) -> None:
        skill = DIAGNOSE.read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")

        normalized_skill = re.sub(r"\s+", " ", skill)

        self.assertIn("[secret-redaction boundary](references/secret-redaction.md)", skill)
        self.assertIn(
            "before displaying, quoting, delegating, or durably capturing",
            normalized_skill,
        )
        for surface in ("command", "output", "artifact"):
            with self.subTest(surface=surface):
                self.assertRegex(reference, rf"(?im)^\| {surface} \|")
        self.assertIn("`<REDACTED>`", reference)
        self.assertIn("environment-variable reference", reference)

    def test_synthetic_fixtures_preserve_signal_without_secret_literals(self) -> None:
        reference = REFERENCE.read_text(encoding="utf-8")

        expected_safe_shapes = (
            'Authorization: Bearer <REDACTED>',
            '--token <REDACTED>',
            'status=401 request_id=req_fixture auth=<REDACTED>',
            '<REDACTED auth headers; non-signal lines omitted>',
        )
        for fixture in expected_safe_shapes:
            with self.subTest(fixture=fixture):
                self.assertIn(fixture, reference)
        self.assertNotRegex(reference, r"(?:sk|ghp|github_pat)_[A-Za-z0-9]{12,}")
        self.assertNotRegex(reference, r"(?i)bearer\s+(?!<REDACTED>)[A-Za-z0-9._-]{12,}")

    def test_redaction_loss_opens_a_gate_instead_of_requesting_raw_secrets(self) -> None:
        reference = REFERENCE.read_text(encoding="utf-8")
        triangulate = TRIANGULATE.read_text(encoding="utf-8")

        self.assertIn("Stop the diagnosis at that boundary", reference)
        self.assertIn("user-produced redacted artifact", reference)
        self.assertIn("Never request a raw secret", reference)
        self.assertIn("../diagnose/references/secret-redaction.md", triangulate)
        self.assertIn("before it enters the shared brief", triangulate)


if __name__ == "__main__":
    unittest.main()
