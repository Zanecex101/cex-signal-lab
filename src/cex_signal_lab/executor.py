"""Open paper-trades in the ledger when a signal clears the env filter.

Caller (the scanner) is responsible for:
  - feeding tickers / context (funding history, klines, FGI, OI)
  - sorting candidate signals by strength
  - deciding which symbol's signal we're about to act on

This module just answers: 'given the scored signal, write a Trade'.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from cex_signal_lab.config import AccountConfig
from cex_signal_lab.env_filter import EnvDecision
from cex_signal_lab.ledger import Ledger, LedgerState, Trade
from cex_signal_lab.strategies import Signal

TZ_CN = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(TZ_CN).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def is_in_cooldown(state: LedgerState, symbol: str, hours: int) -> bool:
    """Return True if symbol was opened or closed within the last ``hours``."""
    cutoff = datetime.now(TZ_CN) - timedelta(hours=hours)
    for t in state.trades:
        if t.symbol != symbol:
            continue
        try:
            ts = datetime.fromisoformat(t.entry_time)
        except ValueError:
            continue
        if ts > cutoff:
            return True
    return False


def execute(
    *,
    ledger: Ledger,
    state: LedgerState,
    signal: Signal,
    decision: EnvDecision,
    symbol: str,
    price: float,
    account: AccountConfig,
) -> Trade | None:
    """Open a paper-trade. Returns the trade or None if blocked.

    Block conditions (caller may want to short-circuit earlier, but
    we double-check):
      - already at max_open_positions
      - symbol is in cooldown
      - decision did not pass
    """
    if not decision.passed:
        return None
    if len(state.open_positions()) >= account.max_open_positions:
        return None
    if is_in_cooldown(state, symbol, account.cooldown_hours):
        return None

    balance = state.balance()
    position_usd = balance * account.position_pct / 100
    if signal.direction == "long":
        sl = round(price * (1 - signal.sl_pct), 6)
        tp = round(price * (1 + signal.tp_pct), 6)
    else:
        sl = round(price * (1 + signal.sl_pct), 6)
        tp = round(price * (1 - signal.tp_pct), 6)

    trade = Trade(
        id=state.next_id(),
        symbol=symbol,
        direction=signal.direction,
        leverage=account.leverage,
        position_pct=account.position_pct,
        position_usd=round(position_usd, 4),
        notional_usd=round(position_usd * account.leverage, 4),
        entry_price=price,
        stop_loss=sl,
        take_profit=tp,
        entry_time=_now_iso(),
        strategy=signal.strategy,
        strength=signal.strength,
        reason=signal.reason,
        status="open",
        pre_analysis={"env_score": decision.score, **decision.breakdown},
    )
    ledger.append(state, trade)
    return trade
