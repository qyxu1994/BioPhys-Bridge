import json

from biophysevo.extraction import build_cases as BC


def test_build_cases_uses_llm_when_flag_set(tmp_path, monkeypatch):
    cand = {
        "doc_id": "BPB0005", "entities": {}, "measurements": [], "formulas": [],
        "evidence_blocks": [{"evidence_id": "ev_t0001", "modality": "table", "text": "Csat=2 uM"}],
    }
    cpath = tmp_path / "cand.jsonl"
    cpath.write_text(json.dumps(cand) + "\n")
    out = tmp_path / "cases.jsonl"

    def fake_extract(blocks, *, enabled, model="gpt-4o", client=None):
        assert enabled and model == "gpt-4o"
        return {
            "domain": "biomolecular_phase_separation",
            "quantitative_evidence": [
                {"metric": "Csat", "value": 2.0, "unit": "uM", "condition": None, "evidence_id": "ev_t0001"}],
            "physical_interpretation": {"derived_quantity": "Csat",
                "directionality": "lower=stronger", "consistency_check": "ok", "caveats": []},
            "biological_mechanism": {"mechanism_type": "condensate_formation_mechanism",
                "description": "multivalent contacts", "structure_function_link": None,
                "mutation_or_ligand_effect": None},
            "research_question": "q", "gold_answer": "a", "supporting_evidence_ids": ["ev_t0001"],
        }
    monkeypatch.setattr(BC.llm_fill, "extract_case_fields", fake_extract)

    rc = BC.main(["--candidates", str(cpath), "--out", str(out),
                  "--use-llm", "--model", "gpt-4o",
                  "--run-dir", str(tmp_path / "run")])
    assert rc == 0
    cases = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert len(cases) == 1
    assert cases[0]["domain"] == "biomolecular_phase_separation"


def test_build_cases_records_llm_failure_without_aborting(tmp_path, monkeypatch):
    cands = [
        {"doc_id": "bad", "entities": {}, "measurements": [], "formulas": [],
         "evidence_blocks": [{"evidence_id": "ev_bad", "text": "nope"}]},
        {"doc_id": "good", "entities": {}, "measurements": [], "formulas": [],
         "evidence_blocks": [{"evidence_id": "ev_good", "text": "Kd = 10 nM"}]},
    ]
    cpath = tmp_path / "cand.jsonl"
    cpath.write_text("\n".join(json.dumps(c) for c in cands) + "\n")
    out = tmp_path / "cases.jsonl"

    def fake_extract(blocks, *, enabled, model="gpt-4o", client=None):
        if blocks[0]["evidence_id"] == "ev_bad":
            raise RuntimeError("context too large")
        return {
            "domain": "protein_ligand_binding",
            "quantitative_evidence": [
                {"metric": "Kd", "value": 10.0, "unit": "nM", "condition": None, "evidence_id": "ev_good"}],
            "physical_interpretation": {"derived_quantity": "Kd",
                "directionality": "lower Kd tighter binding", "consistency_check": "ok", "caveats": []},
            "biological_mechanism": {"mechanism_type": "protein_ligand_binding_mechanism",
                "description": "binding changes mechanism", "structure_function_link": None,
                "mutation_or_ligand_effect": None},
            "research_question": "q", "gold_answer": "a", "supporting_evidence_ids": ["ev_good"],
        }

    monkeypatch.setattr(BC.llm_fill, "extract_case_fields", fake_extract)
    rc = BC.main(["--candidates", str(cpath), "--out", str(out),
                  "--use-llm", "--run-dir", str(tmp_path / "run")])
    assert rc == 0
    assert len(out.read_text().splitlines()) == 1
    manifest = (tmp_path / "run" / "manifest.jsonl").read_text()
    assert "context too large" in manifest


def test_llm_prompt_trims_large_evidence_blocks():
    blocks = [
        {"evidence_id": f"ev_{i}", "modality": "text", "text": "background " * 2000}
        for i in range(20)
    ]
    blocks.append(
        {"evidence_id": "ev_metric", "modality": "table", "text": "Kd = 10 nM " * 2000}
    )
    trimmed = BC.llm_fill.trim_evidence_blocks(
        blocks,
        max_total_chars=5000,
        max_block_chars=1000,
    )
    assert sum(len(b["text"]) for b in trimmed) <= 5000
    assert trimmed[0]["evidence_id"] == "ev_metric"
