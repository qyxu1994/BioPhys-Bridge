"""Deterministic hashing for evaluation item IDs."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def deterministic_id(payload: Any, *, prefix: str = "", length: int = 16) -> str:
    """Return a stable short ID derived from a JSON-serializable payload.

    Two equal payloads always produce the same ID across processes/platforms.
    """
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}{digest}" if prefix else digest
