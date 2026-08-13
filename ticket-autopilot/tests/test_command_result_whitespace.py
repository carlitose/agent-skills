from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from autopilot.git_ops import CommandResult, SubprocessCommandRunner  # noqa: E402
from autopilot.providers import (  # noqa: E402
    GET_PR_STATE,
    ProviderExecutor,
    detect_provider,
)


class CommandResultWhitespaceTests(unittest.TestCase):
    """Pins the boundary `WD-02` deferred as "a separate latent equality hazard".

    The hazard is real but inert, and the resolution is the opposite of removing the trim:
    every current consumer treats the output as a scalar and would break without it. What
    was missing is a stated contract and a test that fails if someone later routes a
    whitespace-sensitive payload through this type.
    """

    def test_output_is_trimmed_because_consumers_compare_it_as_a_scalar(self) -> None:
        child = (
            "import sys; "
            "sys.stdout.write('bba712e76f846010f85ed776bb82b0e1b1f7add0\\n'); "
            "sys.stderr.write('  noisy  \\n')"
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = SubprocessCommandRunner().run(
                [sys.executable, "-c", child], cwd=Path(temporary)
            )

        # This is what `git rev-parse` actually answers, and it is compared against a tree
        # OID by identity. Without the trim that comparison never matches.
        self.assertEqual("bba712e76f846010f85ed776bb82b0e1b1f7add0", result.stdout)
        self.assertEqual("noisy", result.stderr)

    def test_a_trailing_newline_does_not_survive_this_type(self) -> None:
        # Stated as a test so the limitation is discoverable from the suite rather than
        # only from a docstring: do not read a body, a file, or a diff back through here.
        # Binary write: a text-mode child on Windows translates \n to \r\n itself, which is
        # the child's behaviour and not the contract under test here.
        child = "import sys; sys.stdout.buffer.write(b'## Summary\\nbody\\n')"
        with tempfile.TemporaryDirectory() as temporary:
            result = SubprocessCommandRunner().run(
                [sys.executable, "-c", child], cwd=Path(temporary)
            )

        self.assertNotEqual("## Summary\nbody\n", result.stdout)
        self.assertEqual("## Summary\nbody", result.stdout)

    def test_a_pr_body_reaches_the_readback_untrimmed_because_it_travels_as_json(
        self,
    ) -> None:
        # The delivery readback compares the body literally, so if it were read back as
        # command text every delivery whose body ends in a newline would gate. It does not:
        # the body is a JSON field, and JSON decoding is unaffected by the trim.
        body = "## Summary\n\nA line.\n"
        document = {
            "number": 57,
            "url": "https://example.invalid/pull/57",
            "state": "OPEN",
            "mergedAt": None,
            "headRefName": "ticket/wt-05",
            "headRefOid": "head-wt05",
            "baseRefName": "main",
            "body": body,
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
        }

        class JsonViewExecutor(ProviderExecutor):
            def _github_view(self, _pr_id: str) -> dict[str, object]:
                return self._json(
                    [
                        sys.executable,
                        "-c",
                        "import sys; sys.stdout.write("
                        f"{json.dumps(document)!r}"
                        " + '\\n')",
                    ]
                )

        with tempfile.TemporaryDirectory() as temporary:
            executor = JsonViewExecutor(
                detect_provider("", override="github"),
                cwd=Path(temporary),
                runner=SubprocessCommandRunner(),
            )
            receipt = executor.execute(GET_PR_STATE, pr_id="57")

        self.assertEqual(body, receipt["body"])

    def test_the_dataclass_carries_the_contract(self) -> None:
        self.assertIn("whitespace-sensitive", CommandResult.__doc__ or "")


if __name__ == "__main__":
    unittest.main()
