"""Regex extraction tests."""

from __future__ import annotations

import json
from pathlib import Path

from biophysevo.extraction.entities import (
    find_ec_numbers,
    find_mutations,
    find_pdb_ids,
    find_uniprot_ids,
)
from biophysevo.extraction.evidence import find_evidence_for_text
from biophysevo.extraction.extract_candidates import main as extract_main
from biophysevo.extraction.formulas import extract_formulas_from_markdown
from biophysevo.extraction.measurements import find_measurements
from biophysevo.mineru.normalize_outputs import dry_run_payload, normalize_mineru_payload


def test_find_uniprot_pdb_ec_mutations():
    text = "The P12345 enzyme (PDB 1ABC, EC 3.4.21.5) bears the A123V mutation."
    assert "P12345" in find_uniprot_ids(text)
    assert "1ABC" in find_pdb_ids(text)
    assert "3.4.21.5" in find_ec_numbers(text)
    assert "A123V" in find_mutations(text)


def test_find_measurements_simple():
    text = "We observed Kd = 120 nM and IC50 = 1.5 uM at pH 7.4."
    ms = find_measurements(text)
    metrics = {m.metric for m in ms}
    assert "Kd" in metrics and "IC50" in metrics
    kd = next(m for m in ms if m.metric == "Kd")
    assert kd.value == 120.0 and kd.unit == "nM"


def test_find_measurements_kcat_km():
    text = "kcat = 12.5 1/s; Km = 0.8 mM."
    ms = find_measurements(text)
    assert any(m.metric == "kcat" and m.value == 12.5 for m in ms)
    assert any(m.metric == "Km" and m.value == 0.8 for m in ms)


def test_formula_extraction_from_markdown():
    md = "Inline: $\\Delta G = RT \\ln K_d$\n\nBlock: $$\\Delta G = -RT \\ln K_a$$"
    f = extract_formulas_from_markdown(md)
    assert len(f) >= 2
    assert any("\\ln K_d" in x["latex"] for x in f)


def test_evidence_id_lookup():
    blocks = [
        {"evidence_id": "ev_a", "text": "Kd = 120 nM"},
        {"evidence_id": "ev_b", "text": "kcat = 12 /s"},
    ]
    assert find_evidence_for_text("120 nM", blocks) == "ev_a"
    assert find_evidence_for_text("kcat", blocks) == "ev_b"
    assert find_evidence_for_text("nothing", blocks) is None


def test_extract_candidates_cli_end_to_end(tmp_path):
    parsed = tmp_path / "parsed_docs"
    normalize_mineru_payload("doc1", dry_run_payload("doc1"), parsed)
    out = tmp_path / "candidates.jsonl"
    rc = extract_main([
        "--parsed-dir", str(parsed),
        "--out", str(out),
        "--run-dir", str(tmp_path / "runs" / "extract"),
    ])
    assert rc == 0
    records = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert records and records[0]["doc_id"] == "doc1"
    measurements = records[0]["measurements"]
    assert any(m["metric"] == "Kd" for m in measurements)
    for m in measurements:
        assert m.get("evidence_id"), "every measurement must have an evidence_id"


def test_extract_candidates_propagates_license(tmp_path):
    """License from parse_metadata.json source_item must reach the candidate."""
    parsed = tmp_path / "parsed_docs"
    normalize_mineru_payload(
        "doc1",
        dry_run_payload("doc1"),
        parsed,
        parse_metadata={
            "mode": "dry-run",
            "source_item": {
                "doc_id": "doc1",
                "license": "CC-BY-4.0",
                "doi": "10.1234/abcd",
                "pmcid": "PMC123",
            },
        },
    )
    out = tmp_path / "candidates.jsonl"
    rc = extract_main([
        "--parsed-dir", str(parsed),
        "--out", str(out),
        "--run-dir", str(tmp_path / "runs" / "extract"),
    ])
    assert rc == 0
    record = [json.loads(l) for l in out.read_text().splitlines() if l.strip()][0]
    assert record["license"] == "CC-BY-4.0"
    assert record["doi"] == "10.1234/abcd"
    assert record["pmcid"] == "PMC123"
