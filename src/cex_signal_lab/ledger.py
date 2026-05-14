"""Paper-trade ledger backed by a single JSON file.

The ledger is the only mutable state in the lab. Every open / close goes
through here. Reads return typed dataclasses; writes are atomic so a
crash mid-write can't leave a half-serialized file behind.
"""

from __future__ import annotations

import dataclasses
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Trade:
    """One paper-trade lifecycle record."""

    id: str
    symbol: str
    direction: str               # "long" | "short"
    leverage: int
    position_pct: float
    position_usd: float
    notional_usd: float
    entry_price: float
    stop_loss: float
    take_profit: float
    entry_time: str              # ISO8601 with offset
    strategy: str
    strength: str                # S | A | B
    reason: str
    status: str = "open"         # "open" | "closed"
    exit_price: float | None = None
    exit_time: str | None = None
    exit_reason: str | None = None
    pnl_pct: float | None = None
    pnl_usd: float | None = None
    pre_analysis: dict[str, Any] = field(default_factory=dict)


@dataclass
class LedgerState:
    initial_balance_usd: float
    trades: list[Trade]

    def balance(self) -> float:
        bal = self.initial_balance_usd
        for t in self.trades:
            if t.status == "closed" and t.pnl_usd is not None:
                bal += t.pnl_usd
        return bal

    def open_positions(self) -> list[Trade]:
        return [t for t in self.trades if t.status == "open"]

    def next_id(self) -> str:
        if not self.trades:
            return "001"
        max_id = max(int(t.id) for t in self.trades)
        return f"{max_id + 1:03d}"


class Ledger:
    """File-backed ledger with atomic write."""

    def __init__(self, path: Path | str, initial_balance_usd: float = 1000.0) -> None:
        self.path = Path(path)
        self.initial_balance_usd = initial_balance_usd

    def load(self) -> LedgerState:
        """Load from disk. Raises ValueError on corrupted JSON."""
        if not self.path.exists():
            return LedgerState(self.initial_balance_usd, [])
        text = self.path.read_text(encoding="utf-8")
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"ledger {self.path} is corrupted ({e}). "
                f"A backup may exist at {self.path}.bak — inspect manually."
            ) from e
        trades = [Trade(**t) for t in raw.get("trades", [])]
        return LedgerState(
            raw.get("initial_balance", self.initial_balance_usd),
            trades,
        )

    def save(self, state: LedgerState) -> None:
        """Crash-safe save: tmp+fsync+rename, with .bak rotation.

        Survives mid-write crashes and power loss. The previous file
        version is preserved as ``<path>.bak`` so a corrupted save
        leaves the prior version recoverable.
        """
        payload = {
            "initial_balance": state.initial_balance_usd,
            "trades": [dataclasses.asdict(t) for t in state.trades],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Rotate previous version to .bak before overwriting.
        if self.path.exists():
            try:
                os.replace(self.path, self.path.with_suffix(self.path.suffix + ".bak"))
            except OSError:
                pass  # not fatal — the atomic rename below still works

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=".ledger.",
            suffix=".tmp",
            delete=False,
        ) as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
            tmp_name = f.name

        os.replace(tmp_name, self.path)
        # fsync the directory so the rename itself is durable.
        dir_fd = os.open(str(self.path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    def append(self, state: LedgerState, trade: Trade) -> None:
        state.trades.append(trade)
        self.save(state)
