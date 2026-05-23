"""24h pump + pullback → fade short.

Rationale: micro-cap pumps tend to retrace meaningfully within 24-72h.
The lab will not short into the pump itself (catching falling knives in
reverse) — entry requires the price to have pulled back ≥10% from the
24h high, signalling distribution has begun.
"""

from __future__ import annotations

from typing import Any

from cex_signal_lab.strategies.base import Signal, Strategy


class PumpShort(Strategy):
    name = "pump_short"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.pump_threshold = float(config.get("pump_24h_pct", 30.0))
        self.min_pullback = float(config.get("min_pullback_pct", 10.0))

    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        symbol = ticker["symbol"]
        try:
            change_pct = float(ticker["priceChangePercent"])
        except (KeyError, TypeError, ValueError):
            return None
        if change_pct <= self.pump_threshold:
            return None
        klines = context.get("klines_1h", {}).get(symbol)
        if not klines or len(klines) < 3:
            return None
        try:
            highs = [float(k[2]) for k in klines]
            current = float(klines[-1][4])
        except (KeyError, IndexError, TypeError, ValueError):
            return None
        peak = max(highs)
        if peak <= 0:
            return None
        pullback = (peak - current) / peak * 100
        if pullback < self.min_pullback:
            return None
        strength = "A" if change_pct > 80 else "B"
        return Signal(
            strategy=self.name,
            direction="short",
            strength=strength,
            reason=(
                f"24h pump {change_pct:.1f}% then pullback {pullback:.1f}% "
                f"from peak {peak:.4f}"
            ),
            sl_pct=float(self.config.get("sl_pct", 0.15)),
            tp_pct=float(self.config.get("tp_pct", 0.20)),
        )
