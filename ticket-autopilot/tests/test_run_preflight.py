"""Starting a run used to report one opaque failure for four different causes.

The q2 autopilot benchmark session failed to start three times, at turns 45, 49 and 51
(see `docs/specs/autopilot-protocol-friction-wayfinder.md`). Two attempts returned
`target-fetch-failed: cannot refresh configured target` and one returned the provider
message, but the same fetch failure also covered a missing remote, an unreachable one and
an unpushed branch, so a caller could not tell whether a fix had worked.

The decision recorded here is to keep failing closed: a repository with no usable remote
is refused, not run in a local mode. What changes is that each refusal now names which
precondition failed and what resolves it, and that the provider is checked before the
fetch instead of after, so its problem stops hiding behind the fetch's.

Both messages are unchanged. The detail is additive.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if __package__:
    from .git_test_support import GitIsolatedTestCase
else:
    from git_test_support import GitIsolatedTestCase

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CLI = SCRIPTS / "ticket-autopilot.py"
sys.path.insert(0, str(SCRIPTS))

from autopilot.providers import _origin_host

TICKET = (
    b'---\nticket_schema: 1\nticket_id: "X-01"\nexecution_mode: AFK\n'
    b"blocked_by: []\n---\n\n# X-01\n\n## What to Build\na\n"
)


class RunPreflightTest(GitIsolatedTestCase):
    """Each attempt below is one the benchmark run actually made."""

    def setUp(self) -> None:
        super().setUp()
        self.temporary = tempfile.TemporaryDirectory(prefix="apf03-")
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.repo = root / "repo"
        self.upstream = root / "upstream.git"
        self.repo.mkdir()
        self.git("init", "-b", "main", str(self.repo))
        self.git("-C", str(self.repo), "config", "user.email", "t@example.com")
        self.git("-C", str(self.repo), "config", "user.name", "Test")
        self.folder = self.repo / "docs/tickets/x"
        self.folder.mkdir(parents=True)
        (self.folder / "01-a.md").write_bytes(TICKET)
        self.git("-C", str(self.repo), "add", "-A")
        self.git("-C", str(self.repo), "commit", "-m", "init")

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True)

    def attempt(self, *extra: str) -> dict:
        """Start a run and return the parsed envelope, failure or success."""
        proc = subprocess.run(
            [sys.executable, "-B", str(CLI), "run", str(self.folder),
             "--repo", str(self.repo), "--base", "main", *extra],
            capture_output=True, text=True, cwd=str(self.repo),
        )
        return json.loads(proc.stdout or proc.stderr)

    def refusal(self, *extra: str) -> tuple[str, dict]:
        """Assert the attempt was refused and that it left nothing behind."""
        envelope = self.attempt(*extra)
        self.assertFalse(envelope["ok"], envelope)
        self.assertFalse(
            (self.repo / ".git/ticket-autopilot").exists(),
            "a refused preflight must leave no run directory, ledger or worktree",
        )
        self.assertEqual(
            self.git("-C", str(self.repo), "worktree", "list").stdout.strip().count("\n"),
            0,
            "a refused preflight must leave no worktree",
        )
        error = envelope["error"]
        detail = error.get("detail")
        self.assertIsInstance(detail, dict, "the refusal must name what to change")
        self.assertEqual(
            sorted(detail), ["expected", "field", "next_step", "received"]
        )
        return error["message"], detail

    def add_origin(self) -> None:
        self.git("init", "--bare", "-b", "main", str(self.upstream))
        self.git("-C", str(self.repo), "remote", "add", "origin", str(self.upstream))

    def test_a_repository_without_a_remote_is_refused_naming_both_remedies(self) -> None:
        """Turn 45: the run was started against a seeded repository with no origin."""
        message, detail = self.refusal()
        self.assertEqual(
            message, "repository has no origin; pass --provider for deterministic negotiation"
        )
        self.assertEqual(detail["field"], "remote.origin.url")
        self.assertIn("git remote add origin", detail["next_step"])
        self.assertIn("--provider", detail["next_step"])

    def test_the_provider_is_reported_before_the_fetch_that_used_to_hide_it(self) -> None:
        """Turn 51: the provider problem only surfaced once the fetch was made to work.

        With an origin whose host matches no known provider, the fetch would fail too.
        The caller has to hear about the provider, not about a fetch failure that says
        nothing about it.
        """
        self.git("-C", str(self.repo), "remote", "add", "origin",
                 "https://unknown.example/o/r.git")
        message, detail = self.refusal()
        self.assertEqual(
            message, "remote provider cannot be detected; pass an explicit supported override"
        )
        self.assertEqual(detail["received"], {"origin_host": "unknown.example", "override": None})

    def test_the_three_causes_of_a_failed_refresh_are_told_apart(self) -> None:
        """One message covered all three; the detail now separates them."""
        absent = self.refusal("--provider", "github")[1]["received"]
        self.assertEqual(absent["origin"], "absent")

        self.git("-C", str(self.repo), "remote", "add", "origin",
                 str(self.upstream / "never-created"))
        unreachable = self.refusal("--provider", "github")[1]["received"]
        self.assertEqual(
            (unreachable["origin"], unreachable["reachable"]), ("configured", False)
        )

        self.git("-C", str(self.repo), "remote", "remove", "origin")
        self.add_origin()
        unpushed = self.refusal("--provider", "github")[1]
        self.assertEqual(
            (unpushed["received"]["reachable"], unpushed["received"]["branch"]),
            (True, "missing"),
        )
        self.assertIn("push main to origin", unpushed["next_step"])

    def test_following_the_advice_reaches_a_started_run(self) -> None:
        """The advice has to be executable, not merely printed.

        Each refusal's next step is applied, and the attempt is repeated. If any advice
        were wrong, the chain would stall on the same message instead of advancing.
        """
        first = self.refusal()[1]["next_step"]
        self.assertIn("--provider", first)

        second = self.refusal("--provider", "github")[1]["next_step"]
        self.assertIn("git remote add origin", second)
        self.add_origin()

        third = self.refusal("--provider", "github")[1]["next_step"]
        self.assertIn("push main to origin", third)
        self.git("-C", str(self.repo), "push", "-q", "origin", "main")

        envelope = self.attempt("--provider", "github")
        self.assertTrue(envelope["ok"], envelope)

    def test_no_credential_from_a_remote_url_reaches_the_envelope(self) -> None:
        """An https remote can carry a token; the refusal must not republish it."""
        self.git("-C", str(self.repo), "remote", "add", "origin",
                 "https://someone:s3cr3t-token@unknown.example/o/r.git")
        envelope = self.attempt()
        self.assertNotIn("s3cr3t-token", json.dumps(envelope))
        self.assertEqual(
            envelope["error"]["detail"]["received"]["origin_host"], "unknown.example"
        )

    def test_a_successful_start_is_unchanged(self) -> None:
        """The preflight must not refuse a run that used to work."""
        self.add_origin()
        self.git("-C", str(self.repo), "push", "-q", "origin", "main")
        envelope = self.attempt("--provider", "github")
        self.assertTrue(envelope["ok"], envelope)
        self.assertNotIn("detail", envelope)


class OriginHostTest(unittest.TestCase):
    """The host names which detection rule missed; the URL may name a secret."""

    def test_a_credential_in_the_url_is_left_behind(self) -> None:
        self.assertEqual(
            _origin_host("https://user:SECRET@github.com/o/r.git"), "github.com"
        )

    def test_scp_syntax_and_azure_resolve_to_their_hosts(self) -> None:
        self.assertEqual(_origin_host("git@github.com:o/r.git"), "github.com")
        self.assertEqual(
            _origin_host("https://dev.azure.com/o/p/_git/r"), "dev.azure.com"
        )

    def test_a_filesystem_remote_has_no_host_to_report(self) -> None:
        """Reading a host out of a Windows path yields the drive letter, which names nothing."""
        self.assertEqual(_origin_host("C:\\repos\\x.git"), "local path")
        self.assertEqual(_origin_host("/srv/repos/x.git"), "local path")
        self.assertIsNone(_origin_host(""))


if __name__ == "__main__":
    unittest.main()
