"""Extreme negative funding → potential squeeze long.

Real implementation lands in Day 15 of the build plan.
"""

from __future__ import annotations

from typing import Any

from cex_signal_lab.strategies.base import Signal, Strategy


class FundingExtremeNeg(Strategy):
    name = "extreme_neg_funding"

    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        return None  # TODO(day15): implement
