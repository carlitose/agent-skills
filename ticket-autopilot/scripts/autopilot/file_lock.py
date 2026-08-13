"""One cross-platform advisory file lock, owned in one place.

`ledger.py` and `ticket_lifecycle.py` each grew their own copy of the same Windows dance —
extend the file to a byte, seek back, `msvcrt.locking` — and they drifted: the ledger locks
without blocking, the lifecycle folder blocks. Both behaviours are wanted, so the choice is
a parameter here rather than a second implementation elsewhere.

Blocking semantics are not identical across platforms and cannot be made so:

- POSIX `fcntl.flock(LOCK_EX)` waits indefinitely.
- Windows `msvcrt.locking(LK_LOCK, 1)` retries ten times at one-second intervals and then
  raises `OSError`.

So a blocking acquisition can still fail on Windows after roughly ten seconds. Callers must
treat `OSError` as "someone else holds it", not as "the lock is broken".
"""

from __future__ import annotations

import os
from typing import IO

# A named seam rather than an `os.name` check at each branch: tests flip this to drive the
# other platform's path, which patching `os.name` itself cannot do without breaking every
# other consumer of that module in the process.
WINDOWS = os.name == "nt"

if WINDOWS:
    import msvcrt
else:
    import fcntl


def acquire_file_lock(handle: IO[str], *, blocking: bool = False) -> None:
    """Take an exclusive lock on `handle`, raising `OSError` if it is held.

    On Windows the lock covers one byte, and a zero-length file has no byte to cover, so
    the file is extended once before locking.
    """

    if WINDOWS:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write("\0")
            handle.flush()
        handle.seek(0)
        mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
        msvcrt.locking(handle.fileno(), mode, 1)
        return
    flags = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
    fcntl.flock(handle.fileno(), flags)


def release_file_lock(handle: IO[str]) -> None:
    """Release a lock taken by `acquire_file_lock`."""

    if WINDOWS:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
