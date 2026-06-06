# Configuring cex-signal-lab

`config.example.toml` ships with safe illustrative defaults. Copy to
`config.toml` and edit. Every knob below is documented; tune one at a
time and run `cex-signal-summary` to see the effect.

## `[account]`

| Key | Type | Default | What it does |
|---|---|---|---|
| `initial_balance_usd` | float | 1000.0 | Starting paper balance. Reflected in `cex-signal-summary` output. |
| `position_pct` | float | 10 | Percent of current balance committed per trade. |
| `leverage` | int | 1 | Multiplier applied to PnL. The lab does not place real orders, so this is purely accounting. |
| `max_open_positions` | int | 5 | Concurrency cap. New signals are dropped once at the limit. |
| `cooldown_hours` | int | 4 | After opening a trade on a symbol, the same symbol can't be re-opened until this many hours have passed. |

## `[universe]`

| Key | Type | Default | What it does |
|---|---|---|---|
| `quote_asset` | str | "USDT" | Only pairs ending in this quote are scanned. |
| `min_24h_volume_m` | float | 10 | Minimum 24h quote-volume in millions USD. Below this, the symbol never sees a strategy. |
| `exclude_symbols` | list[str] | BTCUSDT, ETHUSDT, … | Symbols to ignore entirely. Default excludes majors and stable-on-stable pairs. |

## `[env_filter]`

The filter scores every signal across four orthogonal factors plus the
signal's own strength tier. A trade only opens if `total ≥ score_min`.

| Key | Type | Default | What it does |
|---|---|---|---|
| `score_min` | int | 3 | Minimum total score required to open. Lower = more trades, more loose. |
| `btc_extreme_pct` | float | 5.0 | If `|BTC 24h%| > this`, the BTC factor goes -1 (longs vs falling BTC, shorts vs rising BTC). |
| `fng_fear_threshold` | int | 25 | F&G value below this counts as 'extreme fear' (favours longs). |
| `fng_greed_threshold` | int | 75 | F&G value above this counts as 'extreme greed' (favours shorts). |
| `oi_min_usd` | float | 5_000_000 | Symbol open interest below this scores 0 instead of +1. |
| `volume_min_usd` | float | 50_000_000 | 24h volume above this scores +1; below 40% of it scores -1. |

## `[strategies.<name>]`

Each block has at least:

| Key | Type | Default | What it does |
|---|---|---|---|
| `enabled` | bool | true | Master switch. False = strategy is not even instantiated. |
| `sl_pct` | float | 0.10 | Stop-loss distance as a fraction (0.08 = 8%). |
| `tp_pct` | float | 0.15 | Take-profit distance as a fraction. |

Strategies declare their own knobs in addition. They land in
`StrategyConfig.extras` and the strategy reads them from
`self.config`:

### `[strategies.extreme_neg_funding]`
| Key | Default | What it does |
|---|---|---|
| `funding_threshold` | -0.05 | Current rate (%) must be below this to even consider |
| `min_negative_count` | 4 | Out of last 8 funding periods, ≥ this many must be deeply negative |

### `[strategies.extreme_pos_funding]`
| Key | Default | What it does |
|---|---|---|
| `funding_threshold` | 0.10 | Current rate (%) must exceed this |
| `min_positive_count` | 4 | Out of last 8, ≥ this many must be high |

### `[strategies.crash_bounce]`
| Key | Default | What it does |
|---|---|---|
| `crash_24h_pct` | -20 | 24h price drop must exceed this magnitude |

### `[strategies.pump_short]`
| Key | Default | What it does |
|---|---|---|
| `pump_24h_pct` | 30 | 24h price gain must exceed this |
| `min_pullback_pct` | 10 | Price must be ≥ this far below the 24h high |

## Tuning workflow

1. Pick one knob.
2. Run `cex-signal-lab` for a week with the change.
3. `cex-signal-summary` to compare strategy win-rate before/after.
4. Revert if win-rate dropped > 5 percentage points or PnL flipped sign.

Don't tune three knobs at once — you won't know which mattered.
