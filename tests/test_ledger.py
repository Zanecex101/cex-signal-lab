"""Tests for the trade ledger (atomic writes, balance, ids)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cex_signal_lab.ledger import Ledger, LedgerState, Trade


def _sample_trade(id_: str = "001", pnl: float | None = None, status: str = "open") -> Trade:
    return Trade(
        id=id_, symbol="ABCUSDT", direction="long", leverage=1,
        position_pct=10, position_usd=100.0, notional_usd=100.0,
        entry_price=1.0, stop_loss=0.9, take_profit=1.2,
        entry_time="2026-05-09T00:00:00+08:00",
        strategy="test", strength="A", reason="unit-test",
        status=status, pnl_usd=pnl,
    )


def test_load_returns_empty_when_file_missing(tmp_path: Path) -> None:
    led = Ledger(tmp_path / "missing.json", initial_balance_usd=500.0)
    state = led.load()
    assert state.trades == []
    assert state.initial_balance_usd == 500.0


def test_save_then_load_roundtrip(tmp_path: Path) -> None:
    led = Ledger(tmp_path / "ledger.json")
    state = led.load()
    state.trades.append(_sample_trade())
    led.save(state)

    state2 = led.load()
    assert len(state2.trades) == 1
    assert state2.trades[0].symbol == "ABCUSDT"


def test_balance_sums_only_closed_trades(tmp_path: Path) -> None:
    state = LedgerState(initial_balance_usd=1000.0, trades=[
        _sample_trade("001", pnl=50.0, status="closed"),
        _sample_trade("002", pnl=-20.0, status="closed"),
        _sample_trade("003", pnl=None, status="open"),
    ])
    assert state.balance() == 1000.0 + 50.0 - 20.0


def test_next_id_increments(tmp_path: Path) -> None:
    state = LedgerState(initial_balance_usd=1.0, trades=[])
    assert state.next_id() == "001"
    state.trades.append(_sample_trade("001"))
    state.trades.append(_sample_trade("042"))
    assert state.next_id() == "043"


def test_save_creates_backup(tmp_path: Path) -> None:
    led = Ledger(tmp_path / "ledger.json")
    state = led.load()
    state.trades.append(_sample_trade("001"))
    led.save(state)
    state.trades.append(_sample_trade("002"))
    led.save(state)
    assert (tmp_path / "ledger.json.bak").exists(), \
        "previous version should be preserved as .bak"
