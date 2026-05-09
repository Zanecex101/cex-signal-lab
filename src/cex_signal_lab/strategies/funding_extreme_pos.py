"""Extreme positive funding → crowded long, fade short.

Real implementation lands in Day 15.
"""

from __future__ import annotations

from typing import Any

from cex_signal_lab.strategies.base import Signal, Strategy


class FundingExtremePos(Strategy):
    name = "extreme_pos_funding"

    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        return None  # TODO(day15): implement
