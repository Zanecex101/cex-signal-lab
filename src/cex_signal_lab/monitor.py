"""Position monitor — close open trades on SL/TP touch.

Runs at the start of every scan cycle, BEFORE looking for new signals.
Without this module, paper-trades opened in earlier scans would
accumulate forever — see the Day 17 entry of the build plan for the
backstory.

Pure function over a (LedgerState, ticker_map) input — the scanner is
responsible for fetching the latest 24h tickers and passing them in.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cex_signal_lab.ledger import LedgerState, Trade

TZ_CN = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(TZ_CN).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def _close_trade(t: Trade, exit_price: float, reason: str) -> None:
    if t.direction == "long":
        pnl_pct = (exit_price - t.entry_price) / t.entry_price * 100 * t.leverage
    else:
        pnl_pct = (t.entry_price - exit_price) / t.entry_price * 100 * t.leverage
    t.exit_price = exit_price
    t.exit_time = _now_iso()
    t.exit_reason = reason
    t.pnl_pct = round(pnl_pct, 2)
    t.pnl_usd = round(pnl_pct / 100 * t.position_usd, 4)
    t.status = "closed"


def check_exits(state: LedgerState, ticker_map: dict[str, float]) -> list[Trade]:
    """Mutate state in place, returning the list of trades just closed.

    ``ticker_map`` is a {symbol: current_price} dict. Trades whose symbol
    is missing from the map are left open (the price feed may have
    transient gaps; the next scan cycle will catch up).
    """
    closed: list[Trade] = []
    for t in state.trades:
        if t.status != "open":
            continue
        price = ticker_map.get(t.symbol)
        if price is None:
            continue
        if t.direction == "long":
            if price <= t.stop_loss:
                _close_trade(t, price, "stop_loss")
                closed.append(t)
            elif price >= t.take_profit:
                _close_trade(t, price, "take_profit")
                closed.append(t)
        else:  # short
            if price >= t.stop_loss:
                _close_trade(t, price, "stop_loss")
                closed.append(t)
            elif price <= t.take_profit:
                _close_trade(t, price, "take_profit")
                closed.append(t)
    return closed
