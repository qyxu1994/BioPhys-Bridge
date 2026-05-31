"""Every line of data/samples/sample_cases.jsonl must validate."""

from __future__ import annotations

import json
from pathlib import Path

from biophysevo.schemas.case_schema import validate_cases


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CASES = REPO_ROOT / "data" / "samples" / "sample_cases.jsonl"


def _load_all() -> list[dict]:
    with SAMPLE_CASES.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def test_sample_jsonl_contains_three_cases():
    cases = _load_all()
    assert len(cases) == 3
    assert len({c["case_id"] for c in cases}) == 3


def test_all_samples_validate_and_are_unique():
    cases = _load_all()
    validated = validate_cases(cases)
    assert len(validated) == 3
    domains = {c.domain for c in validated}
    assert domains == {
        "protein_ligand_binding",
        "enzyme_kinetics",
        "protein_stability_thermodynamics",
    }
    for c in validated:
        assert c.dataset_family == "Biophys-Bridge"
        assert c.dataset_subtype == "Sci-Evo"
        assert c.dataset_type == "Sci-Evo"
