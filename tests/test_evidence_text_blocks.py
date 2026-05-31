"""normalize can emit text evidence blocks from numeric-bearing prose paragraphs."""
import json

from biophysevo.mineru.normalize_outputs import normalize_mineru_payload


def test_text_blocks_included_when_requested(tmp_path):
    payload = {
        "markdown": "Intro with no numbers here.\n\nThe Kd was 120 nM at pH 7.4.\n\nClosing prose.",
        "tables": [], "formulas": [], "figures": [],
    }
    out = normalize_mineru_payload("d", payload, tmp_path, include_text_blocks=True)
    blocks = [json.loads(l) for l in (out / "evidence_blocks.jsonl").read_text().splitlines() if l.strip()]
    text_blocks = [b for b in blocks if b["modality"] == "text"]
    assert any("120 nM" in b["text"] for b in text_blocks)
    # paragraphs without digits are skipped (cost control + measurement focus)
    assert not any("Intro with no numbers" in b["text"] for b in text_blocks)
    assert all(b["evidence_id"].startswith("ev_p") for b in text_blocks)


def test_text_blocks_off_by_default(tmp_path):
    payload = {"markdown": "Kd was 120 nM.", "tables": [], "formulas": [], "figures": []}
    out = normalize_mineru_payload("d", payload, tmp_path)
    blocks = [json.loads(l) for l in (out / "evidence_blocks.jsonl").read_text().splitlines() if l.strip()]
    assert blocks == []  # no text blocks by default; no tables/formulas/figures present
