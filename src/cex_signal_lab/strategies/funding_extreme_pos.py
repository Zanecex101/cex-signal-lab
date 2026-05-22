"""Extreme positive funding → crowded long, fade short.

Rationale: when funding is persistently high, longs are paying shorts
and the order book is over-leveraged on the long side. Often resolves
with a flush.
"""

from __future__ import annotations

from typing import Any

from cex_signal_lab.strategies.base import Signal, Strategy


class FundingExtremePos(Strategy):
    name = "extreme_pos_funding"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.threshold = float(config.get("funding_threshold", 0.10))
        self.min_pos_count = int(config.get("min_positive_count", 4))
        self.high_pos_floor = 0.05

    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        symbol = ticker["symbol"]
        rate = context.get("funding_rates", {}).get(symbol)
        if rate is None or rate <= self.threshold:
            return None
        history = context.get("funding_history", {}).get(symbol)
        if history is None or len(history) < 4:
            return None
        high_pos = sum(1 for r in history if r > self.high_pos_floor)
        if high_pos < self.min_pos_count:
            return None
        avg_rate = sum(history) / len(history)
        if avg_rate > 0.20:
            strength = "S"
        elif avg_rate > 0.12:
            strength = "A"
        else:
            strength = "B"
        return Signal(
            strategy=self.name,
            direction="short",
            strength=strength,
            reason=(
                f"funding persistently high: avg={avg_rate:.4f}%, "
                f"{high_pos}/{len(history)} periods above {self.high_pos_floor}%"
            ),
            sl_pct=float(self.config.get("sl_pct", 0.10)),
            tp_pct=float(self.config.get("tp_pct", 0.15)),
        )
