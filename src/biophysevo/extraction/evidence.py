"""Link extracted spans back to evidence_id from evidence_blocks.jsonl."""

from __future__ import annotations

from pathlib import Path

from biophysevo.utils.io import read_jsonl


def load_evidence_blocks(doc_dir: str | Path) -> list[dict]:
    return list(read_jsonl(Path(doc_dir) / "evidence_blocks.jsonl"))


def find_evidence_for_text(
    needle: str,
    blocks: list[dict],
) -> str | None:
    """Return the first evidence_id whose ``text`` contains ``needle``."""
    if not needle:
        return None
    for b in blocks:
        text = b.get("text") or ""
        if needle in text:
            return b.get("evidence_id")
    return None


def attach_evidence_ids(
    measurements: list[dict],
    blocks: list[dict],
) -> list[dict]:
    """For each measurement dict, fill ``evidence_id`` if discoverable."""
    out: list[dict] = []
    for m in measurements:
        snippet = m.get("snippet") or ""
        eid = find_evidence_for_text(snippet, blocks)
        if eid:
            m = {**m, "evidence_id": eid}
        out.append(m)
    return out
