from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
sys.path.insert(0, str(SCRIPTS))

from autopilot.git_ops import SubprocessCommandRunner  # noqa: E402
from autopilot.providers import (  # noqa: E402
    GET_PR_STATE,
    ProviderExecutor,
    detect_provider,
)


class Utf8IoTests(unittest.TestCase):
    def test_command_runner_decodes_stdout_and_stderr_as_utf8(self) -> None:
        payload = "PR body — café"
        child = (
            "import sys; "
            f"payload = {payload!r}.encode('utf-8'); "
            "sys.stdout.buffer.write(payload); "
            "sys.stderr.buffer.write(payload)"
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = SubprocessCommandRunner().run(
                [sys.executable, "-c", child], cwd=Path(temporary)
            )

        self.assertEqual(0, result.returncode)
        self.assertEqual(payload, result.stdout)
        self.assertEqual(payload, result.stderr)

    def test_undecodable_stdout_fails_loudly_because_it_is_data(self) -> None:
        # stdout feeds digests, equality checks and assert_cleanup_safe, which authorizes
        # deleting a worktree. A byte that is not UTF-8 must not become U+FFFD inside one
        # of those comparisons; it must stop the run. This is WD-02's invariant.
        child = "import sys; sys.stdout.buffer.write(b'head-\\xf3-sha')"
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(UnicodeDecodeError):
                SubprocessCommandRunner().run(
                    [sys.executable, "-c", child], cwd=Path(temporary)
                )

    def test_undecodable_stderr_is_preserved_because_it_is_a_diagnostic(self) -> None:
        # On a non-English Windows, git and the provider CLI report failures in the console
        # codepage. Decoding stderr strictly raised UnicodeDecodeError and destroyed the
        # very message being reported, so it is decoded leniently and still arrives.
        child = (
            "import sys; "
            "sys.stderr.buffer.write('fatal: no se encontr'.encode('utf-8')"
            " + b'\\xf3' + ' el archivo'.encode('utf-8')); "
            "sys.exit(128)"
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = SubprocessCommandRunner().run(
                [sys.executable, "-c", child], cwd=Path(temporary)
            )

        self.assertEqual(128, result.returncode)
        self.assertIn("fatal: no se encontr", result.stderr)
        self.assertIn("el archivo", result.stderr)
        self.assertIn("�", result.stderr)

    def test_cli_redirected_json_is_utf8_despite_locale_encoding(self) -> None:
        ticket = (
            "---\n"
            "ticket_schema: 1\n"
            'ticket_id: "UTF8-01"\n'
            "execution_mode: AFK\n"
            "blocked_by: []\n"
            "---\n\n"
            "# Ticket — café\n"
        )
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "cp1252"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ticket_path = root / "ticket.md"
            output_path = root / "output.json"
            ticket_path.write_text(ticket, encoding="utf-8", newline="\n")
            with output_path.open("wb") as output:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "ticket-parse",
                        str(ticket_path),
                    ],
                    cwd=root,
                    env=environment,
                    stdout=output,
                    stderr=subprocess.PIPE,
                    check=False,
                )
            raw_output = output_path.read_bytes()

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(raw_output.decode("utf-8"))
        self.assertEqual("# Ticket — café\n", payload["data"]["body"])

    def test_provider_pr_body_survives_utf8_readback_unchanged(self) -> None:
        body = "Summary — naïve café"
        document = {
            "number": 57,
            "url": "https://example.invalid/pull/57",
            "state": "OPEN",
            "mergedAt": None,
            "headRefName": "ticket/utf8",
            "headRefOid": "head-utf8",
            "baseRefName": "main",
            "body": body,
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
        }
        child = (
            "import json, sys; "
            f"document = {document!r}; "
            "sys.stdout.buffer.write("
            "json.dumps(document, ensure_ascii=False).encode('utf-8'))"
        )

        class PythonViewExecutor(ProviderExecutor):
            def _github_view(self, _pr_id: str) -> dict[str, object]:
                return self._json([sys.executable, "-c", child])

        with tempfile.TemporaryDirectory() as temporary:
            executor = PythonViewExecutor(
                detect_provider("", override="github"),
                cwd=Path(temporary),
                runner=SubprocessCommandRunner(),
            )
            receipt = executor.execute(GET_PR_STATE, pr_id="57")

        self.assertEqual(body, receipt["body"])


if __name__ == "__main__":
    unittest.main()
