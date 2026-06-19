"""Tests for executor cooldown gating."""
from __future__ import annotations

from cex_signal_lab.executor import is_in_cooldown
from cex_signal_lab.ledger import LedgerState


def test_cooldown_zero_disables_gate():
    state = LedgerState(initial_balance_usd=1000.0, trades=[])
    assert is_in_cooldown(state, "BTCUSDT", hours=0) is False
