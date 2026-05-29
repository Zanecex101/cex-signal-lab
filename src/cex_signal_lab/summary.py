"""Daily summary CLI.

Run as: ``cex-signal-summary``
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from cex_signal_lab.ledger import Ledger


def _stats_for(trades: list) -> dict:
    closed = [t for t in trades if t.status == "closed" and t.pnl_usd is not None]
    if not closed:
        return {"n": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "pnl": 0.0,
                "avg_win": 0.0, "avg_loss": 0.0}
    wins = [t for t in closed if t.pnl_usd > 0]
    losses = [t for t in closed if t.pnl_usd <= 0]
    return {
        "n": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(closed) * 100,
        "pnl": sum(t.pnl_usd for t in closed),
        "avg_win": (sum(t.pnl_usd for t in wins) / len(wins)) if wins else 0.0,
        "avg_loss": (sum(t.pnl_usd for t in losses) / len(losses)) if losses else 0.0,
    }


def _print_table(rows: list[tuple[str, dict]]) -> None:
    if not rows:
        print("(no closed trades yet)")
        return
    fmt = "{:<24} {:>6} {:>6} {:>7} {:>9} {:>10} {:>10}"
    print(fmt.format("strategy", "trades", "wins", "winrt%", "PnL USD", "avg win", "avg loss"))
    print("-" * 78)
    for name, s in rows:
        if s["n"] == 0:
            print(fmt.format(name, "-", "-", "-", "-", "-", "-"))
            continue
        print(fmt.format(
            name, s["n"], s["wins"], f"{s['win_rate']:.1f}",
            f"{s['pnl']:+.2f}", f"{s['avg_win']:+.2f}", f"{s['avg_loss']:+.2f}",
        ))


def main() -> int:
    parser = argparse.ArgumentParser(description="Print cex-signal-lab summary")
    parser.add_argument("--ledger", type=Path, default=Path("trades.json"),
                        help="Path to ledger JSON (default: ./trades.json)")
    args = parser.parse_args()

    if not args.ledger.exists():
        print(f"no ledger at {args.ledger} — nothing to summarize")
        return 0

    state = Ledger(args.ledger).load()
    overall = _stats_for(state.trades)

    by_strategy: dict[str, list] = defaultdict(list)
    for t in state.trades:
        by_strategy[t.strategy].append(t)

    rows = [(name, _stats_for(trades)) for name, trades in sorted(by_strategy.items())]
    rows.append(("OVERALL", overall))

    print(f"\nLedger: {args.ledger}")
    print(f"Initial balance: {state.initial_balance_usd:.2f} USD")
    print(f"Current balance: {state.balance():.2f} USD")
    print(f"Open positions:  {len(state.open_positions())}")
    print()
    _print_table(rows)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
