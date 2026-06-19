"""Per-strategy detection modules.

Add a new strategy by:
  1. Subclassing ``Strategy`` in a new module
  2. Registering it in ``ALL_STRATEGIES`` below
  3. Adding a ``[strategies.<name>]`` block to config.example.toml
"""

from cex_signal_lab.strategies.base import Signal, Strategy
from cex_signal_lab.strategies.crash_bounce import CrashBounce
from cex_signal_lab.strategies.funding_extreme_neg import FundingExtremeNeg
from cex_signal_lab.strategies.funding_extreme_pos import FundingExtremePos
from cex_signal_lab.strategies.funding_flip import FundingFlip
from cex_signal_lab.strategies.pump_short import PumpShort

ALL_STRATEGIES: list[type[Strategy]] = [
    FundingExtremeNeg,
    FundingExtremePos,
    CrashBounce,
    PumpShort,
    FundingFlip,
]

__all__ = [
    "ALL_STRATEGIES",
    "CrashBounce",
    "FundingExtremeNeg",
    "FundingExtremePos",
    "FundingFlip",
    "PumpShort",
    "Signal",
    "Strategy",
]
