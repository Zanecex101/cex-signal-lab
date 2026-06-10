"""Funding rate flip detection.

When funding crosses zero with non-trivial magnitude, the order book
has just rebalanced from one side being over-paid to the other. Often
marks a short-term regime shift.

Trigger:
  - Latest funding rate has the opposite sign vs the average of the
    prior 4 periods
  - AND |latest rate| ≥ flip_min_magnitude  (trivial near-zero
    crossings are excluded)
  - AND the prior 4 periods all had the same sign (consistent regime
    that just broke)

Direction:
  - Negative → positive: short crowded longs (direction = "short")
  - Positive → negative: long likely squeeze (direction = "long")
"""

from __future__ import annotations

from typing import Any

from cex_signal_lab.strategies.base import Signal, Strategy


class FundingFlip(Strategy):
    name = "funding_flip"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.flip_min_magnitude = float(config.get("flip_min_magnitude", 0.04))

    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        symbol = ticker["symbol"]
        latest = context.get("funding_rates", {}).get(symbol)
        history = context.get("funding_history", {}).get(symbol)
        if latest is None or history is None or len(history) < 5:
            return None

        if abs(latest) < self.flip_min_magnitude:
            return None

        prior = history[-5:-1]  # 4 most recent before current
        if not prior or any(p == 0 for p in prior):
            return None

        # All prior 4 same sign; latest has opposite sign
        prior_sign = 1 if prior[0] > 0 else -1
        if not all((p > 0) == (prior_sign > 0) for p in prior):
            return None
        latest_sign = 1 if latest > 0 else -1
        if latest_sign == prior_sign:
            return None

        # Direction: latest negative → long; latest positive → short.
        direction = "long" if latest < 0 else "short"
        magnitude = abs(latest)
        if magnitude > 0.10:
            strength = "A"
        else:
            strength = "B"

        return Signal(
            strategy=self.name,
            direction=direction,
            strength=strength,
            reason=(
                f"funding flip: {prior_sign:+d} regime ×4 → {latest:+.4f}% "
                f"(|magnitude|={magnitude:.4f}%)"
            ),
            sl_pct=float(self.config.get("sl_pct", 0.08)),
            tp_pct=float(self.config.get("tp_pct", 0.12)),
        )
