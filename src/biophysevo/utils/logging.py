"""Minimal structured logger that never prints secrets."""

from __future__ import annotations

import logging
import os
import sys

_SECRET_KEYS = (
    "API_KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
)


def _scrub_env_in_message(msg: str) -> str:
    for k, v in os.environ.items():
        if not v:
            continue
        if any(s in k.upper() for s in _SECRET_KEYS):
            msg = msg.replace(v, f"<{k}>")
    return msg


class _ScrubFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        if isinstance(record.msg, str):
            record.msg = _scrub_env_in_message(record.msg)
        return True


def get_logger(name: str = "biophysevo", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    )
    handler.addFilter(_ScrubFilter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
