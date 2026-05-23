"""24h crash + stabilization → mean-revert long.

Rationale: after a 25%+ daily drop, forced sellers (liquidations,
margin calls) tend to clear within hours. If the most recent hourly
candles stop printing lower lows, a relief bounce is a high-base-rate
setup. The lab does not chase falling knives — entry waits for at least
one hourly candle to close flat or up.
"""

from __future__ import annotations

from typing import Any

from cex_signal_lab.strategies.base import Signal, Strategy


class CrashBounce(Strategy):
    name = "crash_bounce"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.crash_threshold = float(config.get("crash_24h_pct", -20.0))

    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        symbol = ticker["symbol"]
        try:
            change_pct = float(ticker["priceChangePercent"])
        except (KeyError, TypeError, ValueError):
            return None
        if change_pct >= self.crash_threshold:
            return None
        klines = context.get("klines_1h", {}).get(symbol)
        if not klines or len(klines) < 3:
            return None
        # last 3 closes; require the latest to be ≥ the previous (flat or up)
        try:
            recent_closes = [float(k[4]) for k in klines[-3:]]
        except (KeyError, IndexError, TypeError, ValueError):
            return None
        if recent_closes[-1] < recent_closes[-2]:
            return None
        return Signal(
            strategy=self.name,
            direction="long",
            strength="B",  # always B — high-volatility regime, treat cautiously
            reason=(
                f"24h drop {change_pct:.1f}% then stabilization "
                f"(last 3 hour closes: "
                f"{recent_closes[0]:.4f} → {recent_closes[1]:.4f} → {recent_closes[2]:.4f})"
            ),
            sl_pct=float(self.config.get("sl_pct", 0.10)),
            tp_pct=float(self.config.get("tp_pct", 0.15)),
        )
