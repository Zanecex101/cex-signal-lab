"""Main scanner entrypoint.

This is Day-7 wiring: load config → fetch market data → run all enabled
strategies → log result. Still no env filter, no orders, no SL/TP loop.
Subsequent days fill in the gaps.
"""

from __future__ import annotations

import sys
from typing import Any

import httpx

from cex_signal_lab import __version__
from pathlib import Path

from cex_signal_lab.binance import (
    fetch_24h_tickers,
    fetch_btc_change_pct,
    fetch_funding_rates,
)
from cex_signal_lab.config import Config, load_config
from cex_signal_lab.ledger import Ledger
from cex_signal_lab.monitor import check_exits
from cex_signal_lab.notify import log
from cex_signal_lab.strategies import ALL_STRATEGIES, Signal


def filter_universe(tickers: list[dict[str, Any]], cfg: Config) -> list[dict[str, Any]]:
    quote = cfg.universe.quote_asset
    excl = set(cfg.universe.exclude_symbols)
    min_vol = cfg.universe.min_24h_volume_m * 1e6
    return [
        t for t in tickers
        if t["symbol"].endswith(quote)
        and t["symbol"] not in excl
        and float(t.get("quoteVolume", 0)) > min_vol
    ]


def build_strategies(cfg: Config) -> list[Any]:
    """Instantiate enabled strategies with their config blocks."""
    out = []
    for cls in ALL_STRATEGIES:
        block = cfg.strategies.get(cls.name)
        if block is None or not block.enabled:
            continue
        out.append(cls({"sl_pct": block.sl_pct, "tp_pct": block.tp_pct, **block.extras}))
    return out


LEDGER_PATH = Path("trades.json")


def scan(cfg: Config) -> list[Signal]:
    signals: list[Signal] = []
    with httpx.Client() as client:
        tickers = fetch_24h_tickers(client)
        funding = fetch_funding_rates(client)
        btc_chg = fetch_btc_change_pct(client)

    # Monitor pass: close any open trades that touched SL/TP.
    ticker_map = {t["symbol"]: float(t["lastPrice"]) for t in tickers}
    ledger = Ledger(LEDGER_PATH, initial_balance_usd=cfg.account.initial_balance_usd)
    state = ledger.load()
    closed = check_exits(state, ticker_map)
    if closed:
        ledger.save(state)
        for t in closed:
            log(f"closed #{t.id} {t.symbol} {t.direction} → {t.exit_reason} "
                f"price={t.exit_price} pnl={t.pnl_usd:+.2f} USD")

    candidates = filter_universe(tickers, cfg)
    log(f"universe: {len(candidates)} symbols passing filters")

    strategies = build_strategies(cfg)
    log(f"strategies enabled: {[s.name for s in strategies]}")

    context = {"funding_rates": funding, "btc_change_pct": btc_chg}

    for ticker in candidates:
        for strat in strategies:
            sig = strat.detect(ticker, context)
            if sig is not None:
                signals.append(sig)
                log(f"signal: {ticker['symbol']} {sig.strategy} "
                    f"{sig.direction} [{sig.strength}] — {sig.reason}")

    log(f"scan complete: {len(signals)} signals across {len(candidates)} symbols")
    return signals


LOCK_PATH = "/tmp/cex-signal-lab.lock"


def main() -> int:
    from cex_signal_lab.lock import single_scan_lock

    print(f"cex-signal-lab v{__version__}")
    with single_scan_lock(LOCK_PATH) as got_lock:
        if not got_lock:
            log("another scan is in flight, exiting cleanly", level="INFO")
            return 0
        try:
            cfg = load_config()
        except FileNotFoundError as e:
            log(f"config not found: {e}", level="ERROR")
            return 2
        try:
            scan(cfg)
        except Exception as e:
            log(f"scan crashed: {e}", level="ERROR")
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
