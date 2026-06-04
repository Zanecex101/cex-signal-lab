"""Tests for the TOML config loader."""

from __future__ import annotations

from pathlib import Path

from cex_signal_lab.config import load_config

SAMPLE = """
[account]
initial_balance_usd = 250
position_pct = 5
leverage = 1
max_open_positions = 2
cooldown_hours = 1

[universe]
quote_asset = "USDT"
min_24h_volume_m = 1
exclude_symbols = ["FOOUSDT"]

[env_filter]
score_min = 1
btc_extreme_pct = 3
fng_fear_threshold = 30
fng_greed_threshold = 70
oi_min_usd = 1_000_000
volume_min_usd = 5_000_000

[strategies.extreme_neg_funding]
enabled = false
sl_pct = 0.05
tp_pct = 0.08
funding_threshold = -0.10
"""


def test_load_config_typed(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(SAMPLE)
    cfg = load_config(cfg_path)
    assert cfg.account.initial_balance_usd == 250
    assert cfg.account.leverage == 1
    assert cfg.universe.exclude_symbols == ["FOOUSDT"]
    assert cfg.env_filter.score_min == 1
    assert "extreme_neg_funding" in cfg.strategies


def test_strategy_extras_captured(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(SAMPLE)
    cfg = load_config(cfg_path)
    block = cfg.strategies["extreme_neg_funding"]
    assert block.enabled is False
    assert block.sl_pct == 0.05
    # custom keys go into extras for strategy-specific access
    assert block.extras.get("funding_threshold") == -0.10
