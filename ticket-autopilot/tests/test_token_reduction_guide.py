from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
GUIDE = REPO_ROOT / "docs" / "autopilot-context-cost-guide.md"
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from controlled_inventory import REPOSITORY_ONLY_SKILLS  # noqa: E402
from autopilot.context_budget import measure_context_budget  # noqa: E402


class TokenReductionGuideTests(unittest.TestCase):
    def controlled_report(self) -> dict[str, object]:
        absent = REPOSITORY_ONLY_SKILLS
        with tempfile.TemporaryDirectory() as temporary:
            install = Path(temporary) / "installed"
            install.mkdir()
            for skill in sorted(REPO_ROOT.glob("*/SKILL.md")):
                if skill.parent.name not in absent:
                    shutil.copytree(skill.parent, install / skill.parent.name)
            return measure_context_budget(
                REPO_ROOT,
                install_root=install,
                workflow="ticket-autopilot",
            )

    def test_quoted_baseline_matches_the_controlled_tk02_report(self) -> None:
        report = self.controlled_report()
        guide = GUIDE.read_text(encoding="utf-8")
        listing = report["always_on_listing"]
        closure = report["workflow_static_closure"]
        listing_bytes = listing["normalized_bytes"]
        closure_bytes = closure["normalized_bytes"]
        combined = listing_bytes + closure_bytes

        for row in (
            f"| Always-on listing | `{listing_bytes:,}` normalized UTF-8 bytes | "
            f"`{listing['visible_skill_count']}` installed model-visible skills |",
            f"| Ticket-autopilot static closure | `{closure_bytes:,}` normalized "
            f"UTF-8 bytes | `{closure['source_count']}` workflow files |",
            f"| Combined static prefix | `{combined:,}` normalized UTF-8 bytes |",
        ):
            with self.subTest(row=row):
                self.assertIn(row, guide)

    def test_guidance_preserves_authority_and_verification_boundaries(self) -> None:
        guide = GUIDE.read_text(encoding="utf-8")
        for required in (
            "Operator behavior:",
            "Contract behavior:",
            "Inline serial composition is the portable default",
            "explicit authority",
            "Verification is not a reduction lever",
            "unmeasured until `TK-09`",
        ):
            with self.subTest(required=required):
                self.assertIn(required, guide)
        self.assertIsNone(re.search(r"\b\d+(?:\.\d+)?%", guide))


if __name__ == "__main__":
    unittest.main()
