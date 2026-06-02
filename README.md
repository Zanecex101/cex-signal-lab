# cex-signal-lab

> **Open lab for rule-based crypto signal strategies on centralized exchanges.**
> Pluggable strategies, paper-trades only, no API keys, every threshold in plain TOML.

[![Tests](https://github.com/Zanecex101/cex-signal-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/Zanecex101/cex-signal-lab/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: Day 22 of 30](https://img.shields.io/badge/status-day%2022%20of%2030-yellow.svg)](#roadmap)

## Why this exists

Most crypto signal tools are either:

- **Closed-source SaaS** ("our AI predicts crashes" — backed by no published methodology)
- **Strategy YouTube videos** (no code, no backtest, no audit trail)

`cex-signal-lab` is the opposite — every signal is ~100 lines of plain Python,
every threshold is in a TOML file you edit, every paper-trade is logged to a
JSON ledger you can inspect. **Read the source. Run it. Change it. Don't trust
anyone, including me.**

It's a sibling project of [`cex-watch-mcp`](https://github.com/Zanecex101/cex-watch-mcp)
(which provides the clean exchange data feed). This one builds the signal
detection layer on top.

## How it works

```
                     ┌────────────────────────┐
                     │ config.toml             │  thresholds, sizes, knobs
                     └────────────┬────────────┘
                                  │
       ┌──────────────────────────┴──────────────────────────┐
       │                       scanner                         │
       │   load_config → fetch tickers/funding/BTC →          │
       │   monitor.check_exits → filter universe →            │
       │   strategies.detect ×N → env_filter →                │
       │   executor.execute → ledger.append                   │
       └──────────────────────────┬──────────────────────────┘
                                  │
        ┌────────────┬───────────┼───────────┬──────────────┐
        ▼            ▼           ▼           ▼              ▼
   strategies/   env_filter   executor    ledger        notify
   (4 stubs +    (4-factor    (cooldown,  (atomic       (TG +
    real rules)   score)       max-N)     JSON+lock)    log)
```

## What it does

- Scans Binance USDT-perpetual futures every minute
- Runs 4 reference rule-based signal strategies:
  - Extreme negative funding → squeeze setup
  - Extreme positive funding → crowded long fade
  - 24h crash + stabilization → mean-revert long
  - 24h pump + pullback → fade short
- Scores every signal against a multi-factor environment filter (BTC regime,
  market sentiment, open interest, volume) before opening
- Opens paper-trades to a local JSON ledger
- Closes positions automatically on stop-loss / take-profit
- Pushes every fill / close to Telegram
- `cex-signal-summary` CLI for win-rate per strategy + cumulative P&L

## Status

| Subsystem                       | Status |
|---------------------------------|--------|
| Project skeleton (Day 1)        | ✅ |
| Package layout (Day 2)          | ✅ |
| Strategy ABC + 4 stubs (Day 3)  | ✅ |
| Ledger module (Day 4)           | ✅ |
| Notify module (Day 5)           | ✅ |
| TOML config (Day 6)             | ✅ |
| Scanner main loop (Day 7)       | ✅ |
| Atomic / fsync ledger (Day 8)   | ✅ |
| fcntl process lock (Day 9)      | ✅ |
| TG escape + retry (Day 10)      | ✅ |
| Binance API validation (Day 11) | ✅ |
| stdlib logging (Day 12)         | ✅ |
| Unit tests (Day 13)             | ✅ |
| GitHub Actions CI (Day 14)      | ✅ |
| Real funding strategies (Day 15)| ✅ |
| Real price strategies (Day 16)  | ✅ |
| Position monitor (Day 17)       | ✅ |
| env_filter scoring (Day 18)     | ✅ |
| Executor + cooldown (Day 19)    | ✅ |
| Daily summary CLI (Day 20)      | ✅ |
| Full integration + Docker (Day 21) | ✅ |
| Documentation (Day 22-26)       | 🚧 |
| 5th strategy (Day 29)           | 🚧 |
| **v0.2.0 release (Day 30)**     | 🚧 |

## Install

```bash
pip install cex-signal-lab    # once published; for now, install from source:

git clone https://github.com/Zanecex101/cex-signal-lab
cd cex-signal-lab
pip install -e .
cp config.example.toml config.toml
cp .env.example .env       # optional — for Telegram notifications
cex-signal-lab             # run one scan
cex-signal-summary         # view P&L breakdown
```

Or with Docker:

```bash
docker compose up -d
```

## Disclaimer

This is **educational software**. Default parameters are illustrative,
not optimized. The lab opens **paper-trades only** — no real orders are placed
on any exchange. Past behavior of any signal is not predictive. **Don't trade
real money based on this code.**

## Author

[Zane](https://github.com/Zanecex101) — independent crypto exchange researcher.
Also editor at [Cex101](https://cex101.com).

## License

MIT — see [LICENSE](LICENSE).
