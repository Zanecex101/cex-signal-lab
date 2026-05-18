"""Standard logging configuration for cex-signal-lab.

Reads LOG_LEVEL from env (default INFO). Logs are written to stdout
in a single-line format that's easy for humans and parseable by
journalctl / logrotate.
"""

from __future__ import annotations

import logging
import os


def setup_logger(name: str = "cex_signal_lab") -> logging.Logger:
    """Idempotent logger setup. Subsequent calls return the configured logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


# Convenience module-level logger for callers that don't need a sub-logger.
log = setup_logger()
