"""Main scanner entrypoint.

For now this is a placeholder. Strategy detection, ledger writes, and
the per-minute scan loop arrive in subsequent daily commits — see the
30-day plan in README.
"""

from __future__ import annotations

import sys

from cex_signal_lab import __version__


def main() -> int:
    print(f"cex-signal-lab v{__version__}")
    print("Scanner not implemented yet — Day 7 of the build plan.")
    print("Track progress at https://github.com/Zanecex101/cex-signal-lab")
    return 0


if __name__ == "__main__":
    sys.exit(main())
