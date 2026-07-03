"""Tests for executor cooldown gating."""
from __future__ import annotations

from cex_signal_lab.executor import is_in_cooldown
from cex_signal_lab.ledger import LedgerState


def test_cooldown_zero_disables_gate():
    state = LedgerState(initial_balance_usd=1000.0, trades=[])
    assert is_in_cooldown(state, "BTCUSDT", hours=0) is False

def test_executor_blocked_at_max_positions(tmp_path):
    from cex_signal_lab.config import AccountConfig
    from cex_signal_lab.env_filter import EnvDecision
    from cex_signal_lab.executor import execute
    from cex_signal_lab.ledger import Ledger, LedgerState, Trade
    from cex_signal_lab.strategies import Signal

    state = LedgerState(initial_balance_usd=1000.0, trades=[
        Trade(id=f"00{i}", symbol=f"X{i}USDT", direction="long",
              leverage=1, position_pct=10, position_usd=100, notional_usd=100,
              entry_price=1.0, stop_loss=0.9, take_profit=1.2,
              entry_time="2026-06-19T10:00:00+08:00",
              strategy="t", strength="A", reason="t")
        for i in range(5)
    ])
    decision = EnvDecision(passed=True, score=5)
    sig = Signal(strategy="t", direction="long", strength="A",
                 reason="t", sl_pct=0.1, tp_pct=0.15)
    ledger = Ledger(tmp_path / "ledger.json")
    out = execute(ledger=ledger, state=state, signal=sig, decision=decision,
                  symbol="NEW", price=10.0,
                  account=AccountConfig(max_open_positions=5))
    assert out is None
