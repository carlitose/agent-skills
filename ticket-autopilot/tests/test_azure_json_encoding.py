from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from autopilot import git_ops
from autopilot.git_ops import AzureCliOutputError, SubprocessCommandRunner

if __package__:
    from .git_test_support import isolated_git_environment
else:
    from git_test_support import isolated_git_environment
from autopilot.providers import (
    CREATE_OR_UPDATE_PR, GET_PR_STATE, ProviderError, ProviderExecutor, detect_provider,
)

ENCODING_ENV = "TICKET_AUTOPILOT_AZURE_STDOUT_ENCODING"

# A local file-backed provider model. It persists acceptance BEFORE emitting a
# faulty response; every real child emits bytes through the production runner.
AZURE_CHILD = r'''
import json
from pathlib import Path
import sys
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
        "pullRequestId":91,"url":"https://example.invalid/pr/91","status":"active",
        "sourceRefName":"refs/heads/" + value("--source-branch"),
        "targetRefName":"refs/heads/" + value("--target-branch"),
        "lastMergeSourceCommit":{"commitId":"a" * 40},"description":body()
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
    if state["fault"] == "decode":
        sys.stdout.buffer.write(b'{"description":"\xf3"}')
    elif state["fault"] == "json":
        sys.stdout.buffer.write(b'{"pullRequestId":91')
    else:
        sys.stdout.buffer.write(b'{"pullRequestId":91}')
        sys.stderr.buffer.write(b"Unable to encode the output with cp1252 encoding. Unsupported characters are discarded.\n")
elif verb == "list" and state["reject_list"] and state["pr"]:
    sys.stdout.buffer.write(b'{')
else:
    sys.stdout.buffer.write(json.dumps(response,ensure_ascii=False).encode("utf-8"))
'''


def azure_document(body: str) -> dict:
    return {
        "pullRequestId": 91,
        "url": "https://example.invalid/pr/91",
        "status": "active",
        "sourceRefName": "refs/heads/ticket/apm09",
        "targetRefName": "refs/heads/main",
        "lastMergeSourceCommit": {"commitId": "a" * 40},
        "description": body,
        "repository": {"project": {"description": body}},
    }


def raw_child(payload: bytes, stderr: bytes = b"", exit_code: int = 0) -> list[str]:
    source = (
        "import sys; "
        f"sys.stdout.buffer.write(bytes.fromhex('{payload.hex()}')); "
        f"sys.stderr.buffer.write(bytes.fromhex('{stderr.hex()}')); "
        f"sys.exit({exit_code})"
    )
    # The resolver seam substitutes a real local Python producer for az. No
    # already-decoded result fake or live Azure command is used.
    return ["az", "-c", source]


