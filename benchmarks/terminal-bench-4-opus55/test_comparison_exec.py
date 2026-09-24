"""Modified harness command timeouts belong in the sandbox, not the Docker client."""
import asyncio
import shlex
import unittest

from harbor.environments.base import ExecResult
from comparison_exec import sandbox_exec


class ComparisonExecTests(unittest.TestCase):
    def test_timeout_is_a_tool_result_and_outer_transport_has_cleanup_headroom(self):
        class Environment:
            async def exec(self, command, *, cwd, timeout_sec):
                self.call = command, cwd, timeout_sec
                return ExecResult(stdout="partial", stderr="TERM sent", return_code=124)
        env = Environment()
        result = asyncio.run(sandbox_exec(env, "printf 'hello'; sleep 50", cwd="/app", timeout_sec=7))
        argv = shlex.split(env.call[0])
        self.assertEqual(argv, ["timeout", "--signal=TERM", "--kill-after=5s", "7s",
                                "/bin/sh", "-lc", "printf 'hello'; sleep 50"])
        self.assertEqual(env.call[1:], ("/app", 22))
        self.assertEqual(result.return_code, 124)
        self.assertEqual(result.stdout, "partial")

    def test_outer_timeout_or_infrastructure_error_is_not_fake_tool_success(self):
        class Environment:
            async def exec(self, *args, **kwargs):
                raise RuntimeError("Command timed out after 22 seconds")
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            asyncio.run(sandbox_exec(Environment(), "sleep 50", cwd=None, timeout_sec=7))

    def test_validate_before_any_exec(self):
        for command, limit in (("", 1), ("true", True), ("true", 0), ("true", 121)):
            with self.subTest(command=command, limit=limit), self.assertRaises(ValueError):
                asyncio.run(sandbox_exec(None, command, cwd=None, timeout_sec=limit))


if __name__ == "__main__":
    unittest.main()
