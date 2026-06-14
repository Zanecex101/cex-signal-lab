"""Multi-factor environment filter.

Single-indicator signals get fooled by every regime change. This
module scores a candidate Signal against four orthogonal factors plus
the signal's own strength tier, returning a pass/fail decision and a
breakdown that's recorded on every trade for later analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cex_signal_lab.config import EnvFilterConfig
from cex_signal_lab.strategies import Signal


@dataclass
class EnvDecision:
    passed: bool
    score: int
    breakdown: dict[str, str] = field(default_factory=dict)


def _score_btc(direction: str, btc_chg: float, cfg: EnvFilterConfig) -> tuple[int, str]:
    if direction == "long":
        if btc_chg > -2:
            return 1, f"BTC {btc_chg:+.1f}% — neutral-to-up, fine for longs (+1)"
        if btc_chg < -cfg.btc_extreme_pct:
            return -1, f"BTC {btc_chg:+.1f}% — crashing, longs risky (-1)"
        return 0, f"BTC {btc_chg:+.1f}% — soft (0)"
    else:  # short
        if btc_chg < 2:
            return 1, f"BTC {btc_chg:+.1f}% — neutral-to-down, fine for shorts (+1)"
        if btc_chg > cfg.btc_extreme_pct:
            return -1, f"BTC {btc_chg:+.1f}% — pumping, shorts risky (-1)"
        return 0, f"BTC {btc_chg:+.1f}% — firm (0)"


def _score_sentiment(direction: str, fng: int | None, cfg: EnvFilterConfig) -> tuple[int, str]:
    # FGI feed occasionally returns None for 2-10 minutes (provider hiccup).
    # We score it 0 and log so the missing factor is visible in the scan log
    # rather than silently flattening the verdict.
    if fng is None:
        import logging
        logging.getLogger("cex_signal_lab").warning(
            "env_filter: FGI unavailable, scoring sentiment factor as 0"
        )
        return 0, "FGI unavailable (0)"
    if direction == "long":
        if fng <= cfg.fng_fear_threshold:
            return 1, f"FGI={fng} — extreme fear, contrarian long (+1)"
        if fng >= cfg.fng_greed_threshold:
            return -1, f"FGI={fng} — extreme greed, longs risky (-1)"
        return 0, f"FGI={fng} — neutral (0)"
    else:
        if fng >= cfg.fng_greed_threshold:
            return 1, f"FGI={fng} — extreme greed, contrarian short (+1)"
        if fng <= cfg.fng_fear_threshold:
            return -1, f"FGI={fng} — extreme fear, shorts risky (-1)"
        return 0, f"FGI={fng} — neutral (0)"


def _score_oi(oi_usd: float | None, cfg: EnvFilterConfig) -> tuple[int, str]:
    if oi_usd is None:
        return 0, "OI unavailable (0)"
    if oi_usd >= cfg.oi_min_usd:
        return 1, f"OI=${oi_usd/1e6:.1f}M — engaged market (+1)"
    return 0, f"OI=${oi_usd/1e6:.1f}M — thin attention (0)"


def _score_volume(quote_volume_usd: float, cfg: EnvFilterConfig) -> tuple[int, str]:
    if quote_volume_usd >= cfg.volume_min_usd:
        return 1, f"24h volume=${quote_volume_usd/1e6:.0f}M — active (+1)"
    if quote_volume_usd >= cfg.volume_min_usd * 0.4:
        return 0, f"24h volume=${quote_volume_usd/1e6:.0f}M — moderate (0)"
    return -1, f"24h volume=${quote_volume_usd/1e6:.0f}M — anemic (-1)"


def _score_strength(strength: str) -> tuple[int, str]:
    if strength == "S":
        return 2, "signal strength S (+2)"
    if strength == "A":
        return 1, "signal strength A (+1)"
    return 0, "signal strength B (0)"


def evaluate(
    signal: Signal,
    *,
    btc_change_pct: float,
    fng_value: int | None,
    oi_usd: float | None,
    quote_volume_usd: float,
    cfg: EnvFilterConfig,
) -> EnvDecision:
    breakdown: dict[str, str] = {}
    total = 0

    s, line = _score_btc(signal.direction, btc_change_pct, cfg)
    breakdown["btc"] = line
    total += s
    s, line = _score_sentiment(signal.direction, fng_value, cfg)
    breakdown["sentiment"] = line
    total += s
    s, line = _score_oi(oi_usd, cfg)
    breakdown["oi"] = line
    total += s
    s, line = _score_volume(quote_volume_usd, cfg)
    breakdown["volume"] = line
    total += s
    s, line = _score_strength(signal.strength)
    breakdown["strength"] = line
    total += s

    breakdown["verdict"] = f"score={total}, threshold={cfg.score_min}"
    return EnvDecision(passed=total >= cfg.score_min, score=total, breakdown=breakdown)
