# Contributing to cex-signal-lab

Most contributions are new signal strategies. The bar is intentionally
low — a working strategy is ~80 lines plus one unit test.

## Adding a new strategy in 5 steps

### 1. Decide what market state you're looking for

In one paragraph, describe:
- the trigger conditions
- the rationale (why this state has historical edge)
- the failure mode (when does this rule lose money)

If you can't write this, the strategy is not ready to merge.

### 2. Subclass `Strategy` in a new file

```python
# src/cex_signal_lab/strategies/my_strategy.py
"""Description in plain English."""

from __future__ import annotations
from typing import Any
from cex_signal_lab.strategies.base import Signal, Strategy


class MyStrategy(Strategy):
    name = "my_strategy"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.threshold = float(config.get("threshold", 0.05))

    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        # Pure rule check. No HTTP. No ledger writes. Read everything
        # from `ticker` and `context`.
        if some_condition_fails:
            return None
        return Signal(
            strategy=self.name,
            direction="long",
            strength="A",
            reason="why this triggered",
            sl_pct=float(self.config.get("sl_pct", 0.08)),
            tp_pct=float(self.config.get("tp_pct", 0.12)),
        )
```

### 3. Register it

```python
# src/cex_signal_lab/strategies/__init__.py
from cex_signal_lab.strategies.my_strategy import MyStrategy

ALL_STRATEGIES = [
    ...,
    MyStrategy,
]
```

### 4. Add a config block

```toml
# config.example.toml
[strategies.my_strategy]
enabled = true
threshold = 0.05
sl_pct = 0.08
tp_pct = 0.12
```

### 5. Add a unit test

```python
# tests/test_my_strategy.py
from cex_signal_lab.strategies.my_strategy import MyStrategy


def test_triggers_when_above_threshold():
    strat = MyStrategy({"threshold": 0.05, "sl_pct": 0.08, "tp_pct": 0.12})
    sig = strat.detect(
        ticker={"symbol": "FOOUSDT", "lastPrice": "1.00", "priceChangePercent": "5"},
        context={"funding_rates": {}, "klines_1h": {"FOOUSDT": [...]}},
    )
    assert sig is not None
    assert sig.direction == "long"


def test_no_trigger_when_below():
    strat = MyStrategy({"threshold": 0.05, "sl_pct": 0.08, "tp_pct": 0.12})
    sig = strat.detect(
        ticker={"symbol": "FOOUSDT", "lastPrice": "1.00", "priceChangePercent": "1"},
        context={"funding_rates": {}, "klines_1h": {"FOOUSDT": [...]}},
    )
    assert sig is None
```

## What the PR template asks for

When you open a PR adding a strategy, include in the description:

- The 1-paragraph rationale from step 1
- Any new context fields the scanner needs to populate
- A note on whether the strategy is meant for the env filter to gate
  loosely (B-rated, expects filter to drop most) or tightly (S-rated,
  filter rarely blocks)

## Code style

- `ruff check src/ tests/` must be clean
- `pytest -q` must pass on Python 3.10/11/12
- No new `import` of `requests` — we standardized on `httpx`
- No catching `BaseException`; let `KeyboardInterrupt` and `SystemExit`
  propagate
- All side-effect modules (notify, ledger, executor) stay forbidden
  imports inside strategy code

## Bug reports

Open an issue with:
- The Python version you're on
- A snippet of `cex-signal-lab` log output around the failure
- `cex-signal-summary` snapshot if relevant

The maintainers run the lab on Linux + Python 3.12. macOS works but
gets less testing.
