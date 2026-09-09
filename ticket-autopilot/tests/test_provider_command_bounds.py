from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from autopilot.git_ops import GitError, SubprocessCommandRunner
from autopilot.providers import (
    CREATE_OR_UPDATE_PR, GET_REPOSITORY, ProviderError, ProviderExecutor, detect_provider,
)

# A local provider-state model, not a live Azure service. Each invocation executes
# a real child and writes acceptance before the response transport can time out.
AZURE_TIMEOUT_MODEL = r'''
import json
from pathlib import Path
import sys
import time
state_path = Path(STATE)
state = json.loads(state_path.read_text(encoding="utf-8"))
verb = ARGV[2]
state["calls"].append(verb)
def value(flag):
    return ARGV[ARGV.index(flag) + 1]
def body():
    return "\n".join(ARGV[ARGV.index("--description") + 1:ARGV.index("--output")])
if verb == "list":
    response = [state["pr"]] if state["pr"] else []
elif verb == "create":
    state["pr"] = {
        "pullRequestId":91, "url":"https://example.invalid/pr/91", "status":"active",
        "sourceRefName":"refs/heads/" + value("--source-branch"),
        "targetRefName":"refs/heads/" + value("--target-branch"),
        "lastMergeSourceCommit":{"commitId":"a" * 40}, "description":body(),
    }
    response = state["pr"]
elif verb == "update":
    state["pr"]["description"] = body()
    response = state["pr"]
elif verb == "show":
    response = state["pr"]
else:
    raise AssertionError(ARGV)
state_path.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8",newline="\n")
if verb == "create":
    sys.stderr.buffer.write(b"fixture mutation accepted; response transport uncertain\n")
    sys.stderr.buffer.flush()
    time.sleep(8)
elif verb == "list" and state["reject_list"] and state["pr"]:
    sys.stdout.buffer.write(b'{"incomplete":')
    sys.stdout.buffer.flush()
    time.sleep(8)
sys.stdout.buffer.write(json.dumps(response,ensure_ascii=False).encode("utf-8"))
'''


class ProviderCommandBoundsTests(unittest.TestCase):
    def test_accepted_create_timeout_requires_readback_not_a_duplicate_create(self):
        with tempfile.TemporaryDirectory(prefix="provider-timeout-é-") as directory:
            root = Path(directory)
            script = root / "provider model.py"
            state_path = root / "state.json"
            script.write_text(AZURE_TIMEOUT_MODEL, encoding="utf-8", newline="\n")
            state_path.write_text(json.dumps({"calls": [], "pr": None, "reject_list": False}),
                                  encoding="utf-8", newline="\n")

            class RawModelRunner(SubprocessCommandRunner):
                def run(self, command, *, cwd):
                    source = (
                        "import runpy; "
                        f"runpy.run_path({str(script)!r}, init_globals="
                        f"{{'ARGV':{command[1:]!r},'STATE':{str(state_path)!r}}})"
                    )
                    return super().run(["az", "-B", "-c", source], cwd=cwd)

            executor = ProviderExecutor(
                detect_provider("", override="azure-devops"), cwd=root,
                runner=RawModelRunner(azure_stdout_encoding="utf-8"),
            )
            parameters = dict(branch="ticket/apm05", base="main", head_sha="a" * 40,
                              title="APM-05", body_artifact="lógica / café β\n")
            with patch.dict(os.environ, {
                "TICKET_AUTOPILOT_COMMAND_TIMEOUT_SECONDS": "0.5",
                "TICKET_AUTOPILOT_COMMAND_MAX_OUTPUT_BYTES": "8192",
            }), patch("autopilot.git_ops.shutil.which", return_value=sys.executable):
                with self.assertRaisesRegex(ProviderError, "timeout") as raised:
                    executor.execute(CREATE_OR_UPDATE_PR, **parameters)
                self.assertIn("fixture mutation accepted", str(raised.exception))
                self.assertIn("uncertain", str(raised.exception))
                self.assertIn("reobserve", str(raised.exception))
                state = json.loads(state_path.read_text(encoding="utf-8"))
                self.assertEqual(state["calls"], ["list", "create"])
                self.assertEqual(state["pr"]["description"], parameters["body_artifact"])

                state["reject_list"] = True
                state_path.write_text(json.dumps(state), encoding="utf-8", newline="\n")
                with self.assertRaisesRegex(ProviderError, "timeout"):
                    executor.execute(CREATE_OR_UPDATE_PR, **parameters)
                state = json.loads(state_path.read_text(encoding="utf-8"))
                self.assertEqual(state["calls"], ["list", "create", "list"])

                state["reject_list"] = False
                state_path.write_text(json.dumps(state), encoding="utf-8", newline="\n")
                receipt = executor.execute(CREATE_OR_UPDATE_PR, **parameters)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["calls"], ["list", "create", "list", "list", "update", "show"])
            self.assertEqual(state["calls"].count("create"), 1)
            self.assertEqual(receipt["body"], parameters["body_artifact"])
            self.assertEqual(receipt["head_sha"], parameters["head_sha"])
            # A normalized receipt from this substituted producer is still only a
            # fixture observation, regardless of the executor's default mode field.

    def test_bounded_repository_readback_failure_is_not_reported_as_absence(self):
        class FailedCapture:
            def run(self, command, *, cwd):
                raise GitError("command output-limit; outcome is uncertain; reobserve")

        executor = ProviderExecutor(
            detect_provider("", override="github"), cwd=Path("."), runner=FailedCapture(),
        )
        # This is a boundary-failure fixture, not native process/provider evidence.
        # The default native executor is exercised separately in test_command_bounds.
        with self.assertRaisesRegex(ProviderError, "output-limit") as raised:
            executor.execute(GET_REPOSITORY, target="fixture/project")
        self.assertIsInstance(raised.exception.__cause__, GitError)


if __name__ == "__main__":
    unittest.main()
