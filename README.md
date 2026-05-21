# cex-signal-lab

> **Open lab for rule-based crypto signal strategies on centralized exchanges.**
> Pluggable strategies, paper-trades only, no API keys, every threshold in plain TOML.

[![Tests](https://github.com/Zanecex101/cex-signal-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/Zanecex101/cex-signal-lab/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: Day 1 of 30](https://img.shields.io/badge/status-day%201%20of%2030-orange.svg)](#roadmap)

> ⚠️ **This project is in active scaffolding (Day 1 of 30).** The first usable
> release lands on Day 7. See the [roadmap](#roadmap) below.

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

## What it will do (when finished)

- Scan Binance USDT-perpetual futures every minute
- Run 4–5 reference rule-based signal strategies:
  - Extreme negative funding → squeeze setup
  - Extreme positive funding → crowded long
  - 24h crash + stabilization → mean-revert long
  - 24h pump + pullback → fade short
- Score every signal against a multi-factor environment filter (BTC regime,
  market sentiment, open interest, volume) before opening
- Open paper-trades to a local JSON ledger
- Push every fill / close to Telegram
- Output daily summary stats: win-rate per strategy, cumulative P&L

## Status

This is the scaffolding commit. There is no working code yet — only the
project skeleton, the configuration schema, and the development plan.

| Subsystem        | Status |
|------------------|--------|
| Project skeleton | ✅ Day 1 |
| Strategy modules | 🚧 Day 3 |
| Ledger module    | 🚧 Day 4 |
| Notify module    | 🚧 Day 5 |
| First runnable scanner | 🚧 Day 7 |
| Position monitor / SL+TP | 🚧 Day 15 |
| First stable release v0.2.0 | 🚧 Day 30 |

## Roadmap

This project is being built deliberately over **30 calendar days**, with one
focused commit per day. The plan:

- **Week 1 (Day 1–7)** — Scaffold and modular extraction
- **Week 2 (Day 8–14)** — Hardening (atomic writes, locking, error handling, tests, CI)
- **Week 3 (Day 15–21)** — Feature polish (auto SL/TP exit, retries, daily summary, Docker)
- **Week 4 (Day 22–30)** — Documentation, examples, second strategy pack, v0.2.0 release

Track progress via the commit log — every commit message is `feat:`, `fix:`,
`refactor:`, `docs:`, `test:`, or `ci:` describing one specific improvement.

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
