"""Wait for job assignment before launching the requested local executable."""
from __future__ import annotations

import os
import subprocess
import sys


def main():
    # Read exactly one byte at the OS boundary: buffered stdin could consume
    # the target's binary input. EOF means assignment failed; never launch.
    if os.read(sys.stdin.fileno(), 1) != b"\x01":
        return 2
    return subprocess.call(sys.argv[1:], stdin=sys.stdin, stdout=sys.stdout,
                           stderr=sys.stderr, close_fds=True)


if __name__ == "__main__":
    raise SystemExit(main())
