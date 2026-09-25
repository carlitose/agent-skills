"""Run foreground task commands with an in-container deadline and group cleanup.

GNU timeout returns 124/137 as a model-visible tool result. The outer Harbor
transport gets cleanup headroom; its failure still aborts because termination
inside the sandbox is then unconfirmed. Never swallow that infrastructure error.
"""
import shlex


async def sandbox_exec(environment, command: str, *, cwd: str | None, timeout_sec: int):
    if not isinstance(command, str) or not command or len(command) > 16384:
        raise ValueError("invalid sandbox command")
    if type(timeout_sec) is not int or not 1 <= timeout_sec <= 120:
        raise ValueError("invalid sandbox timeout")
    wrapped = (f"timeout --signal=TERM --kill-after=5s {timeout_sec}s "
               f"/bin/sh -lc {shlex.quote(command)}")
    return await environment.exec(wrapped, cwd=cwd, timeout_sec=timeout_sec + 15)