class AzureJsonEncodingTests(unittest.TestCase):
    def view(self, payload: bytes, encoding: str, stderr: bytes = b"", exit_code: int = 0) -> tuple[dict, dict]:
        class RawAzureView(ProviderExecutor):
            def _azure_view(self, _pr_id):
                self.parsed = self._json(raw_child(payload, stderr, exit_code))
                return self.parsed

        with tempfile.TemporaryDirectory(prefix="az-json-à-") as temporary:
            with patch.dict(os.environ, {ENCODING_ENV: encoding}):
                runner = SubprocessCommandRunner()
            executor = RawAzureView(
                detect_provider("", override="azure-devops"),
                cwd=Path(temporary), runner=runner,
            )
            with patch("autopilot.git_ops.shutil.which", return_value=sys.executable):
                receipt = executor.execute(GET_PR_STATE, pr_id="91")
            return receipt, executor.parsed

    def test_configured_cp1252_raw_bytes_reach_provider_without_text_change(self):
        document = azure_document("## Summary\nlógica / café.txt\n")
        payload = json.dumps(document, ensure_ascii=False).encode("cp1252")
        self.assertIn(b"\xf3", payload)
        receipt, parsed = self.view(payload, "cp1252")
        self.assertEqual(parsed, document)
        self.assertEqual(receipt["body"], document["description"])
        self.assertEqual(receipt["head_sha"], "a" * 40)
        self.assertEqual(receipt["branch"], "ticket/apm09")

    def test_explicit_utf8_profile_preserves_wide_unicode(self):
        document = azure_document("lógica / café β 日本 / cafe\u0301.txt\r\n \t")
        receipt, parsed = self.view(json.dumps(document, ensure_ascii=False).encode("utf-8"), "utf-8")
        self.assertEqual(parsed, document)
        self.assertEqual(receipt["body"], document["description"])

    def test_another_configured_windows_codepage_preserves_intended_text(self):
        document = azure_document("Łódź / zážitek.txt\n")
        receipt, parsed = self.view(json.dumps(document, ensure_ascii=False).encode("cp1250"), "cp1250")
        self.assertEqual(parsed, document)
        self.assertEqual(receipt["body"], document["description"])

    def test_ambiguous_bytes_follow_only_the_explicit_profile(self):
        payload = json.dumps(azure_document("lógica"), ensure_ascii=False).encode("utf-8")
        utf8, _ = self.view(payload, "utf-8")
        ansi, _ = self.view(payload, "cp1252")
        self.assertEqual(utf8["body"], "lógica")
        self.assertEqual(ansi["body"], "l\u00c3\u00b3gica")
        self.assertNotEqual(utf8["body"], ansi["body"])

    def test_missing_unknown_and_transforming_profiles_fail_before_execution(self):
        for profile in ["", "unknown-encoding", "utf-8-sig", "utf-16", "base64_codec"]:
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as temporary:
                runner = SubprocessCommandRunner(azure_stdout_encoding=profile)
                with patch("autopilot.git_ops._run_captured") as capture:
                    with self.assertRaises(AzureCliOutputError) as caught:
                        runner.run(["az", "repos", "pr", "create"], cwd=Path(temporary))
                capture.assert_not_called()
                self.assertIsNone(caught.exception.returncode)
                self.assertIn("not executed", str(caught.exception))

    def test_default_provider_construction_reads_the_scoped_setting(self):
        # This is the same runner=None path used by the CLI's provider factories.
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {ENCODING_ENV: "cp1252"}):
                executor = ProviderExecutor(detect_provider("", override="azure-devops"), cwd=Path(temporary))
            with patch("autopilot.git_ops.shutil.which", return_value=sys.executable):
                self.assertEqual(executor._json(raw_child(b'{"text":"l\xf3gica"}')), {"text":"lógica"})

    def test_unset_profile_fails_through_provider_before_a_child_runs(self):
        with patch.dict(os.environ):
            os.environ.pop(ENCODING_ENV, None)
            executor = ProviderExecutor(detect_provider("", override="azure-devops"), cwd=Path("."))
        with patch("autopilot.git_ops._run_captured") as capture:
            with self.assertRaises(ProviderError) as caught:
                executor.execute(GET_PR_STATE, pr_id="91")
        capture.assert_not_called()
        self.assertIn(ENCODING_ENV, str(caught.exception))

    def test_explicit_setting_wins_without_rewriting_environment_or_logical_identity(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {ENCODING_ENV: "unsupported-fixture-profile"}):
            runner = SubprocessCommandRunner(azure_stdout_encoding="cp1252")
            for name in ["az", "AZ.CMD", str(Path(temporary) / "az.exe")]:
                with self.subTest(name=name), patch("autopilot.git_ops.shutil.which", return_value=sys.executable):
                    command = raw_child(b"l\xf3gica")
                    command[0] = name
                    self.assertEqual(runner.run(command, cwd=Path(temporary)).stdout, "lógica")
            self.assertEqual(os.environ[ENCODING_ENV], "unsupported-fixture-profile")

    def test_undefined_bytes_fail_with_exit_and_existing_stderr_diagnostics(self):
        for code in [0, 7]:
            with self.subTest(exit_code=code):
                with self.assertRaises(ProviderError) as caught:
                    self.view(b'{"description":"\x81"}', "cp1252", b"fixture diagnostic \xf3", code)
                cause = caught.exception.__cause__
                self.assertIsInstance(cause, AzureCliOutputError)
                self.assertEqual(cause.returncode, code)
                self.assertEqual(cause.stderr, "fixture diagnostic �")
                self.assertIn("cp1252", str(caught.exception))
                self.assertIn("may already have taken effect", str(caught.exception))

    def test_known_lossy_knack_output_is_rejected_even_with_valid_json_and_exit_zero(self):
        warning = b"Unable to encode the output with cp1252 encoding. Unsupported characters are discarded.\r\n"
        with self.assertRaises(ProviderError) as caught:
            self.view(json.dumps(azure_document("lgica / caf  .txt")).encode("ascii"), "cp1252", warning)
        self.assertIn("discarded characters", str(caught.exception))
        self.assertEqual(caught.exception.__cause__.returncode, 0)

    def test_malformed_and_truncated_json_keep_available_diagnostics(self):
        for payload in [b"{", b"not json"]:
            with self.subTest(payload=payload), self.assertRaises(ProviderError) as caught:
                self.view(payload, "utf-8", b"fixture response truncated")
            self.assertIn("invalid JSON", str(caught.exception))
            self.assertIn("fixture response truncated", str(caught.exception))
            self.assertIn("may already have taken effect", str(caught.exception))

    def test_nonzero_response_still_reports_the_existing_diagnostic(self):
        with self.assertRaises(ProviderError) as caught:
            self.view(b'{}', "cp1252", b"fixture command failed \xf3", 7)
        self.assertIn("fixture command failed �", str(caught.exception))

    def test_other_commands_do_not_acquire_azure_decoding_or_warning_policy(self):
        runner = SubprocessCommandRunner(azure_stdout_encoding="cp1252")
        with tempfile.TemporaryDirectory() as temporary:
            for name in ["git", "gh", "other-tool"]:
                with self.subTest(command=name), patch("autopilot.git_ops.shutil.which", return_value=sys.executable):
                    valid = raw_child("lógica".encode("utf-8"))
                    valid[0] = name
                    self.assertEqual(runner.run(valid, cwd=Path(temporary)).stdout, "lógica")
                    invalid = raw_child(b"head-\xf3-sha")
                    invalid[0] = name
                    with self.assertRaises(UnicodeDecodeError):
                        runner.run(invalid, cwd=Path(temporary))
            warning = b"Unable to encode the output with cp1252 encoding. Unsupported characters are discarded."
            command = raw_child(b"safe", warning)
            command[0] = sys.executable
            self.assertEqual(runner.run(command, cwd=Path(temporary)).stdout, "safe")

    def test_uncertain_create_is_reobserved_not_blindly_created_again(self):
        for fault in ["decode", "json", "lossy"]:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(prefix="az-resume-à-") as temporary:
                root = Path(temporary)
                script = root / "provider model.py"
                state_path = root / "state.json"
                script.write_text(AZURE_CHILD, encoding="utf-8", newline="\n")
                state_path.write_text(json.dumps({"calls":[], "pr":None, "fault":fault, "reject_list":False}), encoding="utf-8", newline="\n")

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
                parameters = dict(branch="ticket/apm09", base="main", head_sha="a" * 40, title="APM-09", body_artifact="lógica\n")
                with patch("autopilot.git_ops.shutil.which", return_value=sys.executable):
                    with self.assertRaises(ProviderError) as caught:
                        executor.execute(CREATE_OR_UPDATE_PR, **parameters)
                    self.assertIn("fixture mutation accepted", str(caught.exception))
                    self.assertIn("may already have taken effect", str(caught.exception))
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                    self.assertEqual(state["calls"], ["list", "create"])
                    self.assertIsNotNone(state["pr"])
                    # An unreadable reconciliation response cannot authorize a
                    # second create either. This observation itself is retained.
                    state["reject_list"] = True
                    state_path.write_text(json.dumps(state), encoding="utf-8", newline="\n")
                    with self.assertRaises(ProviderError):
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


