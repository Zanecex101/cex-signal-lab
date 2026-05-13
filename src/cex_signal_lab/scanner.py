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
from cex_signal_lab.binance import (
    fetch_24h_tickers,
    fetch_btc_change_pct,
    fetch_funding_rates,
)
from cex_signal_lab.config import Config, load_config
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


def scan(cfg: Config) -> list[Signal]:
    signals: list[Signal] = []
    with httpx.Client() as client:
        tickers = fetch_24h_tickers(client)
        funding = fetch_funding_rates(client)
        btc_chg = fetch_btc_change_pct(client)

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


def main() -> int:
    print(f"cex-signal-lab v{__version__}")
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
