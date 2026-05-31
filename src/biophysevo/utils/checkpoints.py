"""Checkpoint store: deterministic-ID-based skipping for resumable jobs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io import safe_jsonl_writer


class CheckpointStore:
    """Append-only JSONL checkpoint of completed item IDs.

    File format: one JSON object per line with at least ``{"id": "..."}``.
    On open(), the existing file is fully scanned to populate the in-memory
    set; subsequent writes are flushed eagerly so ``--resume`` survives a hard
    crash.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._done: set[str] = self._load()
        self._writer = safe_jsonl_writer(self.path)

    def _load(self) -> set[str]:
        out: set[str] = set()
        if not self.path.exists():
            return out
        with self.path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rid = rec.get("id")
                if isinstance(rid, str):
                    out.add(rid)
        return out

    def is_done(self, item_id: str) -> bool:
        return item_id in self._done

    def mark_done(self, item_id: str, **extra: Any) -> None:
        if item_id in self._done:
            return
        self._done.add(item_id)
        self._writer.write({"id": item_id, **extra})

    @property
    def completed_count(self) -> int:
        return len(self._done)

    def completed_ids(self) -> set[str]:
        return set(self._done)

    def close(self) -> None:
        self._writer.close()

    def __enter__(self) -> "CheckpointStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
