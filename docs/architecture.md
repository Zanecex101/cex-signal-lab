# Architecture

The lab is a small set of single-purpose modules wired together by one
scanner loop. Knowing what each module owns — and what it doesn't —
makes it cheap to add features without spaghetti.

## Module map

```
src/cex_signal_lab/
├── __init__.py            version + package marker
├── scanner.py             main loop, ties everything together
├── binance.py             Binance public REST fetchers + error type
├── config.py              TOML loader → typed dataclasses
├── ledger.py              trades.json reader/writer (atomic + .bak)
├── lock.py                fcntl-based single-instance lock
├── monitor.py             SL/TP exit pass over open positions
├── env_filter.py          multi-factor score for Signal candidates
├── executor.py            opens new paper-trades respecting cooldown
├── notify.py              Telegram + log_file send (escapes MD, retries)
├── logger.py              stdlib logging configuration
├── summary.py             cex-signal-summary CLI
└── strategies/
    ├── __init__.py        ALL_STRATEGIES registry
    ├── base.py            Strategy ABC + Signal dataclass
    ├── funding_extreme_neg.py
    ├── funding_extreme_pos.py
    ├── crash_bounce.py
    └── pump_short.py
```

## Responsibility boundaries

- **strategies/** — pure rule functions. Do not touch the ledger.
  Do not call any HTTP. Read everything from the `context` dict
  prepared by the scanner.
- **binance.py** — the only place we hit Binance. Every fetcher
  returns a normalized typed value or raises `BinanceAPIError`.
- **ledger.py** — the only place that touches `trades.json`.
  Atomic writes + .bak rotation; readers are pure.
- **monitor.py** / **executor.py** — wrap ledger mutations in
  domain-specific functions. Monitor closes; executor opens.
- **env_filter.py** — pure scoring; no I/O.
- **notify.py** / **logger.py** — outbound side-effects only.
  Strategies and ledger never import these.
- **scanner.py** — the only orchestrator. If you find yourself adding
  cross-module behavior, it probably belongs here.

## Data flow per scan

1. `scanner.main()` acquires the process lock (`lock.py`).
2. Loads config (`config.py`) and ledger state (`ledger.py`).
3. Fetches a 24h ticker dump + funding map + BTC reference
   (`binance.py`).
4. Runs `monitor.check_exits` against open trades. Closes whatever
   touched SL/TP. Persists.
5. Filters tickers by quote/min-volume/excluded-symbol.
6. For each candidate, lazy-fetches funding history + 1h klines. Runs
   each enabled strategy. Collects all `Signal`s.
7. Sorts S>A>B; takes the top one.
8. Pulls the FGI value and the symbol's open interest. Calls
   `env_filter.evaluate`.
9. If the decision passes, `executor.execute` writes a new trade
   (subject to max-open-positions and per-symbol cooldown).
10. Logs and notifies. Releases the lock.

## Why this shape

- **Single source of truth for ledger writes.** Two-process scenarios
  (cron racing itself, monitoring service + scanner) all funnel
  through `Ledger.save` with file lock + atomic rename.
- **Pure strategies = trivial unit tests.** Each `detect` is a
  function of `(ticker, context) → Signal | None`. No mocks needed.
- **Lazy network fetches.** Funding history and klines are 1
  HTTP request per candidate. Only fetching them after a stub
  matches would be incorrect (the stub needs them); so the scanner
  does it once per scan, *before* strategy detection, and caches
  in `context`.
