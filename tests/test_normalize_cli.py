"""Tests for the `biophysevo.mineru.normalize` CLI.

Bridges the MinerU API capture layout (`<doc>/payload.json`) into the canonical
`parsed_docs/<doc>/` layout the extraction pipeline reads, injecting per-doc
provenance (license/doi/pmcid) so downstream cases don't default to "unknown".
"""

from __future__ import annotations

import json
from pathlib import Path

from biophysevo.mineru.normalize import main as normalize_main
from biophysevo.mineru.normalize_outputs import dry_run_payload


def _make_api_doc(input_dir: Path, doc_id: str) -> None:
    doc = input_dir / doc_id
    doc.mkdir(parents=True, exist_ok=True)
    payload = dry_run_payload(doc_id)
    (doc / "payload.json").write_text(json.dumps(payload), encoding="utf-8")
    (doc / "full.md").write_text(payload["markdown"], encoding="utf-8")


def test_normalize_cli_writes_parsed_docs_with_provenance(tmp_path):
    input_dir = tmp_path / "mineru_api"
    _make_api_doc(input_dir, "BPB0001")
    out = tmp_path / "parsed_docs"
    prov = tmp_path / "provenance.json"
    prov.write_text(json.dumps({
        "BPB0001": {"license": "CC-BY-4.0", "doi": "10.1000/x", "paper_title": "T"}
    }))

    rc = normalize_main([
        "--input-dir", str(input_dir),
        "--out-dir", str(out),
        "--provenance", str(prov),
        "--run-dir", str(tmp_path / "runs" / "norm"),
    ])
    assert rc == 0

    doc = out / "BPB0001"
    assert (doc / "document.md").exists()
    assert (doc / "evidence_blocks.jsonl").exists()
    assert (doc / "parse_metadata.json").exists()

    meta = json.loads((doc / "parse_metadata.json").read_text())
    # provenance is injected as source_item so extract_candidates can read it
    assert meta["source_item"]["license"] == "CC-BY-4.0"
    assert meta["source_item"]["doi"] == "10.1000/x"


def test_normalize_cli_missing_provenance_defaults_empty(tmp_path):
    input_dir = tmp_path / "mineru_api"
    _make_api_doc(input_dir, "DOCX")
    out = tmp_path / "parsed_docs"

    rc = normalize_main([
        "--input-dir", str(input_dir),
        "--out-dir", str(out),
        "--run-dir", str(tmp_path / "runs" / "norm"),
    ])
    assert rc == 0
    meta = json.loads((out / "DOCX" / "parse_metadata.json").read_text())
    # no provenance file -> source_item present but empty (not "unknown" magic)
    assert meta.get("source_item", {}) == {}


def test_normalize_cli_resume_skips(tmp_path):
    input_dir = tmp_path / "mineru_api"
    _make_api_doc(input_dir, "BPB0001")
    out = tmp_path / "parsed_docs"
    run_dir = tmp_path / "runs" / "norm"

    assert normalize_main([
        "--input-dir", str(input_dir), "--out-dir", str(out), "--run-dir", str(run_dir),
    ]) == 0
    assert normalize_main([
        "--input-dir", str(input_dir), "--out-dir", str(out), "--run-dir", str(run_dir),
        "--resume",
    ]) == 0

    metrics = json.loads((run_dir / "metrics.json").read_text())
    assert metrics["skipped"] == 1
