"""Outbound notifications — Telegram + log file.

Centralizing all I/O in one module keeps strategies and the scanner pure
and makes it cheap to swap channels later (Discord, email, webhook).

Day 10 of the build plan adds Markdown escaping, retry logic, and proper
error logging on send failure. For now, failures are quietly logged.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ_CN = timezone(timedelta(hours=8))


def _load_env_file() -> dict[str, str]:
    """Load .env from CWD or repo root if present (override OS env)."""
    out: dict[str, str] = {}
    for candidate in [Path.cwd() / ".env", Path(__file__).resolve().parents[2] / ".env"]:
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
            break
    return out


def _config() -> tuple[str, str]:
    env = _load_env_file()
    token = os.environ.get("TG_BOT_TOKEN") or env.get("TG_BOT_TOKEN", "")
    chat_id = os.environ.get("TG_CHAT_ID") or env.get("TG_CHAT_ID", "")
    return token, chat_id


def _now() -> str:
    return datetime.now(TZ_CN).strftime("%m-%d %H:%M:%S")


def log(text: str, level: str = "INFO", log_file: Path | str | None = None) -> None:
    """Append a timestamped line to stdout + optional log file."""
    line = f"[{_now()}] [{level}] {text}"
    print(line, file=sys.stderr if level in {"ERROR", "WARN"} else sys.stdout)
    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError as e:
            print(f"[{_now()}] [WARN] log_file write failed: {e}", file=sys.stderr)


_MD_V2_SPECIAL = r"_*[]()~`>#+-=|{}.!"


def escape_md(text: str) -> str:
    """Escape Telegram MarkdownV2 special characters.

    A single literal underscore in a strategy reason will otherwise turn
    a notification into a 400 from TG and the message vanishes. Strip
    the formatting risk before sending.
    """
    return "".join("\" + c if c in _MD_V2_SPECIAL else c for c in text)


def notify(text: str, *, parse_mode: str = "MarkdownV2", escape: bool = True,
           retries: int = 3) -> bool:
    """Send a Telegram message. Returns True on success.

    No-op (returns False) if TG credentials are not configured.

    ``escape``: when True (default), MarkdownV2 special chars in ``text``
    are escaped automatically. Set to False if you have hand-formatted
    Markdown that you want sent verbatim.
    """
    token, chat_id = _config()
    if not token or not chat_id:
        log("TG credentials missing, skipping notification", level="WARN")
        return False
    payload_text = escape_md(text) if escape else text
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": payload_text,
        "parse_mode": parse_mode,
    }).encode()

    import time
    backoff = 1.0
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, data=data, timeout=10) as r:
                if r.status == 200:
                    return True
                # 4xx is a client problem; don't retry, just log.
                if 400 <= r.status < 500:
                    log(f"TG send rejected status={r.status}", level="WARN")
                    return False
                log(f"TG send 5xx status={r.status}, retrying", level="WARN")
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500:
                log(f"TG send rejected ({e.code} {e.reason})", level="WARN")
                return False
            log(f"TG send HTTPError {e.code}, retrying", level="WARN")
        except Exception as e:
            log(f"TG send error attempt={attempt}: {e}", level="WARN")
        if attempt < retries:
            time.sleep(backoff)
            backoff *= 2
    log(f"TG send gave up after {retries} attempts", level="ERROR")
    return False