class GitCleanupEncodingTests(unittest.TestCase):
    def test_azure_setting_cannot_relax_real_git_cleanup_branch_identity(self):
        with isolated_git_environment(), tempfile.TemporaryDirectory(prefix="az-git-") as temporary:
            root = Path(temporary)
            repo, remote = root / "repo à", root / "remote β.git"
            repo.mkdir()
            remote.mkdir()

            def git(cwd, *args):
                return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True, timeout=15).stdout

            git(remote, "init", "--bare")
            git(repo, "init", "-b", "ticket/café")
            sentinel = repo / "data.txt"
            sentinel.write_bytes(b"unchanged\n")
            git(repo, "add", "data.txt")
            git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")
            git(repo, "remote", "add", "origin", str(remote))
            git(repo, "push", "-u", "origin", "HEAD")
            head = git_ops.run_git(repo, "rev-parse", "HEAD")
            capture = git_ops._run_captured
            commands = []

            def invalid_branch(command, *, cwd):
                commands.append(command)
                if command[:2] == ["git", "symbolic-ref"]:
                    child = raw_child(b"ticket-\xf3")
                    child[0] = sys.executable
                    return capture(child, cwd=cwd)
                return capture(command, cwd=cwd)

            with patch.dict(os.environ, {ENCODING_ENV: "cp1252"}):
                self.assertEqual(git_ops.run_git(repo, "symbolic-ref", "--short", "HEAD"), "ticket/café")
                self.assertIsNone(git_ops.assert_cleanup_safe(repo, {"base_sha": head}))
                with patch("autopilot.git_ops._run_captured", side_effect=invalid_branch):
                    with self.assertRaises(UnicodeDecodeError):
                        git_ops.assert_cleanup_safe(repo, {"base_sha": head})
            self.assertEqual([command[1] for command in commands], ["status", "rev-parse", "symbolic-ref"])
            self.assertEqual(git_ops.run_git(repo, "rev-parse", "HEAD"), head)
            self.assertEqual(sentinel.read_bytes(), b"unchanged\n")
            self.assertTrue(repo.is_dir())


if __name__ == "__main__":
    unittest.main()
