"""Process-level mutual exclusion via fcntl.flock.

The scanner is invoked by cron every minute. A single scan can run
30-60s under adverse network conditions, so two scans can overlap.
Without a lock, both would read the ledger, both would compute the
same next_id, and the second save() would silently overwrite the first.

Use as a context manager:

    with single_scan_lock("/tmp/cex-signal-lab.lock") as got_lock:
        if not got_lock:
            log("another scan in flight, exiting")
            return
        ...
"""

from __future__ import annotations

import contextlib
import errno
import fcntl
import os
from pathlib import Path
from typing import Iterator


@contextlib.contextmanager
def single_scan_lock(path: Path | str) -> Iterator[bool]:
    """Yield True if we acquired the lock, False if another holder exists."""
    fd = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o644)
    got = False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            got = True
        except OSError as e:
            if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise
        if got:
            os.write(fd, f"{os.getpid()}\n".encode())
        yield got
    finally:
        if got:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(fd)
