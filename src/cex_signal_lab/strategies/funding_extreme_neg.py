"""Extreme negative funding → squeeze long.

Rationale: when funding is deeply negative for several periods, shorts
are paying longs. Persistent skew like this is often a setup for a
short squeeze when price stops trending down.

Inputs in ``context``:
  - funding_rates: dict[symbol -> current rate as %]
  - funding_history(symbol): list of last 8 funding rates as %  (lazy via fetcher)

Strategy is a pure function — the scanner is responsible for fetching
the history and putting it in context["funding_history"][symbol].
"""

from __future__ import annotations

from typing import Any

from cex_signal_lab.strategies.base import Signal, Strategy


class FundingExtremeNeg(Strategy):
    name = "extreme_neg_funding"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.threshold = float(config.get("funding_threshold", -0.05))
        self.min_neg_count = int(config.get("min_negative_count", 4))
        self.deep_neg_floor = -0.03

    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        symbol = ticker["symbol"]
        rate = context.get("funding_rates", {}).get(symbol)
        if rate is None or rate >= self.threshold:
            return None
        history = context.get("funding_history", {}).get(symbol)
        if history is None or len(history) < 4:
            return None
        deep_neg = sum(1 for r in history if r < self.deep_neg_floor)
        if deep_neg < self.min_neg_count:
            return None
        avg_rate = sum(history) / len(history)
        if avg_rate < -0.15:
            strength = "S"
        elif avg_rate < -0.10:
            strength = "A"
        else:
            strength = "B"
        return Signal(
            strategy=self.name,
            direction="long",
            strength=strength,
            reason=(
                f"funding deeply negative: avg={avg_rate:.4f}%, "
                f"{deep_neg}/{len(history)} periods below {self.deep_neg_floor}%"
            ),
            sl_pct=float(self.config.get("sl_pct", 0.08)),
            tp_pct=float(self.config.get("tp_pct", 0.12)),
        )
