# Strategies — math and intuition

Every strategy here is a pure rule function. Read each one as: *what
specific market state is this looking for, and what is the rationale?*
None of these are optimized. Backtest before you change a threshold.

## 1. Extreme negative funding → squeeze long

**File**: `src/cex_signal_lab/strategies/funding_extreme_neg.py`

**Trigger**:
- Current funding rate < `funding_threshold` (default −0.05%)
- AND ≥ `min_negative_count` of last 8 funding periods are below
  `deep_neg_floor` (default −0.03%)

**Strength**:
| `avg(history)` | tier |
|---|---|
| < −0.15%      | S |
| < −0.10%      | A |
| otherwise     | B |

**Intuition**: shorts paying longs *persistently* means the short
side is over-positioned. Once price stops trending down, the next
move is often a squeeze.

**Risk**: if the underlying narrative keeps deteriorating (e.g. the
project is genuinely in trouble), funding can stay negative for days
without a bounce. Env filter on BTC regime helps but does not solve.

## 2. Extreme positive funding → fade short

**File**: `src/cex_signal_lab/strategies/funding_extreme_pos.py`

**Trigger**: mirror of #1.
- Current rate > `funding_threshold` (default 0.10%)
- AND ≥ 4 of last 8 periods are above 0.05%

**Strength**: avg > 0.20% → S, > 0.12% → A, else B.

**Intuition**: longs paying shorts persistently means the long side
is leveraged into a corner. Resolves with a flush most of the time.

## 3. 24h crash + stabilization → mean-revert long

**File**: `src/cex_signal_lab/strategies/crash_bounce.py`

**Trigger**:
- 24h price change < `crash_24h_pct` (default −20%)
- AND latest 1-hour close ≥ second-most-recent 1-hour close
  (i.e. stop printing lower lows)

**Strength**: always B — the regime is volatile by definition. Rely
on the env filter to weed these.

**Intuition**: forced sellers (liquidations, margin calls) clear
within hours of a hard daily drop. Catching the *first* hour where
selling pressure stops printing lower closes is a high-base-rate
relief-bounce setup.

**Risk**: catching a falling knife. The strategy explicitly waits for
one hour of stabilization before triggering, but a 25% drop can
become a 50% drop on a continuation.

## 4. 24h pump + pullback → fade short

**File**: `src/cex_signal_lab/strategies/pump_short.py`

**Trigger**:
- 24h price change > `pump_24h_pct` (default 30%)
- AND price has pulled back ≥ `min_pullback_pct` (default 10%) from
  the 24h high

**Strength**: 24h gain > 80% → A, otherwise B.

**Intuition**: micro-cap pumps tend to retrace meaningfully within
24-72 hours. The pullback requirement keeps us from shorting *into*
the pump itself.

**Risk**: if the pump is the start of a multi-day breakout (rare but
real), shorting any pullback is wrong.

## How the env filter changes the picture

The filter is in `src/cex_signal_lab/env_filter.py`. Even after a
strategy fires, the lab won't open a position unless:

```
score(BTC) + score(FGI) + score(OI) + score(volume) + score(strength)
  ≥ cfg.env_filter.score_min
```

Each factor returns +1 / 0 / -1 (volume can be -1 on anemic markets).
Strength bonus: +2 for S, +1 for A, 0 for B.

**Concrete example**: a B-rated `crash_bounce` on a tiny coin during
a BTC crash (-7% on the day) and high greed (FGI=80) scores:
- BTC: -1 (crashing, longs risky)
- FGI: -1 (high greed, longs risky)
- OI: 0 (likely thin)
- volume: -1 (anemic)
- strength: 0 (B)
- **total: -3** → filter blocks. Saves a likely loser.

## Adding a new strategy

See `docs/contributing.md`.
