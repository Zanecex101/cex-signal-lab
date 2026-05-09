"""24h pump + pullback → fade short.

Real implementation lands in Day 16.
"""

from __future__ import annotations

from typing import Any

from cex_signal_lab.strategies.base import Signal, Strategy


class PumpShort(Strategy):
    name = "pump_short"

    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        return None  # TODO(day16): implement
