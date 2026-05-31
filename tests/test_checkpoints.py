"""Checkpoint store: resume skips completed items and survives reopen."""

from __future__ import annotations

from biophysevo.utils.checkpoints import CheckpointStore


def test_checkpoint_skips_completed(tmp_path):
    store = CheckpointStore(tmp_path / "ckpt.jsonl")
    assert not store.is_done("a")
    store.mark_done("a", status="ok")
    store.mark_done("b", status="ok")
    assert store.is_done("a")
    assert store.is_done("b")
    assert store.completed_count == 2
    store.close()


def test_checkpoint_persists_across_reopen(tmp_path):
    path = tmp_path / "ckpt.jsonl"
    s1 = CheckpointStore(path)
    s1.mark_done("a")
    s1.mark_done("b")
    s1.close()

    s2 = CheckpointStore(path)
    assert s2.is_done("a")
    assert s2.is_done("b")
    assert not s2.is_done("c")


def test_mark_done_is_idempotent(tmp_path):
    path = tmp_path / "ckpt.jsonl"
    s = CheckpointStore(path)
    s.mark_done("a")
    s.mark_done("a")
    s.close()
    lines = [l for l in path.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
