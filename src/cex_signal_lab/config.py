"""Typed configuration loader.

config.toml maps directly onto these dataclasses. Loading goes through
this module — never read the TOML elsewhere — so adding a new knob is
a single-place change.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore


@dataclass
class AccountConfig:
    initial_balance_usd: float = 1000.0
    position_pct: float = 10.0
    leverage: int = 1
    max_open_positions: int = 5
    cooldown_hours: int = 4


@dataclass
class UniverseConfig:
    quote_asset: str = "USDT"
    min_24h_volume_m: float = 10.0
    exclude_symbols: list[str] = field(default_factory=lambda: [
        "BTCUSDT", "ETHUSDT", "USDCUSDT", "FDUSDUSDT", "BTCDOMUSDT",
    ])


@dataclass
class StrategyConfig:
    """Per-strategy block. Unused keys are stored in ``extras``."""

    name: str
    enabled: bool = True
    sl_pct: float = 0.10
    tp_pct: float = 0.15
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvFilterConfig:
    score_min: int = 3
    btc_extreme_pct: float = 5.0
    fng_fear_threshold: int = 25
    fng_greed_threshold: int = 75
    oi_min_usd: float = 5_000_000.0
    volume_min_usd: float = 50_000_000.0


@dataclass
class Config:
    account: AccountConfig
    universe: UniverseConfig
    env_filter: EnvFilterConfig
    strategies: dict[str, StrategyConfig]


def _strategy_from_block(name: str, block: dict[str, Any]) -> StrategyConfig:
    known = {"enabled", "sl_pct", "tp_pct"}
    return StrategyConfig(
        name=name,
        enabled=block.get("enabled", True),
        sl_pct=float(block.get("sl_pct", 0.10)),
        tp_pct=float(block.get("tp_pct", 0.15)),
        extras={k: v for k, v in block.items() if k not in known},
    )


def load_config(path: Path | str | None = None) -> Config:
    """Load a Config from a TOML file. Falls back to config.example.toml."""
    if path is None:
        path = Path("config.toml") if Path("config.toml").exists() else Path("config.example.toml")
    raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))

    account_block = raw.get("account", {})
    universe_block = raw.get("universe", {})
    env_block = raw.get("env_filter", {})
    strategies_block = raw.get("strategies", {})

    return Config(
        account=AccountConfig(**account_block),
        universe=UniverseConfig(**universe_block),
        env_filter=EnvFilterConfig(**env_block),
        strategies={
            name: _strategy_from_block(name, block)
            for name, block in strategies_block.items()
        },
    )
