"""Strategy base class. Every signal detector subclasses Strategy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Signal:
    """A potential trade signal emitted by a strategy."""

    strategy: str
    direction: str  # "long" | "short"
    strength: str   # "S" (strongest) | "A" | "B"
    reason: str     # human-readable explanation
    sl_pct: float   # stop-loss distance as fraction (0.08 = 8%)
    tp_pct: float   # take-profit distance as fraction


class Strategy(ABC):
    """One detector per signal type.

    Subclasses must set ``name`` and implement :meth:`detect`. Strategies
    are pure rule functions — they never mutate state. The scanner is
    responsible for calling them, scoring the result, and writing trades.
    """

    name: str = ""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    def detect(self, ticker: dict[str, Any], context: dict[str, Any]) -> Signal | None:
        """Return a Signal if conditions match, else None.

        ``ticker`` is a 24h-ticker dict from the exchange.
        ``context`` carries shared per-scan data (funding rate map,
        BTC reference snapshot, etc.) so strategies don't each refetch.
        """
