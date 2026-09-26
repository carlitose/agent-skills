"""Run foreground task commands with an in-container deadline and group cleanup.

GNU timeout returns 124/137 as a model-visible tool result. The outer Harbor
transport gets cleanup headroom; its failure still aborts because termination
inside the sandbox is then unconfirmed. Never swallow that infrastructure error.
"""
import shlex

from harbor.environments.base import ExecResult


async def sandbox_exec(environment, command: str, *, cwd: str | None, timeout_sec: int):
    if not isinstance(command, str) or not command or len(command) > 16384:
        raise ValueError("invalid sandbox command")
    if type(timeout_sec) is not int or not 1 <= timeout_sec <= 120:
        raise ValueError("invalid sandbox timeout")
    if "\x00" in command or (cwd is not None and "\x00" in cwd):
        # No OS can pass a NUL inside argv; Windows CreateProcess raised and killed the whole
        # agent run. It is the model's malformed command, so it gets a model-visible error.
        return ExecResult(stdout="", stderr="sandbox_exec: command or cwd contains a NUL byte; not executed",
                          return_code=2)
    wrapped = (f"timeout --signal=TERM --kill-after=5s {timeout_sec}s "
               f"/bin/sh -lc {shlex.quote(command)}")
    return await environment.exec(wrapped, cwd=cwd, timeout_sec=timeout_sec + 15)
