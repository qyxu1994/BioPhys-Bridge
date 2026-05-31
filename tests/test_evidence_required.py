"""Evidence-grounding: every gold_answer/quant claim cites an evidence_id."""

from __future__ import annotations

import json
from pathlib import Path

from biophysevo.extraction.build_cases import main as build_main
from biophysevo.extraction.extract_candidates import main as extract_main
from biophysevo.extraction.sci_evo_builder import build_case_from_candidate
from biophysevo.mineru.normalize_outputs import dry_run_payload, normalize_mineru_payload
from biophysevo.schemas.case_schema import Case


def _make_candidate(tmp_path) -> dict:
    parsed = tmp_path / "parsed_docs"
    normalize_mineru_payload("docA", dry_run_payload("docA"), parsed)
    out = tmp_path / "candidates.jsonl"
    rc = extract_main([
        "--parsed-dir", str(parsed),
        "--out", str(out),
        "--run-dir", str(tmp_path / "runs" / "extract"),
    ])
    assert rc == 0
    return json.loads(out.read_text().splitlines()[0])


def test_builder_drops_candidate_without_grounded_measurement():
    out = build_case_from_candidate(
        {"doc_id": "x", "measurements": [], "evidence_blocks": [{"evidence_id": "e1", "text": "x", "modality": "text"}]},
        case_id="biophysevo_test_001",
    )
    assert out is None


def test_builder_produces_valid_case_with_evidence(tmp_path):
    cand = _make_candidate(tmp_path)
    case = build_case_from_candidate(
        cand,
        case_id="biophysevo_test_001",
        source={"license": "CC-BY-4.0", "mineru_parse_id": cand["doc_id"]},
        mineru_artifact_path="data/intermediate/parsed_docs/docA/tables.jsonl",
    )
    assert case is not None
    parsed = Case.model_validate(case)

    assert parsed.agent_tasks[0].supporting_evidence_ids, "gold_answer must cite evidence"
    for qe in parsed.quantitative_evidence:
        assert qe.evidence_id, "every quantitative_evidence must have an evidence_id"
    # Regex-built cases carry templated physics/biology stubs and must be
    # routed to manual review before they can reach the release bundle.
    assert parsed.quality.manual_review_status == "needs_fix"
    assert "[template - needs expert review]" in parsed.physical_interpretation.directionality
    assert "[template - needs expert review]" in parsed.biological_mechanism.description


def test_build_cases_cli_end_to_end(tmp_path):
    cand = _make_candidate(tmp_path)
    cand_path = tmp_path / "candidates.jsonl"
    cand_path.write_text(json.dumps(cand) + "\n")
    out = tmp_path / "cases_draft.jsonl"
    rc = build_main([
        "--candidates", str(cand_path),
        "--out", str(out),
        "--run-dir", str(tmp_path / "runs" / "build"),
    ])
    assert rc == 0
    cases = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert cases
    Case.model_validate(cases[0])
