"""Tests for the process lock used by the scanner."""

from __future__ import annotations

from pathlib import Path

from cex_signal_lab.lock import single_scan_lock


def test_lock_single_holder(tmp_path: Path) -> None:
    path = tmp_path / "scan.lock"
    with single_scan_lock(path) as got_outer:
        assert got_outer is True
        with single_scan_lock(path) as got_inner:
            assert got_inner is False, \
                "second acquire while first is held must report not-acquired"
    # After the outer releases, the next call should succeed again.
    with single_scan_lock(path) as got_again:
        assert got_again is True
