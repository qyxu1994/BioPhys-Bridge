"""IO utilities: safe JSONL writers and readers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Iterator


def read_jsonl(path: str | Path) -> Iterator[dict]:
    path = Path(path)
    if not path.exists():
        return
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


class SafeJSONLWriter:
    """Append-mode JSONL writer that flushes after every record.

    Each write is a single ``f.write`` of a complete line followed by ``flush``;
    on POSIX this is atomic for lines under PIPE_BUF (4096 bytes), which is the
    overwhelmingly common case for our records. For bulk one-shot writes use
    :func:`atomic_write_jsonl` instead.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")

    def write(self, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        self._fh.write(line + "\n")
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.close()

    def __enter__(self) -> "SafeJSONLWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def atomic_write_jsonl(path: str | Path, records: Iterable[dict]) -> None:
    """Atomically write a full JSONL file via tempfile + os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def safe_jsonl_writer(path: str | Path) -> SafeJSONLWriter:
    """Functional alias for the writer (matches naming in spec)."""
    return SafeJSONLWriter(path)


def dedup_by_id(records: Iterable[dict], *, key: str = "id") -> list[dict]:
    """Keep the first occurrence per ``key``, preserving order."""
    seen: set[Any] = set()
    out: list[dict] = []
    for r in records:
        k = r.get(key)
        if k is None or k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out
