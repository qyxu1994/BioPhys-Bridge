"""LLM fill: anti-fabrication validation + monkeypatched API shim (no network)."""
import json

from biophysevo.extraction import llm_fill


def test_validate_drops_fabricated_evidence_ids():
    fields = {
        "domain": "protein_ligand_binding",
        "quantitative_evidence": [
            {"metric": "Kd", "value": 120.0, "unit": "nM", "condition": "pH 7.4", "evidence_id": "ev_t0001"},
            {"metric": "Ki", "value": 5.0, "unit": "nM", "condition": None, "evidence_id": "ev_FAKE"},
        ],
        "supporting_evidence_ids": ["ev_t0001", "ev_NOPE"],
    }
    valid = {"ev_t0001", "ev_t0002"}
    out = llm_fill.validate_against_evidence(fields, valid)
    assert [qe["metric"] for qe in out["quantitative_evidence"]] == ["Kd"]
    assert out["supporting_evidence_ids"] == ["ev_t0001"]


def test_validate_drops_qe_with_nonnumeric_value():
    fields = {
        "quantitative_evidence": [
            {"metric": "Kd", "value": "see text", "unit": "nM", "evidence_id": "ev_t0001"},
        ],
        "supporting_evidence_ids": [],
    }
    out = llm_fill.validate_against_evidence(fields, {"ev_t0001"})
    assert out["quantitative_evidence"] == []


class _FakeClient:
    def __init__(self, content):
        self._c = content
        self.chat = self

    @property
    def completions(self):
        return self

    def create(self, **kw):
        msg = type("M", (), {"content": self._c})
        choice = type("C", (), {"message": msg})
        return type("R", (), {"choices": [choice]})


def test_extract_case_fields_validates_with_fake_client():
    blocks = [{"evidence_id": "ev_t0001", "modality": "table", "text": "Kd = 120 nM"}]
    content = json.dumps({
        "domain": "protein_ligand_binding",
        "quantitative_evidence": [
            {"metric": "Kd", "value": 120.0, "unit": "nM", "condition": None, "evidence_id": "ev_t0001"},
            {"metric": "Ki", "value": 1.0, "unit": "nM", "condition": None, "evidence_id": "ev_HALLUC"},
        ],
        "supporting_evidence_ids": ["ev_t0001"],
    })
    out = llm_fill.extract_case_fields(blocks, enabled=True, client=_FakeClient(content))
    assert [qe["metric"] for qe in out["quantitative_evidence"]] == ["Kd"]


def test_extract_case_fields_disabled_returns_none():
    assert llm_fill.extract_case_fields([], enabled=False) is None
