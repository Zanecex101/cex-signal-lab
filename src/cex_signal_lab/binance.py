"""Public Binance USDT-perpetual data fetchers (no auth required)."""

from __future__ import annotations

from typing import Any

import httpx

BASE = "https://fapi.binance.com"
TIMEOUT = 10.0


def fetch_24h_tickers(client: httpx.Client) -> list[dict[str, Any]]:
    r = client.get(f"{BASE}/fapi/v1/ticker/24hr", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def fetch_funding_rates(client: httpx.Client) -> dict[str, float]:
    r = client.get(f"{BASE}/fapi/v1/premiumIndex", timeout=TIMEOUT)
    r.raise_for_status()
    return {
        item["symbol"]: float(item["lastFundingRate"]) * 100
        for item in r.json()
    }


def fetch_btc_change_pct(client: httpx.Client) -> float:
    r = client.get(
        f"{BASE}/fapi/v1/ticker/24hr",
        params={"symbol": "BTCUSDT"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return float(r.json()["priceChangePercent"])
