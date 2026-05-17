"""Public Binance USDT-perpetual data fetchers (no auth required).

All fetchers go through ``_check_response`` which raises a
``BinanceAPIError`` if the API replied with the rate-limit / error
shape ``{"code": <negative int>, "msg": ...}`` that Binance returns
with HTTP 200.
"""

from __future__ import annotations

from typing import Any

import httpx

BASE = "https://fapi.binance.com"
TIMEOUT = 10.0


class BinanceAPIError(RuntimeError):
    """Raised when Binance returns the error envelope instead of data."""

    def __init__(self, code: int, msg: str, endpoint: str) -> None:
        super().__init__(f"binance {endpoint} returned code={code} msg={msg!r}")
        self.code = code
        self.msg = msg
        self.endpoint = endpoint


def _check_response(payload: Any, endpoint: str) -> Any:
    """If ``payload`` is the error envelope, raise. Otherwise pass it through."""
    if isinstance(payload, dict) and "code" in payload and "msg" in payload:
        try:
            code = int(payload["code"])
        except (TypeError, ValueError):
            return payload  # weird shape, but not the standard error envelope
        if code < 0:
            raise BinanceAPIError(code, str(payload["msg"]), endpoint)
    return payload


def fetch_24h_tickers(client: httpx.Client) -> list[dict[str, Any]]:
    r = client.get(f"{BASE}/fapi/v1/ticker/24hr", timeout=TIMEOUT)
    r.raise_for_status()
    data = _check_response(r.json(), "/fapi/v1/ticker/24hr")
    if not isinstance(data, list):
        raise BinanceAPIError(-9999, f"expected list, got {type(data).__name__}",
                              "/fapi/v1/ticker/24hr")
    return data


def fetch_funding_rates(client: httpx.Client) -> dict[str, float]:
    r = client.get(f"{BASE}/fapi/v1/premiumIndex", timeout=TIMEOUT)
    r.raise_for_status()
    data = _check_response(r.json(), "/fapi/v1/premiumIndex")
    if not isinstance(data, list):
        raise BinanceAPIError(-9999, f"expected list, got {type(data).__name__}",
                              "/fapi/v1/premiumIndex")
    return {item["symbol"]: float(item["lastFundingRate"]) * 100 for item in data}


def fetch_btc_change_pct(client: httpx.Client) -> float:
    r = client.get(
        f"{BASE}/fapi/v1/ticker/24hr",
        params={"symbol": "BTCUSDT"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = _check_response(r.json(), "/fapi/v1/ticker/24hr?symbol=BTCUSDT")
    return float(data["priceChangePercent"])


def fetch_funding_history(
    client: httpx.Client, symbol: str, limit: int = 8
) -> list[float]:
    r = client.get(
        f"{BASE}/fapi/v1/fundingRate",
        params={"symbol": symbol, "limit": limit},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = _check_response(r.json(), "/fapi/v1/fundingRate")
    if not isinstance(data, list):
        raise BinanceAPIError(-9999, f"expected list, got {type(data).__name__}",
                              "/fapi/v1/fundingRate")
    return [float(item["fundingRate"]) * 100 for item in data]


def fetch_klines(
    client: httpx.Client, symbol: str, interval: str = "1h", limit: int = 6
) -> list[list[Any]]:
    r = client.get(
        f"{BASE}/fapi/v1/klines",
        params={"symbol": symbol, "interval": interval, "limit": limit},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = _check_response(r.json(), "/fapi/v1/klines")
    if not isinstance(data, list):
        raise BinanceAPIError(-9999, f"expected list, got {type(data).__name__}",
                              "/fapi/v1/klines")
    return data


def fetch_open_interest(client: httpx.Client, symbol: str) -> float:
    r = client.get(
        f"{BASE}/fapi/v1/openInterest",
        params={"symbol": symbol},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = _check_response(r.json(), "/fapi/v1/openInterest")
    return float(data["openInterest"])
